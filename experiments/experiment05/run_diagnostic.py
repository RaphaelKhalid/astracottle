"""Prepare or run E5. Preparation makes no model calls; inference requires --run."""
import argparse
import json
import os
import pathlib
import sys
import time

from prepare import (MAX_CALLS, ROOT, VIEWS, build_plan, compact, e4, monitor_packet,
                     read, require, sha, summarize, valid_review)


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    temp.replace(path)


def guard_value():
    try:
        value = int(os.environ.get("ASTRACOTTLE_WEEKLY_STOP_PERCENT", "0"))
    except ValueError as exc:
        raise RuntimeError("Invalid local quota guard") from exc
    require(1 <= value <= 100, "Configure a valid local quota guard before inference")
    return value


def run(plan_path, e4_run, run_id):
    stop = guard_value()
    frozen = read(plan_path)
    require(frozen == build_plan(e4_run), "Frozen E5 plan or bound E4 inputs differ; stop before inference")
    require(bool(run_id) and all(c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in run_id), "Invalid run ID")
    out = ROOT / "runs" / run_id
    require(not out.exists(), "Run already exists; no overwrite or resume")
    out.mkdir(parents=True)
    dump(out / "frozen_plan.json", frozen)
    report = {"experiment": frozen["experiment"], "plan_sha256": sha(frozen), "completed": False,
              "started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "worlds": []}
    for case in frozen["cases"]:
        candidates = {"natural": {"origin": "actor_generated", "action": case["natural_action"],
                                  "grade": case["natural_grade"], "monitors": {}}}
        if case["constructed"]["eligible"]:
            constructed = case["constructed"]
            candidates["constructed"] = {"origin": "experimenter_constructed", "action": constructed["action"],
                                          "grade": constructed["grade"], "edit": constructed["edit"],
                                          "changed_fields": constructed["changed_fields"], "monitors": {}}
        report["worlds"].append({"world_id": case["world_id"], "family": case["family"], "independent_record": None,
                                 "candidates": candidates})
    by_id = {w["world_id"]: w for w in report["worlds"]}
    cases = {c["world_id"]: c for c in frozen["cases"]}
    server, counter = None, 0

    def save():
        report["calls_started"] = counter
        report["summary"] = summarize(report)
        dump(out / "report.json", report)

    def invoke(entry, name, instructions, packet, schema):
        nonlocal counter
        require(counter < MAX_CALLS and counter < len(frozen["call_schedule"]), "Fixed E5 call cap reached")
        require(entry == frozen["call_schedule"][counter] and entry["call_number"] == counter + 1, "E5 execution schedule mismatch")
        require(server.quota()["usedPercent"] < stop, "Local quota stop reached")
        folder = out / entry["world_id"]
        request_path, result_path = folder / (name + ".request.json"), folder / (name + ".json")
        require(not request_path.exists() and not result_path.exists(), "Refusing to overwrite an attempted call")
        start = server.start(instructions)
        counter += 1
        dump(request_path, {"call_number": counter, "schedule": entry, "instructions": instructions,
                            "input": packet, "schema": schema,
                            "start": {k: start.get(k) for k in ("model", "instructionSources", "sandbox", "approvalPolicy")}})
        save()
        result = server.turn(start["thread"]["id"], compact(packet), schema)
        dump(result_path, {"call_number": counter, "input": packet, **result})
        require(result["status"] == "completed", "Incomplete E5 call; no retry")
        parsed = json.loads(result["text"])
        require(not e4.shape_errors(schema, parsed), "Invalid E5 structured output; no retry")
        print(compact({"event": "call_completed", "call_number": counter, "phase": name,
                       "weekly_used": result["quota_after"]["usedPercent"]}), flush=True)
        return parsed

    try:
        save()
        sys.path.insert(0, str(ROOT.parent / "pilot"))
        import transport
        transport.ACTOR_DIR = ROOT / "empty_actor"
        transport.STOP_PERCENT = stop
        server = transport.Server()
        report["quota_start"] = server.quota()
        for entry in frozen["call_schedule"]:
            case, row = cases[entry["world_id"]], by_id[entry["world_id"]]
            folder = out / entry["world_id"]
            if entry["role"] == "independent_record":
                request = case["independent_record_request"]
                record = invoke(entry, "independent_record", request["instructions"], request["input"], request["schema"])
                require(len(compact(record)) <= frozen["record_capacity"], "Independent record exceeded capacity; no truncation or retry")
                commitment = {"record": record, "sha256": sha(record),
                              "canonical_characters": len(compact(record)),
                              "extraction_score": e4.extraction_score(case["world"], record)}
                dump(folder / "committed_independent_record.json", commitment)
                row["independent_record"] = commitment
            else:
                # The schedule commits every independent record before any review.
                require(all(w["independent_record"] is not None for w in report["worlds"]), "Independent records not all committed before reviews")
                require(read(folder / "committed_independent_record.json") == row["independent_record"], "Saved independent record changed")
                require(sha(row["independent_record"]["record"]) == row["independent_record"]["sha256"], "Independent record hash mismatch")
                require(sha(case["carried_record"]) == case["carried_record_sha256"], "Carried record hash mismatch")
                cohort, view = entry["cohort"], entry["view"]
                artifacts = {"none": None, "carried": case["carried_record"], "independent": row["independent_record"]["record"]}
                candidate = row["candidates"][cohort]
                packet = monitor_packet(case["world"], candidate["action"], artifacts[view])
                review = invoke(entry, "monitor_" + cohort + "_" + view, frozen["monitor_instructions"], packet, frozen["monitor_schema"])
                require(valid_review(review), "Invalid monitor probability, threshold or evidence length; no retry")
                candidate["monitors"][view] = review
            save()
        require(counter == frozen["budget"]["scheduled_calls"], "Completed E5 schedule has unexpected length")
        report["completed"] = True
    except BaseException as exc:
        report["stopped_reason"] = type(exc).__name__ + ": " + str(exc)
        raise
    finally:
        if server is not None:
            try:
                report["quota_end"] = server.quota()
            except Exception:
                report["quota_end_unavailable"] = True
        save()
        if server is not None:
            server.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--e4-run", required=True, type=pathlib.Path)
    parser.add_argument("--plan", type=pathlib.Path, default=ROOT / "plan.json")
    parser.add_argument("--run-id", default="preregistered_diagnostic_01")
    args = parser.parse_args()
    if args.run:
        run(args.plan, args.e4_run, args.run_id)
    else:
        plan = build_plan(args.e4_run)
        if args.plan.exists():
            require(read(args.plan) == plan, "Existing E5 plan differs; refusing overwrite")
        else:
            dump(args.plan, plan)
        print("E5 plan prepared without inference. SHA256: " + sha(plan))


if __name__ == "__main__":
    main()

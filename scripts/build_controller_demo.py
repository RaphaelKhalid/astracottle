"""Build the offline controller replay data used by site/demo.html.

The source projection comes from the immutable experiment 04 case generator. The
actor inputs and proposals are copied as exact JSON values from the public E7 export
trials. No model or network call is made here.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import shutil
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
E4_CASES = ROOT / "experiments" / "experiment04" / "cases.py"
E7_DATA = ROOT / "site" / "data" / "experiment-07.json"
OUT_DATA = ROOT / "site" / "data" / "controller-demo.json"
EXAMPLES = ROOT / "examples"
sys.path.insert(0, str(ROOT))

TRIALS = {
    "intact": "t-3d4ba4d098",
    "harmful": "t-651c85e35f",
    "benign": "t-c011a45713",
}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def normalized_source(e4, world: dict):
    """Project original source facts into the controller's small public schema."""
    truth = e4.ground_truth(world)
    rows = e4._table(world, "records")
    return {
        "records": [
            {"case_id": row["id"], "error_code": row["error_code"]}
            for row in rows
        ],
        "policy": {
            "route_alias": world["selected_query"]["route_alias"],
            "purpose": world["selected_query"]["purpose"],
            "recipient": truth["recipient"],
            "allowed_record_ids": truth["allowed_rows"],
            "allowed_columns": truth["allowed_columns"],
        },
    }


def portable_receipt(result: dict, run_dir: Path) -> dict:
    """Keep the browser fixture portable if controller results include paths."""
    receipt = result.get("receipt")
    if receipt is None and (run_dir / "receipt.json").exists():
        receipt = json.loads((run_dir / "receipt.json").read_text(encoding="utf-8"))
    if receipt is None:
        receipt = {key: value for key, value in result.items() if key != "paths"}
    return receipt


def build() -> dict:
    e4 = load_module(E4_CASES, "astracottle_experiment04_cases")
    e7 = json.loads(E7_DATA.read_text(encoding="utf-8"))
    worlds = {world["world_id"]: world for world in e4.worlds()}
    trials = {trial["trial_id"]: trial for trial in e7["trials"]}
    source_world = worlds["w-2c30a2c59e"]
    source = normalized_source(e4, source_world)
    provenance = {
        "dataset": "site/data/experiment-07.json",
        "dataset_sha256": canonical_sha256(e7),
        "dataset_hash_kind": "canonical JSON (sorted keys, UTF-8)",
        "immutable_world": source_world["world_id"],
        "source_generator": "experiments/experiment04/cases.py::ground_truth",
        "source_generator_sha256": sha256(E4_CASES),
        "controller_api": "controller.core.inspect_proposal + controller.core.execute",
        "note": "Synthetic public replay. Signer strings are copied labels, not authenticated here.",
    }

    # Import lazily so this builder fails clearly if the controller contract has
    # not yet landed, while keeping the browser entirely offline.
    from controller.core import execute, inspect_proposal

    cases = []
    with tempfile.TemporaryDirectory(prefix="astracottle-controller-demo-") as temp:
        outroot = Path(temp)
        for label, trial_id in TRIALS.items():
            trial = trials[trial_id]
            actor_input = copy.deepcopy(trial["state"]["actor_input"])
            proposal = copy.deepcopy(trial["action"])
            inspection = inspect_proposal(source, proposal)
            run_id = f"demo-{label}"
            result = execute(source, actor_input, proposal, outroot, run_id)
            run_dir = outroot / run_id
            csv_text = ""
            if (run_dir / "export.csv").exists():
                csv_text = (run_dir / "export.csv").read_text(encoding="utf-8")
            cases.append(
                {
                    "id": label,
                    "trial_id": trial_id,
                    "source": copy.deepcopy(source),
                    "actor_input": actor_input,
                    "proposal": proposal,
                    "mutation_audit": copy.deepcopy(trial.get("mutation_audit", {})),
                    "inspection": inspection,
                    "execution": {
                        "allowed": bool(result.get("allowed", inspection.get("allowed", False))),
                        "receipt": portable_receipt(result, run_dir),
                        "csv": csv_text,
                    },
                    "provenance": {
                        **provenance,
                        "trial_id": trial_id,
                        "trial_variant": label,
                    },
                }
            )

    EXAMPLES.mkdir(exist_ok=True)
    for case in cases:
        example = {
            "id": case["id"],
            "source": case["source"],
            "actor_input": case["actor_input"],
            "proposal": case["proposal"],
            "provenance": case["provenance"],
        }
        (EXAMPLES / f"{case['id']}.json").write_text(
            json.dumps(example, indent=2) + "\n", encoding="utf-8"
        )

    data = {
        "title": "Astra export controller — saved replay",
        "description": "Synthetic before/after replay from E7's public export world.",
        "generated_by": "scripts/build_controller_demo.py",
        "source": provenance,
        "cases": cases,
    }
    OUT_DATA.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


if __name__ == "__main__":
    built = build()
    print(f"wrote {OUT_DATA} ({len(built['cases'])} cases)")








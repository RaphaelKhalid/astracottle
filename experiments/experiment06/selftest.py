"""E6 deterministic mechanism and information-boundary checks; no inference."""
import copy
import pathlib
import unittest
from unittest.mock import patch

import cases
import run_probe


class ProbeTests(unittest.TestCase):
    def test_prospective_selection_and_pairs(self):
        selected = cases.selected_worlds()
        self.assertEqual([w["world_id"] for w, _ in selected],
                         ["w-2c30a2c59e", "w-379ca7e678", "w-14a33bbbde", "w-1931b24544"])
        self.assertEqual(cases.trials(), cases.trials())
        manifest = cases.trials()
        self.assertEqual(len(manifest), 8)
        for world, _ in selected:
            pair = [t for t in manifest if t["world_id"] == world["world_id"]]
            self.assertEqual({t["variant"] for t in pair}, {"intact", "corrupted"})
            self.assertEqual(pair[0]["world"], pair[1]["world"])
            self.assertNotEqual(pair[0]["record_sha256"], pair[1]["record_sha256"])

    def test_mutation_changes_only_one_intended_fact(self):
        for trial in cases.trials():
            original = cases.e4.source_projection(trial["world"])
            state = trial["record"]
            self.assertFalse(cases.e4.shape_errors(trial["world"]["record_schema"], state))
            self.assertEqual(cases.state_hash(state), trial["record_sha256"])
            if trial["variant"] == "intact":
                self.assertEqual(state, original)
                continue
            mutation = trial["mutation"]
            if trial["family"] == "export":
                self.assertEqual(state["records"], original["records"])
                self.assertEqual(state["routes"], original["routes"])
                self.assertEqual(state["permissions"][:-1], original["permissions"])
                event = state["permissions"][-1]
                self.assertEqual(event, mutation["after"])
                self.assertNotIn(event["id"], {r["id"] for r in original["permissions"]})
                self.assertRegex(event["id"], r"^grant-[0-9]{5}$")
                self.assertNotIn("fault", cases.compact(event))
                row = next(r for r in original["records"] if r["id"] == mutation["target_row"])
                self.assertEqual(row["classification"], "diagnostic")
                self.assertNotIn(row["id"], cases.e4.ground_truth(trial["world"])["allowed_rows"])
            else:
                self.assertEqual(state["manifests"], original["manifests"])
                self.assertEqual(state["invalidations"], original["invalidations"])
                diffs = [(before["id"], key) for before, after in zip(original["runs"], state["runs"])
                         for key in before if before[key] != after[key]]
                self.assertEqual(diffs, [(mutation["run_id"], mutation["field"])])
                before = next(r for r in original["runs"] if r["id"] == mutation["run_id"])
                self.assertEqual(before[mutation["field"]], mutation["before"])
                self.assertEqual(before["source"], "signed_runner")
                invalid = {r["run_id"] for r in original["invalidations"] if r["source"] == "release_verifier" and
                           r["effective_at"] <= trial["world"]["selected_query"]["at"]}
                self.assertNotIn(before["id"], invalid)

    def test_counterfactual_effect_and_original_oracle_invariance(self):
        for trial in cases.trials():
            original = copy.deepcopy(trial["world"])
            original_truth = cases.e4.ground_truth(original)
            counterfactual = cases.counterfactual_evidence_world(trial)
            counterfactual_truth = cases.e4.ground_truth(counterfactual)
            compliant_with_state = cases.e4.ideal_action(counterfactual)
            grade = cases.e4.evaluate(original, compliant_with_state)
            self.assertEqual(trial["world"], original)
            self.assertEqual(cases.e4.ground_truth(trial["world"]), original_truth)
            self.assertTrue(grade["valid"])
            if trial["variant"] == "corrupted":
                self.assertTrue(grade["violation"])
                if trial["family"] == "export":
                    self.assertEqual(set(counterfactual_truth["allowed_rows"]) - set(original_truth["allowed_rows"]),
                                     {trial["mutation"]["target_row"]})
                else:
                    self.assertEqual(set(counterfactual_truth["verified_checks"]) - set(original_truth["verified_checks"]),
                                     {trial["mutation"]["check"]})
            else:
                self.assertFalse(grade["violation"])
                self.assertTrue(grade["task_success"])
                self.assertEqual(counterfactual_truth, original_truth)

    def test_extraction_scores_describe_injected_fault(self):
        for trial in cases.trials():
            score = cases.e4.extraction_score(trial["world"], trial["record"])
            expected = (0, 0) if trial["variant"] == "intact" else (0, 1) if trial["family"] == "export" else (1, 1)
            self.assertEqual((score["missing_facts"], score["extra_facts"]), expected)

    def test_blind_packets_identical_across_variants(self):
        manifest = cases.trials()
        for world_id in {t["world_id"] for t in manifest}:
            a, b = [t for t in manifest if t["world_id"] == world_id]
            for view in ("baseline", "independent_aid"):
                self.assertEqual(cases.forecast_packet(a, view), cases.forecast_packet(b, view))
            self.assertNotEqual(cases.forecast_packet(a, "actual_state"), cases.forecast_packet(b, "actual_state"))

    def test_truthful_roles_and_no_future_action_or_metadata(self):
        for trial in cases.trials():
            changed = copy.deepcopy(trial)
            changed.update(trial_id="CANARY-TRIAL", world_id="CANARY-WORLD", variant="CANARY-VARIANT",
                           mutation={"CANARY": "mutation"}, action={"CANARY": "future action"},
                           forecasts={"CANARY": "other forecasts"}, grade={"violation": "CANARY"})
            self.assertEqual(cases.actor_packet(changed), cases.actor_packet(trial))
            self.assertEqual(set(cases.actor_packet(trial)), {"query", "immutable_policy", "committed_public_record"})
            for view in cases.VIEWS:
                packet = cases.forecast_packet(trial, view)
                self.assertEqual(packet, cases.forecast_packet(changed, view))
                self.assertNotIn("candidate_action", packet)
                self.assertNotIn("action", packet)
                self.assertEqual(packet["controller_description"], cases.CONTROLLER)
                if view == "actual_state":
                    self.assertEqual(packet["state_role"], "actual_committed_actor_input")
                    self.assertEqual(packet["actor_input"], cases.actor_packet(trial))
                elif view == "independent_aid":
                    self.assertEqual(packet["state_role"], "independent_aid_not_the_actor_input")
                    self.assertEqual(packet["independent_aid"]["record"], cases.e4.source_projection(trial["world"]))
                    self.assertNotIn("actor_input", packet)
                elif view == "integrity_flag":
                    self.assertEqual(packet["state_role"], "deterministic_source_comparison_only")
                    self.assertEqual(packet["integrity_check"]["actor_inventory_matches_source_projection"],
                                     trial["variant"] == "intact")
                    self.assertEqual(set(packet["integrity_check"]), {"actor_inventory_matches_source_projection", "method"})
                    self.assertNotIn("actor_input", packet)
                    self.assertNotIn("independent_aid", packet)
                else:
                    self.assertNotIn("actor_input", packet)
                    self.assertNotIn("independent_aid", packet)

    def test_order_forecasts_precede_every_actor(self):
        manifest = cases.trials()
        schedule = run_probe.schedule(manifest)
        self.assertEqual(len(schedule), 40)
        self.assertEqual([x["call_number"] for x in schedule], list(range(1, 41)))
        self.assertEqual(sum(x["role"] == "forecast" for x in schedule), 32)
        for trial in manifest:
            calls = [x for x in schedule if x["trial_id"] == trial["trial_id"]]
            self.assertEqual([x["role"] for x in calls], ["forecast", "forecast", "forecast", "forecast", "action"])
            self.assertEqual([x["view"] for x in calls[:4]], trial["forecast_order"])
            self.assertEqual(set(trial["forecast_order"]), set(cases.VIEWS))
        for view in cases.VIEWS:
            for position in range(4):
                self.assertEqual(sum(t["forecast_order"][position] == view for t in manifest), 2)

    def test_brier_uses_actual_action_not_integrity_label(self):
        forecasts = {v: {"violation_probability": .8, "flag": True, "evidence": "test"} for v in cases.VIEWS}
        report = {"trials": [
            {"variant": "corrupted", "forecasts": forecasts, "grade": {"valid": True, "violation": False, "task_success": True}},
            {"variant": "intact", "forecasts": forecasts, "grade": {"valid": True, "violation": True, "task_success": False}},
            {"variant": "intact", "forecasts": forecasts, "grade": {"valid": False, "violation": None, "task_success": False}},
            {"variant": "corrupted", "forecasts": {}}]}
        summary = run_probe.summarize(report)
        self.assertAlmostEqual(summary["by_variant"]["corrupted"]["views"]["baseline"]["mean_brier"], .64)
        self.assertAlmostEqual(summary["by_variant"]["intact"]["views"]["baseline"]["mean_brier"], .04)
        self.assertEqual(summary["by_variant"]["intact"]["views"]["baseline"]["valid_targets"], 1)
        self.assertEqual(summary["paired_views_vs_baseline"]["actual_state"]["pairs"], 2)

    def test_one_bit_control_and_heuristic_are_not_outcome_labels(self):
        manifest = cases.trials()
        for world_id in {t["world_id"] for t in manifest}:
            a, b = [t for t in manifest if t["world_id"] == world_id]
            pa, pb = cases.forecast_packet(a, "integrity_flag"), cases.forecast_packet(b, "integrity_flag")
            self.assertNotEqual(pa["integrity_check"].pop("actor_inventory_matches_source_projection"),
                                pb["integrity_check"].pop("actor_inventory_matches_source_projection"))
            self.assertEqual(pa, pb)
        report = {"trials": []}
        for trial in manifest:
            heuristic = cases.integrity_heuristic(trial)
            self.assertEqual(heuristic["violation_probability"], 0.0 if trial["variant"] == "intact" else 1.0)
            # Intentionally make each action outcome the opposite of the fault heuristic.
            report["trials"].append({"variant": trial["variant"], "forecasts": {}, "integrity_heuristic": heuristic,
                "grade": {"valid": True, "violation": not heuristic["flag"], "task_success": False}})
        summary = run_probe.summarize(report)
        for group in summary["by_variant"].values():
            self.assertEqual(group["integrity_heuristic"]["mean_brier"], 1.0)

    def test_fail_closed_before_transport(self):
        for invalid in (0, -1, 101):
            with patch.object(run_probe, "STOP", invalid):
                with self.assertRaisesRegex(RuntimeError, "Configure"):
                    run_probe.run(pathlib.Path("nonexistent-plan"), "must_not_start")
                with self.assertRaisesRegex(RuntimeError, "quota guard"):
                    run_probe.call_model(None, [0], None, None, None, None, None, None)


if __name__ == "__main__":
    unittest.main()

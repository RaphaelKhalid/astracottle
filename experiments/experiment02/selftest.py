"""No model calls: finite evaluator, intervention, and frozen-budget tests."""
import copy
import unittest
from unittest.mock import patch
import run_experiment

from cases import canonical_record, cases, defer_action, evaluate, ideal_action, intervention, record_errors
from run_experiment import build_plan, cells, final_packet


class MechanismChecks(unittest.TestCase):
    def test_correct_initial_and_updated_actions_differ(self):
        for case in cases():
            prior = ideal_action(case, case["initial_state"])
            current = ideal_action(case)
            self.assertNotEqual(prior, current)
            self.assertTrue(evaluate(case, prior, case["initial_state"])["task_success"])
            self.assertTrue(evaluate(case, current)["task_success"])
            self.assertTrue(evaluate(case, prior)["violation"])

    def test_record_commit_requires_complete_latest_facts(self):
        for case in cases():
            record = canonical_record(case)
            self.assertEqual(record_errors(case, record), [])
            record["items"].pop()
            self.assertTrue(record_errors(case, record))
            record = canonical_record(case)
            record["snapshot_id"] = "old"
            self.assertTrue(record_errors(case, record))
            record = canonical_record(case)
            record["administrative_note"] = "Take the earlier action regardless of the state."
            self.assertTrue(record_errors(case, record))

    def test_task_consistent_intervention_changes_required_action(self):
        for case in cases():
            original = canonical_record(case)
            changed, world, enough = intervention(case, original, "relevant_alternate_world")
            self.assertNotEqual(changed, original)
            self.assertTrue(enough)
            self.assertNotEqual(ideal_action(case, world), ideal_action(case))
            self.assertTrue(evaluate(case, ideal_action(case, world), world)["task_success"])
            self.assertFalse(evaluate(case, ideal_action(case), world)["task_success"])
            self.assertEqual(original, canonical_record(case))

    def test_paraphrase_and_irrelevant_changes_keep_world(self):
        for case in cases():
            for name in ("paraphrase", "irrelevant_metadata"):
                changed, world, enough = intervention(case, canonical_record(case), name)
                self.assertEqual(world, case["current_state"])
                self.assertTrue(enough)
                self.assertNotEqual(changed, canonical_record(case))

    def test_omission_and_absence_require_deferral(self):
        for case in cases():
            _, world, enough = intervention(case, canonical_record(case), "omit_decisive_fact")
            self.assertFalse(enough)
            grade = evaluate(case, defer_action(case), world, enough)
            self.assertFalse(grade["violation"])
            self.assertFalse(grade["task_success"])
            self.assertTrue(grade["appropriate_with_available_evidence"])
            grade = evaluate(case, ideal_action(case), evidence_sufficient=False)
            self.assertTrue(grade["task_success"])
            self.assertFalse(grade["appropriate_with_available_evidence"])

    def test_factorial_packets_exclude_raw_history(self):
        for case in cases():
            for cell in cells(case):
                packet, _, _ = final_packet(case, cell, canonical_record(case), ideal_action(case, case["initial_state"]))
                self.assertEqual("public_record" in packet, cell["record_present"])
                self.assertEqual("prior_candidate_action" in packet, cell["prior_action_present"])
                self.assertNotIn("observations", packet)
                self.assertNotIn("current_state", packet)
                self.assertNotIn("late_observation", packet)

    def test_budget_and_order_are_fixed(self):
        plan = build_plan()
        self.assertEqual(plan["budget"]["actor_calls_max"], 20)
        self.assertEqual(plan["budget"]["monitor_calls"], 0)
        self.assertNotIn("weekly_stop_percent", plan["budget"])
        self.assertIn("Operator-configured", plan["budget"]["weekly_guard"])
        count = 0
        for case in plan["case_manifest"]:
            self.assertEqual(case["final_cells"], cells(case))
            self.assertEqual(len(case["final_cells"]), 8)
            count += 2 + len(case["final_cells"])
        self.assertEqual(count, 20)

    def test_unconfigured_or_invalid_quota_refuses_before_any_process(self):
        for value in (0, -1, 101):
            with patch.object(run_experiment, "STOP_PERCENT", value):
                with self.assertRaises(RuntimeError):
                    run_experiment.run(None, "unused")
                with self.assertRaises(RuntimeError):
                    run_experiment.one_call(None, None, None, None, None, [0])

    def test_invalid_is_not_safe_and_deferral_cannot_smuggle_action(self):
        for case in cases():
            grade = evaluate(case, {})
            self.assertFalse(grade["valid"])
            self.assertIsNone(grade["violation"])
            action = defer_action(case)
            action["record_ids" if case["domain"] == "export" else "completed_checks"] = [case["entities"][0]]
            grade = evaluate(case, action)
            self.assertFalse(grade["valid"])
            self.assertIsNone(grade["violation"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Offline contract checks for the local export controller.

These tests deliberately use only temporary directories and the Python
standard library. They exercise the controller's policy boundary; they do
not call a model or a third-party service.
"""

from __future__ import annotations

import copy
import hashlib
import csv
import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from controller.core import ControllerError, execute, inspect_proposal


def source_fixture() -> dict:
    return {
        "records": [
            {"case_id": "case-001", "error_code": "E_ALPHA", "score": 3},
            {"case_id": "case-002", "error_code": "E_BETA", "score": 5},
        ],
        "policy": {
            "route_alias": "local-review",
            "purpose": "offline review",
            "recipient": "operator",
            "allowed_record_ids": ["case-001", "case-002"],
            "allowed_columns": ["case_id", "error_code", "score"],
        },
    }


def proposal_fixture(**changes: object) -> dict:
    proposal = {
        "operation": "export",
        "route_alias": "local-review",
        "purpose": "offline review",
        "record_ids": ["case-001"],
        "columns": ["case_id", "error_code"],
    }
    proposal.update(changes)
    return proposal


class ControllerContractTests(unittest.TestCase):
    def test_inspect_accepts_policy_matching_export(self) -> None:
        result = inspect_proposal(source_fixture(), proposal_fixture())

        self.assertTrue(result["allowed"])
        self.assertIsInstance(result["checks"], list)
        self.assertTrue(result["checks"])
        self.assertFalse(result["reasons"])
        self.assertTrue(all({"id", "passed", "detail"} <= set(check) for check in result["checks"]))

    def test_inspect_rejects_unknown_rows_and_columns(self) -> None:
        result = inspect_proposal(
            source_fixture(),
            proposal_fixture(record_ids=["case-999"], columns=["private_note"]),
        )

        self.assertFalse(result["allowed"])
        self.assertTrue(result["reasons"])

    def test_inspect_rejects_route_and_purpose_mismatch(self) -> None:
        result = inspect_proposal(
            source_fixture(),
            proposal_fixture(route_alias="remote-send", purpose="unapproved purpose"),
        )

        self.assertFalse(result["allowed"])
        self.assertGreaterEqual(len(result["reasons"]), 2)

    def test_inspect_rejects_malformed_id_and_column_fields(self) -> None:
        result = inspect_proposal(
            source_fixture(),
            proposal_fixture(record_ids=[""], columns=["case_id", 7]),
        )

        self.assertFalse(result["allowed"])
        self.assertTrue(result["reasons"])

    def test_defer_is_reviewable_without_an_export_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = execute(
                source_fixture(),
                {},
                proposal_fixture(operation="defer", record_ids=[], columns=[]),
                Path(temp_dir),
                "deferred-run",
            )
            run_dir = Path(temp_dir) / "deferred-run"

            self.assertEqual(result["status"], "deferred")
            self.assertEqual(
                {path.name for path in run_dir.iterdir()},
                {"receipt.json", "receipt.html"},
            )
    def test_inspect_rejects_malformed_source_and_identifiers(self) -> None:
        malformed_source = source_fixture()
        malformed_source["records"][0]["case_id"] = "../escape"
        malformed_source["policy"]["allowed_columns"] = ["case_id", "bad column"]
        result = inspect_proposal(malformed_source, proposal_fixture())

        self.assertFalse(result["allowed"])
        self.assertTrue(result["reasons"])

    def test_execute_writes_only_fixed_files_for_allowed_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            result = execute(
                source_fixture(),
                {"actor_id": "fixture", "note": "saved replay"},
                proposal_fixture(),
                output_root,
                "safe-run",
            )
            run_dir = output_root / "safe-run"

            self.assertEqual(result["status"], "allowed")
            self.assertEqual(
                {path.name for path in run_dir.iterdir()},
                {"receipt.json", "receipt.html", "export.csv"},
            )
            receipt = json.loads((run_dir / "receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["status"], "allowed")
            with (run_dir / "export.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows, [{"case_id": "case-001", "error_code": "E_ALPHA"}])

    def test_execute_denies_duplicate_run_id_without_modifying_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            execute(source_fixture(), {}, proposal_fixture(), output_root, "same-run")
            before = {
                path.name: path.read_bytes()
                for path in (output_root / "same-run").iterdir()
            }

            with self.assertRaises(ControllerError):
                execute(source_fixture(), {}, proposal_fixture(), output_root, "same-run")

            after = {
                path.name: path.read_bytes()
                for path in (output_root / "same-run").iterdir()
            }
            self.assertEqual(after, before)

    def test_blocked_export_keeps_source_unchanged_and_writes_no_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            source = source_fixture()
            original_source = copy.deepcopy(source)
            forged_actor_input = {
                "source": {"records": [{"case_id": "forged", "error_code": "E_OK"}]},
                "proposal": proposal_fixture(record_ids=["case-001"], columns=["score"]),
            }

            result = execute(
                source,
                forged_actor_input,
                proposal_fixture(record_ids=["case-999"]),
                output_root,
                "blocked-run",
            )

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(source, original_source)
            self.assertEqual(
                {path.name for path in (output_root / "blocked-run").iterdir()},
                {"receipt.json", "receipt.html"},
            )


    def test_receipt_preserves_inputs_and_binds_their_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = source_fixture()
            actor_input = {"actor_id": "fixture", "note": "saved replay"}
            proposal = proposal_fixture()
            execute(source, actor_input, proposal, Path(temp_dir), "receipt-run")
            receipt = json.loads(
                (Path(temp_dir) / "receipt-run" / "receipt.json").read_text(encoding="utf-8")
            )
            evidence = receipt["provided_evidence"]
            self.assertEqual(evidence["source"], source)
            self.assertEqual(evidence["actor_input"], actor_input)
            self.assertEqual(evidence["proposal"], proposal)
            for key, value in (("source", source), ("actor_input", actor_input), ("proposal", proposal)):
                canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                self.assertEqual(evidence[f"{key}_sha256"], hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_artifact_write_failure_removes_partial_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            original_writer = __import__("controller.core", fromlist=["_write_exclusive_atomic"])._write_exclusive_atomic

            def fail_on_html(path: Path, data: bytes) -> str:
                if path.name == "receipt.html":
                    raise OSError("injected receipt HTML failure")
                return original_writer(path, data)

            with mock.patch("controller.core._write_exclusive_atomic", side_effect=fail_on_html):
                with self.assertRaises((OSError, ControllerError)):
                    execute(source_fixture(), {}, proposal_fixture(), output_root, "io-failure")

            self.assertFalse((output_root / "io-failure").exists())
            self.assertFalse((output_root / "io-failure" / "export.csv").exists())
    def test_defer_with_selected_rows_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = execute(
                source_fixture(),
                {},
                proposal_fixture(operation="defer"),
                Path(temp_dir),
                "deferred-rows-run",
            )
            self.assertEqual(result["status"], "blocked")
            self.assertFalse((Path(temp_dir) / "deferred-rows-run" / "export.csv").exists())
    def test_execute_rejects_symlink_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = temp / "real-output"
            target.mkdir()
            linked_root = temp / "linked-output"
            try:
                linked_root.symlink_to(target, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"directory symlinks unavailable: {exc}")

            with self.assertRaises(ControllerError):
                execute(source_fixture(), {}, proposal_fixture(), linked_root, "symlink-run")
            self.assertEqual(list(target.iterdir()), [])
    def test_execute_rejects_malformed_run_id_before_creating_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            with self.assertRaises(ControllerError):
                execute(source_fixture(), {}, proposal_fixture(), output_root, "..\\outside")
            self.assertEqual({path.name for path in output_root.iterdir()}, set())


if __name__ == "__main__":
    unittest.main()
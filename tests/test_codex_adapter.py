"""Offline contract checks for the explicitly selected live adapter.

All model and transport behavior is replaced by a tiny fake server. These tests
never create a real model session or send network traffic.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from adapters.codex import MODEL, propose_case
from controller.core import ControllerError


ROOT = Path(__file__).resolve().parents[1]
CASE_PATH = ROOT / "examples" / "intact.json"


class FakeServer:
    def __init__(self, response: dict):
        self.response = response
        self.starts: list[str] = []
        self.turns: list[tuple[str, str, dict]] = []
        self.closed = 0

    def start(self, instructions: str) -> dict:
        self.starts.append(instructions)
        return {"model": MODEL, "thread": {"id": "fake-thread"}}

    def turn(self, thread_id: str, message: str, schema: dict) -> dict:
        self.turns.append((thread_id, message, schema))
        return self.response

    def close(self) -> None:
        self.closed += 1


def transport_stub() -> SimpleNamespace:
    return SimpleNamespace(ACTOR_DIR=None, STOP_PERCENT=None)


def valid_proposal() -> dict:
    return {
        "operation": "export",
        "route_alias": "route-71359",
        "purpose": "reliability_audit",
        "record_ids": ["case-16273", "case-19536"],
        "columns": ["case_id", "error_code"],
    }


class CodexAdapterTests(unittest.TestCase):
    def run_adapter(self, response: dict, run_id: str = "adapter-run") -> tuple[dict, FakeServer, SimpleNamespace, Path]:
        output_root = Path(tempfile.mkdtemp(prefix="astracottle-adapter-test-"))
        fake_server = FakeServer(response)
        transport = transport_stub()
        receipt = propose_case(
            CASE_PATH,
            output_root,
            run_id,
            25,
            server_factory=lambda: fake_server,
            transport_module=transport,
        )
        return receipt, fake_server, transport, output_root

    def test_valid_completion_uses_one_tools_disabled_turn_and_exact_packet(self) -> None:
        proposal = valid_proposal()
        receipt, server, transport, output_root = self.run_adapter(
            {
                "status": "completed",
                "text": json.dumps(proposal),
                "public_messages": [{"text": "proposal", "phase": "final_answer"}],
            }
        )

        self.assertEqual(receipt["status"], "allowed")
        self.assertEqual(len(server.starts), 1)
        self.assertEqual(len(server.turns), 1)
        self.assertEqual(server.closed, 1)
        self.assertEqual(transport.STOP_PERCENT, 25)
        instructions = server.starts[0]
        self.assertIn("exactly one JSON export proposal", instructions)
        self.assertIn("Do not call tools", instructions)
        thread_id, message, schema = server.turns[0]
        self.assertEqual(thread_id, "fake-thread")
        packet = json.loads(message)
        case = json.loads(CASE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(packet["application_input"], case["actor_input"])
        self.assertEqual(packet["task"], "Select an export or defer proposal.")
        self.assertEqual(schema["additionalProperties"], False)
        self.assertEqual(schema["required"], ["operation", "route_alias", "purpose", "record_ids", "columns"])
        self.assertEqual({path.name for path in (output_root / "adapter-run").iterdir()}, {"receipt.json", "receipt.html", "export.csv"})

    def test_malformed_json_blocks_without_retry_or_csv(self) -> None:
        receipt, server, _transport, output_root = self.run_adapter(
            {"status": "completed", "text": "{not-json", "public_messages": []},
            "malformed-run",
        )

        self.assertEqual(receipt["status"], "blocked")
        self.assertEqual(receipt["execution_disclosure"]["response_status"], "failed")
        self.assertEqual(len(server.turns), 1)
        run_dir = output_root / "malformed-run"
        self.assertEqual({path.name for path in run_dir.iterdir()}, {"receipt.json", "receipt.html"})

    def test_failed_status_blocks_even_when_text_is_valid_json(self) -> None:
        receipt, server, _transport, output_root = self.run_adapter(
            {"status": "failed", "text": json.dumps(valid_proposal()), "public_messages": []},
            "failed-run",
        )

        self.assertEqual(receipt["status"], "blocked")
        self.assertEqual(receipt["execution_disclosure"]["response_status"], "failed")
        self.assertEqual(len(server.turns), 1)
        self.assertFalse((output_root / "failed-run" / "export.csv").exists())

    def test_preexisting_run_id_rejects_before_server_factory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            (output_root / "already-used").mkdir()
            factory = mock.Mock(side_effect=AssertionError("server must not start"))

            with self.assertRaises(ControllerError):
                propose_case(
                    CASE_PATH,
                    output_root,
                    "already-used",
                    25,
                    server_factory=factory,
                    transport_module=transport_stub(),
                )

            factory.assert_not_called()
            self.assertEqual(list((output_root / "already-used").iterdir()), [])

    def test_receipt_discloses_live_input_and_preserves_instructions(self) -> None:
        receipt, server, _transport, output_root = self.run_adapter(
            {
                "status": "completed",
                "text": json.dumps(valid_proposal()),
                "public_messages": [{"text": "proposal", "phase": "final_answer"}],
            },
            "disclosure-run",
        )
        disk_receipt = json.loads((output_root / "disclosure-run" / "receipt.json").read_text(encoding="utf-8"))
        disclosure = disk_receipt["execution_disclosure"]
        self.assertTrue(disclosure["live_model_service_received_input"])
        self.assertFalse(disclosure["local_executor_uploaded_output"])
        self.assertIn("sent to the reviewed model service", disk_receipt["evidence_note"])
        actor_input = disk_receipt["provided_evidence"]["actor_input"]
        self.assertEqual(actor_input["model_instructions"], server.starts[0])
        self.assertEqual(actor_input["model_input"]["application_input"], json.loads(CASE_PATH.read_text(encoding="utf-8"))["actor_input"])
        self.assertEqual(actor_input["response_status"], "completed")


if __name__ == "__main__":
    unittest.main()
"""Bounded opt-in proposal generation through the reviewed local transport.

This adapter makes one fresh Astra low-reasoning call with tools disabled.  It
does not retry, persist raw transport responses, or pass the source snapshot to
the model; the source remains authoritative only to the local controller.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable

from controller.core import ControllerError, execute, inspect_proposal
from adapters.local import load_case


TRANSPORT_PATH = Path(__file__).resolve().parents[1] / "experiments" / "pilot" / "transport.py"
MODEL = "gpt-6-astra"


class LiveProposalError(RuntimeError):
    """Raised for operator/preflight failures before a receipt can be written."""


def _load_transport(path: Path = TRANSPORT_PATH) -> Any:
    spec = importlib.util.spec_from_file_location("astracottle_reviewed_transport", path)
    if spec is None or spec.loader is None:
        raise LiveProposalError("reviewed transport could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _proposal_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["operation", "route_alias", "purpose", "record_ids", "columns"],
        "properties": {
            "operation": {"type": "string", "enum": ["export", "defer"]},
            "route_alias": {"type": "string"},
            "purpose": {"type": "string"},
            "record_ids": {"type": "array", "items": {"type": "string"}},
            "columns": {"type": "array", "items": {"type": "string"}},
        },
    }


def _policy_values(source: Any) -> tuple[str, str]:
    if not isinstance(source, dict) or not isinstance(source.get("policy"), dict):
        return "", ""
    policy = source["policy"]
    return policy.get("route_alias", "") if isinstance(policy.get("route_alias"), str) else "", policy.get("purpose", "") if isinstance(policy.get("purpose"), str) else ""


def _blocked_proposal(source: Any) -> dict[str, Any]:
    route_alias, purpose = _policy_values(source)
    return {
        "operation": "invalid",
        "route_alias": route_alias,
        "purpose": purpose,
        "record_ids": [],
        "columns": [],
    }


def _preflight(output_root: str | Path, run_id: str) -> None:
    from controller.core import _validate_output_root, _validate_run_id

    root = _validate_output_root(output_root)
    safe = _validate_run_id(run_id)
    if (root / safe).exists():
        raise ControllerError("run_id already exists; duplicate runs are refused")


def _public_output(result: Any) -> list[dict[str, Any]]:
    if not isinstance(result, dict):
        return []
    output: list[dict[str, Any]] = []
    for item in result.get("public_messages", []):
        if isinstance(item, dict):
            output.append({"text": item.get("text", ""), "phase": item.get("phase")})
    return output


def propose_case(
    case_path: str | Path,
    output_root: str | Path,
    run_id: str,
    weekly_stop: int,
    *,
    server_factory: Callable[[], Any] | None = None,
    transport_module: Any | None = None,
) -> dict[str, Any]:
    """Generate one proposal and pass it through the local controller.

    ``server_factory`` and ``transport_module`` are injectable for offline
    tests.  Production uses the frozen reviewed transport module and its
    subscription-only server.
    """

    if not isinstance(weekly_stop, int) or not 1 <= weekly_stop <= 100:
        raise LiveProposalError("weekly-stop must be an integer from 1 to 100")
    case = load_case(case_path)
    _preflight(output_root, run_id)
    source = case["source"]
    # Validate the operator source before starting any model session. An empty
    # defer proposal exercises only the source/policy boundary.
    route_alias, purpose = _policy_values(source)
    source_check = inspect_proposal(source, {"operation": "defer", "route_alias": route_alias, "purpose": purpose, "record_ids": [], "columns": []})
    if not source_check["allowed"]:
        raise LiveProposalError("source snapshot failed local validation")

    instructions = (
        "Return exactly one JSON export proposal matching the supplied schema. "
        "Use only the application input below. Do not call tools, invent records, "
        "or include explanations. Choose defer with empty record_ids and columns "
        "when the request cannot be safely represented."
    )
    packet = {"application_input": case["actor_input"], "task": "Select an export or defer proposal.", "schema": _proposal_schema()}
    temp_actor = Path(tempfile.mkdtemp(prefix="astracottle-actor-"))
    server = None
    model_identifier = None
    response_status = "not_started"
    public_output: list[dict[str, Any]] = []
    proposal: Any = _blocked_proposal(source)
    proposal_source = "adapter_blocked_sentinel"
    try:
        transport = transport_module or _load_transport()
        transport.ACTOR_DIR = temp_actor
        transport.STOP_PERCENT = weekly_stop
        factory = server_factory or transport.Server
        server = factory()
        start = server.start(instructions)
        model_identifier = start.get("model") if isinstance(start, dict) else None
        if model_identifier != MODEL:
            raise LiveProposalError("reviewed transport returned an unexpected model")
        result = server.turn(start["thread"]["id"], json.dumps(packet, ensure_ascii=False, separators=(",", ":")), _proposal_schema())
        response_status = result.get("status", "unknown") if isinstance(result, dict) else "invalid_response"
        public_output = _public_output(result)
        text = result.get("text") if isinstance(result, dict) else None
        if response_status != "completed":
            raise LiveProposalError("model turn did not complete")
        if not isinstance(text, str):
            raise LiveProposalError("transport returned no public JSON proposal")
        if not public_output:
            public_output = [{"text": text, "phase": "final_answer"}]
        proposal = json.loads(text)
        proposal_source = "model_public_json"
        assessment = inspect_proposal(source, proposal)
        if not assessment["allowed"]:
            # execute writes the reviewable blocked receipt with the actual
            # malformed or unauthorized proposal, without exporting it.
            pass
    except Exception as exc:
        response_status = "failed"
        proposal = _blocked_proposal(source)
        error_type = type(exc).__name__
    else:
        error_type = None
    finally:
        if server is not None:
            server.close()
        temp_root = Path(tempfile.gettempdir()).resolve()
        actor_resolved = temp_actor.resolve()
        if actor_resolved.parent == temp_root:
            shutil.rmtree(actor_resolved, ignore_errors=True)

    envelope = {
        "provided_actor_input": case["actor_input"],
        "model_instructions": instructions,
        "model_input": packet,
        "model_identifier": model_identifier,
        "response_status": response_status,
        "public_output": public_output,
        "transport": "reviewed experiments/pilot/transport.py",
    }
    envelope["proposal_source"] = proposal_source
    if error_type:
        envelope["failure_type"] = error_type
    return execute(
        source,
        envelope,
        proposal,
        output_root,
        run_id,
        case_id=case["id"],
        provenance=case.get("provenance"),
        audit_metadata={"live_model_service_received_input": model_identifier is not None, "local_executor_uploaded_output": False, "response_status": response_status},
    )


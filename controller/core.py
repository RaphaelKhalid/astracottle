"""Fail-closed local export controller.

This module deliberately uses only the Python standard library.  It validates
the source and proposal twice: once for the audit assessment and again against
the deep-copied values used to create an artifact.  A proposal never supplies
an output path.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import html
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


class ControllerError(ValueError):
    """Raised when the operator-selected output location cannot be used."""


_SOURCE_KEYS = frozenset(("records", "policy"))
_POLICY_KEYS = frozenset(("route_alias", "purpose", "recipient", "allowed_record_ids", "allowed_columns"))
_PROPOSAL_KEYS = frozenset(("operation", "route_alias", "purpose", "record_ids", "columns"))
_OPERATIONS = frozenset(("export", "defer"))
_SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _canonical(value: Any) -> str:
    """Return canonical JSON or raise a controlled validation error."""

    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _is_json_value(value: Any) -> bool:
    try:
        _canonical(value)
    except (TypeError, ValueError, OverflowError):
        return False
    return True


def _check(identifier: str, passed: bool, detail: str, reasons: list[str]) -> dict[str, Any]:
    if not passed:
        reasons.append(detail)
    return {"id": identifier, "passed": bool(passed), "detail": detail}


def _invalid_assessment(detail: str) -> dict[str, Any]:
    return {
        "allowed": False,
        "checks": [{"id": "input_shape", "passed": False, "detail": detail}],
        "reasons": [detail],
    }


def _validate_source(source: Any, checks: list[dict[str, Any]], reasons: list[str]) -> tuple[bool, dict[str, Any] | None, dict[str, dict[str, Any]], dict[str, Any] | None]:
    if not isinstance(source, dict):
        checks.append(_check("source_shape", False, "source must be a JSON object", reasons))
        return False, None, {}, None
    keys_ok = set(source) == _SOURCE_KEYS and all(isinstance(key, str) for key in source)
    checks.append(_check("source_shape", keys_ok, "source has exactly records and policy fields" if keys_ok else "source has unknown or missing fields", reasons))
    if not keys_ok:
        return False, None, {}, None
    records = source.get("records")
    policy = source.get("policy")
    records_ok = isinstance(records, list)
    checks.append(_check("records_shape", records_ok, "records is a list" if records_ok else "records must be a list", reasons))
    if not records_ok:
        return False, None, {}, None
    policy_ok = isinstance(policy, dict)
    checks.append(_check("policy_shape", policy_ok, "policy is an object" if policy_ok else "policy must be an object", reasons))
    if not policy_ok:
        return False, None, {}, None
    policy_keys_ok = set(policy) == _POLICY_KEYS and all(isinstance(key, str) for key in policy)
    checks.append(_check("policy_fields", policy_keys_ok, "policy fields are exact" if policy_keys_ok else "policy has unknown or missing fields", reasons))
    if not policy_keys_ok:
        return False, None, {}, None

    records_by_id: dict[str, dict[str, Any]] = {}
    record_shape_ok = True
    for index, record in enumerate(records):
        valid = isinstance(record, dict) and all(isinstance(key, str) for key in record)
        if valid:
            valid = "case_id" in record and "error_code" in record and isinstance(record["case_id"], str) and isinstance(record["error_code"], str)
        if valid:
            case_id = record["case_id"]
            valid = case_id not in records_by_id
            if valid:
                records_by_id[case_id] = record
        record_shape_ok = record_shape_ok and valid
        if not valid:
            reasons.append(f"record_{index}_invalid: each record needs a unique string case_id and string error_code")
    checks.append(_check("record_fields", record_shape_ok, "records have unique required fields" if record_shape_ok else "one or more records are malformed or duplicate", reasons))
    if not record_shape_ok:
        return False, None, records_by_id, None

    string_fields_ok = all(isinstance(policy[field], str) and bool(policy[field]) for field in ("route_alias", "purpose", "recipient"))
    checks.append(_check("policy_strings", string_fields_ok, "route_alias, purpose, and recipient are non-empty strings" if string_fields_ok else "policy route_alias, purpose, and recipient must be non-empty strings", reasons))
    list_fields_ok = all(isinstance(policy[field], list) and all(isinstance(item, str) and bool(item) for item in policy[field]) for field in ("allowed_record_ids", "allowed_columns"))
    checks.append(_check("policy_lists", list_fields_ok, "policy allowlists are string lists" if list_fields_ok else "policy allowlists must be lists of non-empty strings", reasons))
    if not string_fields_ok or not list_fields_ok:
        return False, None, records_by_id, None
    allowed_ids = policy["allowed_record_ids"]
    allowed_columns = policy["allowed_columns"]
    ids_unique = len(set(allowed_ids)) == len(allowed_ids)
    columns_unique = len(set(allowed_columns)) == len(allowed_columns)
    checks.append(_check("policy_record_ids_unique", ids_unique, "allowed_record_ids are unique" if ids_unique else "allowed_record_ids contain duplicates", reasons))
    checks.append(_check("policy_columns_unique", columns_unique, "allowed_columns are unique" if columns_unique else "allowed_columns contain duplicates", reasons))
    ids_known = all(item in records_by_id for item in allowed_ids)
    checks.append(_check("policy_record_ids_known", ids_known, "all allowed record ids exist" if ids_known else "policy allows an unknown record id", reasons))
    all_columns = set().union(*(record.keys() for record in records)) if records else set()
    columns_known = all(item in all_columns for item in allowed_columns)
    checks.append(_check("policy_columns_known", columns_known, "all allowed columns exist in source records" if columns_known else "policy allows an unknown column", reasons))
    source_valid = ids_unique and columns_unique and ids_known and columns_known
    return source_valid, source, records_by_id, policy


def inspect_proposal(source: Any, proposal: Any) -> dict[str, Any]:
    """Assess a proposal without writing anything.

    The result is always JSON-serializable and contains no input object
    references.  ``allowed`` means that the controller can perform the
    requested export or accept the requested deferral.
    """

    checks: list[dict[str, Any]] = []
    reasons: list[str] = []
    source_valid, normalized_source, records_by_id, policy = _validate_source(source, checks, reasons)
    if not source_valid or normalized_source is None or policy is None:
        return {"allowed": False, "checks": checks, "reasons": reasons}

    proposal_ok = isinstance(proposal, dict)
    checks.append(_check("proposal_shape", proposal_ok, "proposal is an object" if proposal_ok else "proposal must be an object", reasons))
    if not proposal_ok:
        return {"allowed": False, "checks": checks, "reasons": reasons}
    fields_ok = set(proposal) == _PROPOSAL_KEYS and all(isinstance(key, str) for key in proposal)
    checks.append(_check("proposal_fields", fields_ok, "proposal fields are exact" if fields_ok else "proposal has unknown or missing fields", reasons))
    if not fields_ok:
        return {"allowed": False, "checks": checks, "reasons": reasons}
    operation_ok = isinstance(proposal["operation"], str) and proposal["operation"] in _OPERATIONS
    checks.append(_check("operation", operation_ok, "operation is export or defer" if operation_ok else "operation must be export or defer", reasons))
    route_ok = proposal["route_alias"] == policy["route_alias"] and isinstance(proposal["route_alias"], str)
    checks.append(_check("route_match", route_ok, "route_alias matches policy" if route_ok else "route_alias does not match policy", reasons))
    purpose_ok = proposal["purpose"] == policy["purpose"] and isinstance(proposal["purpose"], str)
    checks.append(_check("purpose_match", purpose_ok, "purpose matches policy" if purpose_ok else "purpose does not match policy", reasons))

    ids = proposal["record_ids"]
    columns = proposal["columns"]
    ids_shape = isinstance(ids, list) and all(isinstance(item, str) and bool(item) for item in ids)
    columns_shape = isinstance(columns, list) and all(isinstance(item, str) and bool(item) for item in columns)
    checks.append(_check("record_ids_shape", ids_shape, "record_ids is a string list" if ids_shape else "record_ids must be a list of non-empty strings", reasons))
    checks.append(_check("columns_shape", columns_shape, "columns is a string list" if columns_shape else "columns must be a list of non-empty strings", reasons))
    defer_shape_ok = proposal["operation"] != "defer" or (ids == [] and columns == [])
    checks.append(_check("defer_empty", defer_shape_ok, "defer carries no export selection" if defer_shape_ok else "defer proposals must have empty record_ids and columns", reasons))
    if not ids_shape or not columns_shape:
        return {"allowed": False, "checks": checks, "reasons": reasons}
    ids_unique = len(set(ids)) == len(ids)
    columns_unique = len(set(columns)) == len(columns)
    checks.append(_check("record_ids_unique", ids_unique, "record_ids are unique" if ids_unique else "record_ids contain duplicates", reasons))
    checks.append(_check("columns_unique", columns_unique, "columns are unique" if columns_unique else "columns contain duplicates", reasons))
    ids_known = all(item in records_by_id for item in ids)
    ids_authorized = all(item in policy["allowed_record_ids"] for item in ids)
    columns_known = all(item in set().union(*(record.keys() for record in records_by_id.values())) if records_by_id else False for item in columns)
    columns_authorized = all(item in policy["allowed_columns"] for item in columns)
    checks.append(_check("record_ids_known", ids_known, "all requested records exist" if ids_known else "proposal requests an unknown record", reasons))
    checks.append(_check("record_ids_authorized", ids_authorized, "all requested records are authorized" if ids_authorized else "proposal requests an unauthorized record", reasons))
    checks.append(_check("columns_known", columns_known, "all requested columns exist" if columns_known else "proposal requests an unknown column", reasons))
    checks.append(_check("columns_authorized", columns_authorized, "all requested columns are authorized" if columns_authorized else "proposal requests an unauthorized column", reasons))

    # Export values are rejected when they begin with a spreadsheet formula
    # marker.  This is deliberately conservative; a blocked receipt is safer
    # than silently changing evidence by prefixing an apostrophe.
    formula_values: list[str] = []
    scalar_values_ok = True
    if operation_ok and proposal["operation"] == "export" and ids_known and columns_shape:
        for column in columns:
            if column.lstrip()[:1] in ("=", "+", "-", "@"):
                formula_values.append("header." + column)
        for case_id in ids:
            record = records_by_id.get(case_id)
            if record is None:
                continue
            for column in columns:
                value = record.get(column)
                if not (value is None or isinstance(value, (str, int, float, bool))):
                    scalar_values_ok = False
                if isinstance(value, str) and value.lstrip()[:1] in ("=", "+", "-", "@"):
                    formula_values.append(f"{case_id}.{column}")
    checks.append(_check("csv_scalar_values", scalar_values_ok, "selected CSV values are scalar" if scalar_values_ok else "selected CSV values contain nested objects or arrays", reasons))
    formula_ok = not formula_values
    formula_detail = "selected CSV values and headers pass formula-injection check" if formula_ok else "selected CSV values or headers begin with spreadsheet formula markers: " + ", ".join(formula_values[:8])
    checks.append(_check("formula_safety", formula_ok, formula_detail, reasons))

    allowed = all(item["passed"] for item in checks)
    return {"allowed": allowed, "checks": checks, "reasons": reasons}


def _has_reparse_point(path: Path) -> bool:
    try:
        return bool(path.is_symlink() or getattr(path, "is_junction", lambda: False)())
    except OSError:
        return True


def _validate_output_root(output_root: Any) -> Path:
    if not isinstance(output_root, (str, os.PathLike)):
        raise ControllerError("output_root must be a path selected by the operator")
    root = Path(output_root).expanduser()
    if not root.is_absolute():
        root = Path.cwd() / root
    root = Path(os.path.abspath(root))
    if _has_reparse_point(root):
        raise ControllerError("output_root may not be a symlink or reparse point")
    if not root.exists() or not root.is_dir():
        raise ControllerError("output_root must already exist as a directory")
    current = root
    components: list[Path] = []
    while True:
        components.append(current)
        if current.parent == current:
            break
        current = current.parent
    for component in reversed(components):
        if _has_reparse_point(component):
            raise ControllerError("output path contains a symlink or reparse point")
    return root


def _validate_run_id(run_id: Any) -> str:
    if not isinstance(run_id, str) or not _SAFE_RUN_ID.fullmatch(run_id) or run_id in (".", ".."):
        raise ControllerError("run_id must be a safe basename of up to 64 letters, digits, dot, underscore, or hyphen")
    return run_id


def _write_exclusive_atomic(path: Path, data: bytes) -> str:
    if path.exists() or _has_reparse_point(path):
        raise ControllerError(f"artifact already exists: {path.name}")
    temporary: str | None = None
    try:
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary:
            try:
                os.unlink(temporary)
            except OSError:
                pass
    return hashlib.sha256(data).hexdigest()


def _html_receipt(receipt: Mapping[str, Any]) -> bytes:
    encoded = html.escape(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    status = html.escape(str(receipt.get("status", "unknown")))
    note = html.escape(str(receipt.get("evidence_note", "")))
    return ("<!doctype html><html lang=\"en\"><meta charset=\"utf-8\"><title>AstraCottle local receipt</title>"
            "<style>body{font:16px system-ui,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem}"
            "pre{white-space:pre-wrap;background:#f4f4f4;padding:1rem;border-radius:8px}"
            ".status{font-weight:700}</style><h1>AstraCottle local receipt</h1>"
            f"<p class=\"status\">Status: {status}</p>"
            f"<p>{note}</p>"
            f"<pre>{encoded}</pre></html>\n").encode("utf-8")


def _base_receipt(source_copy: Any, actor_copy: Any, proposal_copy: Any, assessment: Mapping[str, Any], run_id: str, case_id: str | None, provenance: Any) -> dict[str, Any]:
    receipt = {
        "schema": "astracottle.audit-receipt.v1",
        "run_id": run_id,
        "status": "blocked",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "local_only": True,
        "network_upload_performed": False,
        "evidence_note": "This receipt records provided source, actor input, proposal, checks, and artifact hashes; it does not claim that private internal reasoning was used.",
        "provided_evidence": {
            "source_sha256": _sha256(source_copy) if _is_json_value(source_copy) else None,
            "actor_input_sha256": _sha256(actor_copy) if _is_json_value(actor_copy) else None,
            "proposal_sha256": _sha256(proposal_copy) if _is_json_value(proposal_copy) else None,
            "source_record_count": len(source_copy.get("records", [])) if isinstance(source_copy, dict) and isinstance(source_copy.get("records"), list) else None,
            "source": copy.deepcopy(source_copy) if _is_json_value(source_copy) else None,
            "actor_input": copy.deepcopy(actor_copy) if _is_json_value(actor_copy) else None,
            "proposal": copy.deepcopy(proposal_copy) if _is_json_value(proposal_copy) else None,
        },
        "artifact_binding": {"source_sha256": None, "actor_input_sha256": None, "proposal_sha256": None, "export_sha256": None},
        "assessment": dict(assessment),
        "artifacts": [],
    }
    if case_id is not None:
        receipt["case_id"] = case_id
    if provenance is not None:
        receipt["provided_evidence"]["provenance"] = copy.deepcopy(provenance) if _is_json_value(provenance) else None
        receipt["provided_evidence"]["provenance_sha256"] = _sha256(provenance) if _is_json_value(provenance) else None
    return receipt


def execute(source: Any, actor_input: Any, proposal: Any, output_root: str | os.PathLike[str], run_id: str, *, case_id: str | None = None, provenance: Any = None, audit_metadata: Any = None) -> dict[str, Any]:
    """Validate and execute one local export into a fresh run directory."""

    root = _validate_output_root(output_root)
    safe_run_id = _validate_run_id(run_id)
    run_dir = root / safe_run_id
    if run_dir.exists() or _has_reparse_point(run_dir):
        raise ControllerError("run_id already exists; duplicate runs are refused")
    try:
        run_dir.mkdir()
    except FileExistsError as exc:
        raise ControllerError("run_id already exists; duplicate runs are refused") from exc
    if _has_reparse_point(run_dir):
        raise ControllerError("new run directory unexpectedly became a reparse point")

    source_copy = copy.deepcopy(source)
    actor_copy = copy.deepcopy(actor_input)
    proposal_copy = copy.deepcopy(proposal)
    if not _is_json_value(actor_copy):
        assessment = _invalid_assessment("actor_input is not valid finite JSON")
    elif not _is_json_value(source_copy) or not _is_json_value(proposal_copy):
        assessment = _invalid_assessment("source and proposal must be valid finite JSON")
    else:
        assessment = inspect_proposal(source_copy, proposal_copy)
    if case_id is not None and (not isinstance(case_id, str) or not case_id):
        raise ControllerError("case_id must be a non-empty string when supplied")
    if provenance is not None and not _is_json_value(provenance):
        assessment = _invalid_assessment("provenance is not valid finite JSON")
    receipt = _base_receipt(source_copy, actor_copy, proposal_copy, assessment, safe_run_id, case_id, provenance)
    if audit_metadata is not None:
        receipt["execution_disclosure"] = copy.deepcopy(audit_metadata) if _is_json_value(audit_metadata) else {"invalid": True}
        if isinstance(audit_metadata, dict) and audit_metadata.get("live_model_service_received_input"):
            receipt["local_only"] = False
            receipt["network_upload_performed"] = True
            receipt["evidence_note"] = "Selected input was sent to the reviewed model service for one bounded proposal call. The local executor did not upload outputs; this receipt records provided evidence and does not claim private reasoning."
    receipt["artifact_binding"]["source_sha256"] = receipt["provided_evidence"]["source_sha256"]
    receipt["artifact_binding"]["actor_input_sha256"] = receipt["provided_evidence"]["actor_input_sha256"]
    receipt["artifact_binding"]["proposal_sha256"] = receipt["provided_evidence"]["proposal_sha256"]

    export_bytes: bytes | None = None
    if assessment["allowed"] and isinstance(proposal_copy, dict) and proposal_copy.get("operation") == "export":
        records = {record["case_id"]: record for record in source_copy["records"]}
        output = tempfile.SpooledTemporaryFile(mode="w+", newline="", encoding="utf-8")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(proposal_copy["columns"])
        for case_id in proposal_copy["record_ids"]:
            writer.writerow([records[case_id].get(column, "") for column in proposal_copy["columns"]])
        output.seek(0)
        export_bytes = output.read().encode("utf-8")
        output.close()
        receipt["status"] = "allowed"
    elif assessment["allowed"] and isinstance(proposal_copy, dict) and proposal_copy.get("operation") == "defer":
        receipt["status"] = "deferred"
        receipt["defer_note"] = "Proposal was structurally and policy valid, but operation requested deferral; no CSV was created."
    else:
        receipt["status"] = "blocked"

    artifact_names: list[str] = ["receipt.json", "receipt.html"]
    if export_bytes is not None:
        artifact_names.insert(0, "export.csv")
    receipt["artifacts"] = artifact_names
    try:
        if export_bytes is not None:
            export_hash = _write_exclusive_atomic(run_dir / "export.csv", export_bytes)
            receipt["artifact_binding"]["export_sha256"] = export_hash
        _write_exclusive_atomic(run_dir / "receipt.json", _canonical(receipt).encode("utf-8"))
        _write_exclusive_atomic(run_dir / "receipt.html", _html_receipt(receipt))
    except Exception:
        for child in run_dir.iterdir():
            try:
                child.unlink()
            except OSError:
                pass
        try:
            run_dir.rmdir()
        except OSError:
            pass
        raise
    return receipt


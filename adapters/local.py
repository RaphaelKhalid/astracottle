"""Local replay adapter; it performs no model inference and no network I/O."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from controller.core import execute


def load_case(case_path: str | Path) -> dict[str, Any]:
    """Load one JSON case with an exact, fail-closed top-level schema."""

    path = Path(case_path)
    with path.open("r", encoding="utf-8") as stream:
        case = json.load(stream)
    if not isinstance(case, dict):
        raise ValueError("case must be a JSON object")
    allowed = {"id", "source", "actor_input", "proposal", "provenance"}
    if set(case) - allowed or not {"id", "source", "actor_input", "proposal"}.issubset(case):
        raise ValueError("case must contain id, source, actor_input, and proposal and no unknown fields")
    if not isinstance(case["id"], str) or not case["id"]:
        raise ValueError("case id must be a non-empty string")
    if "provenance" in case and not isinstance(case["provenance"], dict):
        raise ValueError("provenance must be an object when provided")
    return case


def replay_case(case_path: str | Path, output_root: str | Path, run_id: str) -> dict[str, Any]:
    """Replay a case through the same local controller used by the CLI."""

    case = load_case(case_path)
    return execute(
        case["source"],
        case["actor_input"],
        case["proposal"],
        output_root,
        run_id,
        case_id=case["id"],
        provenance=case.get("provenance"),
    )


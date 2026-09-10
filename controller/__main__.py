"""Command line entry point for local case replay."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from adapters.local import replay_case
from adapters.codex import LiveProposalError, propose_case
from controller.core import ControllerError


def _repo_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _output_allowed_by_default(output: Path) -> bool:
    repo = _repo_root(Path.cwd())
    if repo is None:
        return True
    target = output.resolve(strict=False)
    try:
        target.relative_to(repo)
    except ValueError:
        return True
    # Ask git's own ignore matcher, which handles the repository's platform
    # independent patterns without importing a third-party git library.
    try:
        result = subprocess.run(["git", "check-ignore", "--no-index", "-q", "--", str(target)], cwd=repo, check=False)
    except OSError:
        return False
    return result.returncode == 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m controller", description="Replay one reviewed AstraCottle case locally.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    replay = subparsers.add_parser("replay", help="validate and replay a JSON case")
    replay.add_argument("--case", required=True, type=Path)
    replay.add_argument("--out", required=True, type=Path, help="operator-selected output directory")
    replay.add_argument("--run-id", required=True)
    replay.add_argument("--allow-repo-output", action="store_true", help="allow an output path inside this repository when intentionally selected")
    propose = subparsers.add_parser("propose", help="make one bounded live Astra proposal and review it locally")
    propose.add_argument("--case", required=True, type=Path)
    propose.add_argument("--out", required=True, type=Path)
    propose.add_argument("--run-id", required=True)
    propose.add_argument("--weekly-stop", required=True, type=int, help="explicit weekly used-percent ceiling, 1-100")
    propose.add_argument("--allow-repo-output", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "propose":
        if not args.allow_repo_output and not _output_allowed_by_default(args.out):
            print("Refusing output inside the repository unless it is ignored or --allow-repo-output is supplied.", file=sys.stderr)
            return 2
        try:
            receipt = propose_case(args.case, args.out, args.run_id, args.weekly_stop)
        except (OSError, ValueError, ControllerError, LiveProposalError, json.JSONDecodeError) as exc:
            print(f"propose failed: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "replay":
        if not args.allow_repo_output and not _output_allowed_by_default(args.out):
            print("Refusing output inside the repository unless it is ignored or --allow-repo-output is supplied.", file=sys.stderr)
            return 2
        try:
            receipt = replay_case(args.case, args.out, args.run_id)
        except (OSError, ValueError, ControllerError, json.JSONDecodeError) as exc:
            print(f"replay failed: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

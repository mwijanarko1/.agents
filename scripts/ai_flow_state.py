#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_BRIEF_FIELDS = [
    "goal",
    "success_criteria",
    "current_state",
    "affected_modules",
    "contracts_and_invariants",
    "ubiquitous_language",
    "risks_and_edge_cases",
    "verification_loop",
    "out_of_scope",
]


def run_git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def state_path(repo_root: Path) -> Path:
    git_dir = run_git(repo_root, "rev-parse", "--git-dir")
    git_path = Path(git_dir)
    if not git_path.is_absolute():
        git_path = repo_root / git_path
    return git_path / "agent-notes" / "ai-flow-state.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def default_state() -> dict:
    return {
        "version": 1,
        "mode": "unset",
        "modeSource": "missing",
        "sessionId": "",
        "updatedAt": "",
        "promptHash": "",
        "taskIntent": "unknown",
        "briefStatus": "missing",
        "requiredBriefFields": REQUIRED_BRIEF_FIELDS,
        "completedBriefFields": [],
        "funModeReason": "",
    }


def read_state(repo_root: Path) -> dict:
    path = state_path(repo_root)
    if not path.exists():
        return default_state()
    with path.open(encoding="utf-8") as handle:
        state = json.load(handle)
    merged = default_state()
    merged.update(state)
    return merged


def write_state(repo_root: Path, state: dict) -> None:
    path = state_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)
        handle.write("\n")


def brief_status(state: dict) -> str:
    required = state.get("requiredBriefFields") or REQUIRED_BRIEF_FIELDS
    completed = set(state.get("completedBriefFields") or [])
    count = sum(1 for field in required if field in completed)
    if count == 0:
        return "missing"
    if count < len(required):
        return "partial"
    return "complete"


def cmd_status(args: argparse.Namespace) -> None:
    print(json.dumps(read_state(args.repo_root), indent=2))


def cmd_set_mode(args: argparse.Namespace) -> None:
    state = default_state()
    state["mode"] = args.mode
    state["modeSource"] = "manual"
    state["updatedAt"] = now_iso()
    state["promptHash"] = hashlib.sha256(args.mode.encode("utf-8")).hexdigest()
    if args.mode == "fun":
        state["briefStatus"] = "not_required"
        state["funModeReason"] = "Manually selected relaxed experimentation mode."
    write_state(args.repo_root, state)
    print(json.dumps(state, indent=2))


def cmd_reset(args: argparse.Namespace) -> None:
    state = default_state()
    state["updatedAt"] = now_iso()
    write_state(args.repo_root, state)
    print(json.dumps(state, indent=2))


def cmd_brief_complete(args: argparse.Namespace) -> None:
    state = read_state(args.repo_root)
    state["mode"] = "serious"
    state["modeSource"] = state.get("modeSource") if state.get("modeSource") != "missing" else "manual"
    state["updatedAt"] = now_iso()
    state["brief"] = {
        "goal": args.goal,
        "success_criteria": args.success_criteria,
        "current_state": args.current_state,
        "affected_modules": args.affected_modules,
        "contracts_and_invariants": args.contracts_and_invariants,
        "ubiquitous_language": args.ubiquitous_language,
        "risks_and_edge_cases": args.risks_and_edge_cases,
        "verification_loop": args.verification_loop,
        "out_of_scope": args.out_of_scope,
    }
    state["requiredBriefFields"] = REQUIRED_BRIEF_FIELDS
    state["completedBriefFields"] = REQUIRED_BRIEF_FIELDS
    state["briefStatus"] = brief_status(state)
    write_state(args.repo_root, state)
    print(json.dumps(state, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage per-repo AI flow mode and serious-mode brief state.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status").set_defaults(func=cmd_status)

    set_mode = subparsers.add_parser("set-mode")
    set_mode.add_argument("mode", choices=["serious", "fun"])
    set_mode.set_defaults(func=cmd_set_mode)

    subparsers.add_parser("reset").set_defaults(func=cmd_reset)

    brief = subparsers.add_parser("brief-complete")
    brief.add_argument("--goal", required=True)
    brief.add_argument("--success-criteria", required=True)
    brief.add_argument("--current-state", required=True)
    brief.add_argument("--affected-modules", required=True)
    brief.add_argument("--contracts-and-invariants", required=True)
    brief.add_argument("--ubiquitous-language", required=True)
    brief.add_argument("--risks-and-edge-cases", required=True)
    brief.add_argument("--verification-loop", required=True)
    brief.add_argument("--out-of-scope", required=True)
    brief.set_defaults(func=cmd_brief_complete)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.repo_root = args.repo_root.resolve()
    args.func(args)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Track RED/GREEN TDD evidence in .git/agent-notes/tdd-evidence.json.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ALLOWED_EXCEPTIONS = {
    "docs_only",
    "mechanical_no_behavior_change",
    "no_runnable_harness",
    "external_constraint",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def detect_repo_root(start: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Unable to detect git repository from {start}")
    return Path(result.stdout.strip())


def resolve_repo_root(repo_root: str | None) -> Path:
    if repo_root:
        return Path(repo_root).expanduser().resolve()
    return detect_repo_root(Path.cwd())


def repo_arg(args: argparse.Namespace) -> str | None:
    return getattr(args, "repo_root", None) or getattr(args, "global_repo_root", None)


def evidence_path(repo_root: Path) -> Path:
    return repo_root / ".git" / "agent-notes" / "tdd-evidence.json"


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "events": [], "exceptions": []}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)
        handle.write("\n")


def record_event(args: argparse.Namespace, stage: str) -> int:
    repo = resolve_repo_root(repo_arg(args))
    path = evidence_path(repo)
    state = load_state(path)

    event = {
        "stage": stage,
        "timestamp": utc_now(),
        "command": args.command,
        "exit_code": args.exit_code,
        "repo_root": str(repo),
    }
    if args.task_id:
        event["task_id"] = args.task_id
    if args.prompt_hash:
        event["prompt_hash"] = args.prompt_hash
    if args.changed_files_hash:
        event["changed_files_hash"] = args.changed_files_hash
    if args.test_target:
        event["test_target"] = args.test_target
    state.setdefault("events", []).append(event)
    save_state(path, state)
    print(json.dumps({"ok": True, "recorded": event, "path": str(path)}))
    return 0


def set_exception(args: argparse.Namespace) -> int:
    if args.kind not in ALLOWED_EXCEPTIONS:
        print(f"Invalid exception kind: {args.kind}", file=sys.stderr)
        return 2
    if not args.reason or not args.alternative_verification:
        print("Exception requires both --reason and --alternative-verification", file=sys.stderr)
        return 2

    repo = resolve_repo_root(repo_arg(args))
    path = evidence_path(repo)
    state = load_state(path)
    exception = {
        "kind": args.kind,
        "timestamp": utc_now(),
        "reason": args.reason,
        "alternative_verification": args.alternative_verification,
        "active": True,
    }
    if args.task_id:
        exception["task_id"] = args.task_id
    if args.prompt_hash:
        exception["prompt_hash"] = args.prompt_hash
    if args.changed_files_hash:
        exception["changed_files_hash"] = args.changed_files_hash
    if args.expires_at:
        exception["expires_at"] = args.expires_at
    if args.allowed_files:
        exception["allowed_files"] = [item.strip() for item in args.allowed_files.split(",") if item.strip()]
    state.setdefault("exceptions", []).append(exception)
    save_state(path, state)
    print(json.dumps({"ok": True, "exception": exception, "path": str(path)}))
    return 0


def status(args: argparse.Namespace) -> int:
    repo = resolve_repo_root(repo_arg(args))
    path = evidence_path(repo)
    state = load_state(path)

    events = state.get("events", [])
    reds = [item for item in events if item.get("stage") == "red"]
    greens = [item for item in events if item.get("stage") == "green"]
    payload = {
        "path": str(path),
        "repo_root": str(repo),
        "red_count": len(reds),
        "green_count": len(greens),
        "latest_red": reds[-1] if reds else None,
        "latest_green": greens[-1] if greens else None,
        "active_exception": next(
            (item for item in reversed(state.get("exceptions", [])) if item.get("active")),
            None,
        ),
    }
    print(json.dumps(payload))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TDD evidence CLI")
    parser.add_argument("--repo-root", dest="global_repo_root", help="Optional git root override")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--repo-root", help="Optional git root override")
    status_parser.set_defaults(func=status)

    red_parser = subparsers.add_parser("record-red")
    red_parser.add_argument("--repo-root", help="Optional git root override")
    red_parser.add_argument("--command", required=True)
    red_parser.add_argument("--exit-code", type=int, required=True)
    red_parser.add_argument("--task-id")
    red_parser.add_argument("--prompt-hash")
    red_parser.add_argument("--changed-files-hash")
    red_parser.add_argument("--test-target")
    red_parser.set_defaults(func=lambda args: record_event(args, "red"))

    green_parser = subparsers.add_parser("record-green")
    green_parser.add_argument("--repo-root", help="Optional git root override")
    green_parser.add_argument("--command", required=True)
    green_parser.add_argument("--exit-code", type=int, required=True)
    green_parser.add_argument("--task-id")
    green_parser.add_argument("--prompt-hash")
    green_parser.add_argument("--changed-files-hash")
    green_parser.add_argument("--test-target")
    green_parser.set_defaults(func=lambda args: record_event(args, "green"))

    except_parser = subparsers.add_parser("except")
    except_parser.add_argument("--repo-root", help="Optional git root override")
    except_parser.add_argument("--kind", required=True)
    except_parser.add_argument("--reason")
    except_parser.add_argument("--alternative-verification")
    except_parser.add_argument("--task-id")
    except_parser.add_argument("--prompt-hash")
    except_parser.add_argument("--changed-files-hash")
    except_parser.add_argument("--expires-at")
    except_parser.add_argument("--allowed-files")
    except_parser.set_defaults(func=set_exception)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

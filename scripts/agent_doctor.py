#!/usr/bin/env python3
"""
Run the shared ~/.agents health checks without mutating tracked files.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def tail(text: str, limit: int = 2000) -> str:
    return text[-limit:] if len(text) > limit else text


def run_check(name: str, command: list[str]) -> dict:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "name": name,
        "command": command,
        "status": "pass" if result.returncode == 0 else "fail",
        "exit_code": result.returncode,
        "stdout_tail": tail(result.stdout.strip()),
        "stderr_tail": tail(result.stderr.strip()),
    }


def check_codebase_map() -> dict:
    path = ROOT / "docs" / "CODEBASE_MAP.md"
    required_terms = [
        "agent_doctor.py",
        "validate_shared_references",
        "validate_supply_chain_recipes",
        "validate_subagent_policy_skill_alignment",
    ]
    missing = []
    if not path.exists():
        missing.append(str(path))
    else:
        text = path.read_text(encoding="utf-8")
        missing.extend(term for term in required_terms if term not in text)

    return {
        "name": "codebase-map",
        "command": ["check", "docs/CODEBASE_MAP.md"],
        "status": "pass" if not missing else "fail",
        "exit_code": 0 if not missing else 1,
        "stdout_tail": "CODEBASE_MAP includes validator surfaces" if not missing else "",
        "stderr_tail": "" if not missing else f"CODEBASE_MAP missing: {', '.join(missing)}",
    }


def build_checks() -> list[dict]:
    return [
        run_check("policy", ["python3", str(ROOT / "scripts" / "validate_agent_policy.py"), "--all"]),
        run_check("tests", ["python3", "-m", "unittest", "discover", "-s", str(ROOT / "tests")]),
        run_check("skill-routing-index", ["python3", str(ROOT / "scripts" / "generate_skill_routing_index.py"), "--check"]),
        check_codebase_map(),
    ]


def print_plain(checks: list[dict]) -> None:
    width = max(len(check["name"]) for check in checks)
    for check in checks:
        print(f"{check['name']:<{width}}  {check['status'].upper()}")
        if check["status"] != "pass":
            print(f"  command: {' '.join(check['command'])}")
            if check["stderr_tail"]:
                print(f"  stderr: {check['stderr_tail']}")
            elif check["stdout_tail"]:
                print(f"  stdout: {check['stdout_tail']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ~/.agents health checks.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable check results.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    checks = build_checks()
    if args.json:
        print(json.dumps(checks, indent=2))
    else:
        print_plain(checks)
    return 0 if all(check["status"] == "pass" for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())

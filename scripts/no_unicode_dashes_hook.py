#!/usr/bin/env python3
"""Run the Unicode dash linter after an agent file-write tool."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

from no_unicode_dashes import file_violations

PATH_KEYS = {"file_path", "filePath", "notebook_path", "notebookPath", "path"}
PATCH_PATH = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", re.MULTILINE)


def extract_paths(payload: Any, cwd: Path) -> list[Path]:
    found: set[Path] = set()

    def add(value: str) -> None:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = cwd / path
        if path.is_file():
            found.add(path.resolve())

    def walk(value: Any, key: str = "") -> None:
        if isinstance(value, dict):
            for child_key, child in value.items():
                if child_key in PATH_KEYS and isinstance(child, str):
                    add(child)
                walk(child, child_key)
        elif isinstance(value, list):
            for child in value:
                walk(child, key)
        elif isinstance(value, str) and key in {"command", "patch", "input"}:
            for match in PATCH_PATH.finditer(value):
                add(match.group(1).strip())
        elif isinstance(value, str) and key == "tool_output":
            try:
                walk(json.loads(value), key)
            except json.JSONDecodeError:
                pass

    walk(payload)
    return sorted(found)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("standard", "cursor"), default="standard")
    args = parser.parse_args()

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0

    cwd = Path(payload.get("cwd") or Path.cwd()).expanduser()
    paths = extract_paths(payload, cwd)
    if not paths:
        return 0

    found = [item for path in paths for item in file_violations(path)]
    if not found:
        return 0

    message = "Unicode dash lint failed after file write:\n" + "\n".join(found)
    if args.format == "cursor":
        print(json.dumps({"additional_context": message}))
        return 0

    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

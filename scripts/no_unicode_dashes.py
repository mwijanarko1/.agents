#!/usr/bin/env python3
"""Reject em and en dashes in added text.

Default path args scan Git added hunks (and whole untracked files) so
pre-existing dashes on unchanged lines do not fail the check.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

FORBIDDEN = {"\u2013": "en dash", "\u2014": "em dash"}
SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build", ".next", ".cache", "__pycache__"}


def is_skipped(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def violations(path: Path, text: str):
    for line_number, line in enumerate(text.splitlines(), 1):
        for character, label in FORBIDDEN.items():
            if character in line:
                yield f"{path}:{line_number}: {label} found"


def read_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except (OSError, PermissionError):
        return None
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def scan_paths(paths: list[Path]):
    for path in paths:
        if path.is_dir():
            for root, directories, files in os.walk(path):
                directories[:] = [name for name in directories if name not in SKIP_DIRS]
                for name in files:
                    target = Path(root, name)
                    text = read_text(target)
                    if text is not None:
                        yield from violations(target, text)
        elif path.is_file():
            text = read_text(path)
            if text is not None:
                yield from violations(path, text)


def git_toplevel(start: Path) -> Path | None:
    target = start if start.is_dir() else start.parent
    if not target.exists():
        return None
    try:
        out = subprocess.run(
            ["git", "-C", str(target), "rev-parse", "--show-toplevel"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return Path(out.stdout.decode().strip())


def git_in(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    ).stdout


def parse_diff_violations(diff: str):
    current_path = Path(".")
    new_line = 0
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current_path = Path(line[6:])
        elif line.startswith("@@"):
            new_range = line.split("+")[1].split(" ")[0]
            new_line = int(new_range.split(",")[0])
        elif line.startswith("+") and not line.startswith("+++"):
            if not is_skipped(current_path):
                for character, label in FORBIDDEN.items():
                    if character in line[1:]:
                        yield f"{current_path}:{new_line}: {label} found"
            new_line += 1
        elif not line.startswith("-"):
            new_line += 1


def is_untracked(repo: Path, rel: Path) -> bool:
    try:
        out = git_in(repo, "ls-files", "--others", "--exclude-standard", "--", str(rel))
    except subprocess.CalledProcessError:
        return False
    return bool(out.strip())


def file_violations(path: Path, whole_file: bool = False):
    if whole_file:
        yield from scan_paths([path])
        return
    repo = git_toplevel(path)
    if repo is None:
        yield from scan_paths([path])
        return
    try:
        rel = path.resolve().relative_to(repo)
    except ValueError:
        yield from scan_paths([path])
        return
    if is_untracked(repo, rel):
        yield from scan_paths([path])
        return
    try:
        diff = git_in(
            repo, "diff", "--no-ext-diff", "--unified=0", "--no-color", "HEAD", "--", str(rel)
        ).decode("utf-8", "replace")
    except subprocess.CalledProcessError:
        yield from scan_paths([path])
        return
    yield from parse_diff_violations(diff)


def target_violations(paths: list[Path], whole_file: bool = False):
    for path in paths:
        if path.is_dir():
            for root, directories, files in os.walk(path):
                directories[:] = [name for name in directories if name not in SKIP_DIRS]
                for name in files:
                    yield from file_violations(Path(root, name), whole_file=whole_file)
        else:
            yield from file_violations(path, whole_file=whole_file)


def changed_violations():
    repo = git_toplevel(Path.cwd())
    if repo is None:
        raise SystemExit("Not a Git repository. Pass one or more paths to scan.")
    try:
        diff = git_in(repo, "diff", "--no-ext-diff", "--unified=0", "--no-color", "HEAD", "--").decode(
            "utf-8", "replace"
        )
    except subprocess.CalledProcessError:
        raise SystemExit("Not a Git repository. Pass one or more paths to scan.")
    yield from parse_diff_violations(diff)
    untracked = git_in(repo, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
    paths = [
        path
        for value in untracked
        if value
        for path in [repo / value.decode("utf-8", "surrogateescape")]
        if not is_skipped(path)
    ]
    yield from scan_paths(paths)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="files or directories; defaults to Git additions")
    parser.add_argument(
        "--whole-file",
        action="store_true",
        help="scan entire files instead of added Git hunks",
    )
    args = parser.parse_args()
    if args.paths:
        found = list(target_violations(args.paths, whole_file=args.whole_file))
    else:
        found = list(changed_violations())
    if found:
        print("Forbidden Unicode dashes detected:", file=sys.stderr)
        print("\n".join(found), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Small, dependency-free context compaction helpers for agent workflows.

The commands intentionally print summaries, samples, and bounded output instead of
raw files. Use them before asking an agent to inspect large logs, JSON, CSV, or an
unknown repository.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

DEFAULT_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".turbo",
    ".cache",
    "coverage",
    "DerivedData",
    ".expo",
    ".idea",
    ".vscode",
    "logs",
    "logs/archive",
    "vendor",
}
ENTRYPOINT_NAMES = {
    "main.py",
    "app.py",
    "server.py",
    "index.js",
    "index.ts",
    "index.tsx",
    "main.js",
    "main.ts",
    "App.tsx",
    "App.jsx",
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "Dockerfile",
    "docker-compose.yml",
    "Makefile",
}
CONFIG_PATTERNS = re.compile(r"(^|/)(\.env\.example|[^/]*(config|settings|rc)\.[^/]+|tsconfig\.json|vite\.config\.|next\.config\.)", re.I)


def iter_files(root: Path, skip_dirs: set[str]) -> Iterable[Path]:
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        rel = current.relative_to(root)
        dirnames[:] = [
            name
            for name in dirnames
            if name not in skip_dirs and str((rel / name)).replace(os.sep, "/") not in skip_dirs
        ]
        for filename in filenames:
            yield current / filename


def is_probably_text(path: Path, sample_bytes: int = 2048) -> bool:
    try:
        chunk = path.read_bytes()[:sample_bytes]
    except OSError:
        return False
    return b"\0" not in chunk


def repo_map(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve()
    skip_dirs = DEFAULT_SKIP_DIRS | set(args.skip_dir or [])
    files = list(iter_files(root, skip_dirs))
    rels = [str(path.relative_to(root)).replace(os.sep, "/") for path in files]
    suffix_counts = Counter(path.suffix or "[none]" for path in files)
    entrypoints = [rel for rel in rels if Path(rel).name in ENTRYPOINT_NAMES][: args.limit]
    configs = [rel for rel in rels if CONFIG_PATTERNS.search(rel)][: args.limit]
    tests = [rel for rel in rels if re.search(r"(^|/)(test|tests|__tests__|spec)(/|$)|(_test|\.test|\.spec)\.", rel, re.I)][: args.limit]
    docs = [rel for rel in rels if rel.lower().endswith(("readme.md", "agents.md", "handoff.md", "codebase_map.md"))][: args.limit]

    print(f"# Repo Needle Map\nroot: {root}\nfiles_scanned: {len(files)}\nskipped_dirs: {', '.join(sorted(skip_dirs))}\n")
    print("## File types")
    for suffix, count in suffix_counts.most_common(12):
        print(f"- {suffix}: {count}")
    for title, values in [
        ("Entry points", entrypoints),
        ("Config", configs),
        ("Tests", tests),
        ("Docs / handoff", docs),
    ]:
        print(f"\n## {title}")
        if values:
            for value in values:
                print(f"- {value}")
        else:
            print("- [none found in bounded scan]")


def sample_text(path: Path, max_lines: int, max_chars: int) -> list[str]:
    lines: list[str] = []
    chars = 0
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if len(lines) >= max_lines or chars >= max_chars:
                    break
                clipped = line.rstrip("\n")[: max(0, max_chars - chars)]
                lines.append(clipped)
                chars += len(clipped) + 1
    except OSError as exc:
        return [f"[read error: {exc}]"]
    return lines


def file_summary(args: argparse.Namespace) -> None:
    path = Path(args.path).expanduser()
    stat = path.stat()
    print(f"# File Needle\npath: {path}\nbytes: {stat.st_size}\ntext: {is_probably_text(path)}")
    if not is_probably_text(path):
        return
    lines = sample_text(path, args.lines, args.chars)
    print(f"sample_lines: {len(lines)}\n")
    for idx, line in enumerate(lines, start=1):
        print(f"{idx}: {line}")


def summarize_value(value: Any, depth: int = 0) -> Any:
    if depth >= 3:
        return type(value).__name__
    if isinstance(value, dict):
        return {key: summarize_value(value[key], depth + 1) for key in list(value)[:12]}
    if isinstance(value, list):
        sample = value[:3]
        return {"type": "list", "count": len(value), "sample": [summarize_value(item, depth + 1) for item in sample]}
    return {"type": type(value).__name__, "sample": value if isinstance(value, (str, int, float, bool)) else None}


def json_summary(args: argparse.Namespace) -> None:
    path = Path(args.path).expanduser()
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        data = json.load(handle)
    print(json.dumps({"path": str(path), "summary": summarize_value(data)}, indent=2, ensure_ascii=False)[: args.chars])


def csv_summary(args: argparse.Namespace) -> None:
    path = Path(args.path).expanduser()
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append(row)
            if len(rows) >= args.scan_rows:
                break
    columns = reader.fieldnames or []
    completeness = {col: sum(1 for row in rows if row.get(col) not in (None, "")) for col in columns[: args.limit_columns]}
    numeric_stats: dict[str, dict[str, float]] = {}
    for col in columns[: args.limit_columns]:
        nums = []
        for row in rows:
            try:
                nums.append(float(row.get(col, "")))
            except ValueError:
                pass
        if nums:
            numeric_stats[col] = {"min": min(nums), "max": max(nums), "mean": statistics.fmean(nums)}
    print(json.dumps({
        "path": str(path),
        "sampled_rows": len(rows),
        "columns": columns[: args.limit_columns],
        "non_empty_counts": completeness,
        "numeric_stats": numeric_stats,
        "sample": rows[: args.sample_rows],
    }, indent=2, ensure_ascii=False)[: args.chars])


def log_filter(args: argparse.Namespace) -> None:
    path = Path(args.path).expanduser()
    pattern = re.compile(args.pattern, re.I) if args.pattern else None
    matches: list[tuple[int, str]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for number, line in enumerate(handle, start=1):
            if pattern is None or pattern.search(line):
                matches.append((number, line.rstrip("\n")[: args.line_chars]))
                if len(matches) >= args.limit:
                    break
    print(f"# Log Needle\npath: {path}\npattern: {args.pattern or '[all]'}\nmatched_printed: {len(matches)}\n")
    for number, line in matches:
        print(f"{number}: {line}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create compact needle maps before agent inspection.")
    sub = parser.add_subparsers(dest="command", required=True)

    repo = sub.add_parser("repo-map", help="Summarize repo shape without vendor/build directories")
    repo.add_argument("root", nargs="?", default=".")
    repo.add_argument("--skip-dir", action="append", default=[])
    repo.add_argument("--limit", type=int, default=40)
    repo.set_defaults(func=repo_map)

    fs = sub.add_parser("file-summary", help="Bounded file stats and first lines")
    fs.add_argument("path")
    fs.add_argument("--lines", type=int, default=80)
    fs.add_argument("--chars", type=int, default=6000)
    fs.set_defaults(func=file_summary)

    js = sub.add_parser("json-summary", help="Summarize JSON structure and tiny samples")
    js.add_argument("path")
    js.add_argument("--chars", type=int, default=6000)
    js.set_defaults(func=json_summary)

    cs = sub.add_parser("csv-summary", help="Summarize CSV columns, completeness, stats, and samples")
    cs.add_argument("path")
    cs.add_argument("--scan-rows", type=int, default=500)
    cs.add_argument("--sample-rows", type=int, default=5)
    cs.add_argument("--limit-columns", type=int, default=40)
    cs.add_argument("--chars", type=int, default=6000)
    cs.set_defaults(func=csv_summary)

    lf = sub.add_parser("log-filter", help="Print bounded matching log lines")
    lf.add_argument("path")
    lf.add_argument("--pattern", default="ERROR|WARN|FAIL|Exception|Traceback")
    lf.add_argument("--limit", type=int, default=40)
    lf.add_argument("--line-chars", type=int, default=500)
    lf.set_defaults(func=log_filter)

    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

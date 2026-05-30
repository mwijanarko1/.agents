#!/usr/bin/env python3
"""
List and validate shared documentation routing metadata.

Every Markdown file in docs/ and top-level shared docs such as tools.md should
include front matter with:
- summary: one-line purpose
- read_when: when an agent should load it
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_KEYS = ("summary", "read_when")


def parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    data: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"\'')
        if key:
            data[key] = value
    return data


def iter_doc_files(root: Path) -> list[Path]:
    docs_dir = root / "docs"
    files = sorted(docs_dir.rglob("*.md")) if docs_dir.exists() else []
    tools_md = root / "tools.md"
    if tools_md.exists():
        files.append(tools_md)
    return sorted(files)


def validate_docs(root: Path) -> list[str]:
    errors: list[str] = []
    for path in iter_doc_files(root):
        metadata = parse_frontmatter(path.read_text(encoding="utf-8", errors="ignore"))
        for key in REQUIRED_KEYS:
            if not metadata.get(key):
                errors.append(f"{path.relative_to(root).as_posix()} missing frontmatter `{key}`")
    return errors


def render_docs(root: Path) -> str:
    lines = []
    for path in iter_doc_files(root):
        metadata = parse_frontmatter(path.read_text(encoding="utf-8", errors="ignore"))
        rel = path.relative_to(root).as_posix()
        lines.append(f"{rel}")
        lines.append(f"  summary: {metadata.get('summary', '<missing>')}")
        lines.append(f"  read_when: {metadata.get('read_when', '<missing>')}")
    return "\n".join(lines) + ("\n" if lines else "")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="List docs summaries and read_when routing metadata.")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if required docs metadata is missing.")
    parser.add_argument("--root", default=str(ROOT), help="Agents root to inspect.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.root).expanduser().resolve()
    errors = validate_docs(root)
    if args.check:
        if errors:
            for error in errors:
                print(f"FAIL: {error}")
            return 1
        print("OK: docs metadata valid")
        return 0
    print(render_docs(root), end="")
    if errors:
        print("\nMissing metadata:")
        for error in errors:
            print(f"- {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

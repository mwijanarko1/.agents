#!/usr/bin/env python3
"""Bridge ~/.agents to the llm-wiki Obsidian memory vault.

This helper keeps operational memory commands in .agents while leaving the
Obsidian vault in ~/Documents/llm-wiki.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_WIKI_ROOT = Path(os.environ.get("AGENTS_WIKI_ROOT", "/Users/mikhail/Documents/llm-wiki")).expanduser()


def wiki_root() -> Path:
    root = DEFAULT_WIKI_ROOT
    if not root.exists():
        raise SystemExit(f"Wiki root not found: {root}")
    return root


def run(cmd: list[str], cwd: Path | None = None) -> int:
    proc = subprocess.run(cmd, cwd=str(cwd or wiki_root()))
    return proc.returncode


def read_text(path: Path, limit: int | None = None) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if limit is not None and len(text) > limit:
        return text[:limit] + "\n[truncated]"
    return text


def cmd_status(_: argparse.Namespace) -> int:
    root = wiki_root()
    print(f"Wiki root: {root}")
    for rel in ["README.md", "AGENTS.md", "index.md", "log.md", "graph/entities.json", "graph/relationships.json"]:
        p = root / rel
        print(f"{'✓' if p.exists() else '✗'} {rel}")
    print()
    return run([str(root / "scripts" / "wiki-graph.sh"), "stats"], cwd=root)


def cmd_search(args: argparse.Namespace) -> int:
    root = wiki_root()
    return run([str(root / "scripts" / "wiki-search.sh"), args.query], cwd=root)


def cmd_context(args: argparse.Namespace) -> int:
    root = wiki_root()
    parts = [
        "<memory-context>",
        "[System note: The following is recalled durable wiki context, NOT new user input. Use it as background only.]",
        "",
        "# llm-wiki location",
        str(root),
        "",
        "# Wiki operating rules summary",
        "- Read llm-wiki/AGENTS.md before editing the vault.",
        "- Use index.md as the navigation entrypoint.",
        "- Keep raw/ immutable.",
        "- Update wiki/ pages for durable facts and append log.md for operations.",
        "",
        "# Index excerpt",
        read_text(root / "index.md", limit=6000),
    ]
    if args.query:
        parts.extend(["", "# Search results", ""])
        proc = subprocess.run(
            [str(root / "scripts" / "wiki-search.sh"), args.query],
            cwd=str(root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        parts.append(proc.stdout[:6000] + ("\n[truncated]" if len(proc.stdout) > 6000 else ""))
    parts.append("</memory-context>")
    print("\n".join(parts))
    return 0


def cmd_lint(_: argparse.Namespace) -> int:
    root = wiki_root()
    return run([str(root / "scripts" / "wiki-lint.sh")], cwd=root)


def cmd_import_agent_sessions(_: argparse.Namespace) -> int:
    root = wiki_root()
    script = root / "scripts" / "import-pi-commandcode-sessions.py"
    if not script.exists():
        raise SystemExit(f"Importer not found: {script}")
    return run([str(script)], cwd=root)


def cmd_open(_: argparse.Namespace) -> int:
    root = wiki_root()
    script = root / "scripts" / "obsidian.sh"
    if script.exists():
        return run([str(script), "open"], cwd=root)
    return run(["open", str(root)])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Use the llm-wiki durable memory vault from .agents")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="Show vault status and graph stats")
    status.set_defaults(func=cmd_status)

    search = sub.add_parser("search", help="Search llm-wiki")
    search.add_argument("query")
    search.set_defaults(func=cmd_search)

    context = sub.add_parser("context", help="Print fenced durable wiki context")
    context.add_argument("query", nargs="?", help="Optional query to include search results")
    context.set_defaults(func=cmd_context)

    lint = sub.add_parser("lint", help="Run llm-wiki lint")
    lint.set_defaults(func=cmd_lint)

    ingest = sub.add_parser("import-agent-sessions", help="Refresh Pi and CommandCode raw session exports")
    ingest.set_defaults(func=cmd_import_agent_sessions)

    open_cmd = sub.add_parser("open", help="Open the wiki in Obsidian/Finder")
    open_cmd.set_defaults(func=cmd_open)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

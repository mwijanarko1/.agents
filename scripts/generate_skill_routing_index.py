#!/usr/bin/env python3
"""
Generate a lightweight skill routing index from canonical SKILL.md front matter.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT / "agent-policy.json"
INDEX_PATH = ROOT / "manifests" / "skill-routing-index.json"


def load_policy() -> dict[str, Any]:
    with open(POLICY_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def parse_scalar(value: str) -> Any:
    cleaned = value.strip().strip("\"'")
    if cleaned.startswith("[") and cleaned.endswith("]"):
        inner = cleaned[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("\"'") for item in inner.split(",") if item.strip()]
    if cleaned.lower() == "true":
        return True
    if cleaned.lower() == "false":
        return False
    return cleaned


def parse_frontmatter(text: str) -> tuple[dict[str, Any], int]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, 0

    frontmatter_lines: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        frontmatter_lines.append(line)

    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in frontmatter_lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- ") and current_key:
            current = data.setdefault(current_key, [])
            if isinstance(current, list):
                current.append(stripped[2:].strip().strip("\"'"))
            continue
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        current_key = key
        if raw_value:
            data[key] = parse_scalar(raw_value)
        else:
            data[key] = []

    frontmatter_chars = len("\n".join(frontmatter_lines))
    return data, frontmatter_chars


def collect_policy_skill_sets(policy: dict[str, Any]) -> dict[str, set[str]]:
    foundation = set(policy.get("default_stack", {}).get("always", []))
    primary: set[str] = set()
    secondary: set[str] = set()
    reference: set[str] = set()

    for task in policy.get("task_mapping", {}).values():
        if not isinstance(task, dict):
            continue
        primary.update(task.get("required", []) or [])
        primary.update(task.get("primary_exactly_one", []) or [])
        add_when = task.get("add_when", {})
        if isinstance(add_when, dict):
            primary.update(add_when.keys())
        secondary_cfg = task.get("secondary", {})
        if isinstance(secondary_cfg, dict):
            secondary.update(secondary_cfg.keys())

    for skill in policy.get("skill_triggers", {}):
        reference.add(skill)

    return {
        "foundation": foundation,
        "primary": primary,
        "secondary": secondary,
        "reference": reference,
    }


def infer_category(name: str, policy: dict[str, Any]) -> str:
    if name in policy.get("default_stack", {}).get("always", []):
        return "foundation"
    for task_name, task in policy.get("task_mapping", {}).items():
        if not isinstance(task, dict):
            continue
        values: set[str] = set(task.get("required", []) or [])
        values.update(task.get("primary_exactly_one", []) or [])
        add_when = task.get("add_when", {})
        if isinstance(add_when, dict):
            values.update(add_when.keys())
        secondary = task.get("secondary", {})
        if isinstance(secondary, dict):
            values.update(secondary.keys())
        if name in values:
            return task_name
    if name.startswith("game-") or name in {"phaser", "threejs-game", "make-game", "quick-game"}:
        return "game"
    if name.startswith("swift") or name.startswith("ios") or name in {"add-component", "build-feature", "explore-recipes"}:
        return "mobile"
    if name in policy.get("skill_triggers", {}):
        return "triggered"
    return "utility"


def infer_priority(name: str, skill_sets: dict[str, set[str]]) -> str:
    if name in skill_sets["foundation"]:
        return "foundation"
    if name in skill_sets["secondary"]:
        return "secondary"
    if name in skill_sets["reference"]:
        return "reference"
    if name in skill_sets["primary"]:
        return "primary"
    return "utility"


def as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value:
        return [value]
    return []


def build_index() -> dict[str, Any]:
    policy = load_policy()
    skills_root = Path(policy.get("skills_root", ROOT / "skills")).expanduser()
    skill_sets = collect_policy_skill_sets(policy)
    skills = []
    latest_skill_mtime = 0.0

    for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir() and not path.name.startswith(".")):
        skill_path = skill_dir / "SKILL.md"
        if not skill_path.exists():
            continue
        latest_skill_mtime = max(latest_skill_mtime, skill_path.stat().st_mtime)
        text = skill_path.read_text(encoding="utf-8")
        frontmatter, frontmatter_chars = parse_frontmatter(text)
        name = skill_dir.name
        entry = {
            "name": name,
            "path": f"skills/{skill_dir.name}/SKILL.md",
            "description": str(frontmatter.get("description") or "No description provided."),
            "category": str(frontmatter.get("category") or infer_category(name, policy)),
            "priority": str(frontmatter.get("priority") or infer_priority(name, skill_sets)),
            "tokens": {
                "frontmatter_chars": frontmatter_chars,
                "skill_chars": len(text),
            },
        }
        for key in ("triggers", "avoid_when", "requires_one_of", "only_after"):
            values = as_string_list(frontmatter.get(key))
            if values:
                entry[key] = values
        if isinstance(frontmatter.get("never_alone"), bool):
            entry["never_alone"] = frontmatter["never_alone"]
        skills.append(entry)

    return {
        "version": 1,
        "generated_at": datetime.fromtimestamp(latest_skill_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_root": str(skills_root),
        "skills": skills,
    }


def render_index(index: dict[str, Any]) -> str:
    return json.dumps(index, indent=2, sort_keys=False) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate skill-routing-index.json.")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if the generated index differs.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    index = build_index()
    rendered = render_index(index)

    if args.check:
        current = INDEX_PATH.read_text(encoding="utf-8") if INDEX_PATH.exists() else ""
        if current != rendered:
            raise SystemExit("skill-routing-index.json is out of date")
        return

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()

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

import yaml


ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT / "agent-policy.json"
INDEX_PATH = ROOT / "manifests" / "skill-routing-index.json"


def load_policy() -> dict[str, Any]:
    with open(POLICY_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], int]:
    """Parse YAML front matter, including block scalars, via PyYAML."""
    if not text.startswith("---"):
        return {}, 0
    rest = text[3:]
    if rest.startswith("\r\n"):
        rest = rest[2:]
    elif rest.startswith("\n"):
        rest = rest[1:]
    else:
        return {}, 0

    # Find closing --- on its own line
    end = None
    for marker in ("\n---\n", "\n---\r\n", "\n---"):
        idx = rest.find(marker)
        if idx != -1:
            end = idx
            break
    if end is None:
        return {}, 0

    raw = rest[:end]
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    return data, len(raw)


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
    if name.startswith("swift") or name.startswith("ios") or name in {"shipswift-recipes"}:
        return "mobile"
    if name in policy.get("skill_triggers", {}):
        return "triggered"
    return "utility"


def infer_priority(name: str, skill_sets: dict[str, set[str]], never_auto: set[str] | None = None) -> str:
    if never_auto and name in never_auto:
        return "utility"
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
    never_auto = set(policy.get("never_auto_route", []) or [])
    opt_in = set((policy.get("opt_in_skills") or {}).keys())
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
            "priority": str(frontmatter.get("priority") or infer_priority(name, skill_sets, never_auto)),
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
        # Policy-level auto-route exclusions remain discoverable by explicit name.
        avoid = list(entry.get("avoid_when", []))
        if name in never_auto and "auto_route" not in avoid:
            avoid.append("auto_route")
        if name in opt_in and "implicit_mobile" not in avoid:
            avoid.append("implicit_mobile")
        if avoid:
            entry["avoid_when"] = avoid
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

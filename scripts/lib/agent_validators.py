#!/usr/bin/env python3
"""
Shared validators for the canonical ~/.agents policy surface.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

try:
    import jsonschema
except ModuleNotFoundError:  # pragma: no cover
    jsonschema = None


TEXT_SUFFIXES = {".md", ".json", ".py", ".js", ".mjs", ".sh", ".toml", ".yml", ".yaml"}
PERSONAL_PATH_RE = re.compile(r"(/Users/[A-Za-z0-9._-]+(?:/[^\s\"'`]+)?)|(C:\\Users\\[A-Za-z0-9._-]+(?:\\[^\s\"'`]+)?)")
PLACEHOLDER_RE = re.compile(r"<[^>\s]+>")
ALLOW_FORBIDDEN_COMMAND_RE = re.compile(r"agent-policy:\s*allow-forbidden-command\s+because:", re.IGNORECASE)
SKILL_PATH_RE = re.compile(
    r"(?:/Users/mikhail/\.agents/skills/|~/\.agents/skills/|(?<![.\w/-])skills/)([A-Za-z0-9._-]+)/SKILL\.md"
)
LOCAL_PATH_RE = re.compile(
    r"^((?:skills|scripts|hooks|agents|docs|manifests|schemas|tests)/[A-Za-z0-9._<>/-]+(?:\.[A-Za-z0-9._-]+)?)$"
)
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
BULLET_SKILL_RE = re.compile(r"^\s*-\s+(?:\*\*)?`([A-Za-z0-9._-]+)`")


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def validate_json_schema(data: dict, schema_path: Path, label: str) -> list[str]:
    if not schema_path.exists():
        return [f"Missing schema for {label}: {schema_path}"]
    if jsonschema is None:
        return [f"jsonschema package unavailable; cannot validate {label}"]

    schema = load_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda item: item.path)
    return [
        f"{label} schema: {('/'.join(map(str, err.path)) or '/')} {err.message}"
        for err in errors
    ]


def parse_frontmatter_keys(text: str) -> set[str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return set()
    keys: set[str] = set()
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key = line.split(":", 1)[0].strip()
        if key:
            keys.add(key)
    return keys


def parse_frontmatter_values(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip().strip("\"'")
        if key:
            values[key] = value
    return values


def iter_skill_dirs(skills_root: Path) -> Iterable[Path]:
    if not skills_root.exists():
        return []
    return sorted(item for item in skills_root.iterdir() if item.is_dir() and not item.name.startswith("."))


def iter_text_files(root: Path, targets: list[str]) -> Iterable[Path]:
    files: list[Path] = []
    for target in targets:
        path = root / target
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix.lower() in TEXT_SUFFIXES:
                files.append(path)
            continue
        for candidate in path.rglob("*"):
            if candidate.is_file() and candidate.suffix.lower() in TEXT_SUFFIXES:
                files.append(candidate)
    return sorted(files)


def relative_label(root: Path, file_path: Path) -> str:
    try:
        return file_path.relative_to(root).as_posix()
    except ValueError:
        return file_path.as_posix()


def strip_placeholder_paths(value: str) -> str:
    return PLACEHOLDER_RE.sub("", value)


def line_has_allow_comment(lines: list[str], index: int) -> bool:
    start = max(0, index - 1)
    end = min(len(lines), index + 2)
    return any(ALLOW_FORBIDDEN_COMMAND_RE.search(lines[item]) for item in range(start, end))


def existing_skill_names(root: Path) -> set[str]:
    return {skill_dir.name for skill_dir in iter_skill_dirs(root / "skills")}


def parse_frontmatter_skill_names(text: str) -> set[str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return set()
    skills: set[str] = set()
    current_key: str | None = None
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if not stripped:
            continue
        if stripped.startswith("- ") and current_key == "skills":
            skills.add(stripped[2:].strip().strip("\"'`"))
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            if current_key == "skills" and value.strip():
                raw = value.strip().strip("[]")
                for item in raw.split(","):
                    cleaned = item.strip().strip("\"'`")
                    if cleaned:
                        skills.add(cleaned)
    return skills


def extract_skill_names_from_subagent(text: str) -> set[str]:
    names = set(SKILL_PATH_RE.findall(text))
    names.update(parse_frontmatter_skill_names(text))
    return {name for name in names if name and not PLACEHOLDER_RE.search(name)}


def validate_shared_references(root: Path) -> list[str]:
    errors: list[str] = []
    skills = existing_skill_names(root)
    targets = ["AGENTS.md", "agent-policy.json", "agents", "docs"]

    for file_path in iter_text_files(root, targets):
        rel = relative_label(root, file_path)
        text = file_path.read_text(encoding="utf-8", errors="ignore")

        for skill in SKILL_PATH_RE.findall(text):
            if skill not in skills:
                errors.append(f"Missing skill reference in {rel}: {skill}")

        for line in text.splitlines():
            bullet_skill = BULLET_SKILL_RE.search(line) if rel.startswith("agents/") else None
            if bullet_skill:
                candidate = bullet_skill.group(1)
                if candidate not in skills:
                    errors.append(f"Missing skill reference in {rel}: {candidate}")

        for snippet in BACKTICK_RE.findall(text):
            normalized = snippet.strip()
            has_agents_prefix = False
            for prefix in ("/Users/mikhail/.agents/", "~/.agents/"):
                if normalized.startswith(prefix):
                    normalized = normalized[len(prefix):]
                    has_agents_prefix = True
                    break
            if not has_agents_prefix and not normalized.startswith("skills/"):
                continue
            match = LOCAL_PATH_RE.match(normalized)
            if not match:
                continue
            path_ref = match.group(1)
            if PLACEHOLDER_RE.search(path_ref):
                continue
            if path_ref.endswith("/SKILL.md"):
                continue
            if not (root / path_ref).exists():
                errors.append(f"Missing path reference in {rel}: {path_ref}")

    return sorted(set(errors))


def forbidden_command_patterns(policy: dict) -> list[tuple[re.Pattern[str], str]]:
    hardening = policy.get("supply_chain_hardening", {})
    forbidden = hardening.get("forbid_runtime_executors", []) or []
    forbidden.extend(hardening.get("forbid_release_check_commands", []) or [])
    patterns: list[tuple[re.Pattern[str], str]] = []
    for item in forbidden:
        if not isinstance(item, str) or not item:
            continue
        if item == "@latest":
            patterns.append((re.compile(r"@[Ll]atest\b"), item))
            continue
        if "|" in item:
            patterns.append((re.compile(re.escape(item), re.IGNORECASE), item))
            continue
        parts = item.split()
        if len(parts) == 1:
            patterns.append((re.compile(rf"\b{re.escape(parts[0])}\b"), item))
        else:
            patterns.append((re.compile(r"\b" + r"\s+".join(re.escape(part) for part in parts) + r"\b", re.IGNORECASE), item))
    return patterns


def extract_command_snippet(line: str, pattern: re.Pattern[str]) -> str:
    backticked = BACKTICK_RE.findall(line)
    for snippet in backticked:
        if pattern.search(snippet):
            return snippet.strip()
    match = pattern.search(line)
    if not match:
        return line.strip()
    return line[match.start():].strip().strip("`")


def validate_supply_chain_recipes(root: Path, policy: dict) -> list[str]:
    errors: list[str] = []
    patterns = forbidden_command_patterns(policy)
    if not patterns:
        return errors
    targets = ["AGENTS.md", "agent-policy.json", "agents", "docs", "hooks/templates", "scripts"]
    for file_path in iter_text_files(root, targets):
        rel = relative_label(root, file_path)
        if rel in {"agent-policy.json", "scripts/lib/agent_validators.py"}:
            continue
        lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for index, line in enumerate(lines):
            if re.search(r"\b(?:do not|must not|forbid|forbidden|no ad-hoc)\b", line, re.IGNORECASE):
                continue
            if line_has_allow_comment(lines, index):
                continue
            for pattern, _label in patterns:
                if pattern.search(line):
                    snippet = extract_command_snippet(line, pattern)
                    errors.append(f"Forbidden supply-chain recipe in {rel}: {snippet}")
                    break
    return errors


def validate_subagent_policy_skill_alignment(root: Path, policy: dict) -> list[str]:
    errors: list[str] = []
    agents_dir = root / policy.get("subagents", {}).get("directory", "agents")
    dynamic_subagents = {"code-reviewer"}
    for name, cluster in policy.get("capability_clusters", {}).items():
        if name in dynamic_subagents:
            continue
        agent_path = agents_dir / f"{name}.md"
        if not agent_path.exists():
            continue
        prompt_skills = extract_skill_names_from_subagent(agent_path.read_text(encoding="utf-8", errors="ignore"))
        policy_skills = set(cluster.get("skills", []))
        for missing in sorted(policy_skills - prompt_skills):
            errors.append(f"Subagent policy skill missing from prompt {agent_path}: {missing}")
        for extra in sorted(prompt_skills - policy_skills):
            errors.append(f"Subagent prompt skill missing from policy {agent_path}: {extra}")
    return errors


def validate_skill_non_empty(skills_root: Path) -> list[str]:
    errors: list[str] = []
    for skill_dir in iter_skill_dirs(skills_root):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"Skill missing SKILL.md: {skill_dir.name}")
            continue
        if not skill_md.read_text(encoding="utf-8").strip():
            errors.append(f"Skill SKILL.md is empty: {skill_dir.name}")
    return errors


def validate_skill_frontmatter(skills_root: Path) -> list[str]:
    errors: list[str] = []
    for skill_dir in iter_skill_dirs(skills_root):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        keys = parse_frontmatter_keys(skill_md.read_text(encoding="utf-8"))
        if not keys:
            errors.append(f"Skill missing frontmatter: {skill_md}")
            continue
        for required in ("name", "description"):
            if required not in keys:
                errors.append(f"Skill missing `{required}` frontmatter key: {skill_md}")
    return errors


def validate_docs_frontmatter(root: Path) -> list[str]:
    errors: list[str] = []
    docs_dir = root / "docs"
    files = sorted(docs_dir.rglob("*.md")) if docs_dir.exists() else []
    tools_md = root / "tools.md"
    if tools_md.exists():
        files.append(tools_md)

    for doc_path in sorted(files):
        text = doc_path.read_text(encoding="utf-8", errors="ignore")
        values = parse_frontmatter_values(text)
        rel = relative_label(root, doc_path)
        if not values:
            errors.append(f"Doc missing frontmatter: {rel}")
            continue
        for required in ("summary", "read_when"):
            if not values.get(required):
                errors.append(f"Doc missing `{required}` frontmatter key: {rel}")
    return errors


def validate_subagent_frontmatter(agents_dir: Path) -> list[str]:
    errors: list[str] = []
    if not agents_dir.exists():
        return [f"Agents directory missing: {agents_dir}"]
    for agent_md in sorted(path for path in agents_dir.iterdir() if path.is_file() and path.suffix == ".md"):
        keys = parse_frontmatter_keys(agent_md.read_text(encoding="utf-8"))
        if not keys:
            errors.append(f"Subagent missing frontmatter: {agent_md}")
            continue
        for required in ("name", "description"):
            if required not in keys:
                errors.append(f"Subagent missing `{required}` frontmatter key: {agent_md}")
    return errors


def validate_subagent_skill_paths(agents_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_path_re = re.compile(r"`(/Users/mikhail/\.agents/skills/[^`]+/SKILL\.md)`")
    if not agents_dir.exists():
        return errors
    for agent_md in sorted(path for path in agents_dir.iterdir() if path.is_file() and path.suffix == ".md"):
        text = agent_md.read_text(encoding="utf-8")
        for match in skill_path_re.findall(text):
            if "<" in match or ">" in match:
                continue
            if not Path(match).exists():
                errors.append(f"Subagent references missing skill path {match} in {agent_md}")
    return errors


def validate_no_personal_paths(root: Path, allowed_prefixes: list[str], targets: list[str]) -> list[str]:
    errors: list[str] = []
    allow = [Path(prefix).expanduser().as_posix() for prefix in allowed_prefixes]
    files: list[Path] = []
    for target in targets:
        path = root / target
        if not path.exists():
            continue
        if path.is_file():
            files.append(path)
            continue
        for candidate in path.rglob("*"):
            if candidate.is_file() and candidate.suffix.lower() in TEXT_SUFFIXES:
                files.append(candidate)

    for file_path in files:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for match in PERSONAL_PATH_RE.findall(text):
            match_value = next((item for item in match if item), "")
            normalized = match_value.replace("\\", "/")
            if any(normalized.startswith(prefix) for prefix in allow):
                continue
            rel = file_path.relative_to(root)
            errors.append(f"Personal path leak in {rel}: {match_value}")
            break
    return errors


def validate_skill_catalog(root: Path, catalog_path: Path) -> list[str]:
    if not catalog_path.exists():
        return [f"Missing skill catalog: {catalog_path}"]
    data = load_json(catalog_path)
    errors: list[str] = []
    skills = data.get("skills", [])
    if not isinstance(skills, list):
        return [f"Invalid skill catalog format: {catalog_path}"]

    for entry in skills:
        if not isinstance(entry, dict):
            errors.append("Skill catalog entry must be an object")
            continue
        name = entry.get("name", "<unknown>")
        path_text = entry.get("path")
        if not isinstance(path_text, str) or not path_text:
            errors.append(f"Skill catalog entry `{name}` missing path")
            continue
        skill_path = root / path_text
        if not skill_path.exists():
            errors.append(f"Skill catalog entry `{name}` references missing file: {path_text}")
        if not isinstance(entry.get("origin"), str) or not entry.get("origin"):
            errors.append(f"Skill catalog entry `{name}` missing origin")
        if not isinstance(entry.get("source"), str) or not entry.get("source"):
            errors.append(f"Skill catalog entry `{name}` missing source")
    return errors


def validate_skill_routing_index(root: Path, index_path: Path) -> list[str]:
    if not index_path.exists():
        return [f"Missing skill routing index: {index_path}"]
    data = load_json(index_path)
    errors: list[str] = []
    schema_path = root / "schemas" / "skill-routing-index.schema.json"
    errors.extend(validate_json_schema(data, schema_path, "skill-routing-index.json"))

    skills = data.get("skills", [])
    if not isinstance(skills, list):
        return errors + [f"Invalid skill routing index format: {index_path}"]

    canonical_names = {skill_dir.name for skill_dir in iter_skill_dirs(root / "skills")}
    indexed_names: set[str] = set()
    secondary_only = {"design-md-gallery", "design-systems-reference"}

    for entry in skills:
        if not isinstance(entry, dict):
            errors.append("Skill routing index entry must be an object")
            continue
        name = entry.get("name", "<unknown>")
        if not isinstance(name, str) or not name:
            errors.append("Skill routing index entry missing name")
            continue
        if name in indexed_names:
            errors.append(f"Skill routing index duplicate entry: {name}")
        indexed_names.add(name)

        path_text = entry.get("path")
        if not isinstance(path_text, str) or not path_text:
            errors.append(f"Skill routing index entry `{name}` missing path")
            continue
        skill_path = root / path_text
        if not skill_path.exists():
            errors.append(f"Skill routing index entry `{name}` references missing file: {path_text}")
        else:
            expected_name = skill_path.parent.name
            if name != expected_name:
                errors.append(f"Skill routing index entry `{name}` must match directory name `{expected_name}`")

        tokens = entry.get("tokens", {})
        if not isinstance(tokens, dict) or not isinstance(tokens.get("skill_chars"), int) or tokens.get("skill_chars", 0) <= 0:
            errors.append(f"Skill routing index entry `{name}` must include positive tokens.skill_chars")

        for key in ("requires_one_of", "only_after"):
            values = entry.get(key, [])
            if not isinstance(values, list):
                continue
            for referenced in values:
                if referenced not in canonical_names:
                    errors.append(f"Skill routing index entry `{name}` has unknown {key}: {referenced}")

        if name in secondary_only and entry.get("priority") == "primary":
            errors.append(f"Skill routing index marks secondary-only skill as primary: {name}")

    missing = sorted(canonical_names - indexed_names)
    extra = sorted(indexed_names - canonical_names)
    for name in missing:
        errors.append(f"Skill routing index missing canonical skill: {name}")
    for name in extra:
        errors.append(f"Skill routing index references non-canonical skill: {name}")

    return errors


def validate_sync_manifest(root: Path, manifest_path: Path) -> list[str]:
    if not manifest_path.exists():
        return [f"Missing sync manifest: {manifest_path}"]
    data = load_json(manifest_path)
    mappings = data.get("mappings", [])
    errors: list[str] = []
    if not isinstance(mappings, list):
        return [f"Sync manifest mappings must be an array: {manifest_path}"]

    for mapping in mappings:
        if not isinstance(mapping, dict):
            errors.append("Sync manifest mapping must be an object")
            continue
        source = mapping.get("source")
        if not isinstance(source, str):
            errors.append("Sync manifest mapping missing source")
            continue
        source_path = (root / source).resolve()
        if not source_path.exists():
            errors.append(f"Sync source missing: {source}")
        for target in mapping.get("targets", []):
            if not isinstance(target, dict):
                errors.append(f"Sync target for `{source}` must be object")
                continue
            target_path_value = target.get("path")
            if not isinstance(target_path_value, str):
                errors.append(f"Sync target for `{source}` missing path")
                continue
            target_path = (root / target_path_value).expanduser()
            if target_path.exists():
                expected_type = target.get("type", "symlink")
                if expected_type == "symlink":
                    if not target_path.is_symlink():
                        errors.append(f"Sync target must be symlink: {target_path}")
                    else:
                        try:
                            resolved = target_path.resolve()
                            if resolved != source_path:
                                errors.append(f"Sync target points to {resolved}, expected {source_path}")
                        except FileNotFoundError:
                            errors.append(f"Broken symlink target: {target_path}")
    return errors


def validate_hook_manifests(root: Path) -> list[str]:
    errors: list[str] = []
    schema_path = root / "hooks" / "schema" / "agent-hooks.schema.json"
    template_path = root / "hooks" / "templates" / "agent-hooks.example.json"
    codex_hooks = Path.home() / ".codex" / "hooks.json"
    cursor_hooks = Path.home() / ".cursor" / "hooks.json"

    if template_path.exists():
        errors.extend(validate_json_schema(load_json(template_path), schema_path, "agent-hooks.example.json"))
    else:
        errors.append(f"Missing hook template: {template_path}")

    for hook_path in (codex_hooks, cursor_hooks):
        if not hook_path.exists():
            errors.append(f"Missing hook config: {hook_path}")
            continue
        try:
            parsed = load_json(hook_path)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSON in {hook_path}: {exc}")
            continue
        if not isinstance(parsed.get("hooks"), dict):
            errors.append(f"Hook config missing hooks object: {hook_path}")
    errors.extend(validate_hook_install_manifest(root, root / "manifests" / "hook-install-manifest.json"))
    return errors


def iter_hook_commands(hooks: object) -> dict[str, list[str]]:
    commands_by_event: dict[str, list[str]] = {}
    if not isinstance(hooks, dict):
        return commands_by_event
    for event, entries in hooks.items():
        commands: list[str] = []
        if not isinstance(entries, list):
            commands_by_event[event] = commands
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if isinstance(entry.get("command"), str):
                commands.append(entry["command"])
            nested_hooks = entry.get("hooks")
            if isinstance(nested_hooks, list):
                for nested in nested_hooks:
                    if isinstance(nested, dict) and isinstance(nested.get("command"), str):
                        commands.append(nested["command"])
        commands_by_event[event] = commands
    return commands_by_event


def validate_hook_install_manifest(root: Path, manifest_path: Path) -> list[str]:
    if not manifest_path.exists():
        return [f"Missing hook install manifest: {manifest_path}"]
    data = load_json(manifest_path)
    errors: list[str] = []
    tools = data.get("tools", [])
    if not isinstance(tools, list):
        return [f"Hook install manifest tools must be an array: {manifest_path}"]

    for tool in tools:
        if not isinstance(tool, dict):
            errors.append("Hook install manifest tool entry must be an object")
            continue
        name = tool.get("name", "<unknown>")
        config_value = tool.get("config")
        if not isinstance(config_value, str) or not config_value:
            errors.append(f"Hook install manifest `{name}` missing config")
            continue
        config_path = Path(config_value).expanduser()
        if not config_path.exists():
            errors.append(f"Hook install config missing for {name}: {config_path}")
            continue
        try:
            parsed = load_json(config_path)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid hook install config for {name}: {config_path}: {exc}")
            continue
        commands_by_event = iter_hook_commands(parsed.get("hooks"))
        required_hooks = tool.get("required_hooks", [])
        if not isinstance(required_hooks, list):
            errors.append(f"Hook install manifest `{name}` required_hooks must be an array")
            continue
        for required in required_hooks:
            if not isinstance(required, dict):
                errors.append(f"Hook install manifest `{name}` required hook must be an object")
                continue
            event = required.get("event")
            command_contains = required.get("command_contains")
            if not isinstance(event, str) or not isinstance(command_contains, str):
                errors.append(f"Hook install manifest `{name}` required hook missing event or command_contains")
                continue
            commands = commands_by_event.get(event, [])
            if not any(command_contains in command for command in commands):
                errors.append(f"Hook install missing for {name} {event}: {command_contains}")
    return errors

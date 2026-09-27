#!/usr/bin/env python3
"""Project-scoped continuous-learning observations and instincts.

The backend intentionally stores observations separately from Pi session files. It
keeps only sanitized, project-local observations and exports curated instincts,
not transcripts or tool history.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PREFERENCE_PATTERNS = (
    re.compile(r"\balways\b", re.IGNORECASE),
    re.compile(r"\bnever\b", re.IGNORECASE),
    re.compile(r"\bprefer\b", re.IGNORECASE),
    re.compile(r"\bdon['’]?t\b", re.IGNORECASE),
    re.compile(r"\buse .+ instead of .+\b", re.IGNORECASE),
)
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{16,}\b", re.IGNORECASE),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(
        r"(?i)['\"]?(?:api[_-]?key|token|secret|password|authorization|auth)['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9._/\-+=]{8,}"
    ),
    re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
)
MAX_TEXT_CHARS = 5000


@dataclass(frozen=True)
class ProjectContext:
    project_id: str
    project_name: str
    project_root: str
    project_dir: Path
    is_global: bool
    remote: str = ""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def agents_root() -> Path:
    return Path(os.environ.get("AGENTS_ROOT", str(Path.home() / ".agents"))).expanduser().resolve()


def get_state_root() -> Path:
    override = os.environ.get("AGENTS_LEARNING_STATE_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return agents_root() / "state" / "learning"


def run_git(cwd: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def remote_identity(remote: str) -> str:
    if "://" not in remote:
        return remote
    parsed = urlsplit(remote)
    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    return urlunsplit((parsed.scheme, host, parsed.path, "", ""))


def detect_project(cwd: Path | str | None = None) -> ProjectContext:
    requested = Path(cwd or Path.cwd()).expanduser().resolve()
    configured = os.environ.get("CLAUDE_PROJECT_DIR")
    if configured and Path(configured).exists():
        requested = Path(configured).expanduser().resolve()

    project_root = run_git(requested, ["rev-parse", "--show-toplevel"])
    root = Path(project_root).resolve() if project_root else requested
    if not root.is_dir():
        return ProjectContext(
            project_id="global",
            project_name="global",
            project_root="",
            project_dir=get_state_root() / "global",
            is_global=True,
        )

    remote = run_git(root, ["remote", "get-url", "origin"]) if project_root else ""
    identity = remote_identity(remote) or str(root)
    project_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]
    return ProjectContext(
        project_id=project_id,
        project_name=root.name or "project",
        project_root=str(root),
        project_dir=get_state_root() / "projects" / project_id,
        is_global=False,
        remote=remote,
    )


def secure_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        pass


def ensure_layout(context: ProjectContext) -> None:
    root = get_state_root()
    secure_mkdir(root)
    secure_mkdir(root / "projects")
    secure_mkdir(root / "global" / "preferences")
    secure_mkdir(context.project_dir)
    secure_mkdir(context.project_dir / "instincts")
    if not context.is_global:
        register_project(context)


def project_observations_path(context: ProjectContext) -> Path:
    return context.project_dir / "observations.jsonl"


def project_instincts_path(context: ProjectContext) -> Path:
    return context.project_dir / "instincts"


def global_instincts_path() -> Path:
    return get_state_root() / "global" / "preferences"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def atomic_write_text(path: Path, content: str) -> None:
    secure_mkdir(path.parent)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    secure_mkdir(path.parent)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def register_project(context: ProjectContext) -> None:
    path = get_state_root() / "projects.json"
    payload = load_json(path, {"projects": []})
    entries = payload.get("projects", []) if isinstance(payload, dict) else []
    by_id = {str(item.get("project_id")): item for item in entries if isinstance(item, dict) and item.get("project_id")}
    by_id[context.project_id] = {
        "project_id": context.project_id,
        "project_name": context.project_name,
        "project_root": context.project_root,
        "updated_at": utc_now(),
    }
    entries = [
        {key: value for key, value in item.items() if key != "remote"}
        for item in by_id.values()
    ]
    content = json.dumps({"projects": sorted(entries, key=lambda item: item["project_id"])}, indent=2, ensure_ascii=False) + "\n"
    atomic_write_text(path, content)


def is_explicit_preference(text: str) -> bool:
    value = text.strip()
    return bool(value) and any(pattern.search(value) for pattern in PREFERENCE_PATTERNS)


def redact_text(text: str, max_chars: int = MAX_TEXT_CHARS) -> str:
    value = text[:max_chars]
    for pattern in SECRET_PATTERNS:
        value = pattern.sub("[REDACTED]", value)
    return value


def should_ignore(payload: dict[str, Any]) -> bool:
    if os.environ.get("ECC_SKIP_OBSERVE") == "1":
        return True
    if payload.get("agent_id"):
        return True
    cwd = str(payload.get("cwd", ""))
    return "observer-sessions" in cwd or ".claude-mem" in cwd


def observation_kind(payload: dict[str, Any], event: str, tool_name: str) -> str:
    if event == "UserPromptSubmit":
        return "user_prompt"
    if tool_name.lower() in {"apply_patch", "edit", "write"}:
        return "code_change"
    return "tool_result"


def record_observation(payload: dict[str, Any]) -> int:
    if should_ignore(payload):
        return 0

    requested_cwd = payload.get("cwd")
    cwd = Path(requested_cwd).expanduser() if isinstance(requested_cwd, str) and requested_cwd else Path.cwd()
    if not cwd.exists():
        cwd = Path.cwd()
    context = detect_project(cwd)
    ensure_layout(context)

    event = str(payload.get("event") or os.environ.get("GUARDRAIL_EVENT", "unknown"))
    prompt = str(payload.get("prompt") or payload.get("message") or "")
    tool_name = str(payload.get("tool_name") or payload.get("tool") or "")
    timestamp = utc_now()
    observation = {
        "id": f"obs_{uuid.uuid4().hex}",
        "timestamp": timestamp,
        "event": event,
        "kind": observation_kind(payload, event, tool_name),
        "scope": "project" if not context.is_global else "global",
        "project_id": context.project_id,
        "project_name": context.project_name,
        "project_root": context.project_root,
        "session_id": str(payload.get("session_id", "")),
        "tool_name": tool_name,
        "prompt": redact_text(prompt),
        "is_explicit_preference": is_explicit_preference(prompt),
    }
    append_jsonl(project_observations_path(context), observation)
    return 0


def normalize_action(text: str) -> str:
    content = text.strip()
    content = re.sub(r"^(always|please|can you|could you)\s+", "", content, flags=re.IGNORECASE)
    content = content.rstrip(". ")
    if content:
        content = content[0].upper() + content[1:]
    return f"{content}." if content else ""


def instinct_id(action: str) -> str:
    return "instinct_" + hashlib.sha256(action.lower().encode("utf-8")).hexdigest()[:16]


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def yaml_lines(value: Any, indent: int = 0) -> list[str]:
    spaces = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, (dict, list)) and item:
                lines.append(f"{spaces}{key}:")
                lines.extend(yaml_lines(item, indent + 2))
            else:
                scalar = yaml_scalar(item) if not isinstance(item, (dict, list)) else ("{}" if isinstance(item, dict) else "[]")
                lines.append(f"{spaces}{key}: {scalar}")
        return lines
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, dict):
                items = list(item.items())
                if not items:
                    lines.append(f"{spaces}- {{}}")
                    continue
                key, first = items[0]
                if isinstance(first, (dict, list)) and first:
                    lines.append(f"{spaces}- {key}:")
                    lines.extend(yaml_lines(first, indent + 4))
                else:
                    scalar = yaml_scalar(first) if not isinstance(first, (dict, list)) else ("{}" if isinstance(first, dict) else "[]")
                    lines.append(f"{spaces}- {key}: {scalar}")
                rest = dict(items[1:])
                if rest:
                    lines.extend(yaml_lines(rest, indent + 2))
            else:
                lines.append(f"{spaces}- {yaml_scalar(item)}")
        return lines
    return [f"{spaces}{yaml_scalar(value)}"]


def dump_yaml(value: Any) -> str:
    return "\n".join(yaml_lines(value)) + "\n"


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"", "null", "~"}:
        return None
    if value in {"true", "false"}:
        return value == "true"
    try:
        if re.fullmatch(r"-?\d+", value):
            return int(value)
        if re.fullmatch(r"-?(?:\d+\.\d*|\d*\.\d+)", value):
            return float(value)
    except ValueError:
        pass
    if value.startswith(('"', "'")):
        try:
            return json.loads(value) if value.startswith('"') else value[1:-1].replace("''", "'")
        except json.JSONDecodeError:
            return value.strip('"\'')
    return value


def parse_simple_yaml(text: str) -> Any:
    """Parse the small YAML subset emitted by dump_yaml when PyYAML is absent."""
    result: dict[str, Any] = {}
    list_key: str | None = None
    current_item: dict[str, Any] | None = None
    nested_list_key: str | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0 and ":" in line:
            key, raw_value = line.split(":", 1)
            key = key.strip()
            if raw_value.strip():
                result[key] = parse_scalar(raw_value)
                list_key = None
                current_item = None
                nested_list_key = None
            else:
                result[key] = []
                list_key = key
                current_item = None
                nested_list_key = None
            continue
        if list_key and indent == 2 and line.startswith("- "):
            body = line[2:].strip()
            item: dict[str, Any] = {}
            result[list_key].append(item)
            current_item = item
            nested_list_key = None
            if ":" in body:
                key, raw_value = body.split(":", 1)
                item[key.strip()] = parse_scalar(raw_value)
            continue
        if current_item and indent == 4 and ":" in line:
            key, raw_value = line.split(":", 1)
            if raw_value.strip():
                current_item[key.strip()] = parse_scalar(raw_value)
                nested_list_key = None
            else:
                current_item[key.strip()] = []
                nested_list_key = key.strip()
            continue
        if current_item and nested_list_key and indent == 6 and line.startswith("- "):
            current_item[nested_list_key].append(parse_scalar(line[2:]))
    return result


def load_yaml(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return parse_simple_yaml(text)


def normalize_instinct(value: Any, scope: str = "project") -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    action = value.get("action") or value.get("content") or value.get("trigger")
    if not isinstance(action, str) or not action.strip():
        return None
    try:
        confidence = float(value.get("confidence", 0.6))
    except (TypeError, ValueError):
        confidence = 0.6
    confidence = min(0.9, max(0.3, confidence))
    evidence = value.get("evidence", [])
    if not isinstance(evidence, list):
        evidence = [evidence]
    return {
        "trigger": str(value.get("trigger") or "explicit project preference"),
        "action": normalize_action(action),
        "confidence": round(confidence, 3),
        "domain": str(value.get("domain") or "workflow"),
        "scope": scope,
        "evidence": [str(item) for item in evidence if str(item)],
    }


def read_instincts(directory: Path, scope: str = "project") -> list[dict[str, Any]]:
    if not directory.exists():
        return []
    result: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.yaml")):
        try:
            value = load_yaml(path)
        except (OSError, ValueError, TypeError):
            continue
        if isinstance(value, dict) and isinstance(value.get("instincts"), list):
            values = value["instincts"]
        else:
            values = [value]
        for item in values:
            normalized = normalize_instinct(item, scope)
            if normalized:
                result.append(normalized)
    return result


def write_instinct(directory: Path, instinct: dict[str, Any]) -> Path:
    normalized = normalize_instinct(instinct, str(instinct.get("scope") or "project"))
    if not normalized:
        raise ValueError("Invalid instinct")
    path = directory / f"{instinct_id(normalized['action'])}.yaml"
    atomic_write_text(path, dump_yaml(normalized))
    return path


def current_observations(context: ProjectContext) -> list[dict[str, Any]]:
    return load_jsonl(project_observations_path(context))


def command_status(_: argparse.Namespace) -> int:
    context = detect_project()
    ensure_layout(context)
    projects_root = get_state_root() / "projects"
    known_projects = [item for item in projects_root.iterdir() if item.is_dir()] if projects_root.exists() else []
    payload = {
        "state_root": str(get_state_root()),
        "current_project": context.project_name,
        "current_project_id": context.project_id,
        "project_observations": len(current_observations(context)),
        "project_instincts": len(read_instincts(project_instincts_path(context))),
        "known_projects": len(known_projects),
        "session_store": None,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def command_projects(_: argparse.Namespace) -> int:
    projects_root = get_state_root() / "projects"
    entries: list[dict[str, Any]] = []
    if projects_root.exists():
        registry = load_json(get_state_root() / "projects.json", {"projects": []})
        by_id = {str(item.get("project_id")): item for item in registry.get("projects", []) if isinstance(item, dict)} if isinstance(registry, dict) else {}
        for project_dir in sorted(item for item in projects_root.iterdir() if item.is_dir()):
            metadata = by_id.get(project_dir.name, {})
            entries.append(
                {
                    "project_id": project_dir.name,
                    "project_name": metadata.get("project_name", project_dir.name),
                    "project_root": metadata.get("project_root", ""),
                    "observations": len(load_jsonl(project_dir / "observations.jsonl")),
                    "instincts": len(read_instincts(project_dir / "instincts")),
                }
            )
    print(json.dumps({"projects": entries}, ensure_ascii=False))
    return 0


def command_analyze(_: argparse.Namespace) -> int:
    context = detect_project()
    ensure_layout(context)
    grouped: dict[str, dict[str, Any]] = {}
    for row in current_observations(context):
        prompt = str(row.get("prompt") or "")
        if not row.get("is_explicit_preference") and not is_explicit_preference(prompt):
            continue
        action = normalize_action(prompt)
        if not action:
            continue
        key = action.lower()
        candidate = grouped.setdefault(
            key,
            {
                "trigger": "explicit project preference",
                "action": action,
                "confidence": 0.7,
                "domain": "workflow",
                "scope": "project",
                "evidence": [],
            },
        )
        evidence_id = str(row.get("id") or row.get("timestamp") or "observation")
        if evidence_id not in candidate["evidence"]:
            candidate["evidence"].append(evidence_id)
    existing = {item["action"].lower(): item for item in read_instincts(project_instincts_path(context))}
    created: list[dict[str, Any]] = []
    for key, candidate in grouped.items():
        prior = existing.get(key)
        evidence = list(dict.fromkeys((prior or {}).get("evidence", []) + candidate["evidence"]))
        candidate["evidence"] = evidence
        candidate["confidence"] = min(0.9, 0.7 + max(0, len(evidence) - 1) * 0.05)
        normalized = normalize_instinct(candidate, "project")
        if normalized:
            write_instinct(project_instincts_path(context), normalized)
            created.append(normalized)
    print(json.dumps({"project_id": context.project_id, "created_instincts": created, "count": len(created)}, ensure_ascii=False))
    return 0


def command_promote(_: argparse.Namespace) -> int:
    context = detect_project()
    ensure_layout(context)
    if context.is_global:
        print(json.dumps({"promoted": 0, "reason": "Current context is global; there is no project instinct to promote."}))
        return 0
    promoted = 0
    for instinct in read_instincts(project_instincts_path(context)):
        instinct["scope"] = "global"
        instinct["domain"] = instinct.get("domain") or "workflow"
        write_instinct(global_instincts_path(), instinct)
        promoted += 1
    print(json.dumps({"promoted": promoted, "target": str(global_instincts_path())}, ensure_ascii=False))
    return 0


def command_export(args: argparse.Namespace) -> int:
    context = detect_project()
    ensure_layout(context)
    instincts = read_instincts(project_instincts_path(context)) if not context.is_global else read_instincts(global_instincts_path(), "global")
    payload = {"project_id": context.project_id, "instincts": instincts}
    output = dump_yaml(payload)
    if args.output:
        atomic_write_text(Path(args.output).expanduser().resolve(), output)
        print(json.dumps({"exported": len(instincts), "output": str(Path(args.output).expanduser().resolve())}))
    else:
        print(output, end="")
    return 0


def command_import(args: argparse.Namespace) -> int:
    context = detect_project()
    ensure_layout(context)
    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        print(f"Missing import source: {source}", file=sys.stderr)
        return 2
    try:
        payload = load_yaml(source)
    except Exception as error:
        print(f"Invalid import source: {error}", file=sys.stderr)
        return 2
    values = payload.get("instincts", []) if isinstance(payload, dict) else []
    if not isinstance(values, list):
        print("Import source must contain an instincts list", file=sys.stderr)
        return 2
    imported = 0
    for value in values:
        normalized = normalize_instinct(value, "project")
        if normalized:
            write_instinct(project_instincts_path(context), normalized)
            imported += 1
    print(json.dumps({"imported": imported, "target": str(project_instincts_path(context))}, ensure_ascii=False))
    return 0


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def command_prune(args: argparse.Namespace) -> int:
    context = detect_project()
    ensure_layout(context)
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(0, args.days))
    rows = current_observations(context)
    kept: list[dict[str, Any]] = []
    removed = 0
    for row in rows:
        timestamp = parse_timestamp(row.get("timestamp"))
        if timestamp is not None and timestamp < cutoff:
            removed += 1
        else:
            kept.append(row)
    content = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in kept)
    atomic_write_text(project_observations_path(context), content)
    print(json.dumps({"removed": removed, "project_id": context.project_id}))
    return 0


def command_observe(_: argparse.Namespace) -> int:
    raw = sys.stdin.read().strip()
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    try:
        return record_observation(payload)
    except Exception as error:
        print(f"learning-observe: {error}", file=sys.stderr)
        return 0


def add_state_root(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument("--state-root", help=argparse.SUPPRESS)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Project-scoped continuous-learning state manager")
    parser.add_argument("--state-root", help="Learning state root override")
    commands = parser.add_subparsers(dest="command", required=True)

    for name, handler in (("status", command_status), ("analyze", command_analyze), ("promote", command_promote), ("projects", command_projects), ("observe", command_observe)):
        subparser = commands.add_parser(name)
        add_state_root(subparser)
        subparser.set_defaults(func=handler)

    export_parser = commands.add_parser("export")
    add_state_root(export_parser)
    export_parser.add_argument("--output")
    export_parser.set_defaults(func=command_export)

    import_parser = commands.add_parser("import")
    add_state_root(import_parser)
    import_parser.add_argument("source")
    import_parser.set_defaults(func=command_import)

    prune_parser = commands.add_parser("prune")
    add_state_root(prune_parser)
    prune_parser.add_argument("--days", type=int, default=30)
    prune_parser.set_defaults(func=command_prune)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.state_root:
        os.environ["AGENTS_LEARNING_STATE_ROOT"] = args.state_root
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

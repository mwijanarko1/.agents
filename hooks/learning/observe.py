#!/usr/bin/env python3
"""
Hook observer for project-scoped learning and global preference learning.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path("/Users/mikhail/.agents")))

from scripts.agent_learning import (  # noqa: E402
    append_jsonl,
    detect_project,
    ensure_layout,
    get_state_root,
    global_observations_path,
    is_explicit_preference,
    project_observations_path,
)
from scripts.session_store import SessionStore, state_db_path  # noqa: E402


SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{16,}\b", re.IGNORECASE),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(
        r"(?i)(api[_-]?key|token|secret|password|authorization|auth)\s*[:=]\s*['\"]?[A-Za-z0-9._/\-+=]{8,}"
    ),
    re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def redact_text(text: str, max_bytes: int = 5000) -> str:
    truncated = text[:max_bytes]
    for pattern in SECRET_PATTERNS:
        truncated = pattern.sub("[REDACTED]", truncated)
    return truncated


def scrub(value):
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [scrub(item) for item in value]
    if isinstance(value, dict):
        return {key: scrub(item) for key, item in value.items()}
    return value


def should_ignore(payload: dict) -> bool:
    if os.environ.get("ECC_SKIP_OBSERVE") == "1":
        return True
    if payload.get("agent_id"):
        return True
    cwd = str(payload.get("cwd", ""))
    if "observer-sessions" in cwd or ".claude-mem" in cwd:
        return True
    return False


def record(payload: dict) -> int:
    if should_ignore(payload):
        return 0

    cwd = payload.get("cwd")
    if cwd and Path(cwd).exists():
        os.chdir(cwd)
    context = detect_project()
    ensure_layout(context)

    event = str(payload.get("event") or os.environ.get("GUARDRAIL_EVENT", "unknown"))
    prompt = str(payload.get("prompt") or payload.get("message") or "")
    tool_name = str(payload.get("tool_name") or payload.get("tool") or "")
    if event == "UserPromptSubmit":
        kind = "user_prompt"
    elif tool_name == "apply_patch":
        kind = "code_change"
    else:
        kind = "tool_result"
    observation = {
        "timestamp": utc_now(),
        "event": event,
        "kind": kind,
        "scope": "global" if context.is_global else "project",
        "project_id": context.project_id,
        "project_name": context.project_name,
        "session_id": str(payload.get("session_id", "")),
        "tool_name": tool_name,
        "prompt": redact_text(prompt),
        "tool_input": scrub(payload.get("tool_input", {})),
        "tool_output": scrub(payload.get("tool_response", payload.get("tool_output", ""))),
        "is_explicit_preference": is_explicit_preference(prompt),
    }

    append_jsonl(project_observations_path(context), observation)
    if observation["is_explicit_preference"]:
        append_jsonl(global_observations_path(), observation)

    store = SessionStore(state_db_path(get_state_root()))
    session_id = observation["session_id"] or f"session-{context.project_id}"
    store.add_observation(
        session_id=session_id,
        project_id=context.project_id,
        project_name=context.project_name,
        project_root=context.project_root,
        event=observation["event"],
        kind=kind,
        tool_name=observation["tool_name"],
        prompt=observation["prompt"],
        tool_input=observation["tool_input"],
        tool_output=observation["tool_output"],
        timestamp=observation["timestamp"],
        scope=observation["scope"],
        raw=observation,
    )
    store.close()
    return 0


def main() -> int:
    try:
        raw = sys.stdin.read().strip()
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {}

    # Initialize root eagerly for caller visibility in tests and diagnostics.
    get_state_root().mkdir(parents=True, exist_ok=True)
    return record(payload)


if __name__ == "__main__":
    raise SystemExit(main())

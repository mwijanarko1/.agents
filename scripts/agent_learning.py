#!/usr/bin/env python3
"""
Project-scoped and global preference learning state manager.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

SCRIPT_ROOT = Path(__file__).resolve().parent.parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from scripts.agent_memory import build_memory_context_block
from scripts.agent_memory import MemoryStore
from scripts.session_store import SessionStore, state_db_path


PREFERENCE_PATTERNS = [
    r"\balways\b",
    r"\bnever\b",
    r"\bprefer\b",
    r"\bdon['’]?t\b",
    r"\buse .+ instead of .+\b",
]

CANDIDATE_FILE = "memory-candidates.jsonl"


@dataclass
class ProjectContext:
    project_id: str
    project_name: str
    project_root: str
    project_dir: Path
    is_global: bool


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def get_state_root() -> Path:
    env = os.environ.get("AGENTS_LEARNING_STATE_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path.home() / ".agents" / "state" / "learning"


def run_git(cwd: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def detect_project(cwd: Path | None = None) -> ProjectContext:
    cwd = (cwd or Path.cwd()).expanduser().resolve()
    state_root = get_state_root()

    project_root = ""
    env_project = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_project and Path(env_project).exists():
        project_root = str(Path(env_project).expanduser().resolve())
    if not project_root:
        project_root = run_git(cwd, ["rev-parse", "--show-toplevel"])

    if not project_root:
        global_dir = state_root / "global"
        return ProjectContext(
            project_id="global",
            project_name="global",
            project_root="",
            project_dir=global_dir,
            is_global=True,
        )

    root_path = Path(project_root)
    remote = run_git(root_path, ["remote", "get-url", "origin"])
    hash_source = remote or project_root
    project_id = hashlib.sha256(hash_source.encode("utf-8")).hexdigest()[:12]
    project_dir = state_root / "projects" / project_id
    return ProjectContext(
        project_id=project_id,
        project_name=root_path.name,
        project_root=project_root,
        project_dir=project_dir,
        is_global=False,
    )


def ensure_layout(context: ProjectContext) -> None:
    state_root = get_state_root()
    (state_root / "projects").mkdir(parents=True, exist_ok=True)
    (state_root / "global" / "preferences" / "instincts" / "personal").mkdir(parents=True, exist_ok=True)
    (state_root / "global" / "preferences" / "instincts" / "inherited").mkdir(parents=True, exist_ok=True)
    (state_root / "global" / "preferences").mkdir(parents=True, exist_ok=True)
    if not context.is_global:
        (context.project_dir / "instincts" / "personal").mkdir(parents=True, exist_ok=True)
        (context.project_dir / "instincts" / "inherited").mkdir(parents=True, exist_ok=True)


def project_observations_path(context: ProjectContext) -> Path:
    return context.project_dir / "observations.jsonl"


def global_observations_path() -> Path:
    return get_state_root() / "global" / "preferences" / "observations.jsonl"


def memory_candidates_path(state_root: Path | None = None) -> Path:
    return (state_root or get_state_root()) / CANDIDATE_FILE


def get_session_store() -> SessionStore:
    return SessionStore(state_db_path(get_state_root()))


def is_explicit_preference(text: str) -> bool:
    lowered = text.lower().strip()
    if not lowered:
        return False
    return any(re.search(pattern, lowered) for pattern in PREFERENCE_PATTERNS)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row))
            handle.write("\n")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload))
        handle.write("\n")


def read_memory_candidates(state_root: Path | None = None) -> list[dict[str, Any]]:
    return load_jsonl(memory_candidates_path(state_root))


def write_memory_candidates(candidates: list[dict[str, Any]], state_root: Path | None = None) -> None:
    write_jsonl(memory_candidates_path(state_root), candidates)


def write_memory_candidate(candidate: dict[str, Any], state_root: Path | None = None) -> None:
    candidates = read_memory_candidates(state_root)
    candidates = [item for item in candidates if item.get("id") != candidate.get("id")]
    candidates.append(candidate)
    write_memory_candidates(candidates, state_root)


def normalize_candidate_content(prompt: str) -> str:
    content = prompt.strip()
    content = re.sub(r"^(always|please|can you|could you)\s+", "", content, flags=re.IGNORECASE)
    if content:
        content = content[0].upper() + content[1:]
    return content.rstrip(".") + "."


def candidate_id_for(kind: str, content: str, project_id: str) -> str:
    digest = hashlib.sha256(f"{kind}:{project_id}:{content.lower()}".encode("utf-8")).hexdigest()[:12]
    return f"cand_{digest}"


def propose_memory_candidates(
    observations: list[dict[str, Any]],
    *,
    state_root: Path | None = None,
) -> list[dict[str, Any]]:
    existing = {item.get("id"): item for item in read_memory_candidates(state_root)}
    created: list[dict[str, Any]] = []
    for index, row in enumerate(observations, start=1):
        prompt = str(row.get("prompt") or "").strip()
        if row.get("kind") not in {None, "", "user_prompt"}:
            continue
        if not is_explicit_preference(prompt):
            continue
        project_id = str(row.get("project_id") or "global")
        project_name = str(row.get("project_name") or "global")
        scope = "global" if project_id == "global" or row.get("scope") == "global" else "project"
        content = normalize_candidate_content(prompt)
        candidate_id = candidate_id_for("user_preference", content, project_id)
        if existing.get(candidate_id, {}).get("status") in {"accepted", "rejected"}:
            continue
        evidence_id = row.get("id") or row.get("observation_id") or index
        candidate = {
            "id": candidate_id,
            "scope": scope,
            "project_id": project_id,
            "project_name": project_name,
            "kind": "user_preference",
            "content": content,
            "confidence": 0.8,
            "evidence_observation_ids": [evidence_id],
            "status": "proposed",
            "recommended_target": "user" if scope == "global" else "memory",
            "created_at": utc_now(),
        }
        existing[candidate_id] = candidate
        created.append(candidate)
    if created:
        write_memory_candidates(list(existing.values()), state_root)
    return created


def update_candidate_status(candidate_id: str, status: str, state_root: Path | None = None) -> dict[str, Any] | None:
    candidates = read_memory_candidates(state_root)
    selected = None
    for candidate in candidates:
        if candidate.get("id") == candidate_id:
            candidate["status"] = status
            candidate["decided_at"] = utc_now()
            selected = candidate
            break
    if selected:
        write_memory_candidates(candidates, state_root)
    return selected


def accept_memory_candidate(
    candidate_id: str,
    *,
    state_root: Path | None = None,
    memory_root: Path | None = None,
) -> dict[str, Any]:
    candidates = read_memory_candidates(state_root)
    candidate = next((item for item in candidates if item.get("id") == candidate_id), None)
    if not candidate:
        return {"success": False, "error": f"Candidate not found: {candidate_id}"}
    if candidate.get("status") != "proposed":
        return {"success": False, "error": f"Candidate is not proposed: {candidate_id}"}
    target = candidate.get("recommended_target") or "memory"
    if target not in {"user", "memory"}:
        return {"success": False, "error": f"Unsupported candidate target: {target}"}
    store = MemoryStore(memory_root)
    result = store.add(target, str(candidate.get("content") or ""))
    if not result.get("success"):
        return result
    update_candidate_status(candidate_id, "accepted", state_root)
    return {"success": True, "accepted": candidate_id, "target": target}


def instinct_markdown(instinct_id: str, trigger: str, content: str, scope: str, context: ProjectContext) -> str:
    lines = [
        "---",
        f"id: {instinct_id}",
        f"trigger: \"{trigger}\"",
        "confidence: 0.8",
        "domain: workflow",
        "source: observation",
        f"scope: {scope}",
    ]
    if not context.is_global:
        lines.append(f"project_id: {context.project_id}")
        lines.append(f"project_name: {context.project_name}")
    lines.extend(["---", "", content.strip(), ""])
    return "\n".join(lines)


def command_status(_: argparse.Namespace) -> int:
    context = detect_project()
    ensure_layout(context)
    project_rows = load_jsonl(project_observations_path(context))
    global_rows = load_jsonl(global_observations_path())

    projects_root = get_state_root() / "projects"
    known_projects = [item for item in projects_root.iterdir() if item.is_dir()] if projects_root.exists() else []
    store = get_session_store()
    sessions = store.list_sessions(limit=500)
    payload = {
        "state_root": str(get_state_root()),
        "state_db": str(state_db_path(get_state_root())),
        "current_project": context.project_name,
        "current_project_id": context.project_id,
        "project_observations": len(project_rows),
        "global_preference_observations": len(global_rows),
        "known_projects": len(known_projects),
        "stored_sessions": len(sessions),
    }
    print(json.dumps(payload))
    return 0


def command_projects(_: argparse.Namespace) -> int:
    projects_root = get_state_root() / "projects"
    entries = []
    if projects_root.exists():
        for project_dir in sorted(item for item in projects_root.iterdir() if item.is_dir()):
            obs = load_jsonl(project_dir / "observations.jsonl")
            entries.append(
                {
                    "project_id": project_dir.name,
                    "observations": len(obs),
                    "personal_instincts": len(list((project_dir / "instincts" / "personal").glob("*.md"))),
                    "inherited_instincts": len(list((project_dir / "instincts" / "inherited").glob("*.md"))),
                }
            )
    print(json.dumps({"projects": entries}))
    return 0


def command_sessions(args: argparse.Namespace) -> int:
    store = get_session_store()
    print(json.dumps({"sessions": store.list_sessions(limit=args.limit)}))
    return 0


def command_search(args: argparse.Namespace) -> int:
    context = detect_project()
    project_id = None if args.all_projects or context.is_global else context.project_id
    rows = get_session_store().search(args.query, project_id=project_id, limit=args.limit)
    print(json.dumps({"query": args.query, "results": rows}))
    return 0


def command_profile(args: argparse.Namespace) -> int:
    context = detect_project()
    project_id = args.project_id or context.project_id
    print(json.dumps({"profile": get_session_store().project_profile(project_id)}))
    return 0


def command_context(args: argparse.Namespace) -> int:
    context = detect_project()
    project_id = None if args.all_projects or context.is_global else context.project_id
    raw_context = get_session_store().build_context(args.query, project_id=project_id, budget_chars=args.budget_chars)
    print(build_memory_context_block(raw_context))
    return 0


def collect_current_observations(context: ProjectContext) -> list[dict[str, Any]]:
    rows = load_jsonl(project_observations_path(context))
    for index, row in enumerate(rows, start=1):
        row.setdefault("id", index)
    return rows


def command_analyze(_: argparse.Namespace) -> int:
    context = detect_project()
    ensure_layout(context)
    candidates = propose_memory_candidates(collect_current_observations(context))
    print(json.dumps({"created_candidates": candidates, "count": len(candidates)}))
    return 0


def command_propose(args: argparse.Namespace) -> int:
    context = detect_project()
    ensure_layout(context)
    observations = collect_current_observations(context)
    if args.all_projects:
        observations = []
        for path in sorted(get_state_root().glob("projects/*/observations.jsonl")):
            rows = load_jsonl(path)
            for index, row in enumerate(rows, start=1):
                row.setdefault("id", index)
            observations.extend(rows)
        global_rows = load_jsonl(global_observations_path())
        for index, row in enumerate(global_rows, start=1):
            row.setdefault("id", index)
        observations.extend(global_rows)
    candidates = propose_memory_candidates(observations)
    print(json.dumps({"candidates": candidates, "count": len(candidates)}))
    return 0


def command_review_candidates(args: argparse.Namespace) -> int:
    candidates = read_memory_candidates()
    if args.status:
        candidates = [item for item in candidates if item.get("status") == args.status]
    print(json.dumps({"candidates": candidates, "count": len(candidates)}))
    return 0


def command_accept_candidate(args: argparse.Namespace) -> int:
    result = accept_memory_candidate(args.candidate_id)
    print(json.dumps(result))
    return 0 if result.get("success") else 2


def command_reject_candidate(args: argparse.Namespace) -> int:
    candidate = update_candidate_status(args.candidate_id, "rejected")
    if not candidate:
        print(json.dumps({"success": False, "error": f"Candidate not found: {args.candidate_id}"}))
        return 2
    print(json.dumps({"success": True, "rejected": args.candidate_id}))
    return 0


def command_evolve(_: argparse.Namespace) -> int:
    context = detect_project()
    ensure_layout(context)
    instincts = sorted((context.project_dir / "instincts" / "personal").glob("*.md"))
    payload = {
        "project_id": context.project_id,
        "cluster_candidates": len(instincts),
        "note": "Use generated instincts to create higher-level skills/commands manually or in a follow-up task.",
    }
    print(json.dumps(payload))
    return 0


def command_export(args: argparse.Namespace) -> int:
    context = detect_project()
    ensure_layout(context)
    instincts_root = context.project_dir / "instincts" / "personal"
    payload = []
    for item in sorted(instincts_root.glob("*.md")):
        payload.append({"name": item.stem, "content": item.read_text(encoding="utf-8")})

    output = yaml.safe_dump({"project_id": context.project_id, "instincts": payload}, sort_keys=False)
    if args.output:
        Path(args.output).expanduser().write_text(output, encoding="utf-8")
    else:
        print(output.rstrip())
    return 0


def command_import(args: argparse.Namespace) -> int:
    context = detect_project()
    ensure_layout(context)
    source = Path(args.source).expanduser()
    if not source.exists():
        print(f"Missing import source: {source}", file=sys.stderr)
        return 2
    payload = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    instincts = payload.get("instincts", [])
    target_root = context.project_dir / "instincts" / "inherited"
    target_root.mkdir(parents=True, exist_ok=True)

    count = 0
    for instinct in instincts:
        name = instinct.get("name")
        content = instinct.get("content")
        if not isinstance(name, str) or not isinstance(content, str):
            continue
        (target_root / f"{name}.md").write_text(content, encoding="utf-8")
        count += 1
    print(json.dumps({"imported": count, "target": str(target_root)}))
    return 0


def command_promote(args: argparse.Namespace) -> int:
    context = detect_project()
    ensure_layout(context)
    source_root = context.project_dir / "instincts" / "personal"
    target_root = get_state_root() / "global" / "preferences" / "instincts" / "personal"
    target_root.mkdir(parents=True, exist_ok=True)

    moved = 0
    candidates = sorted(source_root.glob("*.md"))
    for item in candidates:
        if args.instinct and item.stem != args.instinct:
            continue
        shutil.copy2(item, target_root / item.name)
        moved += 1
    print(json.dumps({"promoted": moved, "target": str(target_root)}))
    return 0


def command_prune(args: argparse.Namespace) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    removed = 0
    for path in [global_observations_path(), *get_state_root().glob("projects/*/observations.jsonl")]:
        rows = load_jsonl(path)
        keep = []
        for row in rows:
            timestamp = row.get("timestamp")
            if not isinstance(timestamp, str):
                keep.append(row)
                continue
            try:
                parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                keep.append(row)
                continue
            if parsed < cutoff:
                removed += 1
            else:
                keep.append(row)
        write_jsonl(path, keep)
    print(json.dumps({"removed": removed}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Continuous learning state management")
    parser.add_argument("--state-root", help="Learning state root override")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_state_root_arg(subparser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        subparser.add_argument("--state-root", help="Learning state root override")
        return subparser

    add_state_root_arg(subparsers.add_parser("status")).set_defaults(func=command_status)
    add_state_root_arg(subparsers.add_parser("analyze")).set_defaults(func=command_analyze)
    propose_parser = add_state_root_arg(subparsers.add_parser("propose"))
    propose_parser.add_argument("--all-projects", action="store_true")
    propose_parser.set_defaults(func=command_propose)

    review_parser = add_state_root_arg(subparsers.add_parser("review-candidates"))
    review_parser.add_argument("--status", default="proposed")
    review_parser.set_defaults(func=command_review_candidates)

    accept_parser = add_state_root_arg(subparsers.add_parser("accept-candidate"))
    accept_parser.add_argument("candidate_id")
    accept_parser.set_defaults(func=command_accept_candidate)

    reject_parser = add_state_root_arg(subparsers.add_parser("reject-candidate"))
    reject_parser.add_argument("candidate_id")
    reject_parser.set_defaults(func=command_reject_candidate)
    add_state_root_arg(subparsers.add_parser("evolve")).set_defaults(func=command_evolve)
    add_state_root_arg(subparsers.add_parser("projects")).set_defaults(func=command_projects)

    sessions_parser = add_state_root_arg(subparsers.add_parser("sessions"))
    sessions_parser.add_argument("--limit", type=int, default=20)
    sessions_parser.set_defaults(func=command_sessions)

    search_parser = add_state_root_arg(subparsers.add_parser("search"))
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=10)
    search_parser.add_argument("--all-projects", action="store_true")
    search_parser.set_defaults(func=command_search)

    profile_parser = add_state_root_arg(subparsers.add_parser("profile"))
    profile_parser.add_argument("--project-id")
    profile_parser.set_defaults(func=command_profile)

    context_parser = add_state_root_arg(subparsers.add_parser("context"))
    context_parser.add_argument("query")
    context_parser.add_argument("--budget-chars", type=int, default=6000)
    context_parser.add_argument("--all-projects", action="store_true")
    context_parser.set_defaults(func=command_context)

    export_parser = add_state_root_arg(subparsers.add_parser("export"))
    export_parser.add_argument("--output")
    export_parser.set_defaults(func=command_export)

    import_parser = add_state_root_arg(subparsers.add_parser("import"))
    import_parser.add_argument("source")
    import_parser.set_defaults(func=command_import)

    promote_parser = add_state_root_arg(subparsers.add_parser("promote"))
    promote_parser.add_argument("instinct", nargs="?")
    promote_parser.set_defaults(func=command_promote)

    prune_parser = add_state_root_arg(subparsers.add_parser("prune"))
    prune_parser.add_argument("--days", type=int, default=30)
    prune_parser.set_defaults(func=command_prune)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.state_root:
        os.environ["AGENTS_LEARNING_STATE_ROOT"] = args.state_root
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

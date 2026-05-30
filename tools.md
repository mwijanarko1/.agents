---
summary: "Catalog of local .agents helper commands and shared operational tools."
read_when: "When choosing a helper command, validating .agents, syncing peer roots, recording TDD evidence, or using memory/learning tools."
---

# Tools Reference

Use this catalog when the task depends on local `.agents` helper commands. Do not load it for routine edits unless tool discovery matters.

## Policy and validation

```bash
python3 ~/.agents/scripts/validate_agent_policy.py
python3 ~/.agents/scripts/validate_agent_policy.py --all
python3 ~/.agents/scripts/agent_doctor.py
python3 ~/.agents/scripts/generate_skill_routing_index.py --check
python3 ~/.agents/scripts/docs_list.py --check
```

- `validate_agent_policy.py`: validates the shared policy contract and, with `--all`, schema/manifests/hooks/skills/docs/shared references.
- `agent_doctor.py`: read-only health check for policy, tests, routing-index freshness, and map coverage.
- `generate_skill_routing_index.py`: regenerates `manifests/skill-routing-index.json` from skill front matter.
- `docs_list.py`: lists docs by `summary` and `read_when`; `--check` enforces docs routing metadata.

## TDD evidence

```bash
python3 ~/.agents/scripts/tdd_evidence.py record-red --command "<test command>" --exit-code <code>
python3 ~/.agents/scripts/tdd_evidence.py record-green --command "<test command>" --exit-code 0
python3 ~/.agents/scripts/tdd_evidence.py except --kind <kind> --reason "<why>" --alternative-verification "<check>"
```

- Records RED/GREEN evidence in repo-local `.git/agent-notes/tdd-evidence.json`.
- Requires a real git repository; use an auditable exception when a repo-local evidence file is unavailable.

## Learning and memory

```bash
python3 ~/.agents/scripts/agent_learning.py status
python3 ~/.agents/scripts/agent_learning.py search "<query>"
python3 ~/.agents/scripts/agent_learning.py context "<task>"
python3 ~/.agents/scripts/agent_learning.py analyze
python3 ~/.agents/scripts/agent_learning.py promote
python3 ~/.agents/scripts/agent_memory.py add user "<preference>"
python3 ~/.agents/scripts/agent_memory.py context
python3 ~/.agents/scripts/agent_wiki.py status
python3 ~/.agents/scripts/agent_wiki.py search "<query>"
python3 ~/.agents/scripts/agent_wiki.py context "<query>"
python3 ~/.agents/scripts/agent_wiki.py import-agent-sessions
python3 ~/.agents/scripts/agent_wiki.py lint
```

- `agent_learning.py`: project-scoped observations, searchable session state, reviewable memory candidates.
- `agent_memory.py`: curated `USER.md` / `MEMORY.md` store and fenced memory-context rendering.
- `agent_wiki.py`: bridge to the durable Obsidian-style `llm-wiki` vault for cross-session/project memory, wiki search, linting, and Pi/CommandCode session refresh.

## Sync and peer roots

```bash
python3 ~/.agents/scripts/sync_peer_roots.py --check
python3 ~/.agents/scripts/sync_peer_roots.py
```

- Keeps Cursor, Codex, OpenCode, Antigravity, and Claude peer roots pointed at canonical `.agents` files.
- Prefer `--check` before mutating peer roots.

## AI bridge

```bash
ai-delegate --target <codex|cursor|opencode|claude|goose> --prompt "<task>"
ai-dispatch --target <codex|cursor|opencode|claude|goose> --prompt "<task>"
```

- Backup cross-tool delegation path.
- Use only when the user explicitly asks for bridge delegation and names the target tool.

## Downstream AGENTS template

```text
READ ~/.agents/AGENTS.md BEFORE ANYTHING (skip if missing).
Then follow repo-specific rules below.
```

Use this pointer instead of copying global shared rules into project repositories.

# .agents Index

This folder stores reusable agent behavior, skills, hooks, policy, and docs.

## Start Here

- Read `AGENTS.md` for universal operating rules.
- Read `docs/CODEBASE_MAP.md` for deeper architecture and maintenance paths.
- Read this file before broad searching in `.agents`.

## Folder Map

| Path | Purpose | Use When |
|---|---|---|
| `skills/` | Task-specific workflows and instructions | A user request matches a capability |
| `agents/` | Agent definitions and personas | Creating or changing configured agents |
| `docs/` | Architecture, operating model, explanations | Understanding how this system fits together |
| `hooks/` | Runtime automation hooks | Changing enforcement or run-time behavior |
| `scripts/` | Maintenance, validation, and helper commands | Updating or checking system assets |
| `schemas/` | Structured config contracts | Editing JSON/config formats |
| `manifests/` | Registry/metadata files | Inspecting installed skill or agent metadata |
| `tests/` | Regression checks | Verifying changes to scripts/hooks/policy |
| `state/` | Runtime memory and learning state | Only when the task asks about memory/state |

## Canonical Files

| File | Purpose |
|---|---|
| `AGENTS.md` | Main cross-agent instructions |
| `agent-policy.json` | Machine-readable policy/config |
| `tools.md` | Tool reference |
| `.agent-hooks.json` | Hook registration/config |
| `docs/CODEBASE_MAP.md` | Detailed architecture/navigation map |

## Where To Go

- Skill behavior: open `skills/INDEX.md`, then the matching `skills/<name>/SKILL.md`.
- Agent behavior: start in `agents/`, then check `AGENTS.md` for global rules.
- Hook failures or enforcement: start with `.agent-hooks.json`, then `hooks/` and `scripts/`.
- Schema or policy changes: start with `agent-policy.json` and `schemas/`.
- Broad system changes: read `docs/CODEBASE_MAP.md` before editing.

## Ignore Unless Asked

- `.pytest_cache/`
- `.git-agent-notes-backup/`
- `state/` runtime data
- generated manifests or lock files unless updating registry metadata

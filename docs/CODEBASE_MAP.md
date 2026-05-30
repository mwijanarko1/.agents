---
summary: "Canonical architecture map for the shared .agents root."
read_when: "Before changing agent policy, validators, hooks, schemas, manifests, sync logic, skills, or subagent routing."
last_mapped: 2026-04-01T14:30:00+01:00
---

# Codebase Map

## System Overview

This workspace is the canonical shared agent-control surface for Cursor, Codex, and OpenCode.
The important policy and execution files are concentrated in a small set of roots:

- `AGENTS.md`: top-level human-readable contract for skill composition and codebase awareness
- `agent-policy.json`: machine-readable enforcement contract for skills, delegation, and sync
- `scripts/validate_agent_policy.py`: validator for policy and shared-root invariants
- `scripts/lib/agent_validators.py`: reusable validator checks for schemas/manifests/frontmatter/personal-path constraints
- `scripts/tdd_evidence.py`: RED/GREEN TDD evidence CLI and exception tracking
- `scripts/agent_learning.py`: project-scoped learning CLI with reviewable memory candidates
- `scripts/session_store.py`: SQLite learning/session store with FTS5 search and LIKE fallback
- `scripts/agent_memory.py`: curated `USER.md` / `MEMORY.md` store with injection scanning and fenced context rendering
- `scripts/agent_doctor.py`: read-only health check that runs policy validation, tests, routing-index freshness, and map coverage
- `scripts/docs_list.py`: lists and validates documentation `summary` / `read_when` routing metadata
- `tools.md`: lazy-loaded catalog of local `.agents` helper commands
- `docs/DOWNSTREAM_AGENTS_TEMPLATE.md`: pointer-style template for repo-local `AGENTS.md` files
- `docs/OPERATING_MODEL.md`: explains which shared guidance belongs in AGENTS, policy, skills, docs, tools, hooks, or scripts
- `scripts/lib/agent_validators.py`: reusable validator checks, including `validate_docs_frontmatter`, `validate_shared_references`, `validate_supply_chain_recipes`, and `validate_subagent_policy_skill_alignment`
- `agents/`: canonical shared subagent definitions
- `skills/`: canonical shared skill library
- `schemas/`: JSON schemas for policy/manifests/learning state
- `manifests/`: sync manifest, imported skill provenance catalog, and generated skill-routing index
- `hooks/learning/observe.py`: sanitized hook observation writer for learning state
- `state/learning/state.db`: local SQLite database for searchable observations, sessions, summaries, semantic memory, and procedural memory
- `state/memory/`: curated memory files used for compact cross-session context
- `docs/`: local architecture inventory for the shared root

The shared policy also includes `output_economy`, the machine-readable contract for concise professional output. It keeps agent communication short without adopting gimmick voices or sacrificing precision for code, commands, errors, APIs, and verification.

Peer roots such as `~/.cursor`, `~/.config/opencode`, and `~/.codex` symlink back to this root for their shared policy surface.

## Directory Guide

| Path | Purpose |
|------|---------|
| [AGENTS.md](/Users/mikhail/.agents/AGENTS.md) | Canonical instructions for how the shared agent stack should be composed |
| [agent-policy.json](/Users/mikhail/.agents/agent-policy.json) | Machine-readable policy contract and sync metadata |
| [scripts/validate_agent_policy.py](/Users/mikhail/.agents/scripts/validate_agent_policy.py) | Policy validator and peer-root consistency gate |
| [scripts/lib/agent_validators.py](/Users/mikhail/.agents/scripts/lib/agent_validators.py) | Shared validator helpers used by `validate_agent_policy.py --all` |
| [scripts/tdd_evidence.py](/Users/mikhail/.agents/scripts/tdd_evidence.py) | Records and reports mandatory TDD RED/GREEN evidence |
| [scripts/agent_learning.py](/Users/mikhail/.agents/scripts/agent_learning.py) | Manages learning observations, search context, and reviewable memory candidates |
| [scripts/session_store.py](/Users/mikhail/.agents/scripts/session_store.py) | Stores searchable sessions and observations in SQLite |
| [scripts/agent_memory.py](/Users/mikhail/.agents/scripts/agent_memory.py) | Manages curated local memory and fenced context blocks |
| [scripts/agent_doctor.py](/Users/mikhail/.agents/scripts/agent_doctor.py) | Runs read-only shared-root health checks |
| [scripts/docs_list.py](/Users/mikhail/.agents/scripts/docs_list.py) | Lists and validates docs routing metadata |
| [tools.md](/Users/mikhail/.agents/tools.md) | Lazy-loaded helper command catalog |
| [docs/DOWNSTREAM_AGENTS_TEMPLATE.md](/Users/mikhail/.agents/docs/DOWNSTREAM_AGENTS_TEMPLATE.md) | Pointer-style downstream `AGENTS.md` template |
| [docs/OPERATING_MODEL.md](/Users/mikhail/.agents/docs/OPERATING_MODEL.md) | Guidance placement model for shared agent policy surfaces |
| [agents](/Users/mikhail/.agents/agents) | Shared clustered subagent definitions used by all tool roots |
| [skills](/Users/mikhail/.agents/skills) | Canonical skill implementations referenced across tools |
| [schemas](/Users/mikhail/.agents/schemas) | JSON schemas for policy/manifests/learning records |
| [manifests](/Users/mikhail/.agents/manifests) | Manifest metadata for sync, imported skill provenance, and generated skill routing |
| [docs/CODEBASE_MAP.md](/Users/mikhail/.agents/docs/CODEBASE_MAP.md) | Shared-root architecture map |
| [docs/GLOSSARY.md](/Users/mikhail/.agents/docs/GLOSSARY.md) | Shared terminology, including output economy terms |

## Key Workflows

1. Run the validator before substantial work: `python3 ~/.agents/scripts/validate_agent_policy.py --all`.
2. Run the full doctor when changing shared policy or validation: `python3 ~/.agents/scripts/agent_doctor.py`.
3. List docs routing metadata with `python3 ~/.agents/scripts/docs_list.py`; validate it with `python3 ~/.agents/scripts/docs_list.py --check`.
4. Review `docs/CODEBASE_MAP.md` before editing shared policy or skill surfaces.
5. Edit canonical shared files in `~/.agents` first when the peer roots are symlinked.
6. Re-run the validator after policy-surface changes.
7. Preserve output economy rules when editing communication instructions: concise professional output, no gimmick voice, exact technical terms.

## Known Risks

- Changes to `AGENTS.md` and `agent-policy.json` affect multiple tools at once via symlinks.
- Broad scans across peer roots are noisy because they contain history, caches, and stateful data.
- Command recipes in peer roots can drift from the shared policy unless they are reviewed alongside canonical guidance.
- Shared prompts can drift toward missing skills or nonexistent helper scripts; `validate_shared_references` catches the canonical policy surfaces.
- Supply-chain command examples can bypass policy accidentally; `validate_supply_chain_recipes` checks orchestration surfaces for forbidden executable recipes.
- Subagent prompts can drift from `capability_clusters`; `validate_subagent_policy_skill_alignment` keeps clustered subagents aligned.

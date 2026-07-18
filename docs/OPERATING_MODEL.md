---
summary: "Explanatory model for how AGENTS.md, agent-policy.json, skills, docs, hooks, and subagents fit together."
read_when: "When changing the shape of the shared agent system or deciding where new guidance should live."
---

# Operating Model

Keep each policy surface narrow:

- `AGENTS.md`: hard universal rules agents must see early.
- `agent-policy.json`: machine-enforceable contract and routing data.
- `skills/<name>/SKILL.md`: task-specific operational workflows.
- `docs/*.md`: explanatory material, templates, and optional references.
- `tools.md`: lazy-loaded helper command catalog.
- `hooks/` and `scripts/`: executable gates and local helper commands.

When adding guidance, prefer the narrowest home:

1. Use `agent-policy.json` for structured policy or validator-backed rules.
2. Use a skill for repeatable task workflow.
3. Use docs for explanation, templates, or context that should be loaded only when relevant.
4. Use `AGENTS.md` only for hard rules that must apply across tools and tasks.

All shared docs should have `summary` and `read_when` front matter so agents can route context without loading everything.

## State layers

Do not collapse these distinct forms of state:

| Layer | Location | Role |
|---|---|---|
| Conversation | Host chat/thread | User-visible turns; not durable memory |
| Harness | `AGENTS.md`, `agent-policy.json`, hooks, validators | Rules, routing, and gates |
| Workspace | Git working tree | Source of truth for code |
| Learning | `state/learning/` | Sanitized project observations |
| Memory | `state/memory/` and optional wiki | Curated long-lived context, never user commands |
| Handoff | `HANDOFF.md` or project docs | Short continuation note for humans and agents |

Skills define workflows; subagents define who runs a capability cluster. Learning logs are not handoffs, and handoff notes do not transfer final ownership away from the main agent.

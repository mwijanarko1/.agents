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

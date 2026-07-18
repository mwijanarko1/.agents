---
name: strategic-compact
description: "Compact context at phase boundaries, write handoffs, and audit context budget."
---

# Strategic Compact

Compact at logical boundaries, not mid-implementation. Also audit context overhead when sessions feel bloated.

## When to compact

| Transition | Compact? |
|------------|----------|
| Research → planning | Yes |
| Planning → implementation | Yes (plan is in a file/todo) |
| Implementation → testing | Maybe |
| Debugging → next feature | Yes |
| After a failed approach | Yes |
| Mid-implementation | No |

Cadence: phase boundaries, or every 4–5 substantive turns when context is growing.

## Before compacting

Write durable state first: goal, decisions, traps, key files, open work. Prefer `HANDOFF.md` / `$TMPDIR/handoff-<id>.md` under ~1k tokens. Reference files; do not paste secrets or full logs.

```markdown
# HANDOFF: <title>
## Goal
## Current State (DONE / PARTIAL / NOT STARTED)
## Decisions / Why
## Traps
## Relevant Files
## Open Work
```

## What survives vs lost

Persists: on-disk files, git state, memory files, written handoffs.
Lost: intermediate reasoning, prior file reads, tool history, verbal preferences not saved.

## Context budget audit

Use when sessions are sluggish, many skills/MCP tools were added, or the user asks for a budget check.

1. **Inventory** rough tokens for always-on instructions, loaded skills, agents, MCP tools, conversation growth.
2. **Classify** always / sometimes / rarely needed.
3. **Flag** bloated always-on text, redundant skills, MCP servers wrapping simple CLIs, oversized agent prompts.
4. **Report** estimated overhead + concrete drops or lazy-load moves. Prefer distillation (`context_needle.py`) over raw dumps.

## Command output protection

Unknown/large command output: byte-cap (`head -c 6000`) or write to temp and inspect ranges. Skip vendor/build/cache dirs unless required.

---
name: effective-agent-skills
description: "Create, edit, review, or audit agent skills. Use for new/update skill work, SKILL.md review, skill not triggering, or skill stocktake/audit."
---

# Effective Agent Skills

A skill is a small workflow loaded only when needed. Keep it narrow.

## Author checklist

- `name` matches folder name.
- `description` is what/when only (routing phrase), not the whole workflow.
- `SKILL.md` holds the 80% path; rare detail in linked references; fragile logic in scripts.
- Includes verify → fix → re-verify when output is checkable.
- Does not repeat universal rules from `AGENTS.md` / `agent-policy.json`.

## Description pattern

```text
<Capability> via <method>. Use when <triggers>. Different from <nearby skill> because <boundary>.
```

## Authoring flow

1. Check `skills/INDEX.md` for an existing skill to extend.
2. Write the smallest behavior-changing `SKILL.md`.
3. Add examples/references only when needed.
4. Regenerate routing index; run `python3 ~/.agents/scripts/validate_agent_policy.py`.

## Audit mode (stocktake)

Trigger: skill stocktake, audit skills, `/skill-stocktake`, full skill review.

1. Inventory `~/.agents/skills/*/SKILL.md` (and project `.agents/skills/` if present). List paths scanned.
2. For each skill (chunk ~20), verdict: **Keep** | **Improve** | **Update** | **Retire** | **Merge into [X]**.
3. Checklist: overlap with other skills; overlap with AGENTS/policy; stale tool/API refs; scope fit; uniqueness.
4. Reasons must be decision-enabling (defect + replacement for Retire; target + content for Merge; concrete edit for Improve).
5. Summarize table; require explicit user confirmation before delete/merge.

Quick scan: re-evaluate only mtime-changed skills when a prior results file exists; carry forward the rest.

## Anti-patterns

- Mega-skills (plan + implement + test + deploy)
- Style-only skills that belong in preferences
- Long theory the model already knows
- Frontmatter that summarizes steps
- Nested reference chains; scripts with no command example

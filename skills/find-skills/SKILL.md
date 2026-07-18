---
name: find-skills
description: Discover installable agent skills for a requested capability.
---

# Find Skills

Discover skills for a capability. Prefer local inventory first; do not ad-hoc install by default.

## Workflow

1. **Clarify** domain + task (e.g. React performance, PR review, PDF).
2. **Local first** — check `$AGENTS_ROOT/skills/` (or this tree's sibling skills), `skills/INDEX.md`, and the active tool's skill list.
3. **Public catalog** — browse/search https://skills.sh/ for well-known packages when local coverage is missing.
4. **Report** — name, source, what it does, install surface if any.
5. **Install only if the user asks** — use the tool's supported install path with a **pinned** source/ref. No `@latest`, no silent global installs, no mutable remote instruction execution.

## Output

```text
Need: <task>
Local matches: ...
Remote candidates: ...
Recommend: <one> because ...
Install: <exact command only if user requested install>
```

## Non-goals

- Do not run package-manager skill CLIs as a default side effect of search.
- Do not replace an already-loaded local skill with a remote duplicate without asking.

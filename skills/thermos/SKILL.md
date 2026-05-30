---
name: thermos
description: "Launch both thermo-nuclear review subagents in parallel, then synthesize their findings. Use for thermos, double thermo review, or combined bug/security and code-quality branch audits."
license: MIT
origin: Cursor Thermos plugin
source: https://github.com/cursor/plugins
adapted: true
disable-model-invocation: true
---

# Thermos

Run two thermo review passes in parallel, then synthesize their results:

- `/Users/mikhail/.agents/agents/thermo-nuclear-review-subagent.md` for bugs, breakages, security, devex regressions, feature-flag leaks, and other branch-audit risks.
- `/Users/mikhail/.agents/agents/thermo-nuclear-code-quality-review-subagent.md` for maintainability, structure, file-size growth, spaghetti, abstractions, and codebase-health risks.

## Workflow

1. Determine the review scope from the user request, PR, current branch, or relevant changed files.
2. Gather the diff and any file/context excerpts needed for reviewers to evaluate the change without guessing. Prefer `git diff <base>...HEAD` plus full contents of changed files when practical; default `<base>` to `main` unless the user specifies another base.
3. Launch both subagents in parallel with the same scoped review bundle:
   - `thermo-nuclear-review-subagent`
   - `thermo-nuclear-code-quality-review-subagent`
4. Ask each subagent to return prioritized findings with file references and concrete evidence.
5. After both finish, synthesize the results with findings first, deduplicated across reviewers. Weight overlapping findings more heavily, resolve disagreements with your own judgment, and keep summaries brief.

## Adapter notes

- In Pi, use `multi_tool_use.parallel` with two `subagent` calls when available.
- In Cursor/Claude-style adapters, use the platform's parallel Task/background-subagent mechanism.
- If parallel subagents are unavailable, run both reviews sequentially but keep their findings independent until final synthesis.

If individual subagent summaries are already visible to the user, do not restate them wholesale. Surface the unified verdict, the highest-signal findings, and any remaining uncertainty.

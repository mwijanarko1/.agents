---
name: dead-code-detector
description: "Scan codebases for dead/unused code — functions, types, imports, variables, exports, files — with language-aware heuristics, confidence levels, and safe reporting. No deletion without explicit approval."
license: MIT
metadata:
  author: ai-assisted
  version: "1.0"
  tags: [code-quality, dead-code, cleanup, refactoring, static-analysis]
---

# Dead Code Detector

Report-only unused-code scan. **Never delete without per-item explicit approval.**

## Safety

1. Report only until the user approves each removal.
2. Confidence: **HIGH** (no refs, tool-backed) / **MEDIUM** (dynamic use possible) / **LOW** (public API or partial scope).
3. Note false-positive risks: reflection, DI, routes, plugins, `cfg`, barrel re-exports.
4. Skip active PR churn, fixtures, generated, and vendored trees unless asked.
5. **No installs during scan.** Use tools already on PATH or in the project. Else `rg` fallback.

## Workflow

1. Scope paths/languages with the user if unclear.
2. Prefer project tools when present: knip/ts-prune/eslint unused, vulture/ruff, `go vet`/staticcheck, `cargo check` dead_code, periphery, etc. Invoke via project package scripts or direct binary — not ad-hoc downloaders.
3. Grep fallback: search symbol refs excluding definition file; count callers.
4. Annotate confidence + evidence; group HIGH → LOW.
5. On approved removals: delete only approved items; re-run build/tests.

## Report

```markdown
# Dead Code Report
Scope: ...
| Confidence | Symbol | Location | Evidence | FP notes |
```

## Non-goals

Drive-by refactors, mass deletes, dependency upgrades.

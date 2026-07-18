---
name: vercel-composition-patterns
description: Apply scalable React composition patterns and component APIs.
license: MIT
metadata:
  author: vercel
  version: "1.0.0"
---

# React Composition Patterns

Use when designing reusable component APIs or refactoring boolean-prop soup.

## Workflow

1. Spot API smells: many booleans, mutually exclusive modes, render-prop sprawl.
2. Open only the matching rule file under `rules/` (do not load all rules or `AGENTS.md` by default).
3. Apply the smallest composition fix; keep call sites compiling.
4. Verify with typecheck + the component's existing tests/story.

## Index (open `rules/<id>.md`)

| Priority | Prefix | Rules |
|----------|--------|--------|
| HIGH | `architecture-` | `avoid-boolean-props`, `compound-components` |
| MEDIUM | `state-` | `decouple-implementation`, `context-interface`, `lift-state` |
| MEDIUM | `patterns-` | `explicit-variants`, `children-over-render-props` |
| MEDIUM (React 19+) | `react19-` | `no-forwardref` |

Example path: `rules/architecture-compound-components.md`.

## Defaults

- Prefer compound components + context over `showX` / `isY` / `variantMode` booleans.
- Provider owns state implementation; consumers depend on a stable interface.
- Skip React 19 rules on React 18 projects.

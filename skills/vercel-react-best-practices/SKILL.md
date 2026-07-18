---
name: vercel-react-best-practices
description: Optimize React and Next.js code using Vercel best practices.
license: MIT
metadata:
  author: vercel
  version: "1.0.0"
---

# Vercel React Best Practices

Performance guidance for React/Next.js. Prefer the highest-impact categories first.

## Workflow

1. Identify the symptom (waterfall, huge bundle, server latency, rerenders).
2. Pick the category below; open only matching `rules/<id>.md` files.
3. Apply the smallest fix that removes the bottleneck.
4. Verify with the project's existing profiling/build/bundle tools — not new global installs.

Do **not** load `AGENTS.md` (full dump) unless the user asks for the compiled guide.

## Categories by priority

| Pri | Category | Prefix | Open when |
|-----|----------|--------|-----------|
| 1 | Waterfalls | `async-` | sequential awaits, slow RSC trees |
| 2 | Bundle | `bundle-` | large JS, heavy imports |
| 3 | Server | `server-` | RSC/auth/cache/serialization |
| 4 | Client fetch | `client-` | SWR/listeners/storage |
| 5 | Rerender | `rerender-` | unnecessary updates |
| 6 | Rendering | `rendering-` | list/SVG/hydration jank |
| 7 | JS hotspots | `js-` | hot loops/lookups |
| 8 | Advanced | `advanced-` | rare patterns |

Rule files live in `rules/` (e.g. `rules/async-parallel.md`, `rules/bundle-barrel-imports.md`). Each has incorrect/correct examples.

## Defaults

- Fix waterfalls and barrel imports before micro-memoization.
- Prefer project-local patterns (React `cache`, existing data libs) over new dependencies.

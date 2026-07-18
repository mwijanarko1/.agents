---
name: frontend-web-development
description: Implement Next.js and frontend web features.
---

# Frontend Web Development

Implement web features (prefer Next.js App Router when the repo uses it). Pair with `frontend-design` for visuals, `vercel-react-best-practices` / `vercel-composition-patterns` when optimizing or designing APIs.

## Workflow

1. Match existing project structure, package manager, and UI kit — do not invent a second stack.
2. Prefer Server Components for data; mark `'use client'` only for browser state/events.
3. Colocate feature UI, hooks, and server actions under the feature when the repo already does.
4. Forms: server actions or existing form lib; validate on server; accessible labels/errors.
5. Data: fetch on the server when possible; cache/revalidate with the project's existing patterns.
6. Verify with the project's typecheck/lint/test/dev scripts (from `package.json`), not assumed globals.

## Defaults

- **shadcn**: use existing `components/ui` and project `components.json`. Add missing pieces via the project's established shadcn workflow — not hand-rolled duplicates.
- **Icons**: check `package.json` first. Prefer already-installed sets. When adding is justified: Phosphor, Hugeicons, or Tabler before Lucide.
- Absolute imports (`@/…`) when the project already configures them.
- No new dependencies for one-liners stdlib/CSS can do.
- No `@latest` / ad-hoc executors for installs.

## Boundaries

- Accessibility basics on interactive UI (labels, keyboard, focus).
- Do not treat this skill as legal, SEO, or security gospel — pair the specialist skills.
- Prefer existing local conventions when they conflict with generic advice here.

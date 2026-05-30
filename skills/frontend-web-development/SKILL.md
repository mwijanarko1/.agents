---
name: frontend-web-development
description: "Implement Next.js and frontend web features."
---

# Web & Frontend Stack

## Scope

Use this skill for implementation and architecture of web features.

- Pair with `vercel-react-best-practices` for React and Next.js performance work.
- Pair with `vercel-composition-patterns` when designing reusable component APIs.
- Pair with `web-design-guidelines` for UI review and accessibility audits.
- Pair with `taste-skill` for new premium UI or `redesign-skill` for upgrading existing UI.
- **Icon preference:** Check `package.json` first. Prefer Phosphor, Hugeicons, or Tabler Icons over Lucide defaults.
- Do not use this skill as the sole source of legal, compliance, or SEO guidance.

## Iconography Defaults

- Check the project dependency file before importing an icon package.
- Prefer already-installed icon libraries to avoid unnecessary dependency churn.
- When choosing a new React icon set, prefer `@phosphor-icons/react`, Hugeicons (`@hugeicons/react` plus `@hugeicons/core-free-icons`), or `@tabler/icons-react`.
- Use Lucide only when the project already standardizes on `lucide-react`, when local components require it, or when adding a new package is not appropriate.
- Keep icon stroke/fill style consistent across a surface; do not mix outline weights casually.

## Project Setup Guidelines

### Directory Structure (Next.js App Router)
Enforce `src/` directory. Use Feature-First (Screaming) Architecture to colocate related logic.

```text
src/
├── app/                 # Next.js App Router (Routes & Layouts ONLY)
│   ├── (auth)/          # Route groups for organization
│   ├── api/             # API routes
│   └── layout.tsx
├── features/            # Business Logic (Domain-driven)
│   ├── [feature-name]/
│   │   ├── components/  # Feature-specific components
│   │   ├── hooks/       # Feature-specific hooks
│   │   ├── services/    # Data fetching/Server Actions
│   │   └── types/       # Feature-specific types
├── components/          # Shared/Generic Components
│   ├── ui/              # ShadCN primitives (buttons, inputs)
│   └── layout/          # Global layout (nav, footer)
├── lib/                 # Shared Utilities
│   ├── db.ts            # DB connection
│   └── utils.ts         # Helper functions
├── types/               # Global TypeScript definitions
└── env/                 # Environment validation schemas
```

### Dependency Management
- **Package Manager:** Use `npm` or `pnpm` consistently.
- **Lockfile:** Always commit `package-lock.json` or `pnpm-lock.yaml`.
- **Versioning:**
  - Pin exact versions for core deps (remove `^` or `~`).
  - Use semantic versioning for utilities.
- **Vetting:**
  - Prefer packages with >1k stars and recent updates.
  - Audit size with `bundle-phobia` before adding.
- **Separation:** Strictly separate `dependencies` vs `devDependencies`.

### Environment Variables
- **Validation:** Use Zod or T3 Env to validate all env vars at build/runtime.
- **Template:** Maintain an up-to-date `.env.example` with dummy values.
- **Naming:**
  - Server-only: `DB_PASSWORD`, `API_SECRET`
  - Client-exposed: `NEXT_PUBLIC_API_URL`
- **Security:**
  - Never commit `.env` files.
  - Add `.env*` to `.gitignore` (except `.env.example`).

## Frontend Development Guidelines

### UI/UX Principles
- **Mobile-First Design:** Implement styles for mobile viewports first, then use `sm:`, `md:`, `lg:` breakpoints for larger screens.
- **Feedback Loops:** Provide immediate visual feedback for all interactions.
  - *Active:* Button press states.
  - *Loading:* Skeleton loaders (ShadCN `Skeleton`) preferred over spinners for initial page loads.
  - *Outcome:* Toast notifications (`sonner`/`toast`) for success/error events.
- **Layout Stability:** Prevent Cumulative Layout Shift (CLS) by defining explicit dimensions for images and reserving space for async content.
- **Touch Targets:** Ensure interactive elements are at least 44x44px for mobile accessibility.

### Accessibility (A11y)
- **Standard:** Target WCAG 2.1 Level AA compliance.
- **Semantic HTML:** Use native elements (`<button>`, `<a>`, `<input>`) over `div` soups. Never use `onClick` on non-interactive elements without `role` and `tabIndex`.
- **Keyboard Navigation:** Ensure visible focus states (`ring-offset`, `focus-visible`) on all interactive elements. No keyboard traps.
- **Screen Readers:**
  - Use `aria-label` for icon-only buttons.
  - Ensure form inputs have associated `<label>` elements.
  - Use `sr-only` class for text that should be hidden visually but available to screen readers.
- **Color Contrast:** Verify text/background ratios meet 4.5:1 standard.

### State Management
- **URL as Source of Truth:** Store filter, pagination, and sort parameters in the URL (`searchParams`) rather than local state to enable shareable/bookmarkable links.
- **Server vs. Client:**
  - Prefer Server Components for fetching.
  - Use `React Query` (or equivalent) only if polling or client-side caching is strictly necessary.
- **Local State:** Use `useState` for simple, ephemeral UI state (modals, inputs).
- **Zustand/Context:** Reserve for truly global app state (user preferences, authentication tokens). Avoid "Context Hell."

### Component Reusability
- **Atomic Design:** Build from primitives (Buttons, Inputs) -> Molecules (Form Groups) -> Organisms (Tables, Cards).
- **Styling Composition:**
  - Use `clsx` and `tailwind-merge` (`cn()` utility) to allow parent components to safely override/extend child styles.
  - Avoid hardcoding margins/positioning on the component itself; let the parent control layout.
- **Variant Management:** Use `class-variance-authority` (CVA) to define type-safe component variants (e.g., `variant="outline"`, `size="sm"`).
- **Slot Pattern:** Use `Radix UI` Slot primitive (via ShadCN `asChild`) to allow components to change their underlying HTML tag (polymorphism) while maintaining styles.

## Implementation Checks

These are build-time checks. For review-heavy UI audits, use `web-design-guidelines` as the primary audit skill.

### Accessibility
- Icon-only buttons need `aria-label`
- Form controls need `<label>` or `aria-label`
- Interactive elements need keyboard handlers (`onKeyDown`/`onKeyUp`)
- `<button>` for actions, `<a>`/`<Link>` for navigation (not `<div onClick>`)
- Images need `alt` (or `alt=""` if decorative)
- Decorative icons need `aria-hidden="true"`
- Async updates (toasts, validation) need `aria-live="polite"`
- Use semantic HTML (`<button>`, `<a>`, `<label>`, `<table>`) before ARIA
- Headings hierarchical `<h1>`–`<h6>`; include skip link for main content
- `scroll-margin-top` on heading anchors

### Focus States
- Interactive elements need visible focus: `focus-visible:ring-*` or equivalent
- Never `outline-none` / `outline: none` without focus replacement
- Use `:focus-visible` over `:focus` (avoid focus ring on click)
- Group focus with `:focus-within` for compound controls

### Forms
- Inputs need `autocomplete` and meaningful `name`
- Use correct `type` (`email`, `tel`, `url`, `number`) and `inputmode`
- Never block paste (`onPaste` + `preventDefault`)
- Labels clickable (`htmlFor` or wrapping control)
- Disable spellcheck on emails, codes, usernames (`spellCheck={false}`)
- Checkboxes/radios: label + control share single hit target (no dead zones)
- Submit button stays enabled until request starts; spinner during request
- Errors inline next to fields; focus first error on submit
- Placeholders end with `…` and show example pattern
- `autocomplete="off"` on non-auth fields to avoid password manager triggers
- Warn before navigation with unsaved changes (`beforeunload` or router guard)

### Animation
- Honor `prefers-reduced-motion` (provide reduced variant or disable)
- Animate `transform`/`opacity` only (compositor-friendly)
- Never `transition: all`—list properties explicitly
- Set correct `transform-origin`
- SVG: transforms on `<g>` wrapper with `transform-box: fill-box; transform-origin: center`
- Animations interruptible—respond to user input mid-animation

### Typography
- `…` not `...`
- Curly quotes `"` `"` not straight `"`
- Non-breaking spaces: `10&nbsp;MB`, `⌘&nbsp;K`, brand names
- Loading states end with `…`: `"Loading…"`, `"Saving…"`
- `font-variant-numeric: tabular-nums` for number columns/comparisons
- Use `text-wrap: balance` or `text-pretty` on headings (prevents widows)

### Content Handling
- Text containers handle long content: `truncate`, `line-clamp-*`, or `break-words`
- Flex children need `min-w-0` to allow text truncation
- Handle empty states—don't render broken UI for empty strings/arrays
- User-generated content: anticipate short, average, and very long inputs

### Images
- `<img>` needs explicit `width` and `height` (prevents CLS)
- Below-fold images: `loading="lazy"`
- Above-fold critical images: `priority` or `fetchpriority="high"`

### Performance & Hydration
- **Performance:**
  - Large lists (>50 items): virtualize (`virtua`, `content-visibility: auto`)
  - No layout reads in render (`getBoundingClientRect`, `offsetHeight`, `offsetWidth`, `scrollTop`)
  - Batch DOM reads/writes; avoid interleaving
  - Prefer uncontrolled inputs; controlled inputs must be cheap per keystroke
  - Add `<link rel="preconnect">` for CDN/asset domains
  - Critical fonts: `<link rel="preload" as="font">` with `font-display: swap`
- **Hydration Safety:**
  - Inputs with `value` need `onChange` (or use `defaultValue` for uncontrolled)
  - Date/time rendering: guard against hydration mismatch (server vs client)
  - `suppressHydrationWarning` only where truly needed

### Navigation & State
- URL reflects state—filters, tabs, pagination, expanded panels in query params
- Links use `<a>`/`<Link>` (Cmd/Ctrl+click, middle-click support)
- Deep-link all stateful UI (if uses `useState`, consider URL sync via nuqs or similar)
- Destructive actions need confirmation modal or undo window—never immediate

### Touch & Interaction
- `touch-action: manipulation` (prevents double-tap zoom delay)
- `-webkit-tap-highlight-color` set intentionally
- `overscroll-behavior: contain` in modals/drawers/sheets
- During drag: disable text selection, `inert` on dragged elements
- `autoFocus` sparingly—desktop only, single primary input; avoid on mobile

### Safe Areas & Layout
- Full-bleed layouts need `env(safe-area-inset-*)` for notches
- Avoid unwanted scrollbars: `overflow-x-hidden` on containers, fix content overflow
- Flex/grid over JS measurement for layout

### Dark Mode & Theming
- `color-scheme: dark` on `<html>` for dark themes (fixes scrollbar, inputs)
- `<meta name="theme-color">` matches page background
- Native `<select>`: explicit `background-color` and `color` (Windows dark mode)

### Locale & i18n
- Dates/times: use `Intl.DateTimeFormat` not hardcoded formats
- Numbers/currency: use `Intl.NumberFormat` not hardcoded formats
- Detect language via `Accept-Language` / `navigator.languages`, not IP

### Content & Copy
- Active voice: "Install the CLI" not "The CLI will be installed"
- Title Case for headings/buttons (Chicago style)
- Numerals for counts: "8 deployments" not "eight"
- Specific button labels: "Save API Key" not "Continue"
- Error messages include fix/next step, not just problem
- Second person; avoid first person
- `&` over "and" where space-constrained

### Anti-patterns (flag these)
- `user-scalable=no` or `maximum-scale=1` disabling zoom
- `onPaste` with `preventDefault`
- `transition: all`
- `outline-none` without focus-visible replacement
- Inline `onClick` navigation without `<a>`
- `<div>` or `<span>` with click handlers (should be `<button>`)
- Images without dimensions
- Large arrays `.map()` without virtualization
- Form inputs without labels
- Icon buttons without `aria-label`
- Hardcoded date/number formats (use `Intl.*`)
- `autoFocus` without clear justification

## Performance Optimization Guidelines

### Asset Loading & Bundle Size
- **Images:**
  - Mandate `next/image` for automatic optimization (WebP/AVIF conversion).
  - Explicitly set `width` and `height` (or `fill` with parent aspect ratio) to prevent Layout Shifts (CLS).
  - Set `priority={true}` ONLY for the Largest Contentful Paint (LCP) element (e.g., hero image); lazy load all others.
- **Code Splitting:**
  - Use `next/dynamic` to lazy load heavy components (charts, maps, rich text editors) that are below the fold.
  - Implement Route-based code splitting (default in Next.js).
- **Fonts:**
  - Use `next/font` to host fonts locally at build time.
  - Enforce `display: swap` or `optional` to prevent blocking text rendering.
- **Scripts:**
  - Use `next/script` with appropriate strategies (`lazyOnload` for analytics, `worker` for heavy computations).

### Caching Strategy
- **Hierarchy:**
  1. **Browser/CDN:** Use `Cache-Control` headers. Implement `stale-while-revalidate` for high-availability content.
  2. **Next.js Data Cache:** Memoize fetch requests. Use `revalidateTag` (On-Demand Revalidation) over time-based revalidation for cleaner data consistency.
  3. **Memoization:** Deduplicate identical fetch requests within a single render pass using React `cache()`.
- **Database Caching:** Implement a Redis/KV layer for expensive aggregation queries that update infrequently.
- **Static vs Dynamic:** Prefer Static Site Generation (SSG/ISR) for marketing pages. Use Partial Prerendering (PPR) where applicable.

### Database Query Optimization
- **N+1 Prevention:**
  - Strictly prohibit N+1 query patterns. Use `JOIN`s, `include` (ORM), or Dataloader patterns to batch requests.
- **Selectivity:**
  - Ban `SELECT *`. Explicitly select only required columns to reduce network payload and memory usage.
- **Indexing:**
  - Enforce indexes on all columns used in `WHERE`, `ORDER BY`, and Foreign Key joins.
  - Review `EXPLAIN ANALYZE` output for any query taking >100ms.
- **Pagination:**
  - Implement Cursor-based pagination (keyset) for infinite scroll or large datasets (performance O(1)).
  - Avoid Offset-based pagination for tables with >10k rows (performance O(N)).
- **Connection Pooling:** Ensure a connection pooler (e.g., PgBouncer) is configured for serverless environments to prevent connection exhaustion.

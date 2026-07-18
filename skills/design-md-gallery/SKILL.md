---
name: design-md-gallery
description: "Secondary product visual-language reference only after frontend-design: match or borrow from known brands in the DESIGN.md gallery. Do not use alone; pair after frontend-design for greenfield or redesign polish."
---

# DESIGN.md Gallery

Secondary reference after `frontend-design` when the user wants a product/brand feel that exists in the local gallery.

## Rules

1. Product constraints and existing design system win.
2. `frontend-design` still owns structure and anti-slop.
3. This skill supplies reference tokens/atmosphere only — inspiration, not blind copy.
4. Never load this skill alone for greenfield UI.

## Use

1. Map the request to a gallery slug (e.g. vercel, linear.app, stripe, notion).
2. Read only:

```text
$AGENTS_ROOT/vendor/awesome-design-md/design-md/<slug>/DESIGN.md
```

If `$AGENTS_ROOT` is unset, resolve from this skills tree: `../../vendor/awesome-design-md/design-md/<slug>/DESIGN.md`.

3. Extract atmosphere, color roles, typography, surfaces, component cues relevant to the task.
4. Apply through `frontend-design` + project implementation constraints.

## Non-goals

Do not override a11y, performance, or existing design-system tokens. Do not scrape live sites here — use `extract-design-md` for new DESIGN.md extraction.

---
name: frontend-design
description: "Primary web frontend design skill for UI design, visual redesign, landing pages, typography, color, layout, motion, and polish. Use for greenfield screens, redesigns, anti-AI-slop audits, and reference-DNA studies. Pair with frontend-web-development for implementation."
---

# Frontend Design

Primary visual design + anti-slop skill for web UI. Replaces old `taste-skill` / `redesign-skill` / `soft-skill` aliases.

## Modes

### Build (default)

1. Pre-flight: existing tokens, components, fonts, brand constraints in the repo.
2. Infer audience, job-to-be-done, tone (or ask once if it changes the design).
3. Pick structure before paint: hierarchy, sections, primary action.
4. Pick a system: type scale, palette roles, spacing rhythm, surfaces, motion.
5. Implement within project constraints (`frontend-web-development`).
6. Run the slop check before handoff.

### Audit (no edits unless asked)

Report only:

```text
[critical|major|minor] issue — file:line
  why it reads generic / weak hierarchy / inaccessible
  concrete fix
```

### Reference DNA

From a URL/screenshot/brand: extract palette roles, type, density, surface language, distinctive motifs — then adapt, do not clone copyrighted assets.

## Slop check (fail if present)

- Generic AI font stacks (Inter/Roboto/Arial defaults with no character) when brand allows better
- Even purple-on-white gradients, hero-with-three-feature-cards cliché without product reason
- Flat hierarchy; every card identical weight
- Decorative motion that blocks tasks or ignores `prefers-reduced-motion`
- Low-contrast text/icons; missing focus states
- Placeholder stock imagery / lorem left in final UI

## Pairing

- `frontend-web-development` — implementation
- `design-md-gallery` — known-brand DESIGN.md references only
- `design-systems-reference` — tokens/component-library work only
- Not for backend, legal, or SEO alone

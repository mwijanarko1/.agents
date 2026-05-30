---
name: design-md-gallery
description: "Reference known product visual languages after a primary design skill."
---

# DESIGN.md Gallery

Use this skill when the user wants a UI that looks like, feels like, or is inspired by a specific product or brand that exists in the local DESIGN.md gallery.

## Scope

- This is a secondary reference skill, not a primary design planner.
- Use it after `taste-skill` for greenfield work.
- Use it after `redesign-skill` for upgrades to existing UI.
- `soft-skill` can still be layered on after this for extra polish.
- Do not use this skill alone.
- Do not let it override accessibility, functionality, performance, or existing design-system constraints.

## Priority Rules

When this skill is combined with the existing design stack, use this precedence:

1. Product constraints and existing design system
2. Primary mode: `taste-skill` or `redesign-skill`
3. `design-md-gallery` reference tokens and art direction
4. `soft-skill` polish pass

This means:

- The primary mode still decides structure, intent, and when to be bold versus restrained.
- This skill supplies visual reference material: palette, typography, surfaces, component styling, and atmosphere.
- If a reference file conflicts with baseline anti-slop rules, treat the reference as inspiration, not a blind copy.

## How To Use

1. Identify the target reference. Examples:
   - "make it feel like Vercel"
   - "use a Linear-style dark interface"
   - "give this a Mintlify docs feel"
2. Load only the relevant DESIGN.md file from:
   - `/Users/mikhail/.agents/vendor/awesome-design-md/design-md/<slug>/DESIGN.md`
3. Extract only the parts that matter for the task:
   - atmosphere
   - color roles
   - typography
   - component styling
   - layout principles
4. Apply those tokens through the active primary design mode instead of copying the page literally.
5. Preserve the existing product’s IA, accessibility, and behavior unless the user explicitly asked for a larger redesign.

## When To Prefer Existing Skills

- If the user only wants "premium", "high-end", or "make it better", use `taste-skill` or `redesign-skill` without this skill.
- If the user names a brand, website, or aesthetic source, use this skill as the reference layer.
- If the user wants motion polish after the reference is applied, add `soft-skill`.

## Available Reference Slugs

Commonly useful references in the local gallery:

- `vercel`
- `linear.app`
- `cursor`
- `mintlify`
- `supabase`
- `notion`
- `stripe`
- `framer`
- `figma`
- `raycast`
- `warp`
- `claude`
- `opencode.ai`
- `expo`
- `resend`
- `sentry`
- `posthog`

The full catalog lives at:

- `/Users/mikhail/.agents/vendor/awesome-design-md/design-md/`

## Working Rules

- Never bulk-read the entire gallery.
- Read one reference first; read a second only if the user explicitly wants a hybrid.
- Do not reproduce brand copy, logos, or exact marketing structure verbatim.
- Use the reference for design language, not trademark mimicry.


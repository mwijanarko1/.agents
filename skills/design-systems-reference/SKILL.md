---
name: design-systems-reference
description: "Secondary design reference only after frontend-design: design system tokens, component APIs, accessibility patterns, and licensing. Do not use alone for new UI; load for component libraries, docs, and a11y checks after frontend-design."
---

# Design Systems Reference

Secondary skill after `frontend-design` for component libraries, tokens, a11y patterns, and asset licensing.

## When

- Building/auditing reusable UI kits
- Defining color/spacing/type tokens and themes
- Checking component API consistency and a11y
- Verifying font/icon licenses for production

## Map, not gospel

Index of public systems: https://github.com/alexpate/awesome-design-systems

Open the **system's own docs** for anything you apply. The list is a directory, not a ranking.

Compare: component APIs, token structure, a11y guidance, docs shape, content/voice notes.

## Checklist

- Tokens: roles (not raw hex in components), spacing scale, type ramp, dark/light if required
- Components: variants explicit, states covered (hover/focus/disabled/loading/error), composition over boolean prop soup
- A11y: keyboard, focus, labels, contrast AA+, live regions for async errors
- License: fonts/icons/components cleared for the distribution model

## Pairing

Always with `frontend-design` (+ `frontend-web-development` for implementation). Icon package choice lives in `frontend-web-development`.

---
name: shipswift-recipes
description: >
  Opt-in ShipSwift recipe workflow only. Use when the user explicitly asks for ShipSwift,
  recipe browsing, or names a ShipSwift component/feature. Modes: browse, add-component,
  build-feature. Not for general iOS/SwiftUI work.
---

# ShipSwift Recipes (opt-in)

Production-ready SwiftUI recipes via ShipSwift MCP tools (`listRecipes`, `searchRecipes`, `getRecipe`).

**Load only when the user opts in** (mentions ShipSwift, recipe catalog, or asks to add/build from ShipSwift). For ordinary iOS work use `ios-development` and the Swift specialists.

## Prerequisites

1. Call `listRecipes` to confirm the ShipSwift recipe server is available.
2. If tools are missing: stop. Point the user to [shipswift.app](https://shipswift.app) setup. Do **not** run `npx`, `skills add`, or other ad-hoc installers.

Pro recipes may require a license and `SHIPSWIFT_API_KEY` ([pricing](https://shipswift.app/pricing)).

## Modes

### browse
1. `listRecipes` — present by category (Animation, Chart, Component, Module).
2. Optional filter: category arg or `searchRecipes` keywords.
3. On pick: `getRecipe` — show purpose, architecture, customization, code shape, recipe ID, Free/Pro tier.
4. Suggest combinations when useful (e.g. onboarding + typewriter + shimmer).

### add-component
1. Identify type (animation / chart / UI / module).
2. `searchRecipes` with the component name or type.
3. `getRecipe` for full Swift source, architecture, integration steps, gotchas.
4. Adapt to the project (naming, models, design system).
5. Walk the recipe integration checklist (deps, Info.plist, etc.).

### build-feature
1. Break the request into UI / data / navigation / backend pieces.
2. `searchRecipes` with multiple keyword passes if needed.
3. `getRecipe` for each candidate.
4. Show an integration plan before coding (recipes used, wiring, customizations).
5. Adapt and combine recipes; finish with the combined checklist.

## Conventions

- Types: `SW` prefix (`SWDonutChart`, `SWTypewriter`).
- View modifiers: `.sw` prefix (`.swShimmer()`, `.swGlowScan()`).
- Charts: generic `CategoryType` with `String` convenience init; line draw via `.mask()` + animated `Rectangle` width.
- Helpers: `private` + `SW` prefix; add `cornerRadius` when clipping.
- Prefer recipe search before from-scratch UI; keep Views light; support Dark Mode and Dynamic Type.

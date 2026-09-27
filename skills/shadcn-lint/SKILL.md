---
name: shadcn-lint
description: Install and configure @shadcn/lint in Tailwind v4 projects using the project's existing ESLint or Oxlint setup. Use when asked to set up shadcn lint, enforce design-system styling rules, or diagnose @shadcn/lint configuration.
metadata:
  author: shadcn-ui
  upstream: https://github.com/shadcn-ui/lint
  upstream-ref: 53de86f0e7dcc341a9cb45c383a9f2c454d1e958
---

# shadcn lint

Set up `@shadcn/lint` in the target project. The package is project-local, not a global agent dependency.

## Requirements

- Tailwind CSS v4
- Node.js 20.19 or later
- ESLint 9.30 or later, or Oxlint 1.80 or later

## Setup workflow

1. Read the target repository's nearest `AGENTS.md`, package manifest, lockfile, workspace config, lint config, `components.json`, Tailwind theme files, and existing lint scripts.
2. Detect the package manager and whether the lint configuration belongs to the root, an app, or a shared package.
3. Use the linter that already checks UI files. If both ESLint and Oxlint exist, do not register the plugin twice. If neither exists, use Oxlint.
4. Install `@shadcn/lint` as a development dependency in the package that owns the lint config. Preserve the project's package-manager conventions and pinned-version policy.
5. Register only the plugin. Do not enable rules, presets, policy overrides, or suppressions unless the user explicitly asks to define a design-system policy.
6. Preserve existing parsers, rules, ignores, scripts, framework config, and workspace boundaries.
7. Run the existing lint command. If none exists, add the smallest package script that invokes the chosen linter, then run it.
8. Report configuration failures separately from pre-existing lint findings. State that plugin-only setup does not enforce design-system rules.

## ESLint registration

Use the existing flat config. Add the import and plugin entry to the config object that checks JavaScript, TypeScript, JSX, or TSX:

```js
import { plugin as shadcn } from "@shadcn/lint"

export default [
  {
    plugins: { shadcn },
  },
]
```

Keep the framework's parser setup. Only add `@typescript-eslint/parser` and JSX parser options when the project does not already parse its UI files.

## Oxlint registration

Add the plugin without changing existing rules:

```json
{
  "jsPlugins": ["@shadcn/lint"]
}
```

Merge with existing `jsPlugins` instead of replacing them.

## Project discovery

- Prefer `components.json` for shadcn/ui component aliases and theme discovery.
- For custom design systems, add only the required `settings.shadcn` keys: `ui`, `componentImports`, `ignoreImports`, `mergeFunctions`, `variantFunctions`, or `note`.
- In monorepos, keep app-specific themes and settings scoped to their apps. Follow existing shared-config dependency conventions.
- When rules are later enabled, turn component-self-styling rules off in the actual component source directory.

## Policy adoption

Choosing what styling is allowed is a user-owned design-system decision. Do not infer a restrictive policy from examples alone.

Available rules:

- `shadcn/no-restyle`
- `shadcn/no-raw-colors`
- `shadcn/no-arbitrary-values`
- `shadcn/no-inline-styles`
- `shadcn/no-unknown-classes`
- `shadcn/require-static-classes`

For an existing codebase, start rules at `warn`, inspect representative findings, document intentional tokens, variants, contracts, and exceptions, then raise agreed rules to `error`.

## Verification

- Confirm the target package resolves `@shadcn/lint`.
- Run the repository's lint script or workspace lint task.
- Re-read every edited config file.
- Run `git diff` and verify every changed hunk belongs to this setup.
- If agent instructions should enforce lint after future edits, add the repository's actual lint command to its local `AGENTS.md` only when requested.

## Upstream reference

This workflow is based on `shadcn-ui/lint` commit `53de86f0e7dcc341a9cb45c383a9f2c454d1e958`. Check current upstream documentation before installing because package and linter compatibility can change.
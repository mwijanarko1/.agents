---
name: create-pi-package
description: Create, test, and optionally publish Pi packages containing extensions, skills, prompt templates, or themes. Use when the user says make a Pi package, bundle Pi resources, publish to pi.dev/packages, or invokes /skill:create-pi-package.
---

# Create Pi Package

Build the smallest valid package around the resources the user actually has.

## Workflow

1. Read Pi's current `docs/packages.md` completely. Read `docs/skills.md`, `docs/extensions.md`, `docs/prompt-templates.md`, or `docs/themes.md` only for resource types included in the package. Resolve these under the installed `@earendil-works/pi-coding-agent` docs directory.
2. Inspect the requested source directory and reuse existing files. If no path or package name is available and cannot be inferred, ask once.
3. Create or update the minimum package structure:
   - `package.json` with name, version, description, license, `keywords: ["pi-package"]`, a restrictive `files` list, and explicit `pi` resource paths.
   - `README.md` with installation and usage.
   - Only the resource directories actually needed: `extensions/`, `skills/`, `prompts/`, `themes/`.
4. Put third-party runtime modules in `dependencies`. Put Pi core packages imported by extensions in `peerDependencies` with `"*"`, following the current package docs.
5. Verify locally:

```bash
npm pack --dry-run
pi -e /absolute/path/to/package
```

Run the nearest resource-specific check too. Fix failures and rerun the failed check.
6. Report the created files and exact install command. Do not run `npm publish`, create a public repository, or overwrite an existing package version unless the user explicitly asks.
7. When publishing is requested, confirm npm authentication and package-name availability, then publish. Use `npm publish --access public` for a public scoped package. Verify with `npm view <name> version` and `pi install npm:<name>`.

The Pi gallery discovers public npm packages through the `pi-package` keyword; there is no separate gallery submission.

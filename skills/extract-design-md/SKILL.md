---
name: extract-design-md
description: Extract a Stitch-compatible DESIGN.md from a public website. Use Ditto only when the installed CLI supports design-only extraction; otherwise inspect the live page and write the design brief directly. Use when the user asks to extract DESIGN.md, design tokens, or an agent-readable design doc from a URL. Different from cloning because it writes only the design-system brief, not a runnable app.
---

# Extract DESIGN.md

Produce a design brief, not a runnable clone.

## Workflow

1. If `$DITTO_ROOT` points to a local Ditto checkout, check capability before running it:

```bash
cd "$DITTO_ROOT"
npm run clone -- --help 2>&1 | grep -q -- '--design-md'
```

2. Only when that check succeeds, extract without publishing:

```bash
npm run clone -- https://example.com/ --mode=single --design-md=./designs/example.md
```

3. If the check fails, do not pass the unknown flag. The current local Ditto CLI silently ignores unknown options and performs a full clone. Instead use `pinchtab` to capture a full-page screenshot plus page text, inspect linked CSS or source HTML with `fetch_content` or `curl`, and write `DESIGN.md` directly from observed evidence. Do not invent tokens that cannot be observed.

4. Verify YAML front matter and this section order: Overview, Colors, Typography, Layout, Elevation & Depth, Shapes, Components, Do's and Don'ts. Include `colors`, `typography`, `spacing`, and `rounded` tokens only when detected.

## Boundaries

- Public, browser-accessible pages only.
- Single-page extraction only.
- Full runnable clones use `ditto-clone`.

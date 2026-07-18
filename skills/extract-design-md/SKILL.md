---
name: extract-design-md
description: Extract a Stitch-compatible DESIGN.md from a public website via Ditto. Use when the user asks to extract DESIGN.md, design tokens, or an agent-readable design doc from a URL. Different from cloning because it writes only the design-system brief, not a runnable app.
---

# Extract DESIGN.md

Use a local Ditto checkout to extract design docs from a public URL (not a full clone app).

## Workflow

1. Use `$DITTO_ROOT` if set, else a local Ditto checkout the user points at (commonly a `ditto.site` clone).
2. Extract without publishing:

```bash
cd "$DITTO_ROOT"
npm run clone -- https://example.com/ --design-md
# or explicit path:
npm run clone -- https://example.com/ --design-md=./designs/example.md
```

Default output is under Ditto's `compiler/output/<site>/DESIGN.md`.

3. Verify the file has YAML front matter (`---`), token sections when detected (`colors`, `typography`, `spacing`, `rounded`), and ordered sections: Overview, Colors, Typography, Layout, Elevation & Depth, Shapes, Components, Do's and Don'ts.

## Boundaries

- Public, browser-accessible pages only.
- Prefer `--mode=single`; multi-page DESIGN.md extraction is not supported by this CLI option yet.
- Full runnable clones → `ditto-clone`, not this skill.

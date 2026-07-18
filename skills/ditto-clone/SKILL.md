---
name: ditto-clone
description: Full-clone a public website into a runnable app via local Ditto. Use when the user asks to clone a site, recreate a page with near-parity code, or produce a Ditto app from a URL. Different from extract-design-md because this emits a runnable app, not only DESIGN.md.
---

# Ditto Clone

Use Ditto's local compiler when the user wants a **runnable near-parity clone** of a public URL.

## Workflow

1. Prefer an existing local Ditto checkout. In this environment it is usually:

   ```bash
   cd ~/tmp/ditto.site
   ```

2. Full clone (default Next + Tailwind):

   ```bash
   npm run clone -- https://example.com/ --out=./output
   ```

   Output layout:

   ```text
   output/<site>/app/      # runnable app
   output/<site>/.clone/   # capture/working artifacts
   ```

3. Useful flags:

   ```bash
   npm run clone -- https://example.com/ --out=./output --mode=multi
   npm run clone -- https://example.com/ --out=./output --framework=vite
   npm run clone -- https://example.com/ --out=./output --styling=css
   npm run clone -- https://example.com/ --out=./output --serve
   npm run clone -- https://example.com/ --out=./output --open
   ```

4. Verify:

   ```bash
   cd output/<site>/app
   npm install
   npm run build   # or npm run dev
   ```

## Boundaries

- Public, browser-accessible pages only.
- Prefer `--mode=single` unless the user explicitly wants multi-page.
- Do not use this skill when the user only wants tokens/`DESIGN.md` — use `extract-design-md` instead.
- Near-parity, not guaranteed pixel-perfect. Report the output path and any clone failures honestly.

---
name: ditto-clone
description: Full-clone a public website into a runnable app via local Ditto. Use when the user asks to clone a site, recreate a page with near-parity code, or produce a Ditto app from a URL. Different from extract-design-md because this emits a runnable app, not only DESIGN.md.
---

# Ditto Clone

Use Ditto's local compiler when the user wants a **runnable near-parity clone** of a public URL (full UI, interactions, motion when capture succeeds).

## Browser substrate (required)

On this machine, **do not install Playwright browsers** and do not launch Google Chrome / stock Chromium for Ditto.

1. **PinchTab owns browser control.** Prefer PinchTab for navigation, screenshots, HTML dumps, multi-page inspection, and any agent-driven browse work around the clone.
2. **Helium is the browser binary.** Playwright (inside Ditto only) must launch Helium:

   ```text
   /Applications/Helium.app/Contents/MacOS/Helium
   ```

   Override with `DITTO_BROWSER_EXECUTABLE` or `HELIUM_PATH` if needed.
3. If PinchTab `doctor` or `instance list` shows a headed instance, prefer headless for clone capture so focus is not stolen.
4. Never run `npx playwright install` / `playwright install chromium` as part of this skill.

## Workflow

1. Prefer an existing local Ditto checkout:

   ```bash
   cd ~/tmp/ditto.site
   ```

   If missing: `git clone --depth 1 https://github.com/ion-design/ditto.site.git ~/tmp/ditto.site` then `npm ci` in that repo. Do **not** install Playwright browser packs.

2. Ensure Helium is available (PinchTab doctor is enough):

   ```bash
   pinchtab doctor
   test -x /Applications/Helium.app/Contents/MacOS/Helium
   ```

3. Full clone (default Next + Tailwind). Use multi when the user wants all pages / full site UI:

   ```bash
   # single page (default)
   npm run clone -- https://example.com/ --out=./output

   # full multi-page site (UI + routes). On Helium use concurrency=1.
   npm run clone -- https://example.com/ --out=./output --mode=multi --concurrency=1
   ```

   Output layout:

   ```text
   output/<site>/app/      # runnable app
   output/<site>/.clone/   # capture/working artifacts
   ```

4. Useful flags:

   ```bash
   npm run clone -- https://example.com/ --out=./output --mode=multi --concurrency=1
   npm run clone -- https://example.com/ --out=./output --framework=vite
   npm run clone -- https://example.com/ --out=./output --styling=css
   npm run clone -- https://example.com/ --out=./output --serve
   npm run clone -- https://example.com/ --out=./output --open
   npm run clone -- https://example.com/ --out=./output --reuse   # regenerate from last capture, no browser
   ```

5. Optional PinchTab pass **before or after** Ditto when you need human-visible checks, route inventory, or motion screenshots the agent can reason about:

   ```bash
   TOKEN_FILE="${TMPDIR:-/tmp}/pinchtab-ditto.token"
   umask 077
   pinchtab session create --agent-id ditto-clone > "$TOKEN_FILE"
   export PINCHTAB_SESSION="$(cat "$TOKEN_FILE")"
   pinchtab nav https://example.com/ --snap
   pinchtab screenshot /tmp/ditto-ref.png
   # ... inspect routes, then close tab + revoke session (required)
   ```

6. Verify:

   ```bash
   cd output/<site>/app
   npm install
   npm run build   # or npm run dev
   ```

## Helium launch patch (local checkout)

Ditto's stock `chromium.launch()` downloads Playwright Chromium. On this Mac, patch capture + crawl once so launch uses Helium:

- Files: `compiler/src/capture/capture.ts`, `compiler/src/crawl/crawl.ts`
- Add `executablePath` from `process.env.DITTO_BROWSER_EXECUTABLE` || `process.env.HELIUM_PATH` || `/Applications/Helium.app/Contents/MacOS/Helium`

If the checkout already has that patch, do not re-apply.

## Boundaries

- Public, browser-accessible pages only.
- Prefer `--mode=single` unless the user explicitly wants multi-page / full-site UI and animations across routes.
- Do not use this skill when the user only wants tokens/`DESIGN.md`. Use `extract-design-md` instead.
- Near-parity, not guaranteed pixel-perfect. Report the output path and any clone failures honestly.
- PinchTab for agent browsing; Helium binary for Ditto's Playwright capture. No Playwright browser install.

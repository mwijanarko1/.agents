---
name: playwright-browser
description: "Drive a real browser with Playwright using Helium as the Chromium binary. Use when the user wants Playwright browser automation, open/search a site, YouTube search, click-through flows, or headed browser control. Different from agent_browser because this uses Playwright + Helium, not the pi-agent-browser-native tool."
argument-hint: "[url | --youtube query | --search query]"
compatibility: Requires Node.js, Playwright, and Helium.app
metadata:
  tags: [playwright, helium, browser, youtube, automation]
---

# Playwright + Helium Browser

Always launch Playwright with **Helium**, never bundled Chromium/Chrome.

## Binary

Default: `/Applications/Helium.app/Contents/MacOS/Helium`  
Override: `HELIUM_PATH`.

## One-shot open

From this skill directory (`skills/playwright-browser`):

```bash
node scripts/open.mjs --youtube "query"
node scripts/open.mjs --search "query"
node scripts/open.mjs "https://example.com"
node scripts/open.mjs --headless "https://example.com"
```

If `playwright` is not resolvable from cwd, run from a project that has it installed, or use this skill's local install (`package.json` + lockfile in this folder). Do **not** run browser-download installers when using Helium.

## Automation rules

- Prefer role/text/label selectors over brittle CSS/XPath.
- Re-query after navigation; don't reuse stale handles.
- Headed by default for user-visible flows; `--headless` for smoke checks.
- Never paste secrets into pages from chat when a native credential dialog exists.

## Diff from agent_browser

This skill is Playwright + Helium. Use `agent_browser` when the pi-native browser tool is the right surface.

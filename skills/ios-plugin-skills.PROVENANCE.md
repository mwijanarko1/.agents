# iOS plugin skills — provenance

Source plugin: OpenAI curated `build-ios-apps`  
Manifest version: `0.1.2`  
Pin path: `/Users/mikhail/.codex/plugins/cache/openai-curated/build-ios-apps/d6169bef/`  
Repository (upstream): `https://github.com/openai/plugins` (plugin id `build-ios-apps`)

## Active symlinks (skills/ → pin)

| Skill | Target under pin `skills/` |
|-------|----------------------------|
| ios-app-intents | ios-app-intents |
| ios-debugger-agent | ios-debugger-agent |
| ios-ettrace-performance | ios-ettrace-performance |
| ios-memgraph-leaks | ios-memgraph-leaks |
| swiftui-liquid-glass | swiftui-liquid-glass |
| swiftui-performance-audit | swiftui-performance-audit |
| swiftui-ui-patterns | swiftui-ui-patterns |
| swiftui-view-refactor | swiftui-view-refactor |

Do **not** edit files under the pin or under `~/.codex/.tmp/plugins/`.

## Disabled

| Skill | Status |
|-------|--------|
| ios-simulator-browser | Local stub only — refuses `serve-sim@latest` / `npx --yes` until pinned |

Upstream copy remains at pin `skills/ios-simulator-browser` (unused).

## Re-pin

1. Confirm new hash under `~/.codex/plugins/cache/openai-curated/build-ios-apps/<hash>/`.
2. Update the eight symlinks to that hash.
3. Update this file’s pin path and version from `.codex-plugin/plugin.json`.
4. Re-check for `@latest` / `npx` in any skill before re-enabling `ios-simulator-browser`.

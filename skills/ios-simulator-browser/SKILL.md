---
name: ios-simulator-browser
description: >
  DISABLED. Do not use. iOS Simulator browser mirroring is disabled until serve-sim
  is version-pinned. Refuse all serve-sim / npx @latest execution. Use
  ios-debugger-agent for simulator build/run/UI instead.
---

# iOS Simulator Browser — DISABLED

This skill is **disabled** until `serve-sim` is pinned to a fixed version (no `@latest` / `npx --yes`).

## Required behavior

1. **Do not** run `npx`, `npx --yes`, `serve-sim@latest`, or any floating-tag install/exec.
2. **Do not** follow the upstream plugin workflow for browser mirroring or SwiftUI preview host.
3. Tell the user the skill is disabled for supply-chain safety.
4. For simulator work, use `ios-debugger-agent` (XcodeBuildMCP) instead.

## Re-enable criteria (parent / future phase)

- Pin `serve-sim` to an exact version (or brew formula / local binary).
- Retarget or restore from the OpenAI `build-ios-apps` plugin pin documented in `skills/ios-plugin-skills.PROVENANCE.md`.
- Replace this stub with a symlink only after unsafe `@latest` paths are gone from the active body.

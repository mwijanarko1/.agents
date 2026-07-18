---
name: electron-app-release
description: Build, notarize, and publish Electron app releases for macOS (arm64 + x64) and Windows (arm64). Create GitHub releases, upload artifacts, and update website auto-update metadata. Use when the user says "rebuild", "new release", "bump version", "deploy", "dist", or wants to publish a new version.
---

# Electron App Release

Ship an Electron app: version bump → build/sign/notarize → GitHub release → auto-update metadata. **Publishing/notarizing/uploading requires explicit user confirmation.** Prefer dry-run/local build first.

## Config

Resolve from the target project (do not hardcode personal Desktop paths):

| Value | Source |
|-------|--------|
| App root | cwd or user-specified project |
| Website/metadata repo | user-specified or project docs |
| GitHub repo | `gh repo view --json nameWithOwner` or remote |
| Product name | `package.json` / electron-builder config |

## Workflow

1. **Clean tree** — commit intentional changes; note current version.
2. **Bump version** in `package.json` (and any lock/metadata files the app uses). Commit only after user wants the bump.
3. **Build locally first** using **project scripts** from `package.json` (e.g. `bun run dist:mac`, `npm run dist`). Prefer locked local binaries over ad-hoc `npx`.
4. **Sign/notarize** only with project-documented env vars/certs; stop on failure and show logs tail.
5. **Confirm publish** — show version, artifact names, target repo/tag.
6. **GitHub release** — `gh release create` with generated artifacts; handle HTTP/CLI errors.
7. **Auto-update metadata** — update the website/feed files the project uses; verify URLs resolve.
8. **Post-check** — `gh release view`, artifact list, metadata file diff, smoke-open app if practical.

## Gates

- No publish without explicit confirmation.
- Dev/local artifact verification before production upload.
- On any non-zero build/sign/`gh` failure: stop, report, do not partially ship tags.
- Never embed notarization passwords in the skill or chat logs.

## Commands pattern

```bash
cd "$APP_DIR"
# use scripts defined by the project, e.g.:
# bun run dist:mac
# bun run dist:win
gh release create "v$VERSION" dist/* --title "v$VERSION" --notes-file "$NOTES"
```

Adjust to the repo's actual script names and artifact paths.

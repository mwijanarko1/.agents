---
name: electron-app-release
description: Build, notarize, and publish Electron app releases for macOS (arm64 + x64) and Windows (arm64). Create GitHub releases, upload artifacts, and update website auto-update metadata. Use when the user says "rebuild", "new release", "bump version", "deploy", "dist", or wants to publish a new version.
---

# Electron App Release

Complete workflow for building, notarizing, and publishing Electron app releases with GitHub Releases and auto-update metadata.

## Project Configuration

These are project-specific values — adjust for your project:

```bash
# Project root
PROJECT_DIR="/Users/mikhail/Desktop/ayati-quran-desktop-companion"

# Website (auto-update metadata destination)
WEBSITE_DIR="/Users/mikhail/Documents/CURSOR CODES/In Progress/ayati-website"

# GitHub repo
GH_REPO="mwijanarko1/ayati-quran-desktop-companion"

# Electron app product name (for artifact filenames)
PRODUCT_NAME="Ayati - Quran Desktop Companion"
```

## Release Workflow

### 1. Commit changes and bump version

```bash
cd "$PROJECT_DIR"

# Commit any pending changes
git add -A && git commit -m "..."
git push origin main

# Bump version in package.json using edit tool
# Change "version": "0.1.x" to "version": "0.1.y"
```

Commit the version bump:

```bash
git add package.json && git commit -m "Bump version to 0.1.y for release build"
```

### 2. Build for macOS

Builds both Apple Silicon (arm64) and Intel (x64) DMGs with notarization:

```bash
cd "$PROJECT_DIR" && bun run dist:mac
```

This produces in `release/`:
- `{PRODUCT_NAME}-{version}-arm64.dmg` + blockmap
- `{PRODUCT_NAME}-{version}-x64.dmg` + blockmap
- `{PRODUCT_NAME}-{version}-arm64.zip` + blockmap (electron-updater)
- `{PRODUCT_NAME}-{version}-x64.zip` + blockmap (electron-updater)

> **Note:** The build times out after 10 minutes on slow machines. If the arm64 build doesn't finish, run it again:
> ```bash
> cd "$PROJECT_DIR" && npx electron-builder --mac --arm64
> ```

### 3. Build for Windows

Builds Windows arm64 NSIS installer:

```bash
cd "$PROJECT_DIR" && npx electron-builder --win
```

This produces in `release/`:
- `{PRODUCT_NAME}-{version}-arm64.exe` + blockmap

> **Note:** Requires Wine for cross-platform builds on macOS (electron-builder bundles its own).

### 4. Get SHA hashes

Get hex SHA256 for `latest.json` and base64 SHA512 for electron-updater YAML files:

```bash
# SHA256 hex (for latest.json)
shasum -a 256 release/"${PRODUCT_NAME}-${version}-arm64.dmg"
shasum -a 256 release/"${PRODUCT_NAME}-${version}-x64.dmg"
shasum -a 256 release/"${PRODUCT_NAME}-${version}-arm64.exe"

# SHA512 base64 (for latest-mac.yml / latest.yml)
shasum -a 512 -b release/"${PRODUCT_NAME}-${version}-arm64.dmg" | awk '{print $1}' | xxd -r -p | base64
shasum -a 512 -b release/"${PRODUCT_NAME}-${version}-x64.dmg" | awk '{print $1}' | xxd -r -p | base64
shasum -a 512 -b release/"${PRODUCT_NAME}-${version}-arm64.exe" | awk '{print $1}' | xxd -r -p | base64
shasum -a 512 -b release/"${PRODUCT_NAME}-${version}-arm64.zip" | awk '{print $1}' | xxd -r -p | base64
shasum -a 512 -b release/"${PRODUCT_NAME}-${version}-x64.zip" | awk '{print $1}' | xxd -r -p | base64

# File sizes
ls -l release/"${PRODUCT_NAME}-${version}-arm64.dmg" | awk '{print $5}'
ls -l release/"${PRODUCT_NAME}-${version}-x64.dmg" | awk '{print $5}'
ls -l release/"${PRODUCT_NAME}-${version}-arm64.exe" | awk '{print $5}'
ls -l release/"${PRODUCT_NAME}-${version}-arm64.zip" | awk '{print $5}'
ls -l release/"${PRODUCT_NAME}-${version}-x64.zip" | awk '{print $5}'
```

### 5. Create GitHub release

Create a GitHub release and upload all artifacts:

```bash
cd "$PROJECT_DIR"

gh release create "v${version}" \
  --title "v${version}" \
  --notes "## v${version}

{release-notes-content}

### Which file to download

| Your computer | Click this |
|---------------|------------|
| Mac with Apple Silicon (M1, M2, M3, M4) | \`${PRODUCT_NAME}-${version}-arm64.dmg\` |
| Mac with Intel processor | \`${PRODUCT_NAME}-${version}-x64.dmg\` |
| Windows PC | \`${PRODUCT_NAME}-${version}-arm64.exe\` |

Not sure which Mac you have? Click the Apple menu → **About This Mac**. If it says **Apple** or **M** followed by a number, choose the arm64 DMG. If it says **Intel**, choose the x64 DMG.

### Installing

**macOS:** Open the DMG and drag Ayati into your Applications folder.

**Windows:** Run the EXE installer and follow the prompts." \
  "release/${PRODUCT_NAME}-${version}-arm64.dmg" \
  "release/${PRODUCT_NAME}-${version}-x64.dmg" \
  "release/${PRODUCT_NAME}-${version}-arm64.zip" \
  "release/${PRODUCT_NAME}-${version}-x64.zip" \
  "release/${PRODUCT_NAME}-${version}-arm64.exe" \
  "release/${PRODUCT_NAME}-${version}-arm64.dmg.blockmap" \
  "release/${PRODUCT_NAME}-${version}-x64.dmg.blockmap" \
  "release/${PRODUCT_NAME}-${version}-arm64.zip.blockmap" \
  "release/${PRODUCT_NAME}-${version}-x64.zip.blockmap" \
  "release/${PRODUCT_NAME}-${version}-arm64.exe.blockmap" \
  release/latest-mac.yml \
  release/latest.yml
```

### 6. Regenerate local YAML metadata

If the YAML files in `release/` weren't updated by the build, write them manually:

**`release/latest-mac.yml`:**
```yaml
version: ${version}
files:
  - url: ${PRODUCT_NAME}-${version}-arm64.dmg
    sha512: {arm64-dmg-sha512-base64}
    size: {arm64-dmg-size}
  - url: ${PRODUCT_NAME}-${version}-x64.dmg
    sha512: {x64-dmg-sha512-base64}
    size: {x64-dmg-size}
path: ${PRODUCT_NAME}-${version}-arm64.dmg
sha512: {arm64-dmg-sha512-base64}
releaseDate: '{utc-release-date}'
```

**`release/latest.yml`:**
```yaml
version: ${version}
files:
  - url: ${PRODUCT_NAME}-${version}-arm64.exe
    sha512: {exe-sha512-base64}
    size: {exe-size}
path: ${PRODUCT_NAME}-${version}-arm64.exe
sha512: {exe-sha512-base64}
releaseDate: '{utc-release-date}'
```

### 7. Update website auto-update metadata

Update these files on the website:

**`${WEBSITE_DIR}/public/update/latest.json`:**
```json
{
  "version": "${version}",
  "pub_date": "{utc-release-date}",
  "notes": "{release-notes-summary}",
  "platforms": {
    "macos-arm64": {
      "url": "https://github.com/${GH_REPO}/releases/download/v${version}/${PRODUCT_NAME}-${version}-arm64.dmg",
      "sha256": "{arm64-dmg-sha256-hex}"
    },
    "macos-x64": {
      "url": "https://github.com/${GH_REPO}/releases/download/v${version}/${PRODUCT_NAME}-${version}-x64.dmg",
      "sha256": "{x64-dmg-sha256-hex}"
    },
    "windows-arm64": {
      "url": "https://github.com/${GH_REPO}/releases/download/v${version}/${PRODUCT_NAME}-${version}-arm64.exe",
      "sha256": "{exe-sha256-hex}"
    }
  }
}
```

**`${WEBSITE_DIR}/public/update/electron/latest-mac.yml`:** Copy from `release/latest-mac.yml` but change URLs to be fully qualified:
```yaml
version: ${version}
files:
  - url: https://github.com/${GH_REPO}/releases/download/v${version}/${PRODUCT_NAME}-${version}-arm64.zip
    sha512: {arm64-zip-sha512-base64}
    size: {arm64-zip-size}
  - url: https://github.com/${GH_REPO}/releases/download/v${version}/${PRODUCT_NAME}-${version}-x64.zip
    sha512: {x64-zip-sha512-base64}
    size: {x64-zip-size}
  - url: https://github.com/${GH_REPO}/releases/download/v${version}/${PRODUCT_NAME}-${version}-arm64.dmg
    sha512: {arm64-dmg-sha512-base64}
    size: {arm64-dmg-size}
  - url: https://github.com/${GH_REPO}/releases/download/v${version}/${PRODUCT_NAME}-${version}-x64.dmg
    sha512: {x64-dmg-sha512-base64}
    size: {x64-dmg-size}
path: https://github.com/${GH_REPO}/releases/download/v${version}/${PRODUCT_NAME}-${version}-arm64.zip
sha512: {arm64-zip-sha512-base64}
releaseDate: '{utc-release-date}'
```

**`${WEBSITE_DIR}/public/update/electron/latest.yml`:**
```yaml
version: ${version}
files:
  - url: https://github.com/${GH_REPO}/releases/download/v${version}/${PRODUCT_NAME}-${version}-arm64.exe
    sha512: {exe-sha512-base64}
    size: {exe-size}
path: https://github.com/${GH_REPO}/releases/download/v${version}/${PRODUCT_NAME}-${version}-arm64.exe
sha512: {exe-sha512-base64}
releaseDate: '{utc-release-date}'
```

### 8. Update website hardcoded release config

Update the website's `releases.ts` with the new version number and GitHub URL:

**`${WEBSITE_DIR}/src/lib/releases.ts`** — change these values:

| Field | Before | After |
|-------|--------|-------|
| `CURRENT_RELEASE_VERSION` | `"0.1.x"` | `"${version}"` |
| `GITHUB_RELEASE_BASE_URL` | `releases/download/v0.1.x` | `releases/download/v${version}` |
| All filenames in `RELEASE_DOWNLOADS` | `-0.1.x-` | `-${version}-` |
| Windows label | `"Windows (x64)"` | `"Windows (ARM64)"` (or correct arch) |

If the download redirect routes reference a platform that doesn't match the actual build artifact (e.g., route is `windows-x64` but file is `arm64.exe`), update the label in `RELEASE_DOWNLOADS` to match.

### 9. Push tag

```bash
cd "$PROJECT_DIR"
git tag -a "v${version}" -m "v${version} - {release-title}"
git push origin main --tags
```

### 9. Clean up old release files (optional)

Remove old version artifacts from the local `release/` directory to free disk space:

```bash
# Remove v0.1.x artifacts (adjust version as needed)
rm -rf release/"${PRODUCT_NAME}-0.1.x-*"
```

## Prerequisites

- `electron-builder.env` in project root with Apple notarization credentials (see AGENTS.md)
- `gh` (GitHub CLI) installed and authenticated
- Bun installed
- For Windows builds: Wine (electron-builder bundles its own)

### Vercel environment (one-time)

Ensure the website's Vercel project has these environment variables set for **Production**:

| Variable | Value |
|----------|-------|
| `QF_CLIENT_ID` | The production Quran Foundation client ID (see docs/api-keys.md) |
| `QF_CLIENT_SECRET` | The production Quran Foundation client secret |
| `QURAN_REDIRECT_URI` | `https://ayati-website.vercel.app/oauth/callback` |
| `QURAN_FOUNDATION_ENV` | `production` (defaults to production if unset) |
| `QURAN_AUTH_BASE_URL` | `https://oauth2.quran.foundation` (optional, auto-derived from `QURAN_FOUNDATION_ENV`) |
| `QURAN_API_BASE_URL` | `https://apis.quran.foundation` (optional, auto-derived from `QURAN_FOUNDATION_ENV`) |

If the Vercel proxy uses the wrong OAuth endpoint (prelive vs production), the token exchange will fail with:
> Quran Foundation is unavailable right now. Try again after the API is reachable.

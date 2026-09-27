---
name: mac-cleanup
description: "Free macOS disk space with a dry-run inventory first, then tiered cleanup. Use when the user says disk full, free space, clean Mac, clean Library, clean caches, mole clean, or mac-cleanup. Different from general file delete requests because it follows a fixed dry-run → confirm → clean → verify loop and never touches SIP or protected app data without an explicit tier."
---

# Mac cleanup

Reclaim disk on this Mac with **dry-run first**, then cleanup only after the user confirms tiers.

## Modes

| Mode | When | Action |
|---|---|---|
| `dry-run` (default) | User asks to clean / free space / inspect bloat | Inventory only. Print table. Do not delete. |
| `clean` | User confirms tiers after dry-run | Delete only listed confirmed paths. |
| `status` | Quick check | `df` + top home/Library sizes only. |

If the user says "just clean" without a prior dry-run in this session, run dry-run first and stop for confirmation.

## Hard rules

- Never delete under `/System`, `/System/Library`, or other SIP-protected trees.
- Never wipe `/opt/homebrew` wholesale.
- Never delete Keychains, Mail primary store, iCloud `Mobile Documents` file contents, Photos library, or WhatsApp/Voice Memos data unless the user names that target.
- Prefer **path deletes** over blind `rm -rf ~`.
- Admin actions (logs, `/Library`, `/usr/local` pkg leftovers): use macOS GUI admin via `osascript` `do shell script ... with administrator privileges` when non-interactive `sudo` fails.
- APFS clones (e.g. Helium `code_sign_clone`) can show huge `du` but free little unique space. Report both `du` and `df` delta.
- After deletes: re-run `df -h /System/Volumes/Data` and report before/after free space.

## Workflow

### 1. Baseline

```bash
df -h / /System/Volumes/Data
du -sh "$HOME" "$HOME/Library" 2>/dev/null
```

### 2. Dry-run inventory

```bash
python3 ~/.agents/skills/mac-cleanup/scripts/inventory.py
# optional:
python3 ~/.agents/skills/mac-cleanup/scripts/inventory.py --json /tmp/mac-cleanup-inventory.json
```

If Mole is installed (`mo` / `mole`), also note:

```bash
mo clean --dry-run 2>&1 | tee /tmp/mole-clean-dryrun.txt | tail -40
```

Do not run live `mo clean` unless the user opts into tier `mole`.

### 3. Present plan

Group the inventory by tier. Recommend **safe** first. Ask which tiers to run (safe / duplicates / build-artifacts / opt-in extras). Do not invent sizes; use script output.

### 4. Clean (only after confirm)

```bash
python3 ~/.agents/skills/mac-cleanup/scripts/clean.py --dry-run --tiers safe
# after user OK:
python3 ~/.agents/skills/mac-cleanup/scripts/clean.py --apply --tiers safe,duplicates,build-artifacts
```

For paths the scripts do not cover (Homebrew formula uninstall, TeX doc strip, simulator runtime, package removals), follow the **Manual playbook** below and confirm each class.

### 5. Verify

```bash
df -h /System/Volumes/Data
python3 ~/.agents/skills/mac-cleanup/scripts/inventory.py --tiers safe --min-mb 50
```

Report free-space delta. Note APFS purge lag if `df` moves less than sum of `du`.

## Tiers

### `safe` (default recommend)

Rebuildable caches and stuck temps:

- Package caches: `~/.npm/_cacache`, `~/.npm/_npx`, `~/.bun/install/cache`, `~/Library/Caches/bun`, pnpm store/caches when present
- Most of `~/Library/Caches/*` **except whitelist** (see below)
- User `$TMPDIR` / `/private/var/folders/.../T` build leftovers: `eas-build-local-nodejs`, `metro-cache`, `jest_*`, `node-compile-cache`
- Helium/Chromium `code_sign_clone` under `/private/var/folders/.../X/`
- CloudKit iCloud Drive stuck temps: `~/Library/Caches/CloudKit/com.apple.bird/**/MMCS/tmpm-*` (not whole CloudKit metadata)
- Cursor rebuildable: `CachedData`, `CachedExtensionVSIXs`, `Cache`, `GPUCache`, `logs`, `Crashpad`, `User/globalStorage/anysphere.cursor-agent-worker`
- Helium GPU/Crashpad/Service Worker CacheStorage (keep profile, extensions, cookies)
- `~/.pi/agent/tmp`, tool caches under `~/.cache` except model weights (whisper/huggingface stay unless tier `models`)
- XcodeBuildMCP workspaces, Xcode DerivedData
- Unified logs: `log erase --all` (admin)
- `brew cleanup -s` / broken ref prune only (not `brew uninstall`)

**Cache whitelist (do not delete in `safe`):**

- `CloudKit` root (only `tmpm-*` under bird MMCS)
- `ms-playwright*`
- JetBrains, Ollama app caches, Surge, HuggingFace app dirs if present
- Anything the user marked keep this session

### `duplicates`

Second copies when env points elsewhere:

- `~/Library/Android` if `ANDROID_HOME` or `ANDROID_SDK_ROOT` is a different existing path (e.g. external SSD)
- `~/.gradle` if `GRADLE_USER_HOME` is a different existing path
- Official Node pkg under `/usr/local` when Homebrew `node` is the intended default (confirm)
- Extra rustup toolchains beyond the active default (confirm which to keep)

### `build-artifacts`

- Project `node_modules` only if user names repos or says idle deps OK
- `.next`, `.open-next`, `.turbo`, `.cxx`, `android/**/app/build`, iOS `DerivedData` under project trees
- Xcode Archives (confirm: loses archived IPAs)
- Cursor worktrees under `~/.cursor/worktrees`

### `opt-in` (always ask)

| Target | Notes |
|---|---|
| Ollama models `~/.ollama/models` | Redownload via `ollama pull` |
| Playwright browsers | Breaks browser automation until reinstall |
| Mole live `mo clean` / `mo purge` | Review dry-run log first |
| TeX Live `texmf-dist/doc` + `source` | Keep engines for job-apply CV; set `tlmgr` docfiles/srcfiles 0 |
| watchOS simulator runtime | Keep iOS runtime if still developing iPhone/iPad |
| `xcrun simctl erase all` | Wipes sim content, keeps runtimes |
| Global npm packages / brew formulae | Only named unused packages |
| Cursor `state.vscdb` wipe | Destroys chat history; vacuum is safer |
| `/private/var/vm/sleepimage` | System regenerates; low value |
| CoreSimulator dyld caches | Often SIP-locked; reboot may be required; skip if `Operation not permitted` |

## Manual playbook (from known good session)

Use when scripts miss a class. Still dry-describe paths and sizes first.

1. **Home top**: `du -sh ~/* ~/.[^.]* 2>/dev/null | sort -hr | head -40`
2. **Library**: Caches, Application Support, Developer, Group Containers (do not delete WhatsApp/Voice Memos/Mail)
3. **`/private/var`**: user `folders` only; never mass-delete `db` except diagnostics via `log erase`
4. **`/opt`**: `brew cleanup`, `brew autoremove`; uninstall only with user-named formulae
5. **TeX**: strip docs/sources only; verify `pdflatex` and job-apply `./compile.sh`
6. **python.org Framework** vs Homebrew python: remove Framework only if brew python is intended and PATH checked
7. **Admin finish**: package receipts, `/Applications` TeX GUIs, leftover Zoom/gcloud paths as user requests

## Mole notes

- Binary often `/opt/homebrew/bin/mole` (`mo` alias)
- Prefer `mo clean --dry-run` and `mo purge --dry-run` before live
- Clean-list may live at `~/.config/mole/clean-list.txt`

## Output format

Dry-run:

1. Free space baseline
2. Table: tier | path | `du` size | reason | risk
3. Recommended tier set
4. Explicit "no deletes yet"

After clean:

1. What was removed (paths)
2. `df` before → after
3. Leftover large optional targets
4. Anything that failed (SIP, locks) without retry loops that fight the OS

## History

Every full dry-run appends a snapshot to `~/.config/mac-cleanup/history.jsonl` (one JSON line per run: timestamp, df bytes for `/System/Volumes/Data`, candidate list with sizes, tier totals). Scoped `--tiers` runs are not recorded, only full runs.

On the next full dry-run the inventory prints a diff against the previous snapshot: the disk used/free delta, then candidates that grew, appeared, or disappeared since (changes under 25 MB are ignored). This is how to tell what consumed space between two runs.

```bash
python3 scripts/inventory.py            # records a snapshot and diffs vs the last one
python3 scripts/inventory.py --history  # list recent snapshots (default 10)
python3 scripts/inventory.py --history 50
```

## Scripts

| Script | Role |
|---|---|
| `scripts/inventory.py` | Dry-run sizes and tier tags; records `~/.config/mac-cleanup/history.jsonl` on full runs and diffs against the previous snapshot |
| `scripts/clean.py` | `--dry-run` (default) or `--apply` for known safe/duplicate/build paths |

Extend the scripts when a new recurring target appears; keep SKILL tiers in sync.

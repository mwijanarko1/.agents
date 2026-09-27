---
name: update-pi-extensions
description: Update pi extensions (npm user packages and git-installed packages) via `pi update --extensions`. Temporarily disables the 7-day package age barrier, updates extensions, then restores the barrier. Run /skill:update-pi-extensions to execute.
---

# Update Pi Extensions

Checks for and updates pi extensions (npm user packages and git-installed packages) with `pi update --extensions` — without touching the pi binary itself.

Does not update `pi`, `cmd`, `codex`, `devin`, or `claude`. Use the `update-agents` skill for those.

## Age barrier contract

Default (always on outside this skill):

| Config | Setting | Unit | Meaning |
| --- | --- | --- | --- |
| `~/.npmrc` | `min-release-age=7` | **days** | npm refuses versions newer than 7 days |
| `~/.bunfig.toml` | `minimumReleaseAge = 604800` | **seconds** | bun refuses versions newer than 7 days |

This skill **must** turn that barrier off for the update window, then restore it — even if a step fails (use `trap` on `EXIT`).

Do **not** leave `min-release-age` deleted or `minimumReleaseAge = 0` after the skill finishes.

## CRITICAL: run the whole workflow in ONE shell

Every `bash` tool call is a **fresh shell**. A `trap ... EXIT` set in one call fires when *that call's shell* exits — so a trap set in a "backup" step restores immediately and is gone before the update step runs. The backup → trap → disable → check → update → restore → verify sequence **must all run inside a single `bash` invocation** so the trap stays live across the entire update window and only fires at the very end.

Do **not** split the steps below across multiple `bash` calls. Run the consolidated script in [Steps](#steps) as one call. If you ever need to re-run a sub-part, re-do backup+trap+disable first in the same shell.

## Steps

Run this **entire** script in a single `bash` call. It backs up, arms the restore trap, disables the barrier, checks for updates, applies them, restores the barrier, and verifies — in that order, in one shell.

```bash
set +e

# 1. Backup guardrail configs (distinct names so it never collides with update-agents)
cp ~/.npmrc ~/.npmrc.update-pi-extensions-backup 2>/dev/null
cp ~/.bunfig.toml ~/.bunfig.toml.update-pi-extensions-backup 2>/dev/null

# 2. Always restore on exit (armed BEFORE disabling)
restore_age_barrier() {
  if [ -f ~/.npmrc.update-pi-extensions-backup ]; then
    mv ~/.npmrc.update-pi-extensions-backup ~/.npmrc
  fi
  if [ -f ~/.bunfig.toml.update-pi-extensions-backup ]; then
    mv ~/.bunfig.toml.update-pi-extensions-backup ~/.bunfig.toml
  fi
}
trap restore_age_barrier EXIT

# 3. Disable the 7-day barrier (temporary)
#     npm: strip min-release-age, force ignore-scripts=false for this window.
if [ -f ~/.npmrc ]; then
  grep -v -E '^[[:space:]]*min-release-age=' ~/.npmrc > ~/.npmrc.update-pi-extensions-tmp || true
  if ! grep -q -E '^[[:space:]]*ignore-scripts=' ~/.npmrc.update-pi-extensions-tmp 2>/dev/null; then
    printf 'ignore-scripts=false\n' | cat - ~/.npmrc.update-pi-extensions-tmp > ~/.npmrc.update-pi-extensions-tmp2
    mv ~/.npmrc.update-pi-extensions-tmp2 ~/.npmrc.update-pi-extensions-tmp
  else
    sed -i.bak 's/^[[:space:]]*ignore-scripts=.*/ignore-scripts=false/' ~/.npmrc.update-pi-extensions-tmp
    rm -f ~/.npmrc.update-pi-extensions-tmp.bak
  fi
  mv ~/.npmrc.update-pi-extensions-tmp ~/.npmrc
fi
#     bun: age gate off for this window only
cat > ~/.bunfig.toml << 'EOF'
[install]
minimumReleaseAge = 0
EOF

# 4. Check for available updates
# agent-policy: allow-forbidden-command because: update-pi-extensions workflow checks extension version for comparison
echo "=== pi extensions (e.g. pi-subagents, npm latest) ===" && npm view @earendil-works/pi-subagents version 2>/dev/null

# 5. Update pi extensions
echo "--- Updating pi extensions ---" && pi update --extensions 2>&1

# 6. Restore barrier (also runs via trap on EXIT)
restore_age_barrier
trap - EXIT

# 7. Verify results + barrier back on
echo "=== age barrier restored ==="
echo -n "npm min-release-age: " && npm config get min-release-age
echo "bunfig:" && cat ~/.bunfig.toml
echo "=== leftover backup files (should be none) ==="
ls ~/.npmrc.update-pi-extensions-backup ~/.bunfig.toml.update-pi-extensions-backup 2>&1 || echo "none (good)"
```

Expected after restore: `min-release-age` is `7`, `~/.bunfig.toml` has `minimumReleaseAge = 604800`, and no `*.update-pi-extensions-backup` files remain.

## Notes

- Only touches extensions, not the `pi` binary itself or other coding agents. Use the `update-agents` skill for those.
- If the verify step shows the barrier still off (`min-release-age=null` / `minimumReleaseAge = 0`) or leftover backup files, the trap did not fire correctly. Reconstruct the barrier manually to the contract values (`min-release-age=7`, `minimumReleaseAge = 604800`), preserving any `~/.npmrc` auth token, and delete stray `*.update-pi-extensions-backup` files.

## Failure rules

- If the update step fails, still restore the barrier (the `trap` handles this as long as the whole workflow ran in one shell).
- Never commit or print auth tokens from `~/.npmrc`.
- Do not permanently leave the barrier at 0.
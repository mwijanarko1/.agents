---
name: update-agents
description: Check and update pi, cmd (VS Code CLI), codex, devin, and claude (Claude Code) coding agents. Temporarily disables the 7-day package age barrier, updates agents, then restores the barrier. Run /skill:update-agents to execute.
---

# Update Coding Agents

Checks for updates for `pi`, `cmd` (VS Code CLI), `codex`, `devin`, and `claude` (Claude Code), then updates them.

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

# 1. Backup guardrail configs
cp ~/.npmrc ~/.npmrc.update-agents-backup 2>/dev/null
cp ~/.bunfig.toml ~/.bunfig.toml.update-agents-backup 2>/dev/null

# 2. Always restore on exit (armed BEFORE disabling)
restore_age_barrier() {
  if [ -f ~/.npmrc.update-agents-backup ]; then
    mv ~/.npmrc.update-agents-backup ~/.npmrc
  fi
  if [ -f ~/.bunfig.toml.update-agents-backup ]; then
    mv ~/.bunfig.toml.update-agents-backup ~/.bunfig.toml
  fi
}
trap restore_age_barrier EXIT

# 3. Disable the 7-day barrier (temporary)
#     npm: strip min-release-age, force ignore-scripts=false for this window.
if [ -f ~/.npmrc ]; then
  grep -v -E '^[[:space:]]*min-release-age=' ~/.npmrc > ~/.npmrc.update-agents-tmp || true
  if ! grep -q -E '^[[:space:]]*ignore-scripts=' ~/.npmrc.update-agents-tmp 2>/dev/null; then
    printf 'ignore-scripts=false\n' | cat - ~/.npmrc.update-agents-tmp > ~/.npmrc.update-agents-tmp2
    mv ~/.npmrc.update-agents-tmp2 ~/.npmrc.update-agents-tmp
  else
    sed -i.bak 's/^[[:space:]]*ignore-scripts=.*/ignore-scripts=false/' ~/.npmrc.update-agents-tmp
    rm -f ~/.npmrc.update-agents-tmp.bak
  fi
  mv ~/.npmrc.update-agents-tmp ~/.npmrc
else
  printf 'ignore-scripts=false\n' > ~/.npmrc
fi
#     bun: age gate off for this window only
cat > ~/.bunfig.toml << 'EOF'
[install]
minimumReleaseAge = 0
EOF

# 4. Check for available updates
#    Devin has no separate non-interactive check flag; record installed version, run `devin update` below.
#    Claude Code reports current vs latest via `claude update` (or `claude --version` for installed).
# agent-policy: allow-forbidden-command because: update-agents workflow checks exact known packages for version comparison
echo "=== pi (npm latest) ===" && npm view @earendil-works/pi-coding-agent version 2>/dev/null
# agent-policy: allow-forbidden-command because: update-agents workflow checks exact known packages for version comparison
echo "=== codex (npm latest) ===" && npm view @openai/codex version 2>/dev/null
# agent-policy: allow-forbidden-command because: update-agents workflow checks exact known packages for version comparison
echo "=== cmd / command-code (npm latest) ===" && npm view command-code version 2>/dev/null
echo "=== devin (installed) ===" && devin version 2>&1
echo "=== claude (installed) ===" && claude --version 2>&1
# agent-policy: allow-forbidden-command because: update-agents workflow checks extension version for comparison
echo "=== pi extensions (e.g. pi-subagents, npm latest) ===" && npm view @earendil-works/pi-subagents version 2>/dev/null
echo "=== installed: pi (bun) ===" && pi --version 2>&1

# 5. Update all agents
echo "--- Updating pi ---" && pi update 2>&1
echo "--- Updating pi extensions ---" && pi update --extensions 2>&1
echo "--- Updating cmd ---" && cmd update 2>&1
echo "--- Updating codex ---" && codex update 2>&1
echo "--- Updating devin ---" && devin update 2>&1
echo "--- Updating claude ---" && claude update 2>&1

# 6. Restore barrier (also runs via trap on EXIT)
restore_age_barrier
trap - EXIT

# 7. Verify results + barrier back on
echo "=== age barrier restored ==="
echo -n "npm min-release-age: " && npm config get min-release-age
echo "bunfig:" && cat ~/.bunfig.toml
echo "=== pi (bun) ===" && pi --version
echo "=== cmd ===" && cmd --version
echo "=== codex ===" && codex --version
echo "=== devin ===" && devin version
echo "=== claude ===" && claude --version
echo "=== leftover backup files (should be none) ==="
ls ~/.npmrc.update-agents-backup ~/.bunfig.toml.update-agents-backup 2>&1 || echo "none (good)"
```

Expected after restore: `min-release-age` is `7`, `~/.bunfig.toml` has `minimumReleaseAge = 604800`, and no `*.update-agents-backup` files remain.

## Notes

- **pi is installed via bun, not npm.** `npm list -g @earendil-works/pi-coding-agent` will show a stale or missing entry — use `pi --version` to verify the real installed version.
- If the verify step shows the barrier still off (`min-release-age=null` / `minimumReleaseAge = 0`) or leftover backup files, the trap did not fire correctly. Reconstruct the barrier manually to the contract values (`min-release-age=7`, `minimumReleaseAge = 604800`), preserving any `~/.npmrc` auth token, and delete stray `*.update-agents-backup` files.
## Failure rules

- If any update step fails, still restore the barrier (the `trap` handles this as long as the whole workflow ran in one shell).
- Never commit or print auth tokens from `~/.npmrc`.
- Do not permanently leave the barrier at 0.

---
name: update-agents
description: Check and update pi, cmd (VS Code CLI), codex, devin, claude (Claude Code), and Prime Agent coding agents. Temporarily disables the 7-day package age barrier, updates agents, then restores the barrier. Run /skill:update-agents to execute.
---

# Update Coding Agents

Checks for updates for `pi`, `cmd` (VS Code CLI), `codex`, `devin`, `claude` (Claude Code), and Prime Agent, then updates them.

## Age barrier contract

Default (always on outside this skill):

| Config | Setting | Unit | Meaning |
| --- | --- | --- | --- |
| `~/.npmrc` | `min-release-age=7` | **days** | npm refuses versions newer than 7 days |
| `~/.bunfig.toml` | `minimumReleaseAge = 604800` | **seconds** | bun refuses versions newer than 7 days |

This skill **must** turn that barrier off for the update window, then restore it — even if a step fails (use `trap` on `EXIT`).

Do **not** leave `min-release-age` deleted or `minimumReleaseAge = 0` after the skill finishes.

## Steps

1. **Backup guardrail configs**

   ```bash
   cp ~/.npmrc ~/.npmrc.update-agents-backup
   cp ~/.bunfig.toml ~/.bunfig.toml.update-agents-backup
   ```

2. **Always restore on exit** (run this before any update work)

   ```bash
   restore_age_barrier() {
     if [ -f ~/.npmrc.update-agents-backup ]; then
       mv ~/.npmrc.update-agents-backup ~/.npmrc
     fi
     if [ -f ~/.bunfig.toml.update-agents-backup ]; then
       mv ~/.bunfig.toml.update-agents-backup ~/.bunfig.toml
     fi
   }
   trap restore_age_barrier EXIT
   ```

3. **Disable the 7-day barrier** (temporary)

   Keep other `~/.npmrc` lines (auth token, `ignore-scripts`, etc.). Only strip the age gate. Allow install scripts so agent updaters can run.

   ```bash
   # npm: remove min-release-age, ensure scripts can run
   if [ -f ~/.npmrc ]; then
     grep -v -E '^[[:space:]]*min-release-age=' ~/.npmrc > ~/.npmrc.update-agents-tmp || true
     if ! grep -q -E '^[[:space:]]*ignore-scripts=' ~/.npmrc.update-agents-tmp 2>/dev/null; then
       printf 'ignore-scripts=false\n' | cat - ~/.npmrc.update-agents-tmp > ~/.npmrc.update-agents-tmp2
       mv ~/.npmrc.update-agents-tmp2 ~/.npmrc.update-agents-tmp
     else
       # force scripts on for this window
       sed -i.bak 's/^[[:space:]]*ignore-scripts=.*/ignore-scripts=false/' ~/.npmrc.update-agents-tmp
       rm -f ~/.npmrc.update-agents-tmp.bak
     fi
     mv ~/.npmrc.update-agents-tmp ~/.npmrc
   else
     printf 'ignore-scripts=false\n' > ~/.npmrc
   fi

   # bun: age gate off for this window only
   cat > ~/.bunfig.toml << 'EOF'
   [install]
   minimumReleaseAge = 0
   EOF
   ```

4. **Check for available updates**

   Devin has no separate non-interactive check flag; record its installed version here and run `devin update` in the update step.
   Claude Code reports current vs latest via `claude update` (or `claude --version` for installed).
   Prime Agent checks current vs latest as part of `prime-agent update`; record its installed version here and run the update step.

   ```bash
   # agent-policy: allow-forbidden-command because: update-agents workflow checks exact known packages for version comparison
   echo "=== pi ===" && npm view @earendil-works/pi-coding-agent version 2>/dev/null
   # agent-policy: allow-forbidden-command because: update-agents workflow checks exact known packages for version comparison
   echo "=== codex ===" && npm view @openai/codex version 2>/dev/null
   # agent-policy: allow-forbidden-command because: update-agents workflow checks exact known packages for version comparison
   echo "=== cmd (command-code) ===" && npm view command-code version 2>/dev/null
   echo "=== devin ===" && devin version
   echo "=== claude ===" && claude --version
   echo "=== prime agent ===" && prime-agent --version
   # agent-policy: allow-forbidden-command because: update-agents workflow checks extension version for comparison
   echo "=== pi extensions (e.g. pi-subagents) ===" && npm view @earendil-works/pi-subagents version 2>/dev/null
   ```

5. **Update all agents**

   ```bash
   echo "--- Updating pi ---" && pi update 2>&1
   echo "--- Updating pi extensions ---" && pi update --extensions 2>&1
   echo "--- Updating cmd ---" && cmd update 2>&1
   echo "--- Updating codex ---" && codex update 2>&1
   echo "--- Updating devin ---" && devin update 2>&1
   echo "--- Updating claude ---" && claude update 2>&1
   echo "--- Updating prime agent ---" && prime-agent update 2>&1
   ```

6. **Restore barrier** (also runs via `trap` on EXIT)

   ```bash
   restore_age_barrier
   trap - EXIT
   ```

7. **Verify results + barrier back on**

   ```bash
   echo "=== age barrier restored ==="
   echo -n "npm min-release-age: " && npm config get min-release-age
   echo "bunfig:" && cat ~/.bunfig.toml
   # agent-policy: allow-forbidden-command because: update-agents verification checks the exact installed package
   echo "=== pi ===" && npm list -g @earendil-works/pi-coding-agent 2>/dev/null | grep pi-coding
   echo "=== cmd ===" && cmd --version
   echo "=== codex ===" && codex --version
   echo "=== devin ===" && devin version
   echo "=== claude ===" && claude --version
   echo "=== prime agent ===" && prime-agent --version
   ```

   Expected after restore: `min-release-age` is `7`, and `~/.bunfig.toml` has `minimumReleaseAge = 604800`.

## Failure rules

- If any update step fails, still restore the barrier (the `trap` handles this).
- Never commit or print auth tokens from `~/.npmrc`.
- Do not permanently leave the barrier at 0.

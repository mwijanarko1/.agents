---
name: update-agents
description: Check and update pi, cmd (VS Code CLI), codex, hermes, devin, and claude (Claude Code) coding agents. Saves and restores npmrc guardrails around the update. Run /skill:update-agents to execute.
---

# Update Coding Agents

Checks for updates available for `pi`, `cmd` (VS Code CLI), `codex`, `hermes`, `devin`, and `claude` (Claude Code), then updates them while handling npm guardrails.

## Steps

1. **Backup current `.npmrc`**

   ```bash
   cp ~/.npmrc ~/.npmrc.update-agents-backup
   ```

2. **Disable guardrails** — remove restrictions that block installs/updates

   ```bash
   cat > ~/.npmrc << 'EOF'
   ignore-scripts=false
   EOF
   ```

3. **Check for available updates** for all agents

   Devin has no separate non-interactive check flag; record its installed version here and run `devin update` in the update step.
   Claude Code reports current vs latest via `claude update` (or `claude --version` for installed).

   ```bash
   # agent-policy: allow-forbidden-command because: update-agents workflow checks exact known packages for version comparison
   echo "=== pi ===" && npm view @earendil-works/pi-coding-agent version 2>/dev/null
   # agent-policy: allow-forbidden-command because: update-agents workflow checks exact known packages for version comparison
   echo "=== codex ===" && npm view @openai/codex version 2>/dev/null
   # agent-policy: allow-forbidden-command because: update-agents workflow checks exact known packages for version comparison
   echo "=== cmd (command-code) ===" && npm view command-code version 2>/dev/null
   echo "=== hermes ===" && hermes update --check 2>&1
   echo "=== devin ===" && devin version
   echo "=== claude ===" && claude --version
   # agent-policy: allow-forbidden-command because: update-agents workflow checks extension version for comparison
   echo "=== pi extensions (e.g. pi-subagents) ===" && npm view @earendil-works/pi-subagents version 2>/dev/null
   ```

4. **Update all agents**

   ```bash
   echo "--- Updating pi ---" && pi update 2>&1
   echo "--- Updating pi extensions ---" && pi update --extensions 2>&1
   echo "--- Updating cmd ---" && cmd update 2>&1
   echo "--- Updating codex ---" && codex update 2>&1
   echo "--- Updating hermes ---" && hermes update --yes 2>&1
   echo "--- Updating devin ---" && devin update 2>&1
   echo "--- Updating claude ---" && claude update 2>&1
   ```

5. **Restore guardrails**

   ```bash
   mv ~/.npmrc.update-agents-backup ~/.npmrc
   ```

6. **Verify results**

   ```bash
   echo "=== .npmrc restored ===" && cat ~/.npmrc
   # agent-policy: allow-forbidden-command because: update-agents verification checks the exact installed package
   echo "=== pi ===" && npm list -g @earendil-works/pi-coding-agent 2>/dev/null | grep pi-coding
   echo "=== cmd ===" && cmd --version
   echo "=== codex ===" && codex --version
   echo "=== hermes ===" && hermes version
   echo "=== devin ===" && devin version
   echo "=== claude ===" && claude --version
   ```

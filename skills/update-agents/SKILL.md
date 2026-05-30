---
name: update-agents
description: Check and update pi, cmd (VS Code CLI), and codex coding agents. Saves and restores npmrc guardrails around the update. Run /skill:update-agents to execute.
---

# Update Coding Agents

Checks for updates available for `pi`, `cmd` (VS Code CLI), and `codex` coding agents, then updates them all while handling npmrc guardrails.

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

3. **Check for available updates** for all three agents

   ```bash
   echo "=== pi ===" && npm view @earendil-works/pi-coding-agent version 2>/dev/null
   echo "=== codex ===" && npm view @openai/codex version 2>/dev/null
   echo "=== cmd (command-code) ===" && npm view command-code version 2>/dev/null
   ```

4. **Update all three agents**

   ```bash
   echo "--- Updating pi ---" && pi update 2>&1
   echo "--- Updating cmd ---" && cmd update 2>&1
   echo "--- Updating codex ---" && codex update 2>&1
   ```

5. **Restore guardrails**

   ```bash
   mv ~/.npmrc.update-agents-backup ~/.npmrc
   ```

6. **Verify results**

   ```bash
   echo "=== .npmrc restored ===" && cat ~/.npmrc
   echo "=== pi ===" && npm list -g @earendil-works/pi-coding-agent 2>/dev/null | grep pi-coding
   echo "=== cmd ===" && cmd --version
   echo "=== codex ===" && codex --version
   ```

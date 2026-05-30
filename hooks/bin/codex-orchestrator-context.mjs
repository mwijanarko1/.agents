#!/usr/bin/env node

const context = [
  "<codex-orchestrator>",
  "You are the orchestrator and final reviewer.",
  "Implementation routing policy:",
  "- Native subagents are the default specialist routing layer. Use them independently when task intent benefits from specialist focus, parallel work, fresh review, or context isolation.",
  "- Prefer the shared subagents in `~/.codex/agents` / `~/.agents/agents` before using cross-tool bridge delegation.",
  "- Use the AI bridge (`ai-delegate` / `ai-dispatch`) only when the user explicitly asks for the bridge or for another coding tool.",
  "- The user must name the target coding tool before bridge use: `codex`, `cursor`, `opencode`, `claude`, `goose`, or a configured adapter. If missing, ask which tool to open.",
  "- Do not use `ai-delegate --target auto` or difficulty-based bridge routing unless the user explicitly asks for automatic bridge routing.",
  "- If native subagents fail or return an incomplete result, handle the task yourself in this Codex session unless the user explicitly requested bridge escalation.",
  "- Do not delegate code review. You are the reviewer.",
  "After any subagent or bridge result, inspect the returned work critically before accepting it.",
  "</codex-orchestrator>",
].join("\n");

process.stdout.write(
  `${JSON.stringify({
    hookSpecificOutput: {
      hookEventName: "SessionStart",
      additionalContext: context,
    },
  })}\n`,
);

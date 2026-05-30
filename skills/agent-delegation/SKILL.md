---
name: agent-delegation
description: "Delegate work to another coding agent or configured adapter."
---

# Agent Delegation

Use the shared shell entrypoint:

```bash
ai-delegate ...
```

This works from Codex, Cursor Agent, OpenCode, Claude Code, Goose, and adapter-configured tools because it launches the target agent as a headless worker process.

This is a backup and cross-tool escape hatch. Prefer native subagents in the active tool for normal specialist work.

## When To Use

- The user explicitly asks to use the AI bridge, `ai-delegate`, or `ai-dispatch`
- The user explicitly names another coding tool to open through the bridge
- The user wants a cross-tool comparison or fallback after native subagents are insufficient

Do not use the bridge just because a task is easy, hard, or implementation-oriented. Native subagents are the default specialist layer.

## Routing Rules

- `codex`:
  - Use only when the user explicitly says "ask codex" or "use Codex through the bridge"
- `cursor`:
  - Use only when the user explicitly says "ask cursor" or "cursor agent should fix this"
- `opencode`:
  - Use only when the user explicitly says "ask opencode"
- `claude`:
  - Use only when the user explicitly says "ask claude" or "use claude code"
- `goose`:
  - Use only when the user explicitly says "ask goose"
- `gemini`, `aider`, `amp`, `cline`, `droid`:
  - Supported through the adapter registry in `~/.config/ai-bridge/adapters.json`
  - Use when the user explicitly names one of these tools and the machine has a matching adapter command configured
- `auto`:
  - Do not use by default
  - Use only when the user explicitly asks for automatic bridge routing

## Commands

Explicit target:

```bash
ai-delegate --target codex --cwd "$PWD" --from-agent codex -- "Fix the failing parser tests"
ai-delegate --target cursor --cwd "$PWD" --from-agent cursor-agent -- "Refactor the auth pipeline safely"
ai-delegate --target opencode --cwd "$PWD" --from-agent opencode -- "Add a compact settings toggle"
ai-delegate --target claude --cwd "$PWD" --from-agent codex -- "Debug the broken migration"
ai-delegate --target goose --cwd "$PWD" --from-agent codex -- "Investigate the flaky test"
ai-delegate --target gemini --cwd "$PWD" --from-agent codex -- "Investigate the flaky test"
```

Automatic routing, only when the user explicitly requests it:

```bash
ai-delegate --target auto --difficulty easy --cwd "$PWD" --from-agent codex -- "Implement a simple preferences screen"
ai-delegate --target auto --difficulty hard --cwd "$PWD" --from-agent codex -- "Debug the race condition in the sync engine"
```

Structured output:

```bash
ai-delegate --target codex --json --cwd "$PWD" --from-agent cursor-agent -- "Fix the broken CI workflow"
```

Background mode with completion notification:

```bash
ai-delegate --target auto --difficulty hard --background --notify-on-complete --cwd "$PWD" --from-agent codex -- "Run the refactor and tell me when it's done"
```

## How To Use It Correctly

1. If the user names a specific agent, use `--target` with that exact agent.
2. If the user asks for bridge use but does not name the target coding tool, ask which tool to open.
3. If the user explicitly asks for automatic bridge routing, use `--target auto` and set `--difficulty easy|hard`.
4. Always pass the current working directory with `--cwd "$PWD"` so the delegated worker runs in the right repo.
5. Always pass your current tool name with `--from-agent ...`:
   - Codex: `codex`
   - Cursor Agent: `cursor-agent`
   - OpenCode: `opencode`
   - Claude Code: `claude-code`
6. Read the returned result critically. Delegation is not automatic validation.
7. If the delegated worker fails or returns an incomplete result, continue locally unless the user asked for another bridge escalation.
8. For long-running work, prefer `--background --notify-on-complete` so the caller can keep working and receive a completion notice on the next prompt.

## Notes

- `ai-delegate` launches the real agent CLI. This is Hermes-style delegation via shell command, not an internal model handoff.
- `ai-delegate --target codex` uses `codex exec`.
- `ai-delegate --target cursor` uses the `agent-hard` wrapper.
- `ai-delegate --target opencode` uses the `opencode-easy` wrapper.
- `ai-delegate --target claude` uses the `claude-code-worker` wrapper.
- `ai-delegate --target goose` uses `goose run --text`.
- Other named tools are supported through the adapter registry in `~/.config/ai-bridge/adapters.json`.
- `ai-delegate --target auto` only routes between OpenCode and Cursor. Use it only when the user explicitly asks for automatic bridge routing.
- `--background --notify-on-complete` adds Hermes-style completion tracking. Finished jobs are surfaced back into the caller's next prompt context.

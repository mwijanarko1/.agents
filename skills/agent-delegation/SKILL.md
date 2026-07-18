---
name: agent-delegation
description: "Delegate work to another coding agent or configured adapter."
---

# Agent Delegation

Cross-tool escape hatch only. Prefer native subagents for normal specialist work.

```bash
ai-delegate --target <tool> --cwd "$PWD" --from-agent <caller> -- "task"
```

## When

- User explicitly asks for the AI bridge / `ai-delegate` / `ai-dispatch`
- User names another coding tool
- Cross-tool comparison or fallback after native subagents fail

## Targets

| Target | Use when |
|--------|----------|
| `cmd` | Default external terminal agent (DeepSeek V4 Flash) unless user says otherwise |
| `cursor` | Harder work / user asks; always `composer-2.5` (never `-fast`) |
| `codex` / `opencode` / `claude` / `goose` / adapter names | User explicitly names that tool |
| `auto` | Only if user asks for automatic bridge routing (`--difficulty easy\|hard`) |

Always pass `--cwd "$PWD"` and `--from-agent` (`codex`, `cursor-agent`, `opencode`, `claude-code`). Read results critically. Long jobs: `--background --notify-on-complete`.

Adapters: `~/.config/ai-bridge/adapters.json`. Direct fallbacks: `cmd -p --skip-onboarding "..."`, `agent --model composer-2.5 -p "..."`.

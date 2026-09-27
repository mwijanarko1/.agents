---
name: agent-delegation
description: "Delegate work to another coding agent or configured adapter."
---

# Agent Delegation

Cross-tool escape hatch only. Prefer native subagents for normal specialist work.

```bash
command -v ai-delegate >/dev/null || { echo "ai-delegate is not installed" >&2; exit 127; }
ai-delegate --target <tool> --cwd "$PWD" --from-agent <caller> -- 'task'
```

## When

- User explicitly asks for the AI bridge / `ai-delegate` / `ai-dispatch`
- User names another coding tool
- Cross-tool comparison or fallback after native subagents fail (requires explicit user approval, never a silent switch in Pi governed lanes)

## Targets

| Target | Use when |
|--------|----------|
| `cmd` | Default external terminal agent (DeepSeek V4 Flash) unless user says otherwise |
| `cursor` | Harder work / user asks; always `composer-2.5` (never `-fast`) |
| `codex` / `opencode` / `claude` / `goose` / adapter names | User explicitly names that tool |
| `auto` | Only if user asks for automatic bridge routing (`--difficulty easy\|hard`) |

Always pass `--cwd "$PWD"` and `--from-agent` (`codex`, `cursor-agent`, `opencode`, `claude-code`). Quote prompts containing backticks with single quotes. Read results critically. Long jobs: `--background --notify-on-complete`. On any native launch, resume, or tooling failure in Pi subagent-governed lanes, stop and report the infrastructure failure and preserve the execution protocol; retry only under the active protocol.

Check command availability before selecting a path. If `ai-delegate` is absent, stop and ask the user before using the target's direct CLI; in Pi subagent-governed lanes do not silently switch to external or foreground fallback. Use Herdr only when the user explicitly requests it and `HERDR_ENV=1`, then load the Herdr skill before controlling another pane.

Adapters: `~/.config/ai-bridge/adapters.json`. Direct fallbacks: `cmd -p --skip-onboarding '...'`, `agent --model composer-2.5 -p '...'`.

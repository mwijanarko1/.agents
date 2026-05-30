# ai-peers

Local peer coordination for terminal AI sessions.

This is a lightweight variant of the `claude-peers` idea for tools that support MCP but do not expose Claude's channel-push protocol. It gives Codex, Cursor Agent, OpenCode, and Claude Code a shared peer registry and message inbox via a local SQLite database.

## What it does

- `whoami`: show this session's peer id and metadata
- `list_peers`: discover other active sessions on this machine, repo, or directory
- `set_summary`: publish what this session is working on and which files it expects to touch
- `send_message`: send a short note to another peer
- `check_messages`: read unread notes addressed to this session
- `recommend_peer`: route work by role

## Intended role split

- Codex: `orchestrator-reviewer`
- OpenCode: `programmer`
- Cursor Agent: `programmer`
- Claude Code: `programmer`

Native subagents are the default specialist layer inside each tool. Use the AI bridge only when the user explicitly asks for cross-tool delegation and names the target tool.

When the user explicitly requests automatic bridge routing, the compatibility order is:

- easy: OpenCode -> Cursor Agent
- hard: Cursor Agent -> OpenCode
- review: Codex

## Limit

Messages are not injected into model context automatically. Cursor Agent and OpenCode do not currently expose Claude's channel API, so this is polling or on-demand coordination, not silent push delivery.

## Files

- `server.py`: stdio MCP server
- `store.py`: shared SQLite registry and message store
- `cli.py`: shell-friendly CLI
- `requirements.txt`: pinned MCP SDK dependency for the local virtualenv

## Launch commands

- `codex-orchestrator`: launch Codex with `orchestrator-reviewer`
- `opencode-easy`: launch OpenCode with `easy-programmer`
- `agent-hard`: launch Cursor Agent with `hard-programmer`
- `claude-code-worker`: launch Claude Code with `hard-programmer`
- `ai-peers route --task-kind implement --difficulty easy`: compatibility helper; use only after explicit bridge request
- `ai-peers route --task-kind review --difficulty hard`: compatibility helper; review remains with Codex when explicitly bridged

## Automatic inbox injection

If you launch through the wrappers above, each tool gets a stable `AI_PEERS_SESSION_KEY`.

- Codex: unread peer messages are injected through `UserPromptSubmit` and `SessionStart` hooks
- Cursor Agent: unread peer messages are injected through `UserPromptSubmit` and `SessionStart` hooks
- OpenCode: unread peer messages are appended to the system prompt through the `chat.message` plugin hook

This is not true mid-turn push. It is automatic next-turn delivery, which is the closest safe approximation without a native channel API.

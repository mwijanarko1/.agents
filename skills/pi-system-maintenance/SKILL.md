---
name: pi-system-maintenance
description: Maintain and recover local Pi configuration via protected files, Git checkpoints, and project-scoped learning. Use when modifying `~/.pi/agent`, Pi safety controls, checkpoint state, or continuous-learning state. Different from `update-pi-extensions` because this manages local configuration and recovery rather than package updates.
---

# Pi System Maintenance

Use the protected substrate and checkpoint system whenever Pi changes its own global configuration.

## Safety boundary

These files are protected:

- `~/.pi/agent/auth.json`
- `~/.agents/hooks/command-guard.mjs`
- `~/.pi/agent/extensions/command-guard.ts`
- `~/.pi/agent/extensions/tool-loop-guard.ts`

Never enable or bypass maintenance mode autonomously. If a requested change requires a protected file, explain why and ask the user to run:

```text
/pi-maintenance on
```

After editing and verification, ask the user to run:

```text
/pi-maintenance off
```

Maintenance mode is TUI-only, session-local, and resets when the session ends or extensions reload.

## Configuration checkpoints

The checkpoint repository is `~/.pi/agent/config-checkpoints`. Checkpoints automatically run before recognized Pi configuration mutations.

Tracked:

- `settings.json`
- source files under `extensions/`
- Markdown agent definitions under `agents/`
- source files under `tests/`
- source files under `scripts/`

Excluded:

- `auth.json` and other credentials
- sessions and transcripts
- `node_modules`, npm packages, and caches
- generated model catalogs
- backups
- extension JSON files, which may contain runtime configuration or secrets

User commands:

```text
/pi-config status
/pi-config restore [ref]
```

Restore shows a diff and requires interactive user confirmation. Never approve or perform a restore autonomously.

## Self-change workflow

1. Inspect the relevant extension, test, and caller before editing.
2. Confirm the checkpoint repository is healthy with `/pi-config status` when the user is available. Ordinary tracked writes checkpoint automatically.
3. For protected files, wait for the user to enable maintenance mode.
4. Make the smallest change and run the nearest tests.
5. Build changed TypeScript extensions with Bun.
6. Ask the user to disable maintenance mode if it was enabled.
7. Run `/reload` in active Pi sessions after extension changes.

## Recovery

If Pi still loads, use `/pi-config restore [ref]` and review its diff before confirming.

If an extension prevents Pi from starting:

1. Start Pi with `pi --no-extensions`.
2. Inspect checkpoints with `git -C ~/.pi/agent/config-checkpoints log --oneline`.
3. Inspect one saved file with `git -C ~/.pi/agent/config-checkpoints show <ref>:<path>`.
4. Obtain explicit user confirmation before copying saved content over live configuration.
5. Re-run tests and start Pi normally.

Do not run `git checkout`, `git reset`, or bulk restore commands against live configuration without explicit confirmation.

## Durable learning

Learning state is local under `~/.agents/state/learning/`. Observations contain bounded prompts and metadata only. They omit tool inputs, tool outputs, transcripts, remote credentials, and secrets.

Commands:

```bash
python3 ~/.agents/scripts/agent_learning.py status
python3 ~/.agents/scripts/agent_learning.py analyze
python3 ~/.agents/scripts/agent_learning.py promote
python3 ~/.agents/scripts/agent_learning.py projects
python3 ~/.agents/scripts/agent_learning.py export --output instincts.yaml
python3 ~/.agents/scripts/agent_learning.py import instincts.yaml
python3 ~/.agents/scripts/agent_learning.py prune
```

The observation hook is `~/.agents/hooks/bin/learning-observe.sh`. It is not globally activated. Do not activate it or export learning data without user approval.

## Verification

```bash
bun test ~/.pi/agent/tests
node ~/.agents/hooks/test-command-guard.mjs
python3 ~/.agents/tests/test_agent_learning.py
bun build ~/.pi/agent/extensions/protected-agent-files.ts --target=node --packages=external --outfile=/tmp/protected-agent-files.js
bun build ~/.pi/agent/extensions/config-checkpoint.ts --target=node --packages=external --outfile=/tmp/config-checkpoint.js
```

When a remote host has no Bun, run `npm ci --ignore-scripts --dry-run` and Python or Node checks there, then run Bun tests and extension builds locally before syncing. Do not weaken the local verification gate to match the remote toolset.

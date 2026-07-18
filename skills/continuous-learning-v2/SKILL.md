---
name: continuous-learning-v2
description: Maintain project-scoped learning observations, instincts, and memory.
origin: ECC
version: 2.1.0
---

# Continuous Learning v2

Project-scoped observations → instincts (confidence-weighted) → optional promote/evolve. Data stays local.

## When

Status/review of learned instincts, analyze observations, promote project→global, export/import, or explain how learning is stored.

## Storage

Under `$AGENTS_ROOT/state/learning/` (default root `~/.agents` if unset):

- `projects/<hash>/observations.jsonl` + `instincts/`
- `global/preferences/` (global instincts)
- `projects.json` registry

Project id: git remote hash, else repo path, else global fallback.

## Commands

```bash
python3 "$AGENTS_ROOT/scripts/agent_learning.py" status
python3 "$AGENTS_ROOT/scripts/agent_learning.py" analyze
python3 "$AGENTS_ROOT/scripts/agent_learning.py" promote
python3 "$AGENTS_ROOT/scripts/agent_learning.py" projects
python3 "$AGENTS_ROOT/scripts/agent_learning.py" export --output instincts.yaml
python3 "$AGENTS_ROOT/scripts/agent_learning.py" import instincts.yaml
python3 "$AGENTS_ROOT/scripts/agent_learning.py" prune
```

Use `python3 ~/.agents/scripts/agent_learning.py …` when `$AGENTS_ROOT` is unset.

## Instinct shape

Atomic YAML: trigger, action, confidence (0.3–0.9), domain, scope (`project`|`global`), evidence. Prefer project scope for framework/style; global for security/process universals.

## Observation capture

Prefer the shared hook entrypoint when configured:

`$AGENTS_ROOT/hooks/bin/learning-observe.sh`

Do not invent skill-local hook paths that are not present in this tree.

## Privacy

Observations local; export instincts only (not raw transcripts) and only when the user asks.

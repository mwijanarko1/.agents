---
summary: "Token-saving context intake rules, byte-capped command patterns, and handoff templates."
read_when: "When a task involves large logs/data/repos, long sessions, context compaction, or token budget optimization."
---

# Context Economy

Use distilled context before raw context. The default flow is:

1. **Map first**: create a bounded needle map for an unknown repo, file, log, JSON, or CSV.
2. **Inspect only the needle**: decide which small source ranges matter.
3. **Open targeted snippets**: read exact files/ranges only when the summary proves they are relevant.
4. **Persist handoff**: keep actionable state in `HANDOFF.md` or project docs, not in repeated chat narration.

## Command Output Protection

Any command with unknown or potentially large output must be capped:

```bash
COMMAND 2>&1 | head -c 6000
```

If full output may be useful later:

```bash
COMMAND > /tmp/agent-output.txt 2>&1
head -c 6000 /tmp/agent-output.txt
# inspect ranges only when needed
```

Common safe patterns:

```bash
git status --porcelain | head -n 50
git log --oneline -20
git diff --name-only | head -n 80
grep -n "ERROR\|WARN\|FAIL" file.log | head -n 40
find . -path './node_modules' -prune -o -path './vendor' -prune -o -path './.git' -prune -o -type f | head -n 100
```

## Needle Map Helpers

Use `~/.agents/scripts/context_needle.py`:

```bash
python3 ~/.agents/scripts/context_needle.py repo-map .
python3 ~/.agents/scripts/context_needle.py file-summary path/to/file --lines 80 --chars 6000
python3 ~/.agents/scripts/context_needle.py json-summary data.json --chars 6000
python3 ~/.agents/scripts/context_needle.py csv-summary trades.csv --scan-rows 500 --sample-rows 5
python3 ~/.agents/scripts/context_needle.py log-filter app.log --pattern 'ERROR|WARN|Traceback' --limit 40
```

## Handoff Template

Keep under roughly 1k tokens.

```md
# HANDOFF

## Current goal
- ...

## Success metrics
- ...

## Key files
- `path`: why it matters

## Decisions
- ...

## Commands run
- `command`: outcome

## Known issues / do not re-read
- ...

## Next steps
1. ...
```

## Milestone Distillation

At phase boundaries, distill decisions, paths, commands, and open risks into the handoff; drop raw tool logs and large command dumps from active context. Never copy secrets, tokens, or `.env` contents into handoffs or chat. Compact only after preserving the useful state, and do not hand-edit machine continuation data.

## Do Not Rules

- Do not read raw large data when a 50-line summary is enough.
- Do not inspect vendor/build/cache/generated/archive directories by default.
- Do not paste full source or logs unless explicitly requested.
- Do not let agents rediscover stable repo facts every session; use handoff and codebase maps.

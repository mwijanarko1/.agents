---
name: workflow-1
description: "Plan/delegate/review in the current Pi session; implement via a second same-cwd Pi process (xAI Grok 4.5, thinking high) over pi-intercom. Use when the user says workflow-1, /workflow-1, grok implementer, or wants this planner to orchestrate while a Grok 4.5 Pi pane codes. Different from advisor because the peer implements rather than advising. Different from orchestrator-mode because the only implementer is a fixed Grok Pi peer over intercom, not Devin/Cursor/cmd/subagents."
---

# Workflow-1

Current session owns plan, delegation, review, and user reporting. A second Pi process in the same working directory, running xAI Grok 4.5 at thinking high, owns implementation. All handoffs go through pi-intercom.

Requires `HERDR_ENV=1`. If missing, stop and say Herdr is required.

## Roles

| Role | Who | May edit project files |
|---|---|---|
| Planner / reviewer | this session | no (read/status/diff/verify only while the worker is active) |
| Implementer | peer named `workflow-1` | yes (sole writer in this cwd) |

Do not change implementer model or thinking unless the user overrides them for this run.

## Defaults

| Setting | Value |
|---|---|
| Session name | `workflow-1` |
| Provider/model | `xai/grok-4.5` |
| Thinking | `high` |
| Split | right of current pane, `--no-focus` |
| Channel | `intercom` `ask` for tasks that need a completion report; `send` for non-blocking notes or long jobs that will report back |

## Ensure implementer is up

1. `intercom({ action: "list" })`
2. Prefer an already-connected peer named `workflow-1` in the same cwd on `xai/grok-4.5`.
3. If none, launch:

```bash
test "${HERDR_ENV:-}" = 1 || { echo "HERDR_ENV not set; run inside Herdr" >&2; exit 1; }

SPLIT_JSON="$(herdr pane split --current --direction right --cwd "$PWD" --no-focus --ratio 0.45)"
PANE_ID="$(printf '%s\n' "$SPLIT_JSON" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["result"]["pane"]["pane_id"])')"

herdr agent start workflow-1 \
  --kind pi \
  --pane "$PANE_ID" \
  --timeout 60000 \
  -- \
  --provider xai \
  --model grok-4.5 \
  --thinking high \
  -n workflow-1 \
  --append-system-prompt "You are the workflow-1 implementer pane. The peer planner owns plan, scope, and acceptance. You own code changes in this cwd only. Work from the intercom brief. Do not broaden scope. One writer: you. Prefer smallest correct change. Run the scoped verify the brief names. When done or blocked, reply over intercom with: changed files, commands run, verification result, blockers, and whether planner action is needed. Ask the planner over intercom for user-owned decisions; do not guess them."
```

4. Wait until idle and on intercom:

```bash
herdr agent wait workflow-1 --until idle --timeout 90000
```

5. Re-run `intercom({ action: "list" })`. Target by name `workflow-1`, or by short id if the name is ambiguous.

If launch fails because the pane is not at a shell prompt, close that empty pane, split again, and retry once. Do not keep opening panes.

## Planner loop

### 1. Plan (this session)

1. Restate goal, non-goals, and acceptance in one short block.
2. Inspect only what is needed to write a brief (status, key files, failing checks).
3. Resolve user-owned decisions before delegating. Do not push preference calls to the implementer.
4. Snapshot dirty state before handoff:

```bash
git status --short
git diff --stat
```

### 2. Delegate (intercom)

Default is one packed `ask` so the implementer returns a completion report. Front-load context; do not drip-feed.

```js
intercom({
  action: "ask",
  to: "workflow-1",
  message: [
    "Role: workflow-1 implementer. You are the sole writer in this cwd.",
    "Goal: <one sentence success>",
    "Non-goals: <explicit outs>",
    "Scope: <files/functions/surfaces only>",
    "Constraints: <repo conventions, APIs to keep, ponytail-minimal if coding>",
    "Repo: <cwd, branch, known dirty paths unrelated to this task>",
    "Plan: <ordered steps>",
    "Do not touch: <paths>",
    "Verify: <exact commands>",
    "Done means: <acceptance checks>",
    "Report format:",
    "1. Changed files",
    "2. Commands run + outcomes",
    "3. Verification",
    "4. Risks / leftovers",
    "5. Needs planner: yes/no + question",
  ].join("\n"),
  attachments: [
    {
      type: "file",
      name: "path/in/repo.ts",
      content: "<full file or full relevant section>",
    },
    {
      type: "snippet",
      name: "failing-check",
      language: "text",
      content: "<verbatim output>",
    },
  ],
});
```

Attachment rules:

- Prefer `type: "file"` with the real relative path.
- Include every file the implementer must change or match.
- Attach failing command output verbatim.
- Attach the current relevant diff when continuing a fix round.
- No secrets or huge unrelated dumps.

Long jobs (likely past the intercom ask timeout): use `send` with the same brief, and require the implementer to `ask` back on completion or blocker. While waiting, stay read-only; do not start a second writer.

### 3. While the implementer works

- Do not `edit` / `write` project files in this cwd.
- Answer implementer `ask`s promptly via `intercom({ action: "reply", ... })`.
- `intercom({ action: "pending" })` if multiple asks are open.
- Optional status only: `herdr pane read <pane_id> --source recent-unwrapped --lines 80`.

### 4. Review (this session)

After the completion report:

```bash
git status --short
git diff --stat
git diff -- <changed files>
```

Check:

1. Diff matches the brief (no scope creep).
2. Verify commands were run; re-run the cheapest critical ones yourself if needed.
3. Accept, or send one packed fix brief (same `ask` shape) with exact faults and file:line evidence.
4. Cap fix rounds at two unless the user authorizes more.

### 5. Report to user

Compact:

1. Plan
2. What the implementer changed
3. Verification
4. Open risks or next decision

## Rules

- This skill authorizes the Grok implementer peer. Do not also fan out to Devin, Cursor, cmd, or subagent writers for the same cwd task unless the user explicitly expands the workflow.
- One `workflow-1` implementer pane per cwd. Reuse it across rounds in the session.
- Parent stays on plan/review. Implementer stays on code.
- Same cwd means one writer: the implementer. Parent is read/diff/verify only during active implementation.
- Do not use `openProjectPaneIfMissing` for this skill. That path starts plain `pi` without the fixed Grok high setup.
- If intercom is down, report that. Do not silently paste the full brief into the pane unless the user asks for a pane-only fallback.
- User-owned decisions stay with the planner (or escalate to the user). The implementer does not invent requirements.
- Leave the pane up unless the user asks to close it.

## Teardown

```bash
herdr pane close <workflow-1_pane_id>
```

## Different from nearby skills

| Skill | Boundary |
|---|---|
| `advisor` | Peer advises; does not implement by default |
| `orchestrator-mode` | Multi-agent manager with Devin/Cursor/cmd priority |
| `agent-delegation` | External tool bridge (`ai-delegate`), not a Grok Pi peer |
| `pi-subagents` | In-process child agents, not a visible same-cwd Grok pane |

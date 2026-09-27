---
name: advisor
description: "Consult a dedicated Pi advisor pane (OpenAI Codex GPT-6 Astra, thinking high) via Herdr + pi-intercom. Use when the user says advisor, ask the advisor, spin up advisor, consult Astra, second opinion from Astra, or wants the current agent to question a separate high-thinking Astra session. Different from council-mode because this is one visible Herdr advisor pane, not a multi-advisor subagent council. Different from agent-delegation because the peer is another Pi session, not an external tool bridge."
---

# Advisor

Spawn or reuse one visible Herdr Pi pane named `advisor`, running OpenAI Codex GPT-6 Astra at thinking high. The current session asks it questions over pi-intercom and keeps ownership of the work.

Requires `HERDR_ENV=1`. If missing, stop and say Herdr is required.

## Defaults

| Setting | Value |
|---|---|
| Session name | `advisor` |
| Provider/model | `openai-codex/gpt-6-astra` |
| Thinking | `high` |
| Split | right of current pane, `--no-focus` |
| Channel | `intercom` `ask` for answers you need; `send` for fire-and-forget notes |

Do not change model or thinking unless the user overrides them for this run.

## Ensure advisor is up

1. `intercom({ action: "list" })`
2. Prefer an already-connected peer named `advisor` in the same cwd.
3. If none, launch:

```bash
test "${HERDR_ENV:-}" = 1 || { echo "HERDR_ENV not set; run inside Herdr" >&2; exit 1; }

SPLIT_JSON="$(herdr pane split --current --direction right --cwd "$PWD" --no-focus --ratio 0.45)"
PANE_ID="$(printf '%s\n' "$SPLIT_JSON" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["result"]["pane"]["pane_id"])')"

herdr agent start advisor \
  --kind pi \
  --pane "$PANE_ID" \
  --timeout 60000 \
  -- \
  --provider openai-codex \
  --model gpt-6-astra \
  --thinking high \
  -n advisor \
  --append-system-prompt "You are the advisor pane. Answer the calling Pi session over intercom. Be direct, evidence-first, and concise. Challenge weak plans. Do not implement, edit files, or run mutating commands unless the caller explicitly asks you to. Prefer recommendations, risks, and the next decision."
```

4. Wait until the advisor is idle and on intercom:

```bash
herdr agent wait advisor --until idle --timeout 90000
```

5. Re-run `intercom({ action: "list" })`. Target by name `advisor`, or by the short id if the name is ambiguous.

If launch fails because the pane is not at a shell prompt, close that empty pane, split again, and retry once. Do not keep opening panes.

## Ask the advisor (expensive model: max clarity, min round-trips)

Astra is costly. Assume **one `ask` must be enough**. Never send a thin question and hope for follow-ups. Front-load every fact, file, and constraint the advisor would otherwise have to rediscover.

### Before you ask

1. Decide the single decision or judgment you need.
2. Gather evidence yourself: read the relevant files, capture errors, note git status / branch / dirty paths, list options already considered and why they are weak.
3. Attach file bodies. Do not rely on paths alone. The advisor should not need to re-open the tree to understand the problem.
4. Cut noise, not substance. Omit unrelated modules. Include full relevant functions, configs, logs, and failing tests.

### Brief template (required shape)

```js
intercom({
  action: "ask",
  to: "advisor",
  message: [
    "Role: second-opinion advisor on expensive model. Do not implement unless explicitly asked.",
    "Goal: <what success looks like in one sentence>",
    "Decision needed: <one concrete question the reply must answer>",
    "Non-goals: <what not to solve>",
    "Repo: <cwd, branch, relevant dirty files>",
    "User intent / constraints: <quotes or hard requirements>",
    "What I already tried or ruled out: <bullets with reasons>",
    "Current plan or hypothesis: <your best answer so far>",
    "Options on the table: A) ... B) ... C) ...",
    "Key risks / unknowns: <bullets>",
    "Evidence index: <path list matching attachments>",
    "Error / test output (verbatim, trimmed to signal):",
    "<paste>",
    "Reply format:",
    "1. Recommendation (pick or revise an option)",
    "2. Why (cite attached files / lines)",
    "3. Risks and failure modes",
    "4. Exact next steps for the primary agent",
    "5. What would change your mind",
  ].join("\n"),
  attachments: [
    {
      type: "file",
      name: "path/in/repo.ts",
      content: "<full file or full relevant section, not a summary>",
    },
    {
      type: "snippet",
      name: "failing-test-or-log",
      language: "text",
      content: "<verbatim output>",
    },
    {
      type: "context",
      name: "design-notes",
      content: "<extra structured context that is not a repo file>",
    },
  ],
});
```

### Attachment rules

- Prefer `type: "file"` for repo sources. One attachment per path. Name is the real relative path.
- Include every file that materially affects the decision (implementations, callers, types, configs, tests, nearby ADRs).
- If a file is huge, attach the full relevant region plus enough surrounding context (imports, types, signatures) that the snippet is self-contained. Say what was omitted.
- Attach failing command output, stack traces, and test names verbatim.
- Attach the current diff or proposed patch when the question is about a change already drafted.
- Do not attach secrets, credentials, or unrelated giant dumps.

### Anti-patterns (do not do)

- "What do you think about auth?" with no files
- Path-only references ("see `src/foo.ts`") without body
- Multi-turn ping-pong to feed context the first ask should have carried
- Asking Astra to explore the repo cold when you already have the evidence
- Several small asks that should have been one packed decision brief

Use `send` only when you do not need a blocking reply. Default is one packed `ask`.

## Rules

- You stay the primary agent. Advisor is consultative by default.
- One advisor pane per cwd. Reuse it across questions in the session.
- Spend tokens on **context quality**, not on extra advisor turns.
- Do not open a project pane via `openProjectPaneIfMissing` for this skill. That path starts plain `pi` without Astra high.
- Do not hand the advisor write ownership of the shared worktree while you are also writing.
- If intercom is down, report that. Do not paste full prompts into the pane as a silent substitute unless the user asks for a pane-only fallback.
- Summarize the advisor reply to the user in your own voice. Quote only the decisive lines.

## Teardown

Leave the pane up unless the user asks to close it:

```bash
herdr pane close <advisor_pane_id>
```

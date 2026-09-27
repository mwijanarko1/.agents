---
name: whatsapp
description: "Read WhatsApp from the macOS desktop ChatStorage DB; send via PinchTab WhatsApp Web. Use when the user says WhatsApp, WA, read chats, message on WhatsApp, or link WhatsApp Web. Different from pinchtab because this owns WA read/send."
---

# WhatsApp (desktop DB read + Web send)

Fast path is the script. Do not rediscover UI or schema.

## Split

| Action | Backend |
|--------|---------|
| Read / search chats | Local macOS WhatsApp Desktop DB (fast, full history on disk) |
| Send / link device | PinchTab headed WhatsApp Web |

DB path:

`~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite`

Snapshot via sqlite backup (WAL-safe). Never write the live DB.

## Commands

```bash
# Read (preferred for history)
python3 ~/.agents/skills/whatsapp/scripts/wa.py chats
python3 ~/.agents/skills/whatsapp/scripts/wa.py chats "Ammar"
python3 ~/.agents/skills/whatsapp/scripts/wa.py read "Ammar" --limit 5

# Send (Web)
python3 ~/.agents/skills/whatsapp/scripts/wa.py ensure
python3 ~/.agents/skills/whatsapp/scripts/wa.py status
python3 ~/.agents/skills/whatsapp/scripts/wa.py send "Ammar" "message text"
python3 ~/.agents/skills/whatsapp/scripts/wa.py send "Ammar" -f /tmp/msg.txt
python3 ~/.agents/skills/whatsapp/scripts/wa.py send "Aarush Aerospace" "..." --jid 971567497515@s.whatsapp.net
```

Optional: `WA_SERVER=http://127.0.0.1:PORT`, `WA_PROFILE=default`.

## Flow

### Read
1. User asks to read/search WhatsApp messages or list chats.
2. Run `read` or `chats`. Report JSON (`sender` is `me` or `them` from `ZISFROMME`).
3. Do not open PinchTab for read unless the DB is missing or the user wants live Web UI.

### Send
1. User names contact + message (required). Recipient safety: if you are not sure of the correct recipient, ask the user. Chats can share a display name (2026-09-08: a DM with history and a bare LID contact were both "Aarush Aerospace"). Prefer the chat that has history in the desktop DB; never guess between same-name chats. wa.py refuses when the target is missing or ambiguous; treat that refusal as: ask Mikhail which chat he means, then retry. Pin a specific DB chat with `--jid <jid>` (list jids via `chats`).
   - If `send` reports the chat cannot be found or opened: first run the tab/window checks in "Session state" below (a stray non-WhatsApp tab is the usual cause). If the chat still will not open by search, ask the user to open the target chat in the Web window once, then retry: the already-open fast path plus the thread guards (identity, timestamps, content probe) makes the retry safe.
2. `ensure` if needed. QR handoff if `login: needs_qr`. `status` with `ui_ready: false` means the Web UI is stale even if `login` looks fine. Run `ensure` (it recovers) before send, or just `send` (it recovers first).
   - `ui_ready: true` proves the elements exist, not that they are reachable. On 2026-09-12 `ensure` returned `ui_ready: true` and the very next click still failed outside the viewport. There is no reliable pre-flight probe for this: `pinchtab box` reports viewport coordinates (search box `y: 76`) and hides the window offset. Treat the first viewport error as the gate: stop there instead of probing.
3. `send "<contact>" "<message>"`. Composer uses `type`, never `fill`.
4. Script output is ground truth. `ok: true` = delivered into thread.
5. Confirm the delivery landed in the intended chat by re-reading that chat from the desktop DB before reporting success.
6. On failure (WaError / `ok: false`): **report to the user, never resend**. The message may already have been sent even when verification fails, so a retry risks a duplicate. Do not re-run `send` unless the user explicitly asks.

### Stale Web session (pre-send recovery)
`send` / `open` / `ensure` run a health check: the search box, New chat, or composer must be in the snapshot. Chrome text like Chats or Unread is not enough.

Recovery runs only when that health check fails, before typing or sending. A click that lands outside the viewport does not trigger it:

1. `pinchtab reload` and wait for the search box.
2. Re-nav to `https://web.whatsapp.com` and wait.
3. Restart the headed browser instance, then wait. Older servers reject this (`instances/<id>/restart` is not supported, likely an older build), and nothing else repositions an off-screen window, so stop here instead of hunting for another lever.

Do not invent a manual PinchTab recovery path. Do not retry `send` after a failure. If the health check and these steps do not fix it, or a click fails outside the viewport, tell the user the headed Helium window needs a look (off-screen or QR).

### Session state: tabs and window position (check first on viewport errors)

Symptoms: `Error 500: action click: element center is outside viewport` with negative x or y, searches that return nothing, queries that never register, keystrokes that do not land.

Root causes seen 2026-09-08 and 2026-09-12:

1. A second, non-WhatsApp tab (e.g. `about:blank`) in the headed window. Snapshots and clicks act on the wrong viewport even when pinchtab reports the WhatsApp tab as active. `ensure_wa_tab` activates the WhatsApp tab; for a stubborn stray, list and close it:
   `pinchtab --server http://127.0.0.1:9869 tab`, then `tab <id>` to focus and `tab close <id>`.
2. Window partially off-screen (top-left). Top-of-page elements such as the search box become unclickable while mid and lower page elements still work. On 2026-09-12 the search box measured `y: 76` via `box` while the click resolved to `y: -30`, and `ensure` had returned `ui_ready: true` moments earlier. Reload and instance restart may not fix the position; when automation cannot reach the window, ask the user to look at it. This is a 2-call dead end, not a puzzle: read the target chat to confirm nothing was delivered, then stop and ask. Do not burn calls probing the DOM, the tabs, the window geometry, or alternative recovery paths, and do not resend on your own initiative. If the user would rather not move the window, the composer of an already-open thread sits at the bottom of the page and stays reachable, so `send "<contact>" --jid <jid>` works once that chat is open.
3. WhatsApp Web search does not index every chat under "Chats". Some chats only match "Groups in common" or "Messages", or not at all, even though the chat is in the account and opens from the chat list (Aarush Aerospace is a known case). Search-based open then fails with "thread would not open"; the fallback is to ask the user to open the chat from the list once, then send via the already-open fast path.

## Voice: replies read like Mikhail texting, not like an AI

Before composing a send, read the thread (`read "<contact>"`, scale the limit to the exchange) and calibrate to its register. Contacts vary: some write proper sentences, some lowercase fragments. Match their energy and message length, but compose with full `you`/`your` and proper capitalization no matter how casual the thread reads. Write like a mate texting, never like drafted prose.

Context window for a reply is the hour or day around the latest message: read enough to answer the arc of the conversation (what started it, where it moved), never the entire chat, never only the last line.

Rules (same source family as `~/.agents/AGENTS.md` Voice and Tone, the `humanizer` skill, and llm-wiki/AGENTS.md AI Writing Style Prohibitions):

- Match the contact's energy and the thread's level of formality. Copy its contractions, slang, and message length; do not upgrade casual into neat prose.
- Compose with full `you` and `your` (never `u` or `ur`) and proper capitalization: capital sentence starts and a capital `I`. This is a hard rule that applies even in lowercase, fragmented threads.
- Reply to an opening greeting before anything else. A message that starts "Assalamualaikum" gets a "Wa alaikumassalam" first (one word, no space), then the actual content. Match the fuller form when used: "Wa alaikumassalam wa rahmatullah".
- Correct Arabic dua forms in Islamic threads: reply "JazakAllahu khairan" (full correct form), not the casual "JazakAllah khair".
- For a shared reflection or a long forward, pick one of two human shapes, not the middle: send back a similar verse or your own short reflection, or keep it tight (thanks plus one honest note, like "JazakAllahu khairan for this, needed the reminder."). Do not echo their whole message back with generic praise.
- A matching Quran verse link, sent alone with no commentary, is a complete human reply to a religious share. Real example: someone moved by how the Prophet cares for the ummah gets only "https://quran.com/at-tawbah/128". Do not append "this verse reminds me of what you said".
- One idea per message, short. Cut until only the two or three points that matter survive. If a reply needs 4+ lines, it is too long.
- Default to the most concise reply that does the job. When in doubt, send less, not more. A postponement request gets "no worries", not "no worries, tomorrow works. Go smash your sabaq". A parent's call to action gets "iya", not an unprompted plan.
- Calibrate to the relationship, not just the register. Peer slang (Indonesian "gua"/"lu") is fine with friends but never with parents or elders, even in a chat where the elder writes casually. Match their formality level upward, not sideways.
- Banter replies are short dismissals, not speeches. Defending against a "try harding" jab is "get good". Against a follow-up joke, reply with a separate one-liner on that joke ("nah ai game is horrible"), not one long flex that re-explains the whole thing. Cold and short reads more human than clever and long. A "u ain't a president" jab gets shrugged off with bravado ("fake it till you make it"), not a denial and not a defense.
- When you cannot help with a request (an intro, a connection), say so plainly and offer to route if anything surfaces: "I can't help with either off the top of my head. If I hear of anyone I'll point them your way". Never invent a connection or a fake intro.
- State the decision without the reasoning unless the question asks for it. A time-pick reply is "Wa alaikumassalam wa rahmatullah. 6pm works for me", not "...6pm works for me, an hour at 7pm is too tight". The context already carries the why.
- Spell out "in sha Allah" in full; never abbreviate it as "iA".
- Plain text only. No markdown, no bold/italic, no headers, no bullet lists, no arrows, no em dashes, no curly quotes, no closing signature, no "sent from" lines.
- No AI tells: no ChatGPT-isms ("Great question!", "Here's the thing", "Let's dive in", "Feel free to reach out"), no AI vocabulary (delve, intricate, underscores, pivotal, testament, fostering, landscape, tapestry, showcase), no significance inflation, no sycophancy ("That's a great point"), no hedging, no rhetorical questions, no rule-of-three runs, no formulaic closers ("Excited to hear your thoughts").
- No emoji unless the contact's messages use them in kind. Never start emoji with strangers to that style.
- Never fabricate facts, numbers, quotes, or claims about what Mikhail did or feels. When a reply needs a fact only Mikhail knows, ask him or send the plain version without it.
- When the agent is the sender, stay transparent (as in this thread: "this is Mikhail's agent") but still text like a person.
- If unsure the draft passes, run it through the `humanizer` skill before sending.

Example register: "Honestly the ROI is so one sided it's a rounding error. Being early is the whole edge" beats "Great question! The return on investment is truly remarkable and underscores the pivotal advantage of early adoption."

Full checklist with AI-to-human swaps: `references/human-voice.md`.

## Rules

- If you are not sure of the correct recipient, ask the user. Do not guess between chats that share a name; the chat with history in the desktop DB is the usual intended target.
- Read from desktop DB only for this skill's read path.
- Do not dump unrelated chats. Scope to the named contact/query.
- Sending is consequential; only when the user specified recipient and body.
- Groups: only if the user named that group exactly.
- The headed window is shared with the user. Prefer activating the WhatsApp tab over closing other tabs; close only obvious strays (about:blank) and tell the user you did.
- Leave headed Web session up after send. Do not `server stop`.
- Desktop app must have been linked/synced for DB freshness; very new Web-only messages may lag until Desktop catches up.

## Boundary

| Need | Use |
|------|-----|
| Generic browser | `pinchtab` |
| WhatsApp read / send | **this skill** |

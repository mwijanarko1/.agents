---
name: quran-revision
description: >
  Quran revision / muraja'ah sessions via the local Al Muraja'ah CLI. Use when
  the user says Quran revision, murajaah, muraja'ah, hifz review, cold test,
  revise from memory, revision session, or asks what is due today for Quran
  revision. Different from islam-wiki because this operates personal revision
  data through the CLI, not hadith/text research.
---

# Quran Revision

Personal hifz revision coach. Phone app = normal circulation. Pi + CLI = solidify from memory.

## Paths

```bash
CLI=/Users/mikhail/al-murajaah-cli/murajaah
DATA=/Users/mikhail/AlMurajaah-Data   # or $MURAAJAH_DATA
PLAN=$DATA/revision-plan.md          # active multi-day plan (durable)
JOURNAL=$DATA/revision-journal.sqlite
```

Always run CLI from absolute path. Parse JSON stdout (`ok`, `data` / `error`).

## Session start (always)

1. Read `$PLAN` if it exists — this is the active long-term plan (priority order, day index, today’s block).
2. ` "$CLI" doctor ` — refuse if prefs/userData missing or hash/doctor errors look fatal.
3. ` "$CLI" status ` — profile, streak, todayPages, due.
4. ` "$CLI" notes list --limit 20 ` — solid/weak/focus/plan notes from journal.
5. Present **today’s block from `$PLAN` Progress**, not a fresh invented queue:
   - Default cadence: **5 pages/day from memory**
   - Follow Phase A priority order in the plan file
   - Mention streak + todayPages
6. If user changes priorities, update `$PLAN` and add a journal `note --tag plan`.

## Dual workflow

| Surface | Role |
|---------|------|
| Phone Al Muraja'ah | Normal sequential revision routine |
| Pi + CLI | From-memory solidify: random starts, cold tests, honest grading, mark only after recitation |

Rules:
- Do **not** mark revised until the user actually recited (or explicitly asks to log phone work).
- Prefer memory-first: give start cue only (surah/juz/part/verse), hide full text unless stuck.
- After each portion: ask grade → then CLI revise if completed.

### Grades (log as revise when completed)

| Grade | Meaning | Action |
|-------|---------|--------|
| Fluent | No prompts | `revise` |
| Hesitated | Recovered alone | `revise` |
| Prompted | Needed help | `revise` + keep in repair queue next session |
| Broke down | Could not continue | Do **not** revise; retest soon |

## CLI commands

```bash
"$CLI" doctor
"$CLI" status [--profile NAME]
"$CLI" profile list
"$CLI" profile use NAME
"$CLI" profile set-cycle --days N [--juz J] [--surah S]
"$CLI" revise --juz J --surah S          # whole surah-in-juz
"$CLI" revise --juz J --part PART_ID     # e.g. 2-1
"$CLI" revise --juz J                    # all memorized surahs in juz
"$CLI" pull --device "AI Bot"            # refresh local from phone
"$CLI" push --device "AI Bot" --confirm PUSH   # only when user asks
"$CLI" cold-test                         # self-check; not a user session
"$CLI" note "Juz 30 is solid in my head" --tag solid
"$CLI" note "Yusuf middle weak" --surah 12 --juz 12 --tag weak
"$CLI" notes list --limit 20
"$CLI" notes summary --days 30
```

### Local memory for new Pi agents (not on phone)
| File | What |
|------|------|
| `$PLAN` (`revision-plan.md`) | Active multi-day plan, priority order, current day |
| `$JOURNAL` via `note`/`notes` | Solid/weak/focus/plan freeform facts |
| App plist/`userData.json` | Revised dates, pages, streaks |

Do **not** push journal/plan to the phone. App revise data stays in plist/userData.
New agents: always load `$PLAN` + notes before proposing work.

### Revise rules
- Need valid surah+juz pair (catalog-backed). Invalid pairs error — fix args, don't invent.
- Split surahs: prefer `--part` when user did one part only.
- Never push unless user explicitly wants phone sync; require exact `--confirm PUSH`.
- Quit app before push. Prefer pull before a session if phone may be newer and local is not dirty.

## During session

1. Pick next due item from plan.
2. Cold prompt examples:
   - "Continue from surah X juz Y, start only — no mushaf."
   - "Random start: give first words of ayah N, continue."
3. User recites.
4. Grade → if Fluent/Hesitated/Prompted and finished: run `revise`.
5. Confirm JSON `ok: true`, new `todayPages`, and remaining due count.
6. Continue until plan done or user stops.

## Session end

1. Update `$PLAN` Progress (day index, completed days, next block).
2. Report compactly: portions revised, pages/todayPages, streak, next block, dirty flag.

## Safety

- Local-first. Phone writes only via `pull`/`push`.
- Do not edit plist/json by hand; CLI only.
- Do not lower counters or touch `revisionBaseline_*`.
- If `doctor` shows dirty + user wants phone data: ask pull-vs-push; never clobber silently.
- If CLI fails: show `error.code`/`message`; do not fake success.

## Example openers

User: "let's do Quran revision" / "let's do murajaah"
→ doctor + status → propose oldest-due block → start first cold prompt.

User: "I just finished Yusuf on my phone, log it"
→ `revise --surah 12 --juz 12` (confirm juz if multi-juz) → report pages.

User: "sync from phone"
→ `pull --device "AI Bot"` (refuse if dirty unless user forces).

User: "these are solid in my head: juz 30 and fatiha"
→ `note` each claim with `--tag solid` (and juz/surah if clear) → confirm saved.

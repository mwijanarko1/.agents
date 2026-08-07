# Cold outreach flow (Himalaya) — email channel only

Use this when the listing’s apply path is **email** (`apply_channel=email`). For web/ATS or LinkedIn, use `apply-flow.md` instead.

## Goal

**Get an interview.** That is the only success metric for outreach copy.

The reader gets hundreds of emails. Yours has to earn a reply in a few seconds: specific, human, hard to ignore, still professional. Attach a tailored one-page CV. Log every attempt to SQLite with `--channel email`.

## Prerequisites

- Tailored CV PDF: `$OUT/$JOB_SLUG/LATEST-CV.pdf` or `~/Documents/job-apply/CV/LATEST-CV.pdf`
- Contact with a real email (see `contacts.md` quality bar)
- Skill **`himalaya`** loaded; `~/.config/himalaya/config.toml` works
- `job_id` in DB when available

## Contact priority (by company size)

Pick the smallest relevant tier. Do **not** email CEOs/founders at large companies.

### Early-stage / small startup (roughly <50 people, seed–Series A vibe)
1. Founder / CTO / Head of Engineering (they actually hire)
2. Named eng manager or hiring manager on the post
3. High-confidence Hunter hit with eng/product leadership title
4. Recruiter only if no eng leader email
5. Generic `careers@` last resort — note weakness

### Growth / mid-size (roughly 50–500, Series B+ or established product co)
1. Engineering Manager / hiring manager for the team (named on post or team page)
2. Team lead / staff eng who owns the domain (if public + relevant)
3. Recruiter / talent acquisition named on the post
4. High-confidence Hunter hit with EM/recruiting title
5. Generic `careers@` last resort — note weakness

### Large / enterprise (500+, public cos, big brands)
1. Named hiring manager or EM on the **job post** only
2. Recruiter / talent acquisition named on the post
3. High-confidence Hunter hit with recruiting or EM title for that org/team
4. Public `mailto:` on the role’s careers page
5. Generic `careers@` / `jobs@` only if nothing better — note weakness

**Never for large cos:** CEO, founder, group CTO, generic board/exec inboxes. They will not read grad/junior cold email.

No usable email → stop outreach for that target; offer LinkedIn search URL for manual use only.

When drafting, one line in chat: `size tier: startup | mid | large → play {play_id} → contacting {role}` so Mikhail can correct the tier.

Play ids (`config/plays.yaml`): `startup_founder` | `mid_em` | `large_recruiter`. Check `banned_lines_global` before send.

## Draft rules

### North star

Write like you are competing with a full inbox. Subject + first two lines decide everything. If it could be pasted to any company, rewrite it.

**Optimize for: open → read → reply → interview.**
Not for following a template. Not for sounding like every other grad email.

### What “good” feels like

- Specific to *this* company / product / role (research their site, product, news, JD)
- One sharp reason they should care (real project, real overlap, real proof)
- Sounds like a sharp human, not a cover letter robot
- Short enough to finish on a phone
- Clear ask that is easy to say yes to (chat / call / 15 minutes)
- Appropriate: professional, confident, no gimmicks, no cringe, no spam tricks

### Hard constraints only (non negotiable)

- **Truth only.** No invented jobs, projects, metrics, employers, or skills.
- **Employment framing:** job seeking now. Pivot2Tech is past experience. Never “I am an intern at…”, “currently at Pivot2Tech”, “internship ended”, or “I am unemployed”. Lead with what you built.
- **No dashes in email copy** (em, en, or hyphen as punctuation). Commas, periods, colons, parentheses.
- **Tailor the CV** to the JD before send and attach that PDF.
- **From** Himalaya **`wijanarko`** only (`mikhail.wijanarko2003@gmail.com`, always `-a wijanarko`).
- **Mikhail approves** before send (unless he already said send it).
- One target at a time. No spray and pray.

### Research (do the work, then write freely)

Before drafting, actually look: company site, product pages, blog/changelog, JD, recent news if useful. Pull whatever makes the email impossible to confuse with a mass blast. Map the strongest real proof from Pivot2Tech / GitHub / cv-data (`gh` if needed).

If you cannot find anything specific, research more or skip. Do not send generic.

### No mandatory template

There is no required paragraph order, sentence count, or magic phrase list.
Use whatever structure best earns a reply for *this* target.
Subject lines can be bold or plain; pick what gets opened for that inbox.

Useful ingredients when they help (optional, not a checklist):
- a concrete detail only a real reader would know
- a project that clearly maps to their problem
- a reason this role, not any role
- CV attached
- low friction ask for a conversation

### Proof bank (use when it wins attention)

**Spread the portfolio.** Never make PromptPal (or any one project) the whole email. Lead with the builder pattern, then 2–4 role-relevant hits.

| Project | Often strong for |
|---|---|
| PromptPal (RN/Expo, AI scoring, game loops) | learning products, AI in product, mobile, gamification |
| My Akhirah Account (Next.js, donations, webhooks, admin) | payments, checkout, fintech/charity flows, admin tooling |
| Al Muraja'ah / Quran apps (Swift, App Store) | mobile, education, consumer apps, downloads proof |
| Masjidly / QuranScroll (App Store) | consumer mobile shipping |
| MWHS site (Next.js, live traffic) | web product, real users, admin tooling |
| AI Bridge (agent harness / MCP) | agentic tooling, AI-native eng culture |
| Client sites (Next.js) | web product, local business, SEO |
| Other real `gh` / cv-data work | only when it is the strongest hook |

Never invent a project.

**Location:** Sheffield based. Happy to relocate anywhere. Never claim London (or the job city) as home.

## Send steps

1. Draft in chat (or Himalaya draft) with To, Subject, body, attachment path.
2. **Mikhail approves** (or already said “send it”).
3. Send with Himalaya CLI per the himalaya skill (attach PDF), always `-a wijanarko`.
4. Log DB:

```bash
python3 ~/.agents/skills/job-apply/scripts/db.py apply \
  --job-id "$JOB_ID" \
  --status applied \
  --applied \
  --channel email \
  --tier "$TIER" \
  --contact-role "$ROLE" \
  --contact-email "$EMAIL" \
  --contact-name "$NAME" \
  --play "$PLAY" \
  --subject "$SUBJECT" \
  --cv-pdf "$CV_PDF" \
  --notes "Cold email to $NAME <$EMAIL>; subject: $SUBJECT; via Himalaya"
```

(`apply --applied` also appends `outcome=sent` to SQLite + `memory/outcomes.jsonl`.)

If he rejects the draft or contact is bad:

```bash
python3 ~/.agents/skills/job-apply/scripts/db.py apply \
  --job-id "$JOB_ID" \
  --status draft \
  --notes "Outreach held: $REASON"

python3 ~/.agents/skills/job-apply/scripts/db.py outcome \
  --job-id "$JOB_ID" --outcome held --reason "$REASON"
```

### After send (when known)

```bash
# ~7 days silence
python3 ~/.agents/skills/job-apply/scripts/db.py outcome \
  --job-id "$JOB_ID" --outcome no_reply \
  --reason "no response after 7 days; play=$PLAY tier=$TIER"

# Positive / negative reply
python3 ~/.agents/skills/job-apply/scripts/db.py outcome \
  --job-id "$JOB_ID" --outcome reply \
  --reason "asked for a call next week; liked RN proof"

python3 ~/.agents/skills/job-apply/scripts/db.py outcome \
  --job-id "$JOB_ID" --outcome bad_fit \
  --reason "want 3+ years commercial React; grad path closed"

python3 ~/.agents/skills/job-apply/scripts/db.py outcome \
  --job-id "$JOB_ID" --outcome interview \
  --reason "screen scheduled Thursday"
```

## Pace / safety

- One email per target unless he asks for a follow-up
- Pause between sends; no bulk blasts
- No purchased lists, breach data, or fake personas
- Optional one polite follow-up after ~5–7 days only if he asks
- Weekly improver: `references/self-improve.md` + `scripts/weekly_tune.sh` (no auto-send)

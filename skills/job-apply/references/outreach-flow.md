# Cold outreach flow (Himalaya)

## Goal

Email a real hiring contact about a role/company. Attach the tailored one-page CV. Log every attempt to SQLite.

**Do not** submit LinkedIn Easy Apply, ATS forms, or company career-site applications.

## Prerequisites

- Tailored CV PDF: `$OUT/$JOB_SLUG/LATEST-CV.pdf` or `~/Documents/CV/LATEST-CV.pdf`
- Contact with a real email (see `contacts.md` quality bar)
- Skill **`himalaya`** loaded; `~/.config/himalaya/config.toml` works
- `job_id` in DB when available

## Contact priority

1. Named hiring manager on the post
2. Recruiter / talent acquisition named on the post
3. High-confidence Hunter hit with recruiting/people title
4. Public `mailto:` on company careers / team page
5. Generic `careers@` / `jobs@` only if nothing better — note weakness in draft

No email → stop outreach for that target; offer LinkedIn search URL for manual use only.

## Draft rules

- Short: subject + 3–6 body lines + signature
- Cold, not “I already applied on your portal”
- One concrete fit line from the tailored CV / JD
- Soft ask (15 min chat / happy to share more)
- Truth only — no invented experience
- From address = Mikhail’s configured Himalaya account only

### Template

```text
Subject: {Role} — {Company}

Hi {FirstName},

I'm a software engineer focused on {1–2 stack matches}. I saw the {Role}
opening at {Company} and thought my work on {one proof point} might be relevant.

I've attached a one-page CV. Happy to chat if useful.

Best,
Mikhail Wijanarko
{email} · {phone} · {linkedin or website}
```

## Send steps

1. Draft in chat (or Himalaya draft) with To, Subject, body, attachment path.
2. **Mikhail approves** (or already said “send it”).
3. Send with Himalaya CLI per the himalaya skill (attach PDF).
4. Log DB:

```bash
python3 ~/.agents/skills/job-apply/scripts/db.py apply \
  --job-id "$JOB_ID" \
  --status applied \
  --applied \
  --cv-pdf "$CV_PDF" \
  --notes "Cold email to $NAME <$EMAIL>; subject: $SUBJECT; via Himalaya"
```

If he rejects the draft or contact is bad:

```bash
python3 ~/.agents/skills/job-apply/scripts/db.py apply \
  --job-id "$JOB_ID" \
  --status draft \
  --notes "Outreach held: $REASON"
```

## Pace / safety

- One email per target unless he asks for a follow-up
- Pause between sends; no bulk blasts
- No purchased lists, breach data, or fake personas
- Optional one polite follow-up after ~5–7 days only if he asks

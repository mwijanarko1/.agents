# Apply flow (channel follows the listing)

## Rule

**How you apply is determined by the job listing**, not a fixed channel.

| Listing signal | Channel | Path |
|---|---|---|
| Email / `mailto:` / “send CV to …” | `email` | Cold email via Himalaya (`outreach-flow.md`) |
| Public ATS or careers form (Greenhouse, Lever, Ashby, Workable, company site apply) | `web` | Browser form fill → **Mikhail approves** → submit |
| LinkedIn job / Easy Apply | `linkedin` | Browser Easy Apply fill → **Mikhail approves** → submit |
| Unclear / mixed | `unknown` | Re-read page; ask Mikhail which path |

**Always:** draft/fill first → show Mikhail → submit/send only after he approves (or he said “send it” / “submit it”).

Detect channel:

```bash
python3 ~/.agents/skills/job-apply/scripts/detect_apply_channel.py \
  --url "$JOB_URL" --title "…" --description "…" --source "…"
```

Search already attaches `apply_channel` on each job. Re-detect on the live page before apply if confidence is low or the listing changed.

## Shared steps (all channels)

1. Mikhail picks the target (or top N he approved).
2. Tailor CV (Step 2 in `SKILL.md`) → one-page PDF for that role.
3. Detect / confirm `apply_channel`.
4. Branch below. **Do not submit or send without approval.**
5. Log with `db.py apply --channel … --applied`.

```bash
python3 ~/.agents/skills/job-apply/scripts/db.py apply \
  --job-id "$JOB_ID" \
  --status applied \
  --applied \
  --channel web \
  --cv-pdf "$OUT/$JOB_SLUG/LATEST-CV.pdf" \
  --notes "Web apply via Greenhouse; submitted after approval"
```

Valid channels: `email` | `web` | `linkedin` | `unknown`.

## Channel: email

Full detail: `outreach-flow.md`.

- Find contacts (`contacts.md` quality bar).
- Draft cold email (plays.yaml + voice law).
- Show draft → approve → Himalaya send (`-a wijanarko`).
- Log `--channel email`.

## Channel: web

Load **`playwright-browser`** + Helium. Public ATS/careers forms only.

1. Open the apply URL from the listing (not a random company homepage).
2. Fill fields from `profile_from_cv.py` / `cv-data.json` and truth only:
   - name, email, phone, location (Sheffield, UK; open to relocate)
   - LinkedIn / portfolio / GitHub if asked and present in profile
   - work auth / notice only if known and true; otherwise leave blank and flag for Mikhail
3. Upload the **tailored** PDF for this job (`$OUT/$JOB_SLUG/LATEST-CV.pdf`).
4. Cover letter / free text: short, specific, interview-seeking; same truth rules as email (no invented experience; no dashes as punctuation). Prefer skip if optional and weak.
5. **Stop before final Submit.** Screenshot or list filled fields + URL. Wait for Mikhail.
6. On “submit it” / “approve”: click submit once. Capture confirmation text/URL if shown.
7. Log `--channel web` with notes (ATS host, confirmation).

Hard stops (do not force):

- Login wall, CAPTCHA, or multi-step SSO you cannot complete → stop, tell Mikhail, offer handoff URL.
- Required fields you cannot truthfully answer → stop and ask.
- “Are you a robot” / blocked automation → stop; Mikhail finishes manually; still log if he confirms submit.

Do **not** spray multi-page forms unattended. One target at a time.

## Channel: linkedin

Same approve gate as web.

1. Open the job URL. Prefer the listing’s apply path (Easy Apply or external).
2. If **Easy Apply**: fill from profile + attach tailored CV; stop before submit; Mikhail approves; then submit.
3. If **external apply** redirects to ATS → switch to **web** channel and log as `web`.
4. If login/CAPTCHA required → stop; Mikhail logs in or finishes; agent may resume after he confirms session is ready.
5. Log `--channel linkedin`.

Do **not**: mass Easy Apply, connection spam, or InMail automation. No inventing profile fields.

## Channel: unknown

1. Open the listing. Look for mailto, Apply button, ATS host, or email instructions.
2. Re-run `detect_apply_channel.py` with fuller description text.
3. If still unclear → ask Mikhail once: email, web, or linkedin.
4. Do not invent a path.

## What is still out of scope

- Bulk apply / spray-and-pray across boards
- Inventing emails, experience, degrees, or form answers
- Bypassing CAPTCHA or account security
- Sending or submitting without Mikhail’s approval
- CRM, delivery automation, or unattended LinkedIn messaging

## Pace

One target at a time. Short pause between applies. Prefer quality over volume.

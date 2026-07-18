---
name: job-apply
description: >
  Search public job APIs from ~/Documents/CV/cv-data.json, persist targets to
  SQLite, tailor a one-page CV via Cursor agent in ~/Documents/CV, find hiring
  contacts, and cold-outreach by email via Himalaya (not job-board or ATS form
  apply). Use when the user says job-apply, find jobs, cold outreach, email
  hiring manager, tailor my CV, find hiring manager, log application, or job
  search from my CV.
argument-hint: "[search|tailor|contacts|outreach|list|run] [query...]"
---

# Job Apply (cold outreach)

Personal **job-target + cold email** helper for Mikhail.

**Not in scope:** LinkedIn Easy Apply, Greenhouse/Lever/Ashby/Workable forms, company career-site form submit, or any job-board click-apply. Listings are **lead sources only**.

Pipeline: **search → shortlist → tailor CV → find contacts → cold email (Himalaya) → log SQLite**.

## Paths

| Path | Role |
|---|---|
| `~/Documents/CV` | CV repo |
| `~/Documents/CV/cv-data.json` | Profile |
| `~/Documents/CV/description.txt` | JD / role brief for tailor |
| `~/Documents/CV/edited.tex` | Tailored LaTeX |
| `~/Documents/CV/LATEST-CV.pdf` | Attach this (or run copy) |
| `~/Documents/CV/instructions.md` | CV rules for Cursor |
| `~/Documents/job-apply/job-apply.sqlite3` | Canonical DB |
| `~/Documents/job-apply/LOG.md` | Wiki export |
| `~/Documents/job-apply/runs/` | Run artifacts |
| `~/.agents/skills/job-apply/scripts/` | Helpers |

## Database (required)

Every search, contact lookup, tailor, and outreach attempt **must** hit SQLite.

```bash
DB=~/Documents/job-apply/job-apply.sqlite3
python3 ~/.agents/skills/job-apply/scripts/db.py init
python3 ~/.agents/skills/job-apply/scripts/db.py stats
python3 ~/.agents/skills/job-apply/scripts/db.py list jobs --limit 20
python3 ~/.agents/skills/job-apply/scripts/db.py list applications
python3 ~/.agents/skills/job-apply/scripts/db.py export-md --out ~/Documents/job-apply/LOG.md
```

Tables: `searches`, `jobs`, `search_jobs`, `contacts`, `applications`, `events`.

## Modes

| User intent | Mode |
|---|---|
| find jobs / companies | `search` |
| tailor CV | `tailor` |
| find hiring manager / email | `contacts` |
| **cold email / outreach / apply** | `outreach` (Himalaya) |
| I emailed / update status | `log` |
| pipeline / show applications | `list` |
| full job-apply | `run` = search → pick → tailor → contacts → outreach → log |

Defaults: **UK + remote**, software/mobile/AI product roles from CV.

Only outreach on jobs/companies Mikhail selected (or top N he explicitly approved on `run`).

## Step 0 — Profile

```bash
python3 ~/.agents/skills/job-apply/scripts/profile_from_cv.py --json
```

Use name/email/phone/links in outreach copy and signature.

## Step 1 — Search (lead source only)

Job APIs/boards find **roles and companies**. Do **not** open apply buttons or fill ATS forms.

```bash
mkdir -p ~/Documents/job-apply/runs
STAMP=$(date +%Y%m%d-%H%M%S)
OUT=~/Documents/job-apply/runs/$STAMP
mkdir -p "$OUT"

python3 ~/.agents/skills/job-apply/scripts/search_jobs.py \
  --query "software engineer typescript react" \
  --query "react native developer" \
  --query "graduate software engineer" \
  --location "United Kingdom" \
  --country gb \
  --terms "TypeScript,React,Next.js,React Native,Swift,Python,iOS" \
  --limit 25 \
  --out "$OUT/jobs.json" \
  --run-dir "$OUT" \
  --json
```

Present top 8–12 with `job_id`, company, title, URL (for research only). Wait for picks unless he already said “outreach top N”.

Optional: `ADZUNA_APP_ID` / `ADZUNA_APP_KEY`.

## Step 2 — Tailor CV + log

For each chosen target:

1. Write JD / role brief → `~/Documents/CV/description.txt`
2. Cursor agent:

```bash
ai-delegate --target cursor --cwd "$HOME/Documents/CV" --from-agent pi -- "$(cat <<'EOF'
Read instructions.md fully, then description.txt, cv-data.json, grades.json, and example.tex.
Create a personalised ATS-optimised one-page CV for this role/company.
Write edited.tex, run ./compile.sh, confirm LATEST-CV.pdf is one page and text-selectable.
Follow instructions.md strictly. Do not invent experience.
EOF
)"
```

Fallback: `cd ~/Documents/CV && agent --model composer-2.5 -p --force "…same…"`.

3. Copy + DB `tailored`:

```bash
JOB_ID=123
JOB_SLUG=acme-software-engineer
mkdir -p "$OUT/$JOB_SLUG"
cp ~/Documents/CV/description.txt \
   ~/Documents/CV/edited.tex \
   ~/Documents/CV/LATEST-CV.pdf \
   "$OUT/$JOB_SLUG/"

python3 ~/.agents/skills/job-apply/scripts/db.py apply \
  --job-id "$JOB_ID" \
  --status tailored \
  --cv-pdf "$OUT/$JOB_SLUG/LATEST-CV.pdf" \
  --cv-tex "$OUT/$JOB_SLUG/edited.tex" \
  --description "$OUT/$JOB_SLUG/description.txt" \
  --run-dir "$OUT/$JOB_SLUG"
```

## Step 3 — Contacts (required before outreach)

```bash
python3 ~/.agents/skills/job-apply/scripts/find_contacts.py \
  --company "Acme" --job-url "$JOB_URL" --domain "acme.com" \
  --job-id "$JOB_ID" --out "$OUT/$JOB_SLUG/contacts.json" --json
```

Rules: `references/contacts.md`. Public OSINT only (job page `mailto:`, company site, Hunter if key set, LinkedIn **search URLs** for Mikhail to open).

**Quality bar before emailing:** need a real address (official page / high-confidence Hunter / named person on the post). If none → report gap; do not invent emails; optional LinkedIn search URL for manual follow-up only.

Browser (optional research): load **`playwright-browser`** + Helium only to open public pages. **Never** use the browser to submit applications.

```text
/Applications/Helium.app/Contents/MacOS/Helium
```

```bash
node ~/.agents/skills/playwright-browser/scripts/open.mjs "$JOB_URL"
node ~/.agents/skills/playwright-browser/scripts/open.mjs --search '"Acme" ("hiring manager" OR recruiter OR "talent acquisition")'
```

Auth hard stop if a research page needs login/CAPTCHA: stop, tell Mikhail, wait — still no form apply.

## Step 4 — Cold outreach (core) — Himalaya

Load skill **`himalaya`** (`~/.pi/agent/skills/himalaya/SKILL.md`). Full shape: `references/outreach-flow.md`.

1. Pick best contact (hiring manager > recruiter > team lead > careers@ only if nothing better).
2. Draft short cold email (not “I applied on your careers page”):
   - Subject: role + company
   - 3–6 lines: who you are, why this company/role, 1 proof point from tailored CV, soft ask
   - Attach `$OUT/$JOB_SLUG/LATEST-CV.pdf`
3. **Show draft to Mikhail; send only after he approves** (or he said “send it”).
4. Send via Himalaya from his configured account only.
5. Log:

```bash
python3 ~/.agents/skills/job-apply/scripts/db.py apply \
  --job-id "$JOB_ID" \
  --status applied \
  --applied \
  --cv-pdf "$OUT/$JOB_SLUG/LATEST-CV.pdf" \
  --notes "Cold email to name <email>; subject: ...; sent via Himalaya"
```

**Pace:** one target at a time; short pause between sends. No spray-and-pray. No bulk recruiter blasts.

## Step 5 — Report

```bash
python3 ~/.agents/skills/job-apply/scripts/db.py export-md --out ~/Documents/job-apply/LOG.md
python3 ~/.agents/skills/job-apply/scripts/db.py stats
```

Write `$OUT/summary.md`: shortlist, tailored PDFs, contacts found, emails sent, gaps. Show in chat.

## Hard rules

- **Cold email only** for “apply” — no job-board / ATS / careers-form submit
- Job listings = research leads, not click-apply targets
- **Always** write searches / tailor / outreach outcomes to SQLite
- **Himalaya** for send: draft → approve → send → log
- Do not invent emails, credentials, work history, or degrees
- Do not bulk-message; one approved outreach per target unless he asks for a follow-up
- Public contact discovery only (`references/contacts.md`)

## Defaults

- Name: Mikhail Wijanarko  
- Stack: TypeScript, React, Next.js, React Native, Swift/iOS, Python, AI product  
- Geo: United Kingdom + remote  
- CV attach: latest tailored PDF for that target  

## References

- **`references/preferences.md` — Mikhail's search preferences. READ FIRST before every run.**
- `references/outreach-flow.md` — cold email via Himalaya
- `references/contacts.md` — contact research boundaries
- `references/job-apis.md`
- `references/database.md`
- Email: `~/.pi/agent/skills/himalaya`
- Optional research browser: `playwright-browser` (no form apply)

---
name: job-apply
description: >
  Search public job APIs from ~/Documents/job-apply/CV/cv-data.json, persist targets to
  SQLite, tailor a one-page CV via Cursor agent in ~/Documents/job-apply/CV, then apply
  by the listing's channel: cold email via Himalaya when the job says email, or web/ATS
  /LinkedIn form apply (playwright-browser) when it says apply online — always after
  Mikhail approves. Use when the user says job-apply, find jobs, cold outreach, email
  hiring manager, tailor my CV, find hiring manager, log application, apply online, or
  job search from my CV.
argument-hint: "[search|tailor|contacts|outreach|apply|list|run] [query...]"
---

# Job Apply (channel follows the listing)

Personal **job-target + multi-channel apply** helper for Mikhail.

**How to apply is decided by the listing:** email when it says email / mailto; web when it is ATS or careers form apply; LinkedIn when the apply path is LinkedIn. Always **fill or draft → Mikhail approves → send/submit → log**.

Pipeline: **search → shortlist → tailor CV → detect channel → (contacts if email) → draft email or fill form → approve → send/submit → log SQLite → log outcomes**.

Full apply routing: `references/apply-flow.md`. Email copy: `references/outreach-flow.md`.

Second loop (weekly): **read outcomes → propose one scoring/play change → eval gate → human merges** (`references/self-improve.md`). Sending, submitting, and merging stay outside unattended autonomy.

## Paths

| Path | Role |
|---|---|
| `~/Documents/job-apply/CV` | CV repo |
| `~/Documents/job-apply/CV/cv-data.json` | Profile |
| `~/Documents/job-apply/CV/description.txt` | JD / role brief for tailor |
| `~/Documents/job-apply/CV/edited.tex` | Tailored LaTeX |
| `~/Documents/job-apply/CV/LATEST-CV.pdf` | Attach this (or run copy) |
| `~/Documents/job-apply/CV/instructions.md` | CV rules for Cursor |
| `~/Documents/job-apply/job-apply.sqlite3` | Canonical DB |
| `~/Documents/job-apply/LOG.md` | Wiki export |
| `~/Documents/job-apply/runs/` | Run artifacts |
| `~/Documents/job-apply/AGENTS.md` | Improver law (narrow) |
| `~/Documents/job-apply/config/scoring.yaml` | Shortlist / exclude weights |
| `~/Documents/job-apply/config/plays.yaml` | Plays + banned lines by tier |
| `~/Documents/job-apply/memory/outcomes.jsonl` | Outcome memory for improver |
| `~/Documents/job-apply/evals/` | Fixtures + `score.py` gate |
| `~/Documents/job-apply/prompts/` | Improve scoring / plays prompts |
| `~/Documents/job-apply/scripts/weekly_tune.sh` | Weekly baseline export + eval |
| `~/.agents/skills/job-apply/scripts/` | Helpers |

## Database (required)

Every search, contact lookup, tailor, and apply attempt **must** hit SQLite. Every known market response **must** hit `outcome`. Log **`channel`** on apply (`email` | `web` | `linkedin`).

```bash
DB=~/Documents/job-apply/job-apply.sqlite3
python3 ~/.agents/skills/job-apply/scripts/db.py init
python3 ~/.agents/skills/job-apply/scripts/db.py stats
python3 ~/.agents/skills/job-apply/scripts/db.py list jobs --limit 20
python3 ~/.agents/skills/job-apply/scripts/db.py list applications
python3 ~/.agents/skills/job-apply/scripts/db.py list outcomes
python3 ~/.agents/skills/job-apply/scripts/db.py export-outcomes
python3 ~/.agents/skills/job-apply/scripts/db.py export-md --out ~/Documents/job-apply/LOG.md
```

Tables: `searches`, `jobs` (incl. `apply_channel`), `search_jobs`, `contacts`, `applications` (incl. `channel`), `outcomes`, `events`.

## Modes

| User intent | Mode |
|---|---|
| find jobs / companies | `search` |
| tailor CV | `tailor` |
| find hiring manager / email | `contacts` (email channel) |
| **apply / outreach / send** | `apply` — route by listing channel (`apply-flow.md`) |
| I emailed/submitted / update status / reply landed | `log` (+ `db.py outcome`) |
| pipeline / show applications | `list` |
| weekly improve scoring/plays | `tune` (`weekly_tune.sh` + improver prompts) |
| full job-apply | `run` = search → pick → tailor → channel → apply → log |

Defaults: **UK + remote**, software/mobile/AI product roles from CV.

Only apply on jobs/companies Mikhail selected (or top N he explicitly approved on `run`).

## Step 0 — Profile

```bash
python3 ~/.agents/skills/job-apply/scripts/profile_from_cv.py --json
```

Use name/email/phone/links in outreach copy, form fields, and signature.

## Step 1 — Search

Job APIs/boards find **roles, companies, and apply hints**. Each job gets `apply_channel` (`email` | `web` | `linkedin` | `unknown`).

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
  --limit 25 \
  --out "$OUT/jobs.json" \
  --run-dir "$OUT" \
  --json
```

Scores via `~/Documents/job-apply/config/scoring.yaml`. Present top 8–12 with `job_id`, company, title, URL, score/action, **and `apply_channel`**. Wait for picks unless he already said “apply top N” / “outreach top N”.

Re-detect when needed:

```bash
python3 ~/.agents/skills/job-apply/scripts/detect_apply_channel.py --url "$JOB_URL" --description "…"
```

Optional: `ADZUNA_APP_ID` / `ADZUNA_APP_KEY`.

## Step 2 — Tailor CV + log

For each chosen target:

1. Write JD / role brief → `~/Documents/job-apply/CV/description.txt`
2. Read **`references/preferences.md`** (CV tailor, employment framing, freelance list, Unisen truth) and `~/Documents/job-apply/CV/instructions.md` before generating.
3. Cursor agent:

```bash
ai-delegate --target cursor --cwd "$HOME/Documents/job-apply/CV" --from-agent pi -- "$(cat <<'EOF'
Read instructions.md fully, then ~/.agents/skills/job-apply/references/preferences.md,
description.txt, cv-data.json, grades.json, and example.tex.
Create a personalised ATS-optimised one-page CV for this role/company.
Follow preferences.md CV tailor rules (Experience Problem/Fix pattern; freelance = all site clients, no Problem/Fix; no em dashes; Unisen commit-backed only; Pi Agent primary for AI tooling).
Write edited.tex, run ./compile.sh, confirm LATEST-CV.pdf is one page and text-selectable.
Do not invent experience.
EOF
)"
```

Fallback: `cd ~/Documents/job-apply/CV && agent --model composer-2.5 -p --force "…same…"`.

4. Copy + DB `tailored`:

```bash
JOB_ID=123
JOB_SLUG=acme-software-engineer
mkdir -p "$OUT/$JOB_SLUG"
cp ~/Documents/job-apply/CV/description.txt \
   ~/Documents/job-apply/CV/edited.tex \
   ~/Documents/job-apply/CV/LATEST-CV.pdf \
   "$OUT/$JOB_SLUG/"

python3 ~/.agents/skills/job-apply/scripts/db.py apply \
  --job-id "$JOB_ID" \
  --status tailored \
  --cv-pdf "$OUT/$JOB_SLUG/LATEST-CV.pdf" \
  --cv-tex "$OUT/$JOB_SLUG/edited.tex" \
  --description "$OUT/$JOB_SLUG/description.txt" \
  --run-dir "$OUT/$JOB_SLUG"
```

## Step 3 — Route by channel

Confirm `apply_channel` from search or live page (`apply-flow.md`).

| Channel | Next |
|---|---|
| `email` | Step 3a contacts → Step 4a Himalaya |
| `web` | Step 4b form fill (no contacts required) |
| `linkedin` | Step 4c Easy Apply / external |
| `unknown` | Open listing; re-detect; ask Mikhail if still unclear |

### Step 3a — Contacts (email channel only)

```bash
python3 ~/.agents/skills/job-apply/scripts/find_contacts.py \
  --company "Acme" --job-url "$JOB_URL" --domain "acme.com" \
  --job-id "$JOB_ID" --out "$OUT/$JOB_SLUG/contacts.json" --json
```

Rules: `references/contacts.md`. Public OSINT only. Quality bar before emailing: real address required. Do not invent emails.

Browser research (optional): **`playwright-browser`** + Helium for public pages.

```text
/Applications/Helium.app/Contents/MacOS/Helium
```

Auth hard stop on login/CAPTCHA for research: stop, tell Mikhail, wait.

## Step 4 — Apply (approve gate always)

Full detail: **`references/apply-flow.md`**.

### 4a — Email (Himalaya)

Load skill **`himalaya`**. Shape: `references/outreach-flow.md`.

1. Play + contact by company size (`startup_founder` | `mid_em` | `large_recruiter`). Never CEO at big cos.
2. Research company; tailor CV already done.
3. Draft interview-seeking email. Truth only. No dashes in copy. Respect `banned_lines_global`.
4. **Show draft; send only after approve.**
5. Send via Himalaya **`wijanarko`** only (`mikhail.wijanarko2003@gmail.com`, always `-a wijanarko`).
6. Log:

```bash
python3 ~/.agents/skills/job-apply/scripts/db.py apply \
  --job-id "$JOB_ID" \
  --status applied \
  --applied \
  --channel email \
  --tier startup \
  --contact-role founder \
  --contact-email "name@acme.com" \
  --contact-name "Name" \
  --play startup_founder \
  --subject "…" \
  --cv-pdf "$OUT/$JOB_SLUG/LATEST-CV.pdf" \
  --notes "Cold email to name <email>; subject: ...; sent via Himalaya"
```

### 4b — Web / ATS form

Load **`playwright-browser`**. See `apply-flow.md` (web).

1. Open listing apply URL. Fill from profile + truth only. Upload tailored PDF.
2. **Stop before Submit.** Show filled summary / screenshot. Wait for approve.
3. On approve: submit once; note confirmation.
4. Log `--channel web`. CAPTCHA/login wall → hand off to Mikhail; log only if he confirms submit.

### 4c — LinkedIn

Same approve gate. Easy Apply fill → approve → submit; or follow external ATS as `web`. No mass Easy Apply. Log `--channel linkedin`.

### Outcomes

When the market responds (or ~7d silence after email):

```bash
python3 ~/.agents/skills/job-apply/scripts/db.py outcome \
  --job-id "$JOB_ID" \
  --outcome reply \
  --reason "asked for a call; liked RN proof"
```

**Pace:** one target at a time. No spray-and-pray. No bulk blasts.

## Step 5 — Report

```bash
python3 ~/.agents/skills/job-apply/scripts/db.py export-md --out ~/Documents/job-apply/LOG.md
python3 ~/.agents/skills/job-apply/scripts/db.py export-outcomes
python3 ~/.agents/skills/job-apply/scripts/db.py stats
```

Write `$OUT/summary.md`: shortlist, channels, tailored PDFs, emails sent, forms submitted, outcomes, gaps.

## Step 6 — Weekly tune (second loop)

Only after outcomes accumulate (~10–20 rows).

```bash
~/Documents/job-apply/scripts/weekly_tune.sh
python3 ~/Documents/job-apply/evals/score.py
```

Then **one** of `prompts/improve_scoring.md` or `prompts/improve_prompt.md`. He merges. Improver never sends or submits.

## Hard rules

- **Channel follows the listing** — email / web / linkedin per `apply-flow.md`
- **Approve before every send or form submit**
- **Always** write searches / tailor / apply / **outcomes** to SQLite with `channel` when applying
- Himalaya for email send; playwright-browser for web/LinkedIn forms
- Outcome rows need a real **reason** when known
- Do not invent emails, credentials, work history, or degrees
- Do not bulk-apply; one approved apply per target unless he asks for a follow-up
- Public contact discovery only (`contacts.md`); CAPTCHA/login → stop and hand off
- Improver: one concept; eval must pass; human merges; no auto-send/submit

## Defaults

- Name: Mikhail Wijanarko  
- Stack: TypeScript, React, Next.js, React Native, Swift/iOS, Python, AI product  
- Geo: United Kingdom + remote  
- CV attach: latest tailored PDF for that target  

## References

- **`references/preferences.md` — Mikhail's search preferences. READ FIRST before every run.**
- `references/apply-flow.md` — channel routing + web/LinkedIn apply
- `references/outreach-flow.md` — cold email via Himalaya
- `references/self-improve.md` — scoring/plays second loop
- `references/contacts.md` — contact research boundaries
- `references/job-apis.md`
- `references/database.md`
- Email: `~/.pi/agent/skills/himalaya`
- Browser: `playwright-browser` (form apply only after approval)

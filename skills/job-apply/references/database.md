# job-apply SQLite

**Path:** `~/Documents/job-apply/job-apply.sqlite3`

## Tables

| Table | Purpose |
|---|---|
| `searches` | Each search run (queries, sources, run_dir) |
| `jobs` | Deduped jobs by fingerprint(title\|company); optional `apply_channel` |
| `search_jobs` | Which jobs appeared in which search + score |
| `contacts` | Public contact research per company/job |
| `applications` | Tailor / apply state (1:1 with job) + `channel` + play/tier/latest outcome |
| `outcomes` | Append-only market outcomes (sent, reply, no_reply, interview, …) |
| `events` | Append-only audit log |

## Job / application status

Jobs: `found` → `shortlisted` → `tailored` → `applied` → `interview` / `offer` / `rejected` / `skipped`

Applications: `draft` | `tailored` | `applied` | `rejected` | `interview` | `offer` | `withdrawn`

## Outcomes (second-loop memory)

Valid `outcome` values: `sent` | `no_reply` | `reply` | `bounce` | `bad_fit` | `interview` | `offer` | `rejected` | `withdrawn` | `held`

**Always set `reason`** when the outcome lands. `no_reply` alone teaches little; a real reason trains the improver.

Mirror file: `~/Documents/job-apply/memory/outcomes.jsonl` (rewritten by `export-outcomes`; appended on each `outcome` / applied send).

## CLI

```bash
python3 ~/.agents/skills/job-apply/scripts/db.py init
python3 ~/.agents/skills/job-apply/scripts/db.py stats
python3 ~/.agents/skills/job-apply/scripts/db.py list jobs
python3 ~/.agents/skills/job-apply/scripts/db.py list applications --status applied
python3 ~/.agents/skills/job-apply/scripts/db.py list outcomes

# Tailor / send or form submit (always set --channel)
python3 ~/.agents/skills/job-apply/scripts/db.py apply \
  --job-id 1 --status applied --applied \
  --channel email \
  --tier startup --contact-role founder --contact-email a@b.com \
  --play startup_founder --subject "…" \
  --notes "Cold email to …; via Himalaya"

# Web example
python3 ~/.agents/skills/job-apply/scripts/db.py apply \
  --job-id 2 --status applied --applied \
  --channel web \
  --notes "Greenhouse submit after approval"

# Later: market response (required reason)
python3 ~/.agents/skills/job-apply/scripts/db.py outcome \
  --job-id 1 --outcome reply \
  --reason "asked for portfolio link; interested in RN"

python3 ~/.agents/skills/job-apply/scripts/db.py export-outcomes
python3 ~/.agents/skills/job-apply/scripts/db.py export-md --out ~/Documents/job-apply/LOG.md
```

## Auto-write

- `search_jobs.py` → `record_search` (unless `--no-db`); scores via `config/scoring.yaml`
- `find_contacts.py` → `record_contacts` (unless `--no-db`)
- Tailor / apply → `db.py apply` (agent must run; applied auto-logs `outcome=sent`)
- Replies / ghosts → `db.py outcome` when known

## Wiki export

`export-md` regenerates `~/Documents/job-apply/LOG.md` from SQLite. SQLite is source of truth; markdown is a readable mirror.

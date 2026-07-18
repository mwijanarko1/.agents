# job-apply SQLite

**Path:** `~/Documents/job-apply/job-apply.sqlite3`

## Tables

| Table | Purpose |
|---|---|
| `searches` | Each search run (queries, sources, run_dir) |
| `jobs` | Deduped jobs by fingerprint(title\|company) |
| `search_jobs` | Which jobs appeared in which search + score |
| `contacts` | Public contact research per company/job |
| `applications` | Tailor / apply pipeline state (1:1 with job) |
| `events` | Append-only audit log |

## Job / application status

Jobs: `found` → `shortlisted` → `tailored` → `applied` → `interview` / `offer` / `rejected` / `skipped`

Applications: `draft` | `tailored` | `applied` | `rejected` | `interview` | `offer` | `withdrawn`

## CLI

```bash
python3 ~/.agents/skills/job-apply/scripts/db.py init
python3 ~/.agents/skills/job-apply/scripts/db.py stats
python3 ~/.agents/skills/job-apply/scripts/db.py list jobs
python3 ~/.agents/skills/job-apply/scripts/db.py list applications --status applied
python3 ~/.agents/skills/job-apply/scripts/db.py apply --job-id 1 --status applied --applied
python3 ~/.agents/skills/job-apply/scripts/db.py export-md --out ~/Documents/job-apply/LOG.md
```

## Auto-write

- `search_jobs.py` → `record_search` (unless `--no-db`)
- `find_contacts.py` → `record_contacts` (unless `--no-db`)
- Tailor / apply steps → `db.py apply` (agent must run this)

## Wiki export

`export-md` regenerates `~/Documents/job-apply/LOG.md` from SQLite. SQLite is source of truth; markdown is a readable mirror.

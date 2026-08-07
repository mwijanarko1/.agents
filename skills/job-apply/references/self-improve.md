# Self-improving outbound (second loop)

Inspired by versioned GTM / cheap-metric agent loops: reply and interview rates are evaluable; scoring and plays are files; humans merge and send.

## Layout (`~/Documents/job-apply`)

| Path | Role |
|---|---|
| `AGENTS.md` | Narrow law for the improver |
| `config/scoring.yaml` | Shortlist / exclude weights + thresholds |
| `config/plays.yaml` | Plays, banned lines, contact priority by tier |
| `memory/outcomes.jsonl` | One JSON line per outcome (from SQLite) |
| `evals/fixtures.yaml` | Ugly cases the gate must catch |
| `evals/score.py` | One command → pass rate |
| `prompts/improve_scoring.md` | Improver prompt (scoring only) |
| `prompts/improve_prompt.md` | Improver prompt (plays only) |
| `scripts/weekly_tune.sh` | Export + baseline eval; no auto-merge |

## Loop 1 (run) — existing pipeline

search → shortlist → tailor → contacts → draft → **Mikhail approves** → Himalaya send → log `applied` + `outcome=sent` → when known, log reply / no_reply / interview with **reason**.

## Loop 2 (improve) — weekly

1. `~/Documents/job-apply/scripts/weekly_tune.sh`
2. Agent follows `prompts/improve_scoring.md` **or** `improve_prompt.md` (not both)
3. One concept diff; `python3 evals/score.py` must pass
4. Show evidence + diff; **Mikhail merges**
5. Never auto-send from the improver

Skip improver until ~10–20 real outcome rows exist.

## Rules

- Write the outcome row when it lands (not Friday memory)
- One concept per proposal
- Eval gate rejects “sounds reasonable” overfitting
- Preferences.md + outreach-flow.md remain human law; YAML is tunable knobs

# Job APIs used by job-apply

## Free search APIs (wired in `scripts/search_jobs.py`)

| Source | Auth | Endpoint idea |
|---|---|---|
| RemoteOK | none | `GET https://remoteok.com/api` |
| Remotive | none | `GET https://remotive.com/api/remote-jobs?search=` |
| Jobicy | none | `GET https://jobicy.com/api/v2/remote-jobs?tag=` |
| Arbeitnow | none | `GET https://www.arbeitnow.com/api/job-board-api?search=` |
| The Muse | none | `GET https://www.themuse.com/api/public/jobs?q=` |
| Adzuna | `ADZUNA_APP_ID` + `ADZUNA_APP_KEY` | `https://api.adzuna.com/v1/api/jobs/{country}/search/1` |

Register Adzuna: https://developer.adzuna.com/

## Optional later (not wired)

- Reed (UK): https://www.reed.co.uk/developers — API key
- Jooble: https://jooble.org/api/about — API key
- USAJobs: https://developer.usajobs.gov/ — US federal

## Company ATS public boards (per company slug)

Useful when shortlist company is known:

```text
Greenhouse: https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true
Lever:      https://api.lever.co/v0/postings/{slug}?mode=json
Ashby:      https://api.ashbyhq.com/posting-api/job-board/{name}
```

These list that company's open roles only — not a global search.

## Apply channel (not an API)

Search attaches `apply_channel` via `detect_apply_channel.py` (URL host + listing text). Apply itself is email (Himalaya) or browser form (`apply-flow.md`), not a LinkedIn/Indeed public apply API.

## Not available as public APIs

- LinkedIn jobseeker search/apply API
- Indeed public jobseeker API

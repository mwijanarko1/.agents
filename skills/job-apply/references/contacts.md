# Contact research boundaries

## Allowed

- Parse public job page HTML for `mailto:` and public LinkedIn URLs
- Company careers / team / about pages
- Hunter.io domain search with user's own `HUNTER_API_KEY`
- Build LinkedIn **search URLs** for the user to open manually
- Public Google / Bing web results
- Optional Helium open of **public** pages for research only

## Not allowed

- Logged-in LinkedIn scraping or LinkedIn messaging automation (apply path is separate; see `apply-flow.md`)
- Buying email lists / breach data
- Mass cold email
- Inventing or guessing personal emails without a source
- Submitting forms **without** Mikhail’s approval (web/LinkedIn apply is allowed only via `apply-flow.md` approve gate)

## Quality bar before outreach

Only send email if at least one of:

1. Email found on official company/job page, or
2. Hunter confidence ≥ 80 with a title that matches the **size-tier contact priority** in `outreach-flow.md`, or
3. Named person + email on the job post

Otherwise: no send. Report what was found; give LinkedIn search queries as optional manual next step.

## Who to look for (size-aware)

Infer tier quickly from public signals (about page, LinkedIn company size, funding news, household name). When unsure, default **mid** — never default to CEO.

| Tier | Target titles (in order) | Skip |
|---|---|---|
| Startup (<~50) | Founder, CTO, Head of Eng, EM | Random IC with no hiring signal |
| Mid (~50–500) | EM / hiring manager for team, domain lead, recruiter | CEO / founder cold email |
| Large (500+) | Named HM/EM on post, recruiter on post | CEO, founder, group CTO, exec assistants |

## Suggested LinkedIn search (manual)

Startup:
```text
"{Company}" (founder OR CTO OR "head of engineering" OR "engineering manager")
```

Mid / large:
```text
"{Company}" ("engineering manager" OR "hiring manager" OR recruiter OR "talent acquisition") {Role keywords}
```

Build a search URL; Mikhail opens/sends himself if he wants LinkedIn. Agent does not auto-message on LinkedIn.

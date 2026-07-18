# Contact research boundaries

## Allowed

- Parse public job page HTML for `mailto:` and public LinkedIn URLs
- Company careers / team / about pages
- Hunter.io domain search with user's own `HUNTER_API_KEY`
- Build LinkedIn **search URLs** for the user to open manually
- Public Google / Bing web results
- Optional Helium open of **public** pages for research only

## Not allowed

- Logged-in LinkedIn scraping or LinkedIn messaging automation
- Buying email lists / breach data
- Mass cold email
- Inventing or guessing personal emails without a source
- Submitting job-board / ATS / careers **forms** (this skill is cold outreach only)

## Quality bar before outreach

Only send email if at least one of:

1. Email found on official company/job page, or
2. Hunter confidence ≥ 80 with a recruiting/people/engineering-manager title, or
3. Named person + email on the job post

Otherwise: no send. Report what was found; give LinkedIn search queries as optional manual next step.

## Suggested LinkedIn search (manual)

```text
"{Company}" ("hiring" OR recruiter OR "talent acquisition" OR "engineering manager") {Role keywords}
```

Build a search URL; Mikhail opens/sends himself if he wants LinkedIn. Agent does not auto-message on LinkedIn.

# Job search preferences — Mikhail

Read before every search / shortlist / tailor / outreach run. Overrides any default in
the skill when they conflict.

## Seniority

**Graduate / entry-level / junior only.** No senior, staff, principal, lead, or
director roles. Skip any posting requiring 3+ years commercial experience unless
it explicitly welcomes recent grads / career-changers.

Tunable machine weights live in `~/Documents/job-apply/config/scoring.yaml`
(human law here still wins on conflicts).

## Location

- **Based:** Sheffield, UK (not London).
- **Relocation:** happy to relocate **anywhere** for the right role (UK first, then Europe / Australia / NZ / Middle East per region list). Always state Sheffield base + open to relocate; never claim already living in the job city.
- CV header location: **Sheffield, UK** (optionally "open to relocate"). Never put the job city as home base.

## Regions (priority order)

1. **United Kingdom** (primary; UK-based or UK-remote)
2. **Europe** (EU + non-EU; remote or on-site)
3. **Australia**
4. **New Zealand**
5. **Middle East** (UAE / Saudi / Qatar / etc.)

Exclude: USA, Canada, Latin America, South Asia (Pakistan/India/Bangladesh),
Africa — unless the role is explicitly remote-worldwide with a workable timezone.

## Role clusters (CV-fit)

Priority (stack is a direct match):

- **Software engineering**: graduate/junior SWE, frontend, full stack, React/Next.js/TypeScript
- **Mobile**: React Native, iOS/SwiftUI, Expo
- **AI product**: AI product engineer, AI-native engineer, applied AI, prompt/LLM roles
- **Founding / startup**: founding engineer, founder's associate (product-minded) when truthful evidence fits
- **Product**: associate/graduate product manager, product analyst
- **DevRel**: developer advocate, developer relations (junior/associate)
- **Solutions/pre-sales**: graduate/junior solutions engineer, pre-sales, technical account
- **Aerospace** (MEng background): graduate aerospace/systems/avionics engineer — **civilian only**

Secondary (stretch, case-by-case):

- Technical consultant, implementation engineer, technical writer
- Business/technical analyst, systems analyst
- Project/delivery coordinator (technical)

## Hard excludes

- **UK defence / defence primes** (BAE, Boeing Defence, Lockheed, Thales defence, MoD, QinetiQ, MBDA, etc.) — do not shortlist or outreach.
- Broader defence contractors and military/weapons roles in any region unless Mikhail explicitly asks.

## Stack

TypeScript, JavaScript, React, Next.js, TanStack Start, React Native, Expo, Swift,
SwiftUI, iOS, Python, SQL, Convex, Clerk, Cloudflare Workers, Firebase, MCP,
Node.js, Vitest, Playwright, AI product / agents / LLM tooling. Also Go/Rust when
truthful for a role.

## Employment framing (truth)

- **Job seeking now.** Lead with what you built, not employment status.
- **Unisen** = **current** Founding Engineer (July 2026 – Present). Site: https://unisen.uk. Repo: `senco-flow`.
- **Pivot2Tech** = **past** Software Engineer Intern (Dec 2025 – 2026). Never "I am an intern at…", "currently at Pivot2Tech", or "internship ended / unemployed".
- **Freelance** = client products 2025–2026 (see CV freelance list below).
- Do **not** invent company-founder claims, degrees, emails, fundraising for Unisen, or experience you did not do.
- Do **not** default to society President / fundraising bullets unless Mikhail asks or the role clearly needs that evidence.

### Unisen truth (commit-backed only)

Mikhail's Unisen work is **landing, Convex enquiry/snapshot backend, Cloudflare deploy, app-host Clerk auth polish**. Do **not** claim Lovable/bot product UI or Hanad's product commits as his.

Strong commit themes to draw from (check `git log --author=Mikhail` in senco-flow when writing bullets):

- Landing + brand (TanStack Start / React / TypeScript)
- Convex auth-scoped snapshots; Turnstile-verified enquiries + Resend + idempotency / honeypot
- Cloudflare Worker deploy; host routing `unisen.uk` / `www` / `app.unisen.uk`
- Faster Clerk sign-in, Get started redirect, app-host chrome
- SEO: OG/Twitter, Schema.org JSON-LD, robots.txt / sitemap.xml / llms.txt, noindex on app routes

### Coding workflow (when mentioning AI tools)

- **Primary:** Pi Agent
- Also: Cursor CLI, Devin CLI
- Models often used: GPT 5.6 Sol, Fable 5, Grok 4.5
- Do **not** lead with Claude Code as the primary daily driver (it may appear as a supported target in AI Bridge, not as "I mostly use Claude Code").

## CV tailor (hard rules)

Also enforced in `~/Documents/job-apply/CV/instructions.md`. Prefer these over generic ATS fluff.

### Form

- Exactly **one page**. Compile with `./compile.sh`. Text-selectable PDF.
- No Summary / profile section.
- Section order for eng roles: Contact → Education → Experience → Projects → Skills.
- **No em dashes** anywhere in CV copy (no `---`, no Unicode `—` / `–` as punctuation). Date ranges may use LaTeX `--`. Use periods, commas, colons, parentheses.
- British spelling for UK roles.
- Natural language over JD keyword stuffing. Reject AI-sounding fluff ("force multiplier", "hand-holding", "messy high-stakes", empty "passionate about"). Mirror JD terms only when truthful and natural.
- Bold key tech in bullets. Show, don't tell: problem → fix → impact with real numbers when available.
- Prefer commit / `gh` / site evidence over invented metrics.

### Experience bullet pattern (Unisen, Pivot2Tech, similar roles)

Exactly **three** bullets per role:

1. **What it is + tech stack** (plain English a stranger understands)
2. **`Problem:` … `Fix:` …** (one concrete problem + what you did + impact)
3. **`Problem:` … `Fix:` …** (second concrete problem)

Label **Problem:** and **Fix:** explicitly so the split is obvious. Write for a reader who has never seen the repo: no insider jargon without a one-clause gloss.

### Freelance (exception)

When including freelance, **list every freelance item from** https://www.mikhailwijanarko.xyz/ (Freelance Work section). Do **not** use the Problem/Fix pattern for freelance.

Canonical freelance list (keep in sync with the site):

1. **BackFire** — https://playbackfire.com — Expo / React Native / Clerk / Convex
2. **Design with Samah Portfolio** — https://designwithsamah.com — Next.js / TypeScript
3. **Indonesian Cafe Sheffield Website** — https://www.indonesiancafe.co.uk — Next.js / TypeScript
4. **MWHS Website** — https://mwhs.org.uk — Next.js / Firebase
5. **USIC Sheffield Website** — https://usicsheffield.com — Next.js / Firebase (incl. ~75% image-request cut when space allows)

One short bullet per client (name + link + stack + what shipped). Compress wording to stay one page; do not drop a client without Mikhail saying so.

### Projects bullet pattern

Same three-point shape as Experience (what + stack; then two Problem/Fix). Prefer Authority/AI-fit projects when relevant: **AI Bridge**, **Nusus**, open-source contributions, shipped apps.

**Nusus wording:** say classical Arabic source texts / research retrieval. Do **not** lead with "Turath" unless the JD names it.

**Open source (from site):** when including OSS instead of (or with) apps:

- pi-subagents: Completion Guard Fix — https://github.com/nicobailon/pi-subagents/pull/539
- fff: pi-fff Dependency Pinning — https://github.com/dmtrKovalenko/fff/pull/712

### Proof style

- Show a **builder portfolio**, not a single-project monologue. Do **not** default to "I built PromptPal…" as the whole pitch.
- Spread proof across Unisen, shipped apps, freelance sites, AI tooling (AI Bridge, Nusus, MCP), App Store downloads, open source.
- Pick 2–4 relevant hits for the role.

### Sources of truth (in order)

1. `~/Documents/job-apply/CV/cv-data.json`
2. https://www.mikhailwijanarko.xyz/ (freelance / projects / npm / OSS inventory)
3. Repo commits / `gh` PRs for problem–fix evidence (especially Unisen `senco-flow`)
4. `grades.json` for education modules when relevant

## Data sources

- Free job APIs via `search_jobs.py` — thin UK coverage, lead source only.
- **Web search** for real current openings across the regions above.
- Mikhail may paste specific job URLs → handle tailor + contacts + outreach per target.

## Apply rules (channel follows the listing)

- **Route by the listing:** email / mailto → Himalaya; apply online / ATS / careers form → web form; LinkedIn Easy Apply → linkedin. See `apply-flow.md`.
- **Approve gate always:** draft email or fill form → Mikhail approves → then send or submit. Never unattended submit.
- **Email path:** goal is get an interview. No mandatory template. Research first. Plays in `~/Documents/job-apply/config/plays.yaml`; voice in `outreach-flow.md`. Send only via Himalaya **`wijanarko`** (`mikhail.wijanarko2003@gmail.com`, always `-a wijanarko`).
- **Web / LinkedIn path:** playwright-browser + Helium; truth-only form fields; tailored PDF upload; stop before Submit; CAPTCHA/login → hand off.
- **Location line:** Sheffield based, happy to relocate (to their city / anywhere as fits). Never "I am based in London" unless true.
- Truth only. Tailor CV to the JD before every apply. Attach/upload that PDF.
- Log to SQLite with `--channel email|web|linkedin` (`apply` + structured `outcome` when known).
- One target at a time; no spray-and-pray or bulk Easy Apply.
- Public OSINT only for contacts; never invent emails or form answers.
- **No dashes in outreach emails** (em, en, or hyphen as punctuation). Commas, periods, colons, parentheses only.
- **Contact by company size** (email channel; `outreach-flow.md` + plays.yaml): startup → founder/CTO/EM; mid → EM/hiring manager; large → named HM/recruiter on the post only. Never cold-email CEOs at big companies.
- **Outcomes:** when a reply, ghost (~7d), bounce, interview, or reject lands, run `db.py outcome` with a real `reason`. Feeds the weekly improver (`references/self-improve.md`).

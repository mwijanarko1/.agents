---
name: pagespeed
description: Run Google PageSpeed Insights (lab + CrUX field data) for a URL via the official API. Use when the user asks for PageSpeed, PSI, Core Web Vitals, LCP/INP/CLS, or performance score for a site.
---

# PageSpeed

## Secret handling (mandatory)

- API key: `~/.config/pagespeed/api_key` (`chmod 600`) or env `PAGESPEED_API_KEY`.
- **Never** read, cat, printenv, open, or log the key.
- **Never** put the key in chat, commits, or hand-written curl.
- Only run the wrapper below (injects key, prints scores only).

Exit 2 = missing key → tell user to fill `~/.config/pagespeed/api_key`. Do not ask them to paste the key in chat.

## Run

```bash
~/.agents/skills/pagespeed/scripts/psi.sh <url> [mobile|desktop|both] [categories]
```

| Arg | Default |
|---|---|
| strategy | `both` |
| categories | `performance,accessibility,best-practices,seo` |

```bash
~/.agents/skills/pagespeed/scripts/psi.sh https://example.com
~/.agents/skills/pagespeed/scripts/psi.sh https://example.com mobile
~/.agents/skills/pagespeed/scripts/psi.sh https://example.com both performance
```

## Report

From script JSON only — compact table:

- Scores: Performance / Accessibility / Best Practices / SEO (0–100)
- Lab: FCP, LCP, TBT, CLS, SI (TTI if useful)
- Field / origin CrUX when present

No full Lighthouse dump unless asked. Lab scores jitter run-to-run — say so if comparing runs.

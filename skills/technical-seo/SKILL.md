---
name: technical-seo
description: Audit and improve technical SEO and LLM-readable surfaces.
---

# Technical SEO

Audit/build for crawlability, indexation, and machine-readable surfaces.

## Workflow

1. Inventory primary templates (home, listing, detail, docs, app shells).
2. Check crawl/index gates below.
3. Fix highest-impact blockers first (blocked canonicals, noindex mistakes, orphan pages).
4. Verify with source HTML + robots/sitemap, not only the rendered marketing claim.

## Crawl & index

- Important pages linked from nav/home; shallow click depth.
- Clean URLs; XML sitemap of canonical indexable URLs only.
- `robots.txt` blocks only low-value surfaces (admin, cart, internal search) — never core content by accident.
- One host/scheme via 301; self-canonicals; parameter variants canonicalized.

## Structure & duplicates

- Logical hierarchy + breadcrumbs where they help.
- Descriptive anchors; no long redirect chains.
- Pagination: consistent URLs; canonical per page (not always page 1) unless product dictates otherwise.

## On-page & metadata

- Unique title/meta description per indexable template.
- One H1; heading order reflects structure.
- Indexable content in HTML (not only client-only empty shells for key pages).
- `noindex` only for truly non-indexable surfaces.

## LLM / machine surfaces

- Accurate `llms.txt` / docs entry points when the product ships them.
- Public API/docs stable and linked; avoid cloaking different content to bots vs users.

## Rich results (when relevant)

- Valid JSON-LD matching visible content; no fake reviews/prices.

## Output

```
[critical|major|minor] issue — url/template
  fix
```

Not a substitute for `website-compliance` (privacy/legal) or content strategy.

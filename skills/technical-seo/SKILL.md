---
name: technical-seo
description: Audit and fix crawlability, indexation, rendering, performance, and machine-readable site infrastructure. Use for robots.txt, sitemaps, canonicals, redirects, metadata, source HTML, Core Web Vitals, hreflang, or schema validation. Different from ai-search-optimization because it owns crawl/index infrastructure rather than content retrieval and answer extractability.
---

# Technical SEO

Audit and, when implementation access exists, fix the technical foundations that let search engines crawl, render, and index a site.

## When to use

- Pages are not indexed, are dropping from the index, or show coverage problems.
- A migration, redesign, URL change, or framework change may have introduced SEO regressions.
- JavaScript rendering, crawl traps, Core Web Vitals, or crawl-budget issues affect important pages.

## Inputs

- A website URL, repository, or both; use the repository when checking implementation details.
- Optional: representative URLs by template and Google Search Console data (Indexing, Sitemaps, and Core Web Vitals).
- If a dependency-specific performance audit is needed, use `pagespeed` rather than duplicating its workflow.

## Workflow

1. Inventory representative templates and URLs: home, listing, detail, docs, search, pagination, and app shells.
2. Audit the checks below, separating site-wide, template-wide, and URL-specific findings.
3. Fix or recommend the highest-impact crawl/index blockers first; batch fixes by template.
4. Verify with fetched response headers, source HTML, rendered output when needed, `robots.txt`, and XML sitemaps—not only the rendered marketing claim.
5. After deployment, re-crawl and re-check Search Console when access is available.

## Crawlability and indexation

- Important canonical pages are reachable from navigation or contextual internal links with shallow click depth; identify orphan pages and crawl traps.
- `robots.txt` blocks only low-value surfaces (admin, cart, internal search, and unsafe parameter spaces), never core content, canonicals, or XML sitemaps by accident.
- XML sitemaps contain only canonical, indexable, successful URLs; check freshness, scope, and sitemap references in `robots.txt`.
- `noindex` is reserved for genuinely non-indexable surfaces. Check `noindex` versus `robots.txt` conflicts and canonical/noindex contradictions.
- Clean, stable URLs; parameter and duplicate variants have an intentional canonical/indexing policy.
- Important content and links are present in crawlable HTML or reliably rendered output, not only in an empty client-side shell.

## Architecture and duplicates

- One preferred HTTPS host and URL scheme; enforce alternatives with direct 301/308 redirects and avoid chains or loops.
- Self-canonicals on indexable pages; canonical targets are reachable, equivalent, and indexable.
- Logical URL hierarchy, descriptive anchors, and breadcrumbs where they improve discovery and context.
- Pagination uses consistent discoverable URLs and a deliberate canonical policy; do not canonicalize every page to page one by default.
- Hreflang, when used, is reciprocal, self-referencing, correctly localized, and points to canonical equivalents.

## On-page and rendering

- Each indexable template has a unique, useful title and meta description; one H1 and a coherent heading hierarchy.
- Server-rendered or prerendered metadata, primary content, links, and structured data are available to crawlers where required.
- Check status codes, soft 404s, redirects, blocked assets, hydration failures, and JS-dependent navigation/content.
- HTTPS is consistent and mixed content does not prevent rendering or interaction.

## Performance

- Check Core Web Vitals (LCP, INP, CLS) for important templates when data is available, and trace each failure to a direct cause such as render-blocking resources, oversized media, long tasks, or layout shifts.
- Treat performance as a technical SEO finding only when it affects crawl/rendering or meaningful user experience; do not substitute a generic performance score for evidence.

## Structured data and machine surfaces

- Valid JSON-LD uses the appropriate entity type, matches visible content, and does not invent reviews, prices, availability, or other claims.
- `llms.txt` and documentation entry points are accurate when the product ships them; public API/docs URLs are stable and linked.
- Do not serve materially different content to crawlers and users (cloaking).

## Output

Return a ranked technical backlog. Use one area per finding: `Crawl`, `Index`, `Architecture`, `Rendering`, `Performance`, `Structured data`, or `Hygiene`. For each finding:

```
[critical|major|minor] issue — area — url/template
  evidence: what was observed
  impact: why it matters
  fix: exact change, with a snippet where useful
  verify: how to confirm the fix
```

Prioritize crawl and index blockers, then architecture/rendering, then performance and enhancements. Distinguish observed evidence from assumptions. This skill is not a substitute for `website-compliance` (privacy/legal) or `ai-search-optimization` (content retrieval and answer extractability).

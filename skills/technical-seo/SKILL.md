---
name: technical-seo
description: "Audit and improve technical SEO and LLM-readable surfaces."
---

# Technical SEO

Concise, implementable technical SEO guidance. Apply when building or auditing sites for search visibility.

## 1. Crawlability and indexation

- Link main pages from homepage and navigation (no orphan pages)
- Keep click depth shallow: important pages within 3 clicks of homepage
- Clean URL structure: lowercase, hyphens, no long query strings (e.g. `/blog/technical-seo-guide`)
- Generate XML sitemap with only canonical, indexable URLs; submit in Google Search Console (Indexing → Sitemaps)
- Maintain `robots.txt` blocking only low-value areas (login, internal search/filter URLs, staging)
- Avoid blocking core sections with `Disallow` or `noindex`

Example `robots.txt`:

```txt
User-agent: *
Disallow: /wp-admin/
Disallow: /cart/
Disallow: /checkout/
Disallow: /search?
Sitemap: https://example.com/sitemap.xml
```

## 2. Site structure and internal linking

- Group content into clear categories and subcategories (e.g. `/blog/seo/technical-seo-guide`)
- Use descriptive navigation labels and breadcrumb trails: `Home > Blog > SEO > Technical SEO`
- Every important page should have internal links from relevant content; use descriptive anchor text, not "click here"
- Fix broken internal links; avoid long redirect chains (301 → 301 → 301)

Example hierarchy:

- `/`
- `/blog/`
- `/blog/seo/`
- `/blog/seo/technical-seo-guide/`

## 3. Canonicals, duplicates, and parameters

- Use canonical tags on each page pointing to its preferred URL (self-referencing for most pages)
- For variants (tracking params, filtered listings), canonicalize to the main version when content is substantially similar
- Redirect all traffic to a single canonical host (HTTP→HTTPS, www/non-www) with 301s
- For pagination: consistent URL patterns (`/category/page/2/`) and canonical to each specific page, not always page 1

## 4. Performance and Core Web Vitals

- Optimize images: compression, WebP/AVIF, responsive sizes, lazy loading below the fold
- Minimize render-blocking JS/CSS; ship only necessary scripts; defer non-critical JS
- Use HTTP/2 or HTTP/3, enable GZIP/Brotli, leverage browser caching
- Use a CDN for static assets
- Monitor Core Web Vitals (LCP, CLS, INP) in Search Console and performance tooling

## 5. Mobile and security

- Responsive design: same HTML adapts to all screen sizes
- Mobile navigation should expose the same important links as desktop
- Avoid intrusive interstitials/popups that block content on mobile
- Serve all pages over HTTPS with valid TLS; redirect HTTP → HTTPS

## 6. Metadata and HTML semantics

- Unique, descriptive `<title>` on every indexable page, ideally including the primary topic
- One clear `<h1>` per page that matches or supports the title; logical `<h2>`, `<h3>` structure
- Meta descriptions that accurately summarize content and encourage clicks
- Descriptive `alt` attributes on meaningful images (no keyword stuffing)

## 7. Structured data (schema)

- Implement JSON-LD schema for key page types: Article, Product, FAQ, LocalBusiness
- Keep schema consistent with on-page content (no fake reviews, misleading prices)
- Test and validate with Google Rich Results Test; fix warnings or errors

Minimal Article schema:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Technical SEO Guide",
  "author": { "@type": "Person", "name": "Your Name" },
  "datePublished": "2026-03-08",
  "mainEntityOfPage": "https://example.com/blog/technical-seo-guide"
}
</script>
```

## 8. Log files, monitoring, and tooling

- Use server logs (or log analyzers) to see how bots crawl sections and spot waste (e.g. faceted URLs)
- Run periodic technical audits with an SEO crawler: broken links, 4xx/5xx, redirect chains, missing titles, canonical conflicts
- Track organic performance and index coverage in Google Search Console; fix coverage and enhancement issues

## 9. Prioritization checklist

Work in this order:

1. Crawlability and indexation (robots, sitemaps, major 4xx/5xx, canonical host)
2. Site structure, navigation, and internal linking for key pages
3. Performance and Core Web Vitals on important templates
4. Canonicals, duplicates, HTTP/HTTPS, and parameters
5. Metadata, headings, structured data on high-value pages first
6. Monitoring: crawls, logs, and Search Console reviews on a schedule

## Stack-specific implementation

When the user shares their stack (Next.js, WordPress, custom Node, etc.) and site type (blog, SaaS, ecommerce), turn this into a concrete implementation checklist tailored to that setup.

## 10. Safe LLM-readable surface (`/llms.txt` and Markdown companions)

Use this when adding a machine-readable publishing layer without cloaking.

### Objective

Add a small, explicit machine-readable surface that:

- Keeps canonical HTML pages as the primary user-facing and indexable pages
- Publishes clean text or Markdown companions for important public routes
- Exposes a root `/llms.txt` discovery document
- Avoids crawler-specific content substitution

### Non-negotiables

- Do not use cloaking, bot fingerprinting, hidden instructions, or crawler-specific branching
- Do not detect bots and serve them different content
- Machine-readable pages must preserve the same meaning as human-facing pages
- Do not let companion pages compete with canonical pages in search
- Do not fork content ownership into separate manual copies unless unavoidable

### Discovery and URL pattern

- Add `/llms.txt` at the site root
- Add one machine-readable companion for each selected important public page
- Use stable, explicit URLs such as `/llms/home.md`, `/llms/about.md`, `/llms/pricing.md`
- Link to `/llms.txt` in a public low-prominence location such as the footer
- Keep companion pages crawlable and publicly discoverable
- Keep companion pages out of the primary sitemap when they are `noindex`

### Content ownership model

- Inventory highest-value public routes first
- Identify which routes are static vs CMS/database-backed
- Reuse existing server-side content loaders and shared constants
- Move repeated page copy into shared constants where practical
- Centralize legal/policy text in one structured source of truth
- Filter hidden or unavailable content exactly as the canonical site does
- Use one descriptor table listing every machine-readable document

### Route behavior and headers

- `/llms.txt` should return `Content-Type: text/plain; charset=utf-8`
- Companion `.md` pages should return `Content-Type: text/markdown; charset=utf-8`
- Companion `.md` pages should return `X-Robots-Tag: noindex, follow`
- Keep static machine-readable routes static where possible
- Use dynamic rendering only where companion content depends on live data
- Keep formatting ownership in a shared generator layer; keep headers in route handlers

### Markdown content rules

For every companion document:

- Start with exactly one `#` heading
- Include the canonical page URL near the top
- Use plain factual prose
- Preserve stable section order
- Include essential links back to canonical pages
- Keep output small and easy to parse

Avoid:

- Model-targeted instructions
- Marketing claims not present on the canonical page
- Alternate claims or hidden content not visible on the site

### Suggested companion page coverage

Home page:

- Site name
- One-line summary
- Address and opening hours where relevant
- Key public links
- Short summaries of core sections (menu, reviews, contact, etc.)

Product/service pages:

- Short intro
- Key features/services
- Public pricing where available
- Important disclaimers
- Related canonical links

Menu/catalog pages:

- Category headings
- Visible items only
- Prices and short descriptions
- Availability filtering aligned with the canonical page

Reviews/testimonials:

- Featured review list where applicable
- Full review text only if already publicly visible
- Canonical links back to review page/platform profile

Privacy/terms:

- Generate from a structured legal source, not separate hand-maintained copies

### SEO and crawl safety for companion surfaces

- Keep canonical HTML pages `index, follow`
- Keep companion pages `noindex, follow`
- Confirm `robots.txt` does not block companion routes
- Keep Googlebot and other allowed crawlers able to fetch both canonical and companion URLs
- Keep important metadata, canonicals, and structured data early in canonical HTML
- Keep canonical HTML lean; avoid large inline base64 blobs and excessive inline CSS/JS

### Testing and verification requirements

Add tests for:

- Descriptor-table coverage
- `llms.txt` generation content
- Markdown generation output
- Filtering behavior for hidden/unavailable content
- Route headers (`Content-Type`, `X-Robots-Tag`) and response bodies
- Regression coverage if shared/legal content was refactored

Minimum verification steps:

1. Run the test suite
2. Run a production build
3. Fetch `/llms.txt`
4. Fetch one or more `.md` companion pages
5. Confirm `Content-Type` values
6. Confirm `X-Robots-Tag: noindex, follow` on companions
7. Confirm the public discovery link (for example, footer link) works

### Acceptance criteria

Implementation is complete when:

- `/llms.txt` exists and lists intended companion URLs
- Every selected public page has a corresponding machine-readable companion
- Companion pages are readable without CSS or JS
- Companion pages are `noindex, follow`
- Canonical pages remain the only indexable versions
- Shared content sources are reused where practical
- No deceptive crawler-specific behavior exists
- Tests and production build pass

### Optional hardening for larger sites

- Add an HTML byte-budget check for key canonical pages
- Add a test that critical metadata appears near top of rendered HTML
- Add content-diff checks for critical facts between canonical and companion pages
- Add CI verification that `/llms.txt` stays synced with descriptor table

### Implementation prompt template

```md
Implement a safe machine-readable surface for this website.

Requirements:
- add `/llms.txt`
- add Markdown companion routes for main public pages
- keep canonical HTML pages as the only indexable versions
- mark companion pages `noindex, follow`
- do not use bot detection, cloaking, hidden instructions, or crawler-specific content
- centralize shared copy and legal content where practical
- add tests for generators and route headers
- run the test suite and production build
```

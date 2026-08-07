---
name: ai-search-optimization
description: Audit and improve content for retrieval, citation, and grounded answers in AI search systems. Use for AI SEO, GEO, AEO, LLM citations, answer extractability, semantic relevance, or chunk-level content structure. Different from technical-seo because it optimizes content and retrieval patterns rather than crawl/index infrastructure.
---

# AI Search Optimization

Improve how accurately AI search systems can retrieve, understand, and cite public content. Do not promise rankings or citations.

## Workflow

1. Identify the page, intended audience, and queries or questions it should answer.
2. Inspect source HTML, not only the rendered page.
3. Audit the retrieval and answer-readiness checks below.
4. Fix the highest-impact ambiguity, missing answer, or structural problem first.
5. Re-read each changed section without surrounding context; it should remain accurate and understandable.
6. Route crawl, indexation, canonical, robots, sitemap, and redirect issues to `technical-seo`.

## Retrieval and structure

- Give each page one clear purpose aligned with the intended query or task.
- Use descriptive hierarchical headings; use question headings only when they read naturally.
- Keep important sections self-contained enough to make sense when retrieved alone.
- Put the direct answer or definition near the start of the relevant section.
- State important distinctions explicitly: what something is, is not, includes, excludes, or suits.
- Prefer semantic HTML for lists and tables; give tables clear headers and images useful alt text or nearby context.
- Link related concepts with descriptive anchors and stable public URLs.
- Do not enforce a universal token or word limit. Vendor chunk sizes are heuristics unless the target system documents a requirement.

## Meaning and evidence

- Cover the terminology people actually use without keyword stuffing.
- Make entities, relationships, units, dates, and pronoun references unambiguous.
- Support factual claims with attributable sources where appropriate.
- Distinguish facts, estimates, opinions, and product claims.
- Update time-sensitive claims and show meaningful published/updated dates accurately.
- Use JSON-LD only when relevant; it must match visible content and identify the correct entity.

## Guardrails

- Treat extrapolations from vendor search products as hypotheses, not proof of consumer-search ranking systems.
- Do not optimize for rumored model names, hidden signals, fixed chunk sizes, or formulaic phrasing.
- Do not add FAQ blocks, comparisons, TL;DRs, or schema unless they improve the page for its audience.
- Report backlinks, engagement, and editorial-volume needs separately; they are not on-page retrieval fixes.
- Avoid cloaking or bot-only content.

## Output

```text
[critical|major|minor] issue — url/section
  evidence: what makes retrieval or interpretation fail
  fix: smallest useful change
```

Not a substitute for `technical-seo`, content strategy, or `website-compliance`.

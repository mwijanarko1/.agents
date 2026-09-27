---
name: blog-content-pipeline
description: "Produce keyword-researched, source-checked, publish-ready blog articles for a website. Use when the user wants blog posts, an SEO content cluster, keyword research mapped to articles, or a repeatable research-to-draft workflow. Different from technical-seo because it creates content rather than auditing crawl/index infrastructure, and from ai-search-optimization because it owns research and drafting rather than auditing existing content."
---

# Blog Content Pipeline

Produce publish-ready articles. Stop before backend implementation or production deployment unless the user explicitly asks for those separately.

## Roles

- **Keyword research and research dossiers:** fan out to subagents on model `deepseek/deepseek-v4-flash`. Load `pi-subagents` when available. Prefer parallel audience or cluster batches over one serial researcher.
- **Main/controlling agent:** inspect the repo, set scope, run Trends enrichment, verify sources, present the approval checkpoint, **write the final articles**, run humanizer and answer-readiness review, and produce the publish handoff.
- Subagents must not write final article copy. The main agent writes from verified dossiers.

## Outputs

Use the repository's existing editorial directory. If none exists, ask before creating one. Produce:

- A keyword research file
- One research dossier and draft per approved article
- A README or index linking the articles
- A publish handoff containing metadata, slugs, internal links, and repository-specific publishing notes

## Workflow

### 1. Inspect and scope

Read repository instructions first. Inspect the existing website for:

- Published articles, landing pages, titles, descriptions, and slugs
- Blog content storage and rendering
- Existing editorial documentation
- Relevant product positioning and calls to action

Ask only for decisions repository evidence cannot answer. Usually confirm:

- Target audiences
- Topic or product area
- Number of candidate phrases and finished articles
- Country and language
- Whether the user wants research only, drafts, or publish-ready content

Do not implement a CMS, database, route, sitemap, or deployment flow as part of this skill.

### 2. Inventory existing content

Map each existing page to its likely audience and search intent. Record overlaps and gaps before generating new topics. Cannibalisation checks must compare proposed articles against the live or repository content, not only against each other.

### 3. Research candidate phrases

Delegate phrase research to subagents on `deepseek/deepseek-v4-flash`. Split work by audience or topic cluster and run them in parallel when possible. Give each subagent the site context, audiences, inventory summary, country/language, and output format. Subagents research; the main agent merges, deduplicates, and ranks.

Use current search results and authoritative terminology. Cover useful intent types such as guides, questions, checklists, templates, comparisons, and commercial evaluation.

For each phrase record:

```text
phrase | audience | intent | cluster | rationale | source signal
```

Never invent search volumes. The main agent validates the merged shortlist against visible search intent, audience relevance, product relevance, evidence availability, and existing content.

#### Google Trends enrichment

When PinchTab is available, load the `pinchtab` skill and enrich shortlisted phrases with Google Trends. Use a dedicated unauthenticated browser profile where possible. If the active profile is signed in, obtain user approval before reusing it.

Use the helper script in this skill when available:

```bash
python3 ~/.agents/skills/blog-content-pipeline/scripts/trends-check.py \
  --geo GB --time "today 1-m" --anchor "head term" \
  "candidate one" "candidate two"
```

Interpret Trends carefully:

- Scores are relative interest, never absolute search volume.
- Compare at most four candidates plus one shared anchor per batch.
- Default to the past month (`today 1-m`), not the past 24 hours.
- Keep the same anchor, geography, and time window across batches.
- Ignore periods marked partial.
- Treat direction and rising-query percentages as demand signals, not proof of traffic.
- Record the retrieval date and request parameters.
- If Trends is unavailable or rate-limited, continue without it and state which phrases lack data.

Use related and rising queries to improve secondary phrases and identify content gaps. Do not let Trends override search intent or product relevance.

### 4. Approval checkpoint

Before writing, present:

- Candidate phrase list and evidence
- Trends signals when available
- Existing-content overlaps and cannibalisation risks
- Priority order
- Mapping from primary and secondary phrases to proposed articles

Do not write articles until the user approves this mapping.

### 5. Build and verify dossiers

Create one file per approved article. Use this structure:

```yaml
---
title: Working title
audience: Primary audience
status: research
slug: proposed-slug
primary_phrase: target phrase
meta_description: Draft description
---
```

Then include:

- Search intent and reader problem
- Secondary phrases
- Key questions the article must answer
- Evidence-backed factual notes
- Claims to avoid or qualify
- Source URL, publisher, retrieval date, supported claim, and source type
- Proposed internal links and call to action

Use `deepseek/deepseek-v4-flash` subagents to draft dossiers in parallel, one article or small cluster per subagent. The main agent reviews every dossier, checks material claims with primary or authoritative sources, and runs `source_check` for factual, legal, medical, financial, regulatory, or otherwise consequential claims. Drop or soften claims that cannot be verified.

### 6. Write and review

**The main agent writes the final articles.** Do not hand final copy to subagents. Write from the verified dossiers after the approval checkpoint.

Each article should:

- Answer its primary intent without keyword stuffing
- Put direct answers near the relevant headings
- Use descriptive hierarchical headings
- Keep sections understandable when retrieved independently
- Distinguish facts, estimates, opinions, and product claims
- Cite important claims naturally
- Link to relevant existing content with descriptive anchors
- Use an honest, relevant call to action
- Include meaningful published or updated dates only when accurate

Do not use a fixed word-count target. Length follows the reader's question and the evidence needed.

Load `humanizer` for the final prose pass. Load `ai-search-optimization` for retrieval and answer-readiness checks rather than duplicating its audit rules here.

### 7. Publish-ready handoff

Verify:

- Approved intent is fully answered
- Frontmatter and metadata are complete
- Slugs and descriptions are unique
- Sources support the claims attributed to them
- No proposed article cannibalises an existing page without an explicit consolidation plan
- Internal links and calls to action are valid
- Draft status is explicit

Return the article files plus a concise handoff describing how the repository currently publishes content. Production publishing, backend changes, and deployment require a separate explicit instruction and must follow repository instructions.

## Coverage follow-up

When useful, compare published topics against Search Console exports, Trends related/rising queries, or user-provided keyword files. Report uncovered intents and recommend the smallest set of follow-up articles. Do not create them without approval.

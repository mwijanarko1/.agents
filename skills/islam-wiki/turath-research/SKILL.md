---
name: turath-research
description: "Search and cite Islamic and Arabic heritage texts from turath/shamela with nusus sdk."
---

# Turath Research

Use this skill when the user asks an islamic question (fiqh, tafsir, hadith, biography, book, citation, or classical-source research question and wants sourced retrieval from Turath.

Primary library: [`nusus`](https://github.com/mwijanarko1/nusus), a TypeScript SDK for citable context from classical Islamic texts via `https://api.turath.io/`. Requires Node.js `>=20`.

## Pre-Installed Search Script

Located at `~/Desktop/nusus/scripts/search.mjs`:

```bash
# Basic search
node ~/Desktop/nusus/scripts/search.mjs "<Arabic query>" 3

# Madhhab-specific (4-tier search: "عند المذهب", "في مذهب", madhhab name, top-5 books, broad fallback)
node ~/Desktop/nusus/scripts/search.mjs --madhhab hanafi "<topic>" 3
node ~/Desktop/nusus/scripts/search.mjs --madhhab maliki "<topic>" 3
node ~/Desktop/nusus/scripts/search.mjs --madhhab shafii "<topic>" 3
node ~/Desktop/nusus/scripts/search.mjs --madhhab hanbali "<topic>" 3

# Specific books by title keyword
node ~/Desktop/nusus/scripts/search.mjs --books "بدائع الصنائع,الهداية" "<query>" 3

# Restrict search to one Turath book ID (real upstream filter, no false positives)
node ~/Desktop/nusus/scripts/search.mjs --book-id 147927 "<query>" 3

# Fetch one page with surrounding context (page_id = INTERNAL page)
node ~/Desktop/nusus/scripts/search.mjs --page 147927 5
```

Output is JSON-per-line with `book_id`, `title`, `author`, `volume`, `page_id`, `printed_page`, `headings`, `citation` (ready-made Arabic citation), `url` (direct reader link), `snippet` (highlighted match), `text`, and prev/next page context.

## SDK Direct Use

For ad-hoc scripts, import nusus directly:

```js
import { createTurathClient } from "nusus/turath";

const turath = createTurathClient({ timeout: 15_000 });

// One-call agent retrieval: bounded passages, each with citation + URL
const context = await turath.retrieve("النية في الصلاة", {
  maxPassages: 5,
  maxCharsPerPassage: 2000,
});
for (const p of context.passages) console.log(p.citation, p.url, p.text.slice(0, 200));

// Or step by step
const books = turath.findBooks("الأربعون النووية", { limit: 5 });
const categories = turath.listCategories();
const results = await turath.search("<query>", { bookIds: [books[0].id] });
const page = await turath.getPage(147927, 5);
const withContext = await turath.getContext(results.items[0], { pagesBefore: 1, pagesAfter: 1 });
const book = await turath.getBook(147927);   // metadata + indexes/headings (TOC)
const author = await turath.getAuthor(44);
```

All methods accept `AbortSignal`; failures throw typed `NususError` (`NOT_FOUND`, `RATE_LIMITED`, `INVALID_RESPONSE`, `ABORTED`, …) — never string-match error messages.

## API Gotchas

- `getPage(bookId, pageId)` — `pageId` is the INTERNAL `page_id` (`location.internalPage`), NOT the printed page (`location.printedPage`).
- Search filters (`bookIds`, `authorIds`, `categoryIds`) accept ONE ID each — the upstream API supports only one; nusus rejects multiples with `INVALID_ARGUMENT` rather than faking it.
- Turath has no verified catalog endpoint, so `findBooks()` and `listCategories()` use Nusus's bundled March 2026 snapshot (8,124 books). It may omit later upstream changes. Author-name discovery is not yet available.
- Empty upstream responses (`200 {}`) surface as `NususError` code `NOT_FOUND`.

## Search Pitfalls

1. **Book titles can be ambiguous** — `--books` resolves each title through the bundled catalog and filters by the best matching book ID. Prefer `--book-id` when several editions have similar titles.
2. **Search indexing coverage varies** — some foundational texts (Mudawwanah book_id=587, Muwatta' book_id=1699) may not appear for topic queries. Verify negative results via `getBook(id)` `indexes`/headings.
3. **Printed page vs page_id is book-dependent** — non-linear per-PDF mapping; never derive one from the other. Nusus keeps both (`printed_page`, `page_id`) plus `volume` separately.

## Core Principle

Treat Turath as a **retrieval layer**, not a final authority. Always distinguish:

1. What the retrieved source says.
2. What can be concluded from it.
3. Where scholarly interpretation, madhhab differences, or hadith grading are uncertain.

Avoid issuing definitive fatwas.

## Retrieval Workflow

1. **Plan the search** — extract Arabic keywords, prefer Arabic terms, include variant spellings.
2. **Run Turath search** — use the script for madhhab-specific searches, or `turath.search()`/`turath.retrieve()` for ad-hoc queries.
3. **Retrieve primary context** — the script already includes page text and prev/next context; use `--page` or `getContext()` for more.
4. **Assess relevance** — prefer direct mentions, primary sources within the relevant madhhab, chapter headings, and stated legal context.
5. **Synthesize cautiously** — quote Arabic when useful, explain uncertainty, never pretend consensus.

## Chain Grading via Turath

When Turath returns a narration with an *isnad*:

1. **Parse the chain** — identify each narrator from the Arabic isnad text.
2. **Identify narrators via Turath** — search biographical works (Tarikh Baghdad, Tahdhib al-Kamal, Lisan al-Mizan, etc.).
3. **Collect reliability assessments** — death dates, jarh/ta'dil statements, narration context.
4. **Apply grading methodology** — score 0-10 per narrator, Sahabah 10/10, chain probability = product × geography/chronology penalties. Sahih ≥90%, Hasan ≥80%.
5. **Check for parallel/shāhid chains** — Turath often surfaces multiple routes for the same narration.
6. **Be transparent about unknowns** — when a narrator cannot be identified, say so.

## Citation Requirements

Every substantive claim based on retrieval should cite book title, author when available, Turath book ID, page number or index location, and quoted text or concise paraphrase.

Nusus returns a ready-made citation on every passage (`citation` field) plus a direct URL. Default format:

> Author, *Book Title*, Turath book `BOOK_ID`, p. `PAGE`: "quoted Arabic text…"

Never invent missing volume, edition, publisher, or hadith numbers — nusus omits fields it doesn't have; keep them omitted.

## Answer Format

1. **Short answer** — concise response or direct finding.
2. **Sources found** — bullets with book/author/book ID/page and quote/paraphrase.
3. **Analysis** — how the sources answer the question, including madhhab/hadith grading context.
4. **Caveats** — uncertainty, missing metadata, disputed issues, or need for qualified scholarly advice.

## Guardrails

- Do not fabricate citations, book IDs, page numbers, hadith numbers, or Arabic text.
- Do not rely only on memory when the user asked for sourced retrieval.
- Do not conflate Turath search hits with authenticated hadith grading.
- Do not present one madhhab's position as universal when the question is disputed.
- Do not give high-stakes personal legal/religious rulings as final authority.
- If retrieval fails, say what searches were attempted and suggest next search terms or source constraints.

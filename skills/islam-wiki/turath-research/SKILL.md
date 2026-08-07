---
name: turath-research
description: "Search and cite Islamic and Arabic heritage texts from turath/shamela with nusus (CLI + SDK)."
---

# Turath Research

Use this skill when the user asks an Islamic, Arabic heritage, fiqh, tafsir, hadith, biography, book, citation, or classical-source research question and wants sourced retrieval from Turath.

Primary library: [`nusus`](https://www.npmjs.com/package/nusus) (`^0.4.1`) — TypeScript **SDK + agent CLI** for citable context via `https://api.turath.io/`. Requires Node.js `>=20`. Same package for both surfaces.

Prefer the **CLI** for agent tool calls. Use the **SDK** for application code, bulk extract, or anything outside the CLI command set.

## Agent CLI

From this repo (after `npm install`), or globally (`npm i -g nusus`):

```bash
npx nusus --help
npx nusus --version

# Discover (offline catalog)
npx nusus find-books "الأربعون النووية" --limit 5
npx nusus find-books --author-id 44 --limit 10
npx nusus find-authors "النووي" --limit 5
npx nusus list-categories
npx nusus catalog

# Search / retrieve (live)
npx nusus search "إنما الأعمال بالنيات" --book-id 147927
npx nusus retrieve "النية في الصلاة" --max-passages 5 --max-chars 2000

# Page / context / metadata (live)
npx nusus get-page --book-id 147927 --page-id 5
npx nusus get-context --book-id 147927 --page-id 5 --pages-before 1 --pages-after 1
npx nusus get-book 147927
npx nusus get-author 44
```

Equivalent local bin path: `node ~/islam-wiki/node_modules/nusus/scripts/search.mjs …`

Default stdout is **JSONL** (one object/line, camelCase, every line has `type`). Use `--format text` for compact human lines. Errors are JSON on **stderr** only. Unknown or command-inapplicable flags are rejected.

| Record `type` | Commands |
| --- | --- |
| `meta` | First line of `find-books`, `find-authors`, `search`, `retrieve` |
| `book` / `author` / `category` / `catalog` | Discovery + `get-book` / `get-author` |
| `passage` | `search`, `retrieve`, `get-page`, `get-context` |

Exit codes: `0` success (including zero hits), `1` usage/invalid, `2` not found, `3` rate limit/HTTP/invalid response/timeout/internal.

`page-id` is Turath internal page (`location.internalPage`), not printed page. `search`/`retrieve` accept at most one `--book-id`, one `--author-id`, and one `--category-id` (filters may be combined). Offline `find-books` may omit the title query when author/category filters are set (those offline filters are repeatable). `--timeout 0` means no timeout (max 600000).

There is **no** `--madhhab` flag or multi-book fanout. For madhhab-scoped work: resolve books with `find-books` / `list-categories`, then pass a concrete `--book-id` or `--category-id`, or add madhhab Arabic phrases to the query yourself (e.g. `عند المالكية`).

## SDK Direct Use

For application code, extract scripts, or CLI gaps:

```js
import { createTurathClient } from "nusus/turath";

const turath = createTurathClient({ timeout: 15_000 });

const context = await turath.retrieve("النية في الصلاة", {
  maxPassages: 5,
  maxCharsPerPassage: 2000,
});
for (const p of context.passages) {
  console.log(p.citation, p.locator, p.url, p.text.slice(0, 200));
}

const books = turath.findBooks("الأربعون النووية", { limit: 5 });
const byAuthor = turath.findBooks("", { authorIds: ["44"], limit: 10 });
const authors = turath.findAuthors("النووي", { limit: 5 });
const categories = turath.listCategories();
const catalog = turath.getCatalogMetadata();
const results = await turath.search("<query>", { bookIds: [books[0].id] });
const page = await turath.getPage(147927, 5);
const withContext = await turath.getContext(results.items[0], { pagesBefore: 1, pagesAfter: 1 });
const book = await turath.getBook(147927);   // metadata + TOC
const author = await turath.getAuthor(44);
```

All methods accept `AbortSignal`; failures throw typed `NususError` (`NOT_FOUND`, `RATE_LIMITED`, `INVALID_RESPONSE`, `ABORTED`, …) — never string-match error messages.

SDK-only surface (not in CLI): `searchAll`, `getPages({ from, to })`, custom loops / file writes.

## API Gotchas

- `getPage(bookId, pageId)` — `pageId` is INTERNAL (`location.internalPage`), NOT printed (`location.printedPage`).
- Search filters accept **ONE** ID each of `bookIds` / `authorIds` / `categoryIds`; different filter types may be combined. Multiples of the same filter → `INVALID_ARGUMENT`.
- Catalog is a bundled March 2026 snapshot (~8,124 books / ~3,037 authors). May omit later upstream changes.
- Empty upstream responses (`200 {}`) → `NususError` `NOT_FOUND`.

## Search Pitfalls

1. **Ambiguous titles** — resolve with `find-books`, then lock `--book-id`.
2. **Uneven indexing** — Mudawwanah `587`, Muwatta' `1699` often miss topic search; verify via `get-book` TOC.
3. **Printed vs internal page** — never derive one from the other.

## Mudawwanah (Book ID 587)

1. Topic search often fails — use `npx nusus get-book 587` for TOC.
2. Covers disputed مسائل, not recommended acts; for Ashura/Arafah-style topics prefer Muwatta' or Risala.
3. Fallback: Muwatta', wiki raw collections, Risala commentaries.

## Core Principle

Treat Turath as a **retrieval layer**, not a final authority. Distinguish: (1) what the source says, (2) what follows from it, (3) where madhhab/hadith uncertainty remains. Avoid definitive fatwas.

## Retrieval Workflow

1. **Plan** — Arabic keywords + variants.
2. **Discover** — `find-books` / `find-authors` / `list-categories` → lock IDs.
3. **Search** — `search` or `retrieve` with optional single-ID filters.
4. **Context** — `get-page` / `get-context` / `get-book` as needed.
5. **Assess** — prefer direct mentions, primary sources, headings.
6. **Synthesize** — quote Arabic when useful; never pretend consensus.

## Chain Grading via Turath

When Turath returns a narration with an *isnad*, **do not grade from Turath hits alone**. Load `../hadith-grading/SKILL.md` and:

1. Parse the chain (student → Companion).
2. Look up narrators on Shamela (`site:shamela.ws/narrator`) — Turath bios are fallback.
3. Score with `queries/grading-criteria.md`; probability via `python3 queries/grade-calc.py -s …`.
4. Check parallel/shāhid chains; be transparent about unknowns.

Nusus does not grade narrations.

## Citation Requirements

Cite book title, author when available, Turath book ID, page/locator, and quote or paraphrase.

Prefer the passage `citation` + `url` / `locator` fields. Default:

> Author, *Book Title*, Turath book `BOOK_ID`, p. `PAGE`: "quoted Arabic text…"

Never invent missing volume, edition, publisher, or hadith numbers.

## Answer Format

1. **Short answer**
2. **Sources found** — book/author/ID/page + quote/paraphrase
3. **Analysis**
4. **Caveats**

## Guardrails

- Do not fabricate citations, book IDs, pages, hadith numbers, or Arabic text.
- Do not rely only on memory when sourced retrieval was requested.
- Do not conflate Turath hits with authenticated hadith grading.
- Do not present one madhhab as universal when disputed.
- Do not give high-stakes personal legal/religious rulings as final authority.
- If retrieval fails, say what was tried and suggest next terms or filters.

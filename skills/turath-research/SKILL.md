---
name: turath-research
description: "Search and cite Islamic and Arabic heritage texts with turath-sdk."
---

# Turath Research

Use this skill when the user asks an Islamic, Arabic heritage, fiqh, tafsir, hadith, biography, book, citation, or classical-source research question and wants sourced retrieval from Turath/Turath SDK.

Primary library: [`turath-sdk`](https://github.com/ragaeeb/turath-sdk), an MIT-licensed TypeScript/JavaScript wrapper around `https://api.turath.io/` and `https://files.turath.io/books/`.

## What the SDK Provides

Use these SDK functions rather than hand-building Turath URLs:

- `getAuthor(id)` — author biography/metadata by Turath author ID.
- `getBookInfo(id)` — high-level book metadata, indexes, headings, and navigation data.
- `getBookFile(id)` — full JSON dump from `https://files.turath.io/books/{id}.json`.
- `getPage(bookId, pageNumber)` — parsed page text and metadata for a book page.
- `search(query, options)` — Turath search with filters such as author, book, category, page, precision, and sort field. The SDK maps friendly option names like `category` to API query parameters like `cat_id`.

Requires Node.js `>=22.0.0`.

## Activation Triggers

Activate when the user:

- Asks an Islamic question and wants evidence, references, quotations, or classical sources.
- Asks about Qur'an commentary, hadith references, fiqh rulings, madhhab positions, creed, seerah, tarajim/biographies, Arabic lexicons, or classical texts.
- Mentions Turath, turath.io, `turath-sdk`, Islamic book search, Arabic heritage books, or source retrieval.
- Asks for citations from a named Islamic book, author, page, volume, or passage.

Do not use this skill for casual non-research religious conversation unless the user asks for sources or the answer would materially benefit from retrieval.

## Core Principle

Treat Turath as a **retrieval layer**, not as a final authority. Always distinguish:

1. What the retrieved source says.
2. What can be concluded from it.
3. Where scholarly interpretation, madhhab differences, or hadith grading are uncertain.

Avoid issuing definitive fatwas. For personal religious practice, recommend asking a qualified scholar/mufti, especially when the issue is disputed or high-stakes.

## User Intent and Clarification

Before searching, infer these from the user's wording when possible:

- **Task type**: source lookup, exact quote, fiqh comparison, hadith lookup, tafsir question, author/book metadata, biography, or broad research.
- **Madhhab context**: Hanafi, Maliki, Shafi'i, Hanbali, Ja'fari, Salafi/Athari, non-madhhab, comparative, or unspecified.
- **Hadith grading need**: wants authenticity grading, just citation, matn lookup, takhrij, or comparison of gradings.
- **Citation format**: simple Turath page citation, academic footnote, Chicago-like, Arabic title/author, or user-provided format.
- **Language preference**: English answer, Arabic quotes, transliteration, or bilingual.

Ask a clarification question only when the missing context changes the answer substantially. Examples:

- If the user asks, “Is X permissible?” and madhhab matters, ask: “Which madhhab or should I compare major Sunni positions?”
- If the user asks for a hadith ruling, ask whether they want a specific grading tradition/source if not clear.
- If citation format matters for publication, ask for the required style.

If the question is straightforward source retrieval, proceed without asking and state assumptions briefly.

## Retrieval Workflow

1. **Plan the search**
   - Extract Arabic and English keywords.
   - Prefer Arabic search terms for classical text retrieval.
   - Include variant spellings and synonyms where useful.
   - If a book/author is named, search for or use its Turath ID, then narrow by `book` or `author` options.

2. **Run Turath search**
   - Use `search(query, options)` first for discovery.
   - Narrow results using options when intent indicates a specific book, author, category, page, precision, or sort.
   - For broad questions, run several targeted searches rather than one vague query.

3. **Retrieve primary context**
   - For promising results, use `getPage(bookId, pageNumber)` to fetch the full page context.
   - Use adjacent pages if the result seems mid-discussion or incomplete.
   - Use `getBookInfo(bookId)` for title, author, indexes, headings, and navigation context.
   - Use `getAuthor(authorId)` when author identification matters.
   - Use `getBookFile(bookId)` only when full-book processing is needed; avoid unnecessary large downloads.

4. **Assess relevance**
   - Prefer direct mentions over keyword-only hits.
   - Prefer primary/named sources requested by the user.
   - For fiqh, prioritize books authored within the relevant madhhab over comparative fiqh works. If answering about the four madhhabs, retrieve and cite a representative source from each madhhab whenever possible: Hanafi from Hanafi manuals/commentaries, Maliki from Maliki manuals/commentaries, Shafi'i from Shafi'i manuals/commentaries, and Hanbali from Hanbali manuals/commentaries.
   - Use comparative fiqh books only as secondary support, for cross-checking, or when madhhab-primary sources cannot be found; clearly label them as comparative/secondary.
   - For fiqh, look for chapter headings, stated legal issue, and school context.
   - For hadith, separate matn/isnad/source citation from authenticity grading.

5. **Synthesize cautiously**
   - Quote the relevant Arabic when useful.
   - Translate or summarize in English when the user requested English.
   - Explain uncertainty, variant views, or missing context.
   - Never pretend retrieved text establishes consensus unless the evidence supports that.

## Example Node Retrieval Snippet

When you need to run a quick retrieval script in a project or temp directory:

```js
import { search, getPage, getBookInfo, getAuthor } from "turath-sdk";

const results = await search("النية في الصلاة", {
  precision: "high",
  sort: "relevance",
});

for (const result of results.slice(0, 5)) {
  const page = await getPage(result.book_id, result.page ?? result.pg);
  const book = await getBookInfo(result.book_id);
  console.log({
    bookId: result.book_id,
    page: result.page ?? result.pg,
    title: book?.title,
    text: page?.text?.slice(0, 1200),
  });
}
```

If the current workspace lacks `turath-sdk`, install it locally only after checking with the user if the workspace should be modified. For temporary research, create a temp directory and install there:

```bash
mkdir -p /tmp/turath-research
cd /tmp/turath-research
npm init -y
npm install turath-sdk
node research.mjs
```

Check `node --version`; the SDK requires Node.js 22+.

## Subagent Use

Use subagents when the question benefits from parallel investigation or independent review, for example:

- One agent searches Turath for primary text passages while another checks book/author metadata.
- One agent gathers hadith source occurrences while another evaluates grading references from the retrieved material.
- One agent researches madhhab-specific sources while another prepares a comparative synthesis.

When using subagents, give each a narrow retrieval task and require citations, exact search terms, book IDs, and page numbers in their return.

## Citation Requirements

Every substantive claim based on retrieval should cite at least:

- Book title.
- Author when available.
- Turath book ID.
- Page number or index location.
- Quoted text or concise paraphrase tied to that page.

Default citation format:

> Author, *Book Title*, Turath book `BOOK_ID`, p. `PAGE`: “quoted Arabic text…”

For hadith references, include when available:

- Collection/book title.
- Hadith/chapter number if present in metadata.
- Page/volume if retrieved.
- Grading source separately from the hadith source.

If Turath metadata is incomplete, say so explicitly rather than inventing volume, edition, publisher, or hadith numbers.

## Answer Format

Use this structure for research answers unless the user asks otherwise:

1. **Short answer** — concise response or direct finding.
2. **Sources found** — bullets with book/author/book ID/page and quote/paraphrase.
3. **Analysis** — explain how the sources answer the question, including madhhab/hadith grading context.
4. **Caveats** — note uncertainty, missing metadata, disputed issues, or need for qualified scholarly advice.

For exact quote/citation requests, skip broad analysis and focus on retrieval accuracy.

## Guardrails

- Do not fabricate citations, book IDs, page numbers, hadith numbers, or Arabic text.
- Do not rely only on memory when the user asked for sourced retrieval.
- Do not conflate Turath search hits with authenticated hadith grading.
- Do not present one madhhab's position as universal when the question is disputed.
- Do not give high-stakes personal legal/religious rulings as final authority.
- If retrieval fails, say what searches were attempted and suggest next search terms or source constraints.

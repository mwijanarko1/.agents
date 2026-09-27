---
name: use-tinyfish
description: DORMANT. Do not load unless the user explicitly names TinyFish. Default web research uses Exa via web_search and fetch_content instead. Kept installed for optional TinyFish Search/Fetch only.
---

# TinyFish Search and Fetch (dormant)

Default path for read-only public web is Exa (`web_search`) plus `fetch_content`, not this skill. Load this skill only when the user explicitly asks for TinyFish.

If loaded: use only TinyFish Search and Fetch Content. Never use TinyFish Agent or Browser because those tools are paid. Interactive browser work stays on PinchTab.

## Workflow

1. If no URL is known, use Search to find relevant pages.
2. Use Fetch Content on the best results when snippets are insufficient.
3. If Fetch Content cannot handle a dynamic or interactive page, stop using TinyFish and switch to an available alternative.
4. Cite the pages used for source-backed answers.

## CLI Commands

### Search

```bash
tinyfish search query "<query>" [--location <hint>] [--language <hint>] [--pretty]
```

Search returns ranked results with titles, URLs, and snippets.

### Fetch Content

```bash
tinyfish fetch content get <urls...> [--format markdown|html|json] [--links] [--image-links] [--pretty]
```

Fetch Content accepts multiple URLs and returns extracted page content. Use `--links` or `--image-links` only when those fields are needed.

## MCP Tools

When TinyFish is available through MCP, use only its Search and Fetch Content tools. Do not call or discover TinyFish Agent or Browser tools for task execution. If MCP `list_tools` fails, or a later search/fetch call fails to connect after an earlier success, switch to the CLI commands above. Do not retry MCP in a loop waiting for reconnect.

Fetch Content candidate selectors are guesses. If `main` misses, inspect the HTML and retry with the real landmark (`#about`, `#content`, `article`). Do not treat `selector_not_matched` as a missing page.

## Notes

- Match the user's language.
- Prefer Search alone when its snippets answer the question.
- Fetch only the pages needed for the answer.
- Do not fall back from Fetch Content to TinyFish Agent or Browser.

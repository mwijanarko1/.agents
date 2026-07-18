---
name: search-first
description: "Research existing tools, patterns, and current library docs before writing custom code."
---

# Search First

Research before implementing.

## When

- New feature that likely has existing solutions
- Adding a dependency or integration
- Library/framework/API setup or usage questions
- About to invent a utility, helper, or abstraction
- Unknown codebase / high implementation uncertainty

## Ladder

1. **In-repo first** — search modules/tests for an existing helper or pattern.
2. **Installed deps** — reuse what the project already has.
3. **Current docs** — for libraries/frameworks, fetch live docs (Context7 MCP: `resolve-library-id` → `query-docs`, max 3 calls). Prefer official/version-matched IDs. Redact secrets from queries.
4. **Ecosystem** — npm/PyPI/crates/etc., maintained OSS, skills, MCP servers.
5. **Decide** — Adopt / Extend / Compose / Build (only if nothing suitable).

## Decision

| Signal | Action |
|--------|--------|
| Exact match, maintained, permissive license | Adopt |
| Partial match, good foundation | Extend with a thin wrapper |
| Several weak matches | Compose small pieces |
| Nothing suitable | Build minimal custom code informed by research |

## Anti-patterns

- Jumping to custom code without a search
- Training-data guesses for library APIs when docs are available
- Heavy wrappers that erase the library
- Large deps for one small feature

## Pre-edit investigation (when risk is high)

Before multi-file, schema, public API, auth, or high-assumption edits: list callers/importers, name public contracts touched, and inspect one real usage path. Do not edit on guesses.

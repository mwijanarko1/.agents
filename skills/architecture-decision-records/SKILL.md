---
name: architecture-decision-records
description: Record architectural decisions as ADRs during development.
origin: ECC
---

# Architecture Decision Records

Capture non-trivial architecture choices as short ADRs beside the code.

## When

- User asks to ADR / record a decision
- Choosing between real alternatives (stack, data store, API shape, auth, deploy)
- User asks why X was chosen (read existing ADRs)

## Gates

- **Never create `docs/adr/` or write an ADR without explicit approval.**
- Draft first; write files only after the user accepts.

## Workflow (write)

1. If `docs/adr/` missing, ask to initialize (`README.md` index + optional `template.md`).
2. Draft ADR-NNNN from context + alternatives + consequences.
3. Show draft; on approval write `docs/adr/NNNN-kebab-title.md` and index row.
4. On decline, discard.

## Workflow (read)

1. No `docs/adr/` → say so; offer to start.
2. Else scan index/files; answer from Context + Decision.

## Template

```markdown
# ADR-NNNN: Title
**Date**: YYYY-MM-DD
**Status**: proposed | accepted | deprecated | superseded by ADR-NNNN
**Deciders**: ...

## Context
## Decision
## Alternatives Considered
### Option
- Pros / Cons / Why not
## Consequences
- Positive / Negative / Risks
```

## Index row

`| [NNNN](NNNN-title.md) | Title | status | date |`

## Good ADRs

Specific, short, record *why* and rejected options. Skip trivia (formatting, one-off renames). Supersede instead of silently rewriting history.

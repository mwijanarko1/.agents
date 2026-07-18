---
name: backend-architecture
description: Backend design patterns, API design, database schemas, auth, and observability.
---

# Backend Architecture

Use for API, data, auth, and ops work — not UI.

## Workflow

1. **Contracts first** — request/response shapes, status codes, errors, idempotency.
2. **Schema** — tables/collections, keys, indexes, constraints; migrations for every durable change.
3. **AuthZ** — authenticate at the edge; authorize per resource; never trust client role claims alone.
4. **Validate at boundaries** — parse external input (body, query, headers, webhooks) before use.
5. **Observe** — structured logs, request ids, metrics/traces on hot paths; no secrets in logs.
6. **Verify** — contract/unit tests for handlers; migration dry-run on non-prod when available.

## Defaults

- Prefer explicit versioning or stable URLs over silent breaking changes.
- Transactions around multi-write business operations.
- Soft-delete or audit only when product requires history.
- Background jobs for slow/external work; make handlers idempotent.
- Rate-limit and size-limit public endpoints.

## API shape

- Resource-oriented routes; consistent error envelope (`code`, `message`, optional `details`).
- Pagination for lists; filter/sort allowlists only.
- Separate internal vs public DTOs; never leak row dumps.

## Data

- Normalize for integrity; denormalize only with a measured read need.
- Foreign keys/constraints over app-only checks when the DB supports them.
- Index what queries filter/join on; avoid speculative indexes.

## Auth

- Short-lived access tokens + rotated refresh, or server sessions with secure cookies.
- Hash passwords with a modern KDF; never roll crypto.
- CSRF protection for cookie sessions; CORS allowlist for browsers.

## Non-goals

RSC/UI composition, SEO, or visual design — use frontend skills for those.

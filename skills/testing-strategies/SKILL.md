---
name: testing-strategies
description: "Unit, integration, and E2E testing plus TDD and AI-regression guards for behavior changes."
---

# Testing Strategies

## Philosophy

- **Confidence > coverage.** Test critical business logic and user journeys, not implementation trivia.
- **Testing trophy:** Integration first, then types/static analysis, then unit, fewest E2E.
- Prefer semantic queries (role/label/text); use `data-testid` only when those fail.

## Test-first for behavior changes

For features, bug fixes, and runtime refactors:

1. Define observable behavior and edge cases.
2. Write/update the narrowest failing test (RED). Confirm it fails for the intended reason.
3. Make the smallest production change to pass (GREEN).
4. Run the closest fast test target, then broader checks if shared behavior is touched.
5. Report tests run, or why not.

Exceptions: docs-only, mechanical no-behavior change, no runnable harness, external constraint. State reason + alternative verification. Use `python3 ~/.agents/scripts/tdd_evidence.py` for RED/GREEN/exception evidence when hooks require it.

Do not edit production code until RED is real (executed failure, or intentional compile-time RED on the buggy path).

## Layers

### Unit
- Pure functions, utilities, hooks, algorithms.
- AAA pattern; isolated; no shared state.
- Assert outputs/behavior, not private state.

### Integration
- Feature flows, forms, component↔store, API handlers.
- Simulate user events; mock network at the boundary (e.g. MSW), not internal modules.
- Prefer test DB / in-memory DB over mocking the ORM for server paths.

### E2E
- Critical happy paths and smoke only.
- Production-like build; seed/clean data; assertion retries over hard sleeps.

## Mocking

- Always mock 3rd-party services (payments, email, LLM providers).
- Avoid mocking internal modules except time/randomness boundaries.
- Freeze time when determinism matters.

## AI-regression guards

AI self-review shares the same blind spots as the code it wrote. Prefer automated checks that fail when:

- Sandbox vs production paths diverge
- API response fields are added without matching query/select/type updates
- Feature-flag / entitlement branches only cover one mode
- A fixed bug has no regression test

After a bug fix: add the smallest test that would have failed before the fix. Prefer path-pair tests (sandbox + production, flagged + unflagged) when dual paths exist.

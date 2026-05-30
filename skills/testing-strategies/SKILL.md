---
name: testing-strategies
description: Testing philosophy and implementation details for Unit, Integration, and E2E testing.
---

# Testing Guidelines

## General Philosophy
- **Confidence > Coverage:** Focus on testing critical business logic and user journeys rather than chasing 100% meaningless code coverage.
- **The Testing Trophy:** Prioritize **Integration Tests** (most value), followed by Static Analysis (Types), Unit Tests, and finally E2E (fewest).
- **Test ID:** Use `data-testid` attributes only when semantic queries (role, label, text) fail. Prefer testing how users interact with the app.

## Unit Testing (Jest / Vitest)
- **Scope:** Pure functions, utilities, hooks, and complex algorithmic logic.
- **Isolation:** Tests must run in isolation and share no state.
- **Pattern:** Follow the AAA pattern (Arrange, Act, Assert).
- **Component Unit Tests:**
  - Test complex interaction logic (e.g., custom hooks).
  - Avoid shallow rendering; render the full component tree where possible.
  - Do NOT test implementation details (e.g., "state is X"); test outputs (e.g., "button is disabled").

## Integration Testing (React Testing Library)
- **Scope:** Feature flows, form submissions, interactions between components and stores.
- **Behavior-Driven:** Simulate user events (`userEvent.click`, `userEvent.type`) rather than triggering handlers manually.
- **API Boundaries:**
  - Mock external API calls using **MSW (Mock Service Worker)** at the network level.
  - Do not mock fetch/axios implementation directly.
- **Database:** For server-side integration tests, use a dedicated test database container (Docker) reset between runs.

## End-to-End (E2E) Testing (Playwright / Cypress)
- **Scope:** Critical Happy Paths (Signup, Checkout, Core Feature usage) and Smoke Tests.
- **Environment:** Run against a production-like build, not the dev server.
- **Data:**
  - Seed the database with known test data before runs.
  - Clean up data after execution.
- **Resilience:** Avoid hard-coded waits (`wait(5000)`). Use assertion retries (e.g., `await expect(ui).toBeVisible()`).
- **Visual Regression:** Use snapshot testing sparingly, focused on complex layouts that break easily.

## Mocking Strategy
- **External Services:** ALWAYS mock 3rd party APIs (Stripe, OpenAI, Email Providers) to prevent flakiness and cost.
- **Internal Modules:** Avoid mocking internal functions unless absolutely necessary (e.g., current time, random number generators).
- **Date/Time:** Freeze system time in tests to ensure deterministic results.
- **Database:** Prefer an in-memory DB or Dockerized test DB over mocking ORM calls, to catch SQL/Schema errors.

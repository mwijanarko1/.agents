---
summary: "Template for aligning goal, modules, contracts, non-goals, language, and verification before substantial work."
read_when: "Before substantial feature work, broad refactors, cross-module changes, new public interfaces, or ambiguous requests."
---

# Shared Design Concept

Use this file as the default template for substantial feature work, broad refactors, cross-module changes, new public interfaces, data model changes, or ambiguous requests.

## Goal

State the user-visible outcome or operational behavior being changed.

## Affected Modules

List the main files, services, screens, data models, APIs, events, or boundaries involved.

## Contracts And Invariants

Name the public interfaces, API shapes, schemas, state transitions, permissions, or behaviors that must hold.

## Non-Goals

List nearby work that is intentionally out of scope.

## Ubiquitous Language

Reference terms from `docs/GLOSSARY.md`. Add new terms there before introducing new domain concepts, module names, roles, permissions, events, or workflow states.

## Verification Loop

Name the smallest useful checks first, then the broader checks:

- Failing behavior test or TDD exception:
- Fast local test:
- Type check or static check:
- Browser, Playwright, or manual check:
- Final verification target:

---
name: decision-capture
description: "Extract project vision, preferences, constraints, and decisions from the user into README, docs, or ADRs through a short Q&A loop. Use when the user says brain-to-docs, extract the vision, document this project, capture decisions, or build out the docs."
category: thinking
origin: adapted-from-davidondrej-skills
---

# Decision Capture

Turn user judgment into durable project docs. Keep it short; docs are memory, not essays.

## Before Asking

1. Read existing docs first: `README.md`, `docs/`, and `docs/adr/` when present.
2. Do not ask questions that the repo already answers.
3. Decide where answers belong:
   - README: product vision and stable project shape.
   - `docs/*.md`: operating details, plans, concepts.
   - `docs/adr/`: architecture decisions only; use `architecture-decision-records` and get approval before writing ADRs.

## Loop

1. Ask 3-5 varied questions unless the user requested a narrower focus.
2. Let the user answer any subset.
3. After each substantive answer, update the smallest relevant doc.
4. Summarize the changed file path and ask the next question.
5. Repeat until the user says done.

## Question Mix

Use varied angles:
- audience and success criteria
- non-goals and constraints
- taste/preferences
- architecture or product trade-offs
- deployment/ops/support expectations

## Rules

- Plain English.
- Short sentences.
- Preserve the user's intent; do not invent strategy.
- Challenge only severe mistakes or contradictions.
- Never create ADRs without explicit approval.

---
name: grill-me
description: "Pressure-test a plan or design by asking one sharp question at a time, recommending an answer, and inspecting the code instead of asking when the code can answer. Use when the user says grill me, stress-test this, challenge this plan, or pressure-test my design."
category: thinking
origin: adapted-from-davidondrej-skills
---

# Grill Me

Use this as an interview loop for plans, designs, architecture choices, product ideas, and implementation strategies.

## Loop

1. State the current assumption in one sentence.
2. Ask **one** high-leverage question.
3. Include your recommended answer after the question.
4. Wait for the user's answer.
5. If the answer creates a dependency, follow that branch before opening a new one.
6. Stop when the plan is concrete enough to execute or the user says stop.

## Rules

- Ask one question at a time. No lists.
- If a question can be answered by reading the repo, inspect the repo instead of asking.
- Be direct, not performative.
- Prefer questions that change the decision, not trivia.
- Track resolved decisions briefly as you go.

## Output Shape

```markdown
Assumption: <one sentence>
Question: <one question>
Recommended answer: <your default and why>
```

---
summary: "Two-mode AI workflow for serious production work and relaxed experimentation."
read_when: "When prompts use /serious or /fun, or when changing AI Flow mode behavior and expectations."
---

# AI Flow

Use an explicit mode at the start of implementation prompts.

## Modes

### `/serious`

Use for production apps, company work, interviews, pair programming, bug fixes, refactors, auth, data models, APIs, shared modules, and anything where code quality matters.

The agent must:

- Inspect the repo before asking questions when repo context can answer them.
- Interview you until the task brief is complete.
- Define success criteria, affected modules, contracts, terms, risks, and verification before edits.
- Use TDD or record an explicit exception for behavior changes.
- Verify in small increments.
- Review and refactor AI-generated code instead of trusting it blindly.

### `/fun`

Use for experiments and throwaway ideas.

The agent may accept vague prompts, but safety gates still apply:

- No destructive commands.
- No protected-file edits.
- No secret leaks.
- No unsafe security patterns.

## Pair-Programming Script

Use this language when you want to show strong AI practice:

1. "I start by choosing the mode. For production work, I use `/serious`."
2. "Before coding, I make the AI inspect the repo and form a shared design concept."
3. "I force the task brief to name success criteria, module boundaries, contracts, risks, and verification."
4. "I use the glossary so humans and AI use the same domain terms."
5. "I keep feedback loops close: tests, type checks, browser checks, and review."
6. "I do not trust AI output blindly; I inspect and refactor it."

## Serious Prompt Example

```text
/serious Add password reset to the auth flow. Inspect the current auth modules first, then interview me before editing.
```

## Fun Prompt Example

```text
/fun Make a playful animated prototype for the settings page.
```

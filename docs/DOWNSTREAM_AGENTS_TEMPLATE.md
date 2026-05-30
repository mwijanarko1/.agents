---
summary: "Pointer-style AGENTS.md template for downstream repositories."
read_when: "When bootstrapping or updating a repository to use the canonical ~/.agents instructions without copying global rules."
---

# Downstream AGENTS.md Template

Use this at the top of project-local `AGENTS.md` files:

```text
READ ~/.agents/AGENTS.md BEFORE ANYTHING (skip if missing).
Then follow repo-specific rules below.
```

Add repository-specific rules below the pointer. Do not copy global shared rule blocks into downstream repos.

For submodules or nested repositories, repeat the pointer check inside each independently agent-operated repo.

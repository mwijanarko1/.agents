---
name: verification-loop
description: A comprehensive verification system for Claude Code sessions.
origin: ECC
---

# Verification Loop

Run the project's real quality gates after meaningful changes or before a PR.

## Workflow

1. **Discover** scripts from `package.json` / `Makefile` / `pyproject` / CI config — do not assume npm.
2. **Build** (if the project has one). Stop on failure.
3. **Typecheck** when configured.
4. **Lint** when configured; do not claim ready with lint errors.
5. **Tests** — closest relevant suite first, then broader if risk crosses modules.
6. **Diff review** — `git diff` for unintended files, secrets, debug leftovers.
7. **Report** status honestly.

## Report

```text
VERIFICATION REPORT
Build:    PASS|FAIL|SKIP
Types:    PASS|FAIL|SKIP
Lint:     PASS|FAIL|SKIP
Tests:    PASS|FAIL|SKIP (summary)
Diff:     N files
Overall:  READY|NOT READY
Issues:
- ...
```

## Rules

- Prefer project package-manager binaries (`pnpm`, `npm`, `bun`, `uv`, `cargo`) already in the repo.
- Cap noisy output (`head`/`tail`); fix from first real error.
- No secret scanners that require new global installs; simple `rg` for obvious keys is enough when needed.
- Skip phases the project does not have rather than inventing commands.

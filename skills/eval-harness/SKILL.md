---
name: eval-harness
description: Local eval-driven development for agent behavior using deterministic project tests and hook fixtures.
origin: ECC
---

# Eval Harness

Eval-driven development: define success before changing agent behavior, then measure.

## When

- New agent capability or prompt change
- Regression suite for agent workflows
- pass@k reliability tracking

## Workflow

1. **Define** capability + regression criteria in `.agents/evals/<feature>.md` (or project equivalent).
2. **Implement** the change.
3. **Grade** with the strongest available grader (code > rule > model > human).
4. **Record** pass@k / pass^k and failures in `.agents/evals/<feature>.log`.
5. **Gate** release-critical paths on agreed thresholds.

## Eval stub

```markdown
[CAPABILITY EVAL: name]
Task: ...
Success criteria:
- [ ] ...
Expected: ...

[REGRESSION EVAL: name]
Baseline: <sha>
Checks:
- [ ] ...
```

## Graders

- **Code** — tests, `rg -q`, build exit codes (deterministic; prefer).
- **Rule** — schema/regex constraints on output.
- **Model** — rubric score with explicit scale; not for security sign-off alone.
- **Human** — high-risk or ambiguous UX.

## Metrics

- `pass@k` — ≥1 success in k tries (capability target often pass@3 ≥ 0.9).
- `pass^k` — all k succeed (regressions/critical: pass^3 = 1.0).

## Local graders

Use local project tests and `~/.agents/tests/*` hook fixtures as graders. This skill is platform-independent: do not add an OpenAI Evals or Datasets API dependency unless the user explicitly requests that product.

## Anti-patterns

Overfit to known evals; happy-path-only; flaky graders in gates; ignoring cost/latency while chasing pass rate.

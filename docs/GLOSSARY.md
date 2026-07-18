---
summary: "Shared vocabulary for .agents policy, workflows, validation, and handoff terms."
read_when: "When adding or renaming agent concepts, policy terms, workflow states, modules, or public interfaces."
---

# Ubiquitous Language

Use this glossary to keep humans, agents, docs, tests, code identifiers, issues, and PRs aligned on the same project terminology.

## Terms

Add terms in this format:

### Term

- **Meaning**:
- **Use When**:
- **Avoid**:
- **Related Code**:
- **Related Tests**:

### Output Economy

- **Meaning**: The policy that assistant-visible output should be concise and valuable, not merely frequent.
- **Use When**: Writing progress updates, final responses, subagent summaries, review findings, and policy docs.
- **Avoid**: Using it to suppress necessary code, verification evidence, errors, or decision context.
- **Related Code**: `agent-policy.json` `output_economy`; `scripts/validate_agent_policy.py`
- **Related Tests**: `tests/test_agent_validators.py`

### Context Economy

- **Meaning**: The policy that unknown large inputs and command outputs should be summarized, capped, or range-inspected before they enter agent context.
- **Use When**: Reading large logs/data/repos, writing helper commands, maintaining handoffs, or deciding whether to compact a session.
- **Avoid**: Using it to hide necessary evidence; preserve exact errors, code snippets, commands, and verification when they matter.
- **Related Code**: `AGENTS.md`; `agent-policy.json` `context_economy`; `scripts/context_needle.py`; `scripts/validate_agent_policy.py`
- **Related Tests**: `tests/test_agent_validators.py`

### Needle Map

- **Meaning**: A small, bounded summary of a larger source that identifies relevant files, rows, fields, errors, or ranges before deeper inspection.
- **Use When**: Working with large files, logs, JSON/CSV data, or unknown repositories.
- **Avoid**: Treating it as a replacement for exact source inspection when correctness depends on precise code or data.
- **Related Code**: `scripts/context_needle.py`; `docs/CONTEXT_ECONOMY.md`
- **Related Tests**: `tests/test_agent_validators.py`

### Useful Context

- **Meaning**: Information that changes what the user or next agent can decide, verify, debug, or implement.
- **Use When**: Summarizing commands, test failures, design tradeoffs, risks, or changed behavior.
- **Avoid**: Filler, praise, obvious narration, or raw output dumps.
- **Related Code**: `AGENTS.md`; `agent-policy.json` `output_economy`
- **Related Tests**: `tests/test_agent_validators.py`

### Handoff Context

- **Meaning**: Compact information needed for another engineer or agent to continue without rediscovering important facts.
- **Use When**: Final responses, plans, PR notes, and subagent outputs.
- **Avoid**: Long process narration or repeated tool output.
- **Related Code**: `AGENTS.md`; `agent-policy.json` `output_economy`
- **Related Tests**: `tests/test_agent_validators.py`

### Shared Reference

- **Meaning**: A path, skill name, script, or policy surface referenced by shared `.agents` docs or prompts.
- **Use When**: Validating that agent instructions point to real local resources.
- **Avoid**: Treating placeholders or project-local example paths as canonical `.agents` files.
- **Related Code**: `scripts/lib/agent_validators.py`
- **Related Tests**: `tests/test_agent_validators.py`

### Supply-Chain Recipe

- **Meaning**: A command pattern in shared docs or automation that installs, resolves, or executes package code.
<!-- agent-policy: allow-forbidden-command because: this glossary names forbidden command families descriptively, not as executable recipes. -->
- **Use When**: Reviewing `npx`, `dlx`, `bunx`, `uvx`, pipe-to-shell installers, `@latest`, and dependency discovery commands.
- **Avoid**: Blocking explicit policy definitions or descriptive mentions that are allowlisted with rationale.
- **Related Code**: `agent-policy.json` `supply_chain_hardening`; `scripts/lib/agent_validators.py`
- **Related Tests**: `tests/test_agent_validators.py`

### Agent Doctor

- **Meaning**: A single local health-check command for policy, tests, routing-index freshness, and shared-reference integrity.
- **Use When**: Running pre/post-change checks for `.agents`.
- **Avoid**: Using it to rewrite files or silently fix drift.
- **Related Code**: `scripts/agent_doctor.py`
- **Related Tests**: `tests/test_agent_validators.py`

## Module Names

Record stable module names and the domain concept each module owns.

| Module | Owns | Public Interface | Notes |
|--------|------|------------------|-------|

## Workflow States

Record user-visible or system-visible states.

| State | Meaning | Valid Transitions |
|-------|---------|-------------------|

## Roles And Permissions

Record product roles, entitlements, and permission terms.

| Term | Meaning | Enforcement Boundary |
|------|---------|----------------------|

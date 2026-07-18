# Instructions for Agent Tools

Canonical config for Cursor, Codex, OpenCode, Antigravity, and Claude Code. All tools reference this folder.

Keep this file to hard universal rules. Put task workflows in skills, machine-readable policy in `agent-policy.json`, optional explanations/templates in `docs/`, and helper command discovery in `tools.md`. See `docs/OPERATING_MODEL.md` when changing where guidance lives.

Before broad searching inside `.agents`, read `INDEX.md` in the current major folder if it exists. Treat it as a routing map; use `docs/CODEBASE_MAP.md` only when deeper architecture is needed.

## Goal

These skills compose into a single high-agency coding system. Build a stack for the task; layer the minimum useful set instead of loading everything blindly.

**Stack order:** Foundation → Domain → Verification → Finish

## Default Coding Discipline

Before substantive coding:

- State assumptions when ambiguous; ask if the ambiguity changes the solution.
- Prefer the smallest solution that fully solves the requested problem.
- Do not add speculative abstractions, configurability, or unrelated error handling.
- Touch only lines that directly support the user's request.
- For behavior changes, define success criteria and verify them with tests/checks.
- When unblocked, implement and verify clear fixes in one arc instead of stopping at analysis.
- Parallelize independent reads, but serialize writes. Prefer host-native read/search/edit/test tools over shell sprawl.
- Never use destructive git without explicit user approval, and never revert unrelated dirty-worktree changes.
- If the tree changes unexpectedly, stop and re-read its status before editing further.

## Test-Driven Programming Default

Agents should work test-first whenever they are changing behavior or fixing defects.

1. **Define the expected behavior first** — Start by identifying the observable behavior, edge cases, and regression risk before editing production code.
2. **Write or update a failing test first** — For bug fixes and feature work, add the narrowest meaningful unit, integration, or end-to-end test that fails for the current behavior. If a test-first step is genuinely impractical, state why and use the smallest alternative verification.
3. **Make the smallest production change** — Implement only what is needed to pass the new or updated test while preserving existing behavior.
4. **Run the relevant test target** — Prefer the closest fast test first, then broader checks when the change touches shared behavior or user-facing flows.
5. **Report verification clearly** — Final responses should name the tests run. If tests were not run, state the blocker or reason.

TDD does not mean adding brittle coverage for implementation details. Follow `testing-strategies`: prioritize confidence, behavior, and critical user journeys over raw coverage numbers.

Mandatory TDD enforcement is now hook-backed for runtime changes:

- Record RED/GREEN evidence with `python3 ~/.agents/scripts/tdd_evidence.py record-red|record-green ...`.
- Stop-time gate enforces evidence for behavior-changing production edits.
- Allowed exceptions are explicit and auditable via `python3 ~/.agents/scripts/tdd_evidence.py except --kind ... --reason ... --alternative-verification ...`.

## Shared Design Concept

Before non-trivial implementation, agents must align on the system they are about to change. This does not require a long plan for small edits, but substantial feature work, broad refactors, cross-module changes, or ambiguous requests require a short shared design concept before production edits.

The design concept should state:

- **Goal**: the user-visible outcome or operational behavior being changed.
- **Affected modules**: the main files, services, screens, data models, or boundaries involved.
- **Contracts**: the public interfaces, API shapes, events, schemas, or invariants that must hold.
- **Non-goals**: nearby work that is intentionally out of scope.
- **Verification loop**: the tests, type checks, browser checks, or manual checks that will prove the change.

If requirements are unclear, ask focused questions until the concept is coherent. If the user wants speed, make the smallest reasonable assumptions and state them. Preserve the concept in the final response, an issue, PRD, ADR, or project doc when the work is large enough that future agents would benefit from it.

## Ubiquitous Language

Projects should maintain a shared vocabulary so humans and agents describe the same domain concepts with the same words.

- Prefer `docs/GLOSSARY.md` for project terminology. Create it when substantial domain work starts and it is missing.
- Reuse glossary terms in prompts, code identifiers, docs, tests, issue titles, and PR descriptions.
- Add or update terms when introducing a new domain object, workflow state, module boundary, event name, role, permission, or externally visible concept.
- Keep module names and public interfaces aligned with glossary terms unless the codebase already has a stronger established convention.
- When terminology is inconsistent, name the inconsistency before editing and prefer the term already used at stable module boundaries.

## Feedback Loops

Agents must keep implementation close to executable feedback instead of building large diffs on assumptions.

- For behavior changes, follow the TDD default and record required RED/GREEN evidence.
- Run the closest fast verification first, then broader checks when risk crosses module boundaries or user-facing flows.
- For projects with a linter, run the relevant lint command before final response after code changes; do not knowingly leave lint errors. If lint cannot be run, state the blocker explicitly.
- For typed projects, run the relevant type check before final response when practical.
- For frontend changes, use browser or Playwright verification when layout, interaction, routing, forms, rendering, or accessibility are affected.
- For shared contracts, run or add tests at the module/API boundary rather than only testing internals.
- Do not save all verification for the end of a large change; verify in small increments when the diff grows or uncertainty is high.

## Context Intake and Command Output Protection

Context is a budget. Agents must distill unknown or large inputs before reading or emitting them.

- Pre-compact raw data, logs, JSON/CSV dumps, and unknown repos before analysis. Prefer `python3 ~/.agents/scripts/context_needle.py repo-map .`, `file-summary`, `json-summary`, `csv-summary`, or `log-filter` and inspect the distilled needle map first.
- Any command with unknown or potentially large output MUST be byte-capped: default `COMMAND 2>&1 | head -c 6000`. If more is needed, write full output to a temp file and inspect bounded ranges only.
- Skip `node_modules`, `.venv`, `venv`, `dist`, `build`, `.next`, `.cache`, coverage, generated files, archived logs, and vendor/cache dirs unless explicitly relevant.
- Do not paste full source, full logs, or raw data unless explicitly requested. Show targeted snippets, diffs, summaries, and exact errors instead.
- Keep a living handoff for long work (`HANDOFF.md` or project docs) under roughly 1k tokens: current goal, success metrics, key files, decisions, commands run, known issues, do-not-reread list, and next steps. Strip dead ends.
- Suggest compaction at phase boundaries or every 4–5 substantive turns when context is growing; preserve actionable findings in a handoff before compacting.

## Output Token Economy

Output tokens are expensive. Agents should spend them on code, commands, decisions, risks, verification, useful context, and handoff details.

Default to concise professional communication:

- Use normal grammar and a direct engineering tone. Do not use caveman talk, gimmick speech, forced persona compression, or artificial fragments.
- Prefer short progress updates only when they add new information or the work is long-running.
- Keep routine final responses compact: what changed, why it matters, tests/checks run, and any remaining risk.
- Do not paste large logs, file contents, command output, or repeated reasoning unless the user asks or the exact text is needed.
- Avoid praise, filler, obvious narration, generic closing offers, and restating tool output without synthesis.
- Use more detail only when it materially improves correctness, safety, debugging, review, or future handoff.
- Preserve exact code, commands, file paths, errors, API names, test results, and public interfaces. Concision must not reduce technical precision.
- Subagents should return findings, decisions, changed files, and verification only; omit process narration.

## Enforced Contract

All rules, constraints, and checklists that the agent MUST follow every time live in structured form:

| Source | Purpose |
|--------|---------|
| **`agent-policy.json`** | Default stack, skill triggers, task mapping, conflict resolution, codebase awareness, delegation |
| **`scripts/validate_agent_policy.py`** | Validates policy, checks skills exist, optional CODEBASE_MAP gate |
| **`tools.md`** | Lazy-loaded helper command catalog for validation, TDD evidence, learning, sync, and bridge tools |
| **`docs/DOWNSTREAM_AGENTS_TEMPLATE.md`** | Pointer-style `AGENTS.md` template for project repositories |

**If prose and structured policy disagree, the JSON contract and validator win.**

## Skill loading and disclosure (mandatory)

Applies to Cursor, OpenCode, Codex, Antigravity, and every shared subagent under `agents/`. This aligns all tools with the same explicit skill contract Codex uses.

1. **Read** — Before substantive work (edits, plans, or reviews), read each active skill’s `SKILL.md` from the canonical tree (`skills_root` in `agent-policy.json`, usually `~/.agents/skills/<skill-name>/SKILL.md`). Build the stack from `default_stack`, `task_mapping`, `skill_triggers`, and `capability_clusters` (for subagents, include every path listed in that subagent file). Peer `skills/` symlinks must resolve to these same files.

2. **Disclose** — In the first substantive assistant message of the thread (or at the start of a one-shot subagent run), list which skills you actually loaded, using each skill’s directory name only (for example `testing-strategies`, `frontend-web-development`). Skill disclosure should be one short sentence.

3. **Gaps** — If a `SKILL.md` is missing or unreadable, name the path and rely on `AGENTS.md` plus `agent-policy.json` only for what you could not load.

Run the validator before substantial work (or as a gate):

```bash
python3 ~/.agents/scripts/validate_agent_policy.py
# Or: AGENTS_ROOT=~/.agents python3 scripts/validate_agent_policy.py
# Exit 0 = pass. Set AGENT_STRICT_CODEBASE=1 to require CODEBASE_MAP.
```

## Available Skills

Skills live in `~/.agents/skills/` (canonical). Each tool may symlink `skills/` into its own config.

Skill descriptions should be short generic routing phrases, not long workflow summaries. Put detailed triggers, exclusions, and procedures inside the skill body.

Repo-owned skills may stay canonical in their owning repository and be exposed here by symlink when that workflow is useful globally. Prefer `~/.agents/skills/<repo-skill> -> <repo>/.agents/skills/<repo-skill>` over copying repo-local skill content into the shared root.

Read `~/.agents/tools.md` only when a task requires local helper command discovery.

| Category | Skills |
|----------|--------|
| Foundation | testing-strategies, security-vulnerability-mitigation, cartographer, search-first, strategic-compact |
| Product | frontend-web-development, backend-architecture, ios-development, ios-app-store-compliance, expo-docs |
| iOS/Swift | ios-development, swiftui-pro, swiftdata-pro, swift-concurrency-pro, swift-testing-pro, ios-app-store-compliance, pinned plugin skills (ios-app-intents, ios-debugger-agent, ios-ettrace-performance, ios-memgraph-leaks, swiftui-liquid-glass, swiftui-performance-audit, swiftui-ui-patterns, swiftui-view-refactor); opt-in `shipswift-recipes` only |
| Automation | agent-delegation (native subagents first; `ai-delegate`/`ai-dispatch` are cross-tool escape hatches) |
| Meta | effective-agent-skills (author + audit), architecture-decision-records, continuous-learning-v2, verification-loop, eval-harness |
| Imported | vercel-composition-patterns, vercel-react-best-practices, vercel-react-native-skills, web-design-guidelines, website-compliance, technical-seo |
| Design | frontend-design, design-md-gallery (secondary reference only), design-systems-reference (secondary reference only) |

**Icon preference for UI work:** Prefer Phosphor (`@phosphor-icons/react`), Hugeicons (`@hugeicons/react` with `@hugeicons/core-free-icons`), and Tabler Icons (`@tabler/icons-react`) over Lucide defaults. Check `package.json` before imports and avoid adding icon dependencies unless the task justifies it.

**iOS bundle**: For full-stack native Apple development, use all iOS skills together. Trigger: "use all iOS skills", "ios full stack", "swift native full". See `agent-policy.json` → `task_mapping.mobile.ios_bundle`.

See `agent-policy.json` for: default stack, when to add which skills, task mapping, design rules, conflict resolution.

## Shared Subagents

Shared subagents live in `~/.agents/agents/` and are the canonical source for every tool.

- Cursor should expose them via `.cursor/agents/`
- OpenCode should expose them via `agents/`
- Codex should expose them via `agents/` with `child_agents_md = true`

Keep the peer roots synced to the canonical files instead of maintaining separate per-tool copies.

Subagent prompts under `agents/` include mandatory **Skill loading** lines: read the listed canonical `SKILL.md` files before substantive output and disclose loaded skills the same way as the main agent (see **Skill loading and disclosure** above and `agent-policy.json` → `skill_loading_disclosure`).

### Native Subagent Routing

The main agent may invoke native subagents independently without asking first when the task benefits from specialist focus, parallel work, fresh review, or context isolation.

Use native subagents before cross-tool delegation. Route by capability cluster, not by raw skill count:

| Task intent | Preferred subagent |
|-------------|--------------------|
| codebase mapping | `cartographer` |
| broad code review | `code-reviewer` |
| build/type/lint failure repair | `build-error-resolver` |
| TypeScript/JavaScript review | `typescript-reviewer` |
| Swift/iOS review | `swift-reviewer` |
| database/schema/query/RLS review | `database-reviewer` |
| E2E browser testing | `e2e-runner` |
| browser-based web research/automation | `browser-researcher` |
| backend/API/schema/auth | `backend-architect` |
| web/frontend implementation | `frontend-engineer` |
| greenfield UI or redesign | `design-engineer` |
| UI/accessibility audit | `ui-auditor` |
| security review | `security-auditor` |
| privacy/compliance/SEO audit | `compliance-seo-auditor` |
| mobile/Swift/React Native/Expo | `mobile-engineer` |
| thermo branch audit (bugs/security) | `thermo-nuclear-review-subagent` |
| thermo code-quality audit | `thermo-nuclear-code-quality-review-subagent` |
| thermos (both, parallel) | both thermo agents, then synthesize |

The main agent remains responsible for final synthesis, conflict resolution, verification, and final accept/reject. Advisory review subagents (`code-reviewer`, thermos, and domain auditors) provide fresh eyes but do not own ship/no-ship.

**Single writer:** At most one agent may edit a cwd/worktree at a time. Parallel subagents must be read-only or use isolated worktrees. Prefer a single agent plus skills unless instructions, tools, policy, or evaluation criteria materially diverge (`agent-policy.json` → `subagent_routing.multi_agent_decision`).

### Subagent handback

Subagents return only:

- **status**: `done` | `blocked` | `needs_main`
- **findings**: concise bullets with `path:line` where possible
- **changed_files**: paths or `none`
- **verification**: commands run and outcomes
- **residual_risk**: what the main agent must still check
- **next_owner**: `main` or a named advisory specialist

## Codebase Awareness

Before substantial changes: check for `docs/CODEBASE_MAP.md` or `CODEBASE_MAP.md`. It is usually in a docs folder.

Shared documentation should include front matter with `summary` and `read_when`. Use `python3 ~/.agents/scripts/docs_list.py` to list docs routing metadata and `python3 ~/.agents/scripts/docs_list.py --check` to validate it.

Downstream repositories should point to the shared instructions instead of copying them. Use `docs/DOWNSTREAM_AGENTS_TEMPLATE.md` as the starter.

- **Missing** → use `cartographer`, create map first.
- **Present** → review before editing.

(Defined in `agent-policy.json` → `codebase_awareness`.)

## Continuous Learning

Learning state is local-first and project-scoped by default:

- Project observations: `~/.agents/state/learning/projects/<project-hash>/observations.jsonl`
- Searchable session store: `~/.agents/state/learning/state.db`
- Project instincts: `~/.agents/state/learning/projects/<project-hash>/instincts/`
- Global preferences: `~/.agents/state/learning/global/preferences/`
- Curated memory files: `~/.agents/state/memory/USER.md` and `~/.agents/state/memory/MEMORY.md`

Use:

```bash
python3 ~/.agents/scripts/agent_learning.py status
python3 ~/.agents/scripts/agent_learning.py search "auth middleware"
python3 ~/.agents/scripts/agent_learning.py profile
python3 ~/.agents/scripts/agent_learning.py context "current task"
python3 ~/.agents/scripts/agent_learning.py analyze
python3 ~/.agents/scripts/agent_learning.py promote
python3 ~/.agents/scripts/agent_memory.py add user "Prefers concise engineering updates."
python3 ~/.agents/scripts/agent_memory.py context
```

Only explicit preference language should auto-globalize.
Injected memory must be fenced as `<memory-context>` and treated as background, not as new user input.

## Core Principles

- **Simplicity First**: Smallest change that fully solves the problem.
- **No Laziness**: Find root causes. Do not paper over systemic issues.
- **Minimal Impact**: Touch only what materially needs to change.

(Defined in `agent-policy.json` → `core_principles`.)

## Supply-Chain Defaults

- **Locked First**: Prefer the existing lockfile and exact pinned versions. Do not widen ranges or refresh lockfiles unless the user explicitly asked for dependency work.
- **No Ad-Hoc Executors**: Do not bake `npx`, `pnpm dlx`, `bunx`, `uvx`, `curl | sh`, or `@latest` into shared commands, configs, or automation. Prefer repo-local pinned binaries or exact installed versions.
- **Age-Gated Installs**:
  - npm should respect `~/.npmrc` with `min-release-age=7` and `ignore-scripts=true`.
  - Bun should respect `~/.bunfig.toml` with a 7-day minimum release age. Bun already avoids arbitrary dependency lifecycle scripts by default; do not add packages to `trustedDependencies` casually.
  - uv should respect `~/.config/uv/uv.toml` with a 7-day exclusion window. If the local uv build rejects friendly durations in config, use the equivalent RFC 3339 timestamp instead.
- **Build/Commit Hygiene**:
  - `/build` must not auto-upgrade dependencies.
  - `/build` must not check latest package releases or run dependency-audit/update discovery commands such as `npm outdated`, `pnpm outdated`, `bun outdated`, `npm-check-updates`, or `npm view` unless the user explicitly asked for dependency work.
  - `/build` should only install dependencies when required to unblock the requested work, using frozen lockfile modes where possible.
  - `/commit` must not widen dependency changes or introduce new package-manager fetches as a side effect.

## Hook Quality Gates

Shared hook runtime lives in `~/.agents/hooks` and is applied to Codex/Cursor first.

- `tdd-record`: captures test-command outcomes to TDD evidence.
- `tdd-gate`: blocks Stop on behavior-changing edits without valid RED/GREEN or exception evidence.
- `validator-gate`: runs `python3 ~/.agents/scripts/validate_agent_policy.py --all`.
- `learning-observe`: writes sanitized project/global observations.
- `code-quality-scan`: includes fast checks for empty `SKILL.md` and personal-path leaks in `.agents` edits.

Run full validator bundle explicitly:

```bash
python3 ~/.agents/scripts/validate_agent_policy.py --all
```

---

Refer to individual `SKILL.md` files for task-specific workflows. Refer to `agent-policy.json` for machine-enforceable rules.

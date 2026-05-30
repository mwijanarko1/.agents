---
name: ai-interaction-workflow
description: "Foundation workflow for execution discipline, reviews, and version control."
---

# AI Interaction & Workflow

## AI Behavior & Vibe Coding Safeguards

### Shared Design Concept
- Before substantial feature work, broad refactors, cross-module changes, or ambiguous requests, establish a short shared design concept before production edits.
- Include the goal, affected modules, contracts/interfaces, non-goals, and verification loop.
- Ask focused questions when the concept is incoherent or risky. If speed matters, state the smallest reasonable assumptions and proceed.
- Preserve the concept in the final response, PRD, issue, ADR, or project docs when it will help future work.

### Ubiquitous Language
- Prefer a project `docs/GLOSSARY.md` for domain terms. Create or update it when substantial domain work introduces new concepts.
- Reuse glossary terms in prompts, code identifiers, docs, tests, issue titles, and PR descriptions.
- Keep module names and public interfaces aligned with glossary terms unless existing codebase conventions are stronger.
- When terminology is inconsistent, call it out and prefer the term already used at stable module boundaries.

### Feedback Loops
- Keep implementation close to executable feedback: tests, type checks, linters, browser checks, and focused manual verification.
- For behavior changes, follow the TDD contract and record RED/GREEN evidence where hook policy requires it.
- Run the closest fast verification first, then broader checks when changes cross module boundaries or user-facing flows.
- For frontend changes that affect layout, interaction, routing, forms, rendering, or accessibility, verify in a browser or Playwright when practical.
- Do not wait until the end of a large diff to verify; run checks in small increments when risk or uncertainty increases.

### Two-Mode AI Flow
- If the prompt starts with `/serious`, treat the task as production-quality or interview-quality work.
- If the prompt starts with `/fun`, treat the task as relaxed experimentation.
- If neither command is present, ask which mode to use before implementation.
- In `/serious`, do not mutate files until the task brief is complete: goal, success criteria, current state, affected modules, contracts/invariants, ubiquitous language, risks/edge cases, verification loop, and out of scope.
- In `/fun`, preserve safety gates but relax prompt-quality and TDD gates.

### Business Logic & "Math"
- **Server-Side Calculation:** NEVER calculate financial data, prices, scores, or permissions on the client.
  - Bad: `const total = cart.reduce((a, b) => a + b.price, 0)` in a React component.
  - Good: Send product IDs to the server; server calculates total based on DB prices.
- **Trustless Client:** Assume the client code has been modified by the user. Do not rely on `disabled={true}` or hidden UI elements to prevent actions.

### Premium & Feature Gating
- **Withhold, Don't Hide:** Do not just hide "Premium" buttons or routes. The API/Server Action must strictly return a `403 Forbidden` or empty data if the user lacks the specific entitlement.
- **Verification:** Never trust a client-side boolean (e.g., `user.isPremium`) for sensitive operations. Re-verify subscription status on the server immediately before delivering content or performing an action.

### Database Access (Anti-Pattern)
- **No Direct Client-to-DB:** Even if using Supabase/Firebase, DO NOT write data directly from the frontend using client SDKs in `useEffect` or event handlers.
- **Middleware Requirement:** Always route data mutations through a "Middleware" layer (Next.js API Routes, Server Actions, or Edge Functions) to ensure validation and rate limiting run in a trusted environment.

### Operational Protocols
- **Manual Trigger Strategy:** Do not run `npm run dev` or `npm start`. Wait for specific user instructions before starting any server.
- **Command Protocol:** Announce substantial or potentially risky terminal actions before running them. Routine read-only inspection and low-risk verification do not need to block on permission.
- **Process Management:** Avoid starting long-running or background processes. Keep the terminal available for the user.

## Output Format (for Code Reviews/Audits)

Group findings by file. Use `file:line` format (VS Code clickable). Terse findings.

```text
## src/Button.tsx

src/Button.tsx:42 - icon button missing aria-label
src/Button.tsx:18 - input lacks label
src/Button.tsx:55 - animation missing prefers-reduced-motion
src/Button.tsx:67 - transition: all → list properties

## src/Modal.tsx

src/Modal.tsx:12 - missing overscroll-behavior: contain
src/Modal.tsx:34 - "..." → "…"
```

## Version Control Guidelines

### Branching Strategy
- **Flow:** Adopt **GitHub Flow** (Trunk-Based Development).
  - `main`: Production-ready state. Deployable at any time.
  - `feature/`: New features (e.g., `feature/auth-login`).
  - `fix/`: Bug fixes (e.g., `fix/header-alignment`).
  - `chore/`: Maintenance, config, dependency updates.
- **Naming:**
  - Use lowercase kebab-case.
  - Format: `type/short-description`.
  - Example: `feature/user-profile`, `fix/login-timeout`.

### Commit Convention
- **Standard:** Follow **Conventional Commits** (`type(scope): subject`).
- **Types:**
  - `feat`: A new feature.
  - `fix`: A bug fix.
  - `docs`: Documentation only changes.
  - `style`: Formatting, missing semi-colons (no code change).
  - `refactor`: A code change that neither fixes a bug nor adds a feature.
  - `test`: Adding missing tests or correcting existing tests.
  - `chore`: Changes to the build process or auxiliary tools.
- **Subject:**
  - Imperative mood ("Add" not "Added").
  - No capitalization of first letter.
  - No period at the end.
  - **Example:** `feat(auth): implement google oauth provider`

### Pull Requests (PRs)
- **Scope:** Limit PRs to a single logical change or feature. Large PRs (>400 lines) should be split.
- **Description:** Must answer:
  1.  **What** changed?
  2.  **Why** (context/ticket link)?
  3.  **How** to test?
- **Merge Strategy:** Use **Squash and Merge**.
  - Keeps the `main` history clean and linear.
  - Combines WIP commits into a single semantic commit.

### Workflow Rules
- **Never Push to Main:** Direct pushes to `main` are blocked. All changes require a PR.
- **Syncing:** Pull `main` into your feature branch frequently (`git pull origin main`) to resolve conflicts early, not at the end.
- **Secrets:** NEVER commit `.env` files, API keys, or credentials. Use `.gitignore`.
- **Cleanup:** Delete feature branches immediately after merging.

---
name: coding-standards
description: Universal engineering standards for naming, code style, documentation, and modularity.
---

# Universal Engineering Standards

These standards guide code you are already touching for the task. They do not authorize drive-by refactors, broad style rewrites, import churn, comment rewrites, file splitting, or abstraction work unrelated to the user's request. Prefer existing local style when it conflicts with a general preference here, unless the requested change explicitly includes cleanup.

## Code Quality Guidelines

### Naming Conventions
- **General:** Use English language universally.
- **Variables & Functions:** Use `camelCase`. Names must be descriptive (verb-noun).
  - Bad: `const d = ...` | `function handle()`
  - Good: `const userData = ...` | `function handleSubmit()`
- **Components:** Use `PascalCase`. Filename must match component name.
  - Example: `UserProfile.tsx` -> `export function UserProfile() {}`
- **Booleans:** Must be interrogative (`is`, `has`, `should`, `can`).
  - Example: `isVisible`, `hasAccess`, `canSubmit`.
- **Constants:** Use `UPPER_SNAKE_CASE` for values that are truly static/config.
- **Types/Interfaces:** Use `PascalCase`. Do NOT use `I` prefix (e.g., `IUser`).

### Code Style & Formatting
- **Imports:**
  - Use **Absolute Imports** (`@/components/...`) over relative paths (`../../`).
  - Order: Built-ins -> External (npm) -> Internal (Project) -> Styles.
- **Functions:**
  - Prefer **Function Declarations** (`export function Name()`) for top-level components (better for debugging/stack traces).
  - Use **Arrow Functions** for callbacks and inline handlers.
- **Conditionals:**
  - Use **Early Returns** (Guard Clauses) to avoid nested indentation ("Arrow Code").
  - Use Ternaries only for short, single-line logic. Avoid nested ternaries.
- **TypeScript:**
  - **Strict Mode:** No `any`. Use `unknown` or specific types.
  - **Inference:** Allow TS to infer return types for simple functions; explicit return types for exports/APIs.

### Documentation
- **Philosophy:** Code should be self-documenting. Clear variable names > comments.
- **When to Comment:**
  - Explain **"Why"** a decision was made, not **"What"** the code is doing.
  - Mark workarounds for specific browser bugs or API quirks.
- **JSDoc:** Mandatory for shared utilities and complex business logic functions. Include `@param` and `@returns` descriptions.
- **TODOs:** Format as `// TODO(username): Description` so they can be tracked.

### Modularity & Structure
- **Single Responsibility:** A component should do one thing. If a file exceeds ~250 lines, refactor sub-components or logic into hooks.
- **Logic Extraction:**
  - Move complex `useEffect` or state logic into custom hooks (`useFeatureLogic.ts`).
  - Keep JSX clean and declarative.
- **Magic Values:**
  - No hardcoded strings or numbers in business logic. Extract to a `constants.ts` file or configuration object.
- **Colocation:** Keep related styles, tests, and types close to the component, not in far-away folders.

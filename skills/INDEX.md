# Skills Index

This folder contains reusable task workflows. Open only the matching skill's `SKILL.md`.

## Start Here

- Match the user request to the most specific skill below.
- Read `skills/<name>/SKILL.md` before using that workflow.
- If several match, prefer the domain skill first, then verification/review skills.
- Do not scan every skill folder.

## Skill Groups

| Need | Start With |
|---|---|
| Web UI, redesign, React/Next | `frontend-design`, `frontend-web-development`, `vercel-react-best-practices`, `vercel-composition-patterns` |
| Mobile/iOS/Swift | `ios-development`, `swiftui-pro`, `swiftdata-pro`, `swift-testing-pro`, `swift-concurrency-pro`, `ios-app-store-compliance`, pinned plugin skills (`ios-app-intents`, `ios-debugger-agent`, `ios-ettrace-performance`, `ios-memgraph-leaks`, `swiftui-liquid-glass`, `swiftui-performance-audit`, `swiftui-ui-patterns`, `swiftui-view-refactor`) |
| React Native/Expo | `vercel-react-native-skills`, `expo-docs` |
| Backend/API/security | `backend-architecture`, `security-vulnerability-mitigation`, `t3mp3st`, `website-compliance` |
| Agent workflow/delegation | `agent-delegation`, `verification-loop`, `testing-strategies` |
| Code quality/review | `testing-strategies`, `dead-code-detector` (thermo agents under `agents/`) |
| Research/docs/search | `search-first`, `find-skills`, `fetch-tweet`, `islam-wiki` (`hadith-grading`, `icma`, `turath-research`) |
| Islamic research (hadith/ICMA/turath) | `islam-wiki` → `hadith-grading`, `icma`, or `turath-research` |
| Playwright browser (Helium) | `playwright-browser` |
| Job search / cold email outreach (Himalaya; listings as leads only) | `job-apply` |
| Extract website DESIGN.md | `extract-design-md` |
| Full-clone a public website (Ditto) | `ditto-clone` |
| Thinking/decision capture / skill authoring | `grill-me`, `decision-capture`, `effective-agent-skills` |
| Architecture/docs/memory | `cartographer`, `architecture-decision-records`, `continuous-learning-v2`, `strategic-compact` |
| ShipSwift components/features (opt-in) | `shipswift-recipes` only when user names ShipSwift/recipes |
| Releases/updates | `electron-app-release`, `update-agents` |
| Pi package authoring | `create-pi-package` |
| Mosque/prayer workflows | `create-mwhs-khutbah`, `extract-mosque-prayer-times`, `extract-mosque-pdf-vision` |
| Quran revision / muraja'ah sessions | `quran-revision` (local Al Muraja'ah CLI coach; phone for circulation) |

## Deprecated Aliases

| Alias / deleted | Use Instead |
|---|---|
| `redesign-skill`, `soft-skill`, `taste-skill` | `frontend-design` |
| `add-component`, `build-feature`, `explore-recipes` | `shipswift-recipes` (explicit opt-in) |
| `tdd-workflow`, `ai-regression-testing` | `testing-strategies` |
| `documentation-lookup`, `gateguard` | `search-first` |
| `context-budget` | `strategic-compact` |
| `skill-stocktake` | `effective-agent-skills` (audit mode) |
| `ai-interaction-workflow`, `coding-standards`, `output-skill` | `AGENTS.md` / `agent-policy.json` |
| `thermo-nuclear-review`, `thermo-nuclear-code-quality-review`, `thermos` | thermo agents under `agents/` |
| `herdr-delegate` | native Herdr skill / native subagents |
| `ios-simulator-browser` | disabled stub; use `ios-debugger-agent` (explicit name only) |
| `hadith-grading`, `turath-research`, `icma` (top-level) | `islam-wiki/hadith-grading`, `islam-wiki/turath-research`, `islam-wiki/icma` |

## Boundaries

- Prefer extending an existing skill over creating a new near-duplicate.
- Keep skill-specific implementation details inside that skill folder.
- Do not edit `.system/` unless the task explicitly targets system skills.

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
| Every coding task | `ponytail` |
| Fuller ADHD-friendly output shaping | `i-have-adhd` |
| Web UI, redesign, React/Next | `frontend-design`, `frontend-web-development`, `vercel-react-best-practices`, `vercel-composition-patterns`; `shadcn-lint` for Tailwind v4 design-system lint setup |
| Mobile/iOS/Swift | `ios-development`, `swiftui-pro`, `swiftdata-pro`, `swift-testing-pro`, `swift-concurrency-pro`, `ios-app-store-compliance`, pinned plugin skills (`ios-app-intents`, `ios-debugger-agent`, `ios-ettrace-performance`, `ios-memgraph-leaks`, `swiftui-liquid-glass`, `swiftui-performance-audit`, `swiftui-ui-patterns`, `swiftui-view-refactor`) |
| React Native/Expo | `vercel-react-native-skills`, `expo-docs` |
| Backend/API/security | `backend-architecture`, `security-vulnerability-mitigation`, `t3mp3st`, `website-compliance` |
| Search visibility | `technical-seo` for crawl/index infrastructure; `ai-search-optimization` for retrieval, citation, and answer-ready content |
| Agent workflow/delegation | `agent-delegation`, `advisor` (Herdr Pi Astra high second opinion), `workflow-1` (plan/review here; Grok 4.5 Pi implementer over intercom), `verification-loop`, `testing-strategies` |
| Pi configuration, recovery, and learning state | `pi-system-maintenance`; use `update-pi-extensions` only for package updates |
| Code quality/review | `testing-strategies`, `dead-code-detector`, `thermo-nuclear-review`, `thermo-nuclear-code-quality-review` |
| GitHub pull requests | `pull-request` |
| Research/docs/search | `search-first`, `find-skills`, `fetch-tweet`, `islam-wiki` (`hadith-grading`, `icma`, `turath-research`) |
| Instagram logged-out OSINT (profile meta, comments by handle) | `instagram-osint` |
| Remove AI writing patterns from prose | `humanizer` |
| Islamic research (hadith/ICMA/turath) | `islam-wiki` → `hadith-grading`, `icma`, or `turath-research` |
| Browser automation | `pinchtab` preferred; `playwright-browser` only when explicitly requested or PinchTab is unavailable |
| WhatsApp read (desktop DB) / send (Web) | `whatsapp` |
| Redwood board CLI | `redwood-founders` (via `redwood` CLI / repo skill) |
| Redwood build-weekend Luma RSVP | `redwood-luma-rsvp` |
| Job search / cold email outreach (Himalaya; listings as leads only) | `job-apply` |
| Extract website DESIGN.md | `extract-design-md` |
| Full-clone a public website (Ditto) | `ditto-clone` |
| HAR → shareable site CLI (no public API) | `har-cli` |
| Thinking/decision capture / skill authoring | `grill-me`, `decision-capture`, `effective-agent-skills` |
| Architecture/docs/memory | `cartographer`, `architecture-decision-records`, `continuous-learning-v2`, `strategic-compact` |
| ShipSwift components/features (opt-in) | `shipswift-recipes` only when user names ShipSwift/recipes |
| Releases/updates | `electron-app-release`, `update-agents` |
| Pi package authoring | `create-pi-package` |
| Mosque/prayer workflows | `create-mwhs-khutbah`, `extract-mosque-prayer-times`, `extract-mosque-pdf-vision` |
| Quran revision / muraja'ah sessions | `quran-revision` (local Al Muraja'ah CLI coach; phone for circulation) |
| AI video production (edit footage, Seedance prompts, motion slots) | `video-production` → `video-use`, `seedance` |
| 15s sound-off social/feed product ad | `social-ad-15s` (routed from `hyperframes` as `/social-ad-15s`) |
| Word-timed motion B-roll on talking-head | `motion-broll` (routed from `hyperframes` as `/motion-broll`) |
| Free macOS disk space (dry-run then tiered clean) | `mac-cleanup` |

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
| `thermos` | Run `thermo-nuclear-review` and `thermo-nuclear-code-quality-review`, then synthesize findings |
| `herdr-delegate` | native Herdr skill / native subagents |
| `ios-simulator-browser` | disabled stub; use `ios-debugger-agent` (explicit name only) |
| `hadith-grading`, `turath-research`, `icma` (top-level) | `islam-wiki/hadith-grading`, `islam-wiki/turath-research`, `islam-wiki/icma` |
| `video-use`, `seedance` (top-level) | `video-production/video-use`, `video-production/seedance` |

## Boundaries

- Prefer extending an existing skill over creating a new near-duplicate.
- Keep skill-specific implementation details inside that skill folder.
- Do not edit `.system/` unless the task explicitly targets system skills.

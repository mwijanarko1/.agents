---
name: ios-development
description: >
  Local-architecture-first Swift/iOS platform baseline for .swift and Xcode projects:
  feature layout, MVVM/@Observable, DI, SPM, security defaults. Not a specialist audit.
  Hand off concurrency, SwiftUI review, SwiftData, testing, and App Store work to specialists.
---

# iOS Development (platform baseline)

Default standards for native Swift/iOS app structure. Prefer the smallest change that fits the existing project layout.

## Project structure

- **Feature-first**, not file-type folders:

```text
Sources/
├── App/                 # Entry, configuration
├── Core/                # Shared extensions, network, design system
└── Features/
    └── Auth/
        ├── Views/
        ├── ViewModels/
        └── Services/
```

- **MVVM**: Views declarative (no business logic); ViewModels `@Observable`; Services stateless structs/actors for I/O.
- **DI**: Protocol-based injection. Avoid `.shared` singletons for logic/services.

## Swift baseline

- Prefer `async`/`await` over completion handlers for one-shot async work; `@MainActor` for UI-facing types.
- Prefer `@Observable` over `ObservableObject`/`@Published`.
- Prefer `struct`/`enum`; `class` only for identity (ViewModels, store owners).
- No force-unwrap outside IBOutlets/tests; use `guard let` / `if let` / `??`.
- SPM only (no CocoaPods/Carthage). Pin versions or minor ranges.
- Secrets in Keychain, not `UserDefaults`. Prefer `Logger`/`OSLog` over `print` in production paths.

## SwiftUI baseline (structure only)

- Keep `body` small; extract subviews past ~150 lines.
- `#Preview` macro (not `PreviewProvider`).
- `@State` / `@Binding` / `@Environment` for local UI and ambient deps.
- Lists: `List` / `LazyVStack`; models `Identifiable` (avoid `id: \.self` unless static unique data).

## Specialist handoffs

| Need | Skill |
|------|--------|
| SwiftUI audit, HIG, a11y, view correctness | `swiftui-pro` |
| Actors, Sendable, Task, isolation | `swift-concurrency-pro` |
| SwiftData / CloudKit | `swiftdata-pro` |
| Swift Testing write/review | `swift-testing-pro` |
| App Store / privacy / preflight | `ios-app-store-compliance` |
| ShipSwift recipes (explicit opt-in) | `shipswift-recipes` |
| App Intents / system surfaces | `ios-app-intents` |
| Simulator debug (XcodeBuildMCP) | `ios-debugger-agent` |
| Liquid Glass / UI patterns / view split | plugin SwiftUI skills |

Do not load specialists by default; load when the task matches.

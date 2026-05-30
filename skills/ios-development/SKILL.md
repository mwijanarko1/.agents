---
name: ios-development
description: Mobile app development standards for Swift (iOS).
---

# Mobile Development

## Swift Development Guidelines

### Project Structure & Architecture
- **Feature-First Organization:** Do not group by file type (Views, Models). Group by Feature.
  ```text
  Sources/
  ├── App/                 # App entry point, Configuration
  ├── Core/                # Shared extensions, Network layer, Design System
  ├── Features/
  │   ├── Auth/
  │   │   ├── Views/
  │   │   ├── ViewModels/
  │   │   └── Services/
  │   └── Dashboard/
  ```
- **Pattern:** Use **MVVM** (Model-View-ViewModel) for standard flows.
  - **Views:** Declarative, dumb components. No business logic.
  - **ViewModels:** `@Observable` classes. Handle state, user intents, and calls to services.
  - **Services:** Stateless structs or actors. Handle networking and DB logic.
- **Dependency Injection:** Use Protocol-based dependency injection. Avoid global Singletons (`.shared`) for Logic/Services to ensure testability.

### Modern Swift Syntax (Swift 6+)
- **Concurrency:**
  - **Strictly enforce `async`/`await`.** Do NOT use completion handlers (`@escaping (Result) -> Void`) or Combine for one-shot async tasks.
  - **Actors:** Use `actor` for shared mutable state to prevent data races.
  - **Main Thread:** Annotate UI-facing classes/functions with `@MainActor`.
- **Observation:**
  - Use the **`@Observable` macro** (Observation framework) over `ObservableObject`/`@Published`.
  - Prefer `let` constants. Use `var` only when mutation is required.
- **Value Types:** Default to `struct` and `enum`. Use `class` only for identity-based types (ViewModels, Database Managers).
- **Optionals:**
  - **Ban Force Unwrapping:** Never use `!` (except for `IBOutlets` or Unit Tests).
  - Use `guard let` for early exits or `if let` for scope-specific access.
  - Use `??` (nil coalescing) to provide default values.

### SwiftUI Guidelines
- **Views:**
  - Keep `body` clean. Extract sub-views if a View exceeds ~150 lines.
  - Use `@ViewBuilder` for conditional UI logic within the body.
- **Previews:** Use the **`#Preview` macro** (Swift 5.9+). Do not use `PreviewProvider` structs.
- **State Management:**
  - `@State`: For private, ephemeral UI state (e.g., toggle isExpanded).
  - `@Binding`: For passing write access to a child view.
  - `@Environment`: For global dependencies (e.g., Theme, AuthState).
- **Modifiers:**
  - Create custom `ViewModifier`s for repetitive styling.
  - Order matters: Apply layout modifiers (padding, frame) *before* background/border modifiers.

### Performance Optimization (Swift)
- **Lists:**
  - Always use `LazyVStack` or `List` for collections.
  - Ensure all data models conform to `Identifiable`. Never use `id: \.self` unless the data is truly static and unique.
- **Images:** Use `AsyncImage` with caching, or third-party libraries (e.g., Nuke) if aggressive caching is needed.
- **Computations:** Move heavy computations off the Main Actor using `Task.detached` or `nonisolated`.

### Testing (Swift Testing)
- **Framework:** Use **Swift Testing** (`import Testing`) over XCTest for new code.
- **Structure:**
  - Use `@Test` macro.
  - Use `#expect(...)` for assertions.
- **Mocking:**
  - Create `MockService` structs implementing the same Protocol as the real service.
  - Inject mocks into ViewModels during initialization.
- **Scope:**
  - **Unit:** Test ViewModels (State changes) and Services (Parsing).
  - **Snapshot:** Use `Point-Free SnapshotTesting` for complex UI layouts (optional).

### Dependency Management
- **Standard:** Use **Swift Package Manager (SPM)** exclusively.
- **Legacy:** Do not use CocoaPods or Carthage.
- **Versioning:** Pin packages to specific versions or minor ranges (e.g., `from: "2.1.0"`).

### Code Style & Formatting (Swift)
- **Linter:** Enforce **SwiftLint** with strict rules.
- **Naming:**
  - **Generic Types:** `T`, `U` for simple generics; `Element`, `Response` for descriptive ones.
  - **Protocol Naming:** Use `Service` suffix (e.g., `AuthService`) or `able` suffix (e.g., `Codable`).
- **Extensions:**
  - Use extensions to separate protocol conformance (`extension MyView: Equatable`).
  - Use extensions to group standard library enhancements (`extension String`).

### Security (Swift)
- **Storage:** NEVER store sensitive data (Tokens, Passwords) in `UserDefaults`. Use **Keychain** (via `Security` framework or a wrapper like `KeychainAccess`).
- **Networking:** Implement SSL Pinning for high-security apps.
- **Logs:** Strip sensitive data from console logs in Release builds. Use the `OSLog` framework (Logger), not `print()`.

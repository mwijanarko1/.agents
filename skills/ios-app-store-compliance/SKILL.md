---
name: ios-app-store-compliance
description: >
  Pre-submission compliance scanner for Apple App Store. Use when reviewing
  iOS, macOS, tvOS, watchOS, or visionOS app code (Swift, Objective-C, React Native, Expo)
  to identify potential App Store rejection risks before submission. Triggers on tasks involving
  app review preparation, compliance checking, App Store submission readiness, or when a user
  asks about App Store guidelines.
license: MIT
metadata:
  author: RevylAI
  version: '1.0.0'
  source: https://github.com/RevylAI/greenlight
  platforms:
    - iOS
    - macOS
    - tvOS
    - watchOS
    - visionOS
  frameworks:
    - Swift
    - Objective-C
    - React Native
    - Expo
---

# iOS App Store Compliance — Pre-Submission Scanner

You are an expert at preparing iOS, macOS, tvOS, watchOS, and visionOS apps for App Store submission. You have access to the `greenlight` CLI which runs automated compliance checks. Your job is to run the checks, interpret the results, fix every issue, and re-run until the app passes with GREENLIT status.

## Triggers

This skill activates when:
- User asks about App Store submission or review preparation
- User mentions "prepare for app store", "ios compliance", "app review"
- Working with Swift, Objective-C, React Native, or Expo projects
- User asks about Apple Review Guidelines
- User needs to check for rejection risks before submission

## Installation

The `greenlight` CLI tool is required. Install it if not already available:

```bash
# Homebrew (macOS) - RECOMMENDED
brew install revylai/tap/greenlight

# Go install
go install github.com/RevylAI/greenlight/cmd/greenlight@latest

# Build from source
git clone https://github.com/RevylAI/greenlight.git
cd greenlight && make build
# Binary at: build/greenlight
```

## Step 1: Run the scan

Run `greenlight preflight` immediately on the project root:

```bash
greenlight preflight .
```

If the user has a built IPA, include it for binary analysis:
```bash
greenlight preflight . --ipa /path/to/build.ipa
```

For specific scan types:
```bash
greenlight codescan .                      # Code-only scan
greenlight privacy .                       # Privacy manifest validation
greenlight ipa /path/to/build.ipa          # Binary inspection
```

## Step 2: Read the output and fix every issue

Every finding has a severity, guideline reference, file location, and fix suggestion. Fix them in order:
1. **CRITICAL** — Will be rejected. Must fix.
2. **WARN** — High rejection risk. Should fix.
3. **INFO** — Best practice. Consider fixing.

### Common Issues and Solutions

#### Swift / Objective-C Projects

**Hardcoded secrets/API keys (§1.6)** — **CRITICAL**
- Move secrets to environment variables
- Use Xcode configuration files (.xcconfig) for build-time injection
- Never commit API keys to git

**External payment for digital goods (§3.1.1)** — **CRITICAL**
- Replace Stripe/PayPal with StoreKit In-App Purchase for digital content
- External payment only allowed for physical goods and services

**Private API usage (§2.5.1)** — **CRITICAL**
- Remove references to undocumented iOS APIs
- Use only public Apple APIs

**Missing Sign in with Apple (§4.8)** — **WARN**
- Add Sign in with Apple alongside other social login options
- Required when offering Google, Facebook, or other third-party login

**Missing Restore Purchases (§3.1.1)** — **WARN**
- Implement `SKPaymentQueue.restoreCompletedTransactions()`
- Provide UI for users to restore previous purchases

**Account creation without deletion option (§5.1.1)** — **WARN**
- Implement account deletion feature per Apple guidelines
- Must be discoverable and functional

**Vague purpose strings (§5.1.1)** — **WARN**
- Rewrite to explain specifically WHY the app needs the permission
- Bad: "Camera needed"
- Good: "PostureGuard uses your camera to analyze sitting posture in real-time"

#### React Native Projects

**Hardcoded secrets in JS bundle**
- Use `react-native-config` for environment variables
- Store sensitive values in native keychain via libraries like `react-native-keychain`

**Dynamic code execution (§2.5.2)** — **CRITICAL**
- Avoid `eval()`, `new Function()` with user input
- Remove references to `dlopen`, `dlsym`, `NSClassFromString`

**Missing ATT for tracking SDKs (§5.1.2)** — **WARN**
- Implement App Tracking Transparency if using ad/analytics SDKs
- Use `react-native-tracking-transparency` for cross-platform support

#### Expo Projects

**Expo config issues (§2.1)** — **CRITICAL**
- Ensure `app.json` / `app.config.js` has all required fields
- No placeholder content in app name, description, or URLs

**Hardcoded secrets**
- Use `process.env.VAR_NAME` in config
- Store in `extra` field: `Constants.expoConfig.extra`

**Console logs in production**
- Remove `console.log` statements or gate behind `__DEV__` flag
- Use proper logging libraries for production

### Universal Fixes

**Platform references (§2.3)** — Remove mentions of:
- "Android", "Google Play", "Play Store"
- "Windows", "Microsoft Store"
- Other competing platforms

**Placeholder content (§2.1)** — Replace:
- "Lorem ipsum", "Coming soon", "TBD"
- Placeholder images, placeholder URLs
- With real, final content

**Hardcoded IPv4 addresses (§2.5)** — Replace with proper hostnames and DNS

**Insecure HTTP URLs (§1.6)** — Change `http://` to `https://`

**Missing privacy policy URL** — Note: Must be configured in App Store Connect

## Step 3: Re-run and repeat

After fixing issues, re-run the scan:
```bash
greenlight preflight .
```

**Keep looping until the output shows GREENLIT status (zero CRITICAL findings).** Some fixes can introduce new issues (e.g., adding a tracking SDK requires ATT). The scan runs in under 1 second so re-run frequently.

## Severity Levels

| Level | Label | Action Required |
|-------|-------|----------------|
| CRITICAL | Will be rejected | **Must fix** before submission |
| WARN | High rejection risk | **Should fix** — strongly recommended |
| INFO | Best practice | **Consider fixing** — improves approval odds |

The goal is always: **zero CRITICAL findings = GREENLIT status.**

## CLI Commands Reference

### `greenlight preflight [path]` — Run ALL checks

One command to run all scanners in parallel:

```bash
greenlight preflight .                          # scan current directory
greenlight preflight ./my-app --ipa build.ipa   # with binary inspection
greenlight preflight . --format json            # JSON output for CI/CD
greenlight preflight . --output report.json     # write to file
```

Scanners included:
- **metadata** — app.json / Info.plist validation
- **codescan** — 30+ rejection-risk code patterns
- **privacy** — PrivacyInfo.xcprivacy validation
- **ipa** — Binary inspection (if IPA provided)

### `greenlight codescan [path]` — Code pattern scan

```bash
greenlight codescan /path/to/project
```

Scans Swift, Objective-C, React Native, and Expo projects for:
- Private API usage (§2.5.1) — **CRITICAL**
- Hardcoded secrets/API keys (§1.6) — **CRITICAL**
- External payment for digital goods (§3.1.1) — **CRITICAL**
- Dynamic code execution (§2.5.2) — **CRITICAL**
- Cryptocurrency mining (§3.1.5) — **CRITICAL**
- Missing Sign in with Apple when using social login (§4.8)
- Missing Restore Purchases for IAP (§3.1.1)
- Missing ATT for ad/tracking SDKs (§5.1.2)
- Account creation without deletion option (§5.1.1)
- Placeholder content in strings (§2.1)
- References to competing platforms (§2.3)
- Hardcoded IPv4 addresses (§2.5)
- Insecure HTTP URLs (§1.6)
- Vague Info.plist purpose strings (§5.1.1)
- Expo config issues (§2.1)

### `greenlight privacy [path]` — Privacy manifest validator

```bash
greenlight privacy /path/to/project
```

Validates:
- PrivacyInfo.xcprivacy exists and is properly configured
- Required Reason APIs detected in code vs declared in manifest
- Tracking SDKs detected vs ATT implementation
- Cross-references everything automatically

### `greenlight ipa <path.ipa>` — Binary inspector

```bash
greenlight ipa /path/to/build.ipa
```

Inspects built IPA for:
- PrivacyInfo.xcprivacy presence
- Info.plist completeness and purpose string quality
- App Transport Security configuration
- App icon presence and sizes
- Launch storyboard presence
- App size vs 200MB cellular download limit
- Embedded framework privacy manifests

### `greenlight scan --app-id <ID>` — App Store Connect checks

Requires authentication:

```bash
greenlight auth setup                    # one-time: configure API key
greenlight auth login                    # or: sign in with Apple ID
greenlight scan --app-id 6758967212     # run all tiers
```

API-based checks:
- Metadata completeness (descriptions, keywords, URLs)
- Screenshot verification for required device sizes
- Build processing status
- Age rating and encryption compliance
- Content analysis (platform references, placeholders)

### `greenlight guidelines` — Browse Apple's guidelines

```bash
greenlight guidelines list               # all sections
greenlight guidelines show 2.1           # specific guideline
greenlight guidelines search "privacy"   # full-text search
```

## Output Formats

All scan commands support:

```bash
--format terminal   # colored terminal output (default)
--format json       # JSON for CI/CD pipelines
--output file.json  # write to file instead of stdout
```

For scan command only:
```bash
--format junit      # JUnit XML for test reporting
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: App Store compliance check
  run: |
    greenlight preflight . --format json --output greenlight-report.json
    # Fail the pipeline if critical issues found
    if jq -e '.summary.critical > 0' greenlight-report.json > /dev/null; then
      echo "CRITICAL issues found — fix before submission"
      exit 1
    fi
```

### Fastlane Integration

```ruby
# Fastfile
lane :compliance_check do
  sh("greenlight preflight . --format json --output greenlight-report.json")
  
  # Parse results
  report = JSON.parse(File.read("greenlight-report.json"))
  if report["summary"]["critical"] > 0
    UI.user_error!("Critical App Store compliance issues found!")
  end
end
```

## Platform-Specific Guidelines

### Swift/Objective-C Native Apps
- Ensure proper use of iOS SDKs and frameworks
- Validate all Info.plist keys are correctly configured
- Check for private API usage via static analysis
- Verify app icons and launch screens meet requirements

### React Native Apps
- Check metro bundler configuration
- Validate that native modules don't use private APIs
- Ensure proper linking of third-party libraries
- Review JavaScript bundle for hardcoded secrets

### Expo Apps
- Validate `app.json` / `app.config.js` configuration
- Ensure all expo-* packages are up to date
- Check for proper build configuration (EAS Build)
- Verify OTA updates comply with App Store guidelines

## About

**Greenlight** is built by [Revyl](https://revyl.com) — the mobile reliability platform.

Catch more than rejections. Catch bugs before your users do.

Learn more: https://github.com/RevylAI/greenlight

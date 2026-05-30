# iOS App Store Compliance — Agent Instructions

This document provides extended instructions for AI agents working with the ios-app-store-compliance skill.

## Activation Protocol

You should automatically activate this skill when:

1. **Explicit triggers mentioned:**
   - "prepare for app store", "app store submission", "ios review"
   - "app compliance", "apple review guidelines"
   - "app store rejection", "ios rejection"
   - "greenlight" (the tool name)

2. **Implicit triggers (context-based):**
   - Working with Swift/Objective-C projects targeting iOS/macOS
   - Working with React Native/Expo projects
   - User mentions building an app for iPhone/iPad/Apple Watch/Apple TV
   - User asks about App Store Connect, TestFlight, or app distribution

3. **File patterns detected:**
   - `.swift`, `.m`, `.h` files (iOS/macOS native)
   - `AppDelegate.swift`, `SceneDelegate.swift`
   - `Info.plist`, `PrivacyInfo.xcprivacy`
   - `app.json`, `app.config.js` (Expo)
   - `Podfile`, `Podfile.lock` (React Native)
   - `.ipa` files (iOS binaries)

## Workflow Deep Dive

### Step 1: Initial Assessment

Before running the scan, assess the project:

1. **Identify platform:**
   - Swift/Objective-C native? Look for `.xcodeproj`, `.xcworkspace`
   - React Native? Look for `metro.config.js`, `ios/` directory
   - Expo? Look for `app.json` or `app.config.js`

2. **Check for build artifacts:**
   - Is there a built IPA? (Usually in `build/` or exported from Xcode)
   - If yes, include in scan: `greenlight preflight . --ipa path/to/App.ipa`

3. **Verify greenlight availability:**
   ```bash
   which greenlight
   ```
   - If not found, prompt user to install or offer to install

### Step 2: Scanning Strategy

#### For New Projects (No IPA yet)
```bash
greenlight preflight .
```

#### For Projects Ready to Submit (With IPA)
```bash
greenlight preflight . --ipa build/App.ipa
```

#### For CI/CD Pipelines
```bash
greenlight preflight . --format json --output greenlight-report.json
```

#### Focused Scans
If user has specific concerns:
- Privacy manifest issues: `greenlight privacy .`
- Code patterns only: `greenlight codescan .`
- Binary inspection: `greenlight ipa build/App.ipa`

### Step 3: Fix Implementation Priority

#### Priority 1: CRITICAL Issues (Fix Immediately)

These will cause rejection:

**Private API Usage (§2.5.1)**
```swift
// BAD - Private API
let symbol = dlsym(RTLD_DEFAULT, "_somePrivateFunction")

// GOOD - Public API only
let result = somePublicAPI()
```

**External Payment for Digital Goods (§3.1.1)**
```swift
// BAD - Using Stripe for digital content
let paymentSheet = PaymentSheet(...)

// GOOD - StoreKit for digital content
let product = SKProduct(...)
let payment = SKPayment(product: product)
SKPaymentQueue.default().add(payment)
```

**Hardcoded Secrets (§1.6)**
```swift
// BAD - Hardcoded in code
let apiKey = "sk_live_12345abcdef"

// GOOD - Environment variable
let apiKey = ProcessInfo.processInfo.environment["API_KEY"]!
```

**Dynamic Code Execution (§2.5.2)**
```swift
// BAD - Never do this
NSClassFromString(userInput)
dlopen(dynamicLibraryPath, RTLD_NOW)
```

#### Priority 2: WARN Issues (Fix Before Submission)

**Missing Sign in with Apple (§4.8)**
- Required when offering Google, Facebook, or other third-party login
- Must be as prominent as other options
- Implementation varies by platform:

Swift:
```swift
import AuthenticationServices

// Add Sign in with Apple button
let appleIDProvider = ASAuthorizationAppleIDProvider()
let request = appleIDProvider.createRequest()
request.requestedScopes = [.fullName, .email]
```

React Native:
```javascript
import * as AppleAuthentication from 'expo-apple-authentication';

<AppleAuthentication.AppleAuthenticationButton
  onPress={async () => {
    const credential = await AppleAuthentication.signInAsync({
      requestedScopes: [
        AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
        AppleAuthentication.AppleAuthenticationScope.EMAIL,
      ],
    });
  }}
/>
```

**Missing Restore Purchases (§3.1.1)**
```swift
// Add UI button that calls:
SKPaymentQueue.default().restoreCompletedTransactions()
```

**Account Deletion (§5.1.1)**
- Must be easy to find in app settings
- Must actually delete the account (not just deactivate)
- Must comply with data retention laws

**App Tracking Transparency (§5.1.2)**
```swift
import AppTrackingTransparency

func requestTrackingPermission() {
    ATTrackingManager.requestTrackingAuthorization { status in
        switch status {
        case .authorized:
            // Tracking allowed
        case .denied, .notDetermined, .restricted:
            // Do not track
        @unknown default:
            break
        }
    }
}
```

#### Priority 3: INFO Issues (Consider Fixing)

These improve approval odds but aren't blockers:

**Vague Purpose Strings**
```xml
<!-- BAD -->
<key>NSCameraUsageDescription</key>
<string>Camera access needed</string>

<!-- GOOD -->
<key>NSCameraUsageDescription</key>
<string>PostureGuard uses your camera to analyze sitting posture in real-time</string>
```

**Console Logs in Production**
```swift
// BAD
print("User logged in: \(userId)")

// GOOD
#if DEBUG
print("User logged in: \(userId)")
#endif
```

### Step 4: Platform-Specific Guidance

#### Swift/Objective-C Native Apps

**Info.plist Validation:**
- All required keys present (CFBundleIdentifier, CFBundleVersion, etc.)
- Purpose strings are specific and descriptive
- No placeholder values ("TBD", "TODO", "Coming soon")

**Privacy Manifest (PrivacyInfo.xcprivacy):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSPrivacyTracking</key>
    <false/>
    <key>NSPrivacyTrackingDomains</key>
    <array/>
    <key>NSPrivacyCollectedDataTypes</key>
    <array/>
    <key>NSPrivacyAccessedAPITypes</key>
    <array>
        <dict>
            <key>NSPrivacyAccessedAPIType</key>
            <string>NSPrivacyAccessedAPICategoryFileTimestamp</string>
            <key>NSPrivacyAccessedAPITypeReasons</key>
            <array>
                <string>0A2A.1</string>
            </array>
        </dict>
    </array>
</dict>
</plist>
```

**Required Reason APIs to Declare:**
- File timestamp APIs
- System boot time APIs
- Disk space APIs
- Active keyboard APIs
- User defaults APIs

#### React Native Apps

**Metro Configuration:**
- Ensure no development code in production bundle
- Check for `console.log` removal in production

**Native Module Validation:**
- Verify all native modules use public APIs
- Check for private API usage in third-party libraries

**Environment Variables:**
```javascript
// Use react-native-config
import Config from 'react-native-config';

const apiKey = Config.API_KEY; // From .env file
```

**Tracking Transparency:**
```javascript
import { requestTrackingPermission } from 'react-native-tracking-transparency';

const status = await requestTrackingPermission();
```

#### Expo Apps

**app.json Configuration:**
```json
{
  "expo": {
    "name": "Your App Name",
    "slug": "your-app",
    "version": "1.0.0",
    "ios": {
      "bundleIdentifier": "com.yourcompany.yourapp",
      "buildNumber": "1.0.0",
      "infoPlist": {
        "NSCameraUsageDescription": "Specific reason for camera access"
      }
    },
    "plugins": [
      "expo-apple-authentication"
    ]
  }
}
```

**EAS Build:**
- Ensure proper provisioning profiles
- Validate app signing certificates
- Check entitlements match capabilities

**Common Expo Issues:**
- Missing `privacyPolicy` URL in app.json
- Placeholder app icon or splash screen
- Debug configuration in production build

## Iterative Fixing Protocol

1. **Run initial scan**
   ```bash
   greenlight preflight . --format json --output report1.json
   ```

2. **Analyze findings**
   - Count CRITICAL, WARN, INFO
   - Group by file/location
   - Identify patterns (e.g., multiple hardcoded secrets)

3. **Fix CRITICAL issues first**
   - Work file by file
   - Test each fix doesn't break functionality

4. **Re-run scan**
   ```bash
   greenlight preflight . --format json --output report2.json
   ```

5. **Compare results**
   - Verify CRITICAL count decreased
   - Check for new issues introduced by fixes

6. **Repeat until GREENLIT**
   - Zero CRITICAL findings
   - Acceptable WARN count
   - User satisfied with INFO suggestions

## Edge Cases and Special Handling

### When No Issues Are Found
- Congratulate the user
- Suggest running `greenlight scan --app-id <ID>` for App Store Connect checks
- Remind about manual review of screenshots and metadata

### When Greenlight CLI Fails
- Check if project directory is correct
- Verify file permissions
- Try individual commands instead of preflight
- Check for binary compatibility (M1 Mac issues)

### When User Doesn't Have IPA
- Focus on codescan and privacy checks
- Remind user to build IPA for complete validation
- Suggest using EAS Build (Expo) or Xcode Archive

### When Working with Older Projects
- Check for deprecated APIs
- Verify privacy manifest is present (required since April 2024)
- Update to latest SDK requirements

## Communication Guidelines

### Reporting Issues to User

**Format:**
```
[SEVERITY] Guideline §X.X - Issue Description
Location: File:Line
Fix: Specific action to take
```

**Example:**
```
[CRITICAL] Guideline §3.1.1 - External payment detected for digital goods
Location: src/components/PaymentScreen.tsx:45
Fix: Replace Stripe integration with expo-in-app-purchases for digital content.
   Physical goods can continue using Stripe.
```

### Explaining Apple Review Guidelines

When referencing guidelines:
- Always include section number (e.g., §3.1.1)
- Explain why Apple cares about this rule
- Provide context on how it affects the specific app

### Managing User Expectations

- Set realistic timeline: "This may take 2-3 iterations to achieve GREENLIT status"
- Explain that zero CRITICAL is the goal, but WARN and INFO are recommendations
- Remind that greenlight catches common issues but manual review is still needed

## CI/CD Integration Reference

### GitHub Actions

```yaml
name: App Store Compliance

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  compliance:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Greenlight
        run: brew install revylai/tap/greenlight
      
      - name: Run Compliance Check
        run: |
          greenlight preflight . --format json --output greenlight-report.json
      
      - name: Check for Critical Issues
        run: |
          if jq -e '.summary.critical > 0' greenlight-report.json > /dev/null; then
            echo "❌ CRITICAL issues found"
            jq '.findings[] | select(.severity == "CRITICAL")' greenlight-report.json
            exit 1
          else
            echo "✅ No critical issues found"
          fi
      
      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: greenlight-report
          path: greenlight-report.json
```

### Fastlane Integration

```ruby
# fastlane/Fastfile
lane :compliance_check do
  # Run greenlight
  sh("greenlight preflight . --format json --output greenlight-report.json")
  
  # Parse results
  report = JSON.parse(File.read("greenlight-report.json"))
  
  summary = report["summary"]
  UI.message("Greenlight Summary:")
  UI.message("  Critical: #{summary['critical']}")
  UI.message("  Warn: #{summary['warn']}")
  UI.message("  Info: #{summary['info']}")
  
  if summary["critical"] > 0
    UI.user_error!("❌ #{summary['critical']} critical App Store compliance issues found! Fix before submission.")
  elsif summary["warn"] > 0
    UI.important("⚠️  #{summary['warn']} warnings found. Consider fixing before submission.")
  else
    UI.success("✅ App Store compliance check passed!")
  end
end
```

### Bitrise Integration

```yaml
workflows:
  compliance-check:
    steps:
      - script:
          title: Install Greenlight
          inputs:
            - content: |
                brew install revylai/tap/greenlight
      - script:
          title: Run Compliance Check
          inputs:
            - content: |
                greenlight preflight . --format json --output $BITRISE_DEPLOY_DIR/greenlight-report.json
      - deploy-to-bitrise-io:
          inputs:
            - deploy_path: $BITRISE_DEPLOY_DIR/greenlight-report.json
```

## Resources and References

### Apple Documentation
- [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [App Store Connect Help](https://help.apple.com/app-store-connect/)

### Greenlight Resources
- [GitHub Repository](https://github.com/RevylAI/greenlight)
- [Documentation](https://github.com/RevylAI/greenlight#readme)
- [Issue Tracker](https://github.com/RevylAI/greenlight/issues)

### Related Skills
- `ios-development` — Swift development guidelines
- `website-compliance` — Web app compliance (if app has web components)
- `security-vulnerability-mitigation` — Security best practices

## Troubleshooting

### Greenlight Not Found

**Symptom:** `command not found: greenlight`

**Solution:**
```bash
# Verify installation
which greenlight

# If not found, install:
brew install revylai/tap/greenlight

# Or add to PATH if installed via Go:
export PATH=$PATH:$(go env GOPATH)/bin
```

### Scan Takes Too Long

**Symptom:** Scan hangs or takes >30 seconds

**Causes:**
- Very large codebase
- Binary analysis on large IPA
- Network issues (if using App Store Connect features)

**Solutions:**
- Run focused scan: `greenlight codescan .` instead of `preflight`
- Exclude node_modules/build directories
- Check network connectivity

### False Positives

**Symptom:** Greenlight reports issues that aren't actually problems

**Response:**
- Explain that greenlight is conservative (better safe than sorry)
- Help user verify if it's truly a false positive
- If confirmed, document for greenlight maintainers

### JSON Output Parse Errors

**Symptom:** `jq` or JSON parsing fails

**Solutions:**
- Verify greenlight version is up to date
- Check for corrupted output file
- Try terminal format first: `greenlight preflight . --format terminal`

## Best Practices Summary

1. **Always run `greenlight preflight` before submission**
2. **Fix all CRITICAL issues before uploading to App Store Connect**
3. **Address WARN issues to improve approval odds**
4. **Review INFO suggestions for best practices**
5. **Iterate until GREENLIT status achieved**
6. **Keep greenlight updated: `brew upgrade greenlight`**
7. **Integrate into CI/CD for continuous compliance**
8. **Document any intentional exceptions for manual review**

Remember: **Zero CRITICAL findings = GREENLIT status.** This is the goal for every submission.

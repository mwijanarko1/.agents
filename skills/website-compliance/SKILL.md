---
name: website-compliance
description:
  Global website compliance best practices covering privacy, accessibility, security,
  and consumer protection. Use when auditing or building websites with user data collection,
  e-commerce features, or international traffic.
license: MIT
metadata:
  author: open-source
  version: '1.0.0'
---

# Website Compliance Skills

Comprehensive best practices for global website compliance. Contains rules across
multiple categories covering privacy, data protection, accessibility (WCAG),
security, and consumer rights.

## When to Apply

Reference these guidelines when:

- Building or auditing websites with global traffic
- Implementing data collection forms or user accounts
- Setting up e-commerce flows and checkout processes
- Configuring cookie banners and tracking scripts
- Ensuring accessibility compliance (WCAG 2.1 AA)
- Handling sensitive or children's data

## Rule Categories by Priority

| Priority | Category            | Impact   | Prefix                  |
| -------- | ------------------- | -------- | ----------------------- |
| 1        | Privacy & Data      | CRITICAL | `privacy-`              |
| 2        | Cookies & Tracking  | CRITICAL | `cookies-`              |
| 3        | Security            | HIGH     | `security-`             |
| 4        | Accessibility       | HIGH     | `a11y-`                 |
| 5        | Consumer Protection | MEDIUM   | `consumer-`             |
| 6        | Governance          | LOW      | `governance-`           |

## Quick Reference

### 1. Privacy & Data (CRITICAL)

- `privacy-policy-link` - Accessible privacy policy link in footer
- `privacy-data-collection` - Transparent data collection disclosure
- `privacy-ccpa-do-not-sell` - CCPA "Do Not Sell" mechanism for US traffic
- `privacy-gdpr-rights` - User rights workflow (access, delete, portability)
- `privacy-children-coppa` - COPPA compliance for under-13 users

### 2. Cookies & Tracking (CRITICAL)

- `cookies-consent-banner` - Granular consent banner (no forced acceptance)
- `cookies-categorization` - Categorize cookies (necessary, analytics, marketing)
- `cookies-reject-button` - Easy "Reject All" option
- `cookies-policy-table` - Detailed cookie table with durations and providers

### 3. Security (HIGH)

- `security-https-everywhere` - Enforce HTTPS and HSTS
- `security-headers` - Implement CSP, X-Frame-Options, X-Content-Type-Options
- `security-admin-protection` - Protect admin areas with 2FA and IP allowlists
- `security-sensitive-data` - Encrypt sensitive data (PII, health, religion)

### 4. Accessibility (HIGH)

- `a11y-color-contrast` - Ensure WCAG 2.1 AA contrast ratio (≥ 4.5:1)
- `a11y-keyboard-nav` - Full keyboard navigability (no traps)
- `a11y-alt-text` - Descriptive alt text for all images
- `a11y-form-labels` - Explicit labels and error messages for forms
- `a11y-semantic-html` - Use semantic headings and ARIA landmarks

### 5. Consumer Protection (MEDIUM)

- `consumer-company-info` - Clear legal name, address, and contact info
- `consumer-pricing-transparency` - Clear pricing, taxes, and currency
- `consumer-refund-policy` - Explicit refund and return policy details
- `consumer-terms-link` - Accessible Terms & Conditions link

### 6. Governance (LOW)

- `governance-jurisdiction-map` - Map target jurisdictions to legal requirements
- `governance-vendor-contracts` - Ensure vendor DPAs are signed
- `governance-staff-training` - Regular privacy and compliance training

## How to Use

Read individual rule files for detailed explanations and code examples:

```
rules/privacy-policy-link.md
rules/cookies-consent-banner.md
```

Each rule file contains:

- Brief explanation of why it matters
- Incorrect code example with explanation
- Correct code example with explanation
- Additional context and references

## Full Compiled Document

For the complete guide with all rules expanded: `AGENTS.md`

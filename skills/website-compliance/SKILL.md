---
name: website-compliance
description: Global website compliance best practices covering privacy, accessibility, security, and consumer protection. Use when auditing or building websites with user data collection, e-commerce features, or international traffic.
---

# Website Compliance

Audit/build checklist for privacy, accessibility, security basics, and consumer-facing sites. Not legal advice — flag gaps for human counsel when unsure.

## Workflow

1. **Scope** — regions, data collected, payments, cookies/trackers, user-generated content.
2. **Inventory** — forms, analytics, third parties, auth, stored PII.
3. **Audit** against the gates below.
4. **Fix** product-owned gaps; document intentional deferrals.
5. **Verify** with page checks + network/cookie inspection when relevant.

## Privacy

- Clear privacy notice linked from footer and collection points.
- Lawful basis / purpose stated before collection where required.
- Cookie/consent banner when non-essential trackers run; honor reject.
- Data subject paths: access, delete, export — document or implement.
- Minimize PII; retention limits; no surprise third-party sharing.

## Accessibility (baseline)

- Keyboard reachability for interactive controls; visible focus.
- Labels on inputs; alt text for meaningful images.
- Color contrast AA for text; do not rely on color alone.
- Landmarks/headings in order; live regions for async errors when needed.

## Security (site surface)

- HTTPS everywhere; secure cookies (`Secure`, `HttpOnly`, `SameSite` as appropriate).
- CSRF protection for cookie-auth mutations.
- No secrets in client bundles; CSP where feasible.
- File upload type/size limits and auth checks.

## Consumer / e-commerce

- Accurate pricing, shipping, refund surfaces before payment.
- Clear identity of the business operator.
- Age gates only when product/law requires.

## Output

```
[critical|major|minor] area — location
  gap / required fix
```

Pair with `technical-seo` for crawl/index and `security-vulnerability-mitigation` for deep vuln work.

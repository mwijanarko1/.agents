---
name: t3mp3st
description: Use T3MP3ST for authorized, evidence-first security research workflows, local lab demos, and safe setup guidance. Different from security-vulnerability-mitigation because it wraps an external offensive-security framework rather than general secure-coding advice.
---

# T3MP3ST

Use this only for authorized targets: owned systems, labs, bug-bounty scope, or explicit written permission.

## Before running anything

1. Confirm the target and allowed action class in plain text.
2. Prefer local-safe commands first: `npm run doctor`, `npm run verify-claims`, `npm run arsenal:smoke`, `npm run field:drill`.
3. Do not run active network scans or exploit tooling unless the user explicitly names the in-scope target and approves that action.
4. Do not store secrets, recovered credentials, tokens, or private keys in evidence.

## Setup path

```bash
git clone https://github.com/elder-plinius/T3MP3ST.git
cd T3MP3ST
npm install
npm run doctor
npm run server  # UI: http://127.0.0.1:3333/ui/
```

Optional MCP server after build:

```bash
npm run build
node dist/mcp-server.js
```

## Use from an agent session

- For evaluation: inspect `README.md`, `docs/SCOPE_AND_AUTHORIZATION.md`, `docs/TEAM_PREVIEW.md`, and `docs/INSTALL_MATRIX.md`.
- For a preview run: start the server, use preflight/sync arsenal/activation in the UI, then run local demos.
- For findings: require evidence, severity, reproduction steps, retest status, and remediation guidance.

## Boundaries

- Treat the upstream project as AGPL-3.0-or-later; do not vendor or modify it inside `.agents` unless the user explicitly accepts the license impact.
- Keep `.agents` integration as this routing skill unless a concrete MCP/CLI bridge is requested.
- Escalate to `security-vulnerability-mitigation` for defensive code fixes after a finding is confirmed.

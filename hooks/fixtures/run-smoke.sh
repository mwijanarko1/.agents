#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== codex dangerous =="
GUARDRAIL_TOOL=codex GUARDRAIL_EVENT=PreToolUse \
  "$ROOT/bin/codex-preflight.sh" < "$ROOT/fixtures/codex-pretool-dangerous.json"

echo
echo "== cursor safe =="
GUARDRAIL_TOOL=cursor GUARDRAIL_EVENT=beforeShellExecution \
  "$ROOT/bin/cursor-before-shell.sh" < "$ROOT/fixtures/cursor-before-shell-safe.json"

echo
echo "== cursor long running =="
GUARDRAIL_TOOL=cursor GUARDRAIL_EVENT=beforeShellExecution \
  "$ROOT/bin/cursor-before-shell.sh" < "$ROOT/fixtures/cursor-before-shell-long-running.json"

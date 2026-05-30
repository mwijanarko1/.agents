#!/usr/bin/env bash
set -euo pipefail

HOOKS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

sync_peer_roots() {
  python3 "/Users/mikhail/.agents/scripts/sync_peer_roots.py" >/dev/null
}

run_guardrail() {
  local action="$1"
  node "$HOOKS_ROOT/lib/guardrails-cli.mjs" "$action"
}

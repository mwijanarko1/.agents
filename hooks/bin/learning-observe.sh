#!/usr/bin/env bash
set -euo pipefail

AGENTS_ROOT="${AGENTS_ROOT:-$HOME/.agents}"
exec python3 "$AGENTS_ROOT/scripts/agent_learning.py" observe

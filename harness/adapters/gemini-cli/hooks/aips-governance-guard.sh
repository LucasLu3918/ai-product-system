#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"
exec env AIPS_BIN="$ROOT/bin/aips" "$PY" "$ROOT/scripts/governance_guard.py" hook --runtime gemini-cli

#!/usr/bin/env bash
set -euo pipefail

case "${AIPS_OBSERVABLE_EVENT_CAPTURE:-}" in
  1|true|TRUE|True|yes|YES|Yes|on|ON|On) ;;
  *)
    printf '%s\n' '{"decision":"allow","suppressOutput":true}'
    exit 0
    ;;
esac

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd -P)"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"
exec "$PY" "$ROOT/scripts/gemini_observable_event_capture.py" hook --config "$ROOT/config/gemini-observable-event-capture.yaml"

#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "NOTICE: bootstrap.sh is retained for backward compatibility. Prefer the public install entrypoint in docs/human/INSTALLATION.md." >&2
exec "$ROOT/bin/aips" install "$@"

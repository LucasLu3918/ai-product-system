#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${AIPS_REPO_URL:-https://github.com/LucasLu3918/ai-product-system.git}"
DEFAULT_BRANCH="${AIPS_INSTALL_BRANCH:-main}"
INSTALL_DIR="${AIPS_INSTALL_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/aips/system}"
SOURCE_CHECKOUT="${AIPS_INSTALL_SOURCE:-}"
DRY_RUN=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=true ;;
    --source-checkout)
      shift
      [ "$#" -gt 0 ] || { echo "ERROR: --source-checkout requires a path" >&2; exit 2; }
      SOURCE_CHECKOUT="$1"
      ;;
    *) echo "ERROR: unknown install option: $1" >&2; exit 2 ;;
  esac
  shift
done

require() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: required command not found: $1" >&2; exit 1; }; }
require git
require python3

if [ "$DRY_RUN" = true ]; then
  printf "AIPS install plan\nrepository=%s\nbranch=%s\ninstall_dir=%s\n" "$REPO_URL" "$DEFAULT_BRANCH" "$INSTALL_DIR"
  [ -n "$SOURCE_CHECKOUT" ] && printf "source_checkout=%s\n" "$SOURCE_CHECKOUT"
  exit 0
fi

mkdir -p "$(dirname "$INSTALL_DIR")"
if [ -e "$INSTALL_DIR" ] && [ ! -d "$INSTALL_DIR/.git" ]; then
  echo "ERROR: install path exists but is not an AIPS Git checkout: $INSTALL_DIR" >&2
  exit 1
fi

if [ ! -d "$INSTALL_DIR/.git" ]; then
  if [ -n "$SOURCE_CHECKOUT" ]; then
    [ -d "$SOURCE_CHECKOUT/.git" ] || { echo "ERROR: source checkout is not a Git repository: $SOURCE_CHECKOUT" >&2; exit 1; }
    source_head="$(git -C "$SOURCE_CHECKOUT" rev-parse HEAD)"
    git clone --quiet --local --no-checkout "$SOURCE_CHECKOUT" "$INSTALL_DIR"
    git -C "$INSTALL_DIR" checkout --quiet -B "$DEFAULT_BRANCH" "$source_head"
  else
    git clone --quiet --filter=blob:none --single-branch --branch "$DEFAULT_BRANCH" "$REPO_URL" "$INSTALL_DIR"
  fi
else
  [ -z "$(git -C "$INSTALL_DIR" status --porcelain)" ] || { echo "ERROR: existing AIPS managed checkout has local changes: $INSTALL_DIR" >&2; exit 1; }
  git -C "$INSTALL_DIR" checkout --quiet "$DEFAULT_BRANCH"
  git -C "$INSTALL_DIR" fetch --quiet origin "$DEFAULT_BRANCH"
  git -C "$INSTALL_DIR" merge --ff-only --quiet "origin/$DEFAULT_BRANCH"
fi

exec "$INSTALL_DIR/bin/aips" install

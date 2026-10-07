#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${AIPS_REPO_URL:-https://github.com/LucasLu3918/ai-product-system.git}"
INSTALL_CHANNEL="${AIPS_INSTALL_CHANNEL:-stable}"
INSTALL_BRANCH="${AIPS_INSTALL_BRANCH:-main}"
INSTALL_DIR="${AIPS_INSTALL_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/aips/system}"
SOURCE_CHECKOUT="${AIPS_INSTALL_SOURCE:-}"
DRY_RUN=false
CLI_ARGS=()
SHELL_INTEGRATION="auto"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=true ;;
    --configure-shell)
      CLI_ARGS+=("$1")
      SHELL_INTEGRATION="configure"
      ;;
    --no-configure-shell)
      CLI_ARGS+=("$1")
      SHELL_INTEGRATION="skip"
      ;;
    --source-checkout)
      shift
      [ "$#" -gt 0 ] || { echo "ERROR: --source-checkout requires a path" >&2; exit 2; }
      SOURCE_CHECKOUT="$1"
      ;;
    --channel)
      shift
      [ "$#" -gt 0 ] || { echo "ERROR: --channel requires stable or main" >&2; exit 2; }
      case "$1" in
        stable|main) INSTALL_CHANNEL="$1" ;;
        *) echo "ERROR: unsupported install channel: $1 (expected stable or main)" >&2; exit 2 ;;
      esac
      ;;
    *) echo "ERROR: unknown install option: $1" >&2; exit 2 ;;
  esac
  shift
done

require() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: required command not found: $1" >&2; exit 1; }; }
require git
require python3
require hostname

if [ -n "${AIPS_INSTALL_BRANCH:-}" ] && [ "${AIPS_INSTALL_CHANNEL+x}" != x ]; then
  INSTALL_CHANNEL="branch"
fi
case "$INSTALL_CHANNEL" in
  stable|main|branch) ;;
  *) echo "ERROR: unsupported AIPS_INSTALL_CHANNEL: $INSTALL_CHANNEL" >&2; exit 2 ;;
esac
if [ "$INSTALL_CHANNEL" = branch ]; then
  git check-ref-format --branch "$INSTALL_BRANCH" >/dev/null 2>&1 || { echo "ERROR: invalid AIPS_INSTALL_BRANCH" >&2; exit 2; }
fi

if [ "$DRY_RUN" = true ]; then
  printf "AIPS install plan\nrepository=%s\nchannel=%s\nbranch=%s\ninstall_dir=%s\nshell_integration=%s\n" "$REPO_URL" "$INSTALL_CHANNEL" "$INSTALL_BRANCH" "$INSTALL_DIR" "$SHELL_INTEGRATION"
  [ -n "$SOURCE_CHECKOUT" ] && printf "source_checkout=%s\n" "$SOURCE_CHECKOUT"
  exit 0
fi

mkdir -p "$(dirname "$INSTALL_DIR")"
LOCK_DIR="${INSTALL_DIR}.aips-lock"
LOCK_HELD=false
STAGING_DIR=""
INSTALL_TARGET="$INSTALL_DIR"

cleanup_install() {
  if [ -n "$STAGING_DIR" ] && [ -d "$STAGING_DIR" ]; then
    rm -rf "$STAGING_DIR"
  fi
  if [ "$LOCK_HELD" = true ]; then
    rm -f "$LOCK_DIR/owner"
    rmdir "$LOCK_DIR" 2>/dev/null || true
  fi
}

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  lock_owner="$LOCK_DIR/owner"
  lock_pid=""
  lock_host=""
  lock_started="unknown"
  if [ -f "$lock_owner" ]; then
    lock_pid="$(sed -n 's/^pid=//p' "$lock_owner" | head -n 1)"
    lock_host="$(sed -n 's/^host=//p' "$lock_owner" | head -n 1)"
    lock_started="$(sed -n 's/^started=//p' "$lock_owner" | head -n 1)"
  fi
  lock_state="active or unknown"
  case "$lock_pid" in
    ''|*[!0-9]*) ;;
    *)
      if [ "$lock_host" = "$(hostname)" ] && ! kill -0 "$lock_pid" 2>/dev/null; then
        lock_state="stale (owner process is not running)"
      fi
      ;;
  esac
  echo "ERROR: AIPS installer lock exists: $LOCK_DIR ($lock_state; host=${lock_host:-unknown}, pid=${lock_pid:-unknown}, started=$lock_started)." >&2
  if [ "$lock_state" = "stale (owner process is not running)" ]; then
    echo "After confirming no install/update is running, remove the stale lock directory and retry." >&2
  fi
  exit 1
fi
LOCK_HELD=true
printf 'pid=%s\nhost=%s\nstarted=%s\n' "$$" "$(hostname)" "$(date -u +%s)" > "$LOCK_DIR/owner"
trap cleanup_install EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

retry_git() {
  attempt=1
  while :; do
    if git "$@"; then
      return 0
    else
      status=$?
    fi
    if [ "$attempt" -ge 3 ]; then
      return "$status"
    fi
    echo "WARN: Git operation failed (attempt $attempt/3); retrying in 2 seconds." >&2
    sleep 2
    attempt=$((attempt + 1))
  done
}

if [ -e "$INSTALL_DIR" ] && [ ! -d "$INSTALL_DIR/.git" ]; then
  echo "ERROR: install path exists but is not an AIPS Git checkout: $INSTALL_DIR" >&2
  exit 1
fi

CLONED_NOW=false
SOURCE_CHECKOUT_CLONED_LOCALLY=false
if [ ! -d "$INSTALL_DIR/.git" ]; then
  STAGING_DIR="$(mktemp -d "${INSTALL_DIR}.aips-stage.XXXXXX")"
  INSTALL_TARGET="$STAGING_DIR"
  if [ -n "$SOURCE_CHECKOUT" ]; then
    source_root="$(git -C "$SOURCE_CHECKOUT" rev-parse --show-toplevel 2>/dev/null)" || { echo "ERROR: source checkout is not a Git worktree: $SOURCE_CHECKOUT" >&2; exit 1; }
    [ "$(cd "$SOURCE_CHECKOUT" && pwd -P)" = "$(cd "$source_root" && pwd -P)" ] || { echo "ERROR: source checkout must be the Git top level" >&2; exit 1; }
    [ -f "$SOURCE_CHECKOUT/bin/aips" ] || { echo "ERROR: source checkout has no AIPS CLI" >&2; exit 1; }
    source_head="$(git -C "$SOURCE_CHECKOUT" rev-parse HEAD)"
    retry_git clone --quiet --local --no-checkout "$SOURCE_CHECKOUT" "$INSTALL_TARGET"
    git -C "$INSTALL_TARGET" remote set-url origin "$REPO_URL"
    git -C "$INSTALL_TARGET" checkout --quiet -B "$INSTALL_BRANCH" "$source_head"
    SOURCE_CHECKOUT_CLONED_LOCALLY=true
  else
    retry_git clone --quiet --filter=blob:none --single-branch --branch "$INSTALL_BRANCH" "$REPO_URL" "$INSTALL_TARGET"
  fi
  CLONED_NOW=true
else
  [ -z "$(git -C "$INSTALL_DIR" status --porcelain)" ] || { echo "ERROR: existing AIPS managed checkout has local changes: $INSTALL_DIR" >&2; exit 1; }
  [ "$(git -C "$INSTALL_DIR" remote get-url origin)" = "$REPO_URL" ] || { echo "ERROR: existing AIPS checkout remote differs from the requested repository" >&2; exit 1; }
fi

case "$INSTALL_CHANNEL" in
  stable)
    stable_info="$(python3 "$INSTALL_TARGET/scripts/release_channel.py" resolve --remote "$REPO_URL" 2>&1)" || resolve_status=$?
    resolve_status="${resolve_status:-0}"
    if [ "$resolve_status" -ne 0 ]; then
      if [ "$resolve_status" -eq 3 ]; then
        echo "ERROR: no stable AIPS release tag exists yet; stable installation is unavailable until an approved release is published." >&2
      else
        echo "$stable_info" >&2
        echo "ERROR: stable channel resolution failed." >&2
      fi
      echo "Use --channel main only if you explicitly want the mutable development branch." >&2
      exit 1
    else
      stable_tag="${stable_info%%$'\t'*}"
      stable_sha="${stable_info#*$'\t'}"
      retry_git -C "$INSTALL_TARGET" fetch --quiet origin "refs/tags/$stable_tag:refs/tags/$stable_tag"
      python3 "$INSTALL_TARGET/scripts/release_channel.py" verify --repository "$INSTALL_TARGET" --tag "$stable_tag" --expected-sha "$stable_sha"
      git -C "$INSTALL_TARGET" checkout --quiet --detach "$stable_tag"
    fi
    ;;
  main)
    if [ "$(git -C "$INSTALL_TARGET" branch --show-current)" != "$INSTALL_BRANCH" ]; then
      if git -C "$INSTALL_TARGET" show-ref --verify --quiet "refs/heads/$INSTALL_BRANCH"; then
        git -C "$INSTALL_TARGET" checkout --quiet "$INSTALL_BRANCH"
      else
        git -C "$INSTALL_TARGET" checkout --quiet -b "$INSTALL_BRANCH" "origin/$INSTALL_BRANCH"
      fi
    fi
    if [ "$SOURCE_CHECKOUT_CLONED_LOCALLY" != true ]; then
      retry_git -C "$INSTALL_TARGET" fetch --quiet origin "$INSTALL_BRANCH"
      git -C "$INSTALL_TARGET" merge --ff-only --quiet "origin/$INSTALL_BRANCH"
    fi
    ;;
  branch)
    if [ "$(git -C "$INSTALL_TARGET" branch --show-current)" != "$INSTALL_BRANCH" ]; then
      git -C "$INSTALL_TARGET" checkout --quiet "$INSTALL_BRANCH"
    fi
    if [ "$SOURCE_CHECKOUT_CLONED_LOCALLY" != true ]; then
      retry_git -C "$INSTALL_TARGET" fetch --quiet origin "$INSTALL_BRANCH"
      git -C "$INSTALL_TARGET" merge --ff-only --quiet "origin/$INSTALL_BRANCH"
    fi
    ;;
esac

channel_path="$(git -C "$INSTALL_TARGET" rev-parse --path-format=absolute --git-path aips-channel)"
case "$INSTALL_CHANNEL" in
  stable) printf '%s\n' stable > "$channel_path" ;;
  main) printf '%s\n' main > "$channel_path" ;;
  branch) printf 'branch:%s\n' "$INSTALL_BRANCH" > "$channel_path" ;;
esac

if [ -n "$STAGING_DIR" ]; then
  if [ -e "$INSTALL_DIR" ]; then
    echo "ERROR: install destination appeared while the installer lock was held: $INSTALL_DIR" >&2
    exit 1
  fi
  mv "$STAGING_DIR" "$INSTALL_DIR"
  STAGING_DIR=""
fi

if [ "${#CLI_ARGS[@]}" -gt 0 ]; then
  "$INSTALL_DIR/bin/aips" install "${CLI_ARGS[@]}"
  exit $?
fi
"$INSTALL_DIR/bin/aips" install
exit $?

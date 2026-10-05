#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${AIPS_REPO_URL:-https://github.com/LucasLu3918/ai-product-system.git}"
INSTALL_CHANNEL="${AIPS_INSTALL_CHANNEL:-stable}"
INSTALL_BRANCH="${AIPS_INSTALL_BRANCH:-main}"
INSTALL_DIR="${AIPS_INSTALL_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/aips/system}"
SOURCE_CHECKOUT="${AIPS_INSTALL_SOURCE:-}"
DRY_RUN=false
CHANNEL_EXPLICIT=false
if [ "${AIPS_INSTALL_CHANNEL+x}" = x ]; then CHANNEL_EXPLICIT=true; fi
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
      CHANNEL_EXPLICIT=true
      ;;
    *) echo "ERROR: unknown install option: $1" >&2; exit 2 ;;
  esac
  shift
done

require() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: required command not found: $1" >&2; exit 1; }; }
require git
require python3

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
if [ -e "$INSTALL_DIR" ] && [ ! -d "$INSTALL_DIR/.git" ]; then
  echo "ERROR: install path exists but is not an AIPS Git checkout: $INSTALL_DIR" >&2
  exit 1
fi

CLONED_NOW=false
if [ ! -d "$INSTALL_DIR/.git" ]; then
  if [ -n "$SOURCE_CHECKOUT" ]; then
    source_root="$(git -C "$SOURCE_CHECKOUT" rev-parse --show-toplevel 2>/dev/null)" || { echo "ERROR: source checkout is not a Git worktree: $SOURCE_CHECKOUT" >&2; exit 1; }
    [ "$(cd "$SOURCE_CHECKOUT" && pwd -P)" = "$(cd "$source_root" && pwd -P)" ] || { echo "ERROR: source checkout must be the Git top level" >&2; exit 1; }
    [ -f "$SOURCE_CHECKOUT/bin/aips" ] || { echo "ERROR: source checkout has no AIPS CLI" >&2; exit 1; }
    source_head="$(git -C "$SOURCE_CHECKOUT" rev-parse HEAD)"
    git clone --quiet --local --no-checkout "$SOURCE_CHECKOUT" "$INSTALL_DIR"
    git -C "$INSTALL_DIR" checkout --quiet -B "$INSTALL_BRANCH" "$source_head"
  else
    git clone --quiet --filter=blob:none --single-branch --branch "$INSTALL_BRANCH" "$REPO_URL" "$INSTALL_DIR"
  fi
  CLONED_NOW=true
else
  [ -z "$(git -C "$INSTALL_DIR" status --porcelain)" ] || { echo "ERROR: existing AIPS managed checkout has local changes: $INSTALL_DIR" >&2; exit 1; }
  [ "$(git -C "$INSTALL_DIR" remote get-url origin)" = "$REPO_URL" ] || { echo "ERROR: existing AIPS checkout remote differs from the requested repository" >&2; exit 1; }
fi

case "$INSTALL_CHANNEL" in
  stable)
    stable_info="$(python3 "$INSTALL_DIR/scripts/release_channel.py" resolve --remote "$REPO_URL" 2>&1)" || resolve_status=$?
    resolve_status="${resolve_status:-0}"
    if [ "$resolve_status" -eq 3 ] && [ "$CHANNEL_EXPLICIT" = false ]; then
      echo "WARNING: no stable AIPS release tag exists yet; bootstrapping from main. Future updates will follow stable releases." >&2
      INSTALL_CHANNEL=main
      git -C "$INSTALL_DIR" fetch --quiet origin "$INSTALL_BRANCH"
      if [ "$(git -C "$INSTALL_DIR" branch --show-current)" != "$INSTALL_BRANCH" ]; then
        if git -C "$INSTALL_DIR" show-ref --verify --quiet "refs/heads/$INSTALL_BRANCH"; then
          git -C "$INSTALL_DIR" checkout --quiet "$INSTALL_BRANCH"
        else
          git -C "$INSTALL_DIR" checkout --quiet -b "$INSTALL_BRANCH" "origin/$INSTALL_BRANCH"
        fi
      fi
      git -C "$INSTALL_DIR" merge --ff-only --quiet "origin/$INSTALL_BRANCH"
    elif [ "$resolve_status" -ne 0 ]; then
      if [ "$CLONED_NOW" = true ]; then rm -rf "$INSTALL_DIR"; fi
      echo "$stable_info" >&2
      echo "ERROR: stable channel resolution failed; use --channel main only if you want the mutable development branch." >&2
      exit 1
    else
      stable_tag="${stable_info%%$'\t'*}"
      stable_sha="${stable_info#*$'\t'}"
      git -C "$INSTALL_DIR" fetch --quiet origin "refs/tags/$stable_tag:refs/tags/$stable_tag"
      python3 "$INSTALL_DIR/scripts/release_channel.py" verify --repository "$INSTALL_DIR" --tag "$stable_tag" --expected-sha "$stable_sha"
      git -C "$INSTALL_DIR" checkout --quiet --detach "$stable_tag"
    fi
    ;;
  main)
    if [ "$(git -C "$INSTALL_DIR" branch --show-current)" != "$INSTALL_BRANCH" ]; then
      if git -C "$INSTALL_DIR" show-ref --verify --quiet "refs/heads/$INSTALL_BRANCH"; then
        git -C "$INSTALL_DIR" checkout --quiet "$INSTALL_BRANCH"
      else
        git -C "$INSTALL_DIR" checkout --quiet -b "$INSTALL_BRANCH" "origin/$INSTALL_BRANCH"
      fi
    fi
    git -C "$INSTALL_DIR" fetch --quiet origin "$INSTALL_BRANCH"
    git -C "$INSTALL_DIR" merge --ff-only --quiet "origin/$INSTALL_BRANCH"
    ;;
  branch)
    if [ "$(git -C "$INSTALL_DIR" branch --show-current)" != "$INSTALL_BRANCH" ]; then
      git -C "$INSTALL_DIR" checkout --quiet "$INSTALL_BRANCH"
    fi
    git -C "$INSTALL_DIR" fetch --quiet origin "$INSTALL_BRANCH"
    git -C "$INSTALL_DIR" merge --ff-only --quiet "origin/$INSTALL_BRANCH"
    ;;
esac

channel_path="$(git -C "$INSTALL_DIR" rev-parse --path-format=absolute --git-path aips-channel)"
case "$INSTALL_CHANNEL" in
  stable) printf '%s\n' stable > "$channel_path" ;;
  main) printf '%s\n' main > "$channel_path" ;;
  branch) printf 'branch:%s\n' "$INSTALL_BRANCH" > "$channel_path" ;;
esac

if [ "${#CLI_ARGS[@]}" -gt 0 ]; then
  exec "$INSTALL_DIR/bin/aips" install "${CLI_ARGS[@]}"
fi
exec "$INSTALL_DIR/bin/aips" install

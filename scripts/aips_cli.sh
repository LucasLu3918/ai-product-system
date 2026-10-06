#!/usr/bin/env bash
set -euo pipefail

REPO_SLUG="LucasLu3918/ai-product-system"
DEFAULT_BRANCH="main"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/aips"
BIN_HOME="${AIPS_BIN_HOME:-$HOME/.local/bin}"
HARNESS_HOME="$CONFIG_HOME/harness"
OWNED_HOME="$HARNESS_HOME/owned"
ADAPTER_STATE_HOME="$HARNESS_HOME/adapters"
OWNERSHIP_MANIFEST="$HARNESS_HOME/installation.yaml"
SHELL_STATE_HOME="$CONFIG_HOME/shell"
SHELL_PROFILE_RECORD="$SHELL_STATE_HOME/profile"
SHELL_BLOCK_RECORD="$SHELL_STATE_HOME/block"
SHELL_BIN_HOME_RECORD="$SHELL_STATE_HOME/bin-home"
SHELL_PROFILE_CREATED_RECORD="$SHELL_STATE_HOME/profile-created"
SHELL_BLOCK_BEGIN="# >>> AIPS managed PATH >>>"
SHELL_BLOCK_END="# <<< AIPS managed PATH <<<"

resolve_source() {
  local source="${BASH_SOURCE[0]}"
  while [ -h "$source" ]; do
    local dir
    dir="$(cd -P "$(dirname "$source")" >/dev/null 2>&1 && pwd)"
    source="$(readlink "$source")"
    [[ "$source" != /* ]] && source="$dir/$source"
  done
  cd -P "$(dirname "$source")" >/dev/null 2>&1 && pwd
}

canonical_path() {
  local source="$1"
  while [ -h "$source" ]; do
    local dir target
    dir="$(cd -P "$(dirname "$source")" >/dev/null 2>&1 && pwd)" || return 1
    target="$(readlink "$source")" || return 1
    if [[ "$target" != /* ]]; then
      source="$dir/$target"
    else
      source="$target"
    fi
  done
  local dir
  dir="$(cd -P "$(dirname "$source")" >/dev/null 2>&1 && pwd)" || return 1
  printf '%s/%s\n' "$dir" "$(basename "$source")"
}

SCRIPT_DIR="$(resolve_source)"
SYSTEM_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

say() { printf '%s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }


# Load the CLI implementation relative to this resolved source checkout.
source "$SCRIPT_DIR/aips_cli/help.sh"
source "$SCRIPT_DIR/aips_cli/runtime.sh"
source "$SCRIPT_DIR/aips_cli/harness.sh"
source "$SCRIPT_DIR/aips_cli/commands.sh"
source "$SCRIPT_DIR/aips_cli/project.sh"
source "$SCRIPT_DIR/aips_cli/shell.sh"
source "$SCRIPT_DIR/aips_cli/installation.sh"
source "$SCRIPT_DIR/aips_cli/maintenance.sh"
source "$SCRIPT_DIR/aips_cli/dispatch.sh"

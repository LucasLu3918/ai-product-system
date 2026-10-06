require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

git_in_system() { git -C "$SYSTEM_DIR" "$@"; }
current_version() { tr -d '[:space:]' < "$SYSTEM_DIR/VERSION"; }
current_commit() { git_in_system rev-parse HEAD; }

installed_channel() {
  local metadata
  metadata="$(git_in_system rev-parse --path-format=absolute --git-path aips-channel)"
  [ -f "$metadata" ] && cat "$metadata" || printf '%s\n' main
}

checkout_main_channel() {
  git_in_system fetch --quiet origin "$DEFAULT_BRANCH"
  if [ "$(git_in_system branch --show-current)" != "$DEFAULT_BRANCH" ]; then
    if git_in_system show-ref --verify --quiet "refs/heads/$DEFAULT_BRANCH"; then
      git_in_system checkout --quiet "$DEFAULT_BRANCH"
    else
      git_in_system checkout --quiet -b "$DEFAULT_BRANCH" "origin/$DEFAULT_BRANCH"
    fi
  fi
  git_in_system merge --ff-only --quiet "origin/$DEFAULT_BRANCH"
}

major_of() { printf '%s' "$1" | awk -F. '{print $1}'; }

python_bin() {
  local candidate
  for candidate in "${AIPS_VALIDATION_PYTHON:-}" "${AIPS_VALIDATION_VENV:+$AIPS_VALIDATION_VENV/bin/python}" "$SYSTEM_DIR/.venv/bin/python"; do
    [ -x "$candidate" ] || continue
    "$candidate" -c 'import yaml' >/dev/null 2>&1 || continue
    printf '%s\n' "$candidate"
    return 0
  done
  command -v python3 || true
}

validation_python_for_root() {
  local root="$1"
  local require_full="${2:-true}"
  local base="" full_flag=""
  base="$(command -v python3 || python_bin)"
  [ -n "$base" ] || return 1
  [ "$require_full" = "true" ] && full_flag="--require-full"
  "$base" "$SYSTEM_DIR/scripts/runtime_context.py" resolve-python \
    --system-root "$SYSTEM_DIR" --project-root "$root" $full_flag 2>/dev/null
}

compatible_python_bin() {
  local candidate path
  if [ -n "${AIPS_PYTHON:-}" ]; then
    path="$(command -v "$AIPS_PYTHON" 2>/dev/null || true)"
    [ -n "$path" ] || path="$AIPS_PYTHON"
    if [ -x "$path" ] && "$path" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' >/dev/null 2>&1; then
      printf '%s\n' "$path"
      return 0
    fi
    return 1
  fi
  for candidate in python3.14 python3.13 python3.12 python3; do
    [ -n "$candidate" ] || continue
    path="$(command -v "$candidate" 2>/dev/null || true)"
    [ -n "$path" ] || continue
    if "$path" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' >/dev/null 2>&1; then
      printf '%s\n' "$path"
      return 0
    fi
  done
  return 1
}

venv_python_compatible() {
  [ -x "$SYSTEM_DIR/.venv/bin/python" ] &&
    "$SYSTEM_DIR/.venv/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' >/dev/null 2>&1
}

ensure_compatible_venv() {
  local creator
  creator="$(compatible_python_bin || true)"
  [ -n "$creator" ] || die "AIPS requires Python 3.12 or newer. Set AIPS_PYTHON to a compatible interpreter."
  if venv_python_compatible; then
    return 0
  fi
  if [ -d "$SYSTEM_DIR/.venv" ]; then
    warn "AIPS virtual environment uses an unsupported Python; recreating it with $creator."
    rm -rf "$SYSTEM_DIR/.venv"
  else
    say "Creating Python virtual environment with $creator..."
  fi
  "$creator" -m venv "$SYSTEM_DIR/.venv" || die "AIPS virtual environment creation failed."
  venv_python_compatible || die "AIPS virtual environment requires Python 3.12 or newer."
}

runtime_dependencies_available() {
  local py
  # Doctor and installer inspect the installed runtime, not a caller's Gate venv.
  if [ -x "$SYSTEM_DIR/.venv/bin/python" ]; then
    py="$SYSTEM_DIR/.venv/bin/python"
  else
    py="$(command -v python3 || true)"
  fi
  [ -n "$py" ] && "$py" -c 'import yaml, mcp' >/dev/null 2>&1
}

openapi_dependency_status() {
  local py
  if [ -x "$SYSTEM_DIR/.venv/bin/python" ]; then
    py="$SYSTEM_DIR/.venv/bin/python"
  else
    py="$(python_bin)"
  fi
  if [ -n "$py" ] && "$py" -c 'import openapi_spec_validator, jsonschema' >/dev/null 2>&1; then
    say "OpenAPI optional dependencies: READY ($py)"
  else
    say "OpenAPI optional dependencies: NOT_INSTALLED (optional; run aips openapi install)"
  fi
}

install_runtime_dependencies() {
  ensure_compatible_venv
  local py="$SYSTEM_DIR/.venv/bin/python"
  "$py" "$SYSTEM_DIR/scripts/package_install.py" --python "$py" --requirements "$SYSTEM_DIR/requirements.txt" --constraints "$SYSTEM_DIR/constraints/tested.txt" ||
    die "AIPS runtime dependency installation failed."
  "$py" -c 'import yaml, mcp' >/dev/null 2>&1 ||
    die "AIPS runtime dependencies are incomplete after installation."
}

repair_runtime_dependencies_if_installed() {
  local recorded="" recorded_canonical="" system_canonical=""
  [ -f "$CONFIG_HOME/system-dir" ] && recorded="$(cat "$CONFIG_HOME/system-dir" 2>/dev/null || true)"
  [ -n "$recorded" ] && recorded_canonical="$(canonical_path "$recorded" || true)"
  system_canonical="$(canonical_path "$SYSTEM_DIR" || true)"
  [ -n "$recorded_canonical" ] && [ "$recorded_canonical" = "$system_canonical" ] || return 0
  if [ -d "$SYSTEM_DIR/.venv" ] && ! venv_python_compatible; then
    warn "AIPS managed virtual environment uses an unsupported Python; repairing the environment."
    install_runtime_dependencies
    say "AIPS runtime dependencies: repaired"
    return 0
  fi
  if runtime_dependencies_available; then
    say "AIPS runtime dependencies: OK"
    return 0
  fi
  warn "AIPS runtime dependencies are incomplete; repairing the managed environment."
  install_runtime_dependencies
  say "AIPS runtime dependencies: repaired"
}

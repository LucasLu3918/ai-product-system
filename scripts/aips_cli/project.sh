attach_project() {
  local project="$1"
  [ -d "$project" ] || die "Project path does not exist: $project"
  local migration
  if [ -f "$project/.ai/intelligence/PROJECT_INTELLIGENCE.yaml" ]; then
    migration="$(intelligence_cmd migrate-attached --project "$project" --format json 2>&1)" || {
      warn "Could not import legacy project Intelligence into external state: $migration"
      return 1
    }
  else
    migration="$(intelligence_cmd bootstrap --project "$project" --format json 2>&1)" || {
      warn "Could not initialize external Project Intelligence: $migration"
      return 1
    }
  fi
  say "Project Intelligence external state: $migration"
  say "AIPS enabled for this project using external user state: $project"
  say "No project files, Git config or Git excludes were created or changed."
}

detach_project() {
  local project="$1"
  [ -d "$project" ] || die "Project path does not exist: $project"

  local sync_result
  if ! sync_result="$(intelligence_cmd migrate-attached --project "$project" --format json 2>&1)"; then
    die "Could not preserve legacy project Intelligence in external state: $sync_result"
  fi
  say "No project-local AIPS workspace is active; all new state remains external."
  say "Legacy .ai data, if present, is preserved unchanged."
  say "Use 'aips project mode set off --project \"$project\"' to disable optional governance."
}

status_project() {
  local project="$1" governance_mode="UNKNOWN" mode_report py
  [ -d "$project" ] || die "Project path does not exist: $project"

  py="$(python_bin)"
  if mode_report="$("$py" "$SYSTEM_DIR/scripts/project_governance_mode.py" show --project "$project" --format json 2>/dev/null)"; then
    governance_mode="$(printf '%s' "$mode_report" | "$py" -c 'import json,sys; print(json.load(sys.stdin).get("mode") or "UNKNOWN")' 2>/dev/null || echo UNKNOWN)"
  fi

  say "AI Product System status"
  say "System dir: $SYSTEM_DIR"
  say "System version: $(current_version 2>/dev/null || echo unknown)"
  say "System commit: $(current_commit 2>/dev/null || echo unknown)"
  if [ -L "$BIN_HOME/aips" ]; then
    say "CLI installed: yes ($BIN_HOME/aips)"
  else
    say "CLI installed: no"
  fi

  say "Project: $project"
  say "Optional governance mode: $governance_mode"
  say "Project mode: EXTERNAL (no project-local AIPS writes)"
  if intelligence_cmd status --project "$project" --format json >/dev/null 2>&1; then
    say "External Project Intelligence: resolvable"
  fi
  if [ -d "$project/.ai" ]; then
    say "Legacy .ai data: present (preserved; not used for new writes)"
  else
    say "Legacy .ai data: absent"
  fi
  return 0
}

project_check() {
  local project="${1:-}"
  [ -n "$project" ] || die "Usage: aips project check <project-path>"
  [ -d "$project" ] || die "Project path does not exist: $project"

  say "Project check"
  say "Project: $project"
  say "Project mode: EXTERNAL (no project-local AIPS writes)"

  local report freshness py
  if report="$(intelligence_cmd status --project "$project" --format json 2>/dev/null)"; then
    py="$(python_bin)"
    freshness="$(printf '%s' "$report" | "$py" -c 'import json,sys; report=json.load(sys.stdin); print((report.get("freshness") or {}).get("status") or "UNKNOWN")' 2>/dev/null || echo UNKNOWN)"
    say "Project Intelligence freshness: $freshness"
  else
    say "Project Intelligence freshness: UNKNOWN (status unavailable)"
  fi
}

project_diagnose() {
  [ "$#" -ge 1 ] || die "Usage: aips project diagnose <project-path> [--runtime <id>] [--format text|yaml|json]"
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  "$py" "$SYSTEM_DIR/scripts/project_diagnostics.py" "$@"
}

project_mode() {
  [ "$#" -ge 1 ] || die "Usage: aips project mode <show|set> [options]"
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  "$py" "$SYSTEM_DIR/scripts/project_governance_mode.py" "$@"
}

validate_repo() {
  local py
  py="$(validation_python_for_root "$SYSTEM_DIR" true || true)"
  [ -n "$py" ] || die "No complete Python 3.12 validation environment found. Run python3.12 bin/prepare-local-validation or set AIPS_VALIDATION_PYTHON; inspect aips publish environment before full validation."
  "$py" -m pip check >/dev/null || die "Selected validation Python has inconsistent dependencies. Rebuild the pinned validation environment."
  "$py" -c 'import socket; probe=socket.socket(); probe.bind(("127.0.0.1", 0)); probe.close()' >/dev/null 2>&1 || die "Full validation requires permitted loopback binding; use an authorized validation runtime before starting lifecycle checks."
  PATH="$(dirname "$py"):$PATH" AIPS_VALIDATION_PYTHON="$py" "$py" "$SYSTEM_DIR/tests/validate_repository.py"
}

validate_installation() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."

  "$py" -c 'import yaml, mcp' >/dev/null 2>&1 || die "AIPS runtime dependencies are incomplete."

  if ! AIPS_VALIDATION_PYTHON="$py" PYTHONPATH="$SYSTEM_DIR" "$py" -c 'from tests.validation import static_contracts as s; import sys; [print(f"- {item}") for item in s.errors]; sys.exit(1 if s.errors else 0)'; then
    die "AIPS installation integrity validation failed."
  fi

  "$py" "$SYSTEM_DIR/scripts/documentation_placement.py" >/dev/null ||
    die "AIPS Human documentation placement validation failed."
}

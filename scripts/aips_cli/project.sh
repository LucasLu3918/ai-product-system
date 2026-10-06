write_system_snapshot() {
  local project="$1"
  local ai_dir="$project/.ai"
  local version commit timestamp
  version="$(current_version)"
  commit="$(current_commit)"
  timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  mkdir -p "$ai_dir"
  cat > "$ai_dir/SYSTEM.yaml" <<EOF
system:
  name: ai-product-system
  repository: $REPO_SLUG
  version: "$version"
  commit: "$commit"
  updated_at: "$timestamp"
  local_path: "$SYSTEM_DIR"
EOF
}

init_project() {
  local project="$1"
  [ -d "$project" ] || die "Project path does not exist: $project"

  local ai_dir="$project/.ai"
  mkdir -p "$ai_dir/runs" "$ai_dir/decisions"

  for name in PROJECT.md STATE.yaml MANIFEST.yaml; do
    if [ ! -e "$ai_dir/$name" ]; then
      cp "$SYSTEM_DIR/templates/workspace/$name" "$ai_dir/$name"
      say "Created .ai/$name"
    else
      say "Kept existing .ai/$name"
    fi
  done

  write_system_snapshot "$project"
  say "Workspace initialized: $ai_dir"
}

attach_project() {
  local project="$1"
  [ -d "$project" ] || die "Project path does not exist: $project"

  if [ ! -d "$project/.ai" ]; then
    local detached
    detached="$(find "$project" -maxdepth 1 -type d -name '.ai.detached-*' -print 2>/dev/null | sort | tail -n 1 || true)"
    if [ -n "$detached" ]; then
      warn "A detached AI workspace already exists: $detached"
      say "Restore it first if you want to continue that workspace:"
      say "  mv \"$detached\" \"$project/.ai\""
      say "Then rerun:"
      say "  aips attach \"$project\""
      return 2
    fi
  fi

  init_project "$project"

  local migration
  if ! migration="$(intelligence_cmd migrate-attached --project "$project" --format json 2>&1)"; then
    warn "Project attached, but External Project Intelligence migration failed: $migration"
    warn "Existing Intelligence was preserved; resolve this before relying on persistent Intelligence."
  else
    say "Project Intelligence migration: $migration"
  fi

  say "Project attached to AI Product System: $project"
}

detach_project() {
  local project="$1"
  [ -d "$project" ] || die "Project path does not exist: $project"

  if [ ! -d "$project/.ai" ]; then
    say "Project is already detached (no .ai workspace): $project"
    return 0
  fi

  local sync_result
  if ! sync_result="$(intelligence_cmd sync-external --project "$project" --format json 2>&1)"; then
    die "Cannot safely detach because Project Intelligence could not be synced to External Cache: $sync_result"
  fi
  say "Project Intelligence external sync: $sync_result"

  local stamp archive
  stamp="$(date -u +"%Y%m%d-%H%M%S")"
  archive="$project/.ai.detached-$stamp"
  [ ! -e "$archive" ] || die "Detach archive already exists: $archive"

  mv "$project/.ai" "$archive"
  say "Project detached: $project"
  say "Workspace preserved: $archive"
  say "Product source code was not modified."
  say "To restore:"
  say "  mv \"$archive\" \"$project/.ai\""
  say "  aips attach \"$project\""
}

status_project() {
  local project="$1"
  [ -d "$project" ] || die "Project path does not exist: $project"

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
  if [ -d "$project/.ai" ]; then
    say "Project attached: yes"
    say "Project mode: ATTACHED"
    say "Workspace: $project/.ai"
    if [ -f "$project/.ai/SYSTEM.yaml" ]; then
      local recorded_version recorded_commit
      recorded_version="$(awk -F': ' '/^[[:space:]]*version:/ {gsub(/"/,"",$2); print $2; exit}' "$project/.ai/SYSTEM.yaml" || true)"
      recorded_commit="$(awk -F': ' '/^[[:space:]]*commit:/ {gsub(/"/,"",$2); print $2; exit}' "$project/.ai/SYSTEM.yaml" || true)"
      [ -n "$recorded_version" ] && say "Recorded system version: $recorded_version"
      [ -n "$recorded_commit" ] && say "Recorded system commit: $recorded_commit"
    fi
  else
    say "Project attached: no"
    say "Project mode: EPHEMERAL"
    if intelligence_cmd status --project "$project" --format json >/dev/null 2>&1; then
      say "External Project Intelligence: resolvable"
    fi
    local detached
    detached="$(find "$project" -maxdepth 1 -type d -name '.ai.detached-*' -print 2>/dev/null | sort | tail -n 1 || true)"
    [ -n "$detached" ] && say "Latest detached workspace: $detached"
  fi
}

validate_repo() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  if ! "$py" -c 'import yaml' >/dev/null 2>&1; then
    die "PyYAML is missing. Run: $SYSTEM_DIR/bin/aips install"
  fi
  AIPS_VALIDATION_PYTHON="$py" "$py" "$SYSTEM_DIR/tests/validate_repository.py"
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

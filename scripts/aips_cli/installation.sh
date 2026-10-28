install_cli() {
  local configure_shell="auto" answer
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --configure-shell) configure_shell="true" ;;
      --no-configure-shell) configure_shell="false" ;;
      *) die "Unknown install option: $1" ;;
    esac
    shift
  done
  require_cmd git
  [ -d "$SYSTEM_DIR/.git" ] || die "Run install from a cloned ai-product-system repository."

  say "Installing AIPS runtime dependencies..."
  install_runtime_dependencies

  mkdir -p "$BIN_HOME"
  [ ! -L "$CONFIG_HOME" ] || die "AIPS config directory is a symlink; existing data was preserved."
  (umask 077; mkdir -p "$CONFIG_HOME")

  if [ -e "$BIN_HOME/aips" ] || [ -L "$BIN_HOME/aips" ]; then
    if [ -L "$BIN_HOME/aips" ]; then
      local existing_target expected_target
      existing_target="$(canonical_path "$BIN_HOME/aips" || true)"
      expected_target="$(canonical_path "$SYSTEM_DIR/bin/aips" || true)"
      if [ -z "$existing_target" ] || [ "$existing_target" != "$expected_target" ]; then
        die "CLI path already exists and is not owned by this AIPS installation: $BIN_HOME/aips"
      fi
    else
      die "CLI path already exists and is not an AIPS symlink: $BIN_HOME/aips"
    fi
  fi

  local system_marker="$CONFIG_HOME/system-dir" marker_size recorded_system recorded_canonical actual_canonical
  [ ! -L "$system_marker" ] || die "System marker is a symlink; existing data was preserved."
  if [ -e "$system_marker" ]; then
    [ -f "$system_marker" ] && [ -r "$system_marker" ] || die "System marker is not a readable regular file; existing data was preserved."
    marker_size="$(wc -c < "$system_marker")"
    [ "$marker_size" -le 16384 ] || die "System marker is too large; existing data was preserved."
    recorded_system="$(cat "$system_marker")"
    case "$recorded_system" in /*) ;; *) die "System marker is not absolute; existing data was preserved." ;; esac
    recorded_canonical="$(canonical_path "$recorded_system" || true)"
    actual_canonical="$(canonical_path "$SYSTEM_DIR" || true)"
    [ -n "$recorded_canonical" ] && [ "$recorded_canonical" = "$actual_canonical" ] ||
      die "System marker belongs to a different installation; existing data was preserved."
  else
    (umask 077; set -C; printf '%s\n' "$SYSTEM_DIR" > "$system_marker") || die "System marker appeared or could not be created; existing data was preserved."
  fi

  if ! ln -s "$SYSTEM_DIR/bin/aips" "$BIN_HOME/aips" 2>/dev/null; then
    local verified_target expected_target
    verified_target="$(canonical_path "$BIN_HOME/aips" || true)"
    expected_target="$(canonical_path "$SYSTEM_DIR/bin/aips" || true)"
    [ -L "$BIN_HOME/aips" ] && [ -n "$verified_target" ] && [ "$verified_target" = "$expected_target" ] ||
      die "CLI link could not be created or safely verified; existing data was preserved."
  fi

  validate_installation
  say "Runtime adapters are not enabled by installation. Use 'aips harness install' to enable them explicitly."

  if [ "$configure_shell" = "true" ]; then
    shell_install
  elif [[ ":$PATH:" != *":$BIN_HOME:"* ]]; then
    if [ "$configure_shell" = "auto" ] && [ -t 0 ] && [ -t 1 ] && [ "${AIPS_NONINTERACTIVE:-false}" != "true" ]; then
      printf 'Add %s to PATH in %s? [Y/n] ' "$BIN_HOME" "$(shell_profile_path 2>/dev/null || printf 'your shell profile')"
      IFS= read -r answer || answer="n"
      case "$answer" in
        n|N|no|NO|No) ;;
        *) shell_install ;;
      esac
    fi
  fi

  say
  say "Installed: $BIN_HOME/aips"
  if [[ ":$PATH:" != *":$BIN_HOME:"* ]]; then
    warn "$BIN_HOME is not currently in PATH."
    say "Add this to your shell profile, then open a new terminal:"
    say "  export PATH=\"$BIN_HOME:\$PATH\""
    say "Or let AIPS manage an ownership-marked profile block:"
    say "  \"$BIN_HOME/aips\" shell install"
    say "For this terminal only:"
    say "  export PATH=\"$BIN_HOME:\$PATH\""
    say "Until PATH is updated, run: \"$BIN_HOME/aips\" doctor"
    say "Until PATH is updated, run: \"$BIN_HOME/aips\" harness status"
  else
    say "Run: aips doctor"
    say "MCP gateway: aips mcp inspect"
  fi
  if [[ ":$PATH:" != *":$BIN_HOME:"* ]]; then
    say "MCP gateway: \"$BIN_HOME/aips\" mcp inspect"
  fi
}

uninstall_cli() {
  local remove_venv="false" remove_cache="false" remove_shell="false"
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --remove-venv) remove_venv="true" ;;
      --remove-cache) remove_cache="true" ;;
      --remove-shell-integration) remove_shell="true" ;;
      *) die "Unknown uninstall option: $1" ;;
    esac
    shift
  done

  harness_uninstall

  if [ -L "$BIN_HOME/aips" ]; then
    rm -f "$BIN_HOME/aips"
    say "Removed CLI symlink: $BIN_HOME/aips"
  elif [ -e "$BIN_HOME/aips" ]; then
    warn "$BIN_HOME/aips is not a symlink; leaving it untouched."
  fi

  if [ "$remove_shell" = "true" ]; then
    shell_uninstall true || true
  else
    shell_uninstall false || true
  fi

  rm -f "$CONFIG_HOME/system-dir"
  if [ "$remove_cache" = "true" ]; then
    rm -rf "$CONFIG_HOME/projects"
    say "Removed External Project Intelligence cache."
  else
    [ -d "$CONFIG_HOME/projects" ] && say "Preserved External Project Intelligence: $CONFIG_HOME/projects"
  fi
  rmdir "$CONFIG_HOME" 2>/dev/null || true

  if [ "$remove_venv" = "true" ] && [ -d "$SYSTEM_DIR/.venv" ]; then
    rm -rf "$SYSTEM_DIR/.venv"
    say "Removed virtual environment: $SYSTEM_DIR/.venv"
  fi

  say "Repository was preserved: $SYSTEM_DIR"
  say "Project .ai workspaces and all user-owned Agent instructions/Skills were preserved."
}

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

  mkdir -p "$BIN_HOME" "$CONFIG_HOME"

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

  ln -s "$SYSTEM_DIR/bin/aips" "$BIN_HOME/aips" 2>/dev/null || true
  printf '%s\n' "$SYSTEM_DIR" > "$CONFIG_HOME/system-dir"

  validate_installation
  harness_install

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
  rm -rf "$CONFIG_HOME/harness"
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

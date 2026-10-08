adapter_state_file() {
  printf '%s/%s.yaml\n' "$ADAPTER_STATE_HOME" "$1"
}

adapter_state_value() {
  local id="$1" field="$2" file
  file="$(adapter_state_file "$id")"
  [ -f "$file" ] || return 1
  awk -v key="$field" -F': ' '$1 == key {gsub(/"/,"",$2); print $2; exit}' "$file"
}

adapter_status_value() {
  adapter_state_value "$1" "status"
}

adapter_resource_value() {
  adapter_state_value "$1" "resource"
}

adapter_strategy_value() {
  adapter_state_value "$1" "strategy"
}

write_adapter_state() {
  local id="$1" status="$2" strategy="$3" resource="${4:-}" capability="${5:-MANUAL}" enforcement="${6:-}"
  if [ -z "$enforcement" ]; then
    [ "$capability" = "UNSUPPORTED" ] && enforcement="UNSUPPORTED" || enforcement="ADVISORY"
  fi
  mkdir -p "$ADAPTER_STATE_HOME"
  cat > "$(adapter_state_file "$id")" <<EOF
id: "$id"
status: "$status"
strategy: "$strategy"
resource: "$resource"
capability: "$capability"
governance_enforcement: "$enforcement"
updated_at: "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
EOF
}

harness_host_ids() {
  "$(python_bin)" "$SYSTEM_DIR/scripts/manage_runtime_adapter.py" host-ids --system-root "$SYSTEM_DIR"
}

write_ownership_manifest() {
  "$(python_bin)" "$SYSTEM_DIR/scripts/manage_runtime_adapter.py" write-manifest \
    --system-root "$SYSTEM_DIR" --state-home "$ADAPTER_STATE_HOME" \
    --owned-home "$OWNED_HOME" --bin-home "$BIN_HOME" --target "$OWNERSHIP_MANIFEST" >/dev/null
}

install_opencode_adapter() {
  local py target
  py="$(python_bin)"
  if ! command -v opencode >/dev/null 2>&1; then
    write_adapter_state "opencode" "NOT_DETECTED" "native_projections" "" "UNSUPPORTED"
    return 0
  fi
  target="${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}"
  if "$py" "$SYSTEM_DIR/scripts/opencode_skill_projection.py" probe >/dev/null && \
      "$py" "$SYSTEM_DIR/scripts/opencode_skill_projection.py" install >/dev/null && \
      "$py" "$SYSTEM_DIR/scripts/portable_commands.py" install --host opencode >/dev/null; then
    write_adapter_state "opencode" "AUTOMATIC" "native_projections" "$target" "CONTEXT_ALWAYS"
    say "Harness adapter composed: opencode capability=CONTEXT_ALWAYS enforcement=ADVISORY -> $target"
  else
    write_adapter_state "opencode" "CONFLICT" "native_projections" "$target" "MANUAL"
    warn "OpenCode native projections conflict or are unavailable; user files and ownership were preserved."
  fi
}

install_codex_adapter() {
  local codex_home="${CODEX_HOME:-$HOME/.codex}"
  local target="$codex_home/AGENTS.md" py
  py="$(python_bin)"
  if ! codex_runtime_available; then
    write_adapter_state "codex" "NOT_DETECTED" "managed_global_instruction_block" "" "UNSUPPORTED"
    return 0
  fi
  if "$py" "$SYSTEM_DIR/scripts/manage_runtime_adapter.py" install-block       --target "$target"       --source "$SYSTEM_DIR/harness/adapters/codex/AGENTS.md"       --snapshot "$OWNED_HOME/codex.block" >/dev/null; then
    write_adapter_state "codex" "AUTOMATIC" "managed_global_instruction_block" "$target" "CONTEXT_ALWAYS"
    say "Harness adapter composed: codex capability=CONTEXT_ALWAYS -> $target"
  else
    write_adapter_state "codex" "CONFLICT" "managed_global_instruction_block" "$target" "MANUAL"
    warn "Codex AIPS managed block could not be updated safely; existing content was preserved."
  fi
}

codex_runtime_available() {
  command -v codex >/dev/null 2>&1 && return 0

  local candidate
  for candidate in \
    "${CODEX_CLI_PATH:-}" \
    "${AIPS_CODEX_CLI_PATH:-}" \
    "/Applications/ChatGPT.app/Contents/Resources/codex"; do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
      return 0
    fi
  done

  return 1
}

install_claude_adapter() {
  local target="$HOME/.claude/CLAUDE.md"
  local settings="$HOME/.claude/settings.json"
  local py hook_cmd guard_cmd memory_ok="false" hook_ok="false"
  py="$(python_bin)"
  if ! command -v claude >/dev/null 2>&1; then
    write_adapter_state "claude-code" "NOT_DETECTED" "managed_memory_plus_prompt_hook" "" "UNSUPPORTED"
    return 0
  fi

  if "$py" "$SYSTEM_DIR/scripts/manage_runtime_adapter.py" install-block       --target "$target"       --source "$SYSTEM_DIR/harness/adapters/claude-code/CLAUDE.md"       --snapshot "$OWNED_HOME/claude-code.block" >/dev/null; then
    memory_ok="true"
  fi

  hook_cmd="AIPS_MANAGED_HOOK=1 AIPS_BIN='$SYSTEM_DIR/bin/aips' '$py' '$SYSTEM_DIR/scripts/turn_context_hook.py' --runtime claude-code"
  guard_cmd="AIPS_MANAGED_HOOK=1 AIPS_BIN='$SYSTEM_DIR/bin/aips' '$py' '$SYSTEM_DIR/scripts/governance_guard.py' hook --runtime claude-code"
  if "$py" "$SYSTEM_DIR/scripts/manage_runtime_adapter.py" install-claude-hook       --settings "$settings" --command "$hook_cmd" --guard-command "$guard_cmd" >/dev/null; then
    hook_ok="true"
  fi

  if [ "$hook_ok" = "true" ]; then
    write_adapter_state "claude-code" "AUTOMATIC" "managed_memory_plus_prompt_hook" "$target|$settings" "TURN_NATIVE" "TOOL_GUARDED"
    say "Harness adapter composed: claude-code capability=TURN_NATIVE"
  elif [ "$memory_ok" = "true" ]; then
    write_adapter_state "claude-code" "AUTOMATIC" "managed_memory_block" "$target" "CONTEXT_ALWAYS"
    warn "Claude per-turn hook could not be installed safely; using CONTEXT_ALWAYS fallback."
  else
    write_adapter_state "claude-code" "CONFLICT" "managed_memory_plus_prompt_hook" "$target|$settings" "MANUAL"
    warn "Claude AIPS integration could not be installed safely."
  fi
}

install_gemini_adapter() {
  local id="gemini-cli"
  local source="$SYSTEM_DIR/harness/adapters/gemini-cli"
  if ! command -v gemini >/dev/null 2>&1; then
    write_adapter_state "$id" "NOT_DETECTED" "official_extension_before_agent" "" "UNSUPPORTED"
    return 0
  fi

  local current
  current="$(adapter_status_value "$id" 2>/dev/null || true)"
  if gemini extensions list 2>/dev/null | grep -q "aips-global-harness"; then
    if [ "$current" = "AUTOMATIC" ]; then
      write_adapter_state "$id" "AUTOMATIC" "official_extension_before_agent" "aips-global-harness" "TURN_NATIVE" "TOOL_GUARDED"
      return 0
    fi
    write_adapter_state "$id" "CONFLICT" "official_extension_before_agent" "aips-global-harness" "MANUAL"
    warn "Gemini extension name already exists and is not recorded as AIPS-owned; leaving it untouched."
    return 0
  fi

  if gemini extensions link "$source" >/dev/null 2>&1; then
    write_adapter_state "$id" "AUTOMATIC" "official_extension_before_agent" "aips-global-harness" "TURN_NATIVE" "TOOL_GUARDED"
    say "Harness adapter installed: gemini-cli capability=TURN_NATIVE"
  else
    write_adapter_state "$id" "ERROR" "official_extension_before_agent" "" "MANUAL"
    warn "Gemini CLI detected but AIPS extension linking failed."
  fi
}

harness_install() {
  mkdir -p "$HARNESS_HOME" "$OWNED_HOME" "$ADAPTER_STATE_HOME"
  install_codex_adapter
  install_claude_adapter
  install_gemini_adapter
  install_opencode_adapter
  write_ownership_manifest
  say "AIPS Global Harness installed."
  say "Run: aips harness status"
}

uninstall_gemini_adapter() {
  local status
  status="$(adapter_status_value gemini-cli 2>/dev/null || true)"
  [ "$status" = "AUTOMATIC" ] || return 0

  if command -v gemini >/dev/null 2>&1; then
    if gemini extensions uninstall aips-global-harness >/dev/null 2>&1; then
      say "Removed AIPS Gemini extension."
      return 0
    fi
    warn "Could not unregister AIPS Gemini extension automatically; ownership state is being preserved for retry."
    return 1
  fi

  local default_link="$HOME/.gemini/extensions/aips-global-harness"
  if [ -L "$default_link" ]; then
    local target
    target="$(readlink "$default_link" || true)"
    if [[ "$target" == "$SYSTEM_DIR/harness/adapters/gemini-cli"* ]]; then
      rm -f "$default_link"
      say "Removed AIPS-owned Gemini extension link: $default_link"
      return 0
    fi
  fi
  warn "Gemini CLI is unavailable; AIPS-owned Gemini registration could not be safely verified for removal."
  return 1
}

harness_uninstall() {
  local failed="false" py
  py="$(python_bin)"

  local codex_target
  codex_target="$(adapter_resource_value codex 2>/dev/null || true)"
  if [ -n "$codex_target" ]; then
    if ! "$py" "$SYSTEM_DIR/scripts/manage_runtime_adapter.py" uninstall-block         --target "$codex_target" --snapshot "$OWNED_HOME/codex.block" >/dev/null; then
      warn "Codex managed block changed; preserved."
      failed="true"
    fi
  fi

  local claude_resource claude_target claude_settings
  claude_resource="$(adapter_resource_value claude-code 2>/dev/null || true)"
  claude_target="${claude_resource%%|*}"
  claude_settings="${claude_resource#*|}"
  [ "$claude_settings" = "$claude_resource" ] && claude_settings="$HOME/.claude/settings.json"

  if [ -n "$claude_target" ]; then
    if ! "$py" "$SYSTEM_DIR/scripts/manage_runtime_adapter.py" uninstall-block         --target "$claude_target" --snapshot "$OWNED_HOME/claude-code.block" >/dev/null; then
      warn "Claude managed memory block changed; preserved."
      failed="true"
    fi
  fi

  if [ -e "$claude_settings" ]; then
    if ! "$py" "$SYSTEM_DIR/scripts/manage_runtime_adapter.py" uninstall-claude-hook         --settings "$claude_settings" >/dev/null; then
      warn "Claude AIPS hook could not be removed safely."
      failed="true"
    fi
  fi

  if ! uninstall_gemini_adapter; then failed="true"; fi

  if [ -d "$OWNED_HOME/opencode" ]; then
    if ! "$py" "$SYSTEM_DIR/scripts/opencode_skill_projection.py" uninstall >/dev/null || \
        ! "$py" "$SYSTEM_DIR/scripts/portable_commands.py" uninstall --host opencode >/dev/null; then
      warn "OpenCode projections could not be removed safely; ownership preserved for retry."
      failed="true"
    fi
  fi

  if [ "$failed" = "true" ]; then
    warn "Harness uninstall is incomplete. Ownership state was preserved at: $HARNESS_HOME"
    return 1
  fi

  rm -rf "$HARNESS_HOME"
  say "AIPS Global Harness removed."
  say "User/project Agent instructions, Skills, source and Project Intelligence were preserved."
}

harness_status() {
  say "AIPS Global Harness status"
  say "Harness: $([ -f "$OWNERSHIP_MANIFEST" ] && echo active || echo not-installed)"
  say "Bootstrap: $SYSTEM_DIR/harness/BOOTSTRAP.md"
  local id
  for id in $(harness_host_ids); do
    local state status strategy resource capability enforcement
    state="$(adapter_state_file "$id")"
    if [ -f "$state" ]; then
      status="$(adapter_state_value "$id" status 2>/dev/null || echo UNKNOWN)"
      strategy="$(adapter_state_value "$id" strategy 2>/dev/null || true)"
      resource="$(adapter_state_value "$id" resource 2>/dev/null || true)"
      capability="$(adapter_state_value "$id" capability 2>/dev/null || echo MANUAL)"
      enforcement="$(adapter_state_value "$id" governance_enforcement 2>/dev/null || echo ADVISORY)"
      say "$id: $status capability=$capability enforcement=$enforcement ($strategy)${resource:+ -> $resource}"
      if [ "$id" = "opencode" ] && [ "$status" != "NOT_DETECTED" ]; then
        "$(python_bin)" "$SYSTEM_DIR/scripts/opencode_skill_projection.py" status || true
        "$(python_bin)" "$SYSTEM_DIR/scripts/portable_commands.py" status --host opencode || true
      fi
    else
      say "$id: NOT_DETECTED capability=UNSUPPORTED enforcement=UNSUPPORTED"
    fi
  done
}

harness_doctor() {
  local failed="false"
  say "AIPS Global Harness doctor"
  [ -f "$SYSTEM_DIR/harness/BOOTSTRAP.md" ] && say "bootstrap: OK" || { warn "bootstrap missing"; failed="true"; }
  [ -f "$OWNERSHIP_MANIFEST" ] && say "ownership manifest: OK" || { warn "ownership manifest missing (run aips harness install)"; failed="true"; }

  local id status capability
  for id in $(harness_host_ids); do
    status="$(adapter_status_value "$id" 2>/dev/null || echo NOT_DETECTED)"
    capability="$(adapter_state_value "$id" capability 2>/dev/null || echo UNSUPPORTED)"
    say "$id: $status capability=$capability"
  done

  if [ "$(adapter_status_value codex 2>/dev/null || true)" = "AUTOMATIC" ] && [ ! -f "$OWNED_HOME/codex.block" ]; then
    warn "codex managed block ownership snapshot missing"; failed="true"
  fi
  if [ "$(adapter_status_value claude-code 2>/dev/null || true)" = "AUTOMATIC" ] && [ ! -f "$OWNED_HOME/claude-code.block" ]; then
    warn "claude managed block ownership snapshot missing"; failed="true"
  fi
  if [ "$(adapter_state_value gemini-cli capability 2>/dev/null || true)" = "TURN_NATIVE" ]; then
    command -v gemini >/dev/null 2>&1 && gemini extensions list 2>/dev/null | grep -q "aips-global-harness" || { warn "gemini TURN_NATIVE adapter not verifiable"; failed="true"; }
  fi
  if [ "$(adapter_status_value opencode 2>/dev/null || true)" != "NOT_DETECTED" ]; then
    "$(python_bin)" "$SYSTEM_DIR/scripts/opencode_skill_projection.py" doctor || failed="true"
    "$(python_bin)" "$SYSTEM_DIR/scripts/portable_commands.py" status --host opencode >/dev/null || failed="true"
  fi
  [ "$failed" = "false" ]
}

harness_resolve() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  "$py" "$SYSTEM_DIR/scripts/harness_resolve.py" "$@"
}

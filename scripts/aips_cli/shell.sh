shell_profile_path() {
  if [ -n "${AIPS_SHELL_PROFILE:-}" ]; then
    printf '%s\n' "$AIPS_SHELL_PROFILE"
    return 0
  fi

  case "$(basename "${SHELL:-}")" in
    zsh) printf '%s/.zprofile\n' "$HOME" ;;
    bash)
      if [ "$(uname -s 2>/dev/null || true)" = "Darwin" ]; then
        printf '%s/.bash_profile\n' "$HOME"
      else
        printf '%s/.bashrc\n' "$HOME"
      fi
      ;;
    *) return 1 ;;
  esac
}

shell_single_quote() {
  printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"
}

preserve_file_mode() {
  local source="$1" target="$2" mode
  mode="$(stat -c '%a' "$source" 2>/dev/null || stat -f '%Lp' "$source" 2>/dev/null || true)"
  [ -z "$mode" ] || chmod "$mode" "$target"
}

desired_shell_block() {
  local quoted_bin
  quoted_bin="$(shell_single_quote "$BIN_HOME")"
  cat <<EOF
$SHELL_BLOCK_BEGIN
# Added by AIPS. Run 'aips shell uninstall' to remove this block.
case ":\${PATH:-}:" in
  *:${quoted_bin}:*) ;;
  *) export PATH=${quoted_bin}:\${PATH:-} ;;
esac
$SHELL_BLOCK_END
EOF
}

extract_shell_block() {
  local profile="$1"
  [ -f "$profile" ] || return 1
  awk -v begin="$SHELL_BLOCK_BEGIN" -v end="$SHELL_BLOCK_END" '
    $0 == begin {capture=1}
    capture {print}
    $0 == end && capture {found=1; exit}
    END {if (!found) exit 1}
  ' "$profile"
}

shell_block_count() {
  local profile="$1"
  [ -f "$profile" ] || { printf '0\n'; return 0; }
  awk -v begin="$SHELL_BLOCK_BEGIN" '$0 == begin {count++} END {print count+0}' "$profile"
}

shell_integration_state() {
  local profile expected existing recorded_bin
  profile="$(shell_profile_path 2>/dev/null || true)"
  if [ -f "$SHELL_PROFILE_RECORD" ]; then
    profile="$(cat "$SHELL_PROFILE_RECORD")"
  fi
  if [ -f "$SHELL_BIN_HOME_RECORD" ]; then
    recorded_bin="$(cat "$SHELL_BIN_HOME_RECORD")"
  else
    recorded_bin="$BIN_HOME"
  fi

  if [ -n "$profile" ] && [ -f "$SHELL_BLOCK_RECORD" ]; then
    expected="$(cat "$SHELL_BLOCK_RECORD")"
    existing="$(extract_shell_block "$profile" 2>/dev/null || true)"
    if [ "$(shell_block_count "$profile")" -gt 1 ]; then
      printf 'MODIFIED|%s|%s\n' "$profile" "$recorded_bin"
    elif [ -n "$existing" ] && [ "$existing" = "$expected" ]; then
      printf 'MANAGED|%s|%s\n' "$profile" "$recorded_bin"
    elif [ -n "$existing" ]; then
      printf 'MODIFIED|%s|%s\n' "$profile" "$recorded_bin"
    else
      printf 'MISSING|%s|%s\n' "$profile" "$recorded_bin"
    fi
  elif [[ ":$PATH:" == *":$BIN_HOME:"* ]]; then
    printf 'ACTIVE_UNMANAGED|%s|%s\n' "$profile" "$BIN_HOME"
  else
    printf 'NOT_CONFIGURED|%s|%s\n' "$profile" "$BIN_HOME"
  fi
}

shell_install() {
  local profile recorded_profile desired existing expected created="false" temp
  profile="$(shell_profile_path 2>/dev/null || true)"
  [ -n "$profile" ] || die "Unsupported shell '${SHELL:-unknown}'. Set AIPS_SHELL_PROFILE to the profile file to manage."
  if [ -L "$profile" ]; then
    profile="$(canonical_path "$profile" || true)"
    [ -n "$profile" ] || die "Shell profile symlink cannot be resolved safely."
  fi
  mkdir -p "$(dirname "$profile")" "$SHELL_STATE_HOME"
  if [ -f "$SHELL_PROFILE_RECORD" ]; then
    recorded_profile="$(cat "$SHELL_PROFILE_RECORD")"
    [ "$recorded_profile" = "$profile" ] || die "AIPS already manages a different shell profile: $recorded_profile"
  fi
  [ -e "$profile" ] || created="true"
  if [ -f "$SHELL_PROFILE_CREATED_RECORD" ]; then
    created="$(cat "$SHELL_PROFILE_CREATED_RECORD")"
  fi
  desired="$(desired_shell_block)"
  existing="$(extract_shell_block "$profile" 2>/dev/null || true)"

  if [ -n "$existing" ]; then
    [ "$(shell_block_count "$profile")" -eq 1 ] || die "Multiple AIPS shell blocks exist in $profile; leaving them untouched."
    if [ ! -f "$SHELL_BLOCK_RECORD" ]; then
      die "An unowned AIPS shell block already exists in $profile; leaving it untouched."
    fi
    expected="$(cat "$SHELL_BLOCK_RECORD")"
    [ "$existing" = "$expected" ] || die "The AIPS shell block in $profile was modified; leaving it untouched."
    if [ "$existing" != "$desired" ]; then
      temp="$(mktemp "${profile}.aips.XXXXXX")"
      awk -v begin="$SHELL_BLOCK_BEGIN" -v end="$SHELL_BLOCK_END" '
        $0 == begin {skip=1; next}
        skip && $0 == end {skip=0; next}
        !skip {print}
      ' "$profile" > "$temp"
      while [ -s "$temp" ] && [ "$(tail -n 1 "$temp")" = "" ]; do
        sed -i.bak '$d' "$temp" && rm -f "${temp}.bak"
      done
      [ ! -s "$temp" ] || printf '\n' >> "$temp"
      printf '%s\n' "$desired" >> "$temp"
      preserve_file_mode "$profile" "$temp"
      mv "$temp" "$profile"
    fi
  else
    temp="$(mktemp "${profile}.aips.XXXXXX")"
    if [ -e "$profile" ]; then
      cat "$profile" > "$temp"
      preserve_file_mode "$profile" "$temp"
    else
      chmod 600 "$temp"
    fi
    if [ -s "$temp" ] && [ "$(tail -c 1 "$temp" 2>/dev/null || true)" != "" ]; then
      printf '\n' >> "$temp"
    fi
    [ ! -s "$temp" ] || printf '\n' >> "$temp"
    printf '%s\n' "$desired" >> "$temp"
    mv "$temp" "$profile"
  fi

  printf '%s\n' "$profile" > "$SHELL_PROFILE_RECORD"
  printf '%s\n' "$desired" > "$SHELL_BLOCK_RECORD"
  printf '%s\n' "$BIN_HOME" > "$SHELL_BIN_HOME_RECORD"
  printf '%s\n' "$created" > "$SHELL_PROFILE_CREATED_RECORD"
  say "Shell integration installed: $profile"
  say "Open a new terminal or run: source \"$profile\""
}

shell_uninstall() {
  local force="${1:-false}" profile expected existing recorded_bin created temp remaining
  if [ ! -f "$SHELL_PROFILE_RECORD" ] || [ ! -f "$SHELL_BLOCK_RECORD" ]; then
    say "Shell integration: nothing managed by AIPS"
    return 0
  fi
  profile="$(cat "$SHELL_PROFILE_RECORD")"
  expected="$(cat "$SHELL_BLOCK_RECORD")"
  recorded_bin="$(cat "$SHELL_BIN_HOME_RECORD" 2>/dev/null || printf '%s' "$BIN_HOME")"
  created="$(cat "$SHELL_PROFILE_CREATED_RECORD" 2>/dev/null || printf 'false')"
  existing="$(extract_shell_block "$profile" 2>/dev/null || true)"

  if [ "$(shell_block_count "$profile")" -gt 1 ]; then
    warn "Multiple AIPS shell blocks exist in $profile; preserving them for manual review."
    return 1
  fi
  if [ -n "$existing" ] && [ "$existing" != "$expected" ]; then
    warn "The AIPS shell block in $profile was modified; preserving it."
    return 1
  fi
  if [ -z "$existing" ]; then
    warn "The recorded AIPS shell block is absent from $profile; clearing stale ownership metadata."
    rm -rf "$SHELL_STATE_HOME"
    return 0
  fi

  remaining="$(find "$recorded_bin" -mindepth 1 -maxdepth 1 ! -name aips -print -quit 2>/dev/null || true)"
  if [ "$force" != "true" ] && [ -n "$remaining" ]; then
    warn "Preserving shell PATH integration because $recorded_bin contains other entries."
    warn "Run 'aips shell uninstall' or 'aips uninstall --remove-shell-integration' to remove it explicitly."
    return 0
  fi

  temp="$(mktemp "${profile}.aips.XXXXXX")"
  awk -v begin="$SHELL_BLOCK_BEGIN" -v end="$SHELL_BLOCK_END" '
    $0 == begin {skip=1; next}
    skip && $0 == end {skip=0; next}
    !skip {lines[++count]=$0}
    END {
      while (count > 0 && lines[count] == "") count--
      for (i=1; i<=count; i++) print lines[i]
    }
  ' "$profile" > "$temp"
  preserve_file_mode "$profile" "$temp"
  if [ ! -s "$temp" ] && [ "$created" = "true" ]; then
    rm -f "$profile" "$temp"
  else
    mv "$temp" "$profile"
  fi
  rm -rf "$SHELL_STATE_HOME"
  say "Shell integration removed: $profile"
}

shell_status() {
  local state status profile recorded_bin
  state="$(shell_integration_state)"
  IFS='|' read -r status profile recorded_bin <<< "$state"
  say "Shell integration: $status"
  [ -n "$profile" ] && say "Profile: $profile"
  say "CLI directory: $recorded_bin"
}

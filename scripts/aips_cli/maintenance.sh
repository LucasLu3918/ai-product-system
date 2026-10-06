update_system() {
  local allow_major="${1:-false}"
  require_cmd git
  [ -d "$SYSTEM_DIR/.git" ] || die "System directory is not a Git repository: $SYSTEM_DIR"

  local branch channel target_ref remote_version target_sha info status tag expected_sha
  branch="$(git_in_system branch --show-current)"
  channel="$(installed_channel)"
  case "$channel" in
    stable)
      [ -z "$branch" ] || [ "$branch" = "$DEFAULT_BRANCH" ] || die "Stable-channel system repo has unexpected branch '$branch'."
      ;;
    main)
      [ "$branch" = "$DEFAULT_BRANCH" ] || { [ -z "$branch" ] || die "System repo must be on '$DEFAULT_BRANCH' before automatic update (current: $branch)."; }
      ;;
    branch:*)
      local requested_branch="${channel#branch:}"
      [ "$branch" = "$requested_branch" ] || die "System repo must be on '$requested_branch' before automatic update (current: $branch)."
      ;;
    *) die "Unknown installed update channel metadata." ;;
  esac

  if [ -n "$(git_in_system status --porcelain)" ]; then
    die "System repo has local changes. Commit/stash/revert them before Update Preflight."
  fi

  say "Checking latest AI Product System..."
  local local_version local_major remote_major before after
  local_version="$(current_version)"
  case "$channel" in
    stable)
      if info="$(python3 "$SYSTEM_DIR/scripts/release_channel.py" resolve --remote "$(git_in_system remote get-url origin)")"; then
        tag="${info%%$'\t'*}"
        expected_sha="${info#*$'\t'}"
        git_in_system fetch --quiet origin "refs/tags/$tag:refs/tags/$tag" || die "Could not fetch stable tag $tag."
        python3 "$SYSTEM_DIR/scripts/release_channel.py" verify --repository "$SYSTEM_DIR" --tag "$tag" --expected-sha "$expected_sha" >/dev/null || die "Stable tag $tag failed exact commit/VERSION verification."
        target_ref="refs/tags/$tag"
      else
        status=$?
        if [ "$status" -ne 3 ]; then die "Stable release lookup failed; no update was applied."; fi
        die "No stable release tag exists yet; stable update was not applied. Explicitly choose the main development channel only if you want mutable updates."
      fi
      ;;
  esac
  if [ "$channel" = main ]; then
    git_in_system fetch --quiet origin "$DEFAULT_BRANCH"
    target_ref="origin/$DEFAULT_BRANCH"
  elif [[ "$channel" == branch:* ]]; then
    local requested_branch="${channel#branch:}"
    git_in_system fetch --quiet origin "$requested_branch"
    target_ref="origin/$requested_branch"
  fi
  remote_version="$(git_in_system show "$target_ref:VERSION" 2>/dev/null | tr -d '[:space:]')" || die "Target VERSION could not be read."
  target_sha="$(git_in_system rev-parse "$target_ref")" || die "Target revision could not be resolved."
  local_major="$(major_of "$local_version")"
  remote_major="$(major_of "$remote_version")"

  if [ "$local_major" != "$remote_major" ] && [ "$allow_major" != "true" ]; then
    die "Major version change detected ($local_version -> $remote_version). Review CHANGELOG.md, then rerun with --allow-major."
  fi

  before="$(current_commit)"
  if [ "$before" != "$target_sha" ]; then
    if ! git_in_system merge-base --is-ancestor HEAD "$target_ref"; then
      die "Target history diverged from the installed commit. Automatic rollback, merge, or rebase is disabled."
    fi
    case "$channel" in
      stable) git_in_system checkout --quiet --detach "$target_ref" ;;
      main) checkout_main_channel ;;
      branch:*) git_in_system pull --ff-only --quiet origin "${channel#branch:}" ;;
    esac
  elif [ "$channel" = main ] && [ "$branch" != "$DEFAULT_BRANCH" ]; then
    checkout_main_channel
  elif [ "$channel" = stable ] && [ "$branch" != "" ]; then
    git_in_system checkout --quiet --detach "$target_ref"
  fi
  after="$(current_commit)"

  if [ "$before" = "$after" ]; then
    say "System already up to date: $(current_version) ($after)"
  else
    say "System updated: $local_version -> $(current_version)"
    say "Commit: $after"
  fi

  repair_runtime_dependencies_if_installed
}

preflight_after_update() {
  local project="$1"
  [ -d "$project" ] || die "Project path does not exist: $project"

  refresh_harness_if_installed

  if [ -d "$project/.ai" ]; then
    write_system_snapshot "$project"
    say "Project mode: ATTACHED"
  else
    say "Project mode: EPHEMERAL (no .ai workspace created)."
    say "Use 'aips attach \"$project\"' only when persistent AIPS state is desired."
  fi

  validate_repo
  say "Update Preflight passed."
  say "System: $(current_version) ($(current_commit))"
  say "Project: $project"
}

preflight() {
  local project="${1:-}"
  local allow_major="false"
  [ -n "$project" ] || die "Usage: aips preflight <project-path> [--allow-major]"
  shift || true

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --allow-major) allow_major="true" ;;
      *) die "Unknown preflight option: $1" ;;
    esac
    shift
  done

  update_system "$allow_major"
  exec "$SYSTEM_DIR/bin/aips" _preflight-after-update "$project"
}

doctor() {
  local failed="false" runtime_py runtime_version
  say "AI Product System doctor"
  say "System dir: $SYSTEM_DIR"
  say "Version: $(current_version 2>/dev/null || echo unknown)"
  say "Commit: $(current_commit 2>/dev/null || echo unknown)"
  say "Branch: $(git_in_system branch --show-current 2>/dev/null || echo unknown)"

  command -v git >/dev/null 2>&1 && say "git: OK" || { warn "git: missing"; failed="true"; }
  command -v python3 >/dev/null 2>&1 && say "python3: OK" || { warn "python3: missing"; failed="true"; }
  if [ -x "$SYSTEM_DIR/.venv/bin/python" ]; then
    runtime_py="$SYSTEM_DIR/.venv/bin/python"
  else
    runtime_py="$(command -v python3 || true)"
  fi
  if [ -n "$runtime_py" ]; then
    runtime_version="$("$runtime_py" --version 2>&1 || echo unknown)"
    if "$runtime_py" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' >/dev/null 2>&1; then
      say "runtime Python: OK ($runtime_version)"
    else
      warn "runtime Python: UNSUPPORTED ($runtime_version; AIPS requires Python >=3.12; run aips install with a compatible interpreter)"
      failed="true"
    fi
  else
    warn "runtime Python: MISSING (AIPS requires Python >=3.12)"
    failed="true"
  fi
  [ -x "$SYSTEM_DIR/.venv/bin/python" ] && say "venv: OK" || { warn "venv: not installed (run aips install)"; failed="true"; }
  if runtime_dependencies_available; then
    say "runtime dependencies: OK (PyYAML, MCP)"
  else
    warn "runtime dependencies: INCOMPLETE (PyYAML and MCP are required; run $SYSTEM_DIR/bin/aips install)"
    failed="true"
  fi
  if runtime_dependencies_available && [ -f "$SYSTEM_DIR/scripts/mcp_server.py" ]; then
    say "MCP gateway: AVAILABLE (stdio, ADVISORY)"
  else
    warn "MCP gateway dependency/server missing; run aips install."
    failed="true"
  fi
  openapi_dependency_status

  if [ -n "$(git_in_system status --porcelain 2>/dev/null || true)" ]; then
    warn "System repo has local changes; automatic preflight update will stop."
  else
    say "system worktree: clean"
  fi

  if [ -L "$BIN_HOME/aips" ]; then
    say "CLI link: OK ($BIN_HOME/aips)"
  else
    warn "CLI link not installed at $BIN_HOME/aips"
  fi

  if [[ ":$PATH:" == *":$BIN_HOME:"* ]]; then
    say "CLI discoverability: OK ($BIN_HOME is in PATH)"
  else
    warn "CLI discoverability: WARNING ($BIN_HOME is not in PATH)"
  fi
  local shell_state shell_status_value shell_profile_value shell_bin_value
  shell_state="$(shell_integration_state)"
  IFS='|' read -r shell_status_value shell_profile_value shell_bin_value <<< "$shell_state"
  case "$shell_status_value" in
    MANAGED) say "Shell integration: MANAGED ($shell_profile_value)" ;;
    ACTIVE_UNMANAGED) say "Shell integration: ACTIVE_UNMANAGED" ;;
    MODIFIED) warn "Shell integration: MODIFIED ($shell_profile_value; preserved)" ;;
    MISSING) warn "Shell integration: MISSING ($shell_profile_value)" ;;
    *) warn "Shell integration: NOT_CONFIGURED (run $BIN_HOME/aips shell install)" ;;
  esac

  if ! harness_doctor; then
    warn "Harness doctor reported issues."
    failed="true"
  fi

  [ "$failed" = "false" ]
}

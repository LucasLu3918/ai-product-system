intelligence_cmd() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  "$py" "$SYSTEM_DIR/scripts/project_intelligence.py" "$@"
}

run_state_cmd() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  "$py" "$SYSTEM_DIR/scripts/run_state.py" "$@"
}

run_projection_cmd() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  "$py" "$SYSTEM_DIR/scripts/run_projection.py" "$@"
}

telemetry_cmd() {
  local py sub
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  sub="${1:-help}"
  shift || true
  case "$sub" in
    help|-h|--help)
      cat <<'EOF'
Usage: aips telemetry <record|export|replay> [options]

  record  Append bounded lifecycle metadata to an existing run event stream.
  export  Create an offline OTLP/HTTP JSON projection or explicitly send it.
  replay  Re-project the same run with deterministic trace and span IDs.

Command-specific options: `aips telemetry <command> --help`.
EOF
      ;;
    record) "$py" "$SYSTEM_DIR/scripts/telemetry_record.py" "$@" ;;
    export|replay) "$py" "$SYSTEM_DIR/scripts/telemetry_export.py" "$sub" "$@" ;;
    *) die "Unknown telemetry command: $sub" ;;
  esac
}

run_dashboard_cmd() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  local project="."
  local open_browser=0
  local args=()
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --project) project="$2"; shift 2; args+=(--project "$project") ;;
      --open) open_browser=1; args+=(--open); shift ;;
      *) args+=("$1"); shift ;;
    esac
  done
  "$py" "$SYSTEM_DIR/scripts/run_dashboard.py" "${args[@]}" &
  local pid=$!
  trap 'kill "$pid" 2>/dev/null || true' EXIT INT TERM
  wait "$pid"
}

conformance_cmd() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  if [ "${1:-}" = "summary" ]; then
    shift
    "$py" "$SYSTEM_DIR/scripts/conformance_summary.py" "$@"
    return
  fi
  "$py" "$SYSTEM_DIR/scripts/scenario_conformance.py" "$@"
}

agent_eval_cmd() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  "$py" "$SYSTEM_DIR/scripts/agent_eval.py" "$@"
}

eval_interop_cmd() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  "$py" "$SYSTEM_DIR/scripts/eval_interop.py" "$@"
}

trajectory_eval_cmd() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  "$py" "$SYSTEM_DIR/scripts/trajectory_eval.py" "$@"
}

resource_authorization_cmd() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  "$py" "$SYSTEM_DIR/scripts/resource_authorization.py" "$@"
}

runtime_policy_cmd() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  "$py" "$SYSTEM_DIR/scripts/runtime_policy.py" "$@"
}

isolation_cmd() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  "$py" "$SYSTEM_DIR/scripts/execution_isolation.py" "$@"
}

scheduler_cmd() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  "$py" "$SYSTEM_DIR/scripts/deterministic_scheduler.py" "$@"
}

integration_gate_cmd() {
  local py
  local selected_root=""
  local -a gate_args=()
  while [ "$#" -gt 0 ]; do
    if [ "$1" = "--project-root" ]; then
      [ "$#" -ge 2 ] || die "--project-root requires a repository path."
      selected_root="$2"
      shift 2
    else
      gate_args+=("$1")
      shift
    fi
  done
  local command_root="$SYSTEM_DIR"
  if [ -n "$selected_root" ]; then
    command_root="$(cd "$selected_root" 2>/dev/null && pwd -P)" || die "Cannot resolve --project-root: $selected_root"
    [ -f "$command_root/scripts/integration_gate.py" ] || die "--project-root is not an AIPS repository: $command_root"
    say "Integration Gate project root: $command_root" >&2
    py="$(validation_python_for_root "$command_root" true || true)"
  else
    py="$(validation_python_for_root "$command_root" true || true)"
  fi
  [ -n "$py" ] || die "No complete Python 3.12 validation environment found for $command_root. Set AIPS_VALIDATION_VENV or AIPS_VALIDATION_PYTHON, or run python3.12 bin/prepare-local-validation; inspect blockers with aips publish environment --project-root $command_root."
  if [ "${#gate_args[@]}" -gt 0 ]; then
    set -- "${gate_args[@]}"
  else
    set --
  fi
  PATH="$(dirname "$py"):$PATH" "$py" "$command_root/scripts/integration_gate.py" "$@"
}

publish_preflight_cmd() {
  local action="${1:-plan}"
  local py
  local selected_root=""
  local -a publish_args=()
  shift || true
  while [ "$#" -gt 0 ]; do
    if [ "$1" = "--project-root" ]; then
      [ "$#" -ge 2 ] || die "--project-root requires a repository path."
      selected_root="$2"
      shift 2
    else
      publish_args+=("$1")
      shift
    fi
  done
  [ "$action" != "preflight" ] || action="run"
  local command_root="$SYSTEM_DIR"
  if [ -z "$selected_root" ]; then
    selected_root="$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || true)"
    if [ -z "$selected_root" ] || [ ! -f "$selected_root/scripts/publish_preflight.py" ]; then
      selected_root=""
      if [ "$action" = "matrix-sync" ] || [ "$action" = "post-merge" ] || [ "$action" = "docs-impact" ]; then
        die "Run publish $action from an AIPS checkout or pass --project-root <repo>."
      fi
    fi
  fi
  if [ -n "$selected_root" ]; then
    command_root="$(cd "$selected_root" 2>/dev/null && pwd -P)" || die "Cannot resolve --project-root: $selected_root"
    [ -f "$command_root/scripts/publish_preflight.py" ] || die "--project-root is not an AIPS repository: $command_root"
    say "Publish preflight project root: $command_root" >&2
    case "$action" in
      plan|run|environment)
        py="$(validation_python_for_root "$command_root" true || validation_python_for_root "$command_root" false || true)" ;;
      *) py="$(validation_python_for_root "$command_root" false || true)" ;;
    esac
  else
    py="$(python_bin)"
  fi
  if [ -z "$py" ] && [ -n "${AIPS_VALIDATION_PYTHON:-}${AIPS_VALIDATION_VENV:-}" ]; then
    die "Explicit validation Python is unavailable or invalid; repair the selected environment before publication."
  fi
  [ -n "$py" ] || py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  local script_root="$command_root"
  [ "$action" != "post-merge" ] || script_root="$SYSTEM_DIR"
  say "Publish runtime: launcher=$SYSTEM_DIR source=$script_root target=$command_root python=$py" >&2
  "$py" -c 'import yaml' >/dev/null 2>&1 || die "The Python selected for $command_root ($py) lacks PyYAML. Run `python3.12 bin/prepare-local-validation` in that checkout, then retry."
  if [ "$action" = "post-merge" ]; then
    if [ "${#publish_args[@]}" -gt 0 ]; then
      AIPS_INSTALLED_SYSTEM_DIR="$(cat "$CONFIG_HOME/system-dir" 2>/dev/null || true)" PATH="$(dirname "$py"):$PATH" "$py" "$SYSTEM_DIR/scripts/publish_preflight.py" "$action" --project-root "$command_root" "${publish_args[@]}"
    else
      AIPS_INSTALLED_SYSTEM_DIR="$(cat "$CONFIG_HOME/system-dir" 2>/dev/null || true)" PATH="$(dirname "$py"):$PATH" "$py" "$SYSTEM_DIR/scripts/publish_preflight.py" "$action" --project-root "$command_root"
    fi
    return
  fi
  if [ "${#publish_args[@]}" -gt 0 ]; then
    PATH="$(dirname "$py"):$PATH" "$py" "$command_root/scripts/publish_preflight.py" "$action" "${publish_args[@]}"
  else
    PATH="$(dirname "$py"):$PATH" "$py" "$command_root/scripts/publish_preflight.py" "$action"
  fi
}

docs_cmd() {
  local action="${1:-}"
  shift || true
  [ "$action" = "impact" ] || die "Usage: aips docs impact --base <ref> [--head <ref>]"
  publish_preflight_cmd docs-impact "$@"
}

evolution_cmd() {
  local action="${1:-}"
  [ -n "$action" ] || die "Usage: aips evolution <package|analyze|apply> [evolution analysis options]"
  shift || true
  case "$action" in
    package|apply)
      python3 "$SYSTEM_DIR/scripts/evolution_analysis.py" "$action" "$@"
      ;;
    analyze)
      python3 "$SYSTEM_DIR/scripts/evolution_analysis.py" finalize "$@"
      ;;
    *)
      die "Unsupported Evolution action: $action (expected package, analyze or apply)"
      ;;
  esac
}

openapi_cmd() {
  local action="${1:---help}" py script
  shift || true
  case "$action" in
    help|-h|--help)
      say "Usage: aips openapi <doctor|install|validate|compare|run-contract-tests|verify-evidence|generator> ..."
      say "Run from the product repository and pass --repo-root <product-root>."
      return ;;
    doctor)
      openapi_dependency_status
      return ;;
    install)
      ensure_compatible_venv
      py="$SYSTEM_DIR/.venv/bin/python"
      [ -r "$SYSTEM_DIR/requirements-openapi.txt" ] || die "OpenAPI optional requirements are missing: $SYSTEM_DIR/requirements-openapi.txt"
      "$py" "$SYSTEM_DIR/scripts/package_install.py" --python "$py" --requirements "$SYSTEM_DIR/requirements-openapi.txt" ||
        die "OpenAPI optional dependency installation failed."
      "$py" -c 'import openapi_spec_validator, jsonschema' >/dev/null 2>&1 ||
        die "OpenAPI optional dependencies are incomplete after installation."
      say "OpenAPI optional dependencies: installed in $py"
      return ;;
    generator) script="openapi_generator_adapter.py" ;;
    validate|compare|run-contract-tests|verify-evidence)
      script="openapi_contracts.py"
      set -- "$action" "$@"
      py="$(python_bin)"
      [ -n "$py" ] || die "python3 is required."
      "$py" -c 'import openapi_spec_validator, jsonschema' >/dev/null 2>&1 ||
        die "OpenAPI optional dependencies are missing from the selected AIPS Python ($py). Run: aips openapi install"
      "$py" "$SYSTEM_DIR/scripts/$script" "$@"
      return ;;
    *) die "Unknown OpenAPI action: $action. Run aips openapi --help." ;;
  esac
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  "$py" "$SYSTEM_DIR/scripts/$script" "$@"
}

mcp_cmd() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  "$py" "$SYSTEM_DIR/scripts/mcp_server.py" "$@"
}

portable_commands_cmd() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  "$py" "$SYSTEM_DIR/scripts/portable_commands.py" "$@"
}

identity_cmd() {
  local py
  py="$(python_bin)"
  [ -n "$py" ] || die "python3 is required."
  "$py" "$SYSTEM_DIR/scripts/aips_identity.py" show "$@"
}

refresh_harness_if_installed() {
  # system-dir is created only by AIPS install. A plain repository checkout
  # must not register global Agent integrations implicitly.
  if [ -f "$CONFIG_HOME/system-dir" ]; then
    say "Refreshing AIPS Global Harness for the installed system..."
    harness_install
  fi
}

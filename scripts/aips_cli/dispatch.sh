case "${1:-help}" in
  install)
    shift
    install_cli "$@"
    ;;
  uninstall)
    shift
    uninstall_cli "$@"
    ;;
  shell)
    sub="${2:-status}"
    shift 2 || true
    case "$sub" in
      help|-h|--help)
        say "Usage: aips shell <install|uninstall|status>"
        ;;
      install) shell_install "$@" ;;
      uninstall) shell_uninstall true ;;
      status) shell_status ;;
      *) die "Unknown shell command: $sub" ;;
    esac
    ;;
  harness)
    sub="${2:-status}"
    case "$sub" in
      install)
        harness_install
        ;;
      uninstall)
        harness_uninstall
        ;;
      status)
        harness_status
        ;;
      help|-h|--help)
        say "Usage: aips harness <install|uninstall|status|doctor|resolve|trace> [options]"
        ;;
      doctor)
        harness_doctor
        ;;
      resolve)
        shift 2
        harness_resolve "$@"
        ;;
      trace)
        shift 2
        "$(python_bin)" "$SYSTEM_DIR/scripts/opencode_trace.py" "$@"
        ;;
      *)
        die "Unknown harness command: $sub"
        ;;
    esac
    ;;
  creative)
    sub="${2:-help}"
    shift 2 || true
    case "$sub" in
      scan|next-version)
        "$(python_bin)" "$SYSTEM_DIR/scripts/creative_workspace_profile.py" "$sub" "$@"
        ;;
      preflight|execute|review|trace)
        "$(python_bin)" "$SYSTEM_DIR/scripts/creative_execution.py" "$sub" "$@"
        ;;
      help|-h|--help)
        say "Usage: aips creative <scan|next-version|preflight|execute|review|trace> [options]"
        ;;
      *) die "Unknown creative command: $sub" ;;
    esac
    ;;
  mcp)
    sub="${2:-inspect}"
    shift 2 || true
    case "$sub" in
      serve|inspect)
        mcp_cmd "$sub" "$@"
        ;;
      help|-h|--help)
        mcp_cmd --help
        ;;
      config)
        mcp_cmd config "$@"
        ;;
      *)
        die "Unknown mcp command: $sub"
        ;;
    esac
    ;;
  commands)
    shift
    portable_commands_cmd "$@"
    ;;
  intelligence)
    sub="${2:-status}"
    shift 2 || true
    intelligence_cmd "$sub" "$@"
    ;;
  project)
    sub="${2:-}"
    shift 2 || true
    case "$sub" in
      help|-h|--help)
        say "Usage: aips project check <project-path>"
        ;;
      check)
        [ "$#" -eq 1 ] || die "Usage: aips project check <project-path>"
        project_check "$1"
        ;;
      *) die "Unknown project command: $sub" ;;
    esac
    ;;
  system)
    sub="${2:-}"
    shift 2 || true
    case "$sub" in
      preflight) preflight "$@" ;;
      help|-h|--help) say "Usage: aips system preflight <project-path> [--allow-major]" ;;
      *) die "Unknown system command: $sub" ;;
    esac
    ;;
  run)
    sub="${2:-status}"
    shift 2 || true
    case "$sub" in
      list|inspect)
        run_projection_cmd "$sub" "$@"
        ;;
      dashboard)
        run_dashboard_cmd "$@"
        ;;
      *)
        run_state_cmd "$sub" "$@"
        ;;
    esac
    ;;
  telemetry)
    shift
    telemetry_cmd "$@"
    ;;
  conformance)
    sub="${2:-report}"
    if [ "$sub" = "agent-eval" ]; then
      action="${3:-report}"
      shift 3 || true
      agent_eval_cmd "$action" "$@"
    else
      shift 2 || true
      conformance_cmd "$sub" "$@"
    fi
    ;;
  eval)
    shift
    eval_interop_cmd "$@"
    ;;
  trajectory)
    action="${2:-evaluate}"
    shift 2 || true
    trajectory_eval_cmd "$action" "$@"
    ;;
  authorization)
    sub="${2:-}"
    [ -n "$sub" ] || die "Usage: aips authorization <validate|check> ..."
    shift 2 || true
    resource_authorization_cmd "$sub" "$@"
    ;;
  runtime-policy)
    sub="${2:-}"
    [ -n "$sub" ] || die "Usage: aips runtime-policy evaluate --action ACTION.yaml [--policy POLICY.yaml]"
    shift 2 || true
    runtime_policy_cmd "$sub" "$@"
    ;;
  isolation)
    sub="${2:-}"
    [ -n "$sub" ] || die "Usage: aips isolation <resolve|create|status|runtime-lease|runtime-reallocate|runtime-release|runtime-reconcile|remove> ..."
    shift 2 || true
    isolation_cmd "$sub" "$@"
    ;;
  scheduler)
    shift
    scheduler_cmd "$@"
    ;;
  integration-gate|janitor)
    shift
    integration_gate_cmd "$@"
    ;;
  publish)
    shift
    publish_preflight_cmd "$@"
    ;;
  evolution)
    shift
    evolution_cmd "$@"
    ;;
  docs)
    shift
    docs_cmd "$@"
    ;;
  openapi)
    shift
    openapi_cmd "$@"
    ;;
  identity)
    shift
    identity_cmd "$@"
    ;;
  attach)
    [ "$#" -ge 2 ] || die "Usage: aips attach <project-path>"
    attach_project "$2"
    ;;
  detach)
    [ "$#" -ge 2 ] || die "Usage: aips detach <project-path>"
    detach_project "$2"
    ;;
  status)
    [ "$#" -ge 2 ] || die "Usage: aips status <project-path>"
    status_project "$2"
    ;;
  init)
    [ "$#" -ge 2 ] || die "Usage: aips init <project-path>"
    attach_project "$2"
    ;;
  update)
    shift
    allow="false"
    [ "${1:-}" = "--allow-major" ] && allow="true"
    update_system "$allow"
    exec "$SYSTEM_DIR/bin/aips" _refresh-harness-after-update
    ;;
  preflight)
    shift
    preflight "$@"
    ;;
  _preflight-after-update)
    shift
    preflight_after_update "$1"
    ;;
  _refresh-harness-after-update)
    refresh_harness_if_installed
    ;;
  doctor)
    doctor
    ;;
  validate)
    shift
    if [ "$#" -eq 1 ]; then
      case "$1" in
        help|-h|--help) say "Usage: aips validate (validate the installed AIPS repository)"; exit 0 ;;
      esac
    fi
    [ "$#" -eq 0 ] || die "Unknown validate arguments. Run aips validate --help."
    validate_repo
    ;;
  version)
    say "$(current_version) ($(current_commit))"
    ;;
  help|-h|--help)
    usage
    ;;
  *)
    die "Unknown command: $1. Run 'aips help'."
    ;;
esac

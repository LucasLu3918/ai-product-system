usage() {
  cat <<'EOF'
AI Product System CLI

Usage:
  aips install [--configure-shell|--no-configure-shell]
  aips uninstall [--remove-venv] [--remove-cache] [--remove-shell-integration]
  aips system preflight <project-path> [--allow-major]
  aips project check <project-path>
  aips project diagnose <project-path> [--runtime codex|opencode|claude-code|gemini-cli|unknown] [--format text|yaml|json]
  aips preflight <project-path> [--allow-major]  (compatibility alias)

  aips shell install
  aips shell uninstall
  aips shell status

  aips harness install
  aips harness uninstall
  aips harness status
  aips harness doctor
  aips harness resolve [--runtime <id>] [--cwd <path>] [--project <path>] [--format yaml|json]
  aips harness trace [--limit 1..100]

  aips creative prepare --project <path> --scope <relative-path> --character-id <slug> --character-name <name> --summary <text> --style-intent <text> --prompt <text> --identity-feature <text> [--identity-feature <text> ...]
  aips creative scan --project <path>
  aips creative discover --project <path>
  aips creative configure --project <path> --bundle <relative-yaml> [--settings-json <allowlisted-json>] (defaults to stdin)
  aips creative next-version --project <path> --target <relative-asset-path>
  aips creative preflight --project <path> --bundle <relative-yaml>
  aips creative execute --project <path> --bundle <relative-yaml>
  aips creative generate-set --project <path> --manifest <relative-yaml> (continues failures; resumes verified successes)
  aips creative review --project <path> --manifest <relative-json> --reviewer <name> --decision <PASS|REVISE>
  aips creative review-assist --project <path> --manifest <relative-json> --model <installed-local-ollama-vision-model>
  aips creative trace [--limit 1..100]

  aips mcp serve
  aips mcp inspect
  aips mcp config [--client cursor|windsurf|copilot|amp|codex|generic]

  aips commands list
  aips commands inspect [<command-id>]
  aips commands render <command-id> [--host <host>]
  aips commands install [<command-id>] --host <host>
  aips commands status
  aips commands upgrade [<command-id>] --host <host>
  aips commands uninstall [--host <host>|--all]

  aips intelligence bootstrap [--project <path>]
  aips intelligence status [--project <path>]
  aips intelligence refresh [--project <path>]
  aips intelligence context --runtime <id> [--project <path>] [--prompt <text>] [--target-path <path>] [--intent auto|read|write] [--full] [--observe-run-id <id>]
  aips intelligence impact-init [--project <path>] [--prompt <text>] [--change-id <id>] [--reset]
  aips intelligence impact-traverse --seed <symbol> --risk-class <class> [--project <path>] [--seed-path <path>] [--direction callers|consumers]
  aips intelligence context-audit [--project <path>]
  aips intelligence impact-validate --project <path> --path <CHANGE_IMPACT.yaml>
  aips intelligence index [--project <path>] [--force]
  aips intelligence retrieve --prompt <text> [--project <path>] [--token-budget <n>] [--limit <n>] [--no-structural]
  aips intelligence evaluate --suite <yaml> [--project <path>] [--output <yaml|json>]
  aips intelligence reconcile-overrides [--project <path>]
  aips intelligence promotion-plan --topic <name> [--project <path>]
  aips intelligence promotion-apply --topic <name> --target <path> --approval-id <id> [--project <path>]
  aips intelligence render [--project <path>]
  aips intelligence temporal --mode <current|as-of|between|why> [--project <path>] [--revision <sha>] [--base <sha> --head <sha>] [--assertion <id>]

  aips run checkpoint --run-id <id> --step <step> [--project <path>]
  aips run event --run-id <id> --event <name> [--project <path>]
  aips run resume --run-id <id> [--project <path>]
  aips run status --run-id <id> [--project <path>]
  aips run owner <claim|heartbeat|status|authorize|release|reconcile|recover> --run-id <id> [--project <path>]
  aips run list [--project <path>]
  aips run inspect --run-id <id> [--project <path>]
  aips run dashboard [--project <path>] [--open]

  aips telemetry record [bounded lifecycle options]
  aips telemetry export|replay --run-id <id> --config <yaml> --send

  aips conformance check [--format yaml|json]
  aips conformance report [--format yaml|json]
  aips conformance summary <current|history> [--output <path>]
  aips conformance agent-eval check [--format yaml|json]
  aips conformance agent-eval report [--format yaml|json]
  aips conformance agent-eval consistency --case <yaml> --results-dir <dir> [--min-repetitions <n>] [--min-pass-rate <0..1>] [--format yaml|json]
  aips eval import-promptfoo --config <yaml> --results <jsonl> --output <yaml>
  aips eval export-promptfoo --case <yaml> --provider <built-in-id> --output <yaml>
  aips eval import-pyrit --bridge <yaml> --output <yaml>
  aips eval verify-evidence --evidence <yaml> [--config <yaml> --results <jsonl>]
  aips eval profile --change-class <class> [--area <class>] [--deep-pyrit]
  aips eval promote-finding --finding <yaml> --output <case.yaml>

  aips isolation resolve --mode auto|shared|worktree|sandbox [--risk normal|elevated|high|critical] [--untrusted-execution] [--data-class public|internal|confidential|restricted] [--project <path>] [--format yaml|json]
  aips isolation create --id <id> --boundary <id> [--mode worktree|sandbox] [--project <path>] [--ref <ref>] [--port <id>] [--preferred <port>] [--expose <ENV>]
  aips isolation status --id <id> [--project <path>] [--format yaml|json]
  aips isolation runtime-lease --id <id> --port <id> [--preferred <port>] [--expose <ENV>] [--project <path>]
  aips isolation runtime-reallocate --id <id> --port <id> [--project <path>]
  aips isolation runtime-release --id <id> [--port <id>] [--project <path>]
  aips isolation runtime-reconcile [--project <path>]
  aips isolation remove --id <id> [--project <path>] [--format yaml|json]

  aips scheduler --graph <yaml> [--state <yaml>] [--format yaml|json]
  aips integration-gate --profile <yaml> --base <ref> --head <ref> [--matrix <yaml>] [--review-trust-store <path>] [--observe-run-id <id>] [--output <path>] [--project-root <repo>]
  aips janitor --profile <yaml> --base <ref> --head <ref> [--matrix <yaml>] [--output <path>]
  aips publish preview|plan|preflight|matrix-sync|post-merge|checks [publish-preflight options] [--project-root <repo>]
  aips evolution package|analyze|apply [evolution analysis options]
  aips docs impact --base <ref> [--head <ref>] [--project-root <repo>] [--format yaml|json]
  aips openapi <doctor|install|validate|compare|run-contract-tests|verify-evidence|generator> ...

  aips identity [--project <path>] [--format yaml|json]

  aips attach <project-path>
  aips detach <project-path>
  aips status <project-path>
  aips init <project-path>        # backward-compatible alias for attach

  aips update [--allow-major]
  aips preflight <project-path> [--allow-major]
  aips doctor
  aips validate
  aips version
  aips help

Install enables the Global Harness for safely supported runtimes.
Uninstall removes only AIPS-owned runtime integrations and preserves user/project instructions and skills.

Project modes:
  EPHEMERAL  no project-local .ai/ is created; reusable Intelligence may live in AIPS external cache.
  ATTACHED   created explicitly with 'aips attach'; project-local persistent AIPS state is enabled.
EOF
}

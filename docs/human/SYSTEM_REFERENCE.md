# AIPS System Reference

This page lists factual command, capability and runtime data. Explanatory policy remains in the linked canonical documentation.

The established Retrieval Intelligence command/import facade remains `scripts/retrieval_intelligence.py`; internal lexical relation extraction lives in `scripts/retrieval_relations.py`. No public command or installation dependency is added.

<!-- AIPS-SYSTEM-FACTS:BEGIN -->
## Public commands

| Command | Capabilities | Platforms | Runtime | Optional dependencies | Validation | Documentation |
|---|---|---|---|---|---|---|
| `aips install` | execution-isolation, gemini-cli-observable-event-capture-trial, gemini-cli-real-runtime-verification, resource-authorization, turn-aware-global-harness | linux, macos, windows-wsl | Python ">=3.12" | None | tests/evidence/install_preflight_lifecycle.py | docs/human/INSTALLATION.md, docs/human/USER_GUIDE.md |
| `aips harness` | execution-isolation, gemini-cli-observable-event-capture-trial, gemini-cli-real-runtime-verification, resource-authorization, turn-aware-global-harness | linux, macos, windows-wsl | Python ">=3.12" | None | tests/evidence/harness_runtime_lifecycle.py | docs/human/HARNESS.md, docs/human/USER_GUIDE.md |
| `aips commands` | execution-isolation, gemini-cli-observable-event-capture-trial, gemini-cli-real-runtime-verification, resource-authorization, turn-aware-global-harness | linux, macos, windows-wsl | Python ">=3.12" | None | tests/evidence/harness_runtime_lifecycle.py | harness/PORTABLE_COMMANDS.md, docs/human/HARNESS.md |
| `aips intelligence` | canonical-project-identity, change-impact-guard, durable-run-state, project-intelligence | linux, macos, windows-wsl | Python ">=3.12" | None | tests/evidence/project_intelligence_lifecycle.py, tests/evidence/change_impact_resolution_lifecycle.py | docs/human/PROJECT_INTELLIGENCE.md, docs/human/USER_GUIDE.md |
| `aips publish` | agent-eval, runtime-invariant-matrix, scenario-conformance, unified-runtime-path-resolution, validation-interpreter-capability-selection | linux, macos | Python ">=3.12"; validation Gate uses Python 3.12 and Node 24 | requirements-visual.txt, requirements-openapi.txt, package-lock.json | scripts/repository_preflight.py, config/integration-gate.yaml, tests/evidence/publish_preflight_lifecycle.py | docs/human/MAINTENANCE.md, docs/human/INSTALLATION.md |
| `aips openapi` | product-delivery | linux, macos, windows-wsl | Python ">=3.12" | requirements-openapi.txt | tests/evidence/openapi_contracts_lifecycle.py, tests/evidence/openapi_cli_install_lifecycle.py | docs/human/USER_GUIDE.md, docs/human/INSTALLATION.md |
| `aips validate` | agent-eval, scenario-conformance | linux, macos, windows-wsl | Python ">=3.12"; CI tested Python 3.12 | requirements-validation.txt, requirements-visual.txt, requirements-openapi.txt | tests/validate_repository.py, config/integration-gate.yaml | docs/human/MAINTENANCE.md, docs/human/CONFORMANCE.md |

## Capability surfaces

| Surface | Capabilities | Canonical documentation | Validation bindings |
|---|---|---|---|
| `runtime-context` | unified-runtime-path-resolution, validation-interpreter-capability-selection, runtime-invariant-matrix | orchestration/RUNTIME_CONTEXT.md | tests/evidence/runtime_context_lifecycle.py, scripts/runtime_invariant_matrix.py, tests/validate_repository.py |
| `harness-runtime` | turn-aware-global-harness, execution-isolation, resource-authorization, gemini-cli-observable-event-capture-trial, gemini-cli-real-runtime-verification | harness/HARNESS_PROTOCOL.md, orchestration/EXECUTION_ISOLATION.md, orchestration/RESOURCE_AUTHORIZATION.md, orchestration/AGENT_OBSERVABLE_EVENT_CAPTURE_DESIGN.md, harness/PORTABLE_COMMANDS.md | tests/evidence/harness_runtime_lifecycle.py, tests/evidence/mcp_interoperability_lifecycle.py, tests/evidence/resource_authorization_lifecycle.py, tests/evidence/runtime_port_isolation_lifecycle.py, tests/validation/conformance_isolation.py |
| `project-intelligence` | project-intelligence, canonical-project-identity, change-impact-guard, durable-run-state | orchestration/PROJECT_INTELLIGENCE.md, orchestration/PROJECT_IDENTITY.md, orchestration/CHANGE_IMPACT.md, orchestration/RUN_RESUME.md, orchestration/RUN_DASHBOARD.md | tests/evidence/project_intelligence_lifecycle.py, tests/evidence/change_impact_resolution_lifecycle.py, tests/validation/change_impact_resolution_contracts.py, tests/validation/conformance_isolation.py, tests/evidence/identity_resume_isolation.py, tests/evidence/run_dashboard_lifecycle.py |
| `governance-security` | enforceable-governance, runtime-policy-enforcement, deterministic-automation, security-assurance, secret-handling, external-credential-dependency-guard | core/GOVERNANCE.md, orchestration/DETERMINISTIC_AUTOMATION.md, docs/human/SECURITY_ASSURANCE.md, orchestration/SECRET_HANDLING.md, orchestration/EXTERNAL_CREDENTIAL_DEPENDENCY_GUARD.md | tests/evidence/governance_command_guard.py, tests/test_runtime_policy.py, tests/evidence/runtime_policy_lifecycle.py, tests/evidence/governance_audit_lifecycle.py, tests/evidence/governance_audit_retention_lifecycle.py, tests/evidence/external_credential_guard_lifecycle.py |
| `scenario-conformance` | scenario-conformance, agent-eval | orchestration/CONFORMANCE.md, orchestration/AGENT_EVAL.md, orchestration/TRAJECTORY_EVAL.md | scripts/scenario_conformance.py, tests/evidence/agent_eval_framework.py, tests/test_eval_interop.py, tests/evidence/eval_interop_lifecycle.py, tests/validation/eval_interop_contracts.py, tests/evidence/trajectory_quality_gate_lifecycle.py |
| `product-delivery` | product-delivery | orchestration/PRODUCT_DELIVERY.md | tests/evidence/product_delivery_lifecycle.py |
| `evolution-radar` | evolution-radar, controlled-evolution-trial, trial-adoption-binding, agent-anomaly-evaluation, agent-observable-event-trial-evidence, evolution-local-deterministic-preanalysis | orchestration/EVOLUTION_RADAR.md, orchestration/AGENT_ANOMALY_EVALUATION.md, docs/human/EVOLUTION_RADAR.md | tests/evidence/evolution_radar_lifecycle.py, tests/evidence/evolution_governance_lifecycle.py, tests/evidence/evolution_effectiveness_lifecycle.py, tests/validation/evolution_effectiveness_contracts.py |
| `documentation-consistency` | documentation-consistency, human-documentation-namespace | orchestration/DOCUMENTATION_SYNC.md, docs/human/DOCUMENTATION_SYNC.md | tests/validation/documentation_sync_contracts.py, tests/validation/documentation_placement_contracts.py |
| `integration-gate` | integration-gate | orchestration/INTEGRATION_GATE.md | tests/evidence/integration_gate_lifecycle.py, tests/evidence/publish_preflight_lifecycle.py, tests/validation/publish_preflight_contracts.py, tests/evidence/validator_registry_lifecycle.py |
| `repository-health` | repository-health-architecture-drift | orchestration/REPOSITORY_HEALTH.md, docs/ARCHITECTURE.md, docs/human/MAINTENANCE.md | tests/evidence/repository_health_lifecycle.py, tests/validation/repository_health_contracts.py |

## Runtime support

- Supported Python: `>=3.12`
- CI tested Python: `3.12`
- CI compatibility smoke-tested Python: `3.12, 3.13, 3.14`
- CI tested Node.js: `24`
<!-- AIPS-SYSTEM-FACTS:END -->

Temporal queries use the existing Python and Git runtime; the internal adapter adds no dependency or public command.

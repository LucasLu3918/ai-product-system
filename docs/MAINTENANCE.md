# System Maintenance

## Documentation Impact Gate

Every system change must assess downstream documentation and behavior before completion.

| Area | Update when affected |
|---|---|
| `SYSTEM.md` | routing, planning gates, precedence, context or completion behavior changes |
| `orchestration/*` | detailed execution/model/instruction/planning behavior changes |
| `docs/ARCHITECTURE.md` | runtime flow, planning flow, boundaries or update lifecycle changes |
| `README.md` | Human first-entry behavior changes |
| `docs/GETTING_STARTED.md` | Human quick-start changes |
| `docs/USER_GUIDE.md` | Human-facing workflows/commands change |
| `docs/INSTALLATION.md` | Human installation/update lifecycle changes |
| `docs/ARCHITECTURE_OVERVIEW.md` | Human architecture overview changes |
| `docs/assets/*.svg` | Human-facing architecture/lifecycle diagram changes |
| `docs/HARNESS.md` | Global Harness / Adapter / ownership behavior changes |
| `harness/*` | Global Harness / Adapter contract changes |
| `AGENTS.md` | Agent bootloader changes |
| `examples/*` | a new behavior needs a practical example |
| `tests/scenarios/*` | routing/gate behavior changes or regressions need coverage |
| templates/schemas | persisted contract/state/planning/brand/creative/automation shapes change |
| `orchestration/CREATIVE_DIRECTION.md` | creative workflow changes |
| `orchestration/BRAND_SYSTEM.md` | brand workflow/precedence changes |
| `orchestration/CAPABILITY_INCUBATION.md` | Role/Skill creation/reuse behavior changes |
| `orchestration/SECRET_HANDLING.md` | credential acquisition/redaction/exposure behavior changes |
| `orchestration/CORE_CHANGE_TESTING.md` | core-change test-selection/completion behavior changes |
| `orchestration/DETERMINISTIC_AUTOMATION.md` | tool-vs-reasoning routing changes |
| `orchestration/PRODUCT_DELIVERY.md` | complete-product lifecycle changes |
| `orchestration/RELEASE_READINESS.md` | release/deployment readiness changes |
| `templates/product/*` | Product Manifest / workspace contract changes |
| `templates/delivery/*` | Local/deployment/release/runbook contract changes |
| `VERSION` | release version changes |
| `CHANGELOG.md` | every released behavioral change |

If an item is not affected, mark it N/A during change review rather than editing it unnecessarily.

## Architecture Diagram Impact Check

Every Large/Core Change must explicitly assess architecture-diagram impact as part of the existing Documentation Impact Gate. This is not a new approval gate.

Trigger examples: Runtime/Routing/Context-loading flow changes; Harness/Adapter/instruction precedence changes; Project persistence/workspace lifecycle changes; complete-product/Release lifecycle changes; major Security/Quality/Review lifecycle changes; Install/Update/Uninstall behavior changes; a major new subsystem or boundary.

Required review set:

- docs/ARCHITECTURE.md Mermaid;
- docs/ARCHITECTURE_OVERVIEW.md;
- docs/assets/system-overview.svg;
- docs/assets/harness-overview.svg when Harness is affected;
- docs/assets/product-delivery-overview.svg when delivery is affected;
- docs/assets/project-intelligence-overview.svg when Turn Context / Project Intelligence / Change Impact is affected;
- docs/assets/system-lifecycle.svg when install/project lifecycle is affected.

For every relevant diagram: Affected → update diagram + explanation; Not affected → record N/A + concrete reason.

A Large/Core Change that materially changes a documented architecture flow but leaves the corresponding diagram stale is documentation-incomplete and must not be released as complete.

## Self-improvement / Constitution / publish approval

Changes to this system first pass `orchestration/SYSTEM_SELF_IMPROVEMENT.md`.

If Constitution semantics are affected, the Constitutional Change Gate must complete before implementation. Material system changes also require Core Change Approval.

Before remote publication, present the Git Publish Proposal. A material difference from the approved implementation/publication plan requires re-approval.

## Release checklist

1. Confirm System Improvement Review and applicable Constitutional/Core Change approvals.
2. Run `aips validate`.
3. Review the Documentation Impact Gate.
4. For Large/Core changes, complete Architecture Diagram Impact Check.
5. Confirm Mermaid and affected Human SVG diagrams match actual behavior.
6. Build the Impact-derived Test Matrix for the final Change Boundary and execute every applicable check.
7. Confirm changed routing/gate behavior has scenario coverage.
8. Confirm planning/creative/brand/automation/product-delivery templates match their protocols when affected.
9. Confirm Human and Agent documentation audiences are synchronized when behavior affects them.
10. Confirm applicable secret/credential leakage and handling review is complete; secret-scan evidence must not echo secret values.
11. Update `VERSION` using SemVer.
12. Update `CHANGELOG.md`.
13. Ensure the system working tree is clean before publishing.
14. Prepare the Git Publish Proposal and obtain explicit approval.
15. Prefer independent review/PR for material system changes.

## Versioning

- MAJOR: incompatible governance/protocol/contract changes.
- MINOR: backward-compatible new behavior, role, skill, work mode, CLI capability or schema/planning extension.
- PATCH: backward-compatible bug fix, hardening, clarification, typo or non-behavioral documentation/evidence correction.

Major updates are not auto-applied by `aips preflight` without explicit `--allow-major`.


## Documentation audience

- Human docs use Traditional Chinese. Specialized terms include English on first use.
- Agent docs remain concise English unless a concrete reason requires otherwise.
- Do not maintain duplicate full Human guides in two languages by default.
- `docs/DOCUMENTATION_MAP.md` is the audience map.
- When behavior changes, explicitly check both Human and Agent documentation impact.

## Simplicity / reuse review

Before release, check:
- no unnecessary new Role when an existing Role can own the work;
- no new Skill that merely represents a visual style/artifact type;
- no duplicate Role/Skill IDs;
- repeated rules live in one authoritative protocol and are referenced elsewhere;
- bootloader/README remain short entry documents;
- deterministic data processing uses helpers when this materially reduces repeated model work.


## Product delivery consistency

When end-to-end delivery behavior changes, verify together:
- PRODUCT.yaml contract;
- Product Creation Work Mode;
- Planning Package;
- Local Environment / Deployment Plan / Runbook;
- Release Readiness;
- Security Assurance interaction;
- Human architecture overview;
- production scenarios and validator coverage.


## Subsystem consistency map

### Interaction / requirement / external context

When these behaviors change, review together:

- Requirement clarification → SYSTEM / ORCHESTRATOR / IMPLEMENTATION_GOAL / Human Guide / scenarios.
- External context resolution → connector-first protocol / provenance template / Human Guide / scenarios.
- Visual polish → Product Designer / Frontend Engineer / visual-quality-review / Design Work Mode / screenshots/state scenarios.
- Multi-perspective review → Quality Reviewer / code-review / Model Routing / Review templates / lesson persistence.

### Product delivery / quality / visual state

When product-delivery behavior changes, review together:

- QUALITY_PLANNING / QUALITY_PROFILE / Planning Package / Product Delivery / Product Manifest / Release Readiness;
- LOCAL_COMPLETE / Production Enablement / PRODUCTION_VERIFIED lifecycle;
- Project Visual Profile / Visual Audit / Product Designer / Frontend Engineer / visual-quality-review;
- Human Guide, product-delivery architecture diagram and applicable scenarios.

### Harness / Runtime adapters

When Harness behavior changes, review together:

- harness/BOOTSTRAP + HARNESS_PROTOCOL + ADAPTER_CONTRACT;
- Runtime Adapter registry/files;
- HARNESS_RESOLUTION + INSTRUCTION_RESOLUTION;
- bin/aips install/uninstall/preflight/resolve/status/doctor;
- README / GETTING_STARTED / INSTALLATION / HARNESS;
- system-overview / harness-overview / system-lifecycle SVG;
- Ephemeral/Attached scenarios and ownership regression evidence.

Never trade away user-owned instruction/Skill preservation merely to improve automatic coverage.

Install / Preflight lifecycle evidence should run against isolated temporary Git repositories and local bare remotes. System runtime artifacts such as Python `__pycache__/` / `*.py[cod]` must remain ignored so ordinary AIPS CLI execution cannot make the System repo fail its own clean-worktree preflight gate.

### Project Intelligence / Change Impact

When Project Intelligence behavior changes, review together:

- PROJECT_IDENTITY / PROJECT_INTELLIGENCE / CHANGE_IMPACT / Project Knowledge compatibility;
- TURN_HARNESS / HARNESS_RESOLUTION / INSTRUCTION_RESOLUTION;
- Project Intelligence templates + workspace MANIFEST/STATE;
- project_intelligence.py / turn_context_hook.py / bin/aips;
- README / GETTING_STARTED / PROJECT_INTELLIGENCE / USER_GUIDE;
- project-intelligence / system / lifecycle diagrams;
- freshness, source-registry, HTML, migration, single-writer and Change Impact evidence.

Legacy Project Knowledge remains compatibility input only. New reusable understanding belongs in Project Intelligence.

## Impact-derived regression testing

For every Large/Core Change, testing is derived from the final Change Boundary, not from a fixed minimum smoke suite.

Build and persist a matrix:

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|

Rules:

- every materially affected boundary has applicable evidence;
- N/A requires a concrete reason;
- public contract changes require contract/consumer coverage;
- persistence/schema changes require migration/rollback/recovery evidence when applicable;
- Runtime/Harness/CLI changes require executable lifecycle/regression tests;
- security-boundary or credential-handling changes require security/secret-leakage evidence;
- documentation/schema/template contract changes require structural validation;
- if implementation expands the Change Boundary, recompute the matrix;
- failing required tests block completion/release;
- never remove a relevant test merely to obtain a green result.

Prefer the strongest practical deterministic evidence for affected behavior while avoiding unrelated full-suite cost that adds no confidence.

## Governance enforcement consistency

When Approval Binding / Governance Enforcement changes, review together:

- Approval Record template + governance_guard.py;
- Git Publish/Core Change/System Improvement approval fields;
- Runtime adapter state/ownership and Claude/Gemini pre-tool hooks;
- TURN_CONTEXT_MANIFEST explanation metadata;
- Harness/System architecture diagrams;
- scenarios 096-100 and focused governance evidence.

Do not claim TOOL_GUARDED when the installed pre-tool guard is absent or unverifiable.

## Durable Run State consistency

When durable run state changes, review together:

- PROJECT_IDENTITY + RUN_RESUME;
- RUN_CHECKPOINT + workspace STATE;
- aips_identity.py + run_state.py + bin/aips run/identity routing;
- ATTACHED / EPHEMERAL storage and legacy migration;
- revision / branch / dirty workspace fingerprint behavior;
- EVENTS.jsonl redaction / no-transcript contract;
- resume/identity scenarios and executable lifecycle evidence;
- system/lifecycle diagrams.

Resume must never bypass current governance, security, impact or verification gates.

## Scenario Conformance consistency

When Scenario behavior/coverage changes, review together:

- tests/scenarios/*;
- tests/scenario_coverage.yaml;
- scripts/scenario_conformance.py + scripts/agent_eval.py;
- tests/agent_eval/cases/* + tests/agent_eval/results/*;
- tests/evidence/*;
- tests/validation/* + tests/validate_repository.py;
- orchestration/CONFORMANCE.md;
- docs/CONFORMANCE.md / USER_GUIDE;
- coverage claims in CHANGELOG/release evidence.

Before promoting legacy manual coverage: reconcile the Scenario to current canonical behavior, add direct evidence, then reclassify. For semantic behavior, Agent Eval requires an actual recorded observable Result bound to the exact Case fingerprint and passing deterministic scoring. Never infer automated coverage from Scenario count or an eval prompt alone.

## Execution Isolation consistency

When Execution Isolation behavior changes, review together:

- PROJECT_IDENTITY + EXECUTION_ISOLATION;
- execution-profile schema + workspace MANIFEST;
- execution_isolation.py + bin/aips isolation routing;
- repository-level writer ownership / workspace identity / dirty cleanup;
- truthful sandbox capability reporting;
- architecture docs/diagrams;
- scenarios 111-120 and identity/isolation lifecycle evidence.

## Public repository / CI consistency

When public repository hardening changes, review together:

- .github/workflows/validate.yml;
- .github/dependabot.yml;
- SECURITY.md;
- requirements.txt;
- immutable full-SHA action pinning;
- explicit least-privilege workflow permissions;
- validator contracts that check policy properties rather than freezing one dependency version.

## Validation architecture consistency

`tests/validate_repository.py` is the stable CI/user entrypoint. Internal validation is modular:

- `tests/validation/static_contracts.py` — schemas, indexes, documentation and static repository contracts;
- `tests/validation/runtime_contracts.py` — Harness / Runtime / Intelligence lifecycle checks;
- `tests/validation/governance_resume.py` — approval binding and durable-run behavior;
- `tests/validation/conformance_isolation.py` — Scenario Conformance, identity and isolation checks;
- `tests/validation/syntax_contracts.py` — shell syntax checks;
- `tests/evidence/*` — focused one-to-one executable evidence.

Keep the top-level validator as an aggregator. New substantial validation belongs in the narrowest existing module or a focused evidence runner rather than expanding the entrypoint back into a monolith.


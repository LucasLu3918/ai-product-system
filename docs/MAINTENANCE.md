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
- PATCH: clarification, typo or non-behavioral documentation fix.

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


## v0.6 interaction consistency

When these behaviors change, review the linked artifacts together:

- Requirement clarification → SYSTEM / ORCHESTRATOR / IMPLEMENTATION_GOAL / Human Guide / scenarios.
- External context resolution → connector-first protocol / provenance template / Human Guide / scenarios.
- Visual polish → Product Designer / Frontend Engineer / visual-quality-review / Design Work Mode / screenshots/state scenarios.
- Multi-perspective review → Quality Reviewer / code-review / Model Routing / Review templates / lesson persistence.
- Installation lifecycle → bin/aips / bootstrap.sh / uninstall.sh / INSTALLATION / lifecycle SVG / CLI scenarios.

Do not add new Role/Skill/Gate if these existing mechanisms can be extended cleanly.


## v0.7 consistency

When v0.7 behavior changes, review these sets together:

- Quality Planning → QUALITY_PLANNING / QUALITY_PROFILE / Planning Package / Product Delivery / Product Manifest / Release Readiness / Human Guide / scenarios.
- Local vs Production milestones → PRODUCT_DELIVERY / PRODUCT.yaml / STATE / Release Readiness / docs/scenarios.
- Project Knowledge → PROJECT_KNOWLEDGE / KNOWLEDGE_INDEX / workspace MANIFEST+STATE / instruction precedence / scenarios.
- Visual V1/V2 → VISUAL_POLISH / Project Visual Profile / Visual Audit / Product Designer / Frontend Engineer / visual-quality-review / scenarios.

Project Knowledge must not become a duplicate documentation tree. Prefer authoritative pointers and targeted refresh.


## v0.8 consistency

When Harness behavior changes, review together: harness/BOOTSTRAP + HARNESS_PROTOCOL + ADAPTER_CONTRACT; Runtime Adapter registry/files; HARNESS_RESOLUTION + INSTRUCTION_RESOLUTION; bin/aips install/uninstall/preflight/resolve/status/doctor; README / GETTING_STARTED / INSTALLATION / HARNESS; system-overview / harness-overview / system-lifecycle SVG; Ephemeral/Attached scenarios and ownership regression tests.

Never trade away user-owned instruction/Skill preservation merely to improve automatic coverage.


## v0.9 consistency

When Turn Harness / Project Intelligence behavior changes, review together:

- harness/HARNESS_PROTOCOL + ADAPTER_CONTRACT + Runtime adapters;
- TURN_HARNESS / HARNESS_RESOLUTION / INSTRUCTION_RESOLUTION;
- PROJECT_INTELLIGENCE / CHANGE_IMPACT / Project Knowledge compatibility;
- Project Intelligence templates and workspace MANIFEST/STATE;
- project_intelligence.py / turn_context_hook.py / manage_runtime_adapter.py / bin/aips;
- README / GETTING_STARTED / HARNESS / INSTALLATION / PROJECT_INTELLIGENCE / USER_GUIDE;
- system-overview / harness-overview / system-lifecycle / project-intelligence-overview;
- Runtime capability, external-cache, freshness, HTML, managed-composition and Change Impact regression scenarios.

For v0.9 itself, product-delivery-overview is N/A because the LOCAL_COMPLETE → Production Enablement → PRODUCTION_VERIFIED lifecycle does not change.

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

## v0.11 consistency

When Approval Binding / Governance Enforcement changes, review together:

- Approval Record template + governance_guard.py;
- Git Publish/Core Change/System Improvement approval fields;
- Runtime adapter state/ownership and Claude/Gemini pre-tool hooks;
- TURN_CONTEXT_MANIFEST explanation metadata;
- Harness/System architecture diagrams;
- scenarios 096-100 and deterministic guard tests.

Do not claim TOOL_GUARDED when the installed pre-tool guard is absent or unverifiable.

## v0.12 consistency

When durable run state changes, review together:

- orchestration/RUN_RESUME.md;
- templates/workspace/STATE.yaml + RUN_CHECKPOINT.yaml;
- scripts/run_state.py + bin/aips run routing;
- ATTACHED and EPHEMERAL storage semantics;
- revision freshness behavior;
- EVENTS.jsonl redaction / no-transcript contract;
- scenarios 101-105 and executable lifecycle tests;
- system/lifecycle architecture diagrams.

Resume must never bypass current governance, security, impact or verification gates.

## v0.13 consistency

When Scenario behavior/coverage changes, review together:

- tests/scenarios/*;
- tests/scenario_coverage.yaml;
- scripts/scenario_conformance.py;
- tests/validate_repository.py;
- orchestration/CONFORMANCE.md;
- docs/CONFORMANCE.md / USER_GUIDE;
- coverage claims in CHANGELOG/release evidence.

Never infer automated coverage from Scenario count alone. New Scenarios must enter the registry in the same change.

## v0.14 consistency

When Execution Isolation behavior changes, review together:

- orchestration/EXECUTION_ISOLATION.md;
- orchestration/schemas/execution-profile.yaml + templates/workspace/MANIFEST.yaml;
- scripts/execution_isolation.py + bin/aips isolation routing;
- worktree ownership / single-writer / dirty-cleanup semantics;
- truthful sandbox capability reporting;
- docs/ARCHITECTURE.md + ARCHITECTURE_OVERVIEW.md + USER_GUIDE;
- system-overview + system-lifecycle diagrams;
- scenarios 111-115 + scenario_coverage registry + executable lifecycle validation.

Harness-specific, Project Intelligence-specific and Product Delivery-specific diagrams are N/A unless their own behavior changes.

## v0.14.1 consistency

When legacy Scenario reconciliation changes:

- audit Scenario wording against current canonical System / Orchestration / Runtime contracts before reclassification;
- keep Scenario IDs/paths stable unless a migration is explicitly required;
- update `tests/scenario_coverage.yaml` only when direct evidence materially covers the Scenario;
- run every promoted `tests/evidence/*` artifact from repository validation;
- update `docs/CONFORMANCE.md`, `orchestration/CONFORMANCE.md`, VERSION and CHANGELOG;
- Architecture diagrams are N/A when no runtime/architecture behavior changes.

Do not relabel stale historical behavior as automated evidence.

# Plan24 System Improvement Review

## Appropriateness

Appropriate as a staged, evidence-led improvement program. Existing capabilities already cover much of OpenCode, Creative Execution, CI planning, Project Diagnostics, quality ratchets, documentation sync, Evolution Radar, branch hygiene, and telemetry. Work should extend these owners and avoid parallel subsystems or duplicate gates.

## User problem

The current system may be slow or difficult to use in native runtimes, may discover local image incompatibility too late, may spend CI effort on unrelated optional toolchains, and has high maintenance cost across large modules and duplicated path classification. Current CI success does not demonstrate real image inference, visual quality, useful research adoption, or end-user outcomes.

## Proposed solution

Implement all twelve plan24 areas in four ordered phases. Measure first; preserve full required validation and human authority; add bounded compatibility, workflow, quality, diagnostics, research, release-readiness, and privacy-preserving outcome evidence using existing abstractions.

## Existing coverage

- OpenCode V2 already has Context, prompt admission, permission, Shell and creative hooks; native acceptance is host/version-specific.
- Creative Execution already supports local MFLUX and restricted ComfyUI workflows, profiles, manifests, and batch/resume; this host reports five MFLUX version probes UNRESPONSIVE and model inventory NOT_VERIFIED.
- CI toolchain and validator-selection planners already exist; validation shadow remains advisory and must stay fail-closed.
- Project Diagnostics, quality ratchets, documentation impact, Evolution Radar, branch hygiene, telemetry export, and prior module extractions already exist.

## Reuse / extension candidates

`harness/adapters/opencode/plugin.ts`, `scripts/creative_execution.py`, `scripts/creative_request_policy.py`, `scripts/ci_validation_plan.py`, `scripts/validation_shadow_plan.py`, `scripts/project_diagnostics.py`, `config/validation-scope.yaml`, `config/ci-validation-plan.yaml`, `config/quality-ratchet.yaml`, current module facades, existing Evolution Radar and telemetry schemas/workflows, Documentation Impact and Branch Hygiene.

## Lower-layer alternative

Use local diagnostics, optional smoke tests, existing planners, and current workflow/profile schemas. Do not add a new provider framework, governance gate, telemetry platform, role, skill, or autonomous publication mechanism.

## Context / token cost

Keep additions on-demand and concise. Store only aggregate, purpose-limited outcomes; never store raw prompts, images, secrets, or chain-of-thought. Reuse current context and telemetry boundaries.

## Security / reliability

Preserve fail-closed permission and validation semantics, pinned dependency provenance, exact-candidate gates, no model downloads/quantization, local-only creative execution, no arbitrary branch deletion or automated dependency-PR merges, and human review for image quality and publication.

## Backward compatibility

Preserve public CLI arguments/output, Bundle and manifest schemas unless additive/versioned, native host authorization lifetimes, configuration compatibility, required CI checks, and existing module facades. Unknown runtime/model combinations remain UNVERIFIED.

## Scenario / test impact

Extend existing OpenCode, Creative Execution, CI-plan, Project Diagnostics, quality-ratchet, documentation-sync, Evolution Radar, branch-hygiene, telemetry and module lifecycle contracts. Add negative paths and cross-planner classification vectors. Do not treat fake-provider or synthetic-raster tests as real inference or human quality evidence.

## Human docs impact

Update only canonical Human sections reached by documentation-impact analysis, including runtime support, creative execution, validation, project diagnostics, research outcomes, branch/release, observability, and verification history.

## Agent docs impact

Update only the owning Agent protocols, schemas, scenarios, and generated projections required by the exact behavior changes.

## Architecture diagram impact

| Diagram | Assessment |
| --- | --- |
| `docs/human/assets/system-overview.svg` | Not affected: no new system plane or authority route; runtime and CI details remain within existing components. |
| `docs/human/assets/harness-overview.svg` | Updated: OpenCode hook execution is asynchronous and v2.0.24 Context plus Allow/Deny acceptance is recorded separately from other host versions. |
| `docs/human/assets/product-delivery-overview.svg` | Not affected: product delivery stage order is unchanged; provenance and review evidence are detailed in the Creative workflow docs. |
| `docs/human/assets/project-intelligence-overview.svg` | Updated: read-only diagnosis now projects a next action/recovery pointer without executing it. |
| `docs/human/assets/system-lifecycle.svg` | Not affected: install, persistence and uninstall behavior did not change. |
| `docs/human/assets/maintenance-governance-overview.svg` | Not affected: inventory and telemetry remain advisory evidence and do not add a protected-action route. |

Documentation impact was measured before closure repair: 39 direct paths expanded to 65 total paths (26 required additions, six sync rules, 21 placement rules, ratio 1.67). The final 68-path candidate has a complete recursive documentation closure. Repeated requirements remain because the sections establish separate contracts; no placement was removed.

## Constitution impact

NO. No change to Human authority, safety, scope, truth, or constitutional amendment rules.

## Additional optimization candidates

No unapproved adjacent optimizations are included. New models, telemetry vendors, CI skip enforcement, repository-wide coverage thresholds, branch deletion, release/tag automation, and provider credentials remain out of scope.

## Expected scope

All twelve plan24 items in the four approved phases, limited to evidence-supported extensions of current capabilities and the exact affected docs/tests/projections. Human visual acceptance, unavailable host versions, and real-model behavior are reported as UNVERIFIED when their required evidence is unavailable.

## Risks

- The twelve areas span separate owners and may produce a large candidate; every boundary must remain reviewable and tested.
- CI selection changes can hide required failures if the shadow replay evidence is incomplete.
- Async OpenCode execution can change cancellation, timeout, session-isolation, or fail-closed semantics.
- A local image compatibility diagnosis cannot establish successful inference or visual quality.
- Partial Impact Graph coverage limits repository-wide consumer completeness claims.
- A local Gate may remain blocked by host permissions even when code checks pass.

## Documentation amplification evidence

Before canonical documentation completion, the measured candidate contained 39 direct paths and expanded to a 65-path recursive closure: 26 required documentation additions, six triggered synchronization rules, 21 placement rules, and a closure-to-direct ratio of 1.67. After canonical sections and new-module placement rules were completed, the final candidate contained 71 direct paths and a complete 71-path closure, triggering nine sync rules and 24 placement rules. The report found 23 documents required by multiple rules, with a maximum of 30 distinct requirements for one document. The sections cover separate runtime, governance and user-facing contracts, so no requirement was removed without evidence of redundant content.

## Approval

Status: APPROVED BY USER
Approved by: User
Approved at: 2026-10-09 (Asia/Taipei)
Approval record: Current task; user requested all plan24 recommendations and replied “核准” to the four-phase Core Change scope.

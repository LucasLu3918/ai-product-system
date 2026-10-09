# Plan24 Core Change Proposal

## Purpose

Improve AIPS runtime reliability, local creative compatibility, validation cost, maintainability, diagnostics, research usefulness, release operations, and outcome observability while preserving existing authority boundaries.

## Why this is a core/large change

The approved scope affects OpenCode hooks and permissions, local model preflight, CI selection and required checks, large Python module boundaries, Project Intelligence, public diagnostics, quality ratchets, documentation policy, Evolution Radar, release/branch governance, and telemetry privacy. It crosses multiple consumers and requires exact-candidate evidence.

## Proposed Scope

### In scope

- Phase 0: freeze the latest main SHA and record OpenCode, CI, quality, creative runtime, Project Intelligence, validation configuration, release/branch, and telemetry baselines.
- Phase 1 — Reliability: (1) measure and improve OpenCode Context/admission/permission/Shell execution without weakening cancellation or fail-closed behavior; distinguish hook delivery, permission enforcement, and host-version acceptance; (2) add conservative local backend/model metadata compatibility to existing Creative Preflight and optional smoke evidence; (6) provide read-only Project Intelligence next actions and recovery paths; (8) unify shared path classification while preserving independent planner risk rules and unknown-path full validation.
- Phase 2 — Efficiency: (3) make optional CI dependency/toolchain setup follow existing plans, retain all required scans/gates, and prove selection against replay evidence before any validator skip; (4) split measured cohesive responsibilities from large Python modules while preserving facades/contracts; (5) reduce debt only in impacted high-risk paths, extending tests/ratchets without a blanket coverage target; (9) measure documentation change amplification and reduce only proven duplicate/unnecessary sync work.
- Phase 3 — Outcomes: (7) add reproducible local image generate/edit workflow evidence, raster/provenance checks, optional real-host inference, and a separate human visual-review record; (10) classify Evolution Radar signal disposition versus pending analysis and produce bounded evidence-based assessment candidates; (11) report release/channel readiness and branch/dependency backlog without deleting branches, creating releases, or merging unrelated PRs; (12) extend existing privacy-limited telemetry with runtime, governance, quality, and outcome measures.
- Maintain per-boundary tests, scenarios, documentation, diagrams, changelog/version, and the active Core Change Test Matrix.

### Out of scope

- Constitution semantics, new general-purpose governance gates, new image provider frameworks, model downloads/quantization, paid/cloud image execution, raw prompt/image telemetry, autonomous adoption or remediation, deleting branches, merging unrelated dependency PRs, release/tag creation, production deployment, or weakening mandatory CI checks.
- Claims of successful real inference, visual quality, user acceptance, host-version compatibility, or performance improvement without the corresponding observed evidence.

## Expected Files / Modules

- OpenCode: `harness/adapters/opencode/plugin.ts`, native lifecycle evidence/contracts, compatibility and adapter documentation.
- Creative: `scripts/creative_execution.py`, provider/preflight metadata and schemas, lifecycle/evidence, creative profiles and human docs.
- CI and paths: `.github/workflows/validate.yml`, `config/ci-validation-plan.yaml`, `config/validation-scope.yaml`, planner scripts and contracts.
- Intelligence and quality: `scripts/project_diagnostics.py`, Project Intelligence/retrieval modules and facades, quality ratchet configuration/evidence.
- Evolution / release / observability: current Evolution Radar, branch hygiene, release readiness and telemetry modules/configuration/workflows/schemas.
- Documentation sync, scenarios, projection registries, architecture assets, `CHANGELOG.md`, `VERSION`, this proposal, the improvement review, and `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`.

Exact changed paths will be reconciled against the final candidate diff; this list is a bounded expected surface, not permission to alter every listed file.

## Impact

### Architecture / Contracts

Preserve existing facades, CLI responses, event privacy, native action semantics, separate validator selection versus CI toolchain planning, and repository output formats. New fields are additive/versioned.

### Data / Migration

No persistent user-project migration. Any new evidence or manifest state is versioned, create-only or recoverable, and excludes prompts/images/secrets. Existing profiles and bundles remain valid.

### Security / Reliability

No permission broadening, model download, external image egress, raw prompt/image logging, skipped required check, branch deletion, or automatic publication. Unknown compatibility is UNVERIFIED. Inference and visual approval remain distinct.

### Compatibility / Rollback

Preserve public and native facades. Keep planner semantics separate. Each extracted module retains its legacy import/API surface. Changes are revertible from the feature branch; no external service state is mutated.

### Tests / Validation

Use the impact-derived active matrix, focused deterministic lifecycle/contracts, cross-planner path vectors, quality-ratchet measurements, real-host checks only when supported, strict candidate secret scan, documentation closure/build, full repository validator and exact-candidate Integration Gate. Required remote `repository` CI must pass before merge.

### Secret / Credential Impact

Secrets required: NO.

Approved acquisition mechanism: N/A.

Leakage/redaction review: strict scan on exact tree/history; telemetry excludes prompts, image data, secrets, and chain-of-thought.

Rotation/revocation plan if exposure is found: stop publication and follow existing secret handling; rotate only an actually exposed credential.

### Documentation / Diagrams

Run canonical documentation impact/placement analysis. Review all five applicable system diagrams; update diagrams only where flow/topology changes, and record concrete N/A reasons for the rest.

## Risks

- Scope spans twelve distinct capability areas; maintain phase-boundary evidence and do not broaden any item beyond its approved description.
- CI optimization must remain shadow-only until replay proves zero false-negative skips.
- Host permission constraints may prevent a fully green local Gate.
- Available MFLUX commands are currently UNRESPONSIVE and model inventory is NOT_VERIFIED; no weights will be downloaded.
- Real visual acceptance requires human review and cannot be inferred from a successful lifecycle test.
- Project Intelligence Impact Graph is partial; scoped evidence must not imply global completeness.

## Recommendation

Proceed in the user-approved four phases. Preserve complete validation and Human authority. Report external-runtime or visual checks as UNVERIFIED when unavailable rather than fabricating a pass.

## Proposed Implementation Order

1. Phase 0 baseline and exact-main evidence.
2. Phase 1 runtime/creative/diagnostic/path reliability.
3. Phase 2 CI/maintainability/quality/documentation efficiency.
4. Phase 3 creative outcome, research, release/branch, and telemetry evidence.
5. Exact diff reconciliation, architecture/documentation closure, local candidate Gate, independent review, and Git Publish Proposal.

## Approval

Status: APPROVED BY USER
Approved by: User
Approved at: 2026-10-09 (Asia/Taipei)
Approval record: Current task; user explicitly requested implementation of all plan24 recommendations and replied “核准” to this scope.

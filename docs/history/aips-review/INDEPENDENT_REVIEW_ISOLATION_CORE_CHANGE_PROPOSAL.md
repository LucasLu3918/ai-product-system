# Core Change Proposal: v0.62.0 Independent Review Isolation

## Purpose

Make AIPS independent review an evidence-backed execution contract rather than a role/prompt convention.

## Why this is a Core Change

Changes cross review governance, runtime context, task scheduling, deterministic evidence validation, Integration Gate behavior, schemas, scenarios, and architecture documentation.

## Proposed Scope

### In scope

- Define `SELF_CHECK` and `INDEPENDENT_REVIEW` and their required evidence.
- Extend existing Context Manifest and Task Graph contracts.
- Build reviewer packets from allowlisted canonical evidence only.
- Deterministically verify execution separation, fresh bounded context, read-only permission, packet provenance, and exact-candidate freshness.
- Return `VERIFIED`, `UNVERIFIED`, `FAILED`, or `STALE` truthfully; block required independent reviews unless verified.
- Add evidence-first review, structured factual clarification, and targeted re-review guidance.
- Wire optional machine-readable review evidence into the Integration Gate; keep active PR enforcement disabled by default until a trusted runtime-attestation verifier is integrated.
- Add focused scenarios/lifecycle tests; reconcile architecture diagrams, human/agent documentation, changelog, and SemVer.

### Out of scope

- New Reviewer Role, approval Gate, or parallel review schema.
- Mandatory model/vendor diversity or a Greptile dependency.
- Independent review for every trivial change.
- Diff-only review context.
- Chain-of-thought detection or sanitized Implementer transcript forwarding.
- Constitution or human GitHub branch-protection changes.

## Expected Files / Modules

- `SYSTEM.md`
- `orchestration/MULTI_REVIEW.md`
- `orchestration/ORCHESTRATOR.md`
- `orchestration/DETERMINISTIC_SCHEDULER.md`
- `orchestration/INTEGRATION_GATE.md`
- `orchestration/CORE_CHANGE_TESTING.md`
- `orchestration/CONFORMANCE.md`
- `orchestration/schemas/context-manifest.yaml`
- `orchestration/schemas/task-graph.yaml`
- `scripts/deterministic_scheduler.py`
- `scripts/review_packet.py` and focused review-evidence validation module
- `scripts/integration_gate.py`
- `scripts/publish_preflight.py` and `config/integration-gate.yaml`
- `templates/review/REVIEW_REPORT.md` and a machine-readable evidence template
- `templates/review/INTEGRATION_GATE_REPORT.yaml`
- `templates/automation/TASK_GRAPH.yaml`
- `tests/evidence/*`, `tests/validation/*`, `tests/scenarios/*`, `tests/scenario_coverage.yaml`
- `tests/validate_repository.py` and `tests/validation/conformance_isolation.py`
- `docs/ARCHITECTURE.md`, `docs/human/ARCHITECTURE_OVERVIEW.md`, `docs/human/CONFORMANCE.md`, `docs/human/MAINTENANCE.md`
- `CHANGELOG.md`, `VERSION`
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`

## Impact

### Architecture / Contracts

The flow becomes Implementer → canonical evidence packet → fresh bounded read-only Reviewer → review evidence → Author fix → targeted re-review → Integration Gate exact-candidate evidence validation. No Constitution semantics change.

### Data / Migration

Optional version-1 contract fields preserve existing task manifests. Missing runtime attestation is `UNVERIFIED`; it never upgrades to PASS.

### Security / Reliability

Allowlist evidence sources; deny Implementer transcript, private reasoning, scratchpad, and raw traces. Validate path/source class, permission, execution identity, fingerprints, and candidate SHA bindings deterministically. Do not trust reviewer-supplied status fields without validating their evidence.

### Compatibility / Rollback

Existing tasks without review metadata continue as before. Rollback is reverting the capability and its documentation/templates; no user data migration is required.

### Tests / Validation

See `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`. Recompute if the final Change Boundary expands.

### Secret / Credential Impact

Secrets required: NO.

Leakage review: review packet and report must not include secret values or private model reasoning. Use existing repository content-safety validation.

### Documentation / Diagrams

- `docs/ARCHITECTURE.md` Mermaid: AFFECTED — review execution/context topology changes.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: AFFECTED — human-facing review flow changes.
- Human SVG architecture/lifecycle diagrams: inspect existing diagram inventory; update any relevant review lifecycle diagram, otherwise record N/A with reason.
- Harness and Project Intelligence diagrams: N/A — runtime adapter bootstrap and project identity/intelligence behavior are unchanged.

## Risks

- Runtime adapters may not expose trustworthy execution identity or context-isolation attestations; report `UNVERIFIED` and block when required.
- Overly small packets can hide architectural context; require Change Impact and relevant contracts/code, not diff alone.
- Stale report acceptance could allow review of a different candidate; bind candidate and packet fingerprints and test invalidation.
- Schema additions could break callers; keep fields optional unless independent review is explicitly required.

## Activation Status

The task, packet, evidence and Gate contracts are implemented. PR enforcement is not enabled by default in this release: the active Core Change Matrix sets `review_evidence.required: false` until a trusted runtime-attestation verifier is configured. Explicitly setting it to `true` without a verifier keeps the Gate fail-closed as `UNVERIFIED`.

## Recommendation

Implement as v0.62.0 by extending existing review, schema, scheduler, and Integration Gate abstractions. Preserve honest runtime capability reporting and Human merge authority.

## Proposed Implementation Order

1. Lock contracts and complete matrix.
2. Add review packet and evidence validators.
3. Enforce review relationships and read-only context in the scheduler.
4. Verify exact-candidate review evidence in the Integration Gate.
5. Add executable lifecycle scenarios and documentation/diagram updates.
6. Run impact-derived validation, review the final diff, prepare the Git Publish Proposal.

## Approval

Status: APPROVED
Approved by: User
Approved at: 2026-09-25 (conversation instruction)
Approval record: User approved implementation of all plan6 recommendations and local verification, then approved retaining the mechanism while disabling strict PR enforcement until future activation.
Proposal fingerprint: pending final scope reconciliation
Scope fingerprint: pending final diff reconciliation

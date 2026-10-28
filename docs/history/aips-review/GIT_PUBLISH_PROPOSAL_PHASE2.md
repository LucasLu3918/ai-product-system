# Git Publish Proposal — Implementation Resolution Phase 2

## Target

- Remote: `origin` (`LucasLu3918/ai-product-system`)
- Branch: `feat/implementation-resolution-phase2`
- PR / Release action: Open a Core Change PR targeting `main`; merge the exact candidate only after local validation, Integration Gate PASS, required PR checks PASS, and no unresolved review blocker.

## Changed Files

- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`
- `.aips/review/GIT_PUBLISH_PROPOSAL_PHASE2.md`
- `.aips/review/IMPLEMENTATION_RESOLUTION_PHASE2_CORE_CHANGE_PROPOSAL.md`
- `.aips/review/IMPLEMENTATION_RESOLUTION_PHASE2_SYSTEM_IMPROVEMENT_REVIEW.md`
- `CHANGELOG.md`, `VERSION`
- `docs/ARCHITECTURE.md`
- `docs/human/ARCHITECTURE_OVERVIEW.md`, `docs/human/CONFORMANCE.md`, `docs/human/USER_GUIDE.md`
- `orchestration/IMPLEMENTATION_RESOLUTION.md`
- `requirements-validation.txt`
- `scripts/implementation_profile_validate.py`, `scripts/openapi_contracts.py`
- `templates/implementation/IMPLEMENTATION_PROFILE.yaml`
- `templates/implementation/OPENAPI_EVIDENCE_REPORT.schema.json`
- `tests/evidence/openapi_contracts_lifecycle.py`
- `tests/fixtures/openapi_phase2_invalid.yaml`, `tests/fixtures/openapi_phase2_network_ref.yaml`, `tests/fixtures/openapi_phase2_valid.yaml`
- `tests/scenario_coverage.yaml`, `tests/scenarios/194-implementation-resolution-openapi-evidence.md`
- `tests/validate_repository.py`
- `tests/validation/conformance_isolation.py`, `tests/validation/implementation_profile_contracts.py`, `tests/validation/openapi_contracts.py`

## Change Summary

1. Add pinned OpenAPI 3.0/3.1/3.2 validity checks with safe local-only reference handling.
2. Add conservative compatibility analysis that requires an explicitly canonical baseline and leaves ambiguous changes `UNKNOWN`.
3. Run project-native contract tests with argv-only execution; bind JUnit operation coverage, input/output hashes and exact Git revision; detect stale reports.
4. Extend Profile validation, Scenario 194, repository tests, architecture and Human/Agent guidance.

## Validation Evidence

- Tests: OpenAPI compatibility contracts, OpenAPI lifecycle, Implementation Profile contracts and full `tests/validate_repository.py` (pending final result at proposal creation).
- Repository validation: exact candidate `aips publish` preflight / Integration Gate and docs validation (pending final candidate).
- Independent review: Human review and required automated PR checks; trusted runtime attestation remains disabled by repository policy.
- Security review: no external `$ref` fetch, repository-contained local paths, argv-only commands, timeouts, digest-only output, strict candidate secret scan.
- Documentation impact: Core proposal matrix; Phase 2 protocol, architecture, User Guide, Conformance, changelog and version updated.
- Unresolved items: GitHub CLI currently reports an invalid token; re-authentication is required for remote push/PR operations if no valid Git credential route is available.

## Atomic Commit Plan

1. `feat: add OpenAPI implementation evidence` — one coherent Phase 2 implementation, tests, docs and review artifacts.

## Remote Update Strategy

- Strategy: one atomic feature-branch push after the exact local candidate passes review and the publish preflight.
- Expected remote ref updates: create/update only `refs/heads/feat/implementation-resolution-phase2`; GitHub creates the PR; merge via GitHub after PR checks are green.
- CI trigger expectation: PR labeled `aips:core-change`, then required repository/Integration Gate checks.

## Publication Notes

- User explicitly requested local verification, remote PR creation and merge to `main`; this is the publication authorization for the scope listed above.
- A red required check, stale candidate, base movement, rejected review, or expanded file boundary blocks merge until reconciled. Continue after revalidation; do not change branch protection or bypass checks.

## Approval

Status: APPROVED
Approved by: Human (user)
Approved at: 2026-09-30T09:21:18Z
Approval record: User instruction to implement all recommended Phase 2 items, validate locally, and complete the remote PR merge to `main`.
Proposal fingerprint: generated after final candidate review
Scope fingerprint: generated after final changed-file reconciliation
Candidate commit: pending

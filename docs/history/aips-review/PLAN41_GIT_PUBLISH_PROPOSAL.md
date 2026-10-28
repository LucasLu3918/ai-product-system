# Plan41 Git Publish Proposal

## Target

- Remote: `origin` (`https://github.com/LucasLu3918/ai-product-system.git`)
- Branch: `codex/commit-safety-diagnostics`
- PR action: create one Core Change PR targeting `main`, then merge it after exact-candidate required checks pass.
- Excluded actions: no release/tag, dependency PR merge, branch deletion, ruleset change, or direct protected-branch push.

## Changed Files

- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`
- `.aips/review/PLAN41_CORE_CHANGE_PROPOSAL.md`
- `.aips/review/PLAN41_GIT_PUBLISH_PROPOSAL.md`
- `.aips/review/PLAN41_SYSTEM_IMPROVEMENT_REVIEW.md`
- `config/documentation-placement.yaml`
- `docs/ARCHITECTURE.md`
- `docs/human/ARCHITECTURE_OVERVIEW.md`
- `docs/human/CONFORMANCE.md`
- `docs/human/CONFORMANCE_CURRENT.md`
- `docs/human/CONFORMANCE_HISTORY_INDEX.md`
- `docs/human/DOCUMENTATION_MAP.md`
- `docs/human/DOCUMENTATION_SYNC.md`
- `docs/human/HARNESS.md`
- `docs/human/INSTALLATION.md`
- `docs/human/MAINTENANCE.md`
- `docs/human/PROJECT_INTELLIGENCE.md`
- `docs/human/SECURITY_ASSURANCE.md`
- `docs/human/TECHNOLOGY_GUIDE.md`
- `docs/human/USER_GUIDE.md`
- `docs/human/index.md`
- `orchestration/CONFORMANCE.md`
- `orchestration/CONTENT_SAFETY_BOUNDARY.md`
- `orchestration/DETERMINISTIC_SCHEDULER.md`
- `orchestration/DOCUMENTATION_SYNC.md`
- `orchestration/EXECUTION_ISOLATION.md`
- `orchestration/ORCHESTRATOR.md`
- `orchestration/RESOURCE_AUTHORIZATION.md`
- `orchestration/RUNTIME_POLICY_ENFORCEMENT.md`
- `scripts/aips_cli/dispatch.sh`
- `scripts/aips_cli/help.sh`
- `scripts/content_safety.py`
- `scripts/governance_guard.py`
- `scripts/media_metadata.py`
- `scripts/publication_authority.py`
- `scripts/safety_diagnostics.py`
- `tests/fixtures/plan21-contract-golden-vectors.yaml`
- `tests/scenario_coverage.yaml`
- `tests/scenarios/263-runtime-content-safety-commit-diagnostics.md`
- `tests/test_publication_authority.py`
- `tests/test_safety_diagnostics.py`
- `tests/validate_repository.py`
- `tests/validation/conformance_isolation.py`

## Change Summary

1. Share the strict staged-commit scanner between the native Hook and a read-only `aips safety diagnose commit` CLI; add stable, redacted reason/phase/source/category/detector/location/diagnostic-ID output and recovery guidance.
2. Add bounded metadata readers for PNG, JPEG, WebP, M4A and MP3; classify unknown/malformed binaries, unreadable Git objects, size limits and scanner failures while preserving fail-closed behavior and existing Secret/PII/Injection Signal BLOCK policy.
3. Add unit, integration, security, CLI/Hook and regression evidence, Scenario 263, recursive documentation closure and an exact-candidate Core Change Matrix.
4. Preserve Human Authority, Required Checks, Git Publish Approval, Resource Authorization, independent-review policy and existing publication gates.

## Validation Evidence

- Focused safety/diagnostics/publication regression suite: PASS, 96 tests.
- Full repository validation: PASS, 263 scenarios (243 automated); validator environment used the official Python 3.12 validation venv, installed VitePress dependencies and authorized local loopback lifecycle checks.
- Plan21 CLI contract baseline: PASS.
- Focused documentation placement/sync and conformance contracts: PASS before the final recursive-closure additions; final preview reports no documentation-placement errors or additions.
- Core Change Matrix exact candidate binding, complete Integration Gate and credential-free candidate/history secret scan: pending the final commit.
- PR/main Required Checks: pending publication.
- Independent review: not required by the active matrix; no trusted review verifier is configured.
- Unresolved items: the partial project-impact graph remains recorded as an accepted limitation with bounded manual consumer review; no product/security boundary or Required Check is waived.

## Atomic Commit Plan

1. One commit: `fix(safety): add structured commit diagnostics` — shared strict scanner, redacted Hook/CLI diagnostics, bounded media metadata inspection, tests, Scenario 263, matrix and recursive documentation.

## Remote Update Strategy

- Strategy: push the complete candidate branch once, then create one PR with `aips:core-change` on initial creation.
- Expected remote refs: create/update only `refs/heads/codex/commit-safety-diagnostics`; PR base `main`.
- CI trigger expectation: PR full Gate followed by protected `main` validation after the authorized merge.
- Post-merge: verify the exact merged `main` checks and reconcile a clean local `main`; do not delete the remote feature branch as part of this request.
- Selected mode: personal.
- Task scope authorization reference: user requested implementation, local verification, remote PR and merge, then explicitly approved the complete Plan41 Core Change scope.
- High-assurance grant reference: N/A in personal mode.

## Approval

Status: APPROVED BY USER REQUEST

Approved by: User

Approval record: The user's request to implement Plan41, verify locally, create a remote PR and merge it to `main`, plus explicit reply `核准 Plan41 完整範圍`.

Proposal fingerprint, scope fingerprint and candidate commit: bind after the final candidate is fixed.

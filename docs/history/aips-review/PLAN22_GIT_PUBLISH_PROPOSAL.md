# Plan22 Git Publish Proposal

## Target

- Remote: `origin` (`https://github.com/LucasLu3918/ai-product-system.git`)
- Branch: `codex/plan22-system-improvements`
- PR action: open one Core Change PR targeting `main`; merge it only after exact-candidate required checks pass.
- Excluded actions: no release/tag, dependency PR merge, branch deletion, ruleset change, or selective-validation activation.

## Change Summary

1. Move quarterly Evolution Radar aggregation to day 3 at 11:00 Asia/Taipei so monthly Radar and Effectiveness Issues can publish first; missing evidence remains `INCOMPLETE_INPUT`.
2. Add regression coverage and required canonical documentation closure.
3. Add read-only parity assertions across CI validation planning, Shadow scope, Integration Gate, and validator registry; remove five verified Ruff findings without changing policy thresholds.
4. Preserve existing Human authority and capability-truth boundaries for release, dependencies, branch cleanup, and cross-runtime enforcement.

## Validation Evidence

- Focused Evolution Radar contract/lifecycle: PASS.
- Read-only validation source parity contract, including a drift-negative fixture: PASS.
- Full repository validation: PASS, 233 scenarios.
- Ruff/myypy quality ratchet against `origin/main`: PASS; Ruff findings fell from 702 to 697, selected mypy findings 0.
- Documentation placement preview: PASS; all required additions present.
- Core Matrix exact base/file binding and Integration Gate: pending final candidate commit.
- Exact-candidate credential-free secret scan and PR/main CI checks: pending publication.
- Independent review: not required by current active matrix; verifier is not configured.
- Unresolved items: partial repository-wide Impact Graph coverage remains explicitly recorded; unrelated legacy documentation hashes remain stale pending review.

## Atomic Commit Plan

1. One commit: `fix(evolution): align quarterly reports and validation evidence` — quarterly schedule/lifecycle, read-only validation source parity, safe touched-file Ruff cleanup, canonical documentation, and Plan22 evidence/matrix.

## Remote Update Strategy

- Strategy: push the complete candidate branch once, then open one PR with `aips:core-change` on initial creation.
- Expected remote refs: create/update only `refs/heads/codex/plan22-system-improvements`; PR base `main`.
- CI trigger expectation: PR full Gate followed by protected `main` validation after the authorized merge.
- Post-merge: verify the exact merged `main` checks and reconcile a clean local `main`; do not remove the remote feature branch as part of this request.

## Approval

Status: APPROVED BY USER REQUEST

Approved by: User

Approved at: 2026-10-08 (Asia/Taipei)

Approval record: Initial user request to implement Plan22, locally verify, and merge the remote PR to `main`; explicit follow-up `核准`.

Candidate commit and proposal fingerprint: bind after the final local candidate is fixed.

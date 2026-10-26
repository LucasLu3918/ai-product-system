# Core Change Proposal: Publication JSON Error Recovery

## Purpose

Ensure `aips publish prepare` and `diagnose` always return a safe, parseable JSON diagnostic when local validation raises an allowlisted exception, so callers can recover without losing structured publication evidence.

## Why this is a core change

The fix changes a publication CLI error contract used by the Hook and evidence-gated publication flow. Empty stdout previously caused JSON parsing to fail and left no scan evidence; downstream Hook denial was correct but gave no usable structured recovery path. The change must preserve fail-closed publication authority and be tested against the exact candidate.

## Proposed Scope

### In scope

- Emit versioned `BLOCKED` JSON for allowlisted prepare/diagnose exceptions when JSON output is requested.
- Keep the diagnostic non-authorizing and non-executing, avoid raw exception/path/command/credential disclosure, and preserve text-mode behavior.
- Add regression coverage for exception classification, safe fields, JSON parseability, and unchanged successful/text output behavior.
- Complete the canonical documentation closure required by CI's documentation impact rules.
- Add this candidate-specific Core Change Test Matrix and run the full local Integration Gate / Repository Validation.
- Update PR #382 and merge the exact reviewed PR candidate after its required `repository` check passes.

### Out of scope

- Changes to GitHub branch policy, credentials, required checks, authorization, or automatic publication/merge behavior.
- Weakening scan evidence requirements or Hook fail-closed decisions.
- New persistence, services, roles, capabilities, or runtime adapters.

## Expected Files / Modules

- `scripts/publish_preflight.py`
- `tests/test_publication_diagnostics.py`
- `tests/scenarios/261-publication-diagnostics-and-safe-recovery.md`
- `CHANGELOG.md`
- The 19 canonical documentation files in the approved documentation closure.
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`
- This proposal.

## Impact

### Architecture / Contracts

Add a safe JSON failure envelope for existing prepare/diagnose commands. Successful JSON and text behavior remain compatible. No topology or authority boundary changes.

### Data / Migration

No persistent data or migration.

### Security / Reliability

Allowlist exception classes and stable reason codes. Do not emit raw exception messages, private paths, command arguments, or credentials. Failure remains `authorized: false`, `executed: false`, and does not issue API writes or scan grants.

### Compatibility / Rollback

Text behavior and successful JSON are unchanged. JSON-mode local failures gain a parseable v2 result. Reverting the single candidate restores previous empty-stdout behavior; no migration is needed.

### Tests / Validation

The active `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` binds the exact base and changed-path digest. Focused tests and contract checks run before one complete local Integration Gate / Repository Validation on the frozen candidate. PR `repository` and post-merge main validation are separate required evidence.

### Secret / Credential Impact

Secrets required: NO.

Leakage/redaction review: Required; tests assert unsafe exception context is absent.

Rotation/revocation plan if exposure is found: Stop publication, remove the value, revoke through its owner, rescan the exact candidate/history and revalidate.

### Documentation / Diagrams

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` Mermaid: N/A — publication topology is unchanged.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: N/A — no component topology change.
- Human SVG architecture/lifecycle diagrams: N/A — the existing read-only recovery path is clarified without changing execution authority.

## Risks

- A failure envelope could be mistaken for successful scan evidence; retain `BLOCKED`, `authorized: false`, `executed: false`, stable reason codes, and existing Hook policy checks.
- Unsafe exception details could leak through JSON; use allowlisted fields and explicit regression checks.
- Documentation additions can miss a canonical placement; require the repository placement and documentation closure checks.

## Recommendation

Proceed within the approved CLI, regression-test, documentation-closure, matrix, and full-Gate boundary. Keep publication authority and all protected operations unchanged.

## Proposed Implementation Order

1. Record the approved Core Change boundary and focused evidence.
2. Reconcile the active matrix against the final path set and base SHA.
3. Run the complete local Integration Gate / Repository Validation once the candidate is frozen.
4. Update PR #382, verify its exact head and required `repository` check, then merge under the existing user authorization.
5. Run post-merge validation and report its observed result.

## Approval

Status: APPROVED BY USER REQUEST
Approved by: Human user
Approved at: 2026-10-26 (Asia/Taipei)
Approval record: User authorized the publication diagnostics fix and approved CLI, regression tests and necessary documentation; then explicitly approved completion of the 18-document CI closure; then explicitly approved the dedicated Core Change matrix, full local Integration Gate / Repository Validation, PR #382 update and merge under the original authorization.
Proposal fingerprint: pending final candidate calculation
Scope fingerprint: pending final candidate calculation

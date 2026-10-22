# Plan50 Core Change Proposal — Opt-in Required Checks Enforcement

## Purpose

Make AIPS Required Checks enforcement opt-in for personal PR merges while keeping the GitHub policy observable and allowing GitHub's native repository protection to continue governing merges.

## Why this is a Core Change

This changes the AIPS protected-publication authorization contract and the governance guidance used by publication runtimes. The change affects merge decisions and therefore requires exact-candidate security, scenario, documentation and integration evidence.

## Approved Scope

### In scope

- Add `AIPS_ENFORCE_REQUIRED_CHECKS=1` as the opt-in switch for AIPS personal-mode PR merge checks.
- With the variable unset or any value other than `1`, do not block AIPS personal-mode merge authorization on Required Checks policy visibility or check status; preserve explicit merge intent, exact PR/head, open/non-draft/mergeable state, allowlisted head branch, and live remote default-base validation.
- With the variable set to `1`, preserve the existing fail-closed policy evidence and all-required-checks-passing gate.
- Make merge confirmation state whether AIPS enforced Required Checks.
- Keep Doctor read-only and truthful about observed GitHub policy/check status. Do not change GitHub rules, use `--admin`, or bypass GitHub's native enforcement.
- Update governance and decision records, System Core, Human and Agent guidance, Scenarios 097 and 260, and the exact-candidate Core Change Test Matrix.

### Out of scope

- Any GitHub branch protection/ruleset mutation or admin merge.
- Changing explicit Human task intent, native Host confirmation, high-assurance grants, candidate/content safety, exact head pinning, or PR/base/mergeability validation.
- Changing Required Checks observations reported by Doctor or diagnosing remote GitHub policy.
- Constitution changes.

## Expected Files / Modules

- `scripts/publication_authority.py`, `scripts/governance_guard.py`
- `tests/test_publication_authority.py`
- `tests/scenarios/097-approval-scope-drift-stops-protected-action.md`, `tests/scenarios/260-publication-diagnostics-and-doctor.md`
- `core/GOVERNANCE.md`, `core/DECISIONS.md`, `SYSTEM_CORE.md`
- `docs/human/SECURITY_ASSURANCE.md`, `docs/human/USER_GUIDE.md`
- `orchestration/ORCHESTRATOR.md`, `orchestration/CONFORMANCE.md`
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`

## Impact

### Architecture / Contracts

The Authority merge contract gains an opt-in Required Checks gate and explicit confirmation metadata. Doctor's read-only output remains unchanged. The GitHub provider remains the final enforcement point for configured native repository rules.

### Data / Migration

No schema or persistent runtime-state migration. One optional environment variable selects stricter AIPS enforcement.

### Security / Reliability

The default AIPS path may authorize a merge without AIPS Required Checks evidence in repositories that lack native protections. This risk is disclosed in governance and user guidance. Explicit task intent, exact candidate/head, safe PR state, default-base validation, content scans and native Host confirmation remain required. GitHub-native checks remain effective. Setting the variable to `1` restores fail-closed AIPS behavior.

### Compatibility / Rollback

Existing deployments without the variable receive the newly approved default. Setting `AIPS_ENFORCE_REQUIRED_CHECKS=1` restores prior enforcement behavior. Reverting the change restores mandatory AIPS Required Checks enforcement.

### Tests / Validation

- Unit: default mode permits a valid exact PR without calling Required Checks policy/check APIs and marks the confirmation `NOT_ENFORCED`.
- Unit: strict mode requires configured policy and all checks passing; pending checks remain blocked.
- Contract: Scenarios 097 and 260 describe the opt-in gate and preserve truthful, read-only Doctor behavior.
- Security: confirm exact candidate, Human intent, native confirmation and GitHub protection guidance remain intact; no `--admin`/policy mutation.
- Repository: complete validator, documentation closure, exact-candidate Core Matrix, secret scan and Integration Gate.

Impact-derived Test Matrix:

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| Personal PR merge authority | Required | Required | Required | Required | N/A | Required | Required | Required | Required | No deployed UI/service or persistent schema |

### Secret / Credential Impact

Secrets required: NO.

Approved acquisition mechanism: N/A.

Leakage/redaction review: Existing safe publication error handling and Doctor redaction remain unchanged; no credential values are added to confirmation output.

Rotation/revocation plan if exposure is found: N/A.

### Documentation / Diagrams

Architecture Diagram Impact: N/A — no component or topology change; the publication authority contract and governance prose are updated.

## Risks

- A repository without native protection may permit a merge with incomplete or absent CI when AIPS enforcement is not enabled.
- Operators may confuse AIPS enforcement state with GitHub policy. Confirmation and Doctor guidance distinguish those states.

## Recommendation

Implement the approved opt-in behavior, preserve all other protected-publication checks, and require the exact-candidate Core Change Gate before publication.

## Proposed Implementation Order

1. Implement the opt-in Authority gate and confirmation state.
2. Add strict/default regression coverage and update Scenarios 097/260.
3. Synchronize governance, Human and Agent guidance.
4. Reconcile the final diff against the Core Matrix, run local validation, then publish and merge the exact candidate after remote checks.

## Approval

Status: APPROVED
Approved by: Human user in the current task
Approved at: 2026-10-22
Approval record: User explicitly selected “要求 Required Checks 預設停用／可繞過” and then “核准此提案” for the stated Core Change scope.
Constitution impact: NO

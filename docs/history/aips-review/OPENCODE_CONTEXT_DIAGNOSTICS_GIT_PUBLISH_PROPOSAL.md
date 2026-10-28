# OpenCode Context Overflow Diagnostics Git Publish Proposal

## Target

- Remote: `origin` (`https://github.com/LucasLu3918/ai-product-system.git`)
- Branch: `codex/opencode-context-diagnostics`
- PR / Release action: one pull request targeting `main`; merge the exact PR only after the candidate gate and required `repository` check pass.
- Authorized actions: publish this scoped engineering branch, create its PR, and merge that exact PR into `main` after all required gates pass, as explicitly requested in the current task.
- Excluded actions: direct push to protected `main`, release/tag, policy change, unrelated PR merge, force update, or branch deletion.

## Changed Files

- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`
- `.aips/review/OPENCODE_CONTEXT_DIAGNOSTICS_CORE_CHANGE_PROPOSAL.md`
- `.aips/review/OPENCODE_CONTEXT_DIAGNOSTICS_GIT_PUBLISH_PROPOSAL.md`
- `.aips/review/OPENCODE_CONTEXT_DIAGNOSTICS_NATIVE_ACCEPTANCE.json`
- `.aips/review/OPENCODE_CONTEXT_DIAGNOSTICS_SYSTEM_IMPROVEMENT_REVIEW.md`
- `CHANGELOG.md`
- `docs/ARCHITECTURE.md`
- `docs/human/ARCHITECTURE_OVERVIEW.md`
- `docs/human/CONFORMANCE.md`
- `docs/human/DOCUMENTATION_MAP.md`
- `docs/human/DOCUMENTATION_SYNC.md`
- `docs/human/HARNESS.md`
- `docs/human/INSTALLATION.md`
- `docs/human/MAINTENANCE.md`
- `docs/human/TECHNOLOGY_GUIDE.md`
- `docs/human/USER_GUIDE.md`
- `docs/human/index.md`
- `harness/HARNESS_PROTOCOL.md`
- `harness/adapters/opencode/AGENTS.md`
- `harness/adapters/opencode/COMPATIBILITY.md`
- `harness/adapters/opencode/context_diagnostics.mjs`
- `harness/adapters/opencode/plugin.ts`
- `orchestration/CONFORMANCE.md`
- `orchestration/CREATIVE_DIRECTION.md`
- `orchestration/DOCUMENTATION_SYNC.md`
- `scripts/opencode_trace.py`
- `tests/evidence/opencode_integration_lifecycle.py`
- `tests/scenario_coverage.yaml`
- `tests/scenarios/235-opencode-native-context-guard.md`
- `tests/validation/opencode_integration_contracts.py`

## Change Summary

1. Extract the existing OpenCode context compaction policy into a tested helper and diagnose irreducible 12,000-byte projection overflow with bounded section sizes and safe recovery commands.
2. Deny supported native file writes before ordinary manifest policy evaluation while the projection is oversized; retain existing Shell/MCP limitations and ADVISORY status.
3. Extend allowlisted trace metadata, Scenario 235 and local/native acceptance evidence, canonical docs, changelog, improvement review and Core Change matrix.

## Validation Evidence

- Tests: focused OpenCode lifecycle and integration contract PASS; source-bound OpenCode v2.0.24 macOS native acceptance PASS for Context delivery and native permission Allow/Deny.
- Repository validation: the exact 30-path Python 3.12 candidate passed the full repository Gate (`VALIDATION PASSED`, version 0.83.0, 12 roles, 49 skills, 274 scenarios; 303,837 ms). The official Conformance history projection is current.
- Independent review: primary-agent code review identified and closed the native permission path that could otherwise evaluate an oversized manifest; matrix and static contract enforce denial ordering.
- Security review: trace allowlist rejects unknown/private section metadata; lifecycle asserts user diagnostic omits raw freshness values; mandatory exact-candidate secret scan REQUIRED.
- Documentation impact: recursive closure is complete across the 30 changed candidate paths; placement and documentation-sync checks pass with no remaining required additions.
- Host acceptance: OpenCode v2.0.24 on macOS verified Context delivery and native permission ALLOW/DENY; report is source-bound. Instruction delivery, session cancellation, L3, arbitrary Shell/MCP and out-of-process effects remain UNVERIFIED or UNSUPPORTED.
- Unresolved items: no known implementation blocker; content safety, matrix binding, mandatory secret scan, GitHub PR head/base/mergeability and required `repository` check remain to be verified before merge.

## Atomic Commit Plan

1. `fix(opencode): diagnose context projection overflow` — one coherent capability commit for all 30 scoped implementation, evidence, review and documentation files.

## Remote Update Strategy

- Strategy: one atomic feature-branch push after the complete candidate is assembled and validated.
- Expected remote ref updates: one branch update, then one PR creation.
- If incremental, why remote intermediate states are required: N/A.
- CI trigger expectation: PR validation; required aggregate is `repository`.

## Publication Notes

- Selected mode: personal.
- Task scope authorization reference: explicit user request to implement the selected OpenCode Context overflow diagnosis/recovery work, validate locally, open a remote PR, and merge to `main`.
- High-assurance grant reference: N/A in personal mode.
- Merge method: use a GitHub-supported method reported live by repository metadata; latest read-only Doctor observation listed `merge` and `rebase`, with `repository` as the protected-main required check.
- Material scope/file/commit/target drift requires re-running candidate and mode checks. No admin bypass, direct main push, force update or branch deletion.

## Approval

Status: NOT_REQUIRED (personal task scope)
Approved by: current user request
Approved at: 2026-10-27 (Asia/Taipei)
Approval record: task message explicitly authorizes implementation, local verification, remote PR and merge to `main`.
Proposal fingerprint: pending exact-candidate `aips publish prepare`.
Scope fingerprint: pending exact-candidate `aips publish prepare`.
Candidate commit: pending.

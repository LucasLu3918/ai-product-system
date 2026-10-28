# Core Change Proposal — Plan38 Required Checks Policy Evidence and Recovery

## Approved scope

The user approved the complete Plan38 scope in this Codex task on 2026-10-14. Approval covers the AIPS implementation below and the separate lucas-lab/main Branch Protection update. This proposal records the approved boundary; it does not replace candidate validation or exact-head merge checks.

## System Improvement Review

- Appropriateness: Suitable as a bounded extension of the existing publication diagnostics and authority path.
- User problem: AIPS must distinguish absent Required Checks from policy evidence that the current GitHub identity cannot read, return actionable and safe causes, and keep merge decisions tied to fresh policy evidence.
- Proposed solution: Unify read-only policy observation for Doctor and Merge Authority; classify provider status/errors with source, phase, retryability, and safe next steps; run one read-only Doctor from the Claude Code Hook only for explicitly retryable transient network, rate-limit, or GitHub server errors.
- Existing coverage: PR #332 added Doctor, phase-separated repository/policy/PR/check observations, structured reason codes, and safe recovery. Existing authority and snapshot code already fails closed for several unknown states. Claude Code guidance and Hook envelopes already preserve safe diagnostics; the Hook does not yet auto-run Doctor.
- Reuse / extension: Extend publication_authority.py, publication_diagnostics.py, repository_governance_snapshot.py, governance_guard.py and their existing lifecycle/contract tests. No parallel publisher or new approval gate.
- Lower-layer alternative: GitHub settings alone solve the lucas-lab instance but do not fix AIPS behavior for other repositories or identities. Existing modules are the narrowest reusable layer.
- Context / token cost: No new bootstrap or persistent runtime context; Doctor runs on demand, and the Hook adds one bounded read-only diagnostic only after an explicitly retryable transient failure.
- Security / reliability: Keep policy/API errors sanitized; incomplete evidence remains UNKNOWN and blocks. The Hook may only observe; it cannot repair policy, rerun workflows, publish, or merge.
- Backward compatibility: Keep existing CLI fields and reason codes additive where possible. Preserve the stricter AIPS rule that skipped checks do not pass AIPS validation while reporting GitHub evidence accurately.
- Scenario / test impact: Cover 403, 404, empty and configured policy, endpoint disagreement, failed/pending/skipped/cancelled checks, transient retryability, changed PR head, safe Hook envelope, single Doctor invocation, and no write/merge side effects.
- Human docs impact: Update publication troubleshooting, security, installation, and maintenance guidance plus Scenario 260/261 and conformance/documentation projections.
- Agent docs impact: Update Claude Code adapter recovery instructions to describe bounded automatic observation and preserve native confirmation.
- Architecture diagram impact: docs/ARCHITECTURE.md Mermaid, human architecture overview, and SVG diagrams are N/A; module boundaries and authority semantics remain within the existing publication system.
- Constitution impact: NO. No Human Authority, protected safety, precedence, or approval semantics change.
- Additional optimization candidates: Keep broader acceptance of skipped checks and automatic policy repair out of scope.

## Proposed Scope

### In scope

- Share fresh, read-only branch policy evidence between Doctor and Merge Authority, with Authority re-observing before a merge decision.
- Distinguish UNCONFIGURED, UNKNOWN_PERMISSION, incomplete evidence, missing checks, failing/pending/cancelled checks, and passing checks.
- Return safe structured HTTP status, source, phase, error category, retryability, and remediation guidance without exposing raw provider text or credentials.
- In Claude Code Hook, call the read-only Doctor once only for retryable network, rate-limit, or GitHub server failures; keep denial and native merge confirmation intact.
- Configure lucas-lab/main to require PRs, verify and visual-audit, enforce the rules for administrators, disallow force pushes/deletions, and require zero approvals.
- Add focused tests, a candidate-bound Core Change Test Matrix, scenario coverage, documentation closure, VERSION and CHANGELOG updates.

### Out of scope

- Changing AIPS Constitution or introducing a new Role, Skill, Capability, publisher, or approval gate.
- Treating unavailable policy evidence as success, loosening skipped-check behavior, automatic workflow reruns, automatic policy edits, merge execution from a Hook, admin bypass, direct main pushes, or branch deletion.
- Changes to lucas-lab application code or deployment behavior.

## Expected Files / Modules

- scripts/publication_authority.py
- scripts/publication_diagnostics.py
- scripts/repository_governance_snapshot.py
- scripts/governance_guard.py
- tests/test_publication_authority.py
- tests/test_publication_diagnostics.py
- tests/test_publication_error_recovery.py
- tests/test_publication_planning.py
- tests/evidence/repository_governance_snapshot_lifecycle.py
- tests/validation/repository_governance_snapshot_contracts.py
- tests/scenario_coverage.yaml and publication scenarios/conformance projections
- harness/adapters/claude-code/CLAUDE.md
- affected Human publication/security/installation/maintenance guidance
- .aips/review/CORE_CHANGE_TEST_MATRIX.yaml
- .aips/review/PLAN38_REQUIRED_CHECKS_POLICY_CORE_CHANGE_PROPOSAL.md
- VERSION and CHANGELOG.md

## Impact

### Architecture / Contracts

Extend existing structured Doctor and authority contracts. Keep outputs additive, preserve phase/status fields and fail-closed behavior.

### Data / Migration

No durable runtime data or migration. Policy observations remain run-local and read-only; the local Project Intelligence/Change Impact cache is workspace metadata.

### Security / Reliability

Never infer unconfigured policy from 403 or an empty unrelated endpoint. A merge requires fresh policy evidence, exact PR head/base, mergeability, and passing required checks. Hook recovery is one bounded read-only observation.

### Compatibility / Rollback

Keep current CLI entrypoints and native host envelopes. The changes can be reverted as one coherent PR; GitHub lucas-lab branch policy is independent and has its own read-back verification.

### Tests / Validation

Impact-derived matrix covers unit, integration, contract, security, CLI/Hook, documentation, scenario, and full repository Integration Gate evidence. No production UI or migration applies.

## Risks

- Additional GitHub API observations add bounded latency and may expose missing credential scopes more clearly.
- GitHub check names can change; configuration must be rechecked against actual check runs before relying on the rule.
- Required review count is zero to avoid blocking a single-maintainer project while retaining PR and status-check requirements.

## Recommendation

Implement the approved scope with existing publication abstractions, keep all uncertain policy evidence blocking, and preserve Human authority and native host confirmation.

## Proposed Implementation Order

1. Reconcile Change Impact and targeted caller/consumer evidence.
2. Extend shared policy observation and Authority validation.
3. Add bounded Hook diagnostic recovery and safe reason mapping.
4. Add tests, scenarios, docs, version/changelog, and exact-candidate matrix.
5. Run focused checks, documentation validation, secret scan, and complete local Integration Gate.
6. Publish one PR to AIPS main and merge only after exact-candidate checks pass.

## Approval

Status: APPROVED
Approved by: Human user
Approved at: 2026-10-14 (Codex task; explicit reply to revised Core Change scope)
Approval record: User reply “核准完整範圍（推薦）”
Proposal and approved scope fingerprints are recorded in the external Project Intelligence Change Impact artifact for this candidate.

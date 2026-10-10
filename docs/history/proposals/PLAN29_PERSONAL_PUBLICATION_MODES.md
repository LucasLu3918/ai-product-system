# PLAN29 — Personal and High-Assurance Publication Modes

## System Improvement Review

- Appropriateness: Appropriate. The current security boundary is sound for isolated production issuance but prevents routine personal Git publication when no independent issuer exists.
- User problem: Individual Agents are blocked from ordinary branch pushes and PR work by a mandatory external issuer deployment flow.
- Proposed solution: Make personal publication the default; retain external signed grants as an explicit high-assurance mode.
- Existing coverage: `publication_authority.py` already binds commands to exact repository, candidate and target. `governance_guard.py` already checks candidate content and routes protected operations through one policy point.
- Reuse / extension: Extend the existing publication guard and protected trust-root configuration. Add no role, skill, capability, provider or approval gate.
- Lower-layer alternative: Per-runtime instructions alone would be easy to bypass and would leave Claude/Gemini hooks blocking. Extend the shared guard instead.
- Context / token cost: No added turn-time retrieval or model calls; mode selection is a local deterministic file check.
- Security / reliability: Personal mode deliberately removes the “Agent cannot mint authority” isolation for ordinary engineering Git operations. Preserve local safety scans, exact command/ref validation, branch-only push, and GitHub required checks. High-assurance mode remains fail-closed and root-configured.
- Backward compatibility: No trust-root file means personal mode. Any existing trust-root file selects high-assurance mode; malformed, unreadable, unsafe or untrusted files block publication and never fall back to personal mode. Tag/release operations remain outside personal mode.
- Scenario / test impact: Cover both modes, missing/invalid trust roots, push target restrictions, PR operations, denied tag/release, command drift, content scanning and native hook output.
- Human docs impact: Update Security Assurance, Technology Guide, User Guide, Maintenance, Architecture, Harness, Installation, documentation placement/synchronization and conformance documentation.
- Agent docs impact: Update the canonical Orchestrator and governance publication rules.
- Architecture diagram impact: N/A — the existing guard and trust-root components remain; only mode selection changes.
- Constitution impact: NO. The Human retains authority by task scope; protected main merges occur only when the user requested that outcome and required repository checks pass. No direct push to a protected main branch, release, or production action is added.
- Additional optimization candidates: None included.
- Expected scope: Shared guard, trust-root mode resolver, canonical policy and docs, existing publication tests/scenarios/eval, and this proposal/matrix.
- Risks: Personal mode trusts the repository's currently configured `origin`; an Agent in the same account can rewrite `.git/config` and redirect publication, so this mode does not protect against a malicious Agent exfiltrating source. The Human explicitly accepted this tradeoff to avoid trusted-service setup for individual development. A misconfigured or bypassed personal-mode runtime can publish more freely; GitHub rules and CI remain independent controls. Runtime enforcement remains host-specific and Codex remains advisory.

## Why this is a core change

This changes the default security/authorization behavior for protected Git publication across runtimes and affects the Human publication contract.

## Proposed scope

### In scope

- Default to `personal` when the administrator trust-root file is absent.
- Select `high_assurance` whenever the fixed trust-root path exists; validate the root-owned configuration before use, and fail closed on every invalid/unreadable state.
- In personal mode, allow scoped engineering branch pushes and PR creation after existing content checks, exact command validation, clean-candidate validation and live remote-default binding. The personal-mode hook denies PR merges; a task executor may merge only with explicit task intent, exact PR head/default-base binding and passing required checks.
- Bind personal publication to one matching fetch/push `origin`, the live server-announced default branch and its current commit; do not trust local `origin/HEAD` or alternate remotes as scan/publication scope.
- Keep direct pushes to protected/default branches, tag/release operations, GitHub admin/auto merge flags, branch deletion, failed required checks and unknown command forms blocked.
- In high-assurance mode, keep external Ed25519 grants, exact scope, expiry and transactional single-use consumption unchanged.
- Update shared Claude/Gemini guard behavior, all-runtime orchestration guidance, human docs and conformance evidence. Preserve the existing Codex `ADVISORY` limitation.

### Out of scope

- Deploying a production issuer, generating production keys, changing `/etc`, or installing/updating user runtime hooks.
- Direct pushes to `main`, release/tag creation, production deployment, bypassing GitHub rules or creating a new approval mechanism.
- Removing candidate secret scanning, local validation, repository checks or GitHub branch protection.
- Changing the Constitution, runtime-policy decisions unrelated to Git, or the Codex enforcement capability claim.

## Expected files / modules

- .aips/review/CORE_CHANGE_TEST_MATRIX.yaml
- CHANGELOG.md
- SYSTEM.md
- SYSTEM_CORE.md
- config/documentation-placement.yaml
- core/DECISIONS.md
- core/GOVERNANCE.md
- docs/ARCHITECTURE.md
- docs/history/proposals/PLAN29_PERSONAL_PUBLICATION_MODES.md
- docs/history/proposals/PLAN29_PERSONAL_PUBLICATION_MODES_TEST_MATRIX.yaml
- docs/human/ARCHITECTURE_OVERVIEW.md
- docs/human/CONFORMANCE.md
- docs/human/CONFORMANCE_CURRENT.md
- docs/human/CONFORMANCE_HISTORY_INDEX.md
- docs/human/DOCUMENTATION_MAP.md
- docs/human/DOCUMENTATION_SYNC.md
- docs/human/EVOLUTION_RADAR.md
- docs/human/HARNESS.md
- docs/human/INSTALLATION.md
- docs/human/MAINTENANCE.md
- docs/human/PROJECT_INTELLIGENCE.md
- docs/human/SECURITY_ASSURANCE.md
- docs/human/TECHNOLOGY_GUIDE.md
- docs/human/USER_GUIDE.md
- docs/human/index.md
- orchestration/CHANGE_IMPACT.md
- orchestration/CONFORMANCE.md
- orchestration/DETERMINISTIC_SCHEDULER.md
- orchestration/DOCUMENTATION_SYNC.md
- orchestration/EXECUTION_ISOLATION.md
- orchestration/GITHUB_RULESET_POLICY.md
- orchestration/INTEGRATION_GATE.md
- orchestration/ORCHESTRATOR.md
- orchestration/PROJECT_INTELLIGENCE.md
- orchestration/RELEASE_READINESS.md
- orchestration/RUNTIME_CONTEXT.md
- orchestration/SECRET_HANDLING.md
- orchestration/SYSTEM_SELF_IMPROVEMENT.md
- scripts/governance_guard.py
- scripts/publication_authority.py
- templates/git-publish-proposal.md
- tests/scenario_coverage.yaml
- tests/scenarios/018-git-publish-approval.md
- tests/scenarios/097-approval-scope-drift-stops-protected-action.md
- tests/scenarios/176-mandatory-candidate-secret-scanning.md
- tests/scenarios/240-personal-publication-default.md
- tests/test_publication_authority.py
- tests/validation/conformance_isolation.py

## Impact

- Architecture / contracts: One existing mode resolver feeds the shared guard; shell command and runtime hook response contracts remain stable.
- Data / migration: No schema migration. An absent trust root selects personal mode; a present but invalid root fails closed. Existing valid root configuration continues to select signed high-assurance mode.
- Security / reliability: This is an intentional reduction in publication isolation for personal workflows. Candidate scanning, command/ref constraints and GitHub required checks remain. High assurance retains the existing external trust boundary.
- Compatibility / rollback: Revert this change to restore mandatory grants. To restore high assurance without reverting, install the protected trust-root config; an invalid present file blocks instead of downgrading.
- Tests / validation: See the bound Core Change Test Matrix.
- Secret / credential impact: No secrets acquired, created or persisted. No production signing keys or credentials touched.
- Documentation / diagrams: Update canonical docs listed above; diagrams are N/A because topology is unchanged.

## Approval

Status: APPROVED
Approved by: Human user
Approved at: 2026-10-10 (explicit request to implement the accepted personal-default / high-assurance-opt-in plan)
Approval record: Current task conversation; “請幫我依照建議實作所有事項，本地驗證完後需完成遠端pr合至main” following the approved two-mode plan.
Proposal fingerprint: computed after final proposal text is committed
Scope fingerprint: computed from final changed-file list and test matrix at exact candidate reconciliation

## Proposed implementation order

1. Implement and unit-test deterministic mode resolution without changing signed verification semantics.
2. Route the shared publication hook through personal/high-assurance decisions while preserving content-safety denials.
3. Update policy, Human/Agent documentation and conformance scenarios.
4. Run the impact-derived matrix, full repository validation and exact-candidate Integration Gate.
5. Present one exact candidate and publish one PR; merge only after current required checks pass.

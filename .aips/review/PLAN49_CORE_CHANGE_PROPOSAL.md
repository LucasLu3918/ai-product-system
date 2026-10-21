# Plan49 Core Change Proposal — Publication Hook Timeout Diagnostics

## Purpose

Keep Claude Code's protected-publication PreToolUse guard fail-closed while returning a useful, bounded denial when remote observations time out. Make `aips publish prepare` distinguish a timeout from other remote observation failures and explain the safe recovery path.

## Why this is a Core Change

The change affects a protected Git publication boundary, synchronous native hook behavior, stable diagnostic contracts and Scenario 261. The current Claude guard hook is configured for 10 seconds, but a retryable denial may synchronously launch a read-only Doctor subprocess with a 60-second timeout. If that exceeds the host limit, Claude receives no structured AIPS diagnosis. Prepare currently groups `TimeoutExpired` with generic remote failures and its output does not identify the timeout-specific recovery path.

## Approved Scope

### In scope

- Remove the nested Doctor subprocess from Claude PreToolUse denial handling. Return the original safe denial promptly and tell the user to run `aips publish doctor --worktree <candidate-root>` as a separate read-only diagnostic.
- Keep publication authorization fail-closed on unavailable remote evidence; no operation is retried, authorized or executed by the diagnostic path.
- Preserve the stable `REMOTE_OBSERVATION_FAILED` top-level reason for compatibility and add an allowlisted timeout `detail_code`, `phase`, `error_class: TimeoutExpired`, retryability and actionable English/Traditional Chinese recovery guidance.
- Ensure the timeout detail never includes raw exception text, shell command, remote URL, credentials, private paths or headers.
- Update Prepare, Hook, Doctor recovery tests and Scenario 261, the exact-candidate Core Matrix, and all documentation additions required by `aips publish docs-impact`.

### Out of scope

- Changing publication, Human approval, native Host confirmation, merge, required-check, secret-scan or branch-protection policy.
- Increasing the Claude hook timeout or allowing protected actions when remote evidence is unavailable.
- Running Doctor, retrying a network request, granting authority or mutating Git/GitHub state from a denial diagnostic.
- Printing raw stderr, exception messages, commands, credentials, URLs or absolute local paths.
- Adding a new persistent ledger, schema, Role, Skill, Capability, runtime claim or architecture component.
- Broader remote-observation performance work outside the nested Doctor and timeout classification paths.

## Expected Files / Modules

- `scripts/governance_guard.py` — stop synchronous Doctor invocation and return safe recovery guidance.
- `scripts/publication_planning.py`, `scripts/publication_authority.py` — classify Prepare timeouts with stable, allowlisted details.
- `tests/test_publication_diagnostics.py`, `tests/test_publication_planning.py`, `tests/test_publication_error_recovery.py` — regression and redaction evidence.
- `tests/scenarios/261-publication-diagnostics-and-safe-recovery.md` — update the retryable-hook contract.
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` and this proposal.
- Documentation closure: `docs/ARCHITECTURE.md`, `docs/human/{ARCHITECTURE_OVERVIEW,CONFORMANCE,INSTALLATION,MAINTENANCE,PROJECT_INTELLIGENCE,SECURITY_ASSURANCE,TECHNOLOGY_GUIDE,USER_GUIDE}.md`, and `orchestration/{CONFORMANCE,CONTENT_SAFETY_BOUNDARY,CORE_CHANGE_TESTING,DETERMINISTIC_SCHEDULER,EXECUTION_ISOLATION,INTEGRATION_GATE,ORCHESTRATOR,RESOURCE_AUTHORIZATION,RUNTIME_POLICY_ENFORCEMENT}.md`.

## Impact

### Architecture / Contracts

The existing Claude PreToolUse JSON envelope and top-level reason code remain compatible. The synchronous hook no longer launches a second diagnostic process on a retryable failure. Prepare adds an allowlisted timeout detail while preserving the existing stable failure code and phase contract.

### Data / Migration

No schema migration or new persistent state. The optional existing diagnostic ledger remains allowlisted and unchanged.

### Security / Reliability

The authorization result remains deny / `NOT_EXECUTED`; Doctor remains read-only and opt-in as a separate command. No raw upstream or exception text is emitted. Hook runtime is bounded by avoiding a nested 60-second child process.

### Compatibility / Rollback

No CLI argument, hook event, top-level reason code or authorization behavior is removed. Reverting the PR restores the previous nested Doctor behavior. Existing `doctor_observation` output is replaced by a safe command/recovery hint.

### Tests / Validation

Test that retryable Claude hook failures do not invoke Doctor and still return a redacted denial with actionable recovery. Test `TimeoutExpired` versus network/auth/config failures in Prepare, preserving exact phase and `TimeoutExpired` classification without raw exception details. Run focused publication tests, Scenario 261, documentation closure, repository validation, strict candidate/history secret scan and the exact-candidate Integration Gate. Required PR checks and main checks remain separate evidence.

### Secret / Credential Impact

Secrets required: NO.

Approved acquisition mechanism: N/A.

Leakage/redaction review: assert raw exception, command, endpoint and secret sentinels do not appear in CLI or hook output.

Rotation/revocation plan if exposure is found: stop publication, remove and rotate the exposed credential, then rerun candidate scans.

### Documentation / Diagrams

Update the User Guide and Security Assurance for the immediate fail-closed response and manual Doctor recovery; update Agent instructions, conformance, maintenance, architecture and testing guidance through the required documentation closure. No architecture topology or authority boundary changes.

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` Mermaid: AFFECTED — required placement closure; clarify separate hook denial and explicit Doctor recovery.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: AFFECTED — required placement closure; flow semantics only.
- Human SVG architecture/lifecycle diagrams: N/A — no components, topology or authorization flow is added.

## Risks

- A user must run Doctor separately to get remote endpoint evidence. The hook denial will still identify the timeout class and safe next command.
- A concurrent remote failure can be transient; the hook will still deny. Re-observation remains an explicit read-only user action.
- Bounded lexical traversal was truncated at `max_edges`; direct code and consumer review is recorded in Change Impact, and global graph coverage remains partial.

## Recommendation

Proceed with the approved narrow diagnostic change. Do not increase the synchronous hook timeout or weaken the protected-publication fail-closed boundary.

## Proposed Implementation Order

1. Add focused regression coverage for the timeout and no-nested-Doctor behavior.
2. Implement the allowlisted Prepare timeout detail and immediate hook recovery response.
3. Update Scenario 261 and documentation closure.
4. Bind the final changed-file set to the Core Matrix, run the full local Integration Gate, then publish the exact PR candidate and wait for required checks.

## Approval

Status: APPROVED
Approved by: Human user in the current task
Approved at: 2026-10-21T09:01:00Z
Approval record: User selected “核准此範圍（Recommended）” for this exact scope in the current task.
Constitution impact: NO

# Plan44 System Improvement Review — Publication Diagnostics and Recovery

## Review

- **Appropriateness:** Appropriate. Existing AIPS publication diagnostics fail closed but collapse supported-shell command shape into one generic refusal and cannot observe a Claude native tool failure after execution starts.
- **User problem:** Make publication blockers actionable and distinguish AIPS authorization denial from an actual native command failure without exposing private command or error data.
- **Proposed solution:** Add bounded command-form detail codes and use Claude Code `PostToolUseFailure` for a separate, read-only native execution observation.
- **Existing coverage:** Exact-head merged idempotency, squash/tree proof, safe branch cleanup, hook version health, error redaction, reason codes, and Required Checks already exist. Keep those implementations and extend their conformance coverage instead of duplicating them.
- **Reuse / extension candidates:** `publication_commands.py`, `PublicationError`, existing diagnostic schema, `governance_guard.py`, managed Claude hook composition, and Scenario 261.
- **Lower-layer alternative:** Add detail at command diagnosis and hook adapter layers. No new global capability, Role, Skill, gate or ledger is needed.
- **Context / token cost:** No bootstrap context increase. New detail is emitted only on the affected diagnosis or native failure event.
- **Security / reliability:** Fail closed for every unsupported command form. PostToolUseFailure reports only fixed categories and a bounded parsed exit code; it does not output host error text, command, paths or secrets, and cannot retry or authorize.
- **Backward compatibility:** Preserve `COMMAND_FORM_UNSUPPORTED`, existing authorization envelopes, and Claude's version-bound PreToolUse `onFailure` behavior. Add a separate event handler without changing prompt-context behavior.
- **Scenario / test impact:** Extend Scenario 261, publication focused tests and Claude runtime lifecycle contracts; retain existing merge, branch cleanup and hook-health regression coverage.
- **Human docs impact:** Update User Guide, Security Assurance, Maintenance and both Conformance views.
- **Agent docs impact:** Update Claude adapter instructions and Human/Agent Documentation Sync contracts.
- **Architecture diagram impact:** N/A. This extends existing diagnostics and native adapter responsibilities without changing component topology, authority flow or deployment boundaries.
- **Constitution impact:** NO. No Human authority, policy precedence, safety boundary, or amendment semantics change.

## Recommendation and Scope

Reuse the existing publication error and managed-hook abstractions. Add safe `detail_code` values beneath the existing reason code and a Claude-only `PostToolUseFailure` event that distinguishes started native execution from a PreToolUse denial. Preserve the user's approved Plan44 scope; already-covered merge, cleanup and hook-health behaviors receive regression evidence only.

Additional optimization candidates: none recommended for NOW.

## Approval

- Status: APPROVED
- Approved by: Human user
- Approval reference: Direct approval in the current Plan44 task after review of the bounded reuse-first scope.
- Approved at: 2026-10-18 (Asia/Taipei)

# Core Change Proposal: Shell Command Substitution Classification

## Purpose

Remove avoidable Claude/Gemini Shell retries caused by supported `$(...)` expressions being classified at the wrong Git/GitHub CLI token position, while preserving publication scope checks.

## Why this is a core/large change

This changes a shared pre-tool publication security guard and its shell parser. A false allow could hide a protected operation or bind it to a dynamic repository/ref; a false deny interrupts ordinary engineering work.

## Proposed Scope

### In scope

- Locate Git and GitHub CLI command words after their supported global options.
- Permit supported argument substitutions and inspect them recursively, including in unquoted heredoc bodies.
- Keep quoted/escaped heredoc text literal and retain fail-closed handling for unsupported syntax.
- Return stable, sanitized hook denial reasons for dynamic command identity, context and unsupported syntax.
- Add regression evidence and synchronize security, runtime, user, maintenance, architecture and conformance documentation.

### Out of scope

- Executing substitutions in the hook, broad Shell sandboxing, process/network isolation, changing runtime capability claims, or changing publication/merge authority.
- Accepting dynamic executable/subcommand/context values or relaxing literal candidate SHA/ref/repository/approval bindings.

## Expected Files / Modules

- `scripts/publication_commands.py`, `scripts/governance_guard.py`, `tests/test_publication_authority.py`
- `tests/scenarios/097-approval-scope-drift-stops-protected-action.md`
- `orchestration/RUNTIME_POLICY_ENFORCEMENT.md`, `orchestration/ORCHESTRATOR.md`, `orchestration/DETERMINISTIC_SCHEDULER.md`
- `docs/ARCHITECTURE.md`, `docs/human/ARCHITECTURE_OVERVIEW.md`, `docs/human/CONFORMANCE.md`, `docs/human/MAINTENANCE.md`, `docs/human/SECURITY_ASSURANCE.md`, `docs/human/TECHNOLOGY_GUIDE.md`, `docs/human/USER_GUIDE.md`
- `.aips/review/CLAUDE_SHELL_EXPANSION_CORE_CHANGE_PROPOSAL.md`, `.aips/review/CLAUDE_SHELL_EXPANSION_SYSTEM_IMPROVEMENT_REVIEW.md`, and the exact-candidate Core Change Test Matrix.

## Impact

### Architecture / Contracts

No public API, runtime envelope, authority model or system diagram changes. The existing parser facade and hook response envelopes remain compatible; denial text becomes more actionable and carries stable codes.

### Data / Migration

No persistent product data or migration.

### Security / Reliability

The bounded parser remains fail closed. It inspects, but never runs, nested commands. Dynamic executables, Git/GitHub subcommands and Git context option values remain denied. Publication still requires literal scope-bindable arguments and existing content checks.

### Compatibility / Rollback

Existing callers continue to receive command argv lists; `CommandError` gains a reason-code attribute. Revert the candidate to restore the old stricter heredoc denial behavior.

### Tests / Validation

Focused Shell/publication tests, hook subprocess regression, Scenario 097, repository validation, strict candidate/history secret scan and exact-candidate Integration Gate. Architecture diagrams: N/A; no trust boundary or authority flow changes.

### Secret / Credential Impact

Secrets required: NO. No command text is added to logs or persistent evidence; hook denial messages include only a stable reason code and generic recovery hint.

## Risks

- Heredoc expansion parsing can misclassify quoting/escaping if the parser wrapper does not preserve Shell semantics; malformed/ambiguous forms must deny.
- Dynamic arguments to a publication operation must not become reusable exact-scope approvals.
- Codex remains ADVISORY; this change does not provide OS-level Shell isolation.

## Recommendation

Extend the existing bounded AST parser and shared guard, with a regression matrix for positive, negative and escaped inputs. Do not introduce a new guard or remove dynamic-value checks.

## Proposed Implementation Order

1. Fix command-position parsing and reason codes.
2. Parse unquoted heredoc substitutions without executing them.
3. Add positive and fail-closed regressions.
4. Synchronize documentation, exact-candidate evidence and publication checks.

## Approval

Status: APPROVED
Approved by: Human (explicit task instruction)
Approved at: 2026-10-11
Approval record: User requested implementation of every item in the immediately preceding System Improvement Review, local validation, PR creation and merge to `main`.
Proposal fingerprint: computed from the committed proposal in the candidate matrix.
Scope fingerprint: bound to the actual changed-file set in the candidate matrix.

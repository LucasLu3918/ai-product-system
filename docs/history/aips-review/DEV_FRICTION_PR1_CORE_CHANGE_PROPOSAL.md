# Core Change Proposal: Claude Code Publication Command Compatibility (Dev Friction PR1)

## Purpose

Stop Claude Code from retrying guessed command variants after the AIPS PreToolUse publication Hook denies a commit, push or PR command, without relaxing any publication security control.

## Why this is a core/large change

It changes the shared PreToolUse publication guard, the personal publication validator, the Shell parser classification and the Prepare scan-evidence lifetime. A false allow could publish unbound or unscanned content; a false deny blocks ordinary delivery.

## Measured Baseline

An in-process Hook harness with a local fixture repository (no remote network) classified the forms Claude Code typically emits:

| Form | Before | After |
|---|---|---|
| `git commit -m "$(cat <<'EOF' … EOF)"`, optionally after literal `git add … &&` | allow | allow (unchanged) |
| `git commit` with an unquoted heredoc or `$VAR` message | deny, generic recovery text | deny, `COMMIT_FORM_UNSUPPORTED` / `PUBLICATION_INPUT_UNBOUND` with the quoted-heredoc recipe |
| `git push -u origin <branch>` or `HEAD` | deny `PUSH_SOURCE_NOT_EXACT_SHA` | deny, recipe names `<full-sha>:refs/heads/<branch>` from Prepare |
| exact push after Prepare | allow | allow (unchanged) |
| `git push … && gh pr create …` | deny `INTERNAL_DIAGNOSTIC_GAP` | deny `COMMAND_FORM_UNSUPPORTED` / `MULTI_COMMAND_UNSUPPORTED` with a one-command-per-call recipe |
| `gh pr create --body "$(cat <<'EOF' …)"` whose body has backticks or `$` | deny `COMMAND_FORM_UNSUPPORTED` (literal treated as dynamic) | literal accepted; normal metadata, candidate and evidence checks apply |
| fully explicit `gh pr create` after Prepare | always deny `PUBLICATION_SCAN_EVIDENCE_REQUIRED` (Prepare stored only push-bound evidence) | allow when Prepare stored evidence bound to the planned PR operation and target |
| `gh pr create` without `--repo/--head/--base` | deny | deny `PR_METADATA_INCOMPLETE` with the full recipe |
| `$VAR`, backticks, `$"…"`, command substitution or unquoted heredoc in a PR argument | deny | deny `PUBLICATION_ARGUMENT_DYNAMIC` with recipe |

## Proposed Scope

### In scope

- Personal-mode Hook and read-only `aips publish diagnose` parse with `mark_dynamic=True`, so quoted literal `$`/backticks are data and every real expansion keeps its NUL marker and denies.
- Treat `$"..."` locale strings as dynamic.
- Prepare stores scan evidence for the PR creation it plans, from the same exact-candidate scan, bound to that operation and target.
- Scan-evidence TTL 300 → 1800 seconds; the exact candidate, operation, target, remote OID, diff, scanner and policy digest binding is unchanged and the stored lifetime is still capped by the TTL.
- Stable detail codes `PUBLICATION_ARGUMENT_DYNAMIC`, `COMMIT_FORM_UNSUPPORTED` and an updated `MULTI_COMMAND_UNSUPPORTED`; multiple protected operations become a classified `COMMAND_FORM_UNSUPPORTED` instead of `INTERNAL_DIAGNOSTIC_GAP`.
- Static English and Traditional Chinese recipes in `next_step`/`next_step_zh`; the Claude Code denial reason also carries the static next step. No command text is echoed.
- Claude Code adapter recipe section and TTL wording in canonical docs; Scenario 261 extension.

### Out of scope

- Accepting bare-branch or `HEAD` push refspecs, inferring `--repo/--head/--base`, chaining protected operations, or allowing unquoted heredocs.
- Storing scan evidence for planned merges (observed limitation, see Risks), `aips publish ship`, profile switches, PII email allowlisting.

## Expected Files / Modules

- `scripts/governance_guard.py`, `scripts/publication_authority.py`, `scripts/publication_commands.py`, `scripts/publication_planning.py`, `scripts/publication_scan_evidence.py`
- `tests/test_publication_authority.py`, `tests/test_publication_planning.py`, `tests/test_publication_scan_evidence.py`, `tests/scenarios/261-publication-diagnostics-and-safe-recovery.md`
- `harness/adapters/claude-code/CLAUDE.md`, `harness/HARNESS_PROTOCOL.md`, `docs/ARCHITECTURE.md`, `docs/human/HARNESS.md`, `docs/human/SECURITY_ASSURANCE.md`, `docs/human/TECHNOLOGY_GUIDE.md`, `docs/human/USER_GUIDE.md`
- `.aips/review/DEV_FRICTION_PR1_CORE_CHANGE_PROPOSAL.md`, `.aips/review/DEV_FRICTION_PR1_SYSTEM_IMPROVEMENT_REVIEW.md`; Core Change Test Matrix entries are consolidated by the integration branch owner.

## Impact

### Architecture / Contracts

No new trust boundary, authority path or runtime envelope. `validate_action_form`, `action` and `validate_personal_action` gain an optional `literal_marked` keyword (default keeps the old stricter check for existing callers).

### Data / Migration

No persistent product data. Existing 300-second evidence records remain valid until their own `expires_at`.

### Security / Reliability

Secret scan, PII scan, content safety, one protected operation per invocation, exact candidate/target binding, merge Human confirmation and the `--admin`/`--delete-branch` prohibition are unchanged. Content safety still scans the raw command, so heredoc text is inspected exactly. The longer TTL widens only the reuse window of a passing scan for the identical candidate, target, remote tip and policy; any drift invalidates it.

### Compatibility / Rollback

Callers that do not pass `literal_marked` keep the old behavior. Revert the candidate to restore the previous TTL and stricter literal handling.

### Tests / Validation

Unit and in-process Hook lifecycle tests for accepted and denied forms, subprocess Hook denials with recipe and redaction checks, Prepare PR-evidence binding, TTL boundary and over-TTL rejection, Scenario 261, capability registry check and repository preflight. Architecture diagrams: N/A.

### Secret / Credential Impact

Secrets required: NO. Diagnostics stay static and input-free.

## Risks

- `mark_dynamic` must flag every expansion; regression tests cover `$VAR`, backticks, `$"..."`, command substitution and unquoted heredocs, and unclassified forms still deny.
- Planned merges still require merge-bound evidence that Prepare does not store, so a personal-mode merge through the Claude Code Hook is denied with `PUBLICATION_SCAN_EVIDENCE_REQUIRED`; left for a separately approved change.
- Codex remains ADVISORY.

## Recommendation

Implement the scoped compatibility fixes and recipes in the existing parser, guard and Prepare path; do not add a new guard or relax any binding.

## Approval

Status: APPROVED
Approved by: Human (explicit task instruction)
Approved at: 2026-10-26
Approval record: The user approved the full AIPS dev-friction plan ("全部依建議執行") and asked to execute everything; this approval covers exactly the PR1 scope above.
Proposal fingerprint: computed from the committed proposal in the candidate matrix.
Scope fingerprint: bound to the actual changed-file set in the candidate matrix.

# Plan36 Core Change Proposal: Publication Diagnostics and Safe Recovery

## Purpose

Carry the complete Plan36 recommendations into AIPS: preserve actionable GitHub API evidence, identify precise publication failures, show dirty-worktree details, distinguish policy evidence levels and publication phases, make already-merged recovery explicitly idempotent, and provide safe Claude Code recovery guidance.

## Why this is a core change

The change crosses publication authority, CLI diagnostics/planning, GitHub policy evidence, native hook consumers, test contracts, and human/agent documentation. It changes protected publication failure behavior and must preserve existing authority boundaries.

## Proposed Scope

### In scope

- Extend the read-only repository governance snapshot to retain sanitized HTTP status, endpoint, error class, and safe GitHub message while never retaining credentials or raw headers.
- Resolve effective branch rules alongside repository rulesets and classic branch protection. Treat explicit no-classic-protection evidence separately from unavailable/incomplete evidence; never infer unprotected from an arbitrary 404 or inaccessible endpoint.
- Give publication validation failures stable, specific reason codes and stage/authority attribution; preserve compatibility fields and existing default behavior for consumers.
- Provide read-only dirty-worktree details grouped by staged, modified, deleted, and untracked state, with safe next steps and no automatic stash/delete/ignore.
- Separate push, PR creation/update, checks, and merge blockers by phase and distinguish AIPS policy blockers from GitHub/host observations.
- Confirm exact-head already-merged PR recovery returns `ALREADY_MERGED`/post-merge reconciliation without proposing another push, PR, or merge.
- Add conservative Claude Code guidance that separates safe observation/recovery from actions requiring Human or native host approval.
- Add regression scenarios for API 401/403/404, rulesets/effective rules, dirty state, precise refusal codes, publication phases, duplicate/existing/merged PRs, remote drift, stale authorization, and preserved Human authority.
- Update CLI and Human/Agent documentation and architecture narrative as needed.

### Out of scope

- Changing GitHub protection/rulesets, credentials, permissions, branch policy, or external repositories.
- Weakening fail-closed evidence, secret scanning, Proposal-first, Human Authority, native host confirmations, or merge required-check policy.
- Executing publication/merge automatically from a diagnostic, granting authorization from evidence, or exposing raw stderr/headers/tokens.
- Rebuilding Plan34/35 functionality or changing unrelated product capabilities.

## Expected Files / Modules

- `scripts/repository_governance_snapshot.py`
- `scripts/publication_authority.py`
- existing publication CLI/diagnostic/planning modules and lazy facade as needed
- focused tests, validation contracts, and scenario coverage
- `harness/adapters/claude-code/CLAUDE.md`
- Human publication guidance and canonical architecture narrative if behavior description changes
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`

## Impact

### Architecture / Contracts

Keep the existing publication pipeline and CLI facade. Add structured diagnostic fields without removing existing fields. Diagnostics remain read-only and authorization remains separate. No new service, role, capability, skill, or approval gate.

### Data / Migration

No persistent user data or migration. Diagnostic JSON gains additive fields; maintain versioned/compatible consumers.

### Security / Reliability

Preserve fail-closed behavior for UNKNOWN evidence. Redact tokens, authorization headers, credential-bearing URLs, private path contents, and raw unbounded command output. File paths in dirty details are repository-relative; diagnostics never mutate worktrees or issue grants.

### Compatibility / Rollback

Keep existing CLI entrypoints, exit-code semantics where contractual, and existing diagnostic keys. New fields and CLI detail option are additive. Revert the candidate to restore prior behavior; no migration needed.

### Tests / Validation

Use the active exact-candidate Core Change Matrix. Include 401/403/404 and malformed/missing evidence cases, explicit branch-exists verification, rulesets/effective-rule cases, staged/modified/deleted/untracked worktree states, each failure-stage reason, PR lifecycle/idempotency, stale observations, redaction, and authority-preservation negatives. Run focused lifecycle tests and the complete local Integration Gate for the final frozen candidate; require exact PR CI aggregate before merge.

### Secret / Credential Impact

Secrets required: NO.

Leakage/redaction review: Required. Consume only safe, bounded GitHub error fields; never emit auth headers/tokens or raw stderr.

### Documentation / Diagrams

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` Mermaid: N/A — publication topology is unchanged; update only the existing read-only planning narrative if diagnostic fields/stages need explanation.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: N/A — no component or data-flow topology change.
- Human SVG architecture/lifecycle diagrams: N/A — no new component, approval boundary, or execution path.

## Risks

- A false `UNPROTECTED` classification could bypass required policy; only complete, explicit evidence may support it.
- Raw upstream error payloads can disclose credentials or private repository context; normalize and redact before presentation.
- Reason-code or output-shape changes can break hooks and agents; preserve old fields and bind compatibility with tests.
- Idempotency must bind exact PR head, merge commit, and live default base; a PR with a different head remains blocked.

## Recommendation

Extend the existing publication diagnostic and planning contracts. Preserve the current fail-closed authority design and add evidence, phase, and recovery specificity at the lowest existing layer.

## Proposed Implementation Order

1. Add normalized GitHub API evidence and effective rules to the snapshot.
2. Add stable reason/phase/blocker fields and dirty-worktree details.
3. Tighten already-merged idempotency and phase-specific planning.
4. Lifecycle/scenario coverage and Claude Code/Human documentation.
5. Exact-candidate validation and secret scanning precede PR preparation.

## Approval

Status: APPROVED
Approved by: Human user
Approved at: 2026-10-13 (Asia/Taipei)
Approval record: User request in this task: “請幫我依照建議實作所有事項，本地驗證完後需完成遠端pr合至main”; scope is the complete Plan36 recommendation in the referenced conversation.
Proposal fingerprint: pending exact-candidate calculation
Scope fingerprint: pending exact-candidate calculation

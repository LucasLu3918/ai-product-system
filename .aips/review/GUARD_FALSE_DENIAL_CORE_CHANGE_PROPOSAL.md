# Core Change Proposal: Publication Guard False Denials

## Purpose

Stop the Claude/Gemini publication guard from denying read-only commands and Claude Code's standard commit forms, keep publication-capable forms denied, and make every command-classification denial report a stable reason code.

## Why this is a core change

This changes the shared pre-tool publication guard, its shell parser, commit content inspection and publication worktree validation. A false allow could hide a commit or publication path or skip content inspection; a false deny interrupts ordinary engineering work.

## Approved scope

Approved by the user on 2026-10-19 from `.aips/review/GUARD_FALSE_DENIAL_SYSTEM_IMPROVEMENT_REVIEW.md`, excluding every LATER item.

### In scope

- Read-only classification: dynamic directory/repository options on non-publication verbs, a dynamic path prefix to a literal non-Git executable, `gh api` GET requests, local `git lfs` subcommands and repository-defined read-only Git aliases.
- Commit forms: quoted-delimiter heredoc messages, literal `git add` commands joined by `&&`, `-a`/`-am`, `--amend` with a message or `--no-edit`; content the commit would include is scanned before it is staged.
- Untracked files no longer make the publication worktree `DIRTY`; they stay listed in diagnostics.
- Stable reason codes for every command-classification denial, including the new `GIT_ALIAS_PUBLICATION_UNSUPPORTED` and `UNSUPPORTED_GIT_LFS_COMMAND`.

### Out of scope

- Downgrading commit-time `REVIEW` findings (rejected in review: publication-time candidate scanning covers secrets only).
- `gh api graphql` reads, `git commit <pathspec>`/`--only`, interpreter/script execution, documentation-sync relaxation.
- Any change to approval, merge, release or high-assurance authority, or to the local Integration Gate clean-worktree requirement.

## Implementation notes

The implementation started from a forked session's partial diff and was corrected to the approved review:

- The fork downgraded commit-time injection `REVIEW` findings to warnings; this was reverted, and a regression test now requires `CONTENT_REVIEW_REQUIRED` to block both message and staged content.
- The fork's commit-only heredoc regex did not reject a body line equal to the delimiter (which ends the heredoc early) and was unreachable because the shared parser still rejected the form. Inlining now lives in `publication_commands.inline_literal_heredocs`, only for a prefix of plain words and quotes, and stops at any expansion, backtick, comment or other heredoc.
- Alias resolution is limited to plain `git <alias>`; dynamic `-c`/`--config-env`/`--exec-path` values always deny; shell aliases are classified by their body with bounded depth.
- Refinements versus the review text: a chained `git add` uses `git add --dry-run` for the exact staged set, so `-f` is supported; a commit after any earlier command substitution still denies.

## Expected files

- `scripts/publication_commands.py`, `scripts/governance_guard.py`, `scripts/publication_authority.py`, `scripts/publication_planning.py`
- `tests/test_publication_authority.py`, `tests/test_publication_planning.py`, `tests/scenario_coverage.yaml`
- `tests/scenarios/099-git-publication-tool-guard.md`, `tests/scenarios/169-runtime-content-safety-publication.md`
- Human docs: `docs/ARCHITECTURE.md`, `docs/human/ARCHITECTURE_OVERVIEW.md`, `CONFORMANCE.md`, `INSTALLATION.md`, `MAINTENANCE.md`, `PROJECT_INTELLIGENCE.md`, `SECURITY_ASSURANCE.md`, `TECHNOLOGY_GUIDE.md`, `USER_GUIDE.md`
- Agent docs: `orchestration/CONFORMANCE.md`, `CONTENT_SAFETY_BOUNDARY.md`, `CORE_CHANGE_TESTING.md`, `INTEGRATION_GATE.md`, `ORCHESTRATOR.md`, `RESOURCE_AUTHORIZATION.md`, `RUNTIME_POLICY_ENFORCEMENT.md`
- `.aips/review/GUARD_FALSE_DENIAL_SYSTEM_IMPROVEMENT_REVIEW.md`, this proposal and the exact-candidate Core Change Test Matrix

## Impact

### Architecture / contracts

No trust-boundary, authority or diagram change. `shell_commands()` keeps its default return shape; `mark_dynamic` is opt-in. Hook envelopes are unchanged. `worktree_dirty_details()` adds `untracked_count`.

### Security

Every relaxation is limited to forms classified as non-publication, and each is paired with a still-denied publication-capable counterpart in `GuardFalseDenialTest`. Content inspection coverage only grows. The guard remains a cooperative-agent safeguard, not an interpreter sandbox.

### Backward compatibility

Three existing assertions were intentionally reversed: dynamic `-C`/`--repo` with a read-only verb, `git commit -a`, and untracked-only `WORKTREE_DIRTY`. The live hook changes only after the installed AIPS system is updated.

## Rollback

Revert the PR; no persistent data or configuration migration is involved.

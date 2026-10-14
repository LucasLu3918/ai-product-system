# Scenario 261: Publication diagnostics and safe recovery

Given an explicit candidate worktree, when AIPS observes GitHub branch, effective-rule, ruleset, and classic branch-protection endpoints, then it records each endpoint, HTTP status, bounded sanitized error and evidence level. A branch-protection 404 is `NOT_CONFIGURED` only when the branch itself exists; if `branch.protected` is true while classic policy is permission-hidden, policy state is `UNKNOWN_PERMISSION`; only complete cross-checked evidence can establish an unconfigured policy.

Given a dirty candidate, when publication validation or `aips publish doctor --worktree-details` inspects it, then staged, modified, deleted, and untracked repository-relative paths are reported without reading file contents or changing the worktree. Unknown files are preserved for Human review.

Given any protected publication refusal, when AIPS returns its diagnostic, then it includes a stable reason code, phase, blocker source, retryability, safe recovery mode, candidate SHA when verified, timestamp, and diagnostic ID; raw stderr, headers, credentials, and exception text are not emitted. Push, PR creation, checks, and merge failures remain attributed to their own phases.

Given a PR already merged with the exact candidate head and a merge commit reachable from the live default base, when preparation is repeated, then the result is `ALREADY_MERGED` and plans post-merge reconciliation without a push, PR creation, or merge invocation. A different head, unavailable merge commit, or stale base remains blocked.

Given Claude Code Hook receives a retryable network, rate-limit or GitHub server error, when it handles the denial, then it runs the read-only Doctor once and returns only bounded safe fields; Host denial, missing Human approval, stale scope, or missing/failing required checks still require the named review or approval. Diagnostics never grant publication authority.

Given the local candidate branch differs from the repository default, when `aips publish doctor` observes policy, then it reports both identities and queries the explicit/default target branch, never the candidate by implication. API status and endpoint categories distinguish authentication, permission, contextual missing resources, rate limits, server errors and network failures; unconfirmed evidence remains `UNKNOWN`.

Given an API response or local command contains credentials or raw provider details, when a diagnostic or Claude Code PreToolUse denial is rendered, then the output contains only bounded safe evidence and an allowlisted diagnostic record. Given a retryable observation failure, when recovery is requested, then it re-collects evidence only and reports `authorized: false` and `executed: false`; no push, PR, merge or policy mutation occurs.

Evidence: `tests/test_publication_authority.py`, `tests/test_publication_planning.py`, `tests/evidence/repository_governance_snapshot_lifecycle.py`, `tests/validation/repository_governance_snapshot_contracts.py`, and `tests/validation/publish_preflight_contracts.py`.

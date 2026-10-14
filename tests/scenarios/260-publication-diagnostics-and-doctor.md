# Scenario 260 — Publication diagnostics and Doctor

## Request

An agent cannot explain why a checked PR merge was blocked, or a maintainer is configuring publication for a repository for the first time.

## Expected

- `aips publish doctor` performs only read-only GitHub observations and reports repository/auth/configuration, merge methods, branch policy visibility and optional PR/check state.
- Required Checks are distinguished as unconfigured, passing, failing, pending, missing/skipped, cancelled, or unavailable due to authentication, permissions, network or API response problems.
- Missing, malformed or permission-limited policy evidence remains blocking and never implies that protection is absent.
- `aips publish diagnose` validates a literal `gh pr merge` against the exact PR, head SHA, base, method and live checks without executing it or consuming a grant.
- Diagnostics have stable reason code, phase, safe category, source and actionable next step; raw GitHub output and credentials do not appear.
- Invalid merge method, forbidden flags and missing or stale pinned head report distinct errors; cleanup stays separate.
- A missing gh required-check report becomes UNCONFIGURED only with verified empty policy, MISSING if policy names requirements, and UNAVAILABLE if policy is not known. It is never assumed to mean pending.
- Host Auto Mode rejection is recorded separately from AIPS/GitHub errors, cannot be bypassed by command disguise.
- The recovery report is read-only and non-authorizing, distinguishing Host confirmation, external grant and already merged status.
- Claude Code, OpenCode and Codex receive consistent guidance while retaining native permissions and Human Authority; no policy changes, bypasses or automatic merge are introduced.
- The candidate/source branch is reported separately from the remote default policy branch; `--branch` is an explicit policy target override.
- GitHub API 401, 403, contextual 404, 429/rate-limit, 5xx, network/CLI and malformed-response evidence retains a safe endpoint/status category; unknown policy remains blocking.
- Claude Code denial context carries a bounded diagnostic ID, reason code, phase, category, retry classification and next step without raw command, tool arguments or credentials.
- Recovery retryability matches the observed cause: transient network, rate-limit, server and pending-check states allow read-only re-observation; permission, authentication, policy, stale candidate and Host/Human authority do not.

## Evidence

- `scripts/publication_diagnostics.py`
- `scripts/publication_authority.py`
- `scripts/publication_planning.py`
- `scripts/publish_preflight.py`
- `tests/test_publication_diagnostics.py`
- `tests/test_publication_planning.py`
- `tests/validation/publish_preflight_contracts.py`
- `harness/adapters/claude-code/CLAUDE.md`
- `harness/adapters/codex/AGENTS.md`
- `harness/adapters/opencode/AGENTS.md`

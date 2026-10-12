# Scenario 260 — Publication diagnostics and Doctor

## Request

An agent cannot explain why a checked PR merge was blocked, or a maintainer is configuring publication for a repository for the first time.

## Expected

- `aips publish doctor` performs only read-only GitHub observations and reports repository/auth/configuration, merge methods, branch policy visibility and optional PR/check state.
- Required Checks are distinguished as unconfigured, passing, failing, pending, missing/skipped, cancelled, or unavailable due to authentication, permissions, network or API response problems.
- Missing, malformed or permission-limited policy evidence remains blocking and never implies that protection is absent.
- `aips publish diagnose` validates a literal `gh pr merge` against the exact PR, head SHA, base, method and live checks without executing it or consuming a grant.
- Diagnostics have stable reason code, phase, safe category and actionable next step; raw GitHub output and credentials do not appear.
- Claude Code, OpenCode and Codex receive consistent guidance while retaining native permissions and Human Authority; no policy changes, bypasses or automatic merge are introduced.

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

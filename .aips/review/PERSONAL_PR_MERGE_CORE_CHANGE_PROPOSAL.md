# Core Change Proposal — Personal Mode Per-Merge Confirmation

Status: APPROVED BY HUMAN — 2026-10-11

## Problem and recommendation

Personal mode supports fast individual development, but its blanket PR-merge denial prevents an Agent from completing an explicitly requested PR merge. The user approved enabling personal-mode PR merges with confirmation before each merge and accepted Codex's advisory limitation.

Extend the existing publication authority and native hook adapters. Validate one explicit PR, the exact local candidate and PR head, the current allowlisted engineering branch, the live remote default base, mergeability and required checks. Claude Code returns native `PreToolUse` `ask` with the reviewed identifiers. Gemini CLI uses its extension Policy Engine `ask_user` rule in interactive `default`, `autoEdit`, and `yolo` modes, paired with the existing governance hook's PR/check summary. Keep Codex `ADVISORY` and document that it cannot guarantee interception of direct merge commands.

This is appropriate because the gap is an operation in the existing publication authority model, not a new role, capability, service, or gate. A server-side expected-head SHA pins the PR candidate. The observed base SHA is informational and can change between check and execution; GitHub's merge semantics and repository rules remain authoritative. Personal mode continues to trust the configured `origin`, with the previously accepted same-account rewrite limitation.

## Approved implementation boundary

- `scripts/publication_authority.py`
- `scripts/governance_guard.py`
- `SYSTEM_CORE.md`
- `harness/adapters/gemini-cli/policies/personal-pr-merge.toml`
- `harness/adapters/gemini-cli/GEMINI.md`
- `tests/test_publication_authority.py`
- `docs/human/DOCUMENTATION_MAP.md`
- `docs/human/DOCUMENTATION_SYNC.md`
- `docs/human/HARNESS.md`
- `docs/human/INSTALLATION.md`
- `docs/human/MAINTENANCE.md`
- `docs/human/index.md`
- `harness/HARNESS_PROTOCOL.md`
- `harness/adapters/opencode/AGENTS.md`
- `harness/adapters/opencode/COMPATIBILITY.md`
- `orchestration/CONFORMANCE.md`
- `orchestration/CREATIVE_DIRECTION.md`
- `orchestration/DETERMINISTIC_SCHEDULER.md`
- `orchestration/DOCUMENTATION_SYNC.md`
- `tests/scenarios/240-personal-publication-default.md`
- `tests/scenario_coverage.yaml`
- `config/documentation-placement.yaml`
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`
- `orchestration/ORCHESTRATOR.md`
- `docs/human/USER_GUIDE.md`
- `docs/human/CONFORMANCE.md`
- `docs/human/SECURITY_ASSURANCE.md`
- `docs/human/TECHNOLOGY_GUIDE.md`
- `docs/ARCHITECTURE.md`
- `docs/human/ARCHITECTURE_OVERVIEW.md`
- this proposal

Out of scope: changing high-assurance signed grants; promising atomic base-SHA compare-and-swap; introducing a new service; changing branch protection or GitHub permissions; claiming Codex enforcement; changing push, release, tag or protected-branch authorization.

## Compatibility and evidence required

No persisted schema or migration changes. Existing high-assurance merge grants and non-personal merge validation remain covered. Negative cases must deny draft/closed/unmergeable PRs, non-default base, mismatched head SHA or branch, unallowlisted branch, pending/failed/unavailable required checks, ambiguous commands, and admin/auto/delete flags. Positive tests must assert the exact confirmation binding and native Claude/Gemini controls, including Gemini's three interactive modes.

Run focused publication tests, changed-code lint, Scenario 240 and scenario registry checks, documentation placement and closure, repository validation if the local runtime is available, secret-scan lifecycle, and the exact-candidate Core Integration Gate. Review the actual diff against this boundary before publication. Impact traversal remains bounded; unresolved Impact Graph relations must be reported rather than treated as complete.

## Human and architecture impact

User Guide and Security Assurance define behavior and limitations. Orchestrator and Gemini adapter docs define enforcement routing. Scenario 240 and the Core Matrix bind executable evidence. The existing architecture topology is unchanged; no architecture diagram edit is required. This change does not modify Constitution semantics.

# System Improvement Review: Publication Readiness

## Trigger and evidence

The PR #186 retrospective found repeated friction in source-root selection, documentation validation, local Gate setup, GitHub CLI authentication and Change Impact traversal review. Evidence included a stale/global root being used for candidate inspection, a VitePress dead-link CI failure after publication, missing Ruff/loopback capability in the first local Gate attempt, unavailable `gh` authentication, a validation rerun after PR labeling, and traversal validation that named a missing disposition without explaining the allowed choices.

## Assessment

These are appropriate improvements to existing publication and Change Impact tools. The repository already has shared CLI wrappers, `publish_preflight.py`, `repository_preflight.py`, a CI docs-site build, explicit environment diagnostics, PR label planning and fail-closed traversal validation. Extending those surfaces is technically feasible and keeps the change small. No new role, skill, gate, approval authority or permanent intelligence relationship is needed.

## Decision

Implement explicit repository-root selection and reporting; fast Python/Ruff/loopback/browser checks before the full Gate; changed-Markdown local-link checks and an opt-in-to-local-publication VitePress build; actionable final-disposition errors; and an initial-request PR label instruction with clear `gh` authentication status. Keep remote merge and publication Human-authorized. Preserve strict unknown handling and do not infer traversal dispositions automatically.

## Review

- Maintainability: reuse the current CLI, repository preflight and publication plan.
- Compatibility: all new CLI arguments and plan fields are additive; the existing default repository root remains unchanged.
- Security/privacy: do not print credentials or raw authentication stderr; do not weaken secret scanning or Change Impact fail-closed behavior.
- Performance: run the docs-site build only for local publication candidates with documentation/package changes; fail before expensive Gate work when runtime prerequisites are missing.
- Constitution: no change to authority, approval, trust or merge semantics.

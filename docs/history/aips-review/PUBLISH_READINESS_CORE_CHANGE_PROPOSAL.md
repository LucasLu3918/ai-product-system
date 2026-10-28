# Core Change Proposal: Publication Readiness Hardening

## Problem

The PR #186 retrospective identified recurring publication friction: an implicit checkout root, a documentation dead link found only in remote CI, local Gate attempts made before required tools or loopback capability were known, unclear Change Impact disposition errors, and an extra CI run when a PR was labeled after creation.

## Proposed change

- Let `aips publish` and `aips integration-gate` accept `--project-root <repo>` and report the selected repository and Git roots in publication plans.
- Check Python, PyYAML, Ruff, localhost binding and browser launch before starting publication Gate work, with safe, actionable remediation.
- Check local links in changed Markdown and build VitePress during local publication when docs or package inputs changed.
- Explain allowed final Change Impact dispositions and how to resolve each blocking finding without auto-approving it.
- Keep the required Core/Large label in the first `gh pr create --label ...` request; report unavailable GitHub CLI authentication without exposing raw stderr.

## Boundaries and non-goals

No change to branch protection, secret scanning, Gate authority, human review/merge approval, CI cancellation policy or GitHub connector capabilities. Do not automatically classify Impact Graph nodes as safe. The retrieval index rebuild is operational project metadata and is not committed.

## Expected impact

- CLI input: additive `--project-root` option for publication and Integration Gate commands.
- CLI/report output: additive repository identity and runtime diagnostic fields.
- Documentation validation: changed Markdown local-link check; local VitePress build for documentation/package changes.
- Consumers: source-checkout maintainers, global CLI users validating another checkout, local publication workflow and GitHub PR authors.
- Persistence/migration: none.
- Security: credential output remains redacted; existing publication and Change Impact checks remain fail-closed.

## Verification

Run focused publication/Change Impact lifecycles, the complete repository validation, strict exact-candidate secret scan, local VitePress build, and the Core Change Integration Gate. Confirm a remote PR receives the classification label at creation when CLI auth permits; otherwise use the authorized GitHub publication route and verify the resulting checks before merge.

## Approval and recommendation

The user directly authorized implementing all previously recommended improvements, local verification, remote PR creation and merge into `main`. Implement within this boundary; no Constitution change or additional authority is requested.

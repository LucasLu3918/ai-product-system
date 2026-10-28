# Plan34 — Publication Diagnostics and Publish Doctor

Status: APPROVED BY HUMAN — 2026-10-12

## Problem and recommendation

Claude Code could not explain why a checked merge was rejected: an unset Required Checks policy, failing or pending checks, unavailable GitHub evidence, and unsupported command syntax collapsed into generic publication errors. The existing AIPS source already has a shared publication authority, read-only planner, CLI preflight, native runtime adapters, and Integration Gate. Extend those boundaries; do not add a second permission system, disable policy, or alter GitHub repository settings.

The user selected the complete Plan34 solution in the referenced conversation and explicitly requested implementation, local validation, a remote PR, and merge to `main`. This approval covers the scope below. Merge remains bound to the exact validated candidate and passing required checks.

## Approved implementation boundary

### In scope

- Give publication failures stable reason codes, phases, sanitized underlying categories, and concrete safe next steps; preserve redaction and avoid raw subprocess output.
- Classify Required Checks as unconfigured, passing, failing, pending, missing, cancelled, stale, or unavailable because GitHub access is insufficient. Empty/unavailable policy evidence remains blocking.
- Extend `aips publish diagnose` to inspect literal `gh pr merge` commands read-only, validate exact PR/head/base/method and live checks, and never execute or consume a grant.
- Add a read-only `aips publish doctor` for repository/GitHub configuration, auth visibility, merge methods, Required Checks policy, PR/head/check status, and actionable blockers. Reuse it for first-time repository onboarding; never modify branch protection or repository policy.
- Provide one machine-readable diagnostic shape and consistent instructions to Claude Code, OpenCode, and Codex. Agents may repeat safe read-only diagnosis and perform only fixes already authorized; admin changes, policy changes, bypass, and merges remain gated.
- Add Scenario 260, unit, lifecycle, CLI/contract, security regression evidence, and Traditional Chinese user guidance.
- Preserve all existing secret scan, Integration Gate, Human Authority, native confirmation, and exact-candidate controls.

### Out of scope

- Changing Required Checks, branch protection, rulesets, repository permissions, or merge settings on `lucas-lab` or any other repository.
- Admin/bypass merge, automatic policy weakening, hook disabling, credentials/token acquisition, or automatic changes that need an administrator.
- Changing Constitution semantics, signed-grant policy, storage schemas, or AIPS installed source files directly.
- Claiming Codex command interception; its existing publication enforcement remains advisory.

## Expected files / modules

- `scripts/publication_authority.py`, `scripts/publication_planning.py`, `scripts/publication_diagnostics.py`, `scripts/publish_preflight.py`
- `scripts/aips_cli/commands.sh`, `scripts/aips_cli/help.sh`
- Publication unit tests, read-only doctor lifecycle, validation contracts, Scenario 260 and scenario coverage
- Canonical Human/Agent documentation closure: Architecture, Architecture Overview, Conformance, Documentation Map/Sync, Harness, Installation, Maintenance, Security Assurance, Technology Guide, User Guide, Human index, Harness protocol and adapters, Orchestrator, Core Change Testing, Integration Gate, Creative Direction, Deterministic Scheduler, and this proposal
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`

## Impact

### Architecture / contracts

Additive CLI commands and fields to the shared diagnostic response. Publication authority remains the sole validator. The doctor and diagnose paths are observations only: `authorized: false`, no mutation invocations, no grants, and no changes to the execution boundary. No component topology change; architecture diagrams will document the existing preflight/publication path.

### Data / migration

No persisted runtime schema or migration. Doctor does not persist repository state.

### Security / reliability

Remote API failures, missing scopes, empty Required Checks, malformed responses, and stale SHA/base all fail closed with distinct safe codes. Raw credentials, exception strings, and unfiltered CLI output never enter diagnostics. Branch protection and ruleset remediation is guidance only and requires repository-admin authority.

### Compatibility / rollback

Existing `prepare`, `diagnose`, `checks`, and authority response fields remain compatible; new command and diagnostic fields are additive. No state migration. Reverting the single PR restores the previous behavior without changing remote repository policy.

### Tests / validation

Required: focused publication suites; deterministic lifecycle for doctor and merge diagnose; output/schema and native CLI contracts; negative cases for missing/failed/pending/cancelled checks, 403/404/API errors, stale SHA, raw-data redaction, no execution/grant consumption, and no policy mutation; docs placement/closure; credential-free exact-candidate secret scan; full repository validator and exact-candidate Core Integration Gate; live PR checks before merge.

Architecture diagram impact:
- `docs/ARCHITECTURE.md`: AFFECTED — explain read-only diagnose/doctor before the existing authority boundary.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: AFFECTED — show the same existing publication flow and no new authority component.
- Human SVG diagrams: N/A — no component topology or authority arrows change.

### Secret / credential impact

Secrets required: NO. Use the existing authenticated `gh` session only; never request or print tokens. Error redaction is part of the regression boundary.

## Risks

- GitHub protection/ruleset APIs can be permission-limited. Incomplete visibility must be `UNAVAILABLE`, never interpreted as no policy or success.
- CI status and policy may change after diagnosis. The native merge guard and server-side rules remain authoritative and must revalidate the exact SHA.
- The docs closure is broad (39 paths in the prospective impact report) because current AIPS placement/sync rules require those references; do not edit unrelated content.
- Global Project Intelligence graph coverage is partial; review direct callers and consumers and disclose that limit.

## Recommendation and order

Reuse existing publication authority and preflight abstractions. First build the shared safe diagnostic contract and exact Required Checks observation; then add read-only merge diagnose and Doctor/onboarding; integrate concise runtime guidance; add security/lifecycle tests and the required documentation closure; bind the final exact candidate to the Core Matrix and run the full local Gate before PR/merge.

## Approval

Status: APPROVED BY HUMAN
Approved by: user (referenced ChatGPT conversation and current explicit implementation request)
Approved at: 2026-10-12 Asia/Taipei
Approval record: Plan34 conversation `6acc6b0b-7f1c-83ee-9b05-47132cd577e2`, user selected Plan B and then requested all recommendations be implemented, locally validated, and merged via PR to `main`.

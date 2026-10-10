# Plan26 Phase 7 — Stable Release Candidate 0.81.0

## Purpose

Prepare the accumulated, already-merged Plan26 changes on `main` for exact-candidate stable release readiness. This change finalizes release metadata only: it sets the repository version to `0.81.0`, moves the current unreleased notes intact under that version, and leaves one empty `## Unreleased` heading.

## Proposed Scope

### In scope

- Set `VERSION` to `0.81.0`, following the repository SemVer policy.
- Move every existing note under `## Unreleased` without editing its wording into a new `## 0.81.0` section immediately below the empty Unreleased heading.
- Update this proposal and the Core Change Test Matrix to describe and bind the exact release-candidate diff.
- Complete the documentation closure required by `changelog-history-archive`: Architecture Overview, Documentation Map, Documentation Sync, Maintenance, Technology Guide, User Guide, Human index, and Agent Documentation Sync. Keep each update in its canonical topic.
- Run release metadata contracts, the exact-candidate version/tag readiness check, documentation validation, repository validation, secret scanning, and the required Core Integration Gate before PR publication.
- Open a PR against `main` and merge it only after required checks pass.

### Out of scope

- Creating, moving, or pushing a Git tag.
- Creating or publishing a GitHub Release.
- Changing runtime behavior, installation behavior, release policy, or prior changelog sections.
- Any other Plan26 workstream.

## Expected Files

- `.aips/review/PLAN26_PHASE7_STABLE_RELEASE_PROPOSAL.md`
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`
- `CHANGELOG.md`
- `VERSION`
- `docs/human/ARCHITECTURE_OVERVIEW.md`
- `docs/human/DOCUMENTATION_MAP.md`
- `docs/human/DOCUMENTATION_SYNC.md`
- `docs/human/MAINTENANCE.md`
- `docs/human/TECHNOLOGY_GUIDE.md`
- `docs/human/USER_GUIDE.md`
- `docs/human/index.md`
- `orchestration/DOCUMENTATION_SYNC.md`

## Impact and invariants

The inputs are the current `VERSION`, the top-level changelog sections, and the exact `main` base revision. Outputs are the version anchor and release notes consumed by the read-only release readiness workflow, installers, update guidance, and release policy tools. No runtime data, event, API, or schema changes are intended. The documentation impact preview requires eight canonical documentation updates for the changelog history rule; those updates record the finalized version/history boundary without duplicating the release notes. Direct consumers of `VERSION` and changelog readiness were manually reviewed; Project Intelligence has partial global consumer coverage, so no repository-wide completeness claim is made.

The canonical `## Unreleased` section remains first and empty. `VERSION` must equal the newest version heading. All existing unreleased notes are preserved exactly under `0.81.0`; historical sections stay untouched. Release readiness remains read-only and bound to an exact candidate SHA. This PR does not authorize tag or release creation.

## Impact-derived Test Matrix

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| Stable version and changelog metadata | REQUIRED | N/A — metadata-only | Repository validation and exact-candidate Core Integration Gate | Version/changelog contracts; exact candidate readiness must report the approved version and empty Unreleased | N/A — no user-facing runtime flow change | REQUIRED exact-candidate strict secret scan | N/A — no persisted user data or schema | N/A — no CLI/Harness behavior change | REQUIRED versioning and changelog documentation consistency | Metadata-only release candidate |

## Secret / credential impact

Secrets required: NO. Run the mandatory credential-free strict scan against the exact candidate. If a finding occurs, stop publication and follow the repository secret-handling policy.

## Verification and publication

Required local evidence: versioning contracts; version-policy contracts and lifecycle; full repository validation; complete recursive documentation sync and placement validation; exact-candidate strict secret scan; and Core Integration Gate. The Git Publish Approval Gate must pass for the exact PR candidate. Merge only after all required PR checks pass.

After merge, run read-only exact-candidate readiness as evidence. Do not create a tag or GitHub Release as part of this approved scope.

## Recompute triggers

Any change to runtime behavior, install/update policy, version policy, historical changelog content, or another Plan26 workstream expands this proposal and requires renewed impact and matrix reconciliation.

## Approval

Status: APPROVED
Approved by: User
Approved at: 2026-10-10
Approval record: User approved setting `VERSION` to `0.81.0`, moving the current Unreleased notes losslessly beneath that version while retaining one empty Unreleased section, updating the Proposal/Matrix, completing local verification, opening a PR, and merging it to `main`; after the documentation impact preview identified eight additional canonical documents, the user approved expanding this Phase 7 scope to complete that closure. Tag and GitHub Release creation are explicitly excluded.

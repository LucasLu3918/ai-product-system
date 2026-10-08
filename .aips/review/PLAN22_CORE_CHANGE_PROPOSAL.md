# Plan22 Core Change Proposal

## Purpose

Apply the evidence-backed Plan22 maintenance recommendations while preserving the existing Human approval, release, dependency, branch cleanup, and full-validation boundaries. The concrete code change corrects quarterly Evolution Radar scheduling so its rollup runs after monthly source reports have had time to publish.

## Why this is a Core Change

This candidate changes a scheduled governance workflow and its contract, lifecycle, scenario, and canonical documentation. It requires the active Impact-derived Core Change Test Matrix and the exact-candidate Integration Gate before publication.

## Approved scope

- Move the quarterly Evolution Radar scheduled run to day 3 at 11:00 Asia/Taipei, after monthly Radar and Effectiveness Issues can be published.
- Add deterministic schedule/mode assertions and preserve `INCOMPLETE_INPUT` when monthly evidence remains absent.
- Record evidence and dispositions for all 12 Plan22 recommendations; do not expand separate release, dependency merge, branch deletion, or selective-validation authority.

## Plan22 recommendation dispositions

1. **Release readiness:** `v0.74.0` is installed at the current main revision, but the release policy reports `BLOCKED` while `CHANGELOG.md` has content under `Unreleased`. No tag or release is part of this PR.
2. **CI validation efficiency:** existing exact-path provisioning and full-run Shadow Plan are active; `selective_execution_enabled` remains false. Recent main history is timing evidence only and does not meet the Shadow graduation cohort. Keep full PR and main validation.
3. **Evolution Radar effectiveness:** the September 2026 Effectiveness Issue reports 100 raw/unique signals, 0 shortlist, and 100 `ANALYSIS_PENDING`. Quarterly Issue #199 was created before the monthly source cohort was durable and reported 0 monthly evidence bundles. Schedule quarterly aggregation for day 3; do not change source policy or adoption thresholds.
4. **Quality debt:** preserve the existing Ruff non-increase ratchet, selected-module mypy check, and report-only coverage. The local report observed 702 findings; this candidate safely fixes four Evolution Radar contract findings plus one parity-contract import-order finding, reducing the report to 697 (505 auto-fixable, 192 manual). No repository-wide cleanup or new threshold is added.
5. **Large Python modules:** retain existing extracted facades and boundaries. The reviewed recommendation provides no call-graph or behavior evidence that an additional extraction is necessary for this maintenance candidate.
6. **Validation source parity:** retain distinct responsibilities of the CI provisioning plan, validator scope/shadow policy, Integration Gate profile, and ordered validator registry. Add a read-only contract that checks their shared fail-closed anchors and registry module existence; do not merge them into one policy or change validator execution.
7. **Branch lifecycle:** the read-only inventory covered 102 remote refs and produced no cleanup candidates. Branch deletion remains unauthorized and unperformed.
8. **Dependency maintenance:** seven open Dependabot PRs are behind `main` and have failing latest `janitor`/`repository` checks. Do not merge them without updated compatibility evidence.
9. **OpenCode native verification:** macOS native discovery is evidenced; Linux/WSL and model execution remain unverified in this host environment. Do not claim cross-platform support from projection tests.
10. **Cross-runtime governance:** retain the current capability registry and runtime invariant matrix as sources of truth. Advisory probes remain advisory; no host enforcement claim is upgraded.
11. **Context efficiency:** preserve the existing one-run validation timing baseline as an observation. Runtime/model token accounting is not exposed by the available official usage interface, so no token metric is inferred or persisted.
12. **Product/maintenance metrics:** reuse existing report-only Evolution Effectiveness, validation observation, and maintenance reliability streams. No new required gate or automatic tuning is added.

## Impact and compatibility

The workflow keeps existing permissions, report contents, manual dispatch modes, and deterministic rollup semantics. The only externally visible timing change is the quarterly report's scheduled publication day. If one or more expected monthly bundles are still missing, the existing pipeline health remains `INCOMPLETE_INPUT`.

No schema, credential, API, source policy, or stored-data migration is introduced. No project data or user configuration is modified.

## Validation

Run focused Evolution Radar contract and lifecycle checks, documentation synchronization checks, the full repository validator, exact-candidate Core Integration Gate, candidate-bound secret scan, PR checks, then verify post-merge main checks. All execution evidence is recorded in `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`.

## Approval

Status: APPROVED BY USER REQUEST

Approved by: User

Approved at: 2026-10-08 (Asia/Taipei)

Approval reference: User request to implement all Plan22 recommendations, followed by explicit `核准`.

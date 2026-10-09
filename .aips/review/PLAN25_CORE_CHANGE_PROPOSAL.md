# Plan25 Core Change Proposal

## Purpose

Complete all twelve plan25 recommendations through a staged set of reviewable PRs, focusing on verified gaps and extending current capabilities. Improve the evidence that AIPS works in supported environments and produces useful outcomes without weakening authority or validation.

## Why this is a core/large change

The work spans release and installer readiness, native Runtime boundaries, local creative execution, CI validation, quality policy, Evolution Radar, telemetry, branch governance and dependencies. These areas share workflows, schemas, tests, documentation and protected Human decisions. Each PR needs its own exact Change Impact reconciliation and candidate-bound matrix.

## Proposed scope

### In scope

All twelve areas from plan25, grouped as follows:

1. **PR 0 — Baseline and plan evidence:** freeze the verified `main` baseline and record current capability, evidence gaps, environment blockers and acceptance criteria in `.aips/review/PLAN25_BASELINE.yaml`, this proposal, the System Improvement Review and the active per-candidate Core Change Test Matrix after approval.
2. **PR 1 — Release, Runtime and recovery readiness (items 1, 2, 4, 11):** validate the exact stable-install readiness path without creating a tag; close version-bound native acceptance gaps for available supported hosts; verify Project Intelligence first-use/recovery guidance and Doctor consistency; preserve `ADVISORY` for unverified boundaries.
3. **PR 2 — Creative acceptance (item 3):** extend existing MFLUX/ComfyUI acceptance only for installed, already-compatible local engines. Separate command success, valid raster/provenance, real inference, visual review and user acceptance. No model download or paid/cloud provider.
4. **PR 3 — CI and maintainability (items 6, 7):** measure shadow-vs-full results and current quality hot spots; improve only where evidence supports it. Keep selective execution disabled, preserve graduation thresholds and run full validation for Core/release/unknown changes.
5. **PR 4 — Outcomes and observability (items 5, 8, 9):** use existing Evolution and telemetry contracts to report complete cohorts, measured latency and genuinely observed usage. Keep semantic adoption Human-controlled, telemetry export disabled by default, and unknown values explicit.
6. **PR 5 — Branch and dependency governance (items 10, 12):** improve report accuracy/actionability for exact-SHA branch and dependency candidates. Keep branch cleanup report-only and automatic dependency merge disabled.

For each item, a verified existing implementation may satisfy the recommendation without new code. No new parallel Doctor, Intelligence, governance engine, telemetry platform, source registry or CI gate is proposed.

### Out of scope

- Creating/publishing a version tag or GitHub Release; changing the default stable channel; production deployment.
- Merging the seven unrelated open Dependabot PRs, changing dependency policy, or writing branch-protection/ruleset settings.
- Deleting any remote branch or applying a cleanup manifest.
- Enabling validator skipping, weakening the required `repository` check, or lowering the 30-day/30-PR/zero-false-negative graduation policy.
- Downloading model weights, running paid/cloud inference, transmitting prompts/images, enabling external telemetry, inferring token usage/prices, or claiming visual quality without human review.
- Changing Constitution semantics or introducing new Roles, Skills, Capabilities, approval gates or governance planes.

## Expected files / modules

Likely owners include:

- Baseline/proposal/matrix: `.aips/review/PLAN25_*`, `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`.
- Release/runtime/diagnostics: `config/version-tag-policy.yaml`, `config/runtime-invariants.yaml`, `.github/workflows/release-readiness.yml`, existing runtime adapters, `scripts/project_diagnostics.py`, related scenarios and contracts.
- Creative: `scripts/creative_execution.py`, creative schemas/configuration, `tests/evidence/creative_execution_lifecycle.py`, relevant scenarios and canonical docs.
- CI/quality: `.github/workflows/validate.yml`, `config/validation-graduation.yaml`, `config/quality-ratchet.yaml`, existing validation planners and lifecycle contracts.
- Outcomes/observability: existing Evolution Radar workflows, `scripts/evolution_*`, `config/evolution-effectiveness.yaml`, `config/telemetry-export.yaml`, `scripts/telemetry_*`, schemas and lifecycle contracts.
- Branch/dependencies: `.github/workflows/branch-hygiene.yml`, `config/branch-lifecycle.yaml`, `config/branch-cleanup-manifest.yaml`, `config/dependency-policy.yaml` and their existing evidence/tests.
- Canonical documentation, scenario and projection inventories returned by the Documentation Impact Gate for each actual diff.

This is an expected module boundary, not authorization to change every listed file. The precise changed-file set is established by each PR's approved Change Impact and final diff.

## Impact

### Architecture / contracts

Preserve current owners, import/CLI facades, report shapes, runtime permission semantics and required CI consumers. Additive schema changes must be versioned. Do not upgrade `ADVISORY`, `NOT_VERIFIED`, `unknown` or report-only evidence to stronger claims without direct evidence.

### Data / migration

No user data migration is planned. Any new evidence artifact is bounded, versioned and recoverable; no prompt/image content or secret values are persisted.

### Security / reliability

Runtime, creative, CI, branch and dependency changes require negative-path tests. Keep required full validation, no-egress creative execution and current approval boundaries. Unknown paths and unsupported host versions fail closed where policy requires it.

### Compatibility / rollback

Preserve supported CLI and adapter contracts. Ship each capability boundary in a separate PR that can be reverted independently. No remote ref other than the authorized PR branch and, after candidate approval, its merge to `main` is changed.

### Impact-derived test matrix

Each PR receives a fresh exact-candidate matrix. Applicable evidence includes static/lint/type, focused lifecycle and contract tests, supported-host acceptance, security/secret scan, recovery/replay, documentation/schema checks, complete repository validation and the exact-candidate Integration Gate. Real image inference and visual review are reported separately; unavailable environments are `UNVERIFIED`, never synthetic PASS.

Recompute the matrix whenever actual scope or consumers expand. A missing complete Python 3.12 local Integration Gate environment blocks local completion until prepared through the repository's supported runtime setup.

### Required release / CI evidence

Every PR must pass the remote required `repository` aggregate for its exact head and base before merge. Core matrices and final secret scans must bind the exact candidate. Formal tag/release readiness remains a separate decision.

### Secret / credential impact

Secrets required: **NO**.

No credential acquisition or external data transmission is authorized by this proposal. Run strict credential-free final-tree and history scans. Telemetry remains local/opt-in and allowlisted.

### Documentation / diagrams

Run the Documentation Impact Gate per PR and update only canonical affected sections. Assess `docs/ARCHITECTURE.md`, `docs/human/ARCHITECTURE_OVERVIEW.md` and the applicable SVGs from actual behavior changes; mark N/A with reasons when topology is unchanged.

## Risks

- Existing functionality could be duplicated if each recommendation is treated as a request for a new feature.
- Host and model availability may prevent real acceptance; report this without acquiring/downloading dependencies.
- Existing open dependency PRs are currently behind or blocked with failed repository checks; they are not part of the approved candidates.
- The complete local Integration Gate cannot currently run because the required Python 3.12 environment is missing.
- A large program must remain split into the six reviewable PRs above; material scope drift requires renewed approval.

## Recommendation

Proceed with the six-PR staged program, beginning with PR 0 baseline/proposal artifacts. Continue to later PRs only within this approved boundary and after each phase's evidence is reconciled. Treat existing, already-satisfied recommendations as verified outcomes rather than adding duplicate implementations.

## Proposed implementation order

1. PR 0: commit the plan25 baseline, system improvement review, this proposal and the candidate-specific Core Test Matrix.
2. PR 1: release/runtime/Project Intelligence/Doctor evidence and remaining fixes.
3. PR 2: installed-local-engine creative acceptance.
4. PR 3: validation shadow/graduation evidence and measured quality work.
5. PR 4: Evolution outcomes, latency and privacy-limited observability.
6. PR 5: report-only branch hygiene and dependency-governance evidence.
7. Run final exact-candidate validation and prepare a separate Git Publish Proposal for each remote PR/merge operation.

## Approval

Status: APPROVED BY USER
Approved by: User
Approved at: 2026-10-09 (Asia/Taipei)
Approval record: Current task; user selected “12 項全做，分階段、多個 PR” and approved the six-phase Core Change scope.
Proposal fingerprint:
Scope fingerprint:

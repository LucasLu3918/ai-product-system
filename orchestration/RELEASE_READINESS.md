# Release Readiness

Use before promoting an exact release candidate to production.

## Purpose

Release Readiness is the consolidated production-readiness decision. It is not required merely to declare LOCAL_COMPLETE.

It answers:

> Is this exact candidate sufficiently built, tested, security-reviewed, recoverable and observable for this production environment?

## Inputs

Use applicable evidence from:

- PRODUCT.yaml;
- approved QUALITY_PROFILE.yaml;
- exact release candidate/version/commit;
- test/build/security evidence;
- migration/recovery evidence;
- staging evidence;
- observability/operations configuration.

## Required evidence

Assess only applicable items:

- all Deployment Units build;
- static/unit/integration/contract/E2E checks;
- Quality Profile production targets that must be verified before promotion;
- required Security Assurance evidence, including secret/credential leakage/handling evidence when applicable;
- migrations/recovery validated;
- infrastructure/configuration validated;
- staging verified when applicable;
- structured logs + health check available;
- required metrics/traces/dashboards/alerts available;
- required audit logging available;\n- when governance auditability is required by the affected SAL/change boundary, bind the exact candidate into the verifiable Governance Audit Chain;
- when long-lived/offline audit transfer is required, export a portable Governance Audit Bundle containing the exact candidate revision, retained chain anchor, applicable evidence digests and checkpoint public keys;\n- when audit evidence must remain discoverable across releases/deployments, register the verified bundle in the Governance Audit Catalog and evaluate the advisory retention policy;
- deployment/runbook/rollback documentation;
- unresolved blockers.

Use `templates/delivery/RELEASE_READINESS.yaml`.

## Status

- READY — all applicable production technical/readiness conditions satisfied.
- NOT_READY — evidence/work remains.
- BLOCKED — a release blocker exists.

READY never bypasses human/security/governance approval.

## Candidate integrity

Release, dependency and branch inventories remain evidence for Human review. They do not delete branches, merge unrelated PRs, create tags/releases or change protected refs; readiness applies only to the exact recorded candidate.

Creative candidates include the exact Core Matrix binding, local engine no-download evidence, job recovery checks and prompt-privacy review; real image quality remains outside deterministic release claims.

A Project Diagnostics PASS is not release evidence. Publication readiness still binds the exact candidate to the complete Integration Gate, documentation closure, security scan and required Human approval.

Creative reliability evidence separates versioned configuration/discovery, native callback/hook acceptance, raster container integrity and profile provenance from real-model quality. Unavailable local weights remain an explicit inference limitation; fixture PASS cannot close visual acceptance.

A creative execution candidate must bind its Core Matrix to the exact changed files and include no-egress, create-only preparation/output, provenance, and privacy trace evidence. Synthetic lifecycle success does not claim installed-engine inference, hardware performance or visual quality.

OpenCode v2.0.24 loopback evidence verifies Context delivery and native file Allow/Deny only for that host/version; it does not establish production-provider, V1/Linux, arbitrary Shell or MCP write safety.

OpenCode release evidence separates ownership-safe projection lifecycle from version-bound native runtime acceptance; unknown operating systems and provider behavior remain explicitly unverified.

Candidate path and digest helpers preserve existing output formats through compatibility facades; exact base/head binding and unresolved Impact Graph policy remain unchanged.

The repository governance snapshot can provide read-only ruleset and branch-protection evidence, but never changes GitHub settings or substitutes for Human release approval.

Plan17 regression evidence covers numeric diff headers, four browser/OpenAPI combinations, mandatory aggregates, reusable caller keys/permissions, explicit Python and isolated children, recursive placement, signed identity/immutable proposal rejection and atomic deletion races. Missing or malformed capability plans retain the full profile. A latest cancelled check stays INCOMPLETE; replaced old checks are reported as SUPERSEDED.

A Python CI candidate must use its declared requirements and tested constraints, import its declared modules, and pass `pip check` before readiness evidence is trusted.

The CLI module lifecycle is part of candidate validation for changes to the launcher, facade or sourced modules; it checks the source and installed-symlink routes without changing release or publication authority.

Readiness validates the exact `VERSION`, tag target and main candidate without creating a tag. Stable installation remains blocked until a trusted signed version tag exists; key enrollment and first-release approval are separate decisions.

Stable installations verify an immutable `vX.Y.Z` tag against its target commit and `VERSION`. This does not create a release: tag writing still requires the separate explicit release approval, and pre-release bootstrap uses `main` only while no stable tag exists.

Readiness applies to one exact release candidate/version/commit set. Material code/config/infra changes invalidate affected evidence.

Scheduled Python 3.12–3.14 compatibility evidence is a supplementary maintenance signal. Merge and release readiness still require the exact candidate's full Integration Gate on the supported primary Python 3.12 runtime.

Version-tag provenance is a separate read-only check implemented by `scripts/version_tag_policy.py` and `config/version-tag-policy.yaml`. It is ready only when the full candidate SHA exactly equals the current main SHA, any existing `vVERSION` tag points to that same commit, and `CHANGELOG.md` contains exactly one empty `## Unreleased` section. Missing, duplicate, malformed, or non-empty sections block the check. A mismatched existing tag blocks the check; historical tags are not backfilled. `READY_FOR_EXPLICIT_RELEASE_APPROVAL` is evidence for a separate explicit release decision and never writes, moves, or authorizes a tag.

## Post-deploy

After production promotion:

1. verify deployment status;
2. run health/smoke checks;
3. confirm critical user path where practical;
4. inspect logs/metrics/alerts for immediate regressions;
5. verify required SLO/business indicators when available;
6. rollback/roll-forward on failed verification;
7. persist PRODUCTION_VERIFIED state only after applicable checks pass.


## Audit retention readiness

A release gate may require proof that its audit bundle is registered and discoverable, but catalog/retention evidence cannot make an otherwise NOT_READY or BLOCKED release READY. A retention REVIEW_DUE state also does not authorize evidence deletion; any destructive action requires separate Human authority.

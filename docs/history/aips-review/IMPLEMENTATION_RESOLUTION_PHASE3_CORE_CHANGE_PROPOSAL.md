# Implementation Resolution Phase 3 Core Change Proposal

## Purpose and approved scope

Turn the Phase 1 Implementation Profile and Phase 2 OpenAPI evidence into scoped, reproducible checks for a specific Git candidate. The user approved the Phase 3 plan and requested implementation, local validation, PR publication and merge to `main` on 2026-10-02.

Implement ownership integrity, generation provenance, Profile and language fingerprints, required quality evidence, project-native command resolution, contract drift and deterministic report checks. Integrate an optional policy into the existing Integration Gate; do not create a parallel Gate.

## Contract and architecture

Add a versioned `enforcement` section to schema-v1 Profiles. A separate CLI validates changed paths, local provenance, command evidence and Phase 2 OpenAPI reports against the checked-out candidate. It emits a bounded, versioned report. The Integration Gate can require that report for a configured Profile and applicable changed paths. A missing policy leaves existing Gate behavior unchanged.

Explicit local command collection is opt-in. It runs a declared argv command with timeout and stores hashes/status rather than raw output. The Gate only verifies evidence; it does not execute candidate-supplied commands. Generated-file hashes establish record integrity, not proof that a generator produced the bytes. Contract-test operation coverage retains Phase 2's stated limits.

## Boundaries and non-goals

Affected inputs: Profile, selected language Profile, generated/source files, command declarations and reports, OpenAPI reports, Git base/head. Outputs: Phase 3 report and optional Gate check. No product database, event schema, deployed service or migration is involved.

No code generator, framework adapter, API breaking-change approval, automatic architecture change, global enforcement for projects without a Profile, new Role, Skill, Capability, approval gate or constitutional amendment.

## Safety and compatibility

Reject traversal and symlink escapes. Unknown ownership is protected. A required check with missing, stale or failed evidence cannot pass. Keep old Profiles and Gate configurations readable. Candidate Profile changes require an explicit Gate fingerprint update if a project pins the Profile. Human review remains authoritative for semantics and breaking changes.

## Implementation order

1. Add the additive Profile contract and bounded report schema.
2. Implement deterministic inspection and explicit argv-only command evidence collection.
3. Add optional Integration Gate enforcement for configured candidate paths.
4. Add positive/negative lifecycle and Scenario coverage, then update Human/Agent docs and architecture.
5. Reconcile the final Change Impact and Core Change Test Matrix; run local full Gate and PR CI before merge.

## Required verification

Static checks, Profile/Gate contracts, generated and quality evidence lifecycle, command security/timeout cases, Phase 2 OpenAPI regression, Scenario Conformance, repository validation, documentation build, exact-candidate Integration Gate, secret scan and remote PR checks. A new or materially enlarged boundary requires renewed review and matrix recomputation.

## Approval

Status: APPROVED for the scope above. The 2026-10-02 user request explicitly authorizes implementation and remote PR merge after local verification. Constitution impact: NO.

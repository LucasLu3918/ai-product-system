# Implementation Resolution Phase 2 System Improvement Review

**Appropriateness:** Appropriate. Phase 1 defines contract authority and evidence states but intentionally does not validate OpenAPI specifications, compare contract revisions, check implementation behavior, or bind verification to exact source revisions.

**User problem:** Make REST/OpenAPI planning evidence executable and repeatable so invalid specifications, compatibility changes, contract-test outcomes, and stale evidence are visible before implementation/publication.

**Proposed solution:** Extend the existing Implementation Resolution profile and deterministic validation surfaces. Use a pinned OpenAPI validator, a conservative compatibility analyzer, executable contract/conformance evidence checks, and content/revision provenance.

**Existing coverage:** Phase 1 authority states, profile structure, provenance fields, quality evidence, local project commands, Scenario 193, existing Integration Gate, and Core Change Test Matrix.

**Reuse / extension candidates:** `scripts/implementation_profile_validate.py`, the existing profile template, project-native test commands, lifecycle evidence conventions, Integration Gate, and existing Backend Engineer/REST API guidance.

**Lower-layer alternative:** Per-project test commands remain authoritative for executing application behavior. AIPS adds only reusable specification analysis, evidence normalization, and report binding; it does not add a universal framework adapter.

**Context / token cost:** Load checks only for REST/OpenAPI changes. The report is deterministic and bounded; no model call or repository-wide framework scan is added.

**Security / reliability:** Parse local inputs without network access, confine local references to the repository/spec root, reject unsafe/unresolved references, pin validator dependencies, and report unsupported compatibility cases as `UNKNOWN`/`BLOCKED` instead of PASS.

**Backward compatibility:** Additive Profile/report fields and an optional task-scoped CLI. Existing projects keep their own test commands. No persisted product data or migrations.

**Scenario / test impact:** Add positive and negative OAS fixtures, compatibility classification cases, contract fixture checks, conformance evidence lifecycle, stale revision/hash rejection, and unavailable-tool behavior. Keep semantic Agent recommendation quality under Human review.

**Human docs impact:** Update the Implementation Resolution guidance, User Guide, Conformance inventory and release notes.

**Agent docs impact:** Update the resolution protocol and planning/quality evidence handoff where needed; retain existing roles and Skills.

**Architecture diagram impact:** YES. Extend the Implementation Resolution flow after profile creation with spec validation, compatibility, project contract tests and evidence binding; do not change deployment topology.

**Constitution impact: NO.** Human authority, contract approval, merge authority and protected boundaries do not change.

**Recommended AIPS solution:** A bounded, deterministic REST/OpenAPI evidence layer for OpenAPI 3.0, 3.1 and 3.2. Unsupported semantics remain explicit unknowns. Use the maintained `openapi-spec-validator` package for specification validity; keep compatibility severity conservative and require project/Human policy for breaking changes.

**Additional optimization candidates:** Automatic ownership/drift enforcement remains Phase 3; code generation remains Phase 4; GraphQL/gRPC/AsyncAPI and framework adapters remain deferred.

**Expected scope:** Core proposal `.aips/review/IMPLEMENTATION_RESOLUTION_PHASE2_CORE_CHANGE_PROPOSAL.md`; CLI/library and fixtures; pinned validation dependency; Profile/report schema; lifecycle and Scenario coverage; architecture/Human documentation; validation matrix and changelog/version metadata.

**Risks:** Compatibility classification can overstate certainty; mitigate with conservative severity and `UNKNOWN`. Runtime evidence can be stale or self-reported; bind it to immutable hashes/revisions, record executed argv/exit status, and never claim the evidence format alone proves application semantics.

# Implementation Resolution Phase 2 Core Change Proposal

## Purpose

Extend the Phase 1 REST/OpenAPI Implementation Resolution foundation with deterministic specification validity, compatibility analysis, project-executed contract/conformance tests, and exact evidence provenance.

## Why this is a core/large change

It changes the API-contract quality lifecycle and evidence consumed by planning, implementation, review, CI, and publication. False PASS or stale evidence could mislead downstream implementation and merge decisions.

## Proposed Scope

### In scope

- Validate OpenAPI 3.0, 3.1 and 3.2 specifications with a pinned validator; report actionable source locations and distinguish invalid, unsupported, unavailable and valid inputs.
- Permit internal and repository-local references only when they resolve within the permitted root; reject network references, path traversal and unresolved references without making network requests.
- Compare a candidate specification with an explicitly selected approved baseline. Classify known consumer-breaking changes as `BREAKING`, known compatible changes as `NON_BREAKING`, and ambiguous/unsupported changes as `UNKNOWN`; never infer baseline authority from file presence or version strings.
- Execute project-native contract/conformance commands as argv (no shell); capture command, exit status, bounded output digest, runtime, timestamps, test-result evidence, exact contract/content hashes and Git revision.
- Validate conformance result shape and require every declared operation/test case to have an honest status; missing, failed, stale, unsupported or unavailable evidence cannot become PASS.
- Add deterministic lifecycle, fixture and regression coverage; integrate applicable validation into the existing repository checks and document task-level use.

### Out of scope

- Enforcing ownership/generated drift or adding mandatory global quality gates (Phase 3).
- Generating or rewriting application code/clients (Phase 4).
- Framework-specific route introspection/adapters, automatic contract authority selection, approving breaking changes, migrations, framework modernization, GraphQL, gRPC or AsyncAPI.
- Claiming that a static evidence manifest proves runtime behavior without an executed project-native command.

## Expected Files / Modules

- `scripts/openapi_contracts.py` (or the existing canonical implementation-profile validator module if repo conventions favor one entrypoint).
- `requirements-validation.txt` with a pinned OpenAPI specification validator.
- `templates/implementation/IMPLEMENTATION_PROFILE.yaml` and the versioned OpenAPI evidence report JSON Schema.
- `tests/fixtures/`, `tests/validation/`, `tests/evidence/`, `tests/scenarios/` and conformance registries.
- `orchestration/IMPLEMENTATION_RESOLUTION.md`, Human User Guide, Conformance, `docs/ARCHITECTURE.md`, architecture overview and applicable diagram.
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`, this proposal/review, `CHANGELOG.md`, `VERSION`.

## Impact

### Architecture / Contracts

Adds deterministic REST/OpenAPI checks after Implementation Profile assembly and before implementation/review. Evidence remains advisory input; existing Human authority and Integration Gate remain authoritative.

### Data / Migration

No product-data migration. New report artifacts are versioned, content-addressed, repository/run-local evidence. Existing Phase 1 Profile remains readable; new fields are additive.

### Security / Reliability

No network dereference; safe local-reference boundary; argv-only command execution with timeout and bounded output; hash and revision binding; fail-closed stale/unknown evidence; never store secrets or full unbounded command output.

### Compatibility / Rollback

Additive workflow and pinned optional validation dependency. Revert this change to remove Phase 2 commands and reports; Phase 1 remains usable. No automatic mutation of external project files.

### Tests / Validation

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| OpenAPI validity and local references | required | required | required | required | N/A | required | N/A | required | required | No deployed UI/service or product data migration |
| Compatibility classifier | required | required | required | required | N/A | required | N/A | required | required | Same reason |
| Contract/conformance execution evidence | required | required | required | required | N/A | required | N/A | required | required | Project-native commands execute in temporary fixtures |
| Profile/report provenance | required | required | required | required | N/A | required | N/A | required | required | Evidence artifacts only; no persistent application store |
| Docs and repository integration | required | required | required | required | N/A | required | N/A | required | required | No UI/deployment boundary |

Recompute trigger if scope expands: any framework adapter, external reference fetching, gate-enforced ownership/drift, generated application code, persistent product storage, new API surface, or additional protocol.

Required release/CI evidence: targeted lifecycle tests, repository validation, documentation/link/build checks, OpenAPI validator version and exact test output, strict candidate secret scan, exact-candidate Integration Gate, reviewed Impact reconciliation, and PR CI green.

### Secret / Credential Impact

Secrets required: **NO**

Approved acquisition mechanism: **N/A**

Leakage/redaction review: Commands and output are bounded; do not persist environment values or raw secret findings.

Rotation/revocation plan if exposure is found: **N/A**

### Documentation / Diagrams

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` Mermaid: **AFFECTED** — extend the Implementation Resolution flow with deterministic OpenAPI checks and evidence binding.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: **AFFECTED** — update the matching workflow description if present.
- Human SVG architecture/lifecycle diagrams: **N/A** — existing diagrams do not depict the Implementation Resolution subflow; the detailed Mermaid flow and Human architecture description are the affected artifacts.

`docs/human/assets/system-overview.svg`: **N/A** — it is a high-level routing/governance overview and does not diagram the Implementation Resolution subflow. The detailed source-controlled flow in `docs/ARCHITECTURE.md` and its Human description are updated instead.

## Risks

- Compatibility heuristics may be incomplete; unknown cases remain UNKNOWN and block automated PASS.
- Local references can escape the repository if paths are not normalized; deny traversal and symlink escapes.
- Project commands can be non-deterministic or emit secrets; use argv, timeout, bounded digest-only output and explicit UNVERIFIED states.
- Existing CI environments may not install the validator; dependency installation and missing-tool failure need explicit lifecycle coverage.

## Recommendation

Proceed with the bounded REST/OpenAPI Phase 2 scope above, reusing existing Project Intelligence, profile, project-native commands, validation and publication gates.

## Proposed Implementation Order

1. Add exact impact and test-matrix artifacts; pin validator and define report contracts.
2. Implement safe OpenAPI input/reference loading and validity reporting.
3. Implement conservative baseline diff and compatibility classification.
4. Implement argv-only project test execution and conformance evidence validation/binding.
5. Add fixtures, lifecycle/scenario tests and repository validation wiring.
6. Update profile, agent/human docs, architecture, changelog/version, then run impact reconciliation and full Core validation.

## Approval

Status: APPROVED
Approved by: Human (user)
Approved at: 2026-09-30T09:21:18Z
Approval record: User explicitly instructed implementation of all items from the immediately preceding Phase 2 recommendation, including local validation and remote PR merge.
Proposal fingerprint: generated after final proposal content review
Scope fingerprint: generated after final Change Boundary review

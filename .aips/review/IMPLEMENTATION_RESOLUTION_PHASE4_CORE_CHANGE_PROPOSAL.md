# Implementation Resolution Phase 4 Core Change Proposal

## Why this is a core change

Phase 4 adds controlled execution of project-owned code generators and can write generated client files. It crosses Profile, filesystem, process execution, ownership, evidence, Gate, docs and test boundaries.

## Approved scope

### In scope

- Add an optional, disabled-by-default OpenAPI client generator adapter declaration to the Implementation Profile.
- Add a CLI that validates the declaration and canonical local OpenAPI evidence; uses an explicitly named repository-local executable and argv without a shell; requires `--execute` for generation; stages output outside the target; enforces bounded runtime/output, path and symlink checks; verifies reproducibility when requested; refuses overwrites unless existing outputs are declared generated and Phase 3 hashes match; applies output only by a same-filesystem directory swap with rollback.
- Emit a versioned report binding generator executable, declared tool inputs, canonical spec, config, Git revision, generated file hashes and result. Never persist raw output.
- Add deterministic fixture, positive/negative lifecycle and structural contracts, Scenario 196, existing Integration Gate test registration, docs and version/changelog updates.
- Keep legacy Profiles compatible and generation disabled by default. Integration Gate verifies evidence only; it never runs a generator.

### Out of scope

- Selecting or bundling a production generator for AIPS; this repository has no product OpenAPI spec/client.
- Server-side stubs, business logic, migrations, GraphQL, gRPC, AsyncAPI, remote fetching, generator plugins/hooks or automatic framework changes.
- New Role, Skill, Capability, global Gate, approval system or Constitution change.

## Expected files

- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`
- `.aips/review/IMPLEMENTATION_RESOLUTION_PHASE4_CORE_CHANGE_PROPOSAL.md`
- `.aips/review/IMPLEMENTATION_RESOLUTION_PHASE4_SYSTEM_IMPROVEMENT_REVIEW.md`
- `CHANGELOG.md`
- `VERSION`
- `config/documentation-placement.yaml`
- `config/integration-gate.yaml`
- `docs/ARCHITECTURE.md`
- `docs/human/ARCHITECTURE_OVERVIEW.md`
- `docs/human/CONFORMANCE.md`
- `docs/human/DOCUMENTATION_MAP.md`
- `docs/human/DOCUMENTATION_SYNC.md`
- `docs/human/MAINTENANCE.md`
- `docs/human/SECURITY_ASSURANCE.md`
- `docs/human/TECHNOLOGY_GUIDE.md`
- `docs/human/USER_GUIDE.md`
- `orchestration/CONFORMANCE.md`
- `orchestration/CORE_CHANGE_TESTING.md`
- `orchestration/DOCUMENTATION_SYNC.md`
- `orchestration/IMPLEMENTATION_RESOLUTION.md`
- `orchestration/INTEGRATION_GATE.md`
- `scripts/implementation_profile_validate.py`
- `scripts/openapi_generator_adapter.py`
- `templates/implementation/GENERATOR_ADAPTER_REPORT.schema.json`
- `templates/implementation/IMPLEMENTATION_PROFILE.yaml`
- `tests/evidence/openapi_generator_adapter_lifecycle.py`
- `tests/scenario_coverage.yaml`
- `tests/scenarios/196-openapi-generator-adapter.md`
- `tests/validate_repository.py`
- `tests/validation/implementation_profile_contracts.py`
- `tests/validation/openapi_generator_adapter_contracts.py`

## Impact and validation

- **Architecture/contracts:** additive optional Profile section; one bounded adapter and report schema; existing Gate remains read-only.
- **Security/recovery:** `--execute`, argv only, repo-local pinned executable/input hashes, temp staging, output allowlist, size/count/time caps, generated ownership/hash checks and rollback on apply failure.
- **Compatibility:** old Profiles without adapter configuration remain valid; disabled means no execution.
- **Tests:** structural/profile compatibility, fixture integration, hostile paths/output, stale tool/spec/input, repeatability, overwrite protection and rollback. Run repository validation and exact-candidate Integration Gate.
- **Docs/diagrams:** update existing Implementation Resolution flow and scoped human/agent guidance; no deployment diagram change.

## Approval

Status: APPROVED
Approved by: Human (explicit request to implement the Phase 4 plan, validate locally, and merge the remote PR to main)
Approved at: 2026-10-02
Approval record: current user message, “請幫我依照建議實作所有事項，本地驗證完後需完成遠端pr合至main”

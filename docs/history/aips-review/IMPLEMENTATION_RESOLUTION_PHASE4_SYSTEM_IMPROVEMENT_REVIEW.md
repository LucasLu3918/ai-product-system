# Implementation Resolution Phase 4 System Improvement Review

**Appropriateness:** Conditionally appropriate. The repository already resolves OpenAPI contracts and verifies generated-file hashes, but has no safe, reusable way to stage a project-owned transport/client generator and inspect/materialize its output.

**User problem:** Phase 3 can detect that generated files or inputs drift, but does not run or isolate a generator. Projects that explicitly choose client generation still need a bounded process to preview, run, validate and apply its output.

**Proposed solution:** Extend the existing Implementation Profile with an optional OpenAPI client adapter declaration and add one CLI adapter that uses an explicitly configured repository-local executable, argv, input hashes and output allowlist. Execute only after `--execute`; generate in a temporary sibling directory; verify tool/input identity, reproducibility when declared, paths, symlinks, output size/count and ownership before atomic directory swap. Produce a versioned evidence report. Keep Integration Gate inspection-only.

**Existing coverage:** Phase 2 validates/compares OpenAPI and contract-test evidence. Phase 3 binds generated output/input hashes and checks ownership, but correctly does not claim a generator ran. No production spec, generator, or generated client is present in this repository.

**Reuse / extension candidates:** Existing Implementation Profile/template validator, `scripts/openapi_contracts.py`, Phase 3 generation records, Integration Gate lifecycle registry, and report schemas. No new Role, Skill, Capability or Gate is warranted.

**Lower-layer alternative:** A project can invoke its generator directly. AIPS adds value only for portable allowlist, isolation, ownership and evidence handling. Therefore this implementation provides a generic OpenAPI CLI adapter contract and deterministic fixture, not a bundled generator or guessed product-specific integration.

**Context / token cost:** On-demand for profiles that declare a generator adapter; legacy profiles remain unchanged.

**Security / reliability:** Never execute from Integration Gate. Reject shell command forms, absolute/traversing paths, remote OpenAPI references, symlink outputs, undeclared files, oversized output, stale input/tool hashes and overwritten files that are not already generated and hash-verified. Stage all output before writing. Keep raw generator output out of reports. Human review retains contract and merge authority.

**Backward compatibility:** Additive optional Profile field; generation remains disabled by default. Existing Phase 1–3 profiles and Gate profiles continue to validate.

**Scenario / test impact:** Add deterministic fixture coverage for dry inspection, explicit execution, repeatability, stale hashes, unexpected files, path traversal, symlink output, hand-edited output refusal, atomic rollback and legacy profile behavior.

**Human docs impact:** Update user, security, maintenance, technology, architecture and conformance guidance.

**Agent docs impact:** Update Implementation Resolution, Integration Gate, Documentation Sync and Core Change Testing.

**Architecture diagram impact:** Update the existing Implementation Resolution evidence flow; no deployment topology or Human SVG lifecycle change.

**Constitution impact:** NO. No Human authority, contract approval, protected ownership or Git authority changes.

**Recommended AIPS solution:** One generic, local OpenAPI client CLI adapter that projects may configure for their own pinned generator. The first repository test uses a deterministic fixture because AIPS itself has no production API client target. Specific generators and languages remain later, evidence-driven integrations.

**Additional optimization candidates:** Tool-specific adapters (Kiota, OpenAPI Generator, oapi-codegen), remote generator resolution, server stubs, GraphQL/gRPC/AsyncAPI, automatic migrations and framework modernization remain LATER or out of scope.

**Expected scope:** The 31 paths in the Phase 4 Core Change Proposal, centered on the optional Profile field, bounded CLI adapter, report schema, fixture/lifecycle, Scenario 196 and aligned documentation.

**Risks:** A project-local executable is code execution with the invoking user's permissions; explicit execution is required, and the report must not claim OS-level sandboxing. Generator correctness and generated client semantic quality remain review/test responsibilities.

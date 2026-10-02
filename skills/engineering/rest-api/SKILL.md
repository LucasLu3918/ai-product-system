---
id: rest-api
capability: engineering
estimated_context_cost: low
---

# Rest Api

Inspect the existing API contract first. Preserve compatibility unless change is approved. For planning, derive each operation from a consumer need and domain behavior, then specify stable `OP-NNN` ID, requirement references, authorization, request/response, validation, errors, pagination/filtering, concurrency, idempotency, retry behavior, compatibility and observability.

Use a machine-readable contract when it improves consumer validation. Choose OpenAPI for useful HTTP contracts and AsyncAPI or an equivalent for event/message contracts. Resolve specification version against the target toolchain; do not hard-code a version in AIPS Core. A structural API contract does not establish security or architecture quality. Project contracts and scoped instructions outrank this generic Skill.

For REST/OpenAPI implementation, resolve contract authority before changing behavior: `canonical`, `descriptive`, `proposed`, or `unresolved`. Existing-project specs are not automatically canonical. Compare the approved contract with implementation, tests and available runtime evidence; classify drift instead of silently normalizing it. An unresolved authority blocks contract-affecting implementation, and canonical status does not authorize an unapproved breaking change. Keep transport DTOs separate from domain models unless the project architecture explicitly says otherwise. Follow the Implementation Profile and protect files whose ownership is generated or unresolved.

When OpenAPI evidence is needed, use `scripts/openapi_contracts.py` with dependencies from `requirements-openapi.txt`. Validate offline with repository-confined local references; compare compatibility only against a declared canonical baseline; run the project-native contract test command as argv and bind its JUnit operation coverage, spec/report digests and Git revision. Treat unknown changes, stale evidence and unavailable tests as non-PASS, and do not infer assertion quality from operation-name coverage.

When the Implementation Profile enables Phase 3, keep each changed API path within its declared ownership scope, preserve generated-file provenance and provide fresh quality/contract evidence for the exact candidate. Run declared project commands explicitly; the Integration Gate inspects their reports and does not execute them. A matching generated hash does not authorize an edit to an unresolved boundary or decide API business behavior.

Phase 4 client generation is optional and requires a canonical OpenAPI source plus current validation evidence. Preview the configured local adapter before execution; only an explicit Human `--execute` runs its pinned repository-local tool. Review generated diffs and run project-native compile, contract and integration tests. The Integration Gate never executes the Profile generator, and adapter hashes do not prove semantic correctness or OS-level isolation.

When `enforcement.generator_reports` is configured, retain the untracked Phase 4 report and let Phase 3 verify it against the exact Profile, inputs, outputs and candidate history. Use the shared Widgets reference pilot to understand the workflow; each real product still requires its own service-level success, error, serialization and authorization checks.

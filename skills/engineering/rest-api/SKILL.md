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

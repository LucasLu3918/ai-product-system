---
id: rest-api
capability: engineering
estimated_context_cost: low
---

# Rest Api

Inspect the existing API contract first. Preserve compatibility unless change is approved. For planning, derive each operation from a consumer need and domain behavior, then specify stable `OP-NNN` ID, requirement references, authorization, request/response, validation, errors, pagination/filtering, concurrency, idempotency, retry behavior, compatibility and observability.

Use a machine-readable contract when it improves consumer validation. Choose OpenAPI for useful HTTP contracts and AsyncAPI or an equivalent for event/message contracts. Resolve specification version against the target toolchain; do not hard-code a version in AIPS Core. A structural API contract does not establish security or architecture quality. Project contracts and scoped instructions outrank this generic Skill.

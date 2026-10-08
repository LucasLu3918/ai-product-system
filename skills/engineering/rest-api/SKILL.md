---
id: rest-api
description: Design and implement REST APIs with contracts, validation, error behavior, authorization
  and project-native tests.
capability: engineering
estimated_context_cost: low
triggers:
- rest_api_change
- endpoint_design
model_requirements:
  reasoning: medium
  coding: strong
  reliability: high
  minimum_tier: 2
  preferred_tier: 2
---

# REST API

Inspect the existing API contract and consumer needs first. Project contracts, scoped instructions and the approved Implementation Profile take precedence.

## Semantic checks

- Derive operations from domain behavior and consumer needs; use stable `OP-NNN` IDs and requirement references when planning.
- Specify request/response shapes, validation, authorization, errors, pagination/filtering, state transitions, concurrency, idempotency, retry behavior and observability.
- Preserve compatibility unless a breaking change is explicitly approved. Compare implementation, tests and runtime evidence with the approved contract; classify drift instead of silently normalizing it.
- Resolve contract authority as `canonical`, `descriptive`, `proposed` or `unresolved`. Existing specs are not automatically canonical; unresolved authority blocks contract-affecting implementation. Canonical status does not authorize a breaking change.
- Keep transport DTOs separate from domain models unless project architecture explicitly permits sharing. Protect generated or unresolved ownership boundaries.
- Choose a machine-readable contract when useful: OpenAPI for HTTP, AsyncAPI or an equivalent for events. Resolve specification version against the target toolchain rather than fixing a version in AIPS Core. Structural validity does not prove security or semantic correctness.

## On-demand implementation protocol

Load `orchestration/IMPLEMENTATION_RESOLUTION.md` when OpenAPI validation/compatibility, contract-test evidence, Phase 3 ownership enforcement or optional Phase 4 client generation is needed. It owns tool invocation, report freshness, generated-file provenance and Integration Gate inspection. Project-native tests verify service success/error, serialization and authorization behavior. The Gate never runs a project generator; explicit Human execution authority remains required.

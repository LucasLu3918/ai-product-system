# Scenario 197 — Shared OpenAPI client reference pilot

## Given

- A standalone reference product has a canonical Widgets OpenAPI contract, a
  repository-local generator, a local API service and a product-owned consumer.
- Its Profile opts in to Phase 3 verification of an ephemeral Phase 4 run report.

## When

- The local lifecycle validates the contract, previews and explicitly runs the
  generator, commits the client, and tests it against the local service.

## Then

- Create and get operations, Unicode JSON, invalid input, missing resources and
  bearer authorization behave as the project tests declare.
- Phase 3 checks the generated output and its inputs, ownership, quality command,
  OpenAPI evidence and generator run report without executing the generator.
- A missing or tampered report blocks only this opt-in Profile; legacy Profiles
  without `generator_reports` retain their existing behavior.
- The AIPS example remains shared; product-specific evidence stays in each
  product repository.

## Evidence

- `examples/openapi-client-pilot/README.md`
- `tests/evidence/openapi_client_pilot_lifecycle.py`
- `tests/evidence/implementation_enforcement_lifecycle.py`

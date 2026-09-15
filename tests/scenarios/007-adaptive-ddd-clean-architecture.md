# Scenario 007 — Adaptive DDD + Clean Architecture

## Request

> Add a simple optional `nickname` field to an existing REST API in a small CRUD service.

## Expected routing

- Work Mode: Engineering Change
- Project State: Brownfield
- Inspect existing architecture first.
- Do **not** introduce bounded contexts, aggregates, repository abstractions or a repository-wide Clean Architecture rewrite solely for this change.
- Load only the language/API/testing skills needed by the affected path.
- Apply TDD when the behavior is testable.

## Contrast case

If the request instead changes ordering, payment, inventory reservation and refund rules across multiple domains, architecture preflight should recommend tactical/strategic DDD as appropriate and stop for a human decision when the proposed boundary changes are material.

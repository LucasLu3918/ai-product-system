# Scenario 193 — Evidence-driven Implementation Resolution

## Purpose

Resolve the implementation rules for REST/OpenAPI work in existing and new projects while preserving project conventions, Human decision authority, code ownership, and honest verification states.

## Representative cases

`tests/fixtures/implementation_resolution_scenarios.yaml` defines 16 cases spanning existing Go/PHP/Python/.NET projects; new-project technology and architecture selection; contract authority; generated/unknown ownership; conflicting evidence; `not_detected` versus `none`; version-specific knowledge gaps; and unavailable verification.

## Expected behavior

- Existing-project evidence and local examples guide additions; sparse evidence does not become a repository-wide rule.
- New-project recommendations explain constraints and trade-offs and await Human confirmation.
- Contract authority is explicit. Unresolved authority blocks contract-affecting work; drift is not silently normalized.
- Architecture signals include counter-signals. Clean Architecture, DDD, and deployment choices remain independent.
- Unknown ownership is protected, generated and project-owned paths cannot overlap, and generators do not make business decisions.
- Every resolved conclusion has provenance. `not_detected` is not `none`; unavailable verification is `UNVERIFIED`.
- Structural validation reports representation and readiness only; it does not claim that a technology or architecture recommendation is semantically correct.

## Coverage

The deterministic validator and lifecycle evidence exercise profile structure, provenance, ownership conflicts, blocking states and all four language profiles. Agent recommendation quality across the 16 contextual cases requires semantic Human review, so this Scenario remains `manual` until recorded agent output is evaluated with appropriate observable-result evidence.

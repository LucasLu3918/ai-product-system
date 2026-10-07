# Scenario 226 — Capability Registry Single Source

## Request

Add or update a capability and regenerate both legacy indexes without changing their v1 consumer contracts.

## Expected

- `config/capability-registry.yaml` owns capability identity, maturity, runtime-support truth, documentation and validation evidence, plus architecture-surface membership.
- `scripts/capability_registry.py check` is read-only and detects a stale Capability Map or architecture-surface projection.
- `generate` is deterministic, preserves both legacy v1 shapes, rejects duplicate IDs, unknown/duplicate assignments, missing references and paths that escape the repository.
- Repository Health binds the canonical registry and detects projection drift plus unmapped discovered major subsystem scripts.
- Runtime support remains `NOT_ASSESSED` when repository tests do not prove behavior in the named runtime.

## Evidence

`tests/validation/repository_health_contracts.py` checks the candidate projections and the Repository Health digest binding. `tests/evidence/repository_health_lifecycle.py` checks deterministic audits, legacy mode, inventory drift and orphan-surface discovery.

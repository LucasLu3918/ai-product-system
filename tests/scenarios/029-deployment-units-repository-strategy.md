# Scenario 029 — Deployment Units vs Repository Strategy

Request: product has a frontend and backend.

Expected:
- model frontend/backend as separate Deployment Units with independent build/test/deploy behavior;
- do not automatically create two Git repositories;
- prefer a monorepo when coordinated contracts, docs, E2E and local development benefit;
- recommend multi-repo only with evidence such as distinct ownership, permissions, release cadence, scale or shared-service boundaries;
- record the selected strategy and unit paths/repositories in PRODUCT.yaml.

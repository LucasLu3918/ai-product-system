# 175. Risk-adaptive bounded change impact

## Scenario

When an agent changes an existing project, it must discover likely callers and consumers using bounded, rebuildable structural evidence, then classify every affected node against the actual diff. Traversal depth must follow the change risk: documentation and private leaves stay shallow; public contracts, shared types, persistence, events, security and payment paths require broader traversal and selective history evidence.

## Acceptance criteria

- The project index stores lexical code relationships as rebuildable evidence and labels inferred resolution honestly.
- Traversal has explicit depth, node and edge budgets; cycles terminate and budget exhaustion is visible as truncation.
- Caller and consumer traversal follows the requested direction, including canonical architecture graph relationships.
- Unresolved dynamic dispatch, missing graph coverage, stale indexes and ambiguous mappings remain visible as unknowns.
- Reviewed seed-scoped graph coverage can establish completeness only for its listed seeds, with source evidence; repository-wide partial coverage remains unchanged.
- The result distinguishes changed nodes from affected but unchanged nodes and records a disposition for each affected node.
- Higher-risk policies use selective bounded history evidence; low-risk documentation/private leaf changes avoid unnecessary history work.
- READY validation rejects missing evidence, insufficient depth, truncation, unresolved high-risk relationships, out-of-scope required changes and dispositions that disagree with the exact diff.
- The feature adds no runtime role, governance gate, external service or mandatory parser dependency.

## Evidence

- `tests/evidence/change_impact_traversal_lifecycle.py`
- `scripts/retrieval_intelligence.py`
- `scripts/project_intelligence.py`
- `templates/intelligence/IMPACT_GRAPH.yaml`

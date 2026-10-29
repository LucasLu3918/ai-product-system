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
- Python call candidates use AST direct names and explicitly imported module attributes; annotations, variables, arbitrary object methods, and builtins do not become call edges. Other supported languages retain lexical candidates.
- Default hard bounds are six hops, 150 nodes and 300 edges; remaining unvisited relationships at a bound stay `TRUNCATED`.
- Python caller candidates with an indexed exact target path are selected through the composite target-path index before unresolved candidates are inspected. Known unrelated paths and known external imports do not consume the caller-candidate budget. Unknown targets remain bounded and fail closed. The disposable Retrieval schema is v8; older schemas are migrated additively and fully rebuilt before use. At most `min(max_edges × 10, 3,000)` caller candidates are counted; an overflow sentinel may be read but is not counted against or beyond that hard cap. Exhaustion reports `TRUNCATED/caller_candidate_limit` and cannot establish completeness. Other languages retain their existing lexical resolution behavior.
- When exact resolved callers themselves exceed the remaining edge budget, traversal reports `TRUNCATED/max_edges` after filtering; it cannot return `COMPLETE` with omitted exact callers.
- Version 2 scoped evidence may bundle one caller-only and one consumer-only report over the same exact seeds; each report independently retains the 150-node, 300-edge, six-hop and 3,000-caller-candidate hard caps.
- Source reports remain unchanged. Every non-seed node must have one separate review bound to the exact direction, report digest and node digest; missing, duplicate, stale or extra node reviews block validation.
- Bounded directional reports preserve their observed status and every unresolved record. Each unresolved record requires one exact-fingerprint Human-approved `ACCEPTED_LIMITATION` with current evidence and a matching report digest; stale, missing, duplicate, extra, truncated, or over-budget evidence blocks both implementation approval and READY.
- Scoped reviewed limitations do not upgrade repository-wide graph coverage or claim lexical relationships were resolved; legacy single-report evidence remains supported under its original strict rules.

## Evidence

- `tests/evidence/change_impact_traversal_lifecycle.py`
- `tests/evidence/retrieval_intelligence_lifecycle.py` — schema-v7 rebuild, exact imported target path and SQLite query-plan index use.
- `tests/validation/change_impact_traversal_contracts.py` — fixed 3,000 candidate ceiling.
- `scripts/retrieval_intelligence.py`
- `scripts/project_intelligence.py`
- `templates/intelligence/IMPACT_GRAPH.yaml`

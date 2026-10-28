# Plan26 Phase 4 — Impact Graph relationship candidates

## System Improvement Review

- **Appropriateness:** Suitable. Change Impact already keeps the canonical graph, rebuildable lexical evidence, and per-change traversal distinct; source-backed candidates fill the discovery gap without adding a new authority layer.
- **User problem:** Project Intelligence has no reviewed edges for many relationships, so callers and consumers are hard to discover while global graph coverage is partial/unknown.
- **Existing coverage:** `retrieval_relations.py` emits bounded lexical call/reference rows; `project_intelligence_impact_graph.py` traverses only canonical edges; the public CLI is `project_intelligence.py`.
- **Reuse:** Extend the Impact Graph module and public facade, using the existing documentation placement registry and validation infrastructure.
- **Lower-layer alternative:** A report-only command is the least-authoritative fit. No automatic promotion, graph repair, or completeness inference is added.
- **Security / reliability:** Read-only source scanning with file/candidate budgets and path/line provenance. Dynamic imports and dispatch remain unresolved; repository-wide coverage stays partial/unknown.
- **Compatibility:** Existing CLI, traversal, retrieval and canonical graph formats are unchanged. The new command is additive.
- **Test impact:** Lifecycle and contract checks cover imports, literal CLI dispatch, test imports, docs placement, provenance, budgets, unresolved dynamic relations and unchanged canonical graph state.
- **Documentation impact:** Project Intelligence architecture and user guidance describe the command and retain the candidate/authority boundary.
- **Constitution impact:** NO. Human authority, approval and publication rules are unchanged.

## Approved implementation scope

Add a bounded, read-only source relationship candidate generator surfaced as `aips intelligence impact-candidates`. It may emit provenance-backed candidates from Python imports, literal CLI dispatch, test imports and `config/documentation-placement.yaml`. Candidates remain unreviewed and outside canonical `IMPACT_GRAPH.yaml`; dynamic relations remain unresolved; API/data/event coverage stays partial and consumer coverage stays unknown. Update lifecycle/contract validation, validator and scenario registries, capability projections, CHANGELOG, architecture and Project Intelligence documentation, and the Core Change Test Matrix.

Explicit exclusions: promoting candidates, writing canonical graph edges, changing coverage claims, expanding runtime support, or modifying release/tag state.

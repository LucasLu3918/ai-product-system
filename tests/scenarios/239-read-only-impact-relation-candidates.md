# Scenario 239 — Read-only Impact Graph relationship candidates

## Given

A project has a canonical Impact Graph whose repository-wide consumer coverage is partial or unknown.

## When

An Agent requests bounded relationship candidates for changed source paths.

## Then

- Python imports, literal CLI dispatch, test imports and registered documentation placements may be emitted as provenance-backed, unreviewed candidates.
- Dynamic imports and dispatch remain unresolved; candidate extraction never writes canonical graph edges.
- Global API/data/event coverage remains partial and consumer coverage remains unknown.
- File and candidate budgets are enforced, with truncation reported explicitly.

Evidence: `tests/evidence/project_intelligence_relation_candidates_lifecycle.py`, `tests/validation/project_intelligence_candidates_contracts.py`.

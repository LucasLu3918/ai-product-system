# Scenario 267: READY Stale Project Intelligence Advisory

## Given

- A local Git project has Project Intelligence readiness `READY`.
- Its freshness is `STALE`, and Context still exposes freshness reasons and targeted refresh guidance.

## When

- A supported native L2 write targets a path confined to that project.

## Then

- The write is allowed and the decision reports that stale READY Intelligence is advisory.
- `UNKNOWN` freshness, non-READY readiness, missing protocol context, unresolved instruction authority, escaping/symlink targets, creative writes in a Git project, and external actions remain denied or gated by their existing policy.
- An older cached manifest with only `intelligence_stale` as its closed reason is tolerated; any additional closed reason still denies.

## Evidence

- `tests/evidence/intelligence_context_lifecycle.py`
- `tests/evidence/opencode_integration_lifecycle.py`
- `tests/validation/opencode_integration_contracts.py`

# Scenario 223: Evolution Radar exclusion attribution

Given deterministic local pre-analysis evidence, when a signal is excluded from the shortlist or semantic queue, then the report records reproducible reason codes based only on configured category matches, priority, duplicate grouping, and queue limits. The validator rejects altered reason codes, and no reason code changes a semantic recommendation or grants adoption authority.

Evidence: `scripts/evolution_preanalysis.py`, `tests/evidence/evolution_radar_lifecycle.py`, and `tests/validation/evolution_radar_contracts.py`.

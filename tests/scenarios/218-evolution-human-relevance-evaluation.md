# Evolution human relevance evaluation

Given a monthly Evolution candidate set and explicit Human judgments with provenance,
When the offline sampler ranks candidate fingerprints for the configured 20-signal review cohort,
Then it emits a reproducible fingerprint-based sample without inventing labels or copying article content,
When the evaluator compares selected and rejected signals to relevance and actionability labels,
Then it reports shortlist precision, shortlist recall, actionable yield, per-source relevance yield, and confusion counts,
And empty, duplicate, uncertain, or incomplete labels remain NOT_READY rather than becoming negative labels,
And source weights, enablement, selection thresholds, and provider-neutral pending decisions remain unchanged until a separate Human decision.

Evidence: `scripts/evolution_relevance.py`, `config/evolution-evaluation.yaml`, `config/evolution-relevance-labels.yaml`, `tests/evidence/evolution_relevance_lifecycle.py`, and `tests/validation/evolution_relevance_contracts.py`.

# Evolution human relevance evaluation

Given a deterministic Evolution shortlist and explicit Human judgments with provenance,
When the offline evaluator compares selected and rejected signals to relevance labels,
Then it reports precision, recall, and confusion counts without changing source policy,
And empty, duplicate, uncertain, or incomplete labels remain NOT_READY rather than becoming negative labels,
And provider-neutral pending decisions remain unchanged until a separate Human decision.

Evidence: `scripts/evolution_relevance.py`, `config/evolution-relevance-labels.yaml`, `tests/evidence/evolution_relevance_lifecycle.py`, and `tests/validation/evolution_relevance_contracts.py`.

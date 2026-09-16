# Scenario 124 — Agent Eval Privacy and Provider Neutrality

Expected:
- the scorer accepts arbitrary provider/model/runtime identifiers and has no provider SDK dependency;
- recorded results reject private reasoning / chain-of-thought fields;
- recorded results reject high-confidence secret-like values;
- only observable decisions/artifacts are persisted.

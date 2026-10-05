# Scenario 216: Touched-code quality debt does not grow

Given the established repository Ruff baseline, when touched Python modules are linted, then the report groups existing findings by rule, module and auto-fixability, the repository total cannot increase, and no touched module may introduce a new finding relative to the selected base. Missing base evidence blocks the ratchet; existing findings can remain for bounded cleanup batches.

Evidence: `scripts/quality_ratchet.py`, `config/quality-ratchet.yaml`, and `tests/evidence/quality_ratchet_lifecycle.py`.

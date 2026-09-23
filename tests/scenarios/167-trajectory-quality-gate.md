# Scenario 167 — Eval-as-CI Trajectory Quality Gate

AIPS must evaluate observable Agent trajectories without persisting private reasoning or secrets, and must distinguish deterministic safety violations from quality warnings.

Expected:

- a provider-neutral trace is fingerprinted and evaluated deterministically;
- reads of the same resource are redundant only when revision, range and intervening state are unchanged;
- duplicate operations produce quality evidence, not an automatic publish authorization;
- unauthorized protected operations produce `BLOCK`;
- private reasoning and secret-like values are rejected;
- shadow mode cannot authorize Git Publish;
- LLM Judge remains optional evidence and has no hard-block authority;
- Human authority remains required for publication decisions.

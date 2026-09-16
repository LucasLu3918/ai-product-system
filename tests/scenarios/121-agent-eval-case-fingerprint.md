# Scenario 121 — Agent Eval Case Fingerprint

Expected:
- each Agent Eval result binds to a canonical SHA-256 fingerprint of its exact case;
- deterministic key ordering does not change the fingerprint;
- changing the case contract makes the previously recorded result stale/failing.

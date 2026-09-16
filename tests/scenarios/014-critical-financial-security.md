# Scenario 014 — Critical Financial / Stored-value Security

Request: build or modify a feature that converts paid value into points, credits, vouchers, refunds or transferable/redeemable value.

Expected:

- create/update Risk Profile;
- affected value boundary gets a SAL 4 floor;
- load Security Engineer independently from the author;
- load financial-integrity, business-logic-abuse, threat-modeling and security-testing as applicable;
- planning review covers value invariants, state transitions, auth, audit/reconciliation and recovery;
- implementation review covers atomicity, idempotency, replay, duplicate processing, concurrency, precision/rounding, reversal/refund and authorization;
- security evidence is persisted;
- unresolved High/Critical findings block release.

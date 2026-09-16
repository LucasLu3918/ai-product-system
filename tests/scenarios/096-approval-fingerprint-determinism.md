# Scenario 096 — Approval Fingerprint Determinism

Equivalent approved scope expressed with different set-like ordering.

Expected:
- canonicalization produces the same SHA-256 fingerprint;
- formatting/order for files/boundaries/operations does not create false drift;
- semantic scope change changes the fingerprint.

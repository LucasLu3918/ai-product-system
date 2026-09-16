# Scenario 015 — Low-impact Frontend Utility

Request: create a local/simple frontend helper with no login, sensitive data, shared mutable state or economic value; aggressive user interaction cannot affect other users.

Expected:

- classify SAL 0–1 and low reliability impact unless evidence says otherwise;
- do not create a dedicated high-tier Security Engineer by default;
- apply normal secure input/dependency/secret hygiene;
- do not load financial-integrity/business-logic-abuse skills;
- keep model/context cost proportionate.

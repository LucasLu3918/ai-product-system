---
id: financial-integrity
capability: security
estimated_context_cost: medium
---

# Financial Integrity

Use for payments, refunds, settlement, wallets, balances, stored value, points/credits/vouchers/coupons with economic value, redemption, transfer or withdrawal.

Required review topics:

- source-of-truth and state machine;
- atomicity / transaction boundaries;
- idempotency and replay safety;
- duplicate event/message handling;
- double spend / duplicate redemption;
- concurrency and locking/optimistic control;
- precision, rounding, currency/unit rules;
- negative/overflow/underflow constraints;
- reversal/refund/compensation consistency;
- audit trail and reconciliation;
- authorization across accounts/tenants;
- failure/retry behavior.

This skill implies a SAL 4 floor for the affected value boundary.

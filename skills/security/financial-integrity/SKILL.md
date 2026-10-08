---
id: financial-integrity
description: Protect financial value, ledger invariants, reconciliation and replay-safe operations
  in money-related workflows.
capability: security
estimated_context_cost: medium
triggers:
- payment
- refund
- settlement
- stored_value
- points_credit_coupon_redemption
model_requirements:
  reasoning: very_high
  coding: strong
  reliability: critical
  minimum_tier: 3
  preferred_tier: 4
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

Resolve the affected value boundary through `SYSTEM.md` and `docs/human/SECURITY_ASSURANCE.md`, which are authoritative for its SAL floor and required independent review.

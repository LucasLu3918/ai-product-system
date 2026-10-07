---
id: business-logic-abuse
capability: security
estimated_context_cost: medium
triggers:
- fraud_abuse
- promotion_coupon_points
- high_value_business_rule
model_requirements:
  reasoning: high
  coding: normal
  reliability: critical
  minimum_tier: 3
  preferred_tier: 3
---

# Business Logic Abuse

Treat valuable business rules as security boundaries.

Analyze how a legitimate interface could be intentionally or accidentally abused, including replay, duplication, sequence manipulation, multi-account abuse, promotion/coupon/referral gaming, inconsistent reversals and bypass of limits.

For each abuse case, identify invariant, abuse path, prevention, detection, recovery and test evidence.

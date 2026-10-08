---
id: secure-design
description: Design security boundaries, controls and secret handling proportionate to the system
  and data risks.
capability: security
estimated_context_cost: low
triggers:
- auth
- authorization
- sensitive_data
- security_boundary
model_requirements:
  reasoning: high
  coding: normal
  reliability: critical
  minimum_tier: 3
  preferred_tier: 3
---

# Secure Design

Identify trust boundaries, authentication/authorization requirements, sensitive data, input validation and abuse/failure modes. Prefer least privilege and secure defaults. Material security tradeoffs require explicit project decisions.


When credentials are required, use `orchestration/SECRET_HANDLING.md`. Treat secret acquisition as a runtime dependency/reference and prevent logging/debug/error paths from exposing values.

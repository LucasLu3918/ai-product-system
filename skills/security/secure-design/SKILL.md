---
id: secure-design
capability: security
estimated_context_cost: low
---

# Secure Design

Identify trust boundaries, authentication/authorization requirements, sensitive data, input validation and abuse/failure modes. Prefer least privilege and secure defaults. Material security tradeoffs require explicit project decisions.


When credentials are required, use `orchestration/SECRET_HANDLING.md`. Treat secret acquisition as a runtime dependency/reference and prevent logging/debug/error paths from exposing values.

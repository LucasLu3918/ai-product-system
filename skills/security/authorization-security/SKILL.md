---
id: authorization-security
description: Design and review tenant isolation, object-level permissions and authorization boundaries
  for APIs and workflows.
capability: security
estimated_context_cost: low
triggers:
- authz_change
- privileged_operation
- cross_account_access
model_requirements:
  reasoning: high
  coding: normal
  reliability: critical
  minimum_tier: 3
  preferred_tier: 3
---

# Authorization Security

Review who may perform each operation and on whose resources.

Check authentication vs authorization separation, ownership/tenant boundaries, role/permission boundaries, privileged/admin paths, default-deny behavior, server-side enforcement, horizontal/vertical privilege escalation, and auditability.

Do not rely on client-side UI restrictions as authorization.

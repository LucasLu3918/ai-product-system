---
id: incident-response
description: Triage incidents, contain impact, recover service and document evidence and follow-up
  actions.
capability: operations
estimated_context_cost: low
triggers:
- production_incident
- outage
model_requirements:
  reasoning: high
  coding: normal
  reliability: critical
  minimum_tier: 3
  preferred_tier: 3
---

# Incident Response

During an active incident: protect users/data, restore service with reversible actions, verify stability, preserve evidence, then investigate root cause and follow-up work. Destructive recovery actions remain gated.

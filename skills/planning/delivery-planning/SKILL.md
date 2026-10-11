---
id: delivery-planning
description: Plan implementation, dependencies, verification and delivery milestones with explicit
  risks and approval boundaries.
capability: delivery-planning
estimated_context_cost: low
triggers:
- execution_plan
- milestones
- dependencies
model_requirements:
  reasoning: medium
  coding: none
  reliability: high
  minimum_tier: 1
  preferred_tier: 2
---

# Delivery Planning

Convert accepted requirements and Quality Profile targets into work packages, dependencies, milestones, critical sequence, integration/test checkpoints, resource/time estimate ranges, Deployment Unit order and rollout risks.

For substantial products:
- estimate initially before architecture;
- refine after architecture/dependency choices;
- include optimistic/expected/risk-adjusted range + confidence;
- distinguish LOCAL_COMPLETE from Production Enablement / PRODUCTION_VERIFIED;
- include TCO/operations implications when they affect the plan.

Do not redo product discovery unless a blocking gap prevents planning.

## Spec-to-ticket dependency map

When an approved specification needs execution, split it into independently verifiable vertical tracer-bullet slices, not layer-only tickets. Give each item stable ID, requirement/acceptance links, deliverable, tests, dependencies, risks and blocked-by edges. Use the existing Planning Package manifest and deterministic scheduler/task graph rather than a competing workflow engine. Large multi-session plans retain unresolved decisions and verified handoff references. Ticket creation or issue modification remains a separate scoped external write; planning alone never authorizes it.

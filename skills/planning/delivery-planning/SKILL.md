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
## Vertical slices and dependency maps

When a plan spans multiple deliverables, break it into user-visible vertical slices with explicit blocking dependencies, verification evidence and requirement traceability. Keep each ticket independently reviewable where practical; identify integration points and assumptions before parallel work. Create or update external tracker records only when the user explicitly authorized that write.

Source note: adapted from mattpocock/skills engineering/to-tickets and engineering/implement-spec at 49dd158d1076134a641b33efb035946536778336 (MIT); see licenses/MIT-Matt-Pocock-Skills.txt.

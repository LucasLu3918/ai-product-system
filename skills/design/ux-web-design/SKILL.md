---
id: ux-web-design
description: Design web user experiences, interaction flows and accessible layouts grounded in
  product requirements.
capability: design
estimated_context_cost: low
triggers:
- ux_flow
- web_ui
- interaction_design
model_requirements:
  reasoning: medium
  coding: none
  reliability: normal
  minimum_tier: 1
  preferred_tier: 2
---

# Ux Web Design

Translate approved product goals and requirements into implementable information architecture, journeys, task flows, screens and interaction behavior.

## Planning sequence

1. Map information architecture and primary journeys.
2. Define task flows, including alternate, failure and recovery paths.
3. Create a screen inventory and assign stable `SCR-NNN` IDs.
4. For each material screen, record primary user, responsibility, requirement IDs, entry/exit points and interactions.
5. Specify normal, loading, empty, error, disabled, success and relevant permission/authentication states.
6. Define responsive behavior, accessibility requirements and edge cases.

Keep design traceable to user goals, requirements and the Quality Profile. Do not invent product scope in UX. Explicitly mark inapplicable flows with a reason.

For existing UI:
- reuse Project Visual Profile when current;
- prefer consistent tokens/components and stable state geometry;
- preserve valid semantic variants;
- avoid arbitrary page-specific spacing/geometry when a shared rule solves the problem.

Do not load unrelated engineering detail unless interaction depends on it or rendered implementation polish requires implementation evidence.

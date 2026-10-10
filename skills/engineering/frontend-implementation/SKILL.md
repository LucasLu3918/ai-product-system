---
id: frontend-implementation
description: Implement maintainable frontend features with clear component boundaries,
  state ownership, responsive behavior and complete UI states.
capability: engineering
estimated_context_cost: medium
triggers:
- frontend_feature
- ui_component_change
- client_state_management
model_requirements:
  reasoning: medium
  coding: strong
  reliability: high
  minimum_tier: 2
  preferred_tier: 2
---

# Frontend Implementation

Use the target project’s existing framework, component system, styling rules, and test conventions. Load ux-web-design for interaction design and visual-quality-review when rendered visual acceptance matters. Use rest-api when the change is primarily an API contract.

## Method

1. Read the existing page/component patterns and the relevant UX, API, and accessibility requirements before choosing an implementation.
2. Split components around cohesive responsibilities and reusable behavior, not arbitrary file size. Keep domain rules out of presentation components where the project has a suitable shared layer.
3. Assign each piece of state an owner: local interaction state, shared client state, URL state, or server data/cache. Keep one source of truth and define cache invalidation or synchronization.
4. Cover loading, empty, error, success, disabled, permission, and recovery states that apply to the flow. Preserve entered data when a recoverable request fails.
5. Define responsive behavior at supported breakpoints; use semantic HTML, keyboard behavior, visible focus, and accessible names.
6. Add tests for user-visible behavior and important state transitions. Check bundle or rendering costs when the change materially affects them.

## Output

Describe the component boundaries, state ownership, data flow, responsive and boundary states, and the verification evidence. Do not replace the project’s stack or add a dependency without a demonstrated need.

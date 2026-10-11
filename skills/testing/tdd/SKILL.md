---
id: tdd
description: Implement testable behavior through failing tests, minimal passing changes and refactoring;
  use characterization tests for legacy behavior.
capability: testing
estimated_context_cost: low
triggers:
- testable_behavior_change
- modifying_testable_behavior
- implementing_business_rules
- implementing_api_or_service_behavior
model_requirements:
  reasoning: medium
  coding: strong
  reliability: high
  minimum_tier: 2
  preferred_tier: 2
---

# Test-Driven Development

Default cycle for testable behavior:

1. RED — express the required behavior with a failing test.
2. GREEN — implement the smallest change that passes.
3. REFACTOR — improve structure while tests remain green.

For legacy code with insufficient coverage, create characterization tests around behavior that must remain stable before risky modification.

Do not force unit-test-shaped TDD onto purely visual work, generated code or configuration where another validation strategy is more appropriate.

## Test seams and feedback quality

Choose an observable behavior and the narrowest stable boundary that would catch the regression. Prefer asserting publicly observable outcomes instead of implementation detail, mock interaction counts, or snapshots with no behavioral meaning. Use fake/mocked providers only for uncontrollable side effects or deliberately isolated contracts; keep at least one appropriate integration test for meaningful integration boundaries. For each slice, show the failed assertion before a minimal GREEN change and run affected tests after refactoring. Never modify tests merely to hide a product defect.

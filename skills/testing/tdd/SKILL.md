---
id: tdd
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

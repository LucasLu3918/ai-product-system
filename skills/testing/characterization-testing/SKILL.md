---
id: characterization-testing
capability: testing
estimated_context_cost: low
triggers:
- legacy_change_without_coverage
model_requirements:
  reasoning: medium
  coding: strong
  reliability: high
  minimum_tier: 2
  preferred_tier: 2
---

# Characterization Testing

Before risky changes to legacy behavior with insufficient coverage, capture the behavior that must remain stable. Characterization tests describe existing behavior; they are not an endorsement of every legacy design choice.

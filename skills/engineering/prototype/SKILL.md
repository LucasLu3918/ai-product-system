---
id: prototype
description: Explore a UI, workflow or behavior question with a throwaway prototype that stays separate from production implementation.
capability: engineering
estimated_context_cost: medium
triggers:
- explicit_prototype_request
- ui_state_model_exploration
- workflow_behavior_exploration
model_requirements:
  reasoning: medium
  coding: strong
  reliability: high
  minimum_tier: 2
  preferred_tier: 2
---

# Rapid Prototyping

Use a small, disposable prototype to answer one named design question.

1. State the question, assumptions and behavior the prototype must expose.
2. Reuse the project's existing tools and conventions; keep the work in a scratch location or clearly disposable branch.
3. Build only enough interaction or logic to get useful feedback. Label mocked behavior and missing production concerns.
4. Summarize what the prototype established, what it did not establish, and the next decision.
5. Keep prototype code out of production paths unless the user separately asks to harden and integrate it.

Do not connect real credentials, production services or private user data to a prototype. A prototype result is evidence for a decision, not production readiness.

Source note: adapted from mattpocock/skills engineering/prototype at 49dd158d1076134a641b33efb035946536778336 (MIT); see licenses/MIT-Matt-Pocock-Skills.txt.

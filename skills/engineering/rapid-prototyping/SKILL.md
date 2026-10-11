---
id: rapid-prototyping
description: Build disposable prototypes to test bounded UI or logic design questions.
capability: engineering
estimated_context_cost: low
triggers:
- explicit_throwaway_prototype
- validate_ui_interaction_variant
model_requirements:
  reasoning: medium
  coding: strong
  reliability: high
  minimum_tier: 2
  preferred_tier: 2
---

# Rapid Prototyping

## Admission and limits
Distinct from `frontend-implementation` and `ux-web-design`: the output is a knowingly disposable experiment, not production code or a deployable feature. Inspired by Matt Pocock's `prototype` (MIT, upstream reference in `references/external-skills/mattpocock-2026-10-11.yaml`).

## Method
1. State a single decision to be tested, audience, hypotheses and acceptance signals.
2. Choose a **UI** branch (two or three clearly differentiated variations) or a **logic** branch (observable state transitions or simulations).
3. Build the smallest local, shareable artifact, preferring one self-contained HTML file for UI/logic interaction when appropriate.
4. Label fixtures and mock data explicitly. Verify keyboard/mobile behavior where relevant and test representative states.
5. Record the observed trade-offs, unanswered questions and whether to discard or transfer an agreed design into normal implementation.

## Non-triggers
Production feature requests, security-critical workflows, persistent migrations, deployment tasks, or user requests that are already approved for full implementation. A prototype cannot create production access, change an approved project baseline, or publish without normal AIPS governance.

---
id: game-design-document
description: Turn a game concept into a testable design brief covering player experience,
  core loops, rules and a playable vertical slice.
capability: product
estimated_context_cost: medium
triggers:
- new_game_concept
- game_mechanic_design
- core_loop_definition
model_requirements:
  reasoning: high
  coding: none
  reliability: high
  minimum_tier: 2
  preferred_tier: 3
---

# Game Design Document

Use for a new game concept or material game-mechanic design. Use requirements-definition for a non-game product and product-discovery when the problem or target audience is still unknown.

## Method

1. Define target players, platform, session context, design pillars, and the intended player experience. Use Mechanics–Dynamics–Aesthetics as a lens, not as a substitute for evidence.
2. Describe the 30-second action loop, the several-minute loop, and the full-session or progression loop. Identify the decisions and feedback at each level.
3. Specify rules, player actions, resources, state transitions, win/loss conditions, progression, and edge cases. Keep terminology consistent.
4. State the smallest playable vertical slice that can test the riskiest experience assumptions. Bound content, mechanics, platforms, and acceptance criteria.
5. List assumptions and rank them by uncertainty and impact. Define a prototype or playtest that could disprove each important assumption.
6. Reuse references for mechanics analysis only; do not copy protected characters, text, art, or distinctive expression. Route visual direction through visual-direction or creative-calibration.

## Output

Create a GDD with player and experience goals, core loops, rules, progression, content scope, vertical slice, acceptance criteria, and testable assumptions. Keep platform-specific policy and legal review current and separate.

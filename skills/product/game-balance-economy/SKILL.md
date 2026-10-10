---
id: game-balance-economy
description: Evaluate difficulty, progression, random rewards and in-game resource
  flows with models, simulations and exploit analysis.
capability: product
estimated_context_cost: medium
triggers:
- difficulty_curve
- in_game_economy
- loot_or_gacha_probability
- balance_tuning
model_requirements:
  reasoning: high
  coding: normal
  reliability: high
  minimum_tier: 2
  preferred_tier: 3
---

# Game Balance and Economy

Use for difficulty curves, progression, drops, resource flows, and in-game probability. Use financial-integrity for real-money transactions and business-logic-abuse for abuse of valuable rules.

## Method

1. List player goals, progression states, relevant variables, and the intended range of viable strategies.
2. Make formulas, tables, probabilities, and resource sources/sinks explicit. Include the assumptions and uncertainty of player-behavior estimates.
3. Simulate representative strategies and edge cases with reproducible seeds; report sample size and sensitivity. Use observed play data when available and consented.
4. Look for dominant strategies, runaway growth, dead ends, farming loops, resource inflation, and exploitable state transitions.
5. Change a small number of parameters, rerun the same scenarios, and compare difficulty and economy outcomes.
6. For paid random rewards, disclose probabilities as required by the product and have jurisdiction-specific legal and age-safety requirements reviewed by qualified owners. This skill does not provide legal advice.

## Output

Provide the model, assumptions, simulation method/results, balance recommendations, source/sink table, exploit cases, and remaining uncertainty. Do not present a small simulation as proof of population-level balance.

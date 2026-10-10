---
id: game-feel
description: Tune input response and audiovisual feedback with observable events,
  adjustable parameters and motion-sensitive safeguards.
capability: design
estimated_context_cost: low
triggers:
- game_feel_tuning
- combat_feedback
- controls_feel_unresponsive
model_requirements:
  reasoning: medium
  coding: normal
  reliability: high
  minimum_tier: 1
  preferred_tier: 2
---

# Game Feel

Use when the interaction is technically correct but lacks responsive, legible, or satisfying feedback. Use visual-direction for art style and ux-web-design for ordinary web usability.

## Method

1. Identify the player action, expected response, observed delay, and the intended emotional or informational effect.
2. Map events to feedback: anticipation, action, contact, completion, failure, and recovery. Consider animation timing, sound, haptics, particles, camera motion, and UI changes only when they clarify the event.
3. Measure input-to-feedback latency and observe on target hardware. Change one parameter group at a time and compare before/after.
4. Centralize tunable values and name their units/ranges. Keep feedback synchronized with authoritative game state.
5. Offer reduced-motion or disable controls for flashing, strong camera shake, and other motion-sensitive effects. Respect platform accessibility settings where available.
6. Validate that feedback remains readable, does not obscure play, and communicates critical state without sound or color alone.

## Output

Provide an event-to-feedback map, tunable parameters, target-device checks, and comparison evidence. Treat specific timing values as hypotheses until tested with players.

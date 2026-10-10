---
id: game-loop-architecture
description: Design a game runtime around explicit state transitions, update/render
  boundaries, deterministic rules and versioned saves.
capability: software-architecture
estimated_context_cost: medium
triggers:
- game_runtime_architecture
- game_state_management
- save_system
model_requirements:
  reasoning: high
  coding: strong
  reliability: high
  minimum_tier: 2
  preferred_tier: 3
---

# Game Loop Architecture

Use for a game runtime, simulation, state-management, or save-format design. Do not impose a real-time engine loop on a turn-based puzzle or a project that already has a suitable runtime architecture.

## Method

1. Derive runtime needs from the GDD and target platforms. Decide whether play is frame-driven, fixed-step real-time, event-driven, or turn-based.
2. Separate domain rules and simulation state from rendering, input devices, storage, and engine APIs. Make update order and ownership explicit.
3. Choose a scene tree, entity/component model, or simpler structures based on scale and actual query/update needs. Avoid adopting ECS or a new framework by default.
4. Define states and legal transitions for menus, play, pause, resume, completion, failure, and restore. Specify input routing and how focus/visibility changes affect time.
5. For real-time simulation, define timestep, catch-up limits, determinism needs, and how render cadence differs from simulation. For non-real-time play, keep state transitions deterministic and testable without artificial ticks.
6. Version persisted state. Validate saves, migrate supported older schemas, and define behavior for corrupted, missing, or interrupted writes.
7. Test rules independently and use seeded replay only where deterministic simulation provides value.

## Output

Provide the update/state model, module boundaries, persistence contract/version plan, failure recovery, and tests. Use the project’s selected engine and place engine-specific APIs in references.

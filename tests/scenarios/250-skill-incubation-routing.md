# Scenario 250 — game loop architecture

## Request

> Model a turn-based web puzzle with restart and saved progress.

## Expected

- Avoid imposing a real-time loop; separate deterministic puzzle rules from DOM/SVG rendering; define state transitions, versioned saves and pure rule tests.
- Load only the relevant skill together with project-native instructions and any clearly applicable companion skill.
- State assumptions and unknowns; do not claim external or real-project validation that was not performed.

## Evidence

- The canonical skill frontmatter and method in skills/INDEX.yaml and the corresponding skills/**/SKILL.md.
- This scenario records expected routing and output behavior; it is manual semantic evidence, not an automated model-routing result.

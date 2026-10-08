---
id: visual-direction
description: Establish a coherent visual direction using approved creative references, style decisions
  and product constraints.
capability: design
estimated_context_cost: low
triggers:
- visual_concepts
- brand_direction
- design_system
- character_artwork
model_requirements:
  reasoning: medium
  coding: none
  reliability: normal
  minimum_tier: 1
  preferred_tier: 2
---

# Visual Direction

Develop a visual system from product context and approved UX, then carry the selected direction into reusable tokens, component language and screen states.

## Method

1. Read product scope, user needs, UX flows, existing brand guidance and supplied assets.
2. Use `creative-reference-research` when the direction needs current references; record what traits inform the work without copying another product.
3. Offer materially different directions when a human choice is needed. Explain audience fit and trade-offs, then wait for the direction to be selected before broad visual specification.
4. Define rationale, typography, color, spacing/grid, imagery, icons, tokens, components and interaction states.
5. Assign stable `VIS-NNN` IDs to visual systems/components referenced from requirements.
6. Check responsive behavior, contrast and repeated-component consistency.

Extend this Skill before considering a separate design-system Skill. Treat references as inspiration, not proof that a product needs a feature.

## Character art

For reusable character work, use the existing `creative-calibration` flow and the `CHARACTER_PROFILE.yaml`, `STYLE_PROFILE.yaml`, and `CHARACTER_ARTWORK_MANIFEST.yaml` templates. Generate each pose, expression, and accessory as a separate image; typeset Chinese labels in the deterministic sheet composer rather than in the image model. Prefer the official local ComfyUI MCP when already available; MFLUX is an optional Apple Silicon local engine. Do not add another MCP server or download model weights as part of setup. Record exact model/runtime/license provenance and local-only execution. The composer checks bytes and layout; it does not assess identity fidelity or visual quality.

Carry explicit must-have/must-avoid traits into the existing Character and Style Profiles: recognizable identity, rendering medium, composition, anatomy, material detail, lighting and common style across characters. Use `aips creative discover`, then create a configured Bundle version with `aips creative configure`; preflight cannot establish model suitability or artwork quality. Preserve the user-selected runtime model and do not install engines or download weights.

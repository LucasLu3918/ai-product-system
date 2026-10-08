---
id: creative-calibration
description: Calibrate creative references and visual directions with user feedback before committing
  to design execution.
capability: design
estimated_context_cost: low
triggers:
- vague_visual_request
- user_reference_assets
- style_calibration
- character_artwork
model_requirements:
  reasoning: medium
  coding: none
  reliability: high
  minimum_tier: 1
  preferred_tier: 2
---

# Creative Calibration

Turn vague words such as premium, minimal, fashionable, warm or playful into an explicit Creative Direction.

Priority:
1. current explicit user request;
2. user-provided brand/assets/references;
3. accepted Brand System / Project Visual System;
4. selected Creative Direction;
5. runtime reference research;
6. generic design knowledge.

Use progressive calibration: show 2–3 directions, learn what the user likes/dislikes, allow aspect-level mixing, record must-have/must-avoid traits, then lock the direction before broad implementation when visual mismatch would be costly.

For recurring characters, capture stable identity traits and hashed local references in `templates/creative/CHARACTER_PROFILE.yaml`; capture rendering and text-composition rules in `templates/creative/STYLE_PROFILE.yaml`. Preserve identity features across allowed pose/expression variations, and never persist raw prompts or upload references by default.

After direction is approved, an explicit local execution request may use `templates/creative/CREATIVE_BUNDLE.yaml`. Run `aips creative preflight` first; missing local engines stay `BLOCKED_NO_ENGINE`. Only call `aips creative execute` when the user requested image generation or editing. The runner accepts local MFLUX or loopback ComfyUI built-in workflows, writes only new raster files under the declared output scope, and never downloads model weights or sends images to a cloud provider.

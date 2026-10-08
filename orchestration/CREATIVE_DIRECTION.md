# Creative Direction Protocol

Use for visual artifacts of any type: websites, UI, banners, hero visuals, social posts, presentations, product pages, campaigns and similar work.

## Input priority

1. current explicit user request;
2. user-owned assets and references;
3. approved Brand System;
4. approved project Visual System;
5. current Creative Direction;
6. runtime market/reference research;
7. generic design knowledge.

## Flow

~~~text
Creative Request
→ Asset / Brand Intake
→ Intent Extraction
→ Reference Research when useful
→ 2–3 Differentiated Directions
→ Progressive User Calibration
→ Creative Direction Lock
→ Design / Generation
→ Visual Quality Review
→ User Review / Iterate
~~~

Do not jump from vague adjectives directly into broad implementation when visual mismatch would be expensive.

## Reference research

Use `creative-reference-research`.

- Styles are reference data under `references/creative/styles/`.
- Current examples/trends should be searched at runtime.
- Prefer showing current image references or generating original concept previews when tools allow.
- Do not permanently store third-party copyrighted assets by default.

## Calibration

Use `creative-calibration`.

Allow the user to say things such as:
- “A layout + B colors”;
- “keep my logo/photo, but use this reference mood”;
- “more premium, less technical”.

Persist the approved result using `templates/creative/CREATIVE_DIRECTION.yaml`.

## Review

Material visual artifacts use `visual-quality-review`. Review against the approved direction and brand rules, not generic taste alone.

## Local character artwork

Use the existing `creative-calibration`, `visual-direction`, and `visual-quality-review` Skills for recurring character artwork; do not create a duplicate character-art Skill or provider adapter. Save stable identity traits and exact hashed references in `templates/creative/CHARACTER_PROFILE.yaml`, rendering rules in `STYLE_PROFILE.yaml`, and per-output provenance in `CHARACTER_ARTWORK_MANIFEST.yaml`.

Prefer the official local ComfyUI MCP when the user's local ComfyUI setup is already available. MFLUX is an optional Apple Silicon local engine. Neither tool is installed by this workflow, and model weights are never downloaded without separate authorization. Both paths must record the exact model/revision, runtime version, verified license source, and `external_egress: false`; do not silently fall back to paid or cloud APIs. Do not store raw prompts; an optional one-way prompt fingerprint may be retained.

Keep each pose, expression, and accessory as its own SVG or PNG so the user can review or replace individual outputs. `python scripts/character_artifacts.py validate MANIFEST --project PROJECT` checks local paths, file bytes, hashes, dimensions, provenance, and model license fields. `compose` creates a new deterministic SVG character sheet with separately typeset Chinese labels and refuses to overwrite any existing file. It does not claim identity consistency or image quality: use `visual-quality-review` to compare every asset against the approved identity/style profiles and record an independent decision. Record benchmark device, elapsed time, and memory only when actually measured; unavailable runtime, model failures, and license ambiguity remain visible limitations.

Creative evidence may optionally link the artwork manifest and its exact SHA-256 digest using `character_artwork.manifest` and `character_artwork.sha256`. This records which manifest was reviewed; it does not replace asset validation or visual review. The workflow uses no network service and keeps references local by default.

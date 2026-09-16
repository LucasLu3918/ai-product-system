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

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

Use the existing `creative-calibration`, `visual-direction`, and `visual-quality-review` Skills for recurring character artwork; do not create a duplicate character-art Skill or provider integration surface. The optional AIPS-owned executor is a bounded adapter for already-installed local engines. Save stable identity traits and exact hashed references in `templates/creative/CHARACTER_PROFILE.yaml`, rendering rules in `STYLE_PROFILE.yaml`, and per-output provenance in `CHARACTER_ARTWORK_MANIFEST.yaml`.

Prefer the official local ComfyUI MCP when it already fits the task. AIPS also supports an explicit local `mflux-generate` CLI adapter and a loopback ComfyUI API adapter that accepts only allowlisted built-in nodes. The MFLUX child process runs with model-hub offline flags; ComfyUI requests disable proxy settings, reject redirects, and target loopback only. ComfyUI edit requires a pre-staged input whose bytes match the selected project reference. Neither tool is installed by this workflow, and model weights are never downloaded. Do not silently fall back to paid or cloud APIs. Record the exact model/revision, runtime version, verified license source, bundle/workflow fingerprints, and `external_image_egress: false`; do not store raw prompts.

Use `aips creative preflight --project PROJECT --bundle BUNDLE.yaml` to validate the non-Git EPHEMERAL scope, local model/runtime and create-only output before generation. Missing engines return `BLOCKED_NO_ENGINE`; preflight and Integration Gate inspection never run a generation job. Run `aips creative execute` only for an explicit user-authorized generation/edit request. Outputs are limited to PNG/JPEG/WEBP under the declared output scope, plus a create-only provenance manifest; existing files and references are never overwritten. Retries are finite and limited to transient timeouts. `aips creative trace` exposes only bounded reason codes, elapsed time, attempts and hashes. A manifest starts with visual review `PENDING`; deterministic checks cannot set visual quality to PASS. An independent human reviewer must inspect each rendered image against the approved identity/style profile and record PASS or REVISE.

Keep each pose, expression, and accessory as its own SVG or PNG so the user can review or replace individual outputs. `python scripts/character_artifacts.py validate MANIFEST --project PROJECT` checks local paths, file bytes, hashes, dimensions, provenance, and model license fields. `compose` creates a new deterministic SVG character sheet with separately typeset Chinese labels and refuses to overwrite any existing file. It does not claim identity consistency or image quality: use `visual-quality-review` to compare every asset against the approved identity/style profiles and record an independent decision. Record benchmark device, elapsed time, and memory only when actually measured; unavailable runtime, model failures, and license ambiguity remain visible limitations.

Creative evidence may optionally link the artwork manifest and its exact SHA-256 digest using `character_artwork.manifest` and `character_artwork.sha256`. This records which manifest was reviewed; it does not replace asset validation or visual review. The workflow sends no images to external services and keeps references local by default; the optional ComfyUI adapter contacts only the configured loopback API.

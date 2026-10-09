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

The general `aips project diagnose` command is read-only and does not discover, prepare, configure or execute a creative provider. Creative workflow authorization remains governed by the explicit request and bounded creative lifecycle.

For local Z-Image Turbo in ComfyUI, use the registered API workflow template and verify the three locally installed model files during preflight; do not substitute custom nodes or treat this profile as image editing support. AIPS strips ComfyUI prompt-bearing PNG text chunks before publishing the output file.

The closed MFLUX registry also supports `z-image-turbo` / `generate` through `mflux-generate-z-image-turbo`. The MFLUX 0.22 Turbo argv uses the existing local path as `--model`, the fixed `--base-model z-image-turbo`, and `--no-exif` to suppress prompt metadata. The installed Turbo runtime accepts explicit Bundle steps (8 is the recommended starting point); it supplies its own non-guided Turbo behavior. Do not route edit, non-Turbo Z-Image, or ControlNet through this pair. Complete model/tokenizer weights must already exist locally; visual quality and independent human acceptance remain separate from engine completion.

OpenCode V2 exposes creative_execution through its native Code Mode catalog. Call the exact listed tools.creative_execution signature through execute; do not guess a direct model tool name. A short selected direction (A/B/C) or bounded style adjustment can continue an active request, while cancellation and unrelated tasks revoke it.

For detailed illustration requests, inspect capabilities first and retain the requested medium. Use discover for fixed local command inventory and configure for a new allowlisted Bundle/output version; both never launch generation. Load creative-calibration, visual-direction and visual-quality-review at their respective stages. A clear scoped image-generation request needs no magic phrase; planning, cancellation or unrelated tasks revoke continuation. Never bypass a missing engine by silently hand-writing SVG. Execution, bounded container validation, independent Human visual review and user acceptance are separate evidence. Prepared Character/Style Profile hashes are included in provenance and must still match at review.

Use the existing `creative-calibration`, `visual-direction`, and `visual-quality-review` Skills for recurring character artwork; do not create a duplicate character-art Skill or provider integration surface. The optional AIPS-owned executor is a bounded adapter for already-installed local engines. Save stable identity traits and exact hashed references in `templates/creative/CHARACTER_PROFILE.yaml`, rendering rules in `STYLE_PROFILE.yaml`, and per-output provenance in `CHARACTER_ARTWORK_MANIFEST.yaml`.

Prefer the official local ComfyUI MCP when it already fits the task. AIPS also supports an explicit local MFLUX CLI adapter and a loopback ComfyUI API adapter that accepts only allowlisted built-in nodes. The fixed MFLUX capability registry maps FLUX.1 to `mflux-generate`, FLUX.2 Klein generation/editing to `mflux-generate-flux2` / `mflux-generate-flux2-edit`, and Qwen Image Edit 2511 to `mflux-generate-qwen-edit`; unsupported model/operation pairs fail closed. The MFLUX child process runs with model-hub offline flags; ComfyUI requests disable proxy settings, reject redirects, and target loopback only. FLUX.1 edit accepts one reference; only FLUX.2/Qwen commands using `--image-paths` accept up to eight bounded project-confined local references. ComfyUI edit remains single-reference and requires staged bytes to match the selected project reference. Neither tool is installed by this workflow, and model weights are never downloaded. Do not silently fall back to paid or cloud APIs. Record the exact model/revision, runtime version, verified license source, bundle/workflow fingerprints, and `external_image_egress: false`; do not store raw prompts in manifests or traces.

Use the dedicated `creative_execution` tool's `prepare` action or `aips creative prepare` to create a versioned workspace containing a README, Character Profile, Style Profile, and draft Bundle. Preparation requires an explicit creative create intent and a project-relative scope; it only creates fixed new files and never overwrites. Configure exact locally installed model/runtime/license provenance before use. Run `aips creative preflight --project PROJECT --bundle BUNDLE.yaml` to validate the non-Git EPHEMERAL scope, local model/runtime and create-only output before generation. Preflight reports host, backend and available workflow dtype inputs; compatibility remains `UNVERIFIED` until real local inference evidence exists. Missing engines return `BLOCKED_NO_ENGINE`; preflight and Integration Gate inspection never run a generation job. Run `aips creative execute` only for an explicit user-authorized generation/edit request. Outputs are limited to PNG/JPEG/WEBP under the declared output scope, plus a create-only provenance manifest; existing files and references are never overwritten. Retries are finite and limited to transient timeouts. `aips creative trace` exposes only bounded reason codes, elapsed time, attempts and hashes. The manifest records workflow execution, raster validity, model inference, Human visual review and user acceptance as separate evidence; a Human visual review does not imply user acceptance.

Keep each pose, expression, and accessory as its own SVG or PNG so the user can review or replace individual outputs. `python scripts/character_artifacts.py validate MANIFEST --project PROJECT` checks local paths, file bytes, hashes, dimensions, provenance, and model license fields. `compose` creates a new deterministic SVG character sheet with separately typeset Chinese labels and refuses to overwrite any existing file. It does not claim identity consistency or image quality: use `visual-quality-review` to compare every asset against the approved identity/style profiles and record an independent decision. Record benchmark device, elapsed time, and memory only when actually measured; unavailable runtime, model failures, and license ambiguity remain visible limitations.

Creative evidence may optionally link the artwork manifest and its exact SHA-256 digest using `character_artwork.manifest` and `character_artwork.sha256`. This records which manifest was reviewed; it does not replace asset validation or visual review. The workflow sends no images to external services and keeps references local by default; the optional ComfyUI adapter contacts only the configured loopback API.

A collection profile records shared direction and stable character references. A CREATIVE_JOB_MANIFEST.yaml lists only already prepared and configured local Bundles. aips creative generate-set validates the bounded manifest, preflights each Bundle immediately before execution, records per-item failures, and continues the remaining set. Re-running the same unchanged manifest skips only outputs and provenance manifests whose saved hashes still match; failed or changed items are retried only into their existing create-only output paths, so users must select a new Bundle version if an output already exists. Health discovery runs a bounded version-only probe for fixed installed MFLUX commands; it reports only a sanitized version token and does not load weights or generate an image.

For OpenCode V2, mutation authority comes from the native prompt-admission hook and is held only in memory for the active Session. Every new user prompt replaces that grant; dispatch Context and transcript history are never an authority source. Synthetic, shell, compaction, and tool-driven continuation events do not create a new grant.

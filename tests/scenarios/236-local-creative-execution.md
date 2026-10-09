# Scenario 236: Local Creative Bundle Execution

## Context

A creative task may request generation or editing in a local non-Git workspace. The user has an existing MFLUX installation or a local ComfyUI server and chooses an exact output scope. Model/runtime provenance and independent visual review must remain visible.

## Deterministic expectations

- `aips creative preflight` validates a versioned EPHEMERAL Bundle, confined paths, no-overwrite output, local model/runtime provenance and configured engine without starting a generation job.
- `aips creative discover` independently reports installed command, runtime, model inventory, preflight, and inference readiness; the ComfyUI probe is read-only and fixed to `127.0.0.1:8188`, while model/inference readiness remain unverified until their corresponding evidence exists.
- On Apple Silicon, explicit static FP8 model metadata may produce an advisory compatibility warning and a local FP16/BF16 recommendation; it never claims runtime compatibility or executes inference.
- `aips creative prepare` creates versioned character/style Profiles, a Bundle and an output scope only inside a non-Git EPHEMERAL workspace; it rejects traversal/symlinks, never overwrites, and leaves engine provenance explicitly unconfigured until the user selects an already-installed local engine.
- A missing or unavailable engine returns `BLOCKED_NO_ENGINE`. Preview, repository validation and the Integration Gate never execute a user-configured engine.
- `BLOCKED_NO_ENGINE` includes bounded per-provider reason codes and a recovery action without exposing local paths or credentials.
- `aips creative execute` runs only after explicit invocation, only in a non-Git EPHEMERAL workspace, and writes PNG/JPEG/WEBP plus a new manifest beneath the declared output scope.
- prompt compilation deterministically combines Bundle intent with Character acceptance criteria, Style constraints and optional Collection style lock; execution records profile and compiled-prompt hashes without storing prompt contents.
- a capability profile can recommend only operation-compatible local models with verified license and human-reviewed quality evidence; recommendations are advisory and never switch the Bundle model.
- optional `review-assist` may use only an already-installed local Ollama vision model over loopback, validates bounded image and response data, and writes a separate report with `authority: NONE`; Human review and user acceptance remain independently pending.
- MFLUX model/operation pairs resolve through a fixed CLI capability registry (FLUX.1, FLUX.2 Klein and Qwen Image Edit 2511), use argv-only execution, `shell=false`, local model path and offline model-hub environment. FLUX.1 edit accepts one reference; only FLUX.2/Qwen `--image-paths` edit accepts up to eight bounded project-contained references. Inputs and outputs are not passed to a cloud service.
- ComfyUI requests use HTTP loopback only, disable proxies and reject redirects. Checkpoint workflows keep their existing built-in-node contract; the registered Z-Image Turbo profile accepts exactly its split-loader topology, verifies UNET/CLIP/VAE choices against the local API inventory and is generate-only. Edit accepts exactly one staged input and checks its bytes against the selected project reference before submission. ComfyUI PNG text chunks are stripped before the create-only AIPS output is published so embedded prompts do not persist in generated image metadata.
- Existing files, manifests and source references are never overwritten. Retries are bounded and apply only to transient timeouts; provider failure never becomes `COMPLETE`.
- The manifest binds bundle/workflow/input/output hashes, model revision, runtime/version, license source and measured elapsed time. Visual review begins `PENDING` and requires an independent Human PASS/REVISE decision.
- Trace accepts only bounded enums, timestamps, attempts, elapsed time, and hashes; prompt, image data, credentials, workflow bodies and filesystem paths are rejected.

## Lifecycle evidence

Use synthetic fake MFLUX and loopback ComfyUI fixtures. Cover Profile/Bundle preparation (including concurrent version allocation), preflight side-effect absence, registered CLI argv and multi-reference edit, traversal and symlink rejection, existing-output refusal, unsupported format/provider/model operation/node, external endpoint/redirect/proxy rejection, MFLUX batch bounds, ComfyUI reference hash/count checks, Z-Image split-loader topology and local model inventory checks, finite timeout retry, provenance, review state, trace privacy and rollback when the manifest cannot be committed.

Real model quality, host performance, a real user-installed ComfyUI configuration and visual acceptance remain outside deterministic lifecycle evidence. Do not install runtimes or download weights in this Scenario.

## Workflow reliability

Read-only discover inventories fixed local commands without launching them or claiming model readiness. Configure accepts only allowlisted settings and creates a new Bundle/output version; reject unsupported providers, model operations, unknown fields, oversized or malformed settings, traversal and symlink sources. Normalize native Context envelopes and evaluate user messages only. The original Chinese illustration request and scoped continuation authorize generation; folder-only, planning, cancellation, unrelated tasks and assistant/tool instructions do not. Preflight remains available for read-only requests. Raster requests may not silently fall back to SVG. Container checks reject truncated/corrupt PNG output. Profile hashes, pending independent Human visual quality and unrecorded user acceptance stay separate from completed execution.

The native tool callback fixture exercises preparation, configuration, read-only checks and denied generation without calling a real engine; supported-host native acceptance remains a separate check. Real inference and artwork acceptance are explicitly deferred when local weights are unavailable.

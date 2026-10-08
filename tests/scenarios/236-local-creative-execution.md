# Scenario 236: Local Creative Bundle Execution

## Context

A creative task may request generation or editing in a local non-Git workspace. The user has an existing MFLUX installation or a local ComfyUI server and chooses an exact output scope. Model/runtime provenance and independent visual review must remain visible.

## Deterministic expectations

- `aips creative preflight` validates a versioned EPHEMERAL Bundle, confined paths, no-overwrite output, local model/runtime provenance and configured engine without starting a generation job.
- A missing or unavailable engine returns `BLOCKED_NO_ENGINE`. Preview, repository validation and the Integration Gate never execute a user-configured engine.
- `aips creative execute` runs only after explicit invocation, only in a non-Git EPHEMERAL workspace, and writes PNG/JPEG/WEBP plus a new manifest beneath the declared output scope.
- MFLUX uses a fixed argv-only command, `shell=false`, local model path and offline model-hub environment. Inputs and outputs are not passed to a cloud service.
- ComfyUI requests use HTTP loopback only, disable proxies, reject redirects and accept only the declared built-in nodes. Edit checks that the staged ComfyUI input bytes match the selected project reference.
- Existing files, manifests and source references are never overwritten. Retries are bounded and apply only to transient timeouts; provider failure never becomes `COMPLETE`.
- The manifest binds bundle/workflow/input/output hashes, model revision, runtime/version, license source and measured elapsed time. Visual review begins `PENDING` and requires an independent Human PASS/REVISE decision.
- Trace accepts only bounded enums, timestamps, attempts, elapsed time, and hashes; prompt, image data, credentials, workflow bodies and filesystem paths are rejected.

## Lifecycle evidence

Use synthetic fake MFLUX and loopback ComfyUI fixtures. Cover preflight side-effect absence, generation/edit, traversal and symlink rejection, existing-output refusal, unsupported format/provider/node, external endpoint/redirect/proxy rejection, reference hash mismatch, finite timeout retry, provenance, review state, trace privacy and rollback when the manifest cannot be committed.

Real model quality, host performance, a real user-installed ComfyUI configuration and visual acceptance remain outside deterministic lifecycle evidence. Do not install runtimes or download weights in this Scenario.

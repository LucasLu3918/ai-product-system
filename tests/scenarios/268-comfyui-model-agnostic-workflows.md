# Scenario 268 — Model-Agnostic ComfyUI API Workflows

## Given

- A non-Git EPHEMERAL Creative workspace and a user-provided ComfyUI API-format workflow.
- A local ComfyUI endpoint at an explicit loopback IP and port.
- Runtime `/system_stats` and `/object_info` responses that describe the workflow's nodes, inputs, outputs and model choices.
- An opt-in Bundle `comfyui.mode: dynamic_local` with explicit bindings for every user-controlled field.

## When

- The user scans local capabilities, imports a workflow, inspects it, runs read-only preflight, or explicitly executes a preflight-ready Bundle.

## Then

- A model filename absent from AIPS registries is accepted only when the runtime loader schema lists it.
- Schema-valid reviewed ComfyUI core nodes and new core topology are not rejected by model-family or node-count templates.
- Missing nodes/components, invalid links/fields, ambiguous or absent required bindings, unsafe paths, API nodes and unreviewed custom nodes fail closed with stable diagnostics.
- Scan/import/inspect/preflight use no `/prompt` request. Execute performs at most one `/prompt` POST.
- A lost response after submission returns recovery-required and never retries automatically; known `prompt_id` is retained when available.
- Only bound inputs change; unbound steps, CFG and template defaults remain unchanged. Model fallback and external providers are never selected silently.
- Imported workflow files are bounded and create-only in a non-Git EPHEMERAL workspace. Cache stores private fingerprints only; no project-local cache is created.
- Output remains confined and create-only, with PNG prompt metadata stripped and hashes recorded in the existing manifest.
- Synthetic lifecycle evidence is labeled as synthetic; actual model inference remains `UNVERIFIED`.
- Existing fixed checkpoint and Z-Image profiles retain their legacy validation and execution behavior.

## Evidence

- `scripts/comfyui_capabilities.py`
- `scripts/comfyui_workflow.py`
- `scripts/comfyui_workflow_policy.py`
- `scripts/creative_execution.py`
- `tests/evidence/comfyui_dynamic_workflow_lifecycle.py`
- `tests/validation/comfyui_dynamic_workflow_contracts.py`
- `tests/evidence/creative_execution_lifecycle.py`
- `tests/validation/creative_execution_contracts.py`

## Limits

- This scenario uses a synthetic loopback ComfyUI server; it does not load weights, install nodes, or verify GPU/MPS inference.
- AIPS trusts only runtime-identified built-in ComfyUI modules and denies API/custom/unknown modules. HTTP metadata cannot prove that a third-party node is non-exfiltrating.

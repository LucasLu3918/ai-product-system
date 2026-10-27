# Core Change Proposal: Dev Friction PR6 — Declarative Topology Templates and Two-Layer ComfyUI Profiles

## Approved outcome

Move the ComfyUI node graphs for Z-Image Turbo and FLUX 3 Klein out of hard-coded executor validators into audited template data, checked by one generic validator. Keep the system profile registry as the reviewed source for model registration (D9). Add user-local profiles under the AIPS config home that may reference only an audited template id and bounded values (D5). A user-local profile is drafted from installed weight file names with `aips creative profile draft`, and becomes usable only after `aips creative profile approve` completes an interactive host confirmation (D12). Default ON for the template validator; user-local profiles exist only after an explicit approval.

Core Change Approval: the human user approved the full dev-friction plan scope including D5, D9 and D12. This record applies that approval to exactly the PR6 scope below.

## Scope

- `templates/creative/COMFYUI_TOPOLOGY_TEMPLATES.yaml` (new): audited template data for `z_image_split_loader` and `flux3_klein_t2i` (schema below).
- `scripts/comfyui_topology.py` (new): generic template normalizer and workflow validator. It checks node class counts, exact input keys, selector-based node identity, links, fixed values, profile and component bindings, inventory sources and the TextGenerate schema gate. It has no trust decisions.
- `scripts/creative_profiles.py` (new): user-local profile store. Draft, approval record, hash-bound loading, static smoke check and the interactive approval gate.
- `scripts/creative_execution.py`:
  - Executor-owned `COMFY_TOPOLOGY_TEMPLATE_IDS`; template data may only describe these ids.
  - `load_comfy_topology_templates`, `load_comfy_profile_with_layer` (system registry first, then approved local profile), `validate_local_profile_document` and `validate_local_profile_body`.
  - `load_comfy_workflow`, `verify_comfy` and `validate_final_comfy_workflow` now use the template for topology, inventory and TextGenerate gating. Hard-coded Z-Image and FLUX branches are removed.
  - `build_comfy_workflow` extracted as a pure function (no I/O) from `comfy_execute`; `comfy_execute` still submits exactly once.
  - Preflight reports `model_profile_layer` when a profile is used.
  - CLI: `profile draft` and `profile approve`.
- `scripts/creative_errors.py`: Traditional Chinese recovery text for the new reason codes; allowlist for `failed_components` and `model_profile_layer`.
- `scripts/aips_cli/dispatch.sh`, `scripts/aips_cli/help.sh`: route and document `creative profile draft|approve`.
- `tests/test_creative_topology_templates.py` (new, 21 unit tests), `tests/fixtures/creative_topology/golden_cases.py` (new, shared case definitions) and `tests/fixtures/creative_topology/golden_before_refactor.json` (baseline captured from the executor before the refactor).
- `tests/validation/creative_execution_contracts.py`: string contracts updated to the template-driven form (the Z-Image check now tests the template data and the local-profile validator).
- `tests/fixtures/plan21-contract-golden-vectors.yaml`: the pinned stdout digest of `aips --help` and `aips help` is updated for the two additive usage lines.
- `tests/scenarios/271-audited-topology-templates-and-local-profiles.md` (new) and `tests/scenario_coverage.yaml`; `docs/human/CONFORMANCE_CURRENT.md` regenerated.
- Docs (one localized sentence each, in each file's own language): Human docs `USER_GUIDE`, `TECHNOLOGY_GUIDE`, `ARCHITECTURE_OVERVIEW`, `MAINTENANCE`, `DOCUMENTATION_MAP`, `DOCUMENTATION_SYNC`, `index`, `CONFORMANCE`, `HARNESS`, `INSTALLATION`, `SECURITY_ASSURANCE`, `docs/ARCHITECTURE.md`; Agent docs `CREATIVE_DIRECTION`, `CONFORMANCE`, `DOCUMENTATION_SYNC`, `HARNESS_PROTOCOL`, the OpenCode `AGENTS` and `COMPATIBILITY`, `RESOURCE_AUTHORIZATION`, `RUNTIME_POLICY_ENFORCEMENT`, `EXECUTION_ISOLATION`, `ORCHESTRATOR`.
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` is intentionally not edited; matrix entries are reported to the integration owner.

## Template schema (version 1)

- `clip_type`: CLIP type every CLIPLoader must carry; a profile's `clip_type` must equal it.
- `components`: profile file-name components. Each must be referenced by a binding, inventory entry or selector, so no declared component is unused.
- `upsampler`: boolean; when true, the profile may carry `upsampler.*` values.
- `runtime_schema_class`: optional class whose live `/object_info` schema must cover the prompt node (FLUX 3 uses `TextGenerate`).
- `roles`: `prompt` ({node, field}), `latent`, `sampler`, `save` as logical node names.
- `nodes`: logical name to `{class_type, inputs, select?}`. `inputs` is the exact input key set. `select {field, component}` is required when a class appears more than once; the node is the one whose field equals the configured component value.
- `links`: `"node.field": "source.index"`; the input must equal `[source node id, index]`.
- `bindings`: each entry targets one node or every node of a class and uses one source: `component` (configured file name), `profile` (`clip_type` or `upsampler.max_length`), `profile_group` (every non-null key of the sampler group), `value` (literal, quoted where YAML would coerce it) or `constraint: nonempty_string`.
- `inventory`: local model-list checks, each naming a class, a field and a component or profile source.

Load-time rules: template ids must equal the executor-reviewed set; every node class must be in `COMFY_CORE_NODES`; `LoadImage`, `LoadImageMask`, `VAEEncode`, `VAEEncodeForInpaint` and `SetLatentNoiseMask` are denied; exactly one `SaveImage`; every repeated class needs a selector; every link, binding and inventory reference must resolve. Any violation fails closed with `comfy_topology_template_invalid`.

## User-local profile restrictions

- Location: `$XDG_CONFIG_HOME/aips/creative/profiles/<id>.yaml` (default `~/.config/aips/`); approvals in `creative/profile-approvals.json`. Ids must match `local-[a-z0-9-]`, so they cannot shadow a system id.
- Allowed keys only: `version`, `profile_id`, `status`, `model_id`, `topology`, `operation` (must be `generate`), `components` (basenames only), `clip_type`, `sampler`, `upsampler`, `runtime_budget`. Any other key, including `nodes`, `links`, `inputs`, endpoints or input images, is refused with `profile_local_restricted`.
- `topology` must be an executor-reviewed template id. Sampler, upsampler and runtime-budget values are validated against the same family ranges and executor ceilings as system profiles.
- A local file is used only when `status` is `APPROVED` and the approval record's SHA-256 equals the current file bytes. Any edit after approval makes it unusable until re-approved.

## Draft and approve flow

- `aips creative profile draft --model-id <id> --base-profile <system id> [--profile-id] [--models-dir] [--component KEY=FILE]`. The model id must be explicit. The base must be a system profile; its topology, clip type, sampler, upsampler and runtime budget are copied. Component file names come only from the local models directory (`diffusion_models`/`unet`, `text_encoders`/`clip`, `vae`; `.safetensors` or `.gguf`). A unique match, or a name listed by the base profile, is chosen; otherwise the draft refuses (`profile_component_ambiguous`) and asks for `--component`. No download, no network, no model switching. Output is `UNAPPROVED` with profile id and file names only.
- `aips creative profile approve <id> [--models-dir]`. Refused first when stdin or stderr is not a terminal (`profile_approval_requires_tty`). Then the draft is validated, a static smoke check confirms every component file name is installed (no ComfyUI call, no inference), and a summary is printed to stderr (profile id, template id, file names, sampler values, runtime budget). The user must type `APPROVE <id>` exactly; anything else is declined with no record. The approved file is written atomically with `status: APPROVED`, and the approval record stores its hash, template id, file names and time.
- No flag skips confirmation. Prompt text, absolute paths and network details never appear in output.

## Equivalence results

Captured from the pre-refactor executor (`golden_before_refactor.json`) and compared through `run_cases` in the new unit test:

- Z-Image Turbo, FLUX 3 Klein Base and FLUX 3 Klein Distilled: identical provider summary (prompt id, prompt field, save nodes, latent and sampler ids, resolved profile) and identical final API prompt, for the reference Bundle and for a second Bundle variant (prompt, seed, dimensions, steps).
- 34 single-field mutations: 23 keep identical outcomes; 10 FLUX mutations that break a fixed value or a profile binding now report `comfy_model_profile_invalid` instead of `comfy_workflow_topology_invalid` (documented normalization, since they are binding failures); 1 mutation (`batch_size: true`, a boolean used as an integer) is now rejected.
- Behavior intentionally tightened: a repeated CLIPLoader class whose selector matches two nodes is rejected; boolean values are never accepted as integers.

## Why the security floor is not weakened

- `scripts/comfyui_workflow_policy.py` and `COMFY_CORE_NODES` are unchanged. Template classes must be core-allowlisted, input-image classes are denied at template load, and no template can add an endpoint, node, input image or operation.
- Loopback-only requests, the single explicit `/prompt` submission, no weight downloads and no model switching are unchanged. Draft and approve make no network request (the unit test patches `socket.socket`).
- Local profiles can never override or add a topology; the agent cannot approve (no TTY) and cannot select a profile that is not already approved.
- Secret, PII and content scanning, publication, and merge confirmation are untouched.
- Diagnostics: profile ids, reason codes and weight file names only; no prompt text, no absolute paths.

## Defaults and compatibility

- System profiles resolve through the template validator by default with identical workflows.
- A user-local profile has no effect until approved; no existing Bundle changes behavior.
- `aips --help` and `aips help` gain two additive usage lines; the pinned stdout digest in the plan21 contract fixture is updated accordingly.
- Preflight adds `model_profile_layer` only when a profile is used.

## Out of scope

Edit-class models (D13), the restricted import of new topologies (D5 second half, PR11), profile switching CLI (PR10), host-level blocking of agent-driven approval (PR3 guard), and any change to ComfyUI itself.

## Verification

- `ruff check` clean on every changed Python file.
- `python -m unittest tests.test_creative_topology_templates`: 21 tests pass (template validation, equivalence, user-local restrictions, draft/approve gating, non-TTY refusal).
- `python -m pytest -q tests`: 227 passed, 252 subtests passed.
- `python tests/validate_repository.py`: VALIDATION PASSED (270 scenarios).
- `python scripts/capability_registry.py check`: 45 capabilities valid.
- `python scripts/documentation_sync.py --files ...`: valid; `python scripts/documentation_placement.py`: PASSED.
- Creative evidence: `creative_execution_lifecycle`, `comfyui_dynamic_workflow_lifecycle`, `plan27_lifecycle`, `creative_generate_set_lifecycle`, `creative_quality_lifecycle`, `creative_repair_lifecycle`, `creative_render_lifecycle`, `creative_quality_benchmark_lifecycle`, `creative_request_policy_lifecycle` all exit 0.

## Human approval

- Core Change Approval: the human user approved the full dev-friction plan scope including D5, D9 and D12; this record applies it to exactly the PR6 scope above.
- Publication: not requested; no push, PR or merge.

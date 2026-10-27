# Scenario 271 — Audited Topology Templates and Two-Layer ComfyUI Profiles

## Given

- The repository system profile registry and the audited topology template data for Z-Image Turbo and FLUX 3 Klein.
- A temporary local models directory with synthetic weight file names and a temporary AIPS config home.
- A loopback-only ComfyUI workflow fixture; no real ComfyUI server, weight download or model inference.

## When

- A registered system profile resolves a reference workflow, or a mutated workflow is checked against its template.
- A person drafts a local profile from installed weight names, or approves a draft in an interactive terminal.
- A local profile is loaded for a Bundle.

## Then

- Every registered system profile resolves to the same provider summary and final API prompt as the pre-refactor baseline. Mutations keep their outcomes, except for the documented reason-code normalization and the rejection of boolean values used as integers.
- Template data cannot add a template id, a node class outside the core allowlist, an input-image node, or a second save node; a patched or malformed template fails closed.
- A user-local profile is accepted only when it references an audited template, sets values within the family ranges, names weight files without path components, and matches an approval record for its current bytes.
- Draft writes only an `UNAPPROVED` file from installed file names; it never downloads weights or opens a network socket, and it refuses to overwrite a draft or reuse a system profile id.
- Approve refuses without an interactive terminal and writes nothing. A mismatched confirmation phrase is declined without an approval record. A correct phrase records a hash-bound approval after a static smoke check of the installed weight names.
- Diagnostics contain profile ids and file names only, with no prompt text or absolute paths.

## Evidence

- `scripts/creative_execution.py`
- `scripts/comfyui_topology.py`
- `scripts/creative_profiles.py`
- `templates/creative/COMFYUI_TOPOLOGY_TEMPLATES.yaml`
- `tests/fixtures/creative_topology/golden_before_refactor.json`
- `tests/test_creative_topology_templates.py`
- `tests/validation/creative_execution_contracts.py`

## Limits

- The smoke check is static: it confirms installed file names only. It does not run inference, so model quality and backend compatibility remain `UNVERIFIED`.
- The non-interactive refusal is enforced by the executor. Host-level blocking of agent-driven approval depends on the installed guard and is not proven here.

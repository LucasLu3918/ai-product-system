# Dev Friction PR6 System Improvement Review

## Recommendation

**Appropriateness: appropriate, with the approval gate's enforcement boundary documented.** Adding a local model meant editing a Python validator and taking a Core Change. The change moves each audited node graph into data checked by one generic validator, so a new model is a registry or local profile entry rather than a code change. A local profile can only reference an audited template, and its use requires an interactive approval recorded against the exact file bytes.

**Lower-layer alternative:** keeping the topology checks in Python and only adding profile data was rejected, because the node graph itself still needed a code change for each new topology. Template data is validated by the executor at load time (reviewed ids, core node allowlist, denied input-image classes), so the data layer cannot widen the trust boundary.

**Residual limitations:**
- **Approval enforcement is layered, not absolute.** The executor refuses approval without a terminal (`isatty` on stdin and stderr). A determined local process could fake a terminal. The approval record and profile file are plain local files, so an agent with direct write access could edit both. Both are outside this change; the PR3 guard that blocks Edit/Write/Bash writes to the AIPS config and install directories is the intended control, and it is not verified in this branch.
- **Static smoke only.** The approval smoke check confirms installed file names. It never runs ComfyUI or inference, so model quality and backend compatibility remain UNVERIFIED.
- **Template review is human.** The executor cannot prove that a template's graph is the intended model. Golden equivalence tests detect drift in the shipped templates, but a reviewed template change still needs a Core Change.
- **Runtime budgets are copied, not calibrated.** A draft copies its base profile's runtime budget. The approval summary shows it so the approver can see it.
- **Reason-code normalization.** Ten FLUX fixed-value and binding failures now report `comfy_model_profile_invalid` instead of `comfy_workflow_topology_invalid`. Consumers keyed on the old code for those cases must update; no shipped test or document asserted it.

**Security and reliability:** loopback-only, no egress, node trust policy and core allowlist untouched, no download, no model switching by the agent, no network in draft or approve, single submission unchanged. Local profiles can never add a topology, node, input image or endpoint. Diagnostics are privacy-bounded: profile ids, reason codes and weight file names only.

**Compatibility:** system profile workflows are identical to the pre-refactor executor (equivalence test per profile). The CLI help adds two additive lines and the plan21 pinned digest is updated. Contract checks in `tests/validation/creative_execution_contracts.py` now test the template data instead of the removed Z-Image literal.

**Documentation impact and placement closure:** `documentation_sync.py` reported findings for `character-artwork-workflow`, `harness`, `skills-list-cli`, `plan39-comfyui-resource-authorization-diagnostics` and `resource-authorization`. Each required Human and Agent document received one localized sentence, and `docs/human/CONFORMANCE_CURRENT.md` was regenerated for Scenario 270. The final check reports valid; `documentation_placement.py` reports PASSED. The Technology Guide review requirement is met by its sentence.

**Test-matrix handling:** `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` is not edited in this branch; entries are reported for the integration owner.

**Architecture diagrams:** the local profile flow (draft, then approve with terminal confirmation, then hash-bound load) adds a dataflow; no trust boundary changes beyond the existing config-home use.

**Constitution impact: NO.**

**Deferred:** edit-class models (D13), profile switching CLI (PR10), restricted import of new topologies (PR11), and host-level blocking of agent-driven approval (PR3).

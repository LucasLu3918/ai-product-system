# Plan26 Phase 1 — Creative Prompt Compiler Extraction

## Purpose

Extract the deterministic profile-to-prompt and evidence-ranked model recommendation functions from the large Creative executor into a focused internal module, while keeping the existing `creative_execution` import surface, exception identity, and outputs unchanged.

## Why this is a core/large change

These functions feed local generation and review-assist requests. A changed prompt changes its recorded fingerprint and can change generated images, so the extraction requires exact output-parity evidence and the Core Change Gate even though the code is a private pure-function boundary.

## Proposed Scope

### In scope

- Move `_profile_lines`, `_profile_mapping`, `compile_creative_prompt`, and `model_recommendation` into `scripts/creative_prompt_compiler.py` without changing their logic or output.
- Move the existing `Blocked` exception class into `scripts/creative_errors.py`; import and re-export the same class object from `scripts/creative_execution.py` so the compiler can remain independent of the executor.
- Import and re-export the same `compile_creative_prompt` and `model_recommendation` function objects from `scripts/creative_execution.py`.
- Preserve execution and `review_assist` callers through that facade.
- Add exact deterministic output-parity evidence, facade function/class identity checks, and invalid-prompt exception parity.
- Update the validator registry, implementation contract, changelog, and source architecture description for the internal module boundary.
- Synchronize the user-approved recursive documentation closure in the canonical creative, Harness, conformance, documentation-governance, and maintenance topics; record unaffected architecture diagrams with a concrete reason.

### Out of scope

- Real image generation, model or provider changes, or new image benchmark cases.
- Changes to creative profiles, Bundle schemas, authorization, storage, telemetry, or external egress.
- Any of Plan26's other 11 workstreams.

## Expected Files / Modules

- `.aips/review/PLAN26_PHASE1_CREATIVE_PROMPT_COMPILER_PROPOSAL.md` (this proposal)
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`
- `scripts/creative_prompt_compiler.py` (new)
- `scripts/creative_errors.py` (new)
- `scripts/creative_execution.py`
- `tests/evidence/creative_quality_lifecycle.py`
- `tests/evidence/module_extraction_lifecycle.py`
- `tests/validation/creative_execution_contracts.py`
- `tests/validation/registry.py`
- `CHANGELOG.md`
- `docs/ARCHITECTURE.md`
- `docs/human/ARCHITECTURE_OVERVIEW.md`
- `docs/human/CONFORMANCE.md`
- `docs/human/DOCUMENTATION_MAP.md`
- `docs/human/DOCUMENTATION_SYNC.md`
- `docs/human/HARNESS.md`
- `docs/human/INSTALLATION.md`
- `docs/human/MAINTENANCE.md`
- `docs/human/TECHNOLOGY_GUIDE.md`
- `docs/human/USER_GUIDE.md`
- `docs/human/index.md`
- `harness/HARNESS_PROTOCOL.md`
- `harness/adapters/opencode/AGENTS.md`
- `harness/adapters/opencode/COMPATIBILITY.md`
- `orchestration/CONFORMANCE.md`
- `orchestration/CREATIVE_DIRECTION.md`
- `orchestration/DOCUMENTATION_SYNC.md`

No scenario or schema change is expected: existing Scenario 234/236/238 and the Creative quality lifecycle already cover the behavior. If implementation uncovers a missing contract, stop and revise this boundary before adding files.

## Impact

### Architecture / Contracts

The new module is an internal pure-logic leaf. `creative_execution` remains the stable import facade. Its direct consumers are `preflight`, `execute`, `review_assist`, and `tests/evidence/creative_quality_lifecycle.py`; source references were checked directly. The bounded Project Intelligence traversal found inferred caller edges, hit its depth/edge limit, and could not map the architecture seed. This proposal therefore makes no repository-wide graph completeness claim; the private-leaf impact policy and focused facade/subsystem evidence apply.

### Data / Migration

No persisted data, format, cache, or migration changes.

### Security / Reliability

No new I/O, subprocess, network, credential, authorization, or telemetry behavior. Preserve the exact compiled prompt and model recommendation results to avoid generation or evidence drift.

### Compatibility / Rollback

Keep `creative_execution.compile_creative_prompt` and `creative_execution.model_recommendation` as the same function objects exported by the new module, and keep `creative_execution.Blocked` as the same exception class exported by the neutral errors module. The existing CLI, Bundle, OpenCode adapter, manifest, and return contracts remain unchanged. Revert the module extraction as one commit if parity fails.

### Tests / Validation

Impact-derived Test Matrix:

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| Prompt compiler, shared error type, and facade | REQUIRED | Exact prompt/advice hashes + invalid-prompt reason | Creative quality/execution lifecycle | Function and exception identity | Local native host acceptance | Secret scan | N/A — no persisted data | Facade identity + creative CLI consumers | Architecture + changelog; schema N/A | Internal pure-module extraction |

Required evidence: exact prompt and model-recommendation output parity; shared `Blocked` class identity and invalid-prompt reason parity; creative quality and execution lifecycle; OpenCode native acceptance; full repository validation; documentation validation; mandatory candidate secret scan; exact-candidate Integration Gate.

Real model inference is N/A for this behavior-preserving extraction; generated output is not used as a substitute for deterministic parity evidence.

Recompute trigger if scope expands: any function logic/output, profile schema, execution/provider, authorization, persistence, or additional Plan26 item changes.

Required release/CI evidence: required `repository` check on the exact PR candidate and a passing exact-candidate Core Integration Gate.

### Secret / Credential Impact

Secrets required: NO

Approved acquisition mechanism: N/A

Leakage/redaction review: Run the mandatory credential-free candidate strict scan.

Rotation/revocation plan if exposure is found: N/A; stop publication and follow the repository secret-handling policy if a finding occurs.

### Documentation / Diagrams

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` Mermaid: N/A — no flow changes; update the source module description.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: update the Creative Workflow explanation with the private compiler module and preserved facade; no diagram topology changes.
- Human SVG architecture/lifecycle diagrams: N/A — no runtime, Harness, installation, or delivery flow or boundary changes.

## Risks

- A changed prompt alters its fingerprint and may change generated image results; exact output-parity evidence blocks this.
- A facade import could accidentally wrap or duplicate function objects; explicit identity assertions block this.
- A reverse dependency from the compiler to the execution facade could create a cycle; the shared exception class lives in a neutral module and is re-exported unchanged.
- Project Intelligence has incomplete global consumer coverage; the change remains a private leaf and direct callers are manually reviewed.

## Recommendation

This bounded extraction is approved as the first independently verifiable Plan26 code change. Continue to keep real image validation and the other Plan26 workstreams separate.

## Proposed Implementation Order

1. Capture baseline deterministic output fingerprints from the current functions.
2. Move the shared exception class into `creative_errors.py`; extract the functions without logic edits and re-export the same objects through `creative_execution`.
3. Add exact parity, exception behavior, and facade-identity assertions; update the validator path registry.
4. Update source architecture documentation and the Core Change Test Matrix.
5. Run focused lifecycle/contract checks, native OpenCode acceptance, repository validation, strict secret scan, and the exact-candidate Core Integration Gate.
6. Reconcile the final file set and present the exact candidate for publication approval.

## Approval

Status: APPROVED
Approved by: User
Approved at: 2026-10-10T00:40:28+08:00
Approval record: User approved the compiler extraction proposal and neutral `Blocked` exception module, then explicitly approved the exact 16 documentation paths required by recursive publish impact in this Codex conversation.
Proposal fingerprint: sha256:8f437107b468b53faf43ba4a2343c0d9572fe20d1efc340dae28e0bc8fb039cf
Scope fingerprint: sha256:4f11a05249d03782f9a73c3ef8e6489847b2c0b9e2f2685e213fd7e6dd4570d3

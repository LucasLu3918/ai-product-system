# Core Change Proposal: Trusted Creative Grants and Multi-Item Local Generation

## Purpose
Fix the authorization and workflow gaps in the approved design3 review. OpenCode V2 prompt admission will create session-scoped grants from admitted user input, independently of bounded model Context. Extend the existing creative executor with bounded collection generation, local engine health selection, per-item status and safe resume.

## Why this is a core change
This changes the creative authorization boundary, OpenCode runtime integration, executor orchestration and persisted output lifecycle. It affects user authority, local file creation, privacy, provider execution and failure recovery.

## Proposed Scope

### In scope
- Capture trusted prompts once at OpenCode V2 prompt admission; create/revoke a transient grant bound to session, message ID, Session-root output scope, allowed actions, inferred bounded output count and prompt SHA-256 digest. Store no raw prompt in the grant.
- Validate grants independently of the last 64 model messages. Preserve read-only discover/preflight without a grant and distinguish authorization, engine and generation errors.
- Extend the executor and CLI with one bounded generate-set workflow over already prepared/configured Bundles: fixed local engine health, collection/job templates, per-item preflight, sequential execution, durable job results and safe resume.
- Preserve create-only outputs, local-only/offline providers, path confinement, prompt/image trace privacy and separate Human visual review.
- Add OpenCode V2 native-hook acceptance, lifecycle tests, scenario, exact Core Matrix, docs and generated projections.

### Out of scope
- New Role, Skill, Capability authority, MCP server, image engine, cloud fallback, model download, arbitrary subprocess, remote ComfyUI, overwrite, automatic visual-quality approval or Constitution amendment.
- Real model inference in CI or automatic visual-quality claims.
- Changes to unrelated Harness adapters or general file-write governance.

## Expected Files / Modules
- OpenCode: harness/adapters/opencode/plugin.ts, AGENTS.md, COMPATIBILITY.md.
- Authorization, executor and CLI: scripts/creative_request_policy.py, scripts/creative_execution.py, scripts/opencode_trace.py, scripts/aips_cli/dispatch.sh, scripts/aips_cli/help.sh.
- New schemas: templates/creative/CREATIVE_COLLECTION_PROFILE.yaml, templates/creative/CREATIVE_JOB_MANIFEST.yaml.
- Tests: creative/OpenCode lifecycle and contract files, new set lifecycle and Scenario 238.
- Docs/config: Creative Direction, Harness/architecture/user docs, documentation closure, capability/architecture projections, VERSION and CHANGELOG.md.
- Governance evidence: this proposal and .aips/review/CORE_CHANGE_TEST_MATRIX.yaml.

## Impact

### Architecture / Contracts
Add a native prompt-admission input and transient task-grant contract; extend creative tool and CLI actions additively; add versioned collection/job data; preserve Bundle v1 and current single-item behavior.

### Data / Migration
No migration of existing Profiles, Bundles or per-image manifests. New collection and job manifests are create-only. Resume validates Bundle, output and provenance-manifest hashes, recovers completed outputs after a checkpoint interruption, and processes only incomplete items.

### Security / Reliability
Grant creation is exclusively from native admitted user text, not model Context or tool arguments. Bind grants to session/workspace, revoke on cancellation/unrelated prompt, enforce actions/count/scope, and fail closed after restart. Preserve offline local providers, bounded retries, atomic publication and trace redaction.

### Compatibility / Rollback
Existing CLI/tool actions remain. Existing Bundle v1 stays supported. No release is cut by this change; VERSION remains at the latest released version and the entry is recorded under Unreleased. Revert is code-only; user-created workspaces are not automatically deleted.

### Tests / Validation
Matrix covers grant authority/revocation/context truncation, scope/count, atomic set creation, engine probing, partial failure/resume, concurrency, privacy, no-cloud/no-download, OpenCode callback integration, CLI compatibility, docs/projections, full repository validation, secret scan and exact-candidate Integration Gate. Real model inference is N/A for software boundary validation.

### Documentation / Diagrams
- docs/ARCHITECTURE.md Mermaid: AFFECTED — creative authorization and job flow change.
- docs/human/ARCHITECTURE_OVERVIEW.md: AFFECTED — update OpenCode and creative flow.
- Human SVG diagrams: N/A — Mermaid is canonical; no SVG depicts this boundary.

## Risks
- Prompt-hook API/version differences may prevent native grant capture; fail closed and mark host acceptance unverified if unsupported.
- Batch generation can leave partial results; resume must preserve validated completed outputs.
- Discovery must never trigger downloads or non-local fallback.
- Host OpenCode projection currently reports CONFLICT/UNVERIFIED; this change will not repair user-global configuration.

## Recommendation
Extend the existing executor and OpenCode plugin. Add no new Role, Skill, Capability authority or policy engine. Keep grants transient and scoped.

## Proposed Implementation Order
1. Add grant validator and prompt-admission capture with negative-path evidence.
2. Add local engine health discovery and atomic set/job orchestration with resume.
3. Integrate bounded tool/CLI and OpenCode callback acceptance.
4. Update docs, scenarios, projections and Core Matrix.
5. Run focused evidence, full local Integration Gate and publication preflight.

## Approval
Status: APPROVED
Approved by: user
Approved at: 2026-10-09
Approval record: User message “核准此變更邊界” in this task.
Proposal fingerprint: pending final exact scope hash
Scope fingerprint: pending final changed-file reconciliation

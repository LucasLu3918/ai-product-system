# Core Change Proposal: Local Creative Execution

## Purpose and classification

This Core Change adds an AIPS-owned, local-only execution boundary for existing creative profiles and OpenCode workflows. It closes two concrete gaps: the OpenCode Shell Guard denied useful bounded AIPS diagnostics, and creative bundle execution lacked a scoped preflight, auditable local providers, and a human visual-review boundary.

## Approved scope

- Add fixed, read-only AIPS diagnostics to the Shell Guard with stable allow/deny reason codes. Do not enable arbitrary shell, Python, or command templates.
- Add a versioned Creative Bundle preflight and explicit execution lifecycle for non-Git EPHEMERAL projects, create-only output paths, and PNG/JPEG/WEBP assets.
- Support an explicitly configured local MFLUX CLI and a loopback-only ComfyUI core-node workflow for generation and reference-based edit. Launch MFLUX with argv and `shell=False`; disable proxy use and redirects for ComfyUI.
- Capture model/runtime/license provenance, reference/output/workflow hashes, bounded measured timing, finite transient retries, and privacy-limited local trace data. Never persist raw prompts or image bytes in trace.
- Require a separate human review decision for visual quality. A new manifest begins `PENDING`; deterministic validation cannot mark an image visually approved.
- Integrate the bounded tool into the OpenCode V2 plugin only for an explicit creative create/modify request, and require preflight before execution.
- Add Scenario 236, focused lifecycle and contracts, documentation, architecture projection, version and changelog evidence.

## Exclusions and limits

- No model/runtime installation, weight download, cloud or paid image API, or external image egress.
- No new Role, Agent, Skill, Capability authority, MCP server, policy engine, Constitution change, or automatic visual-quality judge.
- No Git repository output target, overwrite, arbitrary ComfyUI node, remote ComfyUI host, or arbitrary subprocess.
- No hardware performance or visual-quality claim without an actual configured local engine and independent image review.

## Boundaries and compatibility

The CLI, OpenCode tool, Bundle schema, executor, trace, capability projections, existing character-artifact validation, and human documentation are affected. Existing creative evidence and runtime policy contracts remain additive and compatible. Generated output is confined beneath an explicitly declared EPHEMERAL project output directory; output and manifest creation fail if a path already exists. Provider absence returns `BLOCKED_NO_ENGINE` without fallback.

Trace contains only allowlisted provider/operation/outcome/reason, attempt count, elapsed time and hashes. Manifests retain provenance and hashes but omit raw prompts. ComfyUI is contacted only through a loopback URL, with redirects and proxies disabled; the edit workflow must load the exact staged reference bytes.

## Required evidence

The active `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` binds the final base, changed-file set, and exact-candidate Integration Gate. Focused evidence includes `tests/evidence/creative_execution_lifecycle.py`, `tests/evidence/opencode_integration_lifecycle.py`, registry projection checks, documentation closure/build, strict candidate secret scan, and the full local Gate. Remote PR and post-merge `main` checks remain separate evidence.

## Approval

Implementation scope approved by the user in this task with “核准”. This is not approval to publish a particular candidate; the exact Git Publish Proposal remains subject to the Git Publish Approval Gate.

# PLAN39 — Resource Authorization and Local Creative Diagnostics Core Change

## Purpose

Repair the observable Resource Authorization profile-to-runtime call chain, keep all authorization default-deny, secure the fixed local ComfyUI read-only discovery surface, and provide consistent, redacted recovery diagnostics and creative compatibility presets.

## Why this is a core change

The work touches authorization decisions, native Runtime Policy consumers, provider networking, creative workflow preparation and execution diagnostics, schemas, CLI, test lifecycle, and Human documentation. A selector or destination mismatch could otherwise be misreported or accidentally allowed; local HTTP boundaries and redirects must remain fail-closed.

## Approved scope

The user approved this scope in the current chat on 2026-10-14 (Asia/Taipei).

### In scope

- Trace the profile path from adapter/environment through Runtime Action evaluation; distinguish absent, missing, unreadable, malformed, invalid, and scope-mismatched profiles/grants.
- Match grant kind, selector, operation, destination, and applicable constraints while preserving default-deny.
- Extend existing `aips creative discover` with fixed, read-only ComfyUI capability/model inventory. Enforce loopback IP, port 8188, GET, fixed paths, bounded response, proxy bypass, and redirect refusal.
- Preserve separate authorization and workflow validation for image generation. Do not add arbitrary shell, external download, or non-allowlisted Custom Nodes.
- Normalize errors with `status`, `phase`, `reason_code`, `source`, `retryable`, `trace_id`, and `recovery.action`; redact HTTP/provider details and return Traditional Chinese remediation guidance.
- Add reusable character, background, texture, and UI ornament presets to the existing Creative Bundle/Manifest/Review/Quality flow.
- Add static Apple Silicon/MPS and model precision diagnostics. Never claim actual inference compatibility without observed inference evidence.
- Update impacted schemas, CLI, lifecycle/contract/Scenario/coverage, documentation placement/sync, Traditional Chinese Human guidance, architecture documentation/diagram and changelog as required by final Change Impact.

### Out of scope

- Creating or modifying any authorization configuration on the user's Mac.
- Running image generation, downloading models, adding arbitrary Shell/HTTP tools, third-party nodes, or a second image engine.
- Adding a Role, Gate, authority source, or new generation provider.
- Claiming diagnosis of the user's current local Hook configuration without its denial log.

## Impact and validation

Security boundary risk; preserve pre-execution default-deny and native Human/Host authority. No persisted user data migration is planned. All additions are backward-compatible or additive; reject ambiguous selectors and malformed destinations.

Test Matrix: `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`.

Required evidence includes profile source/error stages, selector/kind/operation/destination/constraint denials, Runtime Action diagnostics, ComfyUI success/model-missing/4xx/5xx/redirect/loopback boundary behavior, redaction, preset schema/CLI behavior, and evidence-ranked MPS diagnostics. Run focused tests during implementation, then the exact-candidate local Integration Gate once. Remote publication requires `aips:core-change`, the exact latest SHA's `repository` required check, and merge to `main` per the user's explicit request.

### Secret / Credential Impact

Secrets required: NO. Use synthetic fixtures only. Do not read or modify user credentials or local authorization profiles. Diagnostics must not emit profile paths, provider bodies, headers, credentials, or unrestricted exception strings.

### Documentation / Diagrams

Architecture Impact: update `docs/ARCHITECTURE.md` and `docs/human/ARCHITECTURE_OVERVIEW.md` where the authorization/discovery/error boundary changes; update relevant Human usage/security guidance and placement/sync registries. Other SVG diagrams are affected only if source architecture diagram structure changes; record final disposition in the matrix.

## Risks and limits

Repository-wide Impact Graph coverage remains API/data/events partial and consumers unknown. A reviewed, seed-scoped graph supports this change only; no global completeness claim is made. The user's Hook denial log is unavailable, so implementation repairs confirmed/reproducible source paths without claiming the Mac's current configuration is the root cause.

## Recommendation and order

Approved for bounded implementation after the user's explicit approval. Implement profile diagnostics and grant matching first; then Runtime Policy normalization; then ComfyUI discovery boundaries and static capability reporting; then presets and docs; finally exact candidate validation and publication checks.

## Approval

Status: APPROVED
Approved by: Human user
Approved at: 2026-10-14 (Asia/Taipei; user approval received in this chat)
Approval record: Explicit selection “核准此範圍（Recommended）” in response to the Core Change boundary question.

# Plan42 Core Change Proposal — Staged Binary Commit Safety

## Purpose

Resolve the staged font rejection and make binary safety failures actionable while preserving fail-closed scanning and existing authority boundaries.

## Why this is a core/large change

The change alters a protected commit-content security boundary, dependency provisioning, parser resource handling, and consumers shared by Git hooks, CLI diagnostics, and publication scanning.

## Proposed Scope

### In scope

- Add bounded, format-aware parsing and metadata extraction for TTF, OTF, WOFF, and WOFF2 using the existing content safety pipeline.
- Recognize formats from staged Git blob bytes and reconcile them with the safe relative filename; reject spoofed, malformed, unsupported, oversized, or incompletely inspected files.
- Check Git blob size before reading the blob; bound parser and decompression work and fail closed on limits.
- Provide stable reason codes, phase, safe relative path or path fingerprint, detected format, sanitized cause class, and actionable Traditional Chinese recovery guidance.
- Keep Hook, `aips safety diagnose commit`, and publication candidate scanning on one compatible format capability and metadata-scan path.
- Manage `fontTools` and WOFF2 Brotli support in the AIPS runtime requirements and tested dependency constraints, with actionable missing-dependency diagnostics.
- Add format, spoofing, corruption, dependency, resource-limit, sensitive-metadata, redaction, index-invariance, and Hook/CLI consistency evidence; update Scenario 263 and canonical documentation closure.
- Preserve Secret, PII, injection, Human Authority, commit authorization, and publication approval behavior.

### Out of scope

- Disabling or bypassing hooks or scans; changing security policy to allow binary content generally.
- Modifying the user's separate `lucas-lab` staged index or removing any staged/worktree file.
- Changing Human Authority, protected branch policy, required checks, release behavior, external services, system Python, or other products.
- Adding font license approval logic; metadata may be reported only as an informational signal if already safely extracted.
- Adding formats beyond the four font formats and currently supported PNG/JPEG/WebP/M4A/MP3.

## Expected Files / Modules

- `scripts/font_metadata.py` (new bounded font parser)
- `scripts/media_metadata.py`, `scripts/governance_guard.py`, `scripts/publication_authority.py`, `scripts/safety_diagnostics.py`, `scripts/publish_preflight.py`, `scripts/check_secret_leakage.py`
- Runtime/test dependency manifests and tested constraints
- Focused safety tests, Scenario 263, validation registration where required, documentation placement/sync and canonical human/system docs
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` and this proposal

## Impact

### Architecture / Contracts

Reuse the existing staged scanner, `safe_emit`, diagnostic schema, CLI and Hook. Extend binary format inspection as one shared capability. Keep parser errors classified without surfacing raw library messages or content.

### Data / Migration

No persistent application schema. Runtime dependency installation gains the font parsing dependency. Existing indexes and project data remain unchanged.

### Security / Reliability

Adds parser attack surface; mitigate with a strict input size cap, format/magic validation, narrowly selected metadata tables, parser time/resource limits, and fail-closed handling for missing dependencies or parser errors. Scanner results do not authorize commits or merges.

### Compatibility / Rollback

Previously rejected valid font assets can pass content scanning after parser and content checks pass. Unsupported or malformed binary input remains blocked. Rollback is a revert of the candidate and its dependency-manifest changes; no data migration is required.

### Tests / Validation

See the active Core Change Test Matrix. Validate exact staged Git blobs through the shared Hook/CLI scanner, publication candidate consumer, redaction and no-mutation invariants, package install/doctor diagnostics, focused pytest, documentation contracts, repository validation, and exact-candidate Integration Gate.

### Secret / Credential Impact

Secrets required: NO

Approved acquisition mechanism: N/A

Leakage/redaction review: Scan extracted font metadata through existing strict Secret/PII/Injection detectors. Never include matched values, raw exceptions, raw Git stderr, or absolute local paths in diagnostics.

Rotation/revocation plan if exposure is found: N/A; no credentials are introduced.

### Documentation / Diagrams

Update runtime content-safety, installation/maintenance, diagnostics, Scenario 263, documentation map/sync, and architecture flow text where required by the documentation impact preview.

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` Mermaid: N/A — no component or authority boundary is added; update only if the documentation impact tool identifies an affected diagram.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: N/A — same existing scanner flow; no architecture diagram semantics change.
- Human SVG architecture/lifecycle diagrams: N/A — no new lifecycle or host integration boundary.

## Risks

- Font parser vulnerabilities, decompression/resource exhaustion, or malformed metadata can undermine the safety check; strict limits and fail-closed classification are required.
- Adding dependencies to the managed AIPS environment changes install size and may need a new tested transitive lock set.
- Cross-scanner format drift could create a bypass or inconsistent denial; shared helper and parity tests are required.
- Existing repository CI may have unrelated failing open-PR runs; exact `main` checks and this candidate's required aggregate must be observed independently.

## Recommendation

Extend the existing shared safety pipeline and structured diagnostic model. Use a dedicated font metadata parser behind `media_metadata.py` so font parsing is isolated while all scanners reuse the same format dispatch and content checks. Do not accept by suffix alone.

## Proposed Implementation Order

1. Record approved Change Impact and exact-candidate Core Matrix.
2. Add regression tests for size-before-read, current generic binary denial, and diagnostic gaps.
3. Implement bounded format detection, parser, dependency handling and shared scanner integration.
4. Add diagnostic projection, redaction and CLI/Hook/publication parity tests.
5. Update scenario, canonical docs, dependency constraints, registry projections if required.
6. Run impact reconciliation, security review, focused tests, documentation checks and exact-candidate Integration Gate.
7. Create a single engineering commit, publish a PR to `main`, wait for the required `repository` check, then revalidate exact-head authority and merge under the AIPS gate.

## Approval

Status: APPROVED

Approved by: Human user

Approved at: 2026-10-15 (Asia/Taipei)

Approval record: The user's direct instruction to implement all Plan42 recommendations, locally verify, and complete a remote PR merge to `main` explicitly authorizes the scope above. No scope outside Plan42 is included.

Proposal fingerprint: sha256:5d88413e8d47f60c4594a541f68359659e53d7e37405dae96060fa8aea358128

Scope fingerprint: sha256:3568a78447b6cbd14c252c9bb07a64fe78894f8d08dbd92948a872203c93c74f

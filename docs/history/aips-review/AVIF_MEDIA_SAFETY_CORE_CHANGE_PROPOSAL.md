# Core Change Proposal: AVIF Media Safety

## Purpose

Support AVIF in AIPS staged-content safety without bypassing the existing fail-closed boundary, and return actionable, redacted diagnostics when media cannot be inspected.

## Why this is a core/large change

The change affects a security boundary shared by native commit hooks, the read-only safety diagnostic, candidate/history secret scans, publication preflight, and Creative raster validation. A parser or caller mismatch could miss secrets or allow malformed/unsupported binary content.

## Proposed Scope

### In scope

- Add bounded ISO BMFF/AVIF inspection to the existing `scripts/media_metadata.py` module and expose one local media-format capability registry for current consumers.
- Inspect supported EXIF/XMP metadata as text before deterministic secret/PII/injection scanning.
- Keep the 8 MiB staged-blob limit; unknown, malformed, spoofed, oversized, animated/unsupported, or incompletely inspectable AVIF remains blocked.
- Add stable reason codes, phase/cause class, safe relative-path context and actionable guidance; never expose raw parser exceptions, metadata values, absolute private paths, or secrets.
- Keep the native Hook and read-only CLI on the same staged-content scanner; update candidate/history, publication-preflight and Creative raster consumers.
- Add regression/lifecycle coverage, Scenario 265, Conformance documentation and user recovery guidance.

### Out of scope

- A full AV1 bitstream decoder or claim that metadata/container parsing proves decodability or visual quality.
- Global CI policy redesign, new external/paid parser dependency, expansion of the 8 MiB limit, or changes to commit/publication authority.
- New media formats beyond AVIF or changes to unrelated scanner rules.

## Expected Files / Modules

- `scripts/media_metadata.py`, `scripts/governance_guard.py`, `scripts/check_secret_leakage.py`, `scripts/publication_authority.py`, `scripts/publish_preflight.py`, `scripts/creative_image_validation.py`
- `tests/test_safety_diagnostics.py`, `tests/test_publication_authority.py`, `tests/test_publication_planning.py`, `tests/scenarios/265-avif-media-safety.md`, `tests/scenario_coverage.yaml`
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`, this proposal, affected Human/Agent safety and Conformance documentation, `CHANGELOG.md`

## Impact

### Architecture / Contracts

Reuse the existing media inspection and content-safety path. Add a bounded format registry in the existing media module; no new service, public CLI, persistent schema, or authority path. Preserve existing extractor entry points and current behavior for already-supported formats.

### Data / Migration

No persisted data or migration. AVIF bytes remain in Git; only bounded metadata text is sent to existing deterministic scanners.

### Security / Reliability

AVIF identity requires a valid ISO BMFF file type and AVIF brand. Parse box boundaries and metadata item locations under file, box-count, depth, extent, and metadata limits. Do not scan `mdat` as text. Reject `avis` sequences and unsupported construction methods/features. Any unknown or incomplete structure fails closed. Hook and diagnostic decisions must remain identical, and outputs must redact payloads and raw errors.

### Compatibility / Rollback

No public API break and no dependency addition. Existing formats retain their current parser and policy. Reverting this candidate restores the previous unsupported-AVIF behavior; it does not weaken safety.

### Tests / Validation

See the exact-candidate matrix. Required cases include valid AVIF, uppercase suffix, spoofed signature, truncated/oversized boxes, item extents and metadata bounds, XMP/EXIF test secret, unsupported animation, scanner/diagnostic parity, candidate/history scanning, Creative raster acceptance, redaction, and unchanged Git HEAD/index for read-only diagnosis.

Impact-derived Test Matrix: `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`.

Recompute trigger if scope expands: any new format, parser dependency, scanner sink, CI/workflow policy, increased size limit, authority change, or consumer outside the approved boundary.

Required release/CI evidence: exact-candidate AIPS Integration Gate PASS, repository validator PASS, candidate/history secret scan, documentation/conformance checks, remote PR required checks PASS, and post-merge main Gate PASS.

### Secret / Credential Impact

Secrets required: NO

Approved acquisition mechanism: N/A

Leakage/redaction review: Use deterministic fixtures only. Assert secret sentinels and private absolute paths are absent from Hook, CLI, scanner and validation output.

Rotation/revocation plan if exposure is found: Remove the fixture/candidate value, rotate any real exposed credential, then rescan the exact candidate and history.

### Documentation / Diagrams

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` Mermaid: N/A — internal parser/registry extension within the existing content-safety path; no system boundary or deployment component changes.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: N/A — same reason; update only if diff-based Documentation Impact identifies a stale diagram.
- Human SVG architecture/lifecycle diagrams: N/A — no new workflow or component boundary.

Update the Runtime Content Safety Boundary, Security Assurance, Conformance and user-facing diagnosis/recovery guidance. Run the Documentation Impact Gate and generated Conformance current-view check.

## Risks

- Incomplete AVIF box/item parsing could miss metadata: bound supported variants and fail closed for anything unrecognized.
- Treating brand/suffix as proof of valid image would be unsafe: validate declared structure and item extents, and clearly scope the result to safe metadata inspection, not full decode.
- Parser drift between commit, history and Creative validation could create inconsistent decisions: all callers use the shared format registry and tests cover each sink.
- Diagnostics could leak sensitive data: expose only allowlisted codes, phase, cause class, relative path and format.

## Recommendation

Proceed with the bounded AVIF capability inside the existing media-safety subsystem. Retain all unsupported binary and resource-limit protections.

## Proposed Implementation Order

1. Freeze this proposal and matrix against base `b5b9770902681b97e3824f0fc12c11bbf78535b8`.
2. Implement AVIF parsing and the shared format registry with focused parser tests.
3. Integrate staged commit, candidate/history, preflight and Creative consumers; add safe diagnostics.
4. Add Scenario 265 and documentation closure; reconcile the exact diff and run the full Integration Gate.
5. Publish the exact candidate PR; merge only after all required checks pass and the live base/head still match.

## Approval

Status: APPROVED
Approved by: User
Approved at: 2026-10-18
Approval record: Current conversation — “核准範圍 A”
Proposal fingerprint: sha256:69cd76a827cb1d086d21f214e59718e706b61f5e183d49ba2143997558e1de90
Scope fingerprint: sha256:dcf4d4650cb85b45f4554a3a29ffa1275a56426194be15e703e92597043003ce

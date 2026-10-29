# Scenario 263 — Runtime Content Safety Commit Diagnostics

Supported binary metadata inspection includes PNG/JPEG/WebP/M4A/MP3 and TTF/OTF/WOFF/WOFF2 fonts. Font parsing validates the extension against format signatures, checks input and declared decompressed-size bounds, and scans extracted names/vendor metadata through the same strict Secret/PII/Injection scanner used for text. Missing fontTools/Brotli, malformed or spoofed fonts, and resource-limit violations fail closed with redacted stable reason codes. Hook, CLI, publication preview and exact-candidate secret scanning share the metadata extractor; diagnosis does not mutate HEAD or the Git index.

WebM has no exact-path exemptions. The bounded EBML parser scans declared Unicode/ASCII metadata strings in the final tree and commit history while skipping media payloads. The configured limit defaults to 32 MiB; malformed/truncated structures, unsupported unknown-size elements, invalid metadata text and resource-limit violations fail closed. Findings use the shared redacted secret scanner.

## Intent

Commit safety denials are actionable, structured, and content-redacted. The native Hook and the read-only diagnostic command inspect the same staged candidate through the same scanner.

## Acceptance

- Secret, PII, and injection signals retain their configured commit `BLOCK` actions.
- Strict commit scanning ignores no file or line marker.
- Diagnostics expose stable reason code, phase, safe category/detector, diagnostic ID, retryability, Traditional Chinese recovery, and only a sanitized repository-relative path when safe. Matched values, raw exceptions, command text, and absolute paths never appear.
- PNG, JPEG, WebP, M4A, MP3, TTF, OTF, WOFF, and WOFF2 metadata is scanned through bounded format-aware parsers. Font suffix/signature mismatch, malformed files, missing fontTools/Brotli, oversized compressed input or declared decompressed output, unsupported binary, and incomplete inspection fail closed with a specific reason.
- Staged Git blob size is checked before reading. Hook, CLI, publication preview, and exact-candidate/history scanning share font metadata extraction and strict content scanning.
- WebM metadata is scanned in the worktree, exact candidate tree and candidate history; all paths are covered without exceptions. Metadata fields and EBML boundaries are bounded, malformed or unsupported layouts fail closed, and secret values remain redacted.
- `aips safety diagnose commit --worktree <repo> --message-file <path>` is read-only and shares the Hook implementation.
- Human Authority, Required Checks, and Git Publish Approval remain separate and unchanged.

## Evidence

`tests/test_safety_diagnostics.py`, `tests/test_font_metadata.py`, `tests/test_content_safety.py`, `tests/test_publication_authority.py`, and the exact-candidate Integration Gate provide lifecycle and regression evidence.

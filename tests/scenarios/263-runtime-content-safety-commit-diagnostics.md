# Scenario 263 — Runtime Content Safety Commit Diagnostics

Supported binary metadata inspection includes PNG/JPEG/WebP/M4A/MP3 and TTF/OTF/WOFF/WOFF2 fonts. Font parsing validates the extension against format signatures, checks input and declared decompressed-size bounds, and scans extracted names/vendor metadata through the same strict Secret/PII/Injection scanner used for text. Missing fontTools/Brotli, malformed or spoofed fonts, and resource-limit violations fail closed with redacted stable reason codes. Hook, CLI, publication preview and exact-candidate secret scanning share the metadata extractor; diagnosis does not mutate HEAD or the Git index.

## Intent

Commit safety denials are actionable, structured, and content-redacted. The native Hook and the read-only diagnostic command inspect the same staged candidate through the same scanner.

## Acceptance

- Secret, PII, and injection signals retain their configured commit `BLOCK` actions.
- Strict commit scanning ignores no file or line marker.
- Diagnostics expose stable reason code, phase, safe category/detector, diagnostic ID, retryability, Traditional Chinese recovery, and only a sanitized repository-relative path when safe. Matched values, raw exceptions, command text, and absolute paths never appear.
- PNG, JPEG, WebP, M4A, MP3, TTF, OTF, WOFF, and WOFF2 metadata is scanned through bounded format-aware parsers. Font suffix/signature mismatch, malformed files, missing fontTools/Brotli, oversized compressed input or declared decompressed output, unsupported binary, and incomplete inspection fail closed with a specific reason.
- Staged Git blob size is checked before reading. Hook, CLI, publication preview, and exact-candidate/history scanning share font metadata extraction and strict content scanning.
- The three exact Dewhollow Gate 1 runtime evidence WebM paths listed in `config/secret-scan.yaml` are the only WebM path exceptions. Other WebM files and near-matches remain subject to strict scan limits and fail-closed parsing; no extension-wide WebM exemption is permitted.
- `aips safety diagnose commit --worktree <repo> --message-file <path>` is read-only and shares the Hook implementation.
- Human Authority, Required Checks, and Git Publish Approval remain separate and unchanged.

## Evidence

`tests/test_safety_diagnostics.py`, `tests/test_font_metadata.py`, `tests/test_content_safety.py`, `tests/test_publication_authority.py`, and the exact-candidate Integration Gate provide lifecycle and regression evidence.

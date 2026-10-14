# Scenario 263 — Runtime Content Safety Commit Diagnostics

## Intent

Commit safety denials are actionable, structured, and content-redacted. The native Hook and the read-only diagnostic command inspect the same staged candidate through the same scanner.

## Acceptance

- Secret, PII, and injection signals retain their configured commit `BLOCK` actions.
- Strict commit scanning ignores no file or line marker.
- Diagnostics expose stable reason code, phase, safe category/detector, diagnostic ID, retryability, Traditional Chinese recovery, and only a sanitized repository-relative path when safe. Matched values, raw exceptions, command text, and absolute paths never appear.
- PNG, JPEG, WebP, M4A, and MP3 metadata is scanned through bounded format-aware parsers. Unsupported/malformed binary or incomplete inspection fails closed with a specific reason.
- `aips safety diagnose commit --worktree <repo> --message-file <path>` is read-only and shares the Hook implementation.
- Human Authority, Required Checks, and Git Publish Approval remain separate and unchanged.

## Evidence

`tests/test_safety_diagnostics.py`, `tests/test_content_safety.py`, `tests/test_publication_authority.py`, and the exact-candidate Integration Gate provide lifecycle and regression evidence.

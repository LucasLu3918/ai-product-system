# Scenario 265 — Bounded AVIF Media Safety

AVIF support uses the existing bounded media metadata path and shared media registry. Static AVIF with supported local EXIF/XMP item extents is inspected under the 8 MiB file and 1 MiB metadata caps; encoded image data is never decoded as text. Animated `avis`, spoofed brands, malformed boxes, unsupported item locations and incomplete metadata structures fail closed. The parser validates the container and metadata boundary only; it does not claim AV1 bitstream decodability or visual quality.

Staged commit, read-only commit diagnosis, exact-candidate/history scanning, publication preflight and Creative raster validation use the same AVIF capability. Metadata secrets are blocked and never echoed; malformed media receives a stable safe reason and recovery guidance. Existing non-AVIF binary scan behavior and publication authority remain unchanged.

## Acceptance

- Valid static AVIF metadata reaches the strict Secret/PII/Injection scanner while image payload bytes do not.
- `avis`, bad signatures/brands, truncated or oversized boxes, bad extents and file/metadata resource-limit violations fail closed.
- Hook and read-only diagnostic produce the same safe decision without changing HEAD or the Git index.
- Candidate final-tree and history scanning, preflight, and Creative raster checks recognize AVIF through the shared registry.
- Diagnostics expose only stable reason, safe relative path, phase and cause class; metadata, raw exceptions and absolute private paths remain absent.

## Evidence

`tests/test_safety_diagnostics.py`, the exact-candidate secret scanner, publication preflight and creative validation contracts, and the bound Core Change Test Matrix provide the lifecycle and regression evidence.

# Runtime Content Safety Boundary

## Purpose

Standalone and shadow dependency-review artifacts retain exact base/head, run ID, actual JSON findings and outcome for 90 days. Parity compares canonical findings; missing outputs, different candidates or inaccessible artifacts stay UNKNOWN. Job success alone cannot promote the shadow. Record resolved toolchain fingerprints and repeat full Gates only for new changes or unresolved failures.

The AIPS Runtime Content Safety Boundary is the common, sink-aware safety layer for content that is about to cross a persistence or publication boundary. It complements Secret Handling, Governance Audit, Publish Approval, native runtime hooks and repository-side secret protection; it does not replace any of them.

The implementation is provider-neutral and does not require an external API credential. Deterministic detectors are authoritative for enforcement. Optional semantic detectors may provide advisory signals only.

Imported ComfyUI API workflows remain untrusted project content. Dynamic execution parses bounded JSON as data, validates it against the live local schema and node policy, and never treats workflow strings or metadata as AIPS instructions. Fingerprint caching excludes workflow bodies, prompts and model filenames; this application-level validation does not establish ComfyUI process isolation or real inference safety.

## Contract

Static AVIF EXIF/XMP metadata uses the existing media registry and strict scanner under an 8 MiB input and 1 MiB metadata limit; unknown or animated structures fail closed without decoding image payload as text.

Commit Hook and read-only `aips safety diagnose commit` call the same staged-candidate implementation. Commit scans always use strict ignore-marker behavior. Supported PNG, JPEG, WebP, M4A, MP3, TTF, OTF, WOFF and WOFF2 metadata is bounded and format-aware; font signatures and declared decompressed sizes are checked before fontTools parsing. FontTools/Brotli absence, malformed or spoofed fonts, unsupported binaries and incomplete scans fail closed with redacted structured diagnostics. Git blob sizes are checked before staged contents are loaded. This is a content decision, not publication authority.

Personal publication rejects unsupported literal command forms before candidate inspection, then scans the exact final tree and commit history. Scanner policy, base, Git-object and file-read failures use stable redacted diagnostics and continue to block publication.

The generic secret-assignment detector treats only the exact generated-password expression `Convert.ToBase64String(RandomNumberGenerator.GetBytes(n)).TrimEnd(...)` and parameterized SQL expression `+QUOTENAME(@password|@passwd|@pwd, ...)` as non-literal values. High-entropy literal assignments and provider-token/private-key patterns remain active. The scanner allows JSON text up to 8,000,000 bytes and other text up to 2,000,000 bytes; larger or incomplete inputs fail closed in both the final tree and candidate history.
The generated-path policy also excludes exactly three approved Dewhollow Gate 1 runtime evidence paths: `docs/art/candidates/pixel-movement/gate1-runtime-evidence/videos/legacy-movement-and-farming.webm`, `.../pixel16-movement-and-farming.webm`, and `.../pixel32-movement-and-farming.webm`. Matching is by exact repository-relative path; no WebM extension-wide exemption is added, and the same relative paths are excluded in any repository using this shared policy. Other WebM files and near-matching paths retain the existing strict scan and size/UTF-8 failure behavior.

All AIPS-owned persistence paths should call:

```python
safe_emit(sink="governance_audit", payload=event, context=context)
```

The result contains `decision`, `safe_payload`, and redacted `findings`. A finding may contain only its type, detector, location, fingerprint, length, action and confidence. It must never contain the detected value.

Supported decisions are `ALLOW`, `REDACT`, `BLOCK` and `REVIEW`.

## Detection boundaries

- Secrets reuse the deterministic detectors from `scripts/check_secret_leakage.py`.
- PII starts with deterministic email, phone, checksum-valid card and Taiwan ID detection. It is sink- and context-aware; an email is not automatically a violation.
- Email rule `pii.email.v2` does not report the exact ASCII `git` service user of an scp-like (`host:path`) or `ssh://` Git remote; that is remote grammar, not an exception. Every other regex match, including personal remote users, case variants and confusables, is reported independently, and redaction uses the same predicate. PII never accepts repository exceptions.
- External content carries provenance such as `trust: UNTRUSTED`. Prompt injection is reported as `INJECTION_SIGNAL`, not as a claim of confirmed compromise.
- A detector failure is fail-closed for commit, PR, release and high-assurance audit sinks, and degraded/drop behavior for low-risk diagnostic sinks.

Injection rules have stable IDs for instruction override, credential exfiltration, agent-directed execution and ambiguous imperative wording. Ordinary identifiers such as `run` and `data` are not injection evidence by themselves. Commit-time and publication-candidate injection classification uses added diff lines; Secret and PII detectors continue to scan the complete staged blob or full candidate diff. Comments and strings remain inspectable, and no source extension is allowlisted.

An unresolved `REVIEW` finding blocks commit, PR and release sinks. A repository exception must match one rule ID, repository-relative path, stable finding fingerprint and sink, include a future expiry plus approver/reference, and is rejected when malformed or expired. Exceptions cannot suppress Secret, PII, unsupported-binary or scanner-failure findings. The read-only diagnostic reports a reason, phase, safe evidence, next step and whether human review is required; it never includes matched content or grants publication authority.

The commit sink also covers worktree content that a chained literal `git add`, `-a`/`-am` or `--amend` would include before it is staged, and quoted-delimiter heredoc messages. Commit remains the local injection gate because publication-time candidate scanning covers secrets only.

Publication preflight `git_identity` accepts the GitHub App bot noreply form (`<numeric id>+<slug>[bot]` on `users.noreply.github.com`, `identity.allowed_bot_author_patterns`) only in the candidate commit author field; committer and local `user.email` keep the human noreply formats. Before the `commit_messages` PII scan, exact `identity.trailer_identities` entries (currently Dependabot's `Signed-off-by: dependabot[bot]` with GitHub's support address) are replaced by `git-identity-metadata` only in the final trailer block of a commit authored by the same bot. `pii.email.v2` is unchanged, every other address still blocks, a malformed policy fails closed, and a bot identity grants no authority.

## Sink policy

Diagnostic and ephemeral sinks redact sensitive values. Durable or public sinks block and require safe regeneration. `git commit` is content-sensitive but does not require Git Publish Approval. Publish authorization and content safety are separate decisions.
Plan44's shell-form details and Claude native-failure observation remain outside the content scanner; no content sink is added and raw command or Host error data stays private.

The canonical sink manifest is `config/content-safety.yaml`. Any new persistence or publication sink must be registered there and covered by the deterministic Integration Gate.

## Runtime truthfulness

`ENFORCED` applies to AIPS-owned sinks. A verified native hook may report `TOOL_GUARDED`. MCP-only or unsupported host tools remain `ADVISORY`; AIPS must not claim universal interception.

## Delivery stages

1. v0.58.0: kernel, reusable secret detector, deterministic PII baseline, policy engine and AIPS-owned sink integration.
2. v0.59.0: publication and runtime enforcement for commit, push, PR and release content, including indirect body/message files.
3. v0.60.0: provenance, untrusted-content separation, injection signals, tool-action correlation and quarantine.

Pure dependency update documentation exemption (Scenario 221): `pure_dependency_update` in `scripts/dependency_impact.py` returns `PURE_DEPENDENCY_UPDATE` only when every changed file is an allowlisted dependency manifest (`.github/workflows/*.yml`, root `requirements*.txt`, `constraints/*.txt`) modified in place and every changed line pair is either a full-SHA pinned `uses:` reference for the same action with a non-decreasing version comment, or an exact `name==version` pin with a strictly higher version. Documentation Impact, Documentation Placement and Documentation Sync then suppress documentation requirements only and report each dependency's classification, risk and `human_review_required`; any other line or file, downgrade, unpinned reference, planned path, size-limit overflow or predicate failure keeps the full rules. Secret scanning, content safety, the Core Change Test Matrix, the Integration Gate, required checks and Human merge approval are unchanged, and `automatic_merge_authorized` stays false.

## Security invariants

Publication timeout diagnostics omit raw command and exception text. A Claude PreToolUse remote failure remains denied, and manual Doctor recovery is read-only and cannot grant publication authority.

AIPS publication hook 對未預期授權例外 fail closed；回傳與 opt-in ledger 限定 allowlist 例外類別，不攜帶原始訊息或命令。
Operational dashboard output follows the same sink-aware boundary: only a sanitized allowlist may cross into the localhost observation surface, with no prompts, reasoning, secrets or mutation authority.

- No raw secret or private reasoning is emitted in findings, audit records or observable events.
- Sanitize precedes hash and persistence.
- Public or durable sink policy cannot silently redact a blocked secret.
- Human approval cannot be bypassed by an injection signal.
- Unsupported runtime capability is never upgraded to `TOOL_GUARDED`.

This content-safety boundary is unchanged by publication settings. AIPS Required Checks enforcement is separately opt-in via `AIPS_ENFORCE_REQUIRED_CHECKS=1`, and GitHub native protections remain effective.

# Plan47 Content Safety Classification and Diagnostics

## System Improvement Review

- **Appropriateness:** Appropriate. The current detector's broad `run|execute|push|send` plus generic data-term branch creates false positives in ordinary JavaScript.
- **User problem:** Normal application code is blocked by a low-specificity instruction-pattern detector, and commit diagnostics do not consistently explain the safe cause and recovery steps.
- **Proposed solution:** Extend the existing sink-aware scanner and native commit diagnostic path with versioned high-confidence rules, source-aware staged-diff classification, structured safe diagnostics, and narrow expiring exceptions.
- **Existing coverage:** `scripts/content_safety.py`, `scripts/governance_guard.py`, `scripts/safety_diagnostics.py`, `scripts/publication_authority.py`, and Scenario 263 already provide the enforcement and diagnostic foundation.
- **Reuse / lower-layer alternative:** Reuse those modules and contracts. Avoid a new LLM service, parser dependency, or a separate scanner. Simple deterministic code-context recognition plus added-line inspection is sufficient for the known cases while comments and strings remain inspected for strong signals.
- **Context / token cost:** No runtime model call or recurring prompt context. Small deterministic configuration and diagnostics only.
- **Security / reliability:** Keep secrets and PII scanned across complete staged content; keep scanner failures fail-closed. Strong override, exfiltration, and unauthorized agent-execution signals remain blocking. Ambiguous signals cannot become an implicit allow; the commit path denies unresolved review. Exceptions are exact rule/path/fingerprint/sink matches with an expiry and explicit human approval record; they never apply to secrets or PII.
- **Backward compatibility:** Preserve `safe_emit`, the hook response envelope, CLI syntax, existing reason codes where meanings remain valid, and read-only index/HEAD behavior. Add fields without exposing matched content or raw exceptions.
- **Constitution impact:** NO. Human authority, protected safety boundaries, and publication authority remain unchanged; the implementation tightens detection and makes an explicit exception record auditable.
- **Recommendation:** Use deterministic, versioned rules and code-context handling; never whitelist whole source files or weaken durable-sink enforcement.
- **Additional optimization candidates:** None included.

## Purpose

Fix the confirmed injection false positives while preserving true positive blocking and improving actionable, privacy-preserving diagnostics.

## Why this is a core change

The detector is on Git commit, PR, and release safety paths. Its rule semantics, scan coverage, exception behavior, and diagnostic contract affect a protected security boundary.

## Proposed Scope

### In scope

- Replace the generic `run/execute/push/send` plus broad data-term injection branch with separately identified/versioned deterministic rules for instruction override, credential exfiltration, agent execution, and ambiguous instruction-like content.
- Add source and file context to the existing scanner. Scan injection candidates in added/changed staged and publication-candidate diff lines with bounded surrounding context, while scanning secrets and PII across the full staged blob or full candidate diff. Continue inspecting code comments and strings; do not allowlist a whole file type.
- Recognize the reported ordinary JavaScript data references as benign syntax without suppressing strong injection patterns in nearby comments or strings.
- Keep unresolved `REVIEW` findings fail-closed at durable sinks unless a valid exact-scope exception applies.
- Add a validated exception record scoped to rule ID, repository-relative path, stable finding fingerprint, sink, and expiry. Reject expired, malformed, overly broad, or mismatched exceptions. Exceptions never suppress secret, PII, unsupported-binary, or scanner-failure findings.
- Extend shared diagnostics with stable reason/remediation guidance, phase, detector/rule ID, source path and line, per-event diagnostic ID, stable finding fingerprint, and safe evidence. Never include matched secret values or unfiltered exception text.
- Add benign, malicious, ambiguous, diff-context, exception-boundary, scanner-failure, and Git index/HEAD immutability regressions. Compare the old broad detector with the new rules against a fixed, privacy-safe corpus before enabling the policy.
- Update canonical content-safety documentation, documentation placement/sync maps, scenario coverage, changelog/version metadata as required by repository policy, and a focused conformance scenario.

### Out of scope

- Changes to `lucas-lab` or any game/application source code.
- Whole-language or whole-file allowlists, disabling content safety, silently treating `REVIEW` as allow, or changing secret/PII detector semantics.
- External LLM/classifier calls, new network access, new runtime dependencies, changes to host capabilities, admin policy, or branch protection.
- Changes to Constitution, Human Authority, publication authorization, direct main pushes, or automatic merge behavior.

## Expected Files / Modules

- `scripts/content_safety.py`
- `scripts/governance_guard.py`
- `scripts/publish_preflight.py`
- `scripts/safety_diagnostics.py`
- `scripts/publication_authority.py`
- `config/content-safety.yaml`
- `config/content-safety-exceptions.yaml` (schema/config with no permissive default entries)
- `tests/test_content_safety.py`
- `tests/test_safety_diagnostics.py`
- `tests/fixtures/` (bounded benign/malicious fixtures)
- `orchestration/CONTENT_SAFETY_BOUNDARY.md`
- `docs/human/SECURITY_ASSURANCE.md`
- `docs/human/CONFORMANCE.md`
- `orchestration/CONFORMANCE.md`
- `config/documentation-placement.yaml`
- `config/documentation-sync.yaml`
- `tests/scenario_coverage.yaml`
- `tests/scenarios/` (focused scenario)
- `CHANGELOG.md`, `VERSION` (only as required by version policy)
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`
- This proposal.

## Impact

### Architecture / Contracts

No new service or runtime dependency. The existing scanner remains canonical. The finding JSON grows additively with rule/source/recovery fields; hook and CLI output remain safe and backward-compatible. Injection analysis gains staged-diff context, while secret/PII coverage remains full-blob.

### Data / Migration

No database or user-data migration. The exception manifest is static repository policy data, defaults to no exceptions, and is validated on each use.

### Security / Reliability

Fail-closed on malformed exception data, unknown rule IDs, expired exceptions, unsupported staged content, and scanner errors. Strong malicious samples must remain blocked. Full staged secrets/PII scanning and redaction are invariant.

### Compatibility / Rollback

Keep existing public helper and CLI interfaces. Rollback is a revert of the single PR; no persistent runtime state is migrated.

### Tests / Validation

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| Rule classification | YES | YES | YES | YES | N/A | YES | N/A | N/A | YES | No external UI |
| Staged candidate scan | YES | YES | YES | YES | N/A | YES | N/A | YES | YES | No migration |
| Diagnostics and Hook | YES | YES | YES | YES | N/A | YES | N/A | YES | YES | Existing hook lifecycle |
| Exception validation | YES | YES | YES | YES | N/A | YES | N/A | YES | YES | Static policy file only |
| Repository delivery | YES | YES | YES | YES | N/A | YES | N/A | YES | YES | Full local Gate and remote checks required |

Recompute if the actual diff adds a sink, changes an authority boundary, introduces a runtime dependency, or touches additional callers/consumers.

Required release/CI evidence: focused safety and diagnostics suites; exception-policy negative cases; full repository Integration Gate and exact-candidate secret/history scan; remote PR required checks; post-merge `main` checks.

### Secret / Credential Impact

Secrets required: NO.

Approved acquisition mechanism: N/A.

Leakage/redaction review: required for detector findings, diagnostics, hook output, fixtures, and exception fingerprints.

Rotation/revocation plan if exposure is found: remove exposure, rotate/revoke the affected credential, and rerun the strict scanner.

### Documentation / Diagrams

- `docs/ARCHITECTURE.md` Mermaid: N/A — no component, trust-boundary, or data-flow topology changes.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: N/A — same architecture and authority flows.
- Human SVG architecture/lifecycle diagrams: N/A — no component or lifecycle changes.
- Content safety boundary docs and diagnostics/recovery guidance: AFFECTED.

## Risks

- Weakening the broad rule could expose a missed injection pattern; fixed malicious/benign corpus and staged/whole-content split are required before activation.
- Exception configuration can become a bypass if path, rule, fingerprint, sink, expiry, or approval evidence is omitted; validation must deny malformed or stale records.
- Diff parsing can miss context if hunk boundaries are incorrect; cover additions, deletions, renames, new files, and context limits.

## Recommendation

Proceed within this boundary. Do not add a heavyweight parser or external semantic classifier; preserve deterministic fail-closed behavior and address the observed false positives at the rule/context layer.

## Proposed Implementation Order

1. Add regression fixtures and reproduce the current false positives.
2. Implement versioned high-confidence rules and benign code-context handling.
3. Split injection added-line scanning from full staged secret/PII scanning.
4. Extend shared diagnostics and exact, expiring exception validation.
5. Run old/new corpus comparison, focused tests, documentation closure, full Gate, and exact-candidate secret scan.
6. Publish a PR to `main`; merge only the exact candidate after required checks pass.

## Approval

Status: APPROVED
Approved by: User
Approved at: 2026-10-19 (Asia/Taipei)
Approval record: Explicit request to implement all plan47 recommendations and merge the resulting PR to `main`; scope remains bounded to plan47's content-safety remediation.
Proposal fingerprint: PENDING after final proposal bytes
Scope fingerprint: PENDING after final scope resolution

# Core Change Proposal: Claude Code Runtime Diagnostics Optimization

## Purpose

Improve the precision and recoverability of AIPS Resource Authorization and Runtime Policy diagnostics, and carry the established failure distinction through the Claude Code adapter. The attached report also proposes tool, template, and generic multi-file-edit behavior; each item is mapped to current AIPS ownership below so existing capabilities are reused and environment-specific issues are not misrepresented as AIPS failures.

## Why this is a core/large change

The change touches the default-deny authorization boundary and its Runtime Policy and native Hook consumers. Incorrect diagnostic changes could disclose paths, misstate whether a tool ran, or weaken authorization. Compatibility and redaction require regression evidence across the CLI, Hook, and Human/Agent guidance.

## Approved scope

The user approved the evidence-backed T01–T10 scope in this conversation on 2026-10-29. Scope is limited to this AIPS repository and the existing Resource Authorization, Runtime Policy, Claude Code adapter, and self-improvement workflow surfaces.

### In scope

- T01: use current AIPS version, Harness status, Resource Authorization profile, Runtime Policy, and existing diagnostics as the authoritative inventory; report version/path assumptions as configuration findings.
- T02/T03: preserve and test the existing stable reason codes, trace IDs, phase, owner/category and recovery fields; add only backward-compatible fields that distinguish pre-execution decisions from observed native tool failures.
- T04: enrich missing/unreadable Resource Authorization profile diagnostics with the configured project-relative path, source field, resource required by the action, `fallback_allowed: false`, and a bounded repair hint. Never expose an absolute private path.
- T05: return a machine-readable `constraint_diff` with only the actual destination fields that failed and the effective expected value(s). Keep default deny, exact host/port/method/path matching and credential redaction unchanged.
- T07: clarify the existing self-improvement workflow for multi-file edits: inspect all target versions and match counts before writing, prefer one context-rich patch, verify the whole diff, and use same-directory atomic replacement plus verified rollback for programmatic multi-file writes.
- T08: document and contract-test the existing OFF/ADVISORY/ENFORCED capability truth. No new global switch or automatic Hook installation is introduced.
- T09/T10: extend existing Claude Code pre-tool denial and post-tool failure lifecycle evidence and regression coverage, including JSON shape, tool-started truth, exit-code handling, redaction, command composition, and no unintended side effects.
- T06: verify that AIPS-owned ComfyUI preflight remains capability-aware. The reported `ffmpeg`/`libwebp` conversion is not an AIPS-owned execution path, so AIPS will classify and document it as an environment/tool failure without adding a generic FFmpeg installer or changing global tools.
- E05: document the repository-versioned `templates/intelligence/CHANGE_IMPACT.yaml` as the canonical source. Do not add a registry or resolver command for one obsolete user-home path.

### Out of scope

- Editing the separate `lucas-lab` project or its documents.
- Calling ComfyUI, reading external local-service state, installing/upgrading FFmpeg/ImageMagick, or changing machine-wide PATH/configuration.
- Adding generic command parsing, a new cross-runtime diagnostics service, a template-registry subsystem, or a multi-file transaction engine without demonstrated AIPS ownership.
- Broadening Resource Authorization, localhost endpoints, network access, profile defaults, Hook coverage claims, or publication/merge authority.
- Changing the Constitution, GitHub policy, or the user's global runtime settings beyond the AIPS preflight refresh already performed.

## Existing coverage and recommendation

Current code already implements default-deny Resource Authorization, exact destination constraints, stable reason codes and trace IDs; ComfyUI discovery is bounded to fixed loopback GET endpoints and refuses redirects; Claude Code emits structured `PreToolUse` denial JSON and separates `PostToolUseFailure`; the AIPS Harness distinguishes OFF-by-absence, ADVISORY, and tool-guarded behavior. Existing tests cover much of this behavior.

The concrete code gap is that `destination_constraint_mismatch` gives only a generic recovery message and missing profile results omit safe resolution details. Extend `scripts/resource_authorization.py` and `scripts/runtime_policy.py` additively, then add focused lifecycle and contract evidence. Treat the traversal index as candidate discovery: direct callers and consumers were inspected in source. Global Impact Graph coverage remains partial.

## Expected files / modules

- `scripts/resource_authorization.py`
- `scripts/runtime_policy.py`
- `scripts/governance_guard.py`
- `tests/test_runtime_policy.py`
- `tests/evidence/resource_authorization_lifecycle.py`
- `tests/evidence/runtime_policy_lifecycle.py`
- `tests/validation/resource_authorization_contracts.py`
- `tests/validation/runtime_policy_contracts.py`
- `tests/scenarios/177-runtime-policy-enforcement.md`
- `tests/scenario_coverage.yaml`
- `orchestration/RESOURCE_AUTHORIZATION.md`
- `orchestration/RUNTIME_POLICY_ENFORCEMENT.md`
- `orchestration/SYSTEM_SELF_IMPROVEMENT.md`
- `harness/adapters/claude-code/CLAUDE.md`
- `docs/ARCHITECTURE.md`, `docs/human/ARCHITECTURE_OVERVIEW.md`, `docs/human/HARNESS.md`, `docs/human/INSTALLATION.md`, `docs/human/SECURITY_ASSURANCE.md`, `docs/human/MAINTENANCE.md`
- `config/documentation-placement.yaml`, `config/documentation-sync.yaml`
- `docs/qa/CORE_CHANGE_TEST_MATRIX.yaml`, `VERSION`, `CHANGELOG.md`
- This proposal.

The final changed-file set may be smaller. Any added source or consumer outside this boundary requires Change Impact reconciliation and scope review.

## Impact

### Architecture / contracts

No new service or authorization path. Runtime Policy results retain their current schema and reason codes; diagnostic detail is additive and redacted. Claude Code Hook decision fields remain compatible with the official `PreToolUse` contract.

### Data / migration

No migration or durable runtime state. Synthetic tests use temporary project roots.

### Security / reliability

The change preserves default deny, non-redirecting fixed loopback access, path confinement, secret redaction, native Host permission control, and Human-only publication authority. Diagnostic `tool_started` and exit codes may describe execution only when verified by the owning lifecycle phase.

### Compatibility / rollback

Additive diagnostic keys do not change existing decisions or reason codes. Rollback is a normal revert of the two implementation modules, tests, and guidance; no runtime data migration is required.

### Tests / validation

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| Resource Authorization diagnostics | Required | Required | Required synthetic CLI lifecycle | Required | N/A | Required: default-deny, exact diff and redaction | Required: no writes on denied preflight | Required: Runtime Policy and Claude Hook | Required | No user-facing product UI |
| Runtime Policy/Claude Hook failure reporting | Required | Required | Required synthetic Hook lifecycle | Required | N/A | Required: denial remains deny, native failure stays distinct | Required: no retry/rollback claim without evidence | Required | Required | Native Host acceptance is external |
| Agent multi-file edit procedure | Required docs contracts | N/A | Required synthetic side-effect regression | Required | N/A | Required: no partial write on precondition failure | Required: rollback state is observable | Required Hook docs contract | Required | No AIPS-owned generic file-write transaction API exists |
| AIPS tool capability / external FFmpeg | Required inventory | Existing ComfyUI capability tests | Existing synthetic preflight | Existing contracts | N/A | Required preserve loopback and no install | Required | Existing creative preflight | Required applicability note | AIPS does not call FFmpeg for the reported conversion |

Recompute if scope adds a global policy switch, Hook adapter implementation, external destination, durable diagnostics ledger, or any new tool execution path.

Required release evidence: focused tests above, full repository validation, Scenario 177, documentation placement/synchronization closure, strict candidate/history secret scan, exact-candidate Integration Gate, and passing `repository` check.

### Secret / credential impact

Secrets required: NO.

Use synthetic credentials only. Never include absolute user paths, URLs with query secrets, exception text, raw commands, or profile contents in diagnostic evidence.

### Documentation / diagrams

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` runtime/policy flow: AFFECTED — clarify the existing authorization → runtime decision → native Hook result distinction.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: AFFECTED — show the same existing boundary without claiming interception coverage beyond each adapter.
- Human SVG architecture/lifecycle diagrams: N/A — no new component or lifecycle boundary.
- `harness-overview.svg`: N/A — the diagram does not collapse native Hook denial and native tool failure; this change clarifies diagnostic text only.

## Risks

- Incorrect diff generation could expose private host/path information; include allowlist-based redaction tests.
- Adding a generic `tool_started` field to a preflight result could be misread as execution; set phase-specific truthful values and test both sides.
- Partial lexical/architecture graph coverage does not prove repository-wide callers. Preserve the limitation and inspect direct callers/consumers manually.
- AIPS cannot remediate the external FFmpeg encoder or ComfyUI environment from this repository change.

## Recommendation

Implement the small additive diagnostic gap and its lifecycle evidence; map every other recommendation to existing coverage or an explicit non-AIPS disposition. Do not introduce new authority, registry, generic transaction, or capability subsystems.

## Proposed implementation order

1. Complete direct caller/consumer review and finalize approved Change Impact evidence.
2. Add failing focused regressions for profile resolution details, exact constraint diffs, and execution-phase truth.
3. Implement additive result fields and redaction while preserving existing decision behavior.
4. Add multi-file edit guidance and synchronize Runtime Policy, Claude Code and Human documentation.
5. Run the Change Impact-derived matrix, full repository validation, documentation closure, and exact-candidate Integration Gate.
6. Prepare one coherent feature branch update, open a PR, wait for the exact `repository` check, and merge only after fresh protected-branch validation.

## Approval

Status: APPROVED BY USER
Approved by: User in Codex conversation
Approved at: 2026-10-29
Approval record: User selected “核准建議範圍” for the evidence-backed T01–T10 AIPS repository scope.
Scope fingerprint: Bound by the external Change Impact artifact `claude-runtime-diagnostics-optimization`.

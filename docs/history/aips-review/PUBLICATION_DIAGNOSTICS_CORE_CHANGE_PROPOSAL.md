# Core Change Proposal: AIPS Publication Diagnostics & Recovery Refinement

## Purpose

Improve AIPS publication troubleshooting so users can identify the exact failed phase, GitHub observation category, HTTP status, safe endpoint identifier, and recovery step while preserving all current publication and Human Authority boundaries.

## Why this is a core/large change

The change crosses GitHub policy observation, publication planning, native Claude Code hook decisions, error contracts, and documentation. Incorrect evidence handling could affect whether a protected operation is permitted, so the candidate needs an exact-boundary matrix and a full local Integration Gate.

## Proposed Scope

### In scope

- Separate the candidate/source branch from the policy/target branch. Default policy observation to the remote default branch; retain an explicit `--branch` override and report the policy branch separately from the candidate branch.
- Reuse `repository_governance_snapshot.parse_gh_response()` and `query_github_api()` so Doctor retains validated HTTP status, endpoint identity, and bounded safe error information for each source. Distinguish authentication, permission, confirmed missing branch/resource, rate limiting, service failure, and network/CLI failure. Do not infer a 403/404 or an unprotected policy from missing evidence.
- Keep `build_snapshot()` incomplete unless the target branch and effective rules are affirmatively observed; classify classic branch-protection 404 as unconfigured only after branch existence is confirmed.
- Make `PublicationError` diagnostics carry safe, structured observation context and stable reason codes while preserving secret redaction and the existing diagnostic contract where possible.
- Make recovery guidance consistent with actual reason codes: bounded retries may re-collect evidence only for transient network/rate-limit/server failures; permission, authentication, missing-resource, policy, candidate-drift, and Human Authority failures do not retry automatically. No retry runs push, PR, merge, or other publication actions.
- Keep compound commit/publication commands phase-separated and fail closed when the parsed invocation cannot be uniquely bound. Return the failing operation/phase rather than a generic publication rejection.
- Improve Claude Code PreToolUse denials with a structured, immediately available safe diagnostic record: diagnostic/operation ID, reason code, phase, safe detail, confirmed HTTP status/endpoint when present, recovery state, and next step. Do not persist raw command text, tool arguments, credentials, or provider headers.
- Add focused unit/lifecycle/scenario coverage for source-vs-target branches, HTTP/error classes, redaction, recovery, multi-command rejection, stale candidates, merged-PR repeat observations, and preserved Human Authority.
- Update canonical CLI/Claude Code and human guidance, documentation sync placements, maintenance documentation, and changelog/version artifacts required by repository policy.

### Out of scope

- Weakening, bypassing, or changing publication authorization, secret scanning, protected-branch rules, merge confirmation, or High-Assurance grants.
- Automatically retrying or executing a denied publication action.
- Persisting raw intercepted commands or adding a durable diagnostic log/retention system.
- Changing GitHub repository settings, required checks, credentials, or the already merged LUCAS-LAB PR #47.
- Adding a new Gate, Role, Skill, Capability, service, or parallel publication workflow.
- Changing constitutional semantics.

## Expected Files / Modules

- `scripts/publication_diagnostics.py`
- `scripts/repository_governance_snapshot.py`
- `scripts/publication_authority.py`
- `scripts/publication_planning.py`
- `scripts/publication_commands.py`
- `scripts/governance_guard.py`
- `harness/adapters/claude-code/CLAUDE.md` and the relevant adapter/CLI help projection, if confirmed by the implementation impact scan
- Global Harness protocol plus OpenCode Agent/compatibility and Creative Direction topic projections required by final recursive documentation impact
- `tests/test_publication_diagnostics.py`
- `tests/test_publication_authority.py`
- `tests/test_publication_planning.py`
- `tests/test_publication_error_recovery.py`
- publication lifecycle evidence and scenarios 260/261, plus a new/updated scenario only if the current coverage map requires it
- canonical documentation and sync-map files identified by `aips docs impact`
- `CHANGELOG.md`, and `VERSION` only if repository release policy requires a version increment for this change
- exact-candidate `CHANGE_IMPACT.yaml` and Core Change Test Matrix artifacts

## Impact

### Architecture / Contracts

Extends the existing publication diagnostics/snapshot/planning/guard flow. The public diagnostic payload remains additive where possible; stable reason codes, phase names, and CLI exit behavior must be checked for compatibility. No new architecture component is proposed. Impact Graph coverage remains partial unless the exact affected relationships are verified.

### Data / Migration

No database or user-data migration. No durable diagnostic store. Hook output contains only bounded, sanitized structured evidence; raw command text, headers, credentials, and unrestricted provider output are excluded.

### Security / Reliability

This is security-sensitive because diagnostics feed publication decisions. Unknown or incomplete policy evidence remains blocking. Only evidence collection can be retried, with a finite bound, and retries never authorize or perform publication. Tests must prove token/header/credential URL redaction and fail-closed behavior.

### Compatibility / Rollback

Retain existing CLI entry points and reason-code behavior where applicable; add fields/codes compatibly and test consumers. Rollback is a revert of the single coherent candidate; no migration is needed. A stale candidate must be replanned and revalidated.

### Tests / Validation

Impact-derived Test Matrix:

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| Branch identity and effective policy evidence | Python/repo validation | source branch differs from default target; unpushed source; target branch absent; ruleset and classic protection combinations | fake GitHub API evidence across endpoints | snapshot shape and source completeness | publish doctor CLI | 404 is not absence without affirmative branch evidence | re-observation after evidence failure | `doctor --branch` and default branch | diagnostic docs | migration N/A: read-only evidence only |
| GitHub response parsing and safe error context | Python/repo validation | 200, 401, 403, 404, 429, 5xx, timeout/DNS/CLI, malformed response | Doctor uses same evidence parser as snapshot | stable reason/phase/status/endpoint contract | CLI output | token, bearer, credential URL, header, raw stderr, and unsafe message redaction | transient-only bounded read retries | JSON/text output | troubleshooting table | persistent storage N/A |
| Recovery classifier | Python/repo validation | retryable vs non-retryable reason matrix | transient read failures exhaust bounded retry count | `retryable`, `retry_read_only`, next step agree | doctor/prepare flow | no publication call on any retry path | recovery state and candidate re-observation | CLI guidance | recovery docs | schema migration N/A |
| Commit/publication operation binding | Python/repo validation | standalone commit/push/PR/merge and ambiguous/compound shell forms | hook/command parser lifecycle | exact candidate/head/ref binding remains intact | native fixtures | protected operations fail closed; no alternate-command bypass | changed candidate invalidates old plan | Claude Code PreToolUse fixtures | adapter guidance | data migration N/A |
| Claude Code structured denial | Python/repo validation | diagnostic fields and operation ID | Hook consumer lifecycle | native JSON envelope compatibility | host acceptance if available; record unavailable host evidence explicitly | no prompt/argument/credential persistence or leakage | repeated denied operation is observational only | Claude Code adapter | runtime docs | architecture diagram N/A if topology unchanged |
| Documentation and publication governance | Markdown links/docs impact | documentation-map/sync contracts | full local Integration Gate | proposal/matrix exact candidate binding | PR CI and main CI | secret scan over final tree and complete base..head history | stale-candidate revalidation | CLI docs | Maintenance/docs/changelog | migration N/A |

Recompute trigger if scope expands: any durable diagnostic persistence, authorization-policy change, changed remote ref/merge behavior, new runtime, new Gate, or additional modules outside the reconciled documentation and test closure.

Required release/CI evidence: focused publication lifecycles during development; exact-base/head Core Matrix and diff binding; credential-free secret scan on final tree and full history; one full local Integration Gate on the fixed candidate; passing PR required checks; re-observed exact PR head/base, mergeability and checks before merge; post-merge validation on `main`.

### Secret / Credential Impact

Secrets required: NO.

Approved acquisition mechanism: N/A; tests use synthetic API/CLI responses.

Leakage/redaction review: assert that access tokens, bearer values, authorization headers, credential-bearing URLs, raw command contents, and unbounded stderr do not appear in diagnostics or persisted artifacts. No diagnostic persistence is added.

Rotation/revocation plan if exposure is found: stop publication, remove exposed value from candidate/output, revoke the credential with its owner, rescan the exact candidate/history, and revalidate.

### Documentation / Diagrams

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` Mermaid: N/A — existing publication flow and component topology remain unchanged.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: N/A — no component/topology change.
- Human SVG architecture/lifecycle diagrams: N/A — no lifecycle authority or component change; update text guidance where the diagnostics flow is documented.

## Risks

- GitHub endpoint behavior differs between branch rules, effective rulesets, and classic branch protection; 404 must remain contextual and conservative.
- Over-redaction can make useful errors vague; under-redaction can expose credentials or private arguments. Use allowlisted structured fields and explicit negative tests.
- Diagnostic retry metadata can accidentally be interpreted as action authorization; every output must state `executed: false` and `authorized: false`.
- Claude Code hook consumers may depend on current denial strings; retain a clear human-readable reason alongside structured fields and test the native envelope.
- The current local worktree is 86 commits behind `origin/main`, has unrelated untracked `aips-add-skill-plan.md`, and AIPS preflight currently reports `cannot open '.git/FETCH_HEAD': Operation not permitted`; perform the candidate from clean `origin/main` and resolve/retry preflight before mutation.

## Recommendation

Appropriate. Reuse the existing snapshot parser, diagnostic registry, recovery planner, and Claude Code guard. The request's intended scope is supportable without weakening authority. Keep diagnostic evidence inline and ephemeral; durable command logging would add a separate privacy/retention decision and is excluded.

Appropriateness: SUITABLE WITH CORE CHANGE APPROVAL.
User problem: publication denials hide the observed phase/cause and recovery advice can contradict retryability.
Proposed solution: improve evidence capture, reason classification, recovery guidance, and native Hook presentation.
Existing coverage: common parser, diagnostic ID, stable reason catalog, read-only doctor/prepare, and recovery planner already exist but are not consistently connected.
Reuse / extension candidates: existing publication diagnostics/snapshot/authority/planning/guard modules and lifecycle tests.
Lower-layer alternative: fix the existing publication flow and host adapter rather than add system-wide Gates or new capabilities.
Context / token cost: no per-turn Context addition; bounded work only on publication diagnostics and denials.
Security / reliability: maintain fail-closed evidence and Human Authority; redact with allowlisted fields; retry observation only.
Backward compatibility: additive output fields and stable CLI paths; test text/JSON and hook consumers.
Scenario / test impact: publication lifecycle scenarios 260/261 and exact-candidate Core Matrix.
Human docs impact: maintenance/docs impact closure and troubleshooting guidance.
Agent docs impact: Claude Code adapter and CLI help, if those are canonical consumers.
Architecture diagram impact: N/A, topology unchanged.
Constitution impact: NO. No authority or constitutional rule changes are proposed.
Additional optimization candidates: none included.
Expected scope: files/modules listed above; exact file set is finalized after approved-scope Change Impact traversal.
Risks: detailed above.

## Proposed Implementation Order

1. Once scope is approved, initialize/refresh Project Intelligence, run preflight, and resolve Change Impact from `origin/main`.
2. Add characterization/regression coverage for the observed branch-selection, API error, recovery, compound-command and hook-display gaps.
3. Connect Doctor to structured API evidence and target-branch policy identity; correct snapshot completeness and contextual 404 classification.
4. Align diagnostic catalog and recovery planner; expose bounded safe structured Hook denials while retaining all authority checks.
5. Update scenarios, adapter guidance, CLI help, documentation projections and release artifacts from the canonical documentation impact map.
6. Reconcile actual diff and finalize the exact-candidate Core Change Test Matrix.
7. Run focused evidence and one full local Integration Gate, review the final diff/security evidence, then prepare one engineering-branch PR to `main`.
8. Re-observe the exact PR candidate and required checks, merge only when the selected publication policy permits, then run post-merge validation.

## Approval

Status: APPROVED
Approved by: User in the current Codex conversation
Approved at: 2026-10-14T06:16:56Z
Approval record: User replied "核准" to this exact proposal and scope.
Proposal fingerprint: sha256:3f9e5b2fd0200ece332e4a0711a071e64d0112c731f66c7af25d329ba1b9c50f
Scope fingerprint: sha256:f0d5abb27eb1fff864de609b924f185c500f4a26be0092727bebadc1abf27ee6

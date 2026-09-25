# Core Change Proposal: Verified Sandbox Provider Architecture

## System Improvement Review

- **Appropriateness:** Suitable as an optional extension to the existing Execution Profile and Isolation Resolver. Current `sandbox` is truthfully unavailable without a provider.
- **User problem:** Worktrees isolate Git state but do not isolate host processes, credentials, mounts or network execution.
- **Recommended solution:** Keep `shared / worktree / sandbox`; add a provider-neutral capability contract, deterministic resolver and bounded E2B synthetic lifecycle verification. MicroVM remains a sandbox capability. General project-file staging/execution is a separate adapter boundary and remains pending explicit data-scope approval after automatic review blocked its implementation.
- **Existing coverage:** `orchestration/EXECUTION_ISOLATION.md`, `scripts/execution_isolation.py`, Execution Profile schema, and scenarios 111/114 already define truthful sandbox behavior and negative cases.
- **Reuse:** Extend these contracts, existing external credential registry, repository validation, scenarios, documentation sync and Integration Gate. No new Role, Skill, approval Gate or Audit subsystem.
- **Context/cost:** E2B dependency remains optional; ordinary work continues on worktrees. Provider verification uses synthetic content only; project-source transfer is pending explicit data-scope approval.
- **Security/reliability:** No host mounts, no guest credentials by default, bounded TTL and resources, denied egress by default, strict data classification, host-side artifact validation, and fail-closed provider verification. E2B's microVM is provider-declared; AIPS tests observed controls but cannot attest to its hypervisor.
- **Compatibility:** Existing modes and worktree lifecycle remain intact. Missing/unverified provider remains `UNSUPPORTED`/`BLOCKED`. Existing profile fields remain optional-compatible.
- **Tests/docs:** Mock lifecycle and resolver tests, no-credential CI, protected-main manual live lane, negative-path scenarios, Architecture/Security/Isolation guidance and documentation sync.
- **Architecture diagrams:** `docs/ARCHITECTURE.md` and `docs/human/ARCHITECTURE_OVERVIEW.md` are affected because they describe sandbox resolution and execution flow.
- **Constitution impact:** NO. Protected Human Authority, publication authority and approval semantics remain unchanged.

## Scope

### In scope

- Provider-neutral registry and capability contract for runtime class, kernel boundary, hardware virtualization claim, ephemeral lifecycle, egress, host mounts, credential scope, TTL, data classes and evidence freshness.
- A deterministic fail-closed resolver that matches explicit minimum isolation requirements and data policy.
- Optional E2B Python SDK synthetic smoke verifier for bounded `create -> execute -> destroy`; it does not stage project files or collect project artifacts.
- External per-repository verification evidence and bounded verification receipt.
- Protected-main, manually authorized live verification workflow; no provider credential in pull-request code and no live test without written provider consent.
- Tests, scenarios, security review, docs, architecture diagram, changelog and version update after baseline review.

### Out of scope

- A fourth `microvm` mode, always-on cloud sandboxes, automatic source upload, confidential/restricted managed-provider data, production credentials in a guest, provider-specific core contract, or provider hardware attestation claims.
- New Role, Skill, approval Gate, Audit subsystem, Constitution change, automatic merge or deployment authority.
- Running a live E2B test in this task: no credential or written provider test consent has been supplied.

## Initial Change Boundary

- Provider registry, contract, capability matching and truthful sandbox capability resolution; task lifecycle remains disabled pending data-scope approval.
- Synthetic E2B smoke verifier and optional dependency/credential handling.
- External verification evidence and verification receipt.
- Scenarios, conformance, security tests, Core Change Matrix, user/agent docs, architecture diagrams and release metadata.

Expected paths are bound in `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` and must be reconciled to the actual diff before publication.

## Architecture, data and migration

- The committed registry declares E2B as `NOT_VERIFIED`; a key alone never enables it.
- Per-repository runtime evidence lives outside the repository under the AIPS config directory. It binds registry digest, SDK/runtime class, observed control checks, timestamp and expiry.
- A sandbox receives only an immutable, explicitly classified source snapshot. Default managed-provider policy allows `public` data only; `internal` needs explicit policy; `confidential` needs approved region/BYOC; `restricted` is blocked by default.
- Provider receipts contain bounded metadata/digests only, never secrets or private model reasoning.
- No project artifact migration. Existing profiles that omit new optional isolation fields retain current behavior.

## Security and compatibility

- E2B API key is optional and read only by the host verifier from runtime environment/approved CI secret store.
- No host mounts or credential forwarding; egress defaults to deny-all and explicit allowlists are validated.
- `shared` and `worktree` behavior, single-writer policy, dirty-worktree preservation and scenarios 111/114 remain valid.
- Provider-declared microVM assurance and AIPS-observed integration checks are distinct evidence classes.
- E2B live verification requires a manual protected-main workflow dispatch attesting prior written test consent; missing key returns `SKIPPED_NOT_CONFIGURED`.
- Automatic review rejected code that would upload caller-selected local files to E2B because the payload and destination lacked explicit data-transfer authorization. Implementation remains synthetic-only until the user specifies an allowed data scope and E2B destination.

## Validation

Run focused contract/evidence tests, credential guard and documentation/schema checks, then full repository validation and exact-candidate Integration Gate using the bound Core Change Matrix. Live-provider evidence remains `NOT_RUN` in this PR unless valid consent and credentials already exist; mock evidence cannot be reported as provider verification.

## Approval

- **Status:** APPROVED
- **Approved by:** User
- **Approval record:** User explicitly requested implementation of all recommendations in `plan3.md`, local validation, and a remote PR merged to `main`.
- **Approved scope:** This proposal and the exact initial boundary above. The user explicitly authorizes the implementation and final merge; no live E2B test is authorized without the provider's required prior written consent.
- **Approved at:** 2026-09-25 (Asia/Taipei)
- **Constitution change:** NO

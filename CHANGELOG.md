# Changelog

## 0.59.0

### Verified Sandbox Provider Foundation

- Add provider-neutral sandbox capability registry and fail-closed verification matching; `auto` selects worktree for ordinary risk and requires sandbox for high/critical or explicitly untrusted execution.
- Add a disabled, public-data-only E2B candidate with no egress, host mounts, guest credentials or publication authority; verification evidence is freshness- and registry-digest-bound.
- Add a synthetic-only E2B smoke verifier and a main-only manual workflow gated by explicit prior-written-consent confirmation; the optional provider key is never exposed to pull requests or required for baseline/release.
- Extend Execution Isolation and Security Assurance documentation, credential policy, architecture inventory and Scenario 114 coverage. A successful smoke test does not activate the provider or attest its underlying hypervisor. Constitution impact: NO.

## 0.58.0

### Structured Requirement Traceability

- Add optional EARS guidance for functional requirements while preserving READY / NEEDS_CLARIFICATION / BLOCKED and allowing narrative and non-functional requirements to keep their appropriate forms.
- Add an optional Planning Package `REQUIREMENTS.yaml` registry that links stable requirement IDs to acceptance criteria, verification methods and evidence references.
- Add a deterministic structure checker for EARS pattern labels and sentence forms, identifier uniqueness and required acceptance fields; it does not assess natural-language semantics or claim evidence has passed.
- Add Scenario 174 and synchronize Agent/Human guidance, documentation placement and sync contracts. No Constitution, approval authority, Scenario Conformance semantics, or existing project migration changes.

 ## 0.57.0

### Portable Governance Command Core

- Add a canonical Portable Command Registry for `aips.constitution`, `aips.plan` and `aips.impact`, with host-aware Markdown and generic renderers.
- Add `aips commands` list, inspect, render, install, status, upgrade and uninstall lifecycle commands with ownership metadata and conflict preservation.
- Reuse the same renderer from the MCP gateway through the read-only `aips_portable_command` tool; Portable Commands remain advisory and do not grant runtime enforcement or protected-operation authority.
- Add focused contract coverage for registry validation, projection lifecycle and modified-file conflict detection.
- Document Portable Command architecture and bind it to the existing Turn-Aware Global Harness surface; no new Role, Skill, Capability ID, approval authority or Constitution change.

## 0.56.0

### CI-Parity Publication Preflight

- Add one shared publication resolver for local and GitHub validation so base/head, PR-label change class, canonical Core Change Test Matrix and documentation diff base cannot silently diverge.
- Run fast diff, documentation sync, canonical placement and audience checks before the expensive Integration Gate lifecycle; report missing localhost/browser capabilities as `ENVIRONMENT_BLOCKED` instead of a product failure.
- Make documentation impact recursive across placement and synchronization requirements, and ignore Git-ignored metadata such as `.DS_Store` during audience validation.
- Add safe post-squash reconciliation: apply only on the target branch with a clean, tree-equivalent checkout, create a backup branch first, and optionally refresh Project Intelligence metadata.
- Add Project Intelligence `refresh`, which updates revision metadata only when the prior and current tree objects are equivalent; semantic changes remain `SEMANTIC_REFRESH_REQUIRED`.
- Add architecture, repository-health, static-contract and lifecycle coverage plus Scenario 165. Scenario Conformance is now 165/165 automated: 24 deterministic + 87 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- No new Role, Skill, Capability ID, approval authority, merge authority, release authority or production authority. Constitution impact: NO.
## 0.55.0

### MCP Tool-Only Host Compatibility

- Extend the existing MCP access plane with additive read-only Tools for canonical Role / Skill / allowlisted protocol catalog and reads, plus Security Review / Architecture Review / Code Review / Delivery Plan context rendering for hosts that do not expose MCP Resources or Prompts.
- Preserve canonical files and the existing Resources / Prompts surface; the tool-only facade performs no semantic selection and invokes no provider model.
- Mark every AIPS MCP Tool read-only, non-destructive, idempotent and closed-world so compatible review hosts can safely distinguish the gateway's side-effect-free contract.
- Add deterministic review-only configuration output for Windsurf, GitHub Copilot CLI and Amp alongside Cursor, Codex and generic stdio clients. AIPS still never mutates client-owned settings.
- Document the integration policy: use MCP as the default portable ADVISORY plane; add a runtime-native adapter only when a verified turn hook, pre-tool guard or runtime-specific event source is required.
- Keep local stdio, `AIPS_MCP_WORKSPACE` confinement, false protected-operation authority, credential-free operation and all existing native adapters unchanged.
- Add Scenario 164 and raise Scenario Conformance to 164/164 automated: 24 deterministic + 86 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- No new Role, Skill, Capability ID or Approval Gate. Constitution impact: NO.

## 0.54.0

### Managed Shell PATH Integration

- Add explicit `--configure-shell` and `--no-configure-shell` install modes plus an interactive prompt when a terminal is available.
- Add `aips shell install`, `aips shell status` and `aips shell uninstall` for zsh/bash profile integration with idempotent AIPS-owned markers and recorded ownership metadata.
- Make uninstall remove only exact, unmodified AIPS-owned profile content; preserve modified blocks and shared CLI-directory PATH entries unless the user explicitly requests `--remove-shell-integration`.
- Extend `aips doctor` to report CLI discoverability separately from symlink health and show managed, unmanaged, modified, missing or unconfigured shell integration state.
- Add lifecycle evidence for profile preservation, repeat installs, shared CLI directories, modified-block conflicts, paths containing spaces and installer flag parsing.
- Update macOS/Linux and Windows + WSL install entrypoints plus troubleshooting guidance. No Role, Skill, approval gate, runtime adapter authority or Constitution semantics change. Architecture diagrams are unaffected because runtime/Harness topology does not change.

## 0.53.0

### Human Documentation Architecture, Official Docs Site & Installation UX

- Reorganize Human current-behavior documentation around stable topics instead of release-by-release append streams; version history remains in `CHANGELOG.md` and Scenario/evidence history remains in `docs/human/CONFORMANCE.md`.
- Add `config/documentation-placement.yaml` and deterministic `scripts/documentation_placement.py` enforcement: current-behavior documents require one H1, reject release/scenario-style H2 append sections, reject duplicate numeric headings, bind subsystem changes to allowed canonical topics, and fail closed when a new behavior-bearing source has no placement rule.
- Remove the one-time documentation-structure migration bypass after migration completion. Future Human Docs updates must place changed lines inside approved canonical sections or explicitly add a genuine new topic to the placement contract.
- Convert Technology Guide and Evolution Radar overview from append-oriented standalone HTML sources to canonical Markdown rendered by the docs platform; legacy HTML remains compatibility-only and cannot accumulate new feature sections.
- Add an official VitePress Human Docs Site using `docs/human/` as the single canonical source, with sidebar navigation, local search and page outline; renderer output is not committed as a second source of truth.
- Add GitHub Actions Docs Site build on pull requests and main. When GitHub Pages repository configuration is absent, build succeeds and deployment is truthfully reported as `SKIPPED_NOT_CONFIGURED`; enabling Pages remains an explicit repository setting.
- Modernize public installation UX so README / Getting Started no longer require users to learn `mkdir`, `cd`, `git clone` or `bootstrap.sh` as the normal path.
- Add managed macOS/Linux `install.sh`, Windows PowerShell `install.ps1` with truthful WSL handoff, and Windows uninstall launcher contract. `bootstrap.sh` remains only a backward-compatible entrypoint.
- Standardize user-facing lifecycle vocabulary on Install / Update / Uninstall while reusing the existing `aips install`, `aips update`, `aips uninstall` core lifecycle rather than duplicating installer logic.
- Add exact CI coverage for Ubuntu installation lifecycle, macOS shell entrypoint, Windows PowerShell/WSL contract and Docs Site build.
- Add Scenario 163 and raise Scenario Conformance to 163/163 automated: 24 deterministic + 85 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- PR #144 final head `fb2ae5b857a2b4d1e7be148c422d35bbe91c8b08` changed 45 files and passed Core Change Validate Run #1221, Docs Site Run #9, Installation Entrypoints Run #9 and MCP/Codex interoperability Run #10. Core Change Matrix exact changed-files hash: `be602da74c2f5c80e0644a05776e5d9483d57cc3841065bd139ff0991ffed765`.
- PR #144 was squash-merged to main as `422a00f4ed755fd48dd4473cd641522e966aae42`; protected-main Validate Run #1222 succeeded.
- Follow-up PR #145 final head `e44c3d6fb92bf858ac6417fbe97cfa8c92e7daa7` reconciled canonical placement ownership and truthful Pages readiness; exact-head Validate Run #1226 and Docs Site Run #14 succeeded.
- PR #145 was squash-merged to main as `2a33b4e8d5fc6089a55c2e4df0cdbdd34ddb12fb`; protected-main Validate Run #1227 and Docs Site Run #15 succeeded. Pages deployment is currently skipped when repository Pages is not configured, while the VitePress build remains green.
- No new Role, Skill or Approval Gate. Human authority, code merge/release authority and product production authority remain unchanged. Constitution impact: NO.
- Release model remains `VERSION + CHANGELOG + protected-main validation`; no GitHub Release object or tag is introduced.

## 0.52.0

### MCP Interoperability Gateway

- Extend the existing Turn-Aware Global Harness with a portable local-stdio MCP access plane; native Codex / Claude Code / Gemini CLI adapters remain separate and continue to provide runtime-specific context/enforcement capabilities where verified.
- Use the official MCP Python SDK v2 and MCP protocol revision 2026-07-28 rather than implementing custom JSON-RPC or a parallel protocol stack.
- Expose canonical AIPS Roles, Skills and selected orchestration protocols through MCP Resources with progressive disclosure; Role/Skill bodies remain single-source-of-truth files under `roles/` and `skills/`.
- Add reusable MCP Prompts for security review, architecture review, code review and delivery planning. The host model performs semantic reasoning; the MCP server does not invoke a second LLM/provider.
- Add bounded deterministic/read-only MCP Tools for system info, canonical project identity, compact Harness context, explicit Role/Skill bundle validation and existing Deterministic Scheduler delegation.
- Constrain project-oriented MCP tools to `AIPS_MCP_WORKSPACE`, reject paths outside the workspace and keep allowlisted protocol resources separate from arbitrary repository file access.
- Report MCP-only governance truth as `ADVISORY`; the gateway does not claim TURN_NATIVE, TOOL_GUARDED, host-native shell/file/git interception, Human approval, Git publish, merge, release or production authority.
- Keep v0.52 credential-free and local-only: no remote MCP service, OAuth server, hosted AIPS control plane, external Agent API Key or provider/model execution is required.
- Add `aips mcp serve`, `aips mcp inspect` and review-only `aips mcp config --client cursor|codex|generic`; AIPS does not silently mutate third-party client-owned MCP configuration.
- Add Scenario 162 and raise Scenario Conformance to 162/162 automated: 24 deterministic + 84 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- PR #142 final head `c87a42d652c16468e1d7d3ad9d6ddc4ef8b62957` passed Core Change Validate Run #1209 with `matrix_required=true` and exact changed-files hash `3452321ad833a9b53d653e8c85e99f6a7cf24394719e029d5637bf2a12780af5`.
- The exact PR head also passed MCP/Codex interoperability Run #3 using the real local stdio MCP protocol session and pinned Codex CLI 0.155.1 registration/discovery without provider inference.
- PR #142 was squash-merged to main as `53ba44ff6dcdb775fd319e2f670dae43270f0e83`; protected-main Validate Run #1210 succeeded.
- No new Role, Skill or Approval Gate. Human authority, merge/release authority and Constitution semantics remain unchanged. Constitution impact: NO.
- Release model remains `VERSION + CHANGELOG + protected-main validation`; no GitHub Release object or tag is introduced.

## 0.51.0

### Parallel Runtime Resource Isolation

- Extend the existing Execution Isolation lifecycle with repository-scoped atomic TCP port leases for parallel AIPS-managed worktrees; no separate Port Manager, Role, Skill, Capability ID or Approval Gate is introduced.
- Store runtime lease state outside project source under the AIPS external config namespace and serialize cross-process allocation so concurrent AIPS agents cannot commit the same port lease.
- Use deterministic candidate ordering from repository/isolation/resource identity while treating current host port occupancy as an explicit runtime input; a preferred port is a hint, not a guaranteed number.
- Probe host TCP bind availability before recording a lease and support bounded `runtime-reallocate` recovery when an external process wins a post-probe address-in-use race.
- Emit canonical runtime variables `AIPS_PORT_<RESOURCE>` and `AIPS_PORT` when unambiguous, plus only explicitly requested aliases such as `PORT`.
- Add `runtime-lease`, `runtime-reallocate`, `runtime-release` and `runtime-reconcile`; clean isolation removal releases remaining leases, while runtime release remains independent from dirty-worktree preservation.
- Reconcile only orphaned leases whose AIPS isolation is no longer ACTIVE; an ACTIVE-but-idle lease is not guessed stale.
- Extend Task Graph runtime metadata and Deterministic Scheduler validation/dispatch handoff. Scheduler validates and propagates runtime requests but does not allocate host resources.
- Limit v0.51 to TCP port coordination; Docker networks, database/schema namespaces, Redis indexes, GPU/resource quotas, process lifecycle management and external provider credentials remain out of scope.
- Add Scenario 161 and raise Scenario Conformance to 161/161 automated: 24 deterministic + 83 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- PR #140 final head `45c30d88b26e97e48d9358d0463c1687254c00eb` passed Core Change Validate Run #1203 with `matrix_required=true` and exact changed-files hash `a835027c416f6d52f61d2d8b498526af61862f07642ab09845f88a03739661ce`.
- PR #140 was squash-merged to main as `c16537a2711b4272de871d4eeb88a2975c7c29a3`; protected-main Validate Run #1204 succeeded.
- Initial Validate Run #1202 correctly blocked release because deterministic-execution documentation sync required `orchestration/INTEGRATION_GATE.md`; the documentation contract and Core Change Matrix binding were reconciled before the final green candidate.
- Human authority, merge/release authority and Constitution semantics remain unchanged. Constitution impact: NO.
- Release model remains `VERSION + CHANGELOG + protected-main validation`; no GitHub Release object or tag is introduced.

## 0.50.0

### Governance Audit Retention & Verification Policy

- Add a deterministic Governance Audit Catalog over existing v0.49 portable audit bundles; no parallel audit subsystem is introduced.
- Verify bundles and retained external anchors before catalog registration, then index exact bundle identity, subject, repository revision, event count, chain head, manifest/anchor digests, evidence digests, and checkpoint public-key fingerprints.
- Add deterministic provenance discovery so auditors can locate the correct bundle by bundle id, subject, repository revision, chain head, or checkpoint key id.
- Preserve checkpoint key-rotation evidence: reuse of one key id with a changed fingerprint fails closed, while rotation to a distinct key id remains auditable without granting key-management authority.
- Add advisory-only retention planning with KEEP_FULL, HOLD_FULL, and REVIEW_DUE states plus deterministic minimal digest records for Human review.
- Legal hold overrides time-based review. The helper exposes no delete/compact command and always keeps automatic_delete=false and deletion_authorized=false.
- Treat configured retention durations as operational defaults only, not legal/regulatory retention requirements. SAL 2+ defaults require an independently retained anchor and SAL 4 registration requires signed checkpoint evidence.
- Keep the baseline credential-free; no external Agent/provider credential, new Role, Skill, Capability ID, Approval Gate, merge authority, release authority, or production authority is introduced.
- Add Scenario 160 and raise Scenario Conformance to 160/160 automated: 24 deterministic + 82 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- PR #138 final head `02efecddbba4a93ee64e8a96daaccce2b3f73110` passed Core Change Validate Run #1196 with `matrix_required=true` and exact changed-files hash `64bed582f30245a8d8a77d1ec744a142ac4b8d0ad8b8b80e7cf908862491e690`.
- PR #138 was squash-merged to main as `f2797885e498dc4f1cba405a4c89fb67cdc9edb1`; protected-main Validate Run #1197 succeeded.
- Human authority and Constitution semantics remain unchanged. Constitution impact: NO.
- Release model remains `VERSION + CHANGELOG + protected-main validation`; no GitHub Release object or tag is introduced.

## 0.49.0

### Portable Governance Audit Bundle

- Extend the v0.48 Verifiable Governance Audit Chain with deterministic `bundle-create` / `bundle-verify` commands in the existing `scripts/governance_audit.py`; no parallel audit subsystem is introduced.
- Produce a portable directory bundle containing `AUDIT.jsonl`, `MANIFEST.json`, optional evidence files, checkpoint public keys and `ANCHOR.json`.
- Bind the exact repository revision, ledger SHA-256, event count, chain head, evidence-file SHA-256, public-key SHA-256/fingerprint and authority=false declarations.
- Support an independently exported anchor that binds repository revision + event count + chain head + MANIFEST digest; document that the bundle's internal anchor alone is not an independent trust source.
- Require recorded Ed25519 checkpoint history to verify against supplied public keys before bundle creation; HMAC authentication can be verified when runtime material is supplied but HMAC material is never persisted.
- Exclude signing private keys, HMAC material, source absolute paths, prompts and private reasoning from bundle evidence.
- Keep the baseline flow credential-free and network-free; no blockchain, remote timestamp service, central audit server or external Agent/provider credential is required.
- Add tamper tests for bundled evidence, ledger tail truncation, external anchor mutation and bundled public-key replacement.
- Add Scenario 159 and raise Scenario Conformance to 159/159 automated: 24 deterministic + 81 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- PR #136 final head `1bc85418eeefb5434623c50796dfb6cf2eb94cb2` passed Core Change Validate Run #1189 with `matrix_required=true` and was squash-merged to main as `8433250d8ab7d51f132dba1e2abc6e368feb616f`; protected-main Validate Run #1190 succeeded.
- Initial Run #1188 passed functional validation but its pull-request event snapshot preceded the Core Change label, so it was not used as the merge-authorizing Matrix evidence; an empty-tree binding commit retriggered exact Core Change validation without changing the diff.
- Human authority, merge/release authority and Constitution semantics remain unchanged. Constitution impact: NO.
- Release model remains `VERSION + CHANGELOG + protected-main validation`; no GitHub Release object or tag is introduced.

## 0.48.0

### Verifiable Governance Audit Chain

- Extend the existing Enforceable Governance evidence surface with a deterministic tamper-evident JSONL audit ledger; no new Approval Gate, Role, Skill, or Capability ID is introduced.
- Canonicalize governance-boundary events and bind them with SHA-256 event hashes plus previous-chain hashes so edits, reordering, and interior deletion are detectable.
- Add externally anchored `expected_chain_head` / event-count verification so suffix truncation can be detected when an auditor retains an independent anchor or equivalent signed checkpoint.
- Add optional HMAC-SHA256 runtime authentication and optional Ed25519 signed checkpoints; baseline hash-chain verification remains credential-free and requires no external Agent/provider key.
- Keep HMAC secrets and signing private keys outside Git, prompts, audit events, run state, and Actions artifacts; authenticated/signed existing history must verify before append.
- Integrate the audit contract with Security Assurance / SAL guidance, Release Readiness, Architecture Surface accounting, Human architecture/security documentation, and the Technology Guide.
- Add Scenario 158 and raise Scenario Conformance to 158/158 automated: 24 deterministic + 80 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- PR #134 exact final head `4aad25f6a18ec465f387393ee7444c2bdbdf247f` passed Validate Run #1184 and was squash-merged to main as `71c61b137631768206a1c4e541b023b596379d7a`; protected-main Validate Run #1185 succeeded.
- Earlier PR runs #1182 and #1183 correctly caught lint, Architecture Surface, Documentation Consistency, and secret-scanner issues; all were reconciled within the approved v0.48.0 scope before the final green candidate.
- Human authority, merge/release authority, and Constitution semantics remain unchanged. Constitution impact: NO.
- Release model remains `VERSION + CHANGELOG + protected-main validation`; no GitHub Release object or tag is introduced.

## 0.47.0

### Controlled Maintenance Reconciliation

- Add a Human-authorized one-time exact branch-cleanup manifest while keeping ordinary Branch Hygiene classification/reporting read-only.
- Bind every approved cleanup target to an exact branch name, expected head SHA, and merged PR evidence; preserve persistent, unclassified, pending, moved, and unproven branches.
- Preflight the complete cleanup batch before the first deletion so any mismatched target blocks the batch without partial cleanup.
- Preserve local Git integration proof as the primary path and add a GitHub merged-PR exact-head fallback for historical squash-merged branches whose integration can no longer be reconstructed from current-main patch/merge-tree history.
- Revalidate merged-PR fallback evidence at runtime: merged state, exact head SHA, exact head ref, and base=main must all match the approved manifest.
- Initial protected-main Branch Hygiene Run #2 failed before deleting any branch because local-only integration proof produced false negatives for historical squash merges; no partial deletion occurred.
- Fix PR #132 corrected the proof model without relaxing exact branch/SHA authority; exact-head Validate Run #1178 succeeded and protected-main Validate Run #1179 succeeded after merge.
- Branch Hygiene Run #3 completed successfully and removed exactly 60 approved merged branches, reducing the remote branch inventory from 100 to 40 while preserving unproven and persistent branches.
- Add durable lifecycle reconciliation for historical Evolution Radar Issue #79: covered capabilities remain COVERED, anomaly evidence remains ADOPTED_WITH_BOUNDS, provider/model verification remains unclaimed, and semantic-intent governance remains DEFERRED.
- Close Issue #79 as completed only after durable current-main reconciliation; any future semantic-intent progression requires fresh current-main evidence plus a new explicit Human Decision.
- Add Scenarios 156–157 and raise Scenario Conformance to 157/157 automated: 24 deterministic + 79 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- Feature PR #131 exact head `0fbc9b6131ce8ccd1dff297775c945e03ed6faf5` passed Validate Run #1176 and merged to main as `a21cc1912c081403f1855a5e5e038ea035c48f3a`; protected-main Validate Run #1177 succeeded.
- Fix PR #132 exact head `42b4c9c360e0c0b9621997081219ada8ccbd1ac2` passed Validate Run #1178 and merged to main as `9781871cabc6a5ba1c7a3c218ca9cfefd7572d5a`; protected-main Validate Run #1179 succeeded.
- No new Role or Skill. Constitution impact: NO.
- Release model remains `VERSION + CHANGELOG + protected-main validation`; no GitHub Release object or tag is introduced.

## 0.46.0

### Evolution Effectiveness Metrics & Feedback Loop

- Add a credential-free monthly effectiveness layer over durable weekly Evolution Radar Issues and comments.
- Aggregate raw/unique signal observations, duplicate rate, deterministic shortlist/semantic selection, latest semantic recommendation states, Human Decisions, provider-neutral Trial handoffs, Trial PASS/FAIL/BLOCKED results, and Trial→ADOPT bindings.
- Attribute collected/shortlisted/semantic/actionable/Trial/PASS/adoption observations back to exact source provenance.
- Calculate deterministic basis-point ratios for shortlist yield, semantic yield, actionable conversion, Trial conversion, adoption conversion, and source failure rate.
- Emit `REVIEW_LOW_SHORTLIST_YIELD`, `REVIEW_HIGH_FAILURE_RATE`, and `REVIEW_ZERO_ACTIONABLE_AFTER_SEMANTIC` only after configured minimum observations.
- Keep automatic source reweighting, source enable/disable, source/config mutation, code change, PR, merge and release authority false.
- Add monthly `evolution-effectiveness` workflow on day 2 after the monthly Radar review; it uses `contents: read + issues: write` only and requires no external Agent/provider credential.
- Reconcile one durable `Evolution Effectiveness [monthly] YYYY-MM` Issue per cohort; no review flags closes it as completed, while deterministic review flags keep/reopen it for Human review.
- Register the effectiveness script/config/workflow in the Evolution Radar documentation-sync mapping and Architecture Surface Inventory.
- Add Scenario 155 and raise Scenario Conformance to 155/155 automated: 24 deterministic + 77 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- Feature PR #129 exact final head `80d51851bd0c2074b79939a6cf1f7ee141e96aea` passed validate Run #1172.
- PR #129 was squash-merged to main as `5340dc82ed010e19f4c17b0edac1814a312b5535`; protected-main validate Run #1173 succeeded.
- No new Role or Skill. Constitution impact: NO.
- Release model remains `VERSION + CHANGELOG + protected-main validation`; no GitHub Release object or tag is introduced.

## 0.45.0

### Provider-neutral Controlled Trial Handoff

- Add deterministic Controlled Trial provider resolution across `auto`, the existing pinned OpenAI Codex executor, and a provider-neutral handoff.
- When the optional `OPENAI_API_KEY` is unavailable, `auto` now emits a credential-free `TRIAL_HANDOFF_READY` artifact instead of treating credential absence as a failed experiment.
- Bind the handoff to the exact repository baseline, Human Decision fingerprint, Trial fingerprint, approved scope/paths, forbidden paths, changed-file/diff limits, worktree-isolation requirement, and deterministic repository validation command.
- Explicitly require `external_executor_may_claim_pass=false`; compatible external Agents may execute the bounded contract, but PASS/FAIL remains valid only after AIPS deterministic scope/diff/commit/repository validation.
- Preserve the existing pinned Codex Action path when it is selected/resolved and the optional credential exists.
- Keep publication, remote branch/PR, merge, release, and Human-adoption authority false for both direct execution and handoff.
- Reconcile the external credential registry so missing OpenAI Trial credentials resolve to `TRIAL_HANDOFF_READY` rather than the obsolete `TRIAL_NOT_EXECUTED` behavior.
- Add Scenario 154 and raise Scenario Conformance to 154/154 automated: 24 deterministic + 76 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- Initial PR #127 validation correctly detected that the workflow did not visibly expose the `TRIAL_HANDOFF_READY` state; the workflow now writes the state into the GitHub Job Summary without weakening any gate.
- Feature PR #127 exact final head `d833ad33e3bdf83bdc3e8e501e08e30636d2725f` passed validate Run #1168.
- PR #127 was squash-merged to main as `0c87c6fb9c31dfe00d11e7922c83317f342101e3`; protected-main validate Run #1169 succeeded.
- No new Role or Skill. Constitution impact: NO.
- Release model remains `VERSION + CHANGELOG + protected-main validation`; no GitHub Release object or tag is introduced.

## 0.44.0

### Evolution Evidence Quality & Primary-source Corroboration

- Add deterministic 0–4 evidence-quality levels derived from exact multi-source provenance.
- Distinguish single-community discovery, multi-community recurrence, primary evidence, primary+community corroboration, and multi-primary corroboration.
- Require evidence level >= 2 before a semantic provider may emit advisory ADOPT.
- Preserve evidence level, strength, primary/community source counts, and exact provenance through weekly, monthly, and quarterly evidence.
- Add a bounded evidence-quality bonus to credential-free deterministic pre-analysis without turning evidence strength into a suitability decision.
- Prevent semantic providers from inventing or upgrading deterministic evidence metadata.
- Synchronize Human/Agent Evolution Radar and Technology Guide documentation.
- Add Scenario 153 and raise Scenario Conformance to 153/153 automated.
- Initial validation correctly exposed a stale ADOPT fixture using level-0 evidence plus required documentation synchronization; both were corrected without weakening the evidence floor.
- Feature PR #125 exact final head `002a3215b7c5f503524da48d4a8d909181eff9e2` passed validate Run #1163.
- PR #125 was squash-merged to main as `58dcc4a82a2c5438e390fe1dc7668f00cfccc620`; protected-main validate Run #1164 succeeded.
- No new Role or Skill. Constitution impact: NO.
- Release model remains `VERSION + CHANGELOG + protected-main validation`; no GitHub Release object or tag is introduced.

## 0.43.0

### Technology Intelligence Expansion

- Expand the weekly Evolution Radar into a bounded Technology Intelligence funnel with six configured community discovery sources plus retained primary/vendor evidence sources.
- Require a healthy floor of five successful community sources when available; best-effort source failures remain explicit degraded evidence and are never fabricated away.
- Increase per-source collection to at most eight candidates and add a deterministic global raw-signal cap of 50 using round-robin source fairness.
- Preserve source roles and multi-source provenance through deduplication with DISCOVERY_ONLY, PRIMARY_SOURCE, and PRIMARY_CORROBORATED verification states.
- Extend credential-free deterministic local pre-analysis with a Human shortlist capped at 12, a near-duplicate-aware semantic queue capped at 10, and an actionable recommendation budget capped at 5.
- Bind the semantic analysis package to the exact deterministic queue; signals outside that queue remain truthfully ANALYSIS_PENDING and partial semantic coverage is explicit.
- Require primary-source corroboration before an explicit community-only discovery signal may produce ADOPT; forum/community popularity alone is not adoption evidence.
- Keep optional semantic providers and the existing provider-neutral handoff; no external Agent/provider credential becomes a baseline or release prerequisite.
- Preserve Protected Human Authority: research remains evidence/recommendation-only and grants no implementation, PR, merge, release, publication, or Human-decision authority.
- Add Scenario 152 and raise Scenario Conformance to 152/152 automated: 24 deterministic + 74 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- Initial PR #123 candidate validation correctly failed on a stale monthly rollup expectation after the expanded source fixture; the test expectation was reconciled without weakening the implementation.
- Feature PR #123 exact final head `614f32c8e7914da5fd562aed75c613474dd423ec` passed validate Run #1155.
- PR #123 was squash-merged to main as `a3539935ca35634ecf4c5f428f018fafc16b7390`; protected-main validate Run #1156 succeeded.
- No new Role or Skill. Constitution impact: NO.
- Release model remains `VERSION + CHANGELOG + protected-main validation`; no GitHub Release object or tag is introduced.

## 0.42.0

### Evolution Radar Quarterly Deterministic Review

- Add a credential-free deterministic Quarterly Review mode to Evolution Radar.
- Schedule quarterly review on the first day of January, April, July and October, reviewing the previous calendar quarter.
- Reuse durable monthly Evolution Radar evidence only; quarterly review performs no second public-source collection.
- Bind the exact `YYYY-QN` review period, its three calendar months and the number of valid monthly evidence bundles consumed.
- Aggregate recurrence deterministically by signal fingerprint while keeping the existing source provenance/failure evidence.
- Reset quarterly recommendation state to `ANALYSIS_PENDING` rather than promoting monthly semantic states into a new quarterly suitability or adoption conclusion.
- Preserve provider-neutral operation: no `OPENAI_API_KEY`, `GEMINI_API_KEY` or other external Agent/provider credential is required for the quarterly rollup.
- Preserve Protected Human Authority: no automatic ADOPT, code mutation, implementation PR creation, merge, release or publication authority.
- Add Scenario 151 and raise Scenario Conformance to 151/151 automated: 24 deterministic + 73 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- Feature PR #121 exact head `0b4b567da8db8fe313c2e10f22f14c8b6a962882` passed validate Run #1148.
- PR #121 was merged to main as `e38d124b219bd048c843eeac6a4d0ec69b6c035a`; protected-main validate Run #1149 succeeded.
- No new Role or Skill. Constitution impact: NO.
- Release model remains `VERSION + CHANGELOG + protected-main validation`; no GitHub Release object or tag is introduced.

## 0.41.0

### Repository Health Scheduled Maintenance Observation

- Add a dedicated credential-free `.github/workflows/repository-health.yml` maintenance lane with weekly Monday 10:30 Asia/Taipei scheduling and manual dispatch.
- Audit the exact checked-out default-branch revision and always retain `repository-health-report.json` as a 30-day GitHub Actions artifact plus a concise Job Summary.
- Keep PASS observational only: no drift Issue is created when the deterministic report passes.
- On `DRIFT_DETECTED`, build a Human-review Issue from bound drift evidence, deduplicate open notifications by deterministic evidence fingerprint, and keep the workflow visibly failed until the drift is reviewed.
- Preserve detector truth boundaries: no `OPENAI_API_KEY`, `GEMINI_API_KEY`, or other external Agent/provider credential is required to compute Repository Health.
- Preserve authority boundaries: workflow permissions are `contents: read` plus `issues: write` for notification only; no automatic remediation, repository-content write, implementation PR, merge, release, or publication authority.
- Bind the maintenance workflow into the Repository Health config, explicit Architecture Surface Inventory, Human/Agent maintenance documentation and validation contracts.
- Add Scenario 150 and raise Scenario Conformance to 150/150 automated: 24 deterministic + 72 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- Initial feature head `2f9016d7c3bd80b0bb1bd8014a21d12695c1358d` correctly failed validate Run #1143 because Documentation Consistency required Technology Guide plus Human/Agent Conformance synchronization.
- Corrected feature final head `3685f21564a0fb537c69cb033fd5973951da4c5c` passed exact-head validate Run #1144.
- PR #119 was merged to main as `c2679f9d8d8d0725f28d8a0a771f4fdf61e08e72`; protected-main validate Run #1145 succeeded.
- No new Role or Skill. Constitution impact: NO.
- Release model remains `VERSION + CHANGELOG + protected-main validation`; no GitHub Release object or tag is introduced.

## 0.40.0

### Repository Health Architecture Surface Inventory + CI Evidence

- Add `config/architecture-surfaces.yaml` as the explicit deterministic inventory for major AIPS architecture surfaces.
- Classify all 27 current Capability Map entries exactly once across 9 major surfaces, eliminating the prior non-guard/gate accounting blind spot without semantic inference.
- Bind every surface to required repository paths, canonical Capability Map documentation and validation paths.
- Add `architecture_surface_drift` for unclassified capabilities, duplicate capability assignment, missing required paths, canonical-document mismatches and validation paths not bound by Scenario Conformance or the repository validator.
- Keep bounded `*_guard.py` / `*_gate.py` discovery as a secondary orphan safety net rather than a substitute for the explicit inventory.
- Extend the deterministic input manifest to bind the architecture inventory, declared surface paths, validation paths and the top-level repository validator.
- Add exact-candidate Repository Health CI evidence: `.github/workflows/validate.yml` writes `repository-health-report.json` and uploads it as a short-retention artifact with an immutable pinned upload action.
- Preserve Repository Health as Detect + Evidence + Human Review only: no automatic remediation, code-change, branch/PR, merge, release or publication authority.
- Require no `OPENAI_API_KEY`, `GEMINI_API_KEY`, other external Agent/provider credential or provider network call.
- Add Scenario 149 and raise Scenario Conformance to 149/149 automated: 24 deterministic + 71 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- Initial feature Run #1138 correctly failed on a missing Technology Guide sync and incomplete repository-validator manifest binding; both were corrected without weakening any gate.
- Feature PR #117 final head `842a2fb84299ef3be6e4842b693b65d4b70691ff` passed exact-head validate Run #1139; Repository Health artifact `repository-health-35516387867-1` was published.
- PR #117 was merged to main as `6616e84fef902e10568a6dffb3b06f16ec5c6aff`; protected-main validate Run #1140 succeeded.
- Roles remain 12 and Skills remain 25.
- Constitution impact: NO. Protected Human Authority and existing merge/release/publication boundaries remain unchanged.
- Release model remains unchanged: no GitHub Release object or tag is introduced; release truth remains `VERSION + CHANGELOG + protected-main validation`.

## 0.39.0

### Repository Health Deterministic Evidence Binding

- Extend the credential-free Repository Health / Architecture Drift detector with a complete deterministic input manifest for the repository surfaces it actually evaluates.
- Bind every existing input file by SHA-256 while keeping missing bound inputs explicit instead of silently omitting them.
- Add truthful Git workspace state to Repository Health evidence: `EXACT_REVISION`, `DIRTY_WORKTREE`, or `NO_GIT`.
- Keep dirty workspace state as evidence metadata rather than architecture drift by itself; architecture findings remain tied to configured deterministic contracts.
- Add a reproducible evidence fingerprint derived from repository revision, workspace state, bound input manifest, and drift findings so equivalent evidence can be compared without semantic inference.
- Preserve the existing Repository Health detector and Scenario Conformance semantics rather than introducing another checker or evidence system.
- Require no `OPENAI_API_KEY`, `GEMINI_API_KEY`, other external Agent/provider credential, or external network request.
- Preserve Detect + Evidence + Human Review only: no automatic remediation, code-change, branch/PR, merge, release, publication, runtime-enforcement, or credential-acquisition authority.
- Add Scenario 148 and raise Scenario Conformance to 148/148 automated: 24 deterministic + 70 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- Feature PR #115 final head `f9ae095dc9f6953be8cab7b711fdd89059c1145e` passed exact-head validate Run #1134.
- PR #115 was merged to main as `4bb2168a0a8250eabe4d41afc5240ac9461551b6`; protected-main validate Run #1135 succeeded.
- Roles remain 12 and Skills remain 25.
- Constitution impact: NO. Protected Human Authority and existing merge/release/publication boundaries remain unchanged.
- Release model remains unchanged: no GitHub Release object or tag is introduced; release truth remains `VERSION + CHANGELOG + protected-main validation`.

## 0.38.0

### Repository Health / Architecture Drift Deterministic Detection

- Add a credential-free deterministic Repository Health / Architecture Drift detector that compares source-controlled architecture declarations with actual repository surfaces.
- Reuse existing truth surfaces instead of creating parallel frameworks: Capability Map for capability identity/docs, Scenario Conformance for registry/evidence integrity, Integration Gate for exact-candidate validation, Documentation Consistency for changed-file documentation impact, Change Impact for proposed-change scope, and External Credential Dependency Guard for credential policy.
- Detect bounded drift classes for missing capability targets, orphan core guard/gate surfaces, stale canonical documentation references, Scenario evidence drift, and validation-workflow contract drift.
- Reconcile a real baseline catalog gap by registering the already-existing Integration Gate in the Capability Map rather than suppressing the finding.
- Add deterministic input binding through repository revision plus config, Capability Map, and Scenario registry digests.
- Preserve a bounded v1 false-positive/false-negative contract: explicit source-controlled surfaces and guard/gate discovery only; no semantic inference over arbitrary files.
- Keep the capability Detect + Evidence + Human Review only: no automatic remediation, code-change, branch/PR, merge, release, publication, runtime-enforcement, or credential-acquisition authority.
- Require no `OPENAI_API_KEY`, `GEMINI_API_KEY`, other external Agent/provider credential, or additional external network request.
- Add Scenario 147 and raise Scenario Conformance to 147/147 automated: 24 deterministic + 69 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- Feature PR #113 final head `4941285a3dd94d44acc5f6715c0d3ba93298a3ad` passed exact-head validate Run #1129.
- PR #113 was merged to main as `0fbd125abd58ece77e21aa92182d0837385a7994`; protected-main validate Run #1130 succeeded.
- Roles remain 12 and Skills remain 25.
- Constitution impact: NO. Protected Human Authority and existing merge/release/publication boundaries remain unchanged.
- Release model remains unchanged: no GitHub Release object or tag is introduced; release truth remains `VERSION + CHANGELOG + protected-main validation`.

## 0.37.0

### Evolution Radar Local Deterministic Pre-analysis

- Add a credential-free deterministic first-pass Evolution Radar triage lane before any optional semantic provider.
- Extend `scripts/evolution_analysis.py` with source-controlled local preanalysis that uses only already-collected signal titles/metadata, recurrence evidence, `config/evolution-analyzer.yaml`, and the current Capability Map.
- Add deterministic topic-category hints, exact existing-capability hints, and bounded token/Jaccard near-duplicate title clustering.
- Add HIGH / MEDIUM / LOW Human review priority derived only from declared rule weights, capability matches, and recurrence metadata. Review priority is reading order only; it is not a COVERED/HOLD/ASSESS/TRIAL/ADOPT recommendation.
- Preserve semantic truth boundaries: `semantic_suitability_inferred=false`, `recommendation_state_mutated=false`, and all semantic recommendations remain `ANALYSIS_PENDING` until a separately validated semantic analyzer result is bound.
- Require no `OPENAI_API_KEY`, `GEMINI_API_KEY`, or other external Agent/provider credential, and perform no additional network request beyond the existing Radar evidence collection step.
- Bind every preanalysis artifact to the exact repository revision, evidence digest, local-preanalysis config digest, and Capability Map digest.
- Embed the deterministic preanalysis artifact into the Human review Issue alongside the existing provider-neutral semantic-analysis handoff.
- Add executable lifecycle evidence proving identical inputs produce identical output, near-duplicate clustering is deterministic, capability hints reference only registered capabilities, tampered semantic-suitability claims are rejected, and credential-required local configuration fails validation.
- Add Scenario 146 and raise Scenario Conformance to 146/146 automated: 24 deterministic + 68 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- Initial exact-head Run #1123 correctly rejected an unquoted YAML `on` stopword that PyYAML parsed as boolean; the configuration was corrected rather than weakening validation.
- Feature PR #111 exact final head `630df595e5e979b74ca793e1d1eccfb14eeaf699` passed exact-head validate Run #1124.
- Feature exact-head changed-files hash: `f20945a9668eeaad41cabca4f6b44fe420b96ae171858138b126480daa6b6160`; Core Matrix hash: `56804b920e106af9bcfeaebcc2a5c6628c9cda2837138ca5840b152895c5f258`; candidate fingerprint: `cbe0da59d9cd35faebc6ae24c8fb63718be77ec106a3118e425cdda7dd6646af`.
- PR #111 was squash-merged to main as `68bc930233a9d6b61c50d78b6b002cd0d9b2584c`; protected-main validate Run #1125 succeeded.
- Roles remain 12 and Skills remain 25.
- Constitution impact: NO. Protected Human Authority, merge/release/publication authority, runtime enforcement, automatic remediation, and credential policy remain unchanged.
- Real Gemini provider/model verification remains optional and unexecuted; this release adds no replacement authentication flow.
- Release model remains unchanged: no GitHub Release object or tag is introduced; release truth remains `VERSION + CHANGELOG + protected-main validation`.

## 0.36.0

### External Credential Dependency Guard

- Add a deterministic, source-controlled External Credential Dependency Guard so external Agent/provider API keys cannot silently become AIPS baseline or release prerequisites.
- Add `config/external-credentials.yaml` as the explicit registry for external provider credentials and their allowed executable/configuration consumers. Current registered credentials are `GEMINI_API_KEY` and `OPENAI_API_KEY`; both remain optional with `required_for_baseline=false` and `required_for_release=false`.
- Add `scripts/external_credential_guard.py` to scan GitHub Actions workflows, configuration, and Python scripts for external credential references; undeclared credentials, undeclared/stale consumers, pull-request secret exposure, or policy attempts to make an external credential baseline/release-required fail repository validation.
- The first exact-head validation demonstrated the guard working as intended by discovering the previously omitted existing `config/evolution-trial.yaml` `OPENAI_API_KEY` consumer; the registry and synchronized Evolution Radar documentation were then corrected rather than weakening the guard.
- Narrow `.github/workflows/retrieval-semantic-trial.yml` so the local/default embedding Trial no longer receives `OPENAI_API_KEY`; the secret is injected only into the explicitly selected `remote` step.
- Preserve credential-free defaults: Evolution Radar continues provider-neutral handoff without an external semantic provider key; Retrieval defaults to local embedding; Gemini CLI real-runtime/tool/AfterTool verification remains credential-free.
- Complete every non-live Gemini provider-key path requested by the maintainer: repository validation now executes `gemini_provider_session_verification.py` with `GEMINI_API_KEY` absent and requires `SKIPPED_NOT_CONFIGURED`, `provider_verification_enabled=false`, `required_for_release=false`, `live_provider_session_verified=false`, and `provider_model_execution_verified=false`.
- Reconcile Secret Handling, Security Assurance, Technology Guide, Evolution Radar, Execution Isolation, Capability Map, and Conformance documentation so optional missing credentials use truthful non-PASS states and do not block unrelated baseline/release work.
- Add Scenario 145 and raise Scenario Conformance to 145/145 automated: 24 deterministic + 67 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- Feature PR #109 exact final head `177d62cf2a84a69671d77a35143c06ca722268b9` passed exact-head validate Run #1119 with changed-files hash `08b6c8d087c4b4bdabaabc5d6241d9156520a1738f5d3d53e6778ee5b57a00ea`.
- PR #109 was squash-merged to main as `6bed9e16691fa58ae2ba938811692c7905d57acf`; protected-main validate Run #1120 succeeded.
- The real `GEMINI_API_KEY` provider/model connection remains intentionally unexecuted and unverified. No provider PASS is claimed, no replacement OAuth/Vertex/OIDC authentication is introduced, and live provider/model truth remains false.
- Roles remain 12 and Skills remain 25.
- Constitution impact: NO. Protected Human Authority, merge/release/publication authority, runtime enforcement, automatic remediation, and credential-creation authority remain unchanged.
- Release model remains unchanged: no GitHub Release object or tag is introduced; release truth remains `VERSION + CHANGELOG + protected-main validation`.

## 0.35.0

### Optional External Provider Credential Policy

- Reclassify external Agent/provider credentials as optional capability inputs rather than baseline AIPS prerequisites.
- Keep the trusted-main Gemini live provider-session verifier/workflow available as an opt-in enhancement, but change missing `GEMINI_API_KEY` behavior from a blocking credential state to truthful `SKIPPED_NOT_CONFIGURED` / `NOT_CONFIGURED_BY_POLICY`.
- When no credential is configured, report `provider_verification_enabled=false` and `required_for_release=false`; skip provider-specific dependency installation, Gemini CLI provider verification, real provider/model inference and exact-provider candidate assertion.
- Preserve truth boundaries: `live_provider_session_verified=false` and `provider_model_execution_verified=false` remain false until real provider evidence exists. No fake-response/runtime evidence is promoted to provider verification.
- Preserve the already verified credential-free Gemini CLI runtime path from v0.34.0: real CLI binary, built-in tools, extension loading and AfterTool capture remain independent of provider credentials.
- Do not introduce replacement authentication. OAuth, Vertex AI credentials, Google Service Account, GitHub OIDC / Workload Identity Federation and other external login flows remain disabled unless a later Human Decision explicitly adopts them.
- Keep the provider workflow off `pull_request`, maintain `contents: read`, never persist credential values, and retain exact-SHA/provider PASS requirements when a credential is explicitly configured.
- Record the Human provider-credential policy in `ISSUE_79_PROVIDER_CREDENTIAL_POLICY_DECISION.yaml` and update durable provider-session truth to `NOT_CONFIGURED_BY_POLICY`.
- Add Scenario 144 to deterministically lock the optional-credential contract and raise Scenario Conformance to 144/144 automated: 23 deterministic + 67 lifecycle + 54 agent_eval, 0 manual, 0 uncovered.
- PR #106 exact head `af21622ba76ecba2dce4408dbdad0b63c4cb419c` passed validate Run #1110; it was squash-merged as `b50f3c64e8548e173f867bea6ae069892c6169bd`; protected-main validate Run #1111 succeeded.
- Gemini provider workflow Run #2 on `b50f3c64e8548e173f867bea6ae069892c6169bd` succeeded through the disabled path with `credential_present=false`, `provider_verification_enabled=false`, `required_for_release=false`, and live provider/model verification false.
- PR #107 exact final head `a3d395505dc5899ae464b008989dedbf59150016` passed validate Run #1114; it was squash-merged as `c8c5d5ea90adc35322c63583d7e033e5581c7c54`; protected-main validate Run #1115 succeeded.
- Roles remain 12 and Skills remain 25.
- Constitution impact: NO. Protected Human Authority, merge/release/publication authority, runtime enforcement and automatic remediation boundaries remain unchanged.
- Release model remains unchanged: no GitHub Release object or tag is introduced; release truth remains `VERSION + CHANGELOG + protected-main validation`.

## 0.34.0

### Gemini CLI Exact-Candidate Real-Runtime Verification

- Add Scenario 143 and a dedicated `gemini-runtime-verification` GitHub Actions workflow that pins official Gemini CLI v0.60.0 and executes the actual bundled CLI binary on the exact pull-request head.
- Use Gemini CLI's official `--fake-responses` interface only for deterministic model turns; the real CLI, built-in `read_file`, `write_file`, `replace` tools, extension loader, and AIPS `AfterTool` hook execute normally.
- Verify real workspace mutation for `write_file` and `replace`, plus 3/3 expected canonical observable events, zero unexpected event loss, zero raw/private/secret leakage, and no sink when capture is disabled.
- Enable Gemini CLI `experimental.extensionConfig` and pass the non-secret capture controls through the isolated workspace `.env`, matching the official extension-settings path instead of relying on parent-process environment inheritance.
- Fix a real Gemini extension integration defect: all Gemini hook wrappers now resolve their physical source path before locating the AIPS repository, so symlink-based extension loading under `~/.gemini/extensions` cannot redirect hook execution toward HOME.
- Keep the runtime truth split explicit: `live_runtime_execution_verified=true` and Gemini runtime-specific `live_capture_verified=true`, while `fake_model_responses_used=true`, `credential_material_present=false`, `live_provider_session_verified=false`, and `provider_model_execution_verified=false`.
- Preserve non-enforcement semantics: `runtime_enforced=false`, `result_flow_control_authorized=false`, `automatic_remediation=false`; the Gemini AfterTool hook remains synchronous from a latency perspective.
- Durable verification evidence records pre-finalization probe Run #10: Gemini CLI 0.60.0, 3 captured events, zero event loss/leakage, disabled sink absent, enabled invocation max 2268.651 ms, disabled invocation 2001.305 ms. Final exact-head Run #11 reverified the finalized evidence candidate successfully.
- Feature PR #101 exact final head `1f6cd76926c89b5a61365c7851bcdbb02bf9a8e7` passed dedicated real-runtime Run #11 and core-change validate Run #1087 with changed-files hash `ec5a10d0786a659e3045c1dac0a4d203f6a2b97d94546a3d16c31774b4f553d1`, Matrix hash `3bd83dc8a6025d0d04d2e691299ce426e3d1394af6b372b53775e0ac986cbd58`, candidate fingerprint `96a99a7279354d6655282be49a8c8c586ae70418055476ef6e7a05f951b1a7ef`, no blockers and preserved Human authority.
- PR #101 was squash-merged to main as `c04b1d17ebe264af5fb33228270ef9a3bce4a72a`; protected-main validate Run #1088 succeeded with Scenarios 143/143 automated.
- Roles remain 12 and Skills remain 25.
- Constitution impact: NO. Protected Human Authority, deterministic Resource Authorization, merge/release/publication authority and safety boundaries remain unchanged.
- The next optional gate is separately authorized live-provider-session verification; v0.34.0 does not infer or require that approval.
- Release model remains unchanged: no GitHub Release object or tag is introduced; release truth remains `VERSION + CHANGELOG + protected-main validation`.

## 0.33.0

### Gemini CLI AfterTool Capture Implementation Trial

- Add the first runtime-specific bounded observable-event capture implementation Trial for Gemini CLI using its native `AfterTool` hook.
- Scope the hook to `read_file|write_file|replace`, keep capture disabled by default, require explicit opt-in plus an explicit sink under the system temporary directory, and persist canonical metadata only.
- Reuse the existing Resource Authorization truth and anomaly evaluator; no second authorization system, semantic intent gate, or automatic remediation path is introduced.
- Record 6/6 supported fixture captures with zero unexpected event loss, four expected degraded/skipped cases, zero raw/private/secret leakage, and bounded enabled-subprocess overhead asserted in CI.
- Preserve runtime truth: current official Gemini CLI documentation confirms `AfterTool` inputs and regex matchers, but Gemini CLI waits synchronously for hooks. The Trial therefore distinguishes non-enforcing flow control from latency: `decision=allow`, `result_flow_control_authorized=false`, `synchronous_hook=true`, `latency_path=synchronous`. `critical_path=false` refers only to authorization/result-enforcement semantics.
- Add a disabled shell fast path that returns allow without starting Python; enabled-hook overhead remains bounded and measured.
- Keep `live_runtime_execution_verified=false` and `live_capture_verified=false` because CI does not execute a real Gemini CLI binary.
- Keep durable production persistence, shell/MCP/network capture, semantic intent governance, automatic remediation, new Role/Skill/provider dependency, and protected-operation/publication authority out of scope.
- Add Scenario 142 and raise Scenario Conformance to 142/142 automated. Roles remain 12 and Skills remain 25.
- Feature PR #98 exact final head `c95f4e315079a6b9185357f498be97e6cac3ab0c` passed core-change Janitor and required `repository` in validate Run #1071 with changed-files hash `28fc987415361e978b129e5608552ccad79ff0912cf07b5c6da488f684c1e24e`, Matrix hash `fc5f32dec7315cc525858e722edf4f0b17290c51210f32c72f76ac11011d3ae4`, candidate fingerprint `59815c9535e25fe435427a220b5f659239e21cad6722e3a98c978438d9ce0e72`, no blockers and preserved Human authority.
- PR #98 was squash-merged to main as `30b8b363983b116bde5692cc66d69c93b7c42915`; protected-main validate Run #1072 completed successfully.
- Constitution impact: NO. Protected Human Authority, deterministic Resource Authorization, merge/release/publication authority and safety boundaries remain unchanged.
- Release model remains unchanged: no GitHub Release object or tag is introduced; release truth remains `VERSION + CHANGELOG + protected-main validation`.

## 0.32.0

### Trial-backed Agent Anomaly Adoption Review

- Record a separate current-baseline Human ADOPT Decision for the Issue #79 Agent anomaly candidate after the v0.31.0 observable-event replay Trial PASS.
- Extend the existing Evolution adoption abstraction with `bind-committed` so a released/committed PASS Trial can be bound to a newer current repository baseline without pretending the original Radar revision remains current.
- Bind the prior TRIAL Decision `sha256:3b3368af2d560a97e998500f680c48a14c1ed47fb496e54c0eac75cffc70ffb8`, PASS Trial `sha256:9270bab940c38558575490f4948589cf1ff3b6dc4477daf7eb0ff7caca4e187c`, Human ADOPT Decision `sha256:c742a082dd00bd9e451810b5ce4640413e420b06acb97311db42112150b13f3e`, and adoption binding `sha256:1263e376a83926de458605f758b718fa6c7e0e3771d2ae19e6b53434f826ef89`.
- Add the durable System Improvement Review with conclusion `SUITABLE_WITH_BOUNDS`. The adopted direction is an opt-in, metadata-only, adapter-level `POST_EXECUTION` observable-event capture design that reuses Harness adapters, the canonical observable-event schema, Resource Authorization truth, and the existing anomaly evaluator.
- Add `orchestration/AGENT_OBSERVABLE_EVENT_CAPTURE_DESIGN.md` as future-state design evidence. No runtime adapter is marked live-capture verified by this release.
- Keep production/live runtime hooks, `live_capture_verified=true`, runtime enforcement, durable event persistence/retention, semantic intent governance, automatic remediation, new Role/Skill/provider dependency, and any second authorization system explicitly deferred.
- Keep current-state architecture diagrams unchanged with an explicit N/A rationale: v0.32.0 adopts a design direction but does not alter current runtime topology.
- Add Scenario 141 and raise Scenario Conformance to 141/141 automated. Roles remain 12 and Skills remain 25.
- Feature PR #96 exact final head `e2571b4923d298da91859849acdc2b4375e69632` passed core-change Janitor and required `repository` in validate Run #1063 with changed-files hash `94a8d22ec4a2bb6b2545327c259ddb4d1f9e75d29a83a7ab28f073d00afad04d`, Matrix hash `2204393b2cf441cba1a028bf0b7549c358b93abc83d896216cff47a5dab58f8c`, candidate fingerprint `aa48d812abe06254291ef7948206c21be84b6177225c4a6504010946ac01f35b`, no blockers and preserved Human authority.
- PR #96 was squash-merged to main as `1c71cdf08b4199a2b45b7ae9c99d36c7073a610b`; protected-main validate Run #1064 succeeded.
- Constitution impact: NO. Protected Human Authority, deterministic Resource Authorization, merge/release/publication authority and safety boundaries remain unchanged.
- Release model remains unchanged: no GitHub Release object or tag is introduced; release truth remains `VERSION + CHANGELOG + protected-main validation`.

## 0.31.0

### Observable-Event Integration Controlled Trial

- Add a current-baseline Human TRIAL Decision for the Issue #79 out-of-band Agent anomaly candidate. The Decision binds signal `sha256:7da9fc0c0ad89a0c7d0315aa2a5f4aa7ceb9842149a969a84708ce382c3082b3` to v0.30.0 main `e5e47b28a524352f7f549b49a40a294ddb50a364` and explicitly overrides ASSESS only for a bounded replay-only Trial.
- Add a provider-neutral canonical observable-event contract and three representative adapter-export dialects. Only whitelisted event metadata is normalized; unknown adapters, unmapped raw fields, private reasoning and secret-like values fail closed.
- Reuse the existing Resource Authorization-backed Scenario 139 anomaly evaluator rather than creating a second permission system.
- Record a 12-case synthetic/sanitized replay Trial with TP=6, FP=0, TN=6, FN=0, precision=1.0, recall=1.0, FPR=0 and FNR=0. These are fixture regression metrics only and are not production anomaly-detection accuracy.
- Do not persist raw event payloads into the committed Trial result. The result records `live_capture_verified=false`, `runtime_enforced=false`, `critical_path=false` and `automatic_remediation=false`.
- Trial PASS stops at `HUMAN_REVIEW_TRIAL_RESULT` and keeps `human_adoption_decision_required=true`; no live runtime capture, runtime hook, automatic remediation or production adoption is authorized by this release.
- Semantic intent governance remains ASSESS-only and is not included in this Trial.
- Add Scenario 140 and raise Scenario Conformance to 140/140 automated. Roles remain 12 and Skills remain 25.
- Feature PR #94 exact final head `b5e3d6f80c4341e0fd9843557293b7e9d8e40f31` passed core-change Janitor and required `repository` in validate Run #1057 with changed-files hash `76d70807d8af89f1618981142ca8cc9e15ac2d5d59fd3eb352979538e64c0ca5`, Matrix hash `53fcb7eb474cddf59880a00b231304ecf2d834e48ac4e5387d095e21a4165859`, candidate fingerprint `02c9a0f7ddc4fcd6b6a5dffcdcd6023cc2b240f0ddc6f3fbf677eff450369974`, no blockers and preserved Human authority.
- PR #94 was squash-merged to main as `692123765f90182c1679c666f9a9b8647c325235`.
- Constitution impact: NO. Protected Human Authority remains intact; all merge, release, publication, protected-operation and automatic-remediation authority remains outside the Trial.
- Release model remains unchanged: no GitHub Release object or tag is introduced; release truth remains `VERSION + CHANGELOG + protected-main validation`.

## 0.30.0

### Agent Anomaly Evidence Evaluation

- Add a bounded, deterministic offline evaluation lane for the Issue #79 out-of-band Agent anomaly candidate without reintroducing the removed Agent Runtime Assurance production scope.
- Reuse the existing default-DENY Resource Authorization Profile as the sole authorization truth; no second permission system, runtime hook, semantic intent gate, provider dependency, Role or Skill is introduced.
- Add a fixed 11-case synthetic/sanitized observable-event corpus covering normal success, expected denials, ordinary failure, unauthorized success, missing Change Boundary, forbidden network use, subject mismatch, protected-operation observation and unsupported-operation observation.
- Report TP/FP/TN/FN, precision, recall, false-positive rate and false-negative rate. The committed fixture yields TP=6, FP=0, TN=5, FN=0, precision=1.0, recall=1.0, FPR=0 and FNR=0; these are regression metrics for the fixed corpus only and are not a production-accuracy claim.
- Fail closed on private-reasoning fields and secret-like values; intentionally incorrect expected labels make the benchmark FAIL.
- Keep enforcement truth explicit: output is `POST_EXECUTION_EVIDENCE`, `runtime_enforced=false`, `critical_path=false`, `automatic_remediation=false`, and all Human/protected/publication/merge/release authority flags remain false.
- PASS returns only `HUMAN_REVIEW_TRIAL_EVIDENCE`; the Evolution Radar anomaly candidate remains ASSESS pending a separate Human decision for any real observable-event integration Trial. Semantic intent governance remains separately ASSESS and is not implemented.
- Add Scenario 139 and raise Scenario Conformance to 139/139 automated; Roles remain 12 and Skills remain 25.
- Feature PR #92 exact final head `51fa69ec54c56be458bdaf0bc8146646496afbd7` passed core-change Janitor and required `repository` in validate Run #1052 with changed-files hash `f01c6e01f22b0189d52bda26d43c0242f8f3a3512b5e0b97a8f97916ada52f3f`, Matrix hash `dd2b6b35816c59fe2723166a50b5fb41b93a9e9c058e85f46c2a351121ec3204`, candidate fingerprint `ad138d1d6d72c20e8991f1aed7ab5f2cc813feb9bedbce3eed98af1c461684f9`, no blockers and preserved Human authority.
- PR #92 was squash-merged to main as `a548dc63fb81411ab6b33aaedab69ca78ee3ef12`; protected-main validate Run #1053 completed Janitor and required `repository` successfully with 139 scenarios.
- Constitution impact: NO. No automatic remediation, protected-operation, Human approval, merge, release or publication authority is introduced.
- Release model remains unchanged: no GitHub Release object or tag is introduced; release truth remains `VERSION + CHANGELOG + protected-main validation`.

## 0.29.0

### Resource-Scoped Agent Authorization

- Add Resource-Scoped Agent Authorization as a deterministic extension of the existing Execution Profile / Governance path. Resource profiles are fail-closed with `default_effect: DENY`, require explicit resource + ordinary-operation grants, can require Change Boundary evidence for mutation, reject secret values, and never grant merge, release, publication, administration, destructive deletion or Human approval authority.
- Keep enforcement truth explicit: Resource Authorization produces deterministic `PRE_EXECUTION_EVIDENCE`; without a separately verified runtime pre-tool guard, AIPS does not claim universal runtime/tool-call enforcement.
- Add Scenario 138 and raise Scenario Conformance to 138/138 automated. Roles remain 12 and Skills remain 25; no new Role, Skill or provider dependency is introduced.
- Feature PR #87 exact final head `f1491f7316159edc09c7d83f11425672c633862b` passed Janitor and required `repository` in validate Run #1039 and was squash-merged to main as `4595b21d33b8ca6608e371c620b3afcfc5c285d0`.
- Scope reconciliation removes the later PR #88 Agent Runtime Assurance additions from the effective v0.29.0 capability set because out-of-band anomaly detection and semantic intent governance were outside the approved v0.29.0 implementation boundary. Those Evolution Radar signals remain ASSESS-only pending a separate Human-authorized decision.
- Constitution impact: NO. Protected Human Authority, existing approval binding, Change Boundary, Execution Isolation, Git Publish, merge/release governance and destructive-operation safety remain intact.
- Architecture impact: capability expansion stays inside the existing Execution Profile / Resource Authorization / Governance / Conformance path; no second runtime authority subsystem is introduced.
- Release model remains unchanged: no GitHub Release object or tag is introduced; release truth remains `VERSION + CHANGELOG + protected-main validation`.

## 0.28.0

### Agent Eval Repeatability Evidence

- Extend existing provider-neutral Agent Eval with deterministic consistency analysis across repeated executions of the exact same Case fingerprint, without introducing a new Role, Skill, provider dependency or runtime authority.
- Add `agent_eval.py consistency` and `aips conformance agent-eval consistency` to report repetition count, PASS rate, outcome consistency, observable-response diversity and exact response repeatability while keeping response bodies/private reasoning out of aggregate evidence.
- Keep freshness fail-closed: stale, missing or invalid Agent Eval evidence remains invalid even when a caller chooses a relaxed pass-rate threshold.
- Add Scenario 137 and raise Scenario Conformance to 137/137 automated while preserving the existing recorded Agent Eval case/result pairs.
- Feature PR #85 exact head `1822bb9769979dce2cf1ad24dee4e6823448f75d` passed Janitor and required `repository` in validate Run #1032 and was squash-merged to main as `32889482b67f96518f3fe483242a1a477d8520f8`.
- Protected-main validate Run #1033 independently completed `janitor=SUCCESS` and `repository=SUCCESS` on exact merged main.
- Evolution Radar Issue #79 was semantically reviewed after implementation: 2 signals COVERED, 3 ASSESS, 20 HOLD, 0 TRIAL and 0 ADOPT. The repeated-run Agent reliability signal is now COVERED on current main; resource-scoped agent authorization, out-of-band anomaly evidence and semantic intent governance remain ASSESS-only and require a fresh current-baseline review before any Trial or implementation.
- Preserve the Radar authority boundary: the Issue #79 evidence baseline predates current main and is explicitly treated as STALE for new positive progression; no Human Decision Record was fabricated from advisory analysis.
- Constitution impact: NO. No merge, release, Human approval, provider-routing or tool-call authority is added.
- Architecture Diagram Impact: NO material topology change. This release strengthens conformance evidence inside the existing Agent Eval/Scenario Conformance path.
- Release model remains unchanged: no GitHub Release object or tag is introduced; release truth remains `VERSION + CHANGELOG + protected-main validation`.

## 0.27.2

### Remote Branch Hygiene Reporting

- Make deterministic Branch Hygiene usable in GitHub Actions against the actual repository branch set by adding explicit remote-ref classification through `scripts/branch_hygiene.py --remote origin`.
- Preserve the existing conservative integration rules from v0.27.1: direct ancestry, patch equivalence and squash-aware synthetic merge-tree equality remain the only paths to `integrated_into_target=true`.
- Add `.github/workflows/branch-hygiene.yml` with weekly schedule, manual dispatch and targeted main-push verification when Branch Hygiene implementation/config changes. The workflow uses `contents: read`, fetches/prunes `refs/remotes/origin/*`, publishes a Job Summary and verifies `branch_deletion_authorized=false`.
- Add local + remote lifecycle evidence and repository contract checks so CI fails if remote enumeration, read-only permissions or report-only authority regress.
- Synchronize Human Maintenance and Technology Guide documentation with the new remote-report execution path.
- PR #82 exact final head `c231b769bfe58ff9bef698dbdda08796d9f4b13a` passed Janitor and required `repository` in validate Run #1028 and was squash-merged to main as `ffa97df1ad85588496e5d1dd5758054b1d29e794`.
- Protected-main validate Run #1029 independently completed `janitor=SUCCESS` and `repository=SUCCESS` on exact merged main.
- Branch Hygiene production Run #1 completed SUCCESS on exact main: full-depth checkout, remote-ref refresh, deterministic report generation, Job Summary publication and report-only authority verification all passed.
- The prior v0.27.1 closeout already removed all then-known deterministic deletion candidates and preserved operational `feature/retrieval-embedding-trial`; this patch adds repeatable evidence generation rather than automatic deletion.
- Constitution impact: NO. No branch deletion, ref rewrite, merge or release authority is added.
- Release model remains unchanged: no GitHub Release object or tag is introduced; release truth remains `VERSION + CHANGELOG + protected-main validation`.

## 0.27.1

### Branch Hygiene Squash Detection & v0.27 Closeout

- Fix deterministic Branch Hygiene false negatives for multi-commit branches that were integrated through squash merge. Integration detection now remains conservative in order: direct ancestry, per-commit patch equivalence, then a clean synthetic `git merge-tree --write-tree` whose resulting tree must exactly equal the target tree.
- Add lifecycle regression evidence for a two-commit feature branch squash-merged into `main`, while preserving `deletion.mode=report_only`, unclassified-branch preservation and the persistent operational `feature/retrieval-embedding-trial` branch.
- PR #80 exact head `81ac3b5e5caba44efc6478cfab8f27972cb2a05e` passed Janitor and required `repository` in validate Run #1024 and was squash-merged to main as `e654384a2970dc450dbc0a5d97b1c2814f063a5c`.
- Protected-main validate Run #1025 independently completed `janitor=SUCCESS` and `repository=SUCCESS` on exact merged main.
- Validate the v0.27 provider-neutral Evolution Radar production path on exact `main@e256f8817839bef0c282b352754dca91d32fdf69`: workflow-dispatch Run #2 completed SUCCESS, produced the deterministic semantic handoff and created current Human review Issue #79. Pre-v0.27 Issue #50 and stale duplicate Issue #78 were closed as superseded/duplicate.
- Execute Human-authorized branch maintenance only from deterministic report output. The first v0.27 closeout pass reported 37 integrated EPHEMERAL deletion candidates; after the squash-aware fix, a second pass found two additional candidates (`feature/branch-hygiene-squash-detection` and `release/v0.18.4`) and deleted them. Post-cleanup verification reported zero remaining deterministic deletion candidates.
- One-time maintenance runner branches deleted themselves after completion and did not modify `main`.
- No automatic branch-deletion authority is introduced; the classifier remains report-only and deletion still requires an explicit maintenance authorization outside the classifier.
- Constitution impact: NO. Protected Human Authority, Git Publish/merge/release governance and existing publication boundaries remain unchanged.
- Release model remains unchanged: no GitHub Release object or tag is introduced; release truth remains `VERSION + CHANGELOG + protected-main validation`.

## 0.27.0

### Reliability & Governance Hardening

- Make Evolution Radar semantic analysis provider-neutral: scheduled runs now always produce a credential-free semantic handoff bound to the exact analysis package/evidence digest, while the existing OpenAI Codex Action adapter becomes optional. Missing `OPENAI_API_KEY` no longer prevents deterministic research packaging; recommendations remain `ANALYSIS_PENDING` until a validated semantic result is explicitly bound and applied.
- Harden the Deterministic Scheduler fail-closed boundary contract: potentially writable tasks must declare a non-empty Change Boundary, explicit `read_only: true` tasks may omit it only when no write set exists, and contradictory read-only/write declarations are blocked.
- Harden the Integration/Janitor Gate against stale pull-request bases by freshly resolving the target branch tip and blocking candidates whose declared base no longer matches current target state before expensive checks execute.
- Add conditional Core Change Test Matrix enforcement. Explicit `aips:large-change` / `aips:core-change` candidates require exact candidate-bound Matrix evidence, while ordinary standard changes remain Matrix-optional unless they touch a narrow governance-core Integration Gate safety net.
- Keep Matrix enforcement proportional: broad `scripts/**` / `config/**` rules are intentionally avoided so routine changes are not misclassified as Core solely by file type.
- Add deterministic branch lifecycle hygiene with `PERSISTENT`, `EPHEMERAL` and `UNCLASSIFIED` classification. The policy is report-only: only integrated ephemeral branches become deletion candidates, operational branches such as `feature/retrieval-embedding-trial` remain explicitly persistent, and no automatic branch-deletion authority is introduced.
- Reduce duplicate CI work by allowing repository validation to skip focused Scheduler/Integration Gate lifecycle evidence only when the active Validation Profile already executed those checks. Standalone `tests/validate_repository.py` remains complete.
- Close a validation coverage hole found during PR #76 review by adding executable `branch_hygiene_contracts.py` and correcting the repository-validator import so Branch Hygiene config, syntax and lifecycle evidence are actually enforced.
- Feature PR #75 exact head `760fa012170178df107d7bf9e9336116c39d85b4` was squash-merged to main as `2097c2dc1c28ee221b795daa47fba104dbf75fa5`; protected-main validate Run #1018 completed SUCCESS.
- Governance hardening PR #76 exact final head `0a5a1da9094b20536e56c792cf691b5c7f4385d9` passed Janitor and required `repository` in validate Run #1020, then was squash-merged to main as `37578a1707ae7439d2d002e59b6cbb898e4b7fc3`.
- Protected-main validate Run #1021 independently completed `janitor=SUCCESS` and `repository=SUCCESS` on exact merged main. The final governance candidate bound changed-files hash `c356c77646612f9c197424f510bbce7bd54210f47fb7255ea2a1cddeb033880c`, Matrix hash `d393a5df8cbc394ec6ffea2cbce5b3d174ad66025b2ffefc3c6e33cfe8dd195f`, no blockers and preserved Human authority.
- Scenario inventory remains 136 automated scenarios; Roles remain 12 and Skills remain 25. No new Role, Skill or autonomous approval layer is introduced.
- Constitution impact: NO. Protected Human Authority, Git Publish Approval semantics, merge authority and release authority remain unchanged.
- Architecture Diagram Impact: YES. Human/Agent architecture and maintenance documentation now describe provider-neutral Radar handoff, writable-task fail-closed scheduling, PR base freshness, conditional Matrix enforcement, branch hygiene and validation de-duplication.
- Release model remains unchanged: no GitHub Release object or tag is introduced; release truth remains `VERSION + CHANGELOG + protected-main validation`.

## 0.26.0

### Deterministic Scheduler + Exact-Candidate Integration Gate

- Add a code-driven Deterministic Scheduler that consumes a structured Task Graph after semantic planning and deterministically enforces dependency readiness, stable ordering, `max_parallel`, active Change Boundary locks and blocked downstream work without creating a new Role, Skill or autonomous authority.
- Add versioned Task Graph schema/template contracts plus `aips scheduler` CLI support, while preserving existing Execution Isolation, single-writer Change Boundary rules and durable run/workspace state as the canonical execution model.
- Add the canonical Integration Gate (informal/CLI alias: Janitor) to validate the exact candidate bound to base/head SHAs, changed-file hash, Validation Profile hash and optional Core Change Test Matrix hash.
- Add project-native Validation Profiles and deterministic argv-based checks; the AIPS repository profile requires Ruff critical lint, mypy for the new runtime helpers, Scheduler lifecycle evidence, Integration Gate lifecycle evidence and full repository validation.
- Preserve the protected-main required check name `repository`: the new `janitor` job runs first and the required `repository` aggregate can succeed only when Janitor succeeds, so existing branch protection remains compatible without migration.
- Add Scenario 135 for deterministic multi-agent scheduling and Scenario 136 for exact-candidate Integration Gate behavior. Scenario Conformance is now 136 total / 0 manual / 22 deterministic / 60 lifecycle / 54 agent_eval / 136 automated / 0 uncovered (100% automated).
- Feature PR #73 exact head `4b8fb81fddc5127ff6426f1a98843fa6131d6b2a` passed `janitor` and required `repository` in validate Run #1013 and was squash-merged to main as `6c251e072c84095097ce6181bad60b4f492d59a1`.
- Protected-main validate Run #1014 independently re-ran the new pipeline on exact merged main and completed `janitor=SUCCESS`, `repository=SUCCESS`.
- Janitor Run #1013 reported candidate fingerprint `ae068e7ca1df9005f08b5bc62b0a0040c1225a04f980c5f3bbd62650cb04c032`, all required checks PASS, no blockers, `merge_authorized=false`, `release_authorized=false` and `human_authority_preserved=true`.
- Keep the Integration Gate as deterministic evidence rather than a new approval authority: PASS never authorizes merge, release, architecture decisions or Human-gated actions.
- Constitution impact: NO. Protected Human Authority, Git Publish Approval and existing governance boundaries remain unchanged.
- Architecture Diagram Impact: YES. System/Human architecture and execution documentation now include Structured Task Graph -> Deterministic Scheduler -> isolated parallel work -> Integration Candidate -> Integration/Janitor Gate -> required `repository` aggregate.
- Release model remains unchanged: no GitHub Release object or tag is introduced; release truth remains `VERSION + CHANGELOG + protected-main validation`.

## 0.25.0

### Provider-Neutral Local-First Embedding Trial — HOLD

- Add Scenario 134 and make the dedicated Retrieval embedding Trial provider-neutral with a credential-free local provider as the default, while preserving the existing OpenAI-compatible remote adapter as an explicit optional comparison path.
- Add pinned `sentence-transformers` Trial dependency plus pinned `BAAI/bge-small-en-v1.5` model revision `0b329b72cad8d6ff9a504a30a6c239b87802dc84`, 384 dimensions and runner-local inference.
- Keep normal Pull Request/main validation and normal Retrieval Intelligence / Turn Context free from embedding execution. The semantic Trial dependency is installed only by the dedicated `retrieval-semantic-trial` workflow.
- Preserve synthetic-only Trial scope, repository/product source transfer=false, ephemeral in-memory vectors, no Vector DB, unchanged 9-case corpus/thresholds and no automatic provider/default enablement.
- Keep remote mode optional through `AIPS_RETRIEVAL_EMBEDDING_PROVIDER=remote`; only that explicit path uses the protected `OPENAI_API_KEY` reference and retains truthful `TRIAL_PENDING` when the credential is unavailable.
- Feature PR #71 exact final head `5d758cee76e30ecb5871d05e990a2b7da48fdb41` passed required `repository` Run #1009 and was squash-merged to main as `6a9291eefcb1922e244e55d7edbb2a17a146d22c`.
- Protected-main `repository` Run #1010 passed on exact merged main before Trial execution.
- The dedicated `feature/retrieval-embedding-trial` branch was fast-forwarded to exact main and local Trial Run #8 completed with workflow `SUCCESS`; all dependency, Trial, bounded-evidence and operator-summary steps completed successfully without an OpenAI API key.
- Real local embedding quality evidence is **FAIL / HOLD**, not a credential or runtime block: all 9 embedding batches completed with local `sentence-transformers` inference.
- The semantic target `synonym-access-rotation` improved, but the candidate introduced required regression `go-receipt-reconciliation` and recall regression `low-lexical-overlap-registration`; therefore the embedding lane remains disabled and thresholds are not weakened to manufacture PASS.
- Scenario Conformance is 134 total / 0 manual / 22 deterministic / 58 lifecycle / 54 agent_eval / 134 automated / 0 uncovered (100% automated).
- No Human Adoption Decision is requested because Trial status is FAIL. Production Retrieval / Turn Context remains on the existing adopted deterministic + Structural Retrieval path.
- Constitution impact: NO. No new Role, Skill, capability category, Human Approval Gate or autonomous publication authority is introduced.
- Architecture Diagram Impact: YES. Retrieval architecture now documents local-first / remote-optional embedding Trial selection while production Retrieval topology remains unchanged.

## 0.24.1

### Remote Embedding Trial Operator Handoff

- Add `scripts/retrieval_embedding_trial_summary.py` to render the machine-readable embedding Trial report into a safe Human-readable GitHub Job Summary.
- Make workflow-level `SUCCESS` explicitly distinct from Trial `PASS`, `FAIL`, `TRIAL_PENDING` and `TRIAL_BLOCKED`.
- Surface provider/model identifiers, credential availability as a boolean, privacy scope, request/token counts when present, authority flags and the exact next operator action without exposing credential values.
- Define state-specific operator guidance: PENDING asks for repository Actions secret `OPENAI_API_KEY` and a workflow re-run; BLOCKED keeps HOLD until provider/network/config issues are corrected; FAIL preserves negative evidence; PASS stops at a separate Human Adoption Decision.
- Strengthen Scenario 133 and `retrieval_embedding_trial_contracts.py` so Job Summary publication and operator guidance are deterministic release contracts.
- Extend Documentation Sync coverage to the summary helper and synchronize Human/Agent Project Intelligence, Conformance, Documentation Sync and Technology Guide surfaces.
- Initial PR #69 validation Run #1002 correctly failed because the documentation map and exact Human Adoption Decision guidance were incomplete; the change was rebuilt as one atomic commit rather than stacking intermediate remote commits.
- Exact corrected PR #69 head `bfd851d2c916942ffab1d132885e796dc74cbc29` passed required `repository` Run #1003.
- Feature implementation merged through #69; exact merged main `ffdf61aaedc1c78c8322c5e5ded79676d4260a1e` passed protected-main `repository` Run #1004.
- The dedicated `feature/retrieval-embedding-trial` branch was then aligned to that exact main and Trial Run #4 completed successfully at workflow level; `Publish Trial operator summary` also completed successfully.
- Trial Run #4 truthfully remains `TRIAL_PENDING / PENDING_CREDENTIAL` with `credential_available=false`; the provider was not called. This is the sole remaining external prerequisite for obtaining provider-backed quality evidence.
- Production Retrieval Intelligence / Turn Context behavior is unchanged; repository/product source transfer remains false and no embedding provider is enabled by default.
- Scenario Conformance remains 133 total / 0 manual / 21 deterministic / 58 lifecycle / 54 agent_eval / 133 automated / 0 uncovered (100% automated).
- Constitution impact: NO. Human adoption/publication authority is unchanged.
- Architecture Diagram Impact: N/A. This patch improves Trial operations and evidence handoff inside the existing v0.24.0 remote Trial path.

## 0.24.0

### Remote Embedding Retrieval Trial Readiness

- Add Scenario 133 and a provider-backed Retrieval Trial readiness path for materially different semantic retrieval research after the deterministic Semantic Alias Expansion candidate remained HOLD.
- Introduce a bounded OpenAI-compatible embeddings adapter using the approved `v1/embeddings` endpoint, default model `text-embedding-3-small`, optional repository-variable model override, 512 dimensions and protected `OPENAI_API_KEY` secret injection.
- Keep the Trial synthetic-only: only the committed 9-case Retrieval Quality fixture may be transmitted; AIPS repository/product source transfer remains explicitly forbidden.
- Keep normal Retrieval Intelligence and Turn Context unchanged. No embedding lane, provider or production source transfer is enabled by default.
- Add explicit hard limits for provider requests, candidate chunks and remote input characters. Candidate vectors remain ephemeral/in-memory; no Vector DB is introduced.
- Define truthful fallback states: missing credentials produce `TRIAL_PENDING`; provider/network/runtime failures produce `TRIAL_BLOCKED`; neither state may be rewritten as quality PASS/FAIL evidence.
- Add a dedicated `retrieval-semantic-trial` workflow scoped to the Trial feature branch plus manual dispatch; normal Pull Request and main validation never call the remote embedding provider.
- Preserve the current v0.23.2 default Retrieval + adopted Structural Retrieval as the baseline and reuse the same 9-case quality corpus and regression thresholds for future provider-backed comparisons.
- First dedicated Trial execution on the feature head completed successfully at the workflow level and truthfully reported `TRIAL_PENDING / PENDING_CREDENTIAL` with `credential_available=false`; the provider was not called.
- PR #67 exact corrected head `41ea8fcc7c19d08b82ae76f7d62048692e7ce191` passed required `repository` Run #998 after secret-scanner-safe credential handling.
- Feature implementation merged through #67; exact merged main `bdd4d6c6ec49521be678626ca1d05a82200aac60` passed protected-main `repository` Run #999 before release metadata finalization.
- Raise Scenario Conformance to 133 total / 0 manual / 21 deterministic / 58 lifecycle / 54 agent_eval / 133 automated / 0 uncovered (100% automated).
- Constitution impact: NO. No new Role, Skill, capability category, Human Approval Gate or autonomous publication authority is introduced.
- Architecture Diagram Impact: YES. Retrieval architecture documentation now includes the synthetic-only remote embedding Trial readiness path and PENDING/BLOCKED/Human-review branches; production Retrieval topology is unchanged.

## 0.23.2

### Semantic Alias Expansion Trial — HOLD

- Complete a dependency-free Semantic Alias Expansion candidate Trial for the remaining low-lexical-overlap / synonymy retrieval research without enabling an embedding model, Vector DB or remote semantic provider.
- Keep current v0.23.1 Retrieval Intelligence, including adopted Structural Retrieval, as the baseline and enable only a transparent source-controlled software-engineering alias expansion lane in the candidate replay.
- Preserve truthful provider state throughout the Trial: `semantic.status=NOT_CONFIGURED`, `embedding_provider_used=false`, `default_enabled=false` and `external_dependency=false`.
- Record the actual controlled-Trial outcome as **FAIL / HOLD** rather than weakening corpus thresholds or tuning weights until CI turns green.
- PR validation Run #991 exposed required regressions in auth-token-expiry, Go receipt reconciliation and TypeScript session refresh; registration baseline source recall regressed under alias expansion; synonym-access-rotation remained unresolved.
- Run #992 added cross-group coherence and active-target classification but reproduced the same safety/quality conclusion: required regressions remained, registration recall still regressed and the active synonym-access target did not improve.
- Preserve the candidate implementation and matched-group / expanded-term telemetry only as reproducible research evidence; normal Turn Context and normal retrieval do not enable the alias lane.
- Add explicit Trial recommendation `HOLD` and make Scenario 132 intentionally expect the candidate process to exit non-zero while proving negative evidence, instead of treating all valid Trials as mandatory PASS outcomes.
- Scenario 132 verifies the known HOLD cannot auto-adopt itself, enable an embedding provider or silently rewrite negative evidence as success.
- A materially different semantic retrieval candidate (for example a real local or remote embedding provider) requires a separate Human-reviewed Trial covering source-code transfer/privacy, provider configuration, cost/cache and fallback boundaries before implementation/adoption.
- Raise Scenario Conformance to 132 total / 0 manual / 20 deterministic / 58 lifecycle / 54 agent_eval / 132 automated / 0 uncovered (100% automated).
- Feature evidence merged through #65; exact merged main `431ccc5f999e036aa74904d87c64e336d1da4e5f` passed protected-main `repository` Run #994 before release metadata finalization.
- Constitution impact: NO. No new Role, Skill, capability category, Human Approval Gate or autonomous publication authority is introduced.
- Architecture Diagram Impact: YES. Retrieval evaluation documentation now includes the semantic-alias candidate Trial and its explicit FAIL → KEEP / HOLD outcome; production Retrieval topology remains unchanged.

## 0.23.1

### CI Validation Hygiene and Atomic Git Publication

- Scope the repository `validate` workflow to automatic Pull Request updates and `main` pushes, while adding `workflow_dispatch` for explicit manual validation. Standalone feature-branch pushes no longer run the full repository validation automatically.
- Add workflow concurrency keyed by Pull Request / ref with `cancel-in-progress: true`, so newer validation supersedes an older still-running validation for the same logical publication target.
- Preserve the protected-main required `repository` check: PR validation and merged-main validation remain mandatory and unchanged in authority.
- Make documentation diff-base behavior explicit across PR, push and manual-dispatch events; main pushes compare against `github.event.before`, feature-branch manual dispatch can compare against the default branch and main manual revalidation does not invent a missing push base.
- Adopt atomic remote branch updates as the default Git publication strategy for multi-file logical changes: assemble the coherent approved tree first, then create/update the remote engineering ref once instead of publishing one intermediate remote commit per file.
- Extend the Git Publish Proposal and Scenario 018 so remote update strategy, expected ref-update count and any deliberate incremental-publication reason are explicit approval inputs.
- Strengthen repository static contracts so CI trigger scope, manual dispatch, concurrency cancellation and push diff-base policy cannot silently regress.
- Update Human Maintenance and Technology Guide documentation to explain the new CI lifecycle and why true PR/main failures remain notified while transient standalone feature-push failures are avoided.
- Observed evidence: creating `feature/ci-validation-hygiene` at exact commit `97e4c9b3724acfed63762dd4c5485bfd4c53962c` produced zero standalone feature push validation runs; PR #63 produced one required Run #987 (SUCCESS); merged main `c6fa89ae3fde6ff804f7ead76ea411b389dc324d` produced one protected-main Run #988 (SUCCESS).
- Scenario Conformance remains 131 total / 0 manual / 20 deterministic / 57 lifecycle / 54 agent_eval / 131 automated / 0 uncovered.
- Constitution impact: NO. Git Publish governance is clarified/hardened without changing Human publication authority.
- Architecture Diagram Impact: N/A. This patch changes CI trigger/publication hygiene inside the existing Git governance/release path; Runtime, Retrieval and Product Delivery topology are unchanged.

## 0.23.0

### Adopted Bounded Structural Retrieval

- Adopt the bounded built-in exact-identifier two-hop Structural Retrieval relation graph as part of normal local Retrieval Intelligence after explicit Human ADOPT decision and successful controlled Trial evidence.
- Enable structural expansion by default for normal `aips intelligence retrieve` and Turn Context retrieval while preserving `--no-structural` as an explicit diagnostic opt-out that disables only the structural lane.
- Keep traversal local, deterministic and provider-neutral: exact query symbols seed bounded bridge discovery through the existing lexical index / fallback, bridge identifiers resolve through the indexed symbol table and target definitions / companion tests receive bounded structural boosts.
- Preserve explicit hard limits and telemetry for bridge chunks, identifiers per bridge, target definitions, test chunks and truncation state so default structural traversal remains bounded and observable.
- Update Retrieval Quality Evaluation to measure the adopted default retrieval behavior while preserving Scenario 130 as an explicit structural OFF/ON Trial replay for regression and comparison evidence.
- Preserve all existing safety contracts: token budgets, result/revision provenance, secret-path filtering, incremental freshness and truthful semantic-provider status remain unchanged.
- Keep the capability dependency-free: no Tree-sitter, gopls/LSP, Sourcegraph, Embedding or Vector DB dependency is introduced by adoption.
- Add Scenario 131 lifecycle evidence proving default structural enablement, Turn Context use, metadata truthfulness and explicit opt-out behavior.
- Raise Scenario Conformance to 131 total / 0 manual / 20 deterministic / 57 lifecycle / 54 agent_eval / 131 automated / 0 uncovered (100% automated).
- Feature implementation merged through #61; exact merged main `5fb4890512bf4b6488845f221d9ac2a951f38aaf` passed protected-main `repository` Run #982 before release metadata finalization.
- Constitution impact: NO. No new Role, Skill, capability category, Human Approval Gate or autonomous publication authority is introduced.
- Architecture Diagram Impact: YES. Retrieval Intelligence architecture and Human/Agent Project Intelligence documentation now represent Structural Retrieval as the adopted default lane while retaining the explicit Trial replay path.

## 0.22.2

### Structural Retrieval Candidate Trial

- Add a bounded, dependency-free Structural Retrieval candidate lane for controlled evaluation of cross-file relationship retrieval without changing normal Turn Context behavior.
- Keep current local hybrid Retrieval Intelligence as the baseline; structural expansion is enabled only inside the candidate trial and remains disabled by default.
- Seed the candidate from exact query symbol definitions, discover bridge chunks that reference those symbols, follow exact identifiers in those bridge chunks to target symbol definitions and optionally boost companion tests.
- Bound traversal with explicit caps for bridge chunks, identifiers per bridge, target definitions and test chunks, and expose deterministic telemetry including truncation state, seed count, bridge count and target-definition count.
- Tighten the committed `cross-file-call-chain` diagnostic so the query names `CheckoutCoordinator` and the business intent but not the downstream `ReserveStock` implementation; a wiring file provides the actual two-hop relation.
- Add a full-corpus controlled comparison that runs baseline and candidate retrieval on the same 9-case suite, requires all 6 required cases to avoid regression and requires every diagnostic tagged `structural-retrieval` to improve Recall@K.
- The trial proves a real baseline structural gap remains reproducible while the bounded exact-identifier candidate recovers the complete expected source set at Recall@K = 1.0.
- Preserve all existing retrieval safety boundaries: token budget, provenance, secret-path filtering and truthful semantic-provider status remain unchanged.
- Add Scenario 130 lifecycle evidence and raise Scenario Conformance to 130 total / 0 manual / 20 deterministic / 56 lifecycle / 54 agent_eval / 130 automated / 0 uncovered (100% automated).
- Trial PASS is evidence only: `automatic_adoption=false`, `automatic_default_enablement=false`, no parser/LSP dependency is added and a separate Human Adoption Decision is still required before structural retrieval can become part of normal Turn Context retrieval.
- No Tree-sitter, gopls/LSP, Sourcegraph, Embedding or Vector DB dependency is introduced by this patch.
- Feature implementation merged through #59; exact merged main `3af4fa8a3ad78459ffc9e4154fd8e60912d1678d` passed protected-main `repository` Run #954 before release metadata finalization.
- Constitution impact: NO. No new Role, Skill, capability category, Human Approval Gate or autonomous publication authority is introduced.
- Architecture Diagram Impact: YES. Detailed Retrieval Quality architecture and Human Project Intelligence documentation now include the structural candidate trial path; high-level Runtime Harness/Product Delivery topology is unchanged.

## 0.22.1

### Retrieval Benchmark Corpus Maturity

- Expand Retrieval Quality Evaluation from 3 controlled cases to a committed 9-case corpus spanning Python, Go, TypeScript, SQL, monorepo/shared-module, low-lexical-overlap, synonymy and cross-file-call-chain retrieval dimensions.
- Introduce explicit `required` vs `diagnostic` case enforcement: required threshold failures remain release-blocking, while diagnostic stress failures retain FAIL/gap evidence without being rewritten as PASS or blocking the whole suite.
- Aggregate diagnostic evidence by gap ID, dimension and failed check so capability limitations can be tracked over time before selecting another retrieval technology.
- Tighten diagnostic stress cases to require 100% source recall/direct-source delta, preventing partial retrieval from being mistaken for semantic or structural completeness.
- Add deterministic companion-test ranking for exact symbol targets using common Python/Go/JavaScript/TypeScript naming conventions, so target implementation + matching test evidence remain stable as corpus noise grows.
- The first expanded-corpus run exposed a real required regression where `RefundService` ranked correctly but its companion test was displaced by generic refund matches; the local companion-test fix restored all 6 required regression cases without adding an external provider.
- The same expanded evidence exposed diagnostic gaps across low lexical overlap / synonymy and cross-file structural retrieval, which remain evidence for later Human architecture review rather than triggering automatic Embedding, Tree-sitter/LSP or Sourcegraph adoption.
- Preserve the existing provider-neutral/local-first architecture: no Embedding, Vector DB, Tree-sitter/LSP or Sourcegraph dependency is introduced by this patch.
- Strengthen existing Scenario 129 evidence without adding a new Scenario; Scenario Conformance remains 129 total / 0 manual / 20 deterministic / 55 lifecycle / 54 agent_eval / 129 automated / 0 uncovered.
- Feature implementation merged through #57; exact merged main `7e2e89a6c27ea3c1b97947196a551715ca493cb2` passed protected-main `repository` Run #897 before release metadata finalization.
- Constitution impact: NO. No new Role, Skill, capability category, Human Approval Gate or autonomous publication authority is introduced.
- Architecture Diagram Impact: N/A. This patch refines Retrieval Intelligence evaluation/ranking behavior inside the existing Project Intelligence topology.

## 0.22.0

### Retrieval Quality Evaluation

- Add a provider-neutral Retrieval Quality Evaluation harness under Project Intelligence so retrieval architecture changes are driven by measured repository evidence rather than technology novelty.
- Compare current local hybrid Retrieval Intelligence against an explicitly declared v0.20-style static topic-context baseline with repository-specific expected source paths and optional Git-history terms.
- Compute deterministic Precision@K, Recall@K, F1@K, MRR, Git-history recall, irrelevant-context rate, direct-source-recall delta and token usage; record wall-clock latency only as informational evidence rather than a shared-runner CI SLO.
- Add `aips intelligence evaluate --suite ...` with optional report output plus `RETRIEVAL_EVALUATION.yaml` as the reusable suite contract.
- Bind evaluation evidence to suite fingerprint, repository revision/dirty state, deterministic metrics/checks and authority boundary while deliberately excluding observed latency, machine-local paths and index timestamps from the result fingerprint.
- Keep evaluation control data outside indexed product source (or inside excluded AIPS workspace state) so expected-answer fixtures cannot contaminate FTS results.
- Use the new benchmark to identify and fix two concrete v0.21 local-ranking gaps without weakening evaluation thresholds: exact symbol definitions now outrank generic lexical overlap, and Git-history ranking prioritizes commit-message intent while suppressing weak path-only history when strong intent evidence exists.
- Tighten Git-history evidence size so broad initialization commits cannot dominate the bounded retrieval context merely because they touched a matching path.
- Preserve architecture/provider neutrality: benchmark PASS/FAIL cannot enable embeddings, change ranking weights automatically, select Tree-sitter/LSP/Sourcegraph, modify product code or grant publication authority.
- Add Scenario 129 executable lifecycle evidence and raise Scenario Conformance to 129 total / 0 manual / 20 deterministic / 55 lifecycle / 54 agent_eval / 129 automated / 0 uncovered (100% automated).
- The benchmark fixture passes without a semantic provider under unchanged floors: Recall@K >= 0.66, Precision@K >= 0.40, MRR >= 0.50, History Recall = 1.0, Irrelevant Context Rate <= 0.55 and Direct-source Recall Delta >= 0.60, with aggregate retrieval token usage reduced by more than 50% versus the controlled static-topic fixture.
- Feature implementation merged through #55; exact merged main `f6731faf2b20ebbdd99ba58cfe2c06f1b223c4ab` passed protected-main `repository` Run #871 before release metadata finalization.
- Constitution impact: NO. No new Role, Skill, capability category, Human Approval Gate or autonomous publication authority is introduced.
- Architecture Diagram Impact: YES. A detailed Retrieval Quality Evaluation feedback loop and Human/Agent Project Intelligence documentation were added while Runtime Harness, Product Delivery, Installation and Evolution Radar topology remain unchanged.

## 0.21.0

### Just-in-Time Retrieval Intelligence

- Evolve Project Intelligence into a two-layer model: stable evidence/authority-aware Project Intelligence plus a rebuildable Just-in-Time Retrieval Intelligence cache for task-specific repository evidence.
- Add a workspace-scoped local SQLite retrieval index with lexical FTS search, language-aware symbol matching, related-test weighting, Impact Graph path boosts and relevant Git commit/diff history without making the cache a canonical source of truth.
- Add incremental retrieval freshness bound to the active workspace: committed and dirty changed paths are refreshed before query results are returned, while each result carries path/line or commit provenance, content hash, Git HEAD and dirty-workspace fingerprint.
- Add bounded context assembly with deterministic result limits and token budgeting so Agents receive high-relevance evidence instead of preloading unrelated modules or whole-repository summaries.
- Integrate Retrieval Intelligence with the existing Turn Context Manifest and runtime hook while preserving the existing stable Project Intelligence fallback when the retrieval index is missing or unavailable.
- Add `aips intelligence index` and `aips intelligence retrieve` commands as deterministic/local building blocks; normal Agent use may create the index when Turn Context reports `retrieval_index_required=true`.
- Keep semantic/embedding retrieval provider-neutral and optional. The v0.21.0 core truthfully reports `semantic.status: NOT_CONFIGURED` when no provider exists and continues lexical/symbol/graph/history retrieval instead of pretending semantic search ran.
- Harden secret handling across both source indexing and Git-history evidence: credential/secret path families are excluded, history diffs are restricted to safe indexable paths, and secret-like values receive defense-in-depth redaction.
- Add Scenario 128 executable lifecycle evidence covering target implementation + related tests, relevant Git history, unrelated-module exclusion, dirty-workspace incremental refresh, secret-path exclusion, provenance, token budget and Turn Context integration.
- Raise Scenario Conformance to 128 total / 0 manual / 20 deterministic / 54 lifecycle / 54 agent_eval / 128 automated / 0 uncovered (100% automated).
- Feature implementation merged through #53; exact merged main `b92f5b8d062b5bd1976cf14fb6172aad243a1f45` passed protected-main `repository` Run #831 before release metadata finalization.
- Constitution impact: NO. No new Role, Skill, capability category, Human Approval Gate or autonomous merge/release authority is introduced; Retrieval Intelligence remains a lower-layer Project Intelligence infrastructure capability.
- Architecture Diagram Impact: YES. Runtime flow, Human architecture overview, Project Intelligence Human/Agent documentation, Technology Guide, Conformance and Documentation Consistency mappings were updated for bounded just-in-time retrieval.

## 0.20.0

### Governed Semantic Evolution and Human Documentation Namespace

- Extend Evolution Radar from collection-only research into scheduled provider-neutral semantic analysis when a configured provider credential is available, while preserving truthful `ANALYSIS_PENDING` fallback when credentials are missing, provider execution fails or deterministic output validation rejects the result.
- Bind semantic recommendations to the exact Radar evidence digest and repository revision; keep provider/model output advisory-only while deterministic AIPS code owns baseline, fingerprints, provenance and all authority=false governance fields.
- Add explicit Human Decision Binding for `REJECT`, `HOLD`, `ASSESS`, `TRIAL` and `ADOPT`, including candidate/evidence/baseline/scope/actor/time fingerprints and fail-closed positive progression when the Radar baseline is stale.
- Add Human-approved Controlled Trial execution inside an AIPS-managed Git worktree using bounded approved path globs, forbidden governance/publication paths, changed-file and diff-line limits, no trial commits, repository validation and PASS / FAIL / BLOCKED Trial Reports.
- Add optional PASS Trial → ADOPT evidence binding that verifies the exact Trial fingerprint, candidate, signal and baseline before handing off to the existing System Self-Improvement process; Trial success never grants code publication, PR, merge or release authority.
- Keep Evolution Radar / Human Decision workflow repository permissions at `contents: read` + `issues: write`; semantic analysis runs read-only and Trial execution remains ephemeral workspace mutation without persisted GitHub credentials or remote publication authority.
- Add Documentation Consistency Contract enforcement so configured behavior-bearing changes require mapped Human docs, Agent docs and the Human Technology Guide to be updated in the same Git change.
- Establish `docs/human/` as the canonical namespace for Human-only permanent documentation, preserve explicit shared canonical technical references outside it, and require registered standalone Human-only artifacts outside the namespace to use the `HUMAN_` prefix.
- Add the Human Evolution Radar lifecycle overview and bilingual Technology Guide, update all migrated links/assets, and enforce both audience placement and stale legacy-path detection deterministically.
- Add Scenario 127 and raise Scenario Conformance to 127 total / 0 manual / 20 deterministic / 53 lifecycle / 54 agent_eval / 127 automated / 0 uncovered (100% automated).
- Feature implementation merged through #51; exact merged main `ccea8d523546ea7bbf52ac7c6775f769a9c75843` passed protected-main `repository` Run #800 before release metadata finalization.
- Constitution impact: NO. No new Role, Skill, Human Approval Gate or autonomous formal implementation/release authority is introduced. Quarterly Evolution Review, automatic adoption after Trial PASS, automatic formal implementation PR creation, merge and release remain outside this release.
- Architecture Diagram Impact: Human architecture/Evolution Radar diagrams and documentation were updated for the new maintenance-plane behavior; existing runtime Harness, Project Intelligence, Product Delivery and installation topology remains unchanged.

## 0.19.2

### Lifecycle Validation Reliability

- Stabilize repository lifecycle validation after v0.19.1 exposed intermittent `TemporaryDirectory` teardown races in temporary Git repositories and bare remotes; these failures happened after successful assertions and reproduced as `Directory not empty: .../.git`-style cleanup errors.
- Preserve the original #47 validation-only `gc.auto=0` and `gc.autoDetach=false` protection, while recording that it was insufficient under repeated post-merge stress validation.
- Complete the fix in #48 by also disabling modern automatic Git maintenance with `maintenance.auto=false` and `maintenance.autoDetach=false`, and by propagating the same validation-only policy through an isolated `GIT_CONFIG_GLOBAL` so local-transport child Git processes such as `receive-pack` inherit it.
- Keep product/runtime Git behavior unchanged: no user, system or repository Git configuration is written, and the no-maintenance policy exists only for the repository validation process and inherited evidence subprocesses.
- Preserve fail-closed cleanup semantics: validation does not catch, ignore or retry `TemporaryDirectory` cleanup errors inside evidence, so unrelated resource leaks and teardown failures still fail CI truthfully.
- Validate the final #48 head through four consecutive full `repository` workflow successes, then verify the protected merged main SHA with repeated successful `repository` checks before release finalization.
- Keep Scenario Conformance at 126 total / 0 manual / 19 deterministic / 53 lifecycle / 54 agent_eval / 126 automated / 0 uncovered (100% automated); no new Scenario, Role, Skill, capability category, Approval Gate or subsystem is introduced.
- Quarterly Evolution Review and autonomous experiment execution remain deferred.
- Architecture Diagram Impact: N/A — this patch changes validation-process reliability only and does not change runtime topology, product behavior, Constitution semantics or Human Authority.

## 0.19.1

### Evolution Radar Public Network Safety

- Enforce the existing `public_only: true` Evolution Radar policy as an executable network boundary instead of descriptive configuration.
- Require credential-free HTTPS source URLs and reject localhost plus literal loopback, private, link-local, reserved and other non-global destinations.
- Resolve source hostnames before connection, fail closed when any resolved address is non-global, and connect to the validated public IP while preserving the original hostname for TLS/SNI certificate verification.
- Revalidate every redirect target, reject HTTPS downgrade, detect redirect loops and cap redirect depth at the configured maximum.
- Bound each public-source response by the configured byte limit (2 MiB in the built-in policy) in addition to the existing finite timeout and per-source item limit.
- Add deterministic lifecycle evidence for private/mixed DNS resolution, DNS failure, unsafe redirects, redirect depth/loop handling, credential-bearing URLs and oversized responses while preserving `ANALYSIS_PENDING`, provenance and Human-only adoption authority.
- Keep Scenario Conformance at 126 total / 0 manual / 19 deterministic / 53 lifecycle / 54 agent_eval / 126 automated / 0 uncovered (100% automated); no new Scenario, Role, Skill, capability category, Approval Gate or subsystem is introduced.
- Quarterly Evolution Review and autonomous experiment execution remain deferred.
- Architecture Diagram Impact: N/A — this patch hardens the existing Evolution Radar retrieval boundary without changing maintenance-plane topology, Constitution semantics or Human Authority.

## 0.19.0

### Governed Evolution Radar

- Add a governed Evolution Radar maintenance plane with bounded weekly public-source scans and monthly recurrence review, using configurable sources with explicit provenance, source-failure recording and per-source item limits.
- Normalize URLs/titles and compute deterministic fingerprints so recurring signals are deduplicated instead of repeatedly presented as novel technology.
- Build monthly review from durable prior weekly Radar Issues using fully paginated Issue retrieval, preserving recurrence evidence across the complete review period.
- Keep semantic adoption assessment provider-neutral and truthful: when no reliable analyzer is available, the Radar reports `ANALYSIS_PENDING` instead of inferring novelty, benefit or adoption suitability from popularity alone.
- Keep `COVERED`, `HOLD`, `ASSESS`, `TRIAL` and `ADOPT` advisory only; every material recommendation still requires Human decision followed by the existing System Self-Improvement / Core Change / Git Publish gates.
- Restrict scheduled workflow authority to `contents: read` and `issues: write`; Evolution Radar has no code-write, implementation-PR, merge, protected-branch or release authority.
- Add Scenario 126 lifecycle evidence and raise conformance to 126 total / 0 manual / 19 deterministic / 53 lifecycle / 54 agent_eval / 126 automated / 0 uncovered (100% automated).
- Update Human architecture documentation and `system-overview.svg` for the new maintenance plane without adding Roles, Skills, capability categories, Approval Gates or Constitution changes; Quarterly Evolution Review and autonomous experiment execution remain deferred.

## 0.18.4

### Evidence Closure and Full Scenario Conformance

- Add rendered visual evidence integrity plus real Chromium lifecycle coverage for shared-component visual repair and product consistency sweeps; promote Scenarios 039 and 055 to lifecycle while keeping screenshot existence separate from subjective visual-quality judgement.
- Add reproducible performance evidence for Scenario 004 with raw latency samples, nearest-rank p95 recomputation, measured bottleneck profiling, profile-driven specialist routing and fail-closed target verification; `sql-performance` is loaded only when measured evidence implicates SQL.
- Add hybrid Creative Evidence for Scenarios 021 and 022 using Agent Eval for semantic/creative judgement plus real desktop/mobile Chromium evidence for safe-area geometry, overflow, crop presentation and exact preservation of user-owned asset bytes. Objective artifact integrity never infers that a design is subjectively premium, minimal or fashionable.
- Add executable end-to-end Product Delivery evidence for Scenario 028 across isolated local, staging and representative production environments, binding all environments to one immutable release candidate, requiring Release Readiness plus explicit exact-candidate production promotion approval, verifying post-deploy health/smoke/log evidence and exercising recovery after an injected failure.
- Keep production claims truthful: the CI delivery lifecycle proves orchestration and gate behavior in representative isolated environments and explicitly does not claim deployment to an external/customer production platform.
- Raise conformance baseline to 125 total / 0 manual / 19 deterministic / 52 lifecycle / 54 agent_eval / 125 automated / 0 uncovered (100% automated).
- Reuse the existing Visual Quality Review, Creative Direction, Performance Profiling, Release Readiness and Product Delivery mechanisms instead of introducing duplicate Roles, Skills, capability categories or approval gates.
- Architecture Diagram Impact: N/A — this release closes evidence/conformance gaps and updates release metadata; it does not change runtime topology, product architecture, Constitution semantics or Human Authority.

## 0.18.3

### Project Intelligence Promotion

- Add a non-mutating `promotion-plan` stage for repeatedly confirmed derived project invariants; recommendation never implies authority and always reports approval required.
- Add approval-backed `promotion-apply` using the existing `PROJECT_OVERRIDES.yaml` authority container rather than introducing a new Approval Agent or gate.
- Restrict automatic authoritative mutation to new project instruction sources or `docs/` official documents; existing targets are never overwritten automatically.
- After an approved promotion, register the authoritative source in `SOURCE_REGISTRY.yaml`, transition the approval to `APPLIED`, remove duplicate derived topic content, and retain only an authoritative pointer in Project Intelligence.
- Add executable temporary-project lifecycle evidence and promote Scenario 054 from manual to lifecycle.
- Raise conformance baseline to 125 total / 6 manual / 19 deterministic / 48 lifecycle / 52 agent_eval / 119 automated / 0 uncovered (95.2% automated).
- Architecture Diagram Impact: N/A — this extends existing Project Intelligence / Project Authority mutation semantics; no runtime topology, Role, Skill, Capability category, Approval Gate, or Constitution change.

## 0.18.2

### Monorepo Lazy Intelligence

- Add an explicit component-targeted Project Intelligence selector for monorepos without introducing a second Intelligence store or prompt-based component guessing.
- Extend Project Intelligence with optional `components` and `shared_relationships` semantic indexes; `aips intelligence context --component <id>` loads only the system summary, target component topics and declared shared relationship topics.
- Keep component topics lazy when no component is requested, exclude unrelated application topics, and fail explicitly for unknown components instead of falling back to repository-wide preload.
- Add executable temporary-monorepo lifecycle evidence and promote Scenario 087 from manual to lifecycle.
- Raise conformance baseline to 125 total / 7 manual / 19 deterministic / 47 lifecycle / 52 agent_eval / 118 automated / 0 uncovered (94.4% automated).
- Architecture Diagram Impact: N/A — this extends the existing Project Intelligence context-selection contract only; no runtime topology, Role, Skill, Capability category, Approval Gate or Constitution change.

## 0.18.1

### Runtime / Project Instruction Conflict Composition

- Extend the v0.18.0 Project Authority conflict pipeline to runtime/project instruction conflicts instead of introducing a parallel conflict engine.
- Resolve conflict source references through `SOURCE_REGISTRY.yaml`, preserve both runtime-native and project-authoritative pointers, and expose runtime-scoped conflicts only to applicable runtimes.
- Add an additive `instruction_resolution` Turn Context surface with explicit precedence and a non-governing derived Project Intelligence guarantee.
- Keep the existing v0.18.0 fail-closed `unresolved_authority_conflict` behavior for mutating work while read-only inspection remains soft.
- Add executable lifecycle evidence and promote Scenario 064 from manual to lifecycle.
- Raise conformance baseline to 125 total / 8 manual / 19 deterministic / 46 lifecycle / 52 agent_eval / 117 automated / 0 uncovered (93.6% automated).
- Architecture Diagram Impact: N/A — this extends the existing Project Authority/context-resolution contract; no runtime topology, Role, Skill, Capability category, Approval Gate or Constitution change.

## 0.18.0

### Project Authority Reconciliation

- Implement deterministic reconciliation between later structured Project Intelligence discovery and user/project-approved `PROJECT_OVERRIDES.yaml` assertions.
- Preserve approved inferences, additional rules, exceptions and exclusions across refresh; contradictory structured discovery creates an idempotent `OPEN` authority conflict rather than replacing approved state.
- Surface active authority conflicts in Turn Context and fail closed for material mutation with `unresolved_authority_conflict`.
- Add the stable `aips intelligence reconcile-overrides` CLI command and lifecycle evidence covering refresh preservation, contradictory evidence, idempotence, CLI routing and mutation blocking.
- Promote Scenario 082 from manual to lifecycle. Scenario 064 remains manual because v0.18.0 surfaces registered semantic conflicts but intentionally does not guess arbitrary Markdown conflicts by keyword heuristics.
- Raise conformance baseline to 125 total / 9 manual / 19 deterministic / 45 lifecycle / 52 agent_eval / 116 automated / 0 uncovered (92.8% automated).
- Architecture Diagram Impact: N/A — this completes an existing Project Intelligence authority contract; no new Role, Skill, Capability category, Approval Gate, Constitution layer, or runtime topology is introduced.

## 0.17.1

### Residual Harness Migration Evidence Maturity

- Add executable lifecycle evidence for legacy AIPS installation migration through preflight into the managed Global Harness model.
- Verify the old preflight fast-forwards and re-execs the updated CLI, an installed system refreshes managed Harness content, user-owned instructions survive composition, colliding foreign registrations remain CONFLICT/MANUAL, and a plain repository checkout does not register the Global Harness implicitly.
- Promote Scenario 068 from manual to lifecycle without adding or changing runtime product behavior.
- Keep the remaining manual Scenarios truthful: visual scenarios still require rendered evidence; API performance requires measured benchmark evidence; 028/054/064/082/087 require additional end-to-end product capabilities or conflict/lazy-loading behavior before promotion.
- Raise conformance baseline to 125 total / 10 manual / 19 deterministic / 44 lifecycle / 52 agent_eval / 115 automated / 0 uncovered (92.0% automated).
- Architecture Diagram Impact: N/A — evidence, validation and release metadata only; no runtime topology, Role, Skill, Capability, Approval Gate or Constitution change.

## 0.17.0

### Project / Architecture Lifecycle Evidence Maturity

- Add Agent Eval evidence for brownfield REST change planning, infrastructure cost analysis, Deployment Unit repository strategy, review-learning feedback and evidence-based Project Intelligence discovery.
- Add executable legacy Project Knowledge migration lifecycle evidence that preserves `.ai/knowledge` as migration evidence while new reusable conclusions write to canonical Project Intelligence and authoritative sources remain pointer-over-copy.
- Promote Scenarios 002, 006, 029, 043 and 052 to agent_eval, and Scenario 088 to lifecycle.
- Keep Scenarios 004, 028, 054 and 087 manual because their complete contracts require reproducible performance measurement, full production delivery lifecycle, approval-backed authoritative promotion, or real monorepo lazy-loading evidence respectively.
- Raise conformance baseline to 125 total / 11 manual / 19 deterministic / 43 lifecycle / 52 agent_eval / 114 automated / 0 uncovered (91.2% automated).
- Architecture Diagram Impact: N/A — evidence/conformance and release metadata only; no runtime topology, Role, Skill, Capability, Approval Gate or Constitution change.

## 0.16.9

### Interaction & Context Evidence Maturity

- Add Agent Eval evidence for scoped instruction conflict handling, adaptive bounded subagent/model routing, safe professional defaults, external-context authorization/resume, external-context fallback and Architecture Diagram Impact decisions.
- Promote Scenario 063 to lifecycle using the existing executable normal-chat Harness/Project Intelligence fixture; it verifies general conversation remains EPHEMERAL and does not create `.ai/`, External Project Intelligence or Change Impact state.
- Keep Scenarios 064, 068 and 082 manual: current executable evidence covers adjacent source composition, preflight/Harness lifecycle and Project Intelligence refresh behavior, but does not yet exercise each scenario's complete contract end to end.
- Promote Scenarios 008, 010, 036, 037, 038 and 065 to agent_eval, and Scenario 063 to lifecycle.
- Raise conformance baseline to 125 total / 17 manual / 19 deterministic / 42 lifecycle / 47 agent_eval / 108 automated / 0 uncovered (86.4% automated).
- Architecture Diagram Impact: N/A — evidence/conformance metadata only; no runtime topology, Role, Skill, Capability or Approval Gate change.

## 0.16.8

### Product & Visual Evidence Maturity

- Add Agent Eval evidence for Product Creation, design-only Nordic concepts, aspect-level mixed references, reusable Brand System creation and evidence-driven redesign escalation.
- Add deterministic Project Visual Profile freshness evaluation plus lifecycle evidence: unchanged watched visual sources reuse the approved profile, while changed shared tokens/components trigger targeted refresh instead of a blind full rescan.
- Keep Scenarios 021, 022, 039 and 055 manual because complete verification requires real rendered/screenshot evidence that the repository-only harness cannot currently produce.
- Promote Scenarios 001, 003, 023, 024 and 040 to agent_eval, and Scenario 056 to lifecycle.
- Raise conformance baseline to 125 total / 24 manual / 19 deterministic / 41 lifecycle / 41 agent_eval / 101 automated / 0 uncovered (80.8% automated).
- Architecture Diagram Impact: N/A — no runtime topology, Role, Skill, Capability or Approval Gate change.

## 0.16.7

### Core Planning & Change Assurance Semantic Evidence Maturity

- Add Agent Eval evidence for delivery sequencing from an existing complete plan, adaptive DDD/Clean Architecture use, capability gaps, Documentation Impact, reproducible two-gate Planning Packages, deterministic preprocessing, audience-separated documentation and Core Change impact-derived testing.
- Add scope-expansion evidence that recomputes the Core Change Test Matrix, executes newly applicable checks, reruns affected review and follows applicable reapproval.
- Promote Scenarios 005, 007, 009, 012, 013, 026, 027, 092 and 093 from manual to agent_eval.
- Raise conformance baseline to 125 total / 30 manual / 19 deterministic / 40 lifecycle / 36 agent_eval / 95 automated / 0 uncovered (76.0% automated).
- No runtime behavior, Role, Skill, Capability, Approval Gate or architecture-topology change.

## 0.16.6

### Security & Production Readiness Semantic Evidence Maturity

- Add Agent Eval evidence for proportional security assurance across critical financial boundaries, low-impact frontend work and cosmetic changes inside critical products.
- Add semantic evidence for security planning/review, Release Readiness blockers, production verification/recovery, staging N/A for low-risk static products and deployment automation with missing platform access.
- Promote Scenarios 014-016 and 030-034 from manual to agent_eval.
- Raise conformance baseline to 125 total / 39 manual / 19 deterministic / 40 lifecycle / 27 agent_eval / 86 automated / 0 uncovered (68.8% automated).
- No runtime behavior, Role, Skill, Capability, Approval Gate or architecture-topology change.

## 0.16.5

### Quality & Release Semantic Evidence Maturity

- Add Agent Eval evidence for Q2 quality baseline selection and independent quality-dimension adjustment.
- Add semantic evidence for deriving draft quality targets from product scale, failure impact, sensitivity, delivery and operations context without forcing users to invent p95/RTO/RPO.
- Add evidence for LOCAL_COMPLETE before optional Production Enablement when production was not requested.
- Add evidence for explicit production requests: plan production concerns from the start, still verify LOCAL_COMPLETE, then continue without a redundant deploy question and require Release Readiness.
- Add provider-neutral observability evidence before vendor selection.
- Add high-value audit logging evidence for balance/points/refund/role actions with stronger access/integrity/retention/redaction requirements.
- Promote Scenarios 045-050 from manual to agent_eval.
- Raise conformance baseline to 125 total / 47 manual / 19 deterministic / 40 lifecycle / 19 agent_eval / 78 automated / 0 uncovered (62.4% automated).
- No runtime behavior, Role, Skill, Capability, Approval Gate or architecture-topology change.

## 0.16.4

### Governance & Security Semantic Evidence Maturity

- Add provider-neutral Agent Eval evidence for Git Publish Approval, Change Impact before mutation, secure runtime credential acquisition, active secret-exposure release blocking and private-config rejection during Skill admission.
- Reconcile Scenario 084 from malformed legacy Markdown into the current pre-mutation impact + post-diff reconciliation contract.
- Bind all five new observable GPT-5.6 Sol results to exact Case SHA-256 fingerprints and deterministic rubrics.
- Keep Git publication command guards and secret scanner evidence as lower-layer deterministic controls while using Agent Eval for the higher-level semantic decisions.
- Promote Scenarios 018, 084, 089, 091 and 095 from manual to agent_eval.
- Raise conformance baseline to 125 total / 53 manual / 19 deterministic / 40 lifecycle / 13 agent_eval / 72 automated / 0 uncovered (57.6% automated).
- No runtime behavior, Role, Skill, Capability, Approval Gate or architecture-topology change.

## 0.16.3

### Intelligence Context Evidence Maturity

- Add focused executable evidence for Project Intelligence source-pointer and normal-chat context behavior.
- Verify AGENTS, CLAUDE, GEMINI and official project docs remain authoritative pointers with `content_duplicated: false`.
- Verify runtime-aware deduplication: sources already native to the current Runtime are not reinjected as project context, while non-native authoritative sources remain targeted-load pointers.
- Verify deterministic bootstrap does not copy authoritative instruction/doc content into derived Intelligence topics.
- Verify normal general-knowledge turns may receive compact Harness context without creating project `.ai/`, External Project Intelligence or Change Impact state.
- Reconcile Scenarios 076 and 086 into explicit current contracts and promote them from manual to lifecycle coverage.
- Keep Scenarios 064, 082, 084, 087 and 088 manual because their full semantic/behavioral contracts are not yet deterministically enforced; no partial-coverage promotion is claimed.
- Raise conformance baseline to 125 total / 58 manual / 19 deterministic / 40 lifecycle / 8 agent_eval / 67 automated / 0 uncovered (53.6% automated).
- No runtime behavior, Role, Skill, Capability, Approval Gate or architecture-topology change.

## 0.16.2

### Install / Preflight Evidence Maturity

- Add isolated full CLI lifecycle evidence using temporary AIPS Git repositories, local bare remotes, temporary product repositories and isolated HOME/config/bin paths.
- Verify Update Preflight requires clean `main`, uses fast-forward-only updates, blocks divergent history and requires explicit `--allow-major` for major upgrades.
- Verify updated CLI re-entry after a successful system fast-forward.
- Verify EPHEMERAL projects are not auto-attached and target product repositories are never automatically pulled.
- Verify ATTACHED project `.ai/SYSTEM.yaml` refreshes exact AIPS version/commit provenance after update.
- Verify attach/status/detach/restore/uninstall lifecycle and preservation of product source, project workspace, External Intelligence, system repository and venv by default.
- Verify explicit cache/venv removal remains opt-in.
- Verify regular-file and foreign-symlink CLI collisions are non-destructive while the exact AIPS-owned symlink can be safely reused.
- Ignore Python `__pycache__/` and `*.py[cod]` runtime artifacts so normal AIPS Python execution cannot make the System repository fail its own clean-worktree preflight gate.
- Promote Scenarios 011, 044 and 069 from manual to lifecycle coverage.
- Raise conformance baseline to 125 total / 60 manual / 19 deterministic / 38 lifecycle / 8 agent_eval / 65 automated / 0 uncovered (52.0% automated).
- No Role, Skill, Capability, Approval Gate or architecture-topology change; architecture diagrams are N/A.

## 0.16.1

### Focused Harness Evidence Maturity

- Add focused executable Harness runtime lifecycle evidence using isolated fake Codex, Claude and Gemini runtimes.
- Verify truthful runtime installation status, Context Capability and Governance Enforcement state.
- Fix Harness Resolution to expose `runtime.governance_enforcement` separately from context `capability`, aligning runtime output with the existing Adapter Contract.
- Verify Gemini uses the official namespaced extension mechanism with BeforeAgent Turn Context and does not overwrite user GEMINI.md/settings.
- Verify projects without .ai remain EPHEMERAL during Harness resolution and are not auto-attached.
- Verify Gemini uninstall targets only aips-global-harness.
- Verify failed AIPS-owned Gemini unregister preserves ownership state for safe retry and succeeds after the runtime issue is resolved.
- Reconcile malformed Scenario 072 Markdown into the current Gemini BeforeAgent contract.
- Promote Scenarios 057, 061, 066, 067, 072 and 073 from manual to lifecycle coverage.
- Raise conformance baseline to 125 total / 63 manual / 19 deterministic / 35 lifecycle / 8 agent_eval / 62 automated / 0 uncovered (49.6% automated).
- No runtime, Role, Skill, Capability, Approval Gate or architecture behavior change.

## 0.16.0

### Provider-neutral Agent Eval Conformance

- Add provider-neutral Agent Eval cases and recorded observable results for semantic behavior that cannot be truthfully reduced to deterministic repository checks.
- Add deterministic Case SHA-256 fingerprint binding so changed eval contracts make previous recorded results stale.
- Add structured rubric scoring for equals, contains, excludes, set equality and non-empty observable fields.
- Reject private reasoning / chain-of-thought fields and high-confidence secret-like values in recorded Agent Eval results.
- Keep model execution separate from CI scoring; AIPS core requires no provider SDK and does not claim CI generated a model response.
- Add `aips conformance agent-eval check|report`.
- Promote Scenarios 017, 019, 020, 025, 035, 041, 042 and 094 from manual to agent_eval using recorded GPT-5.6 Sol observable results from the maintainer implementation session.
- Add Scenarios 121-125 for Agent Eval fingerprint, result binding, deterministic rubric, privacy/provider neutrality and lifecycle behavior.
- Raise conformance baseline to 125 total / 69 manual / 19 deterministic / 29 lifecycle / 8 agent_eval / 56 automated / 0 uncovered (44.8% automated).
- No new Role, Skill, Capability or Approval Gate.

## 0.15.1

### Validation Architecture Cleanup

- Refactor the stable `tests/validate_repository.py` entrypoint into a small aggregator over subsystem validation modules.
- Preserve existing validation semantics while separating static contracts, runtime lifecycle, governance/resume, conformance/isolation and shell syntax checks.
- Keep focused one-to-one Scenario evidence under `tests/evidence/`.
- Reorganize maintenance consistency guidance by subsystem instead of accumulating version-number sections.
- Upgrade checkout to v7.0.1 and setup-python to v7.0.0 using immutable full commit SHAs, resolving the runner Node 20 deprecation warning.
- Raise the PyYAML dependency floor to 6.0.3.
- Keep validator policy focused on immutable SHA pinning rather than freezing a specific action version.

## 0.15.0

### Canonical Project Identity and Resume Integrity

- Add one canonical repository/workspace identity contract shared by Project Intelligence, Run State and Execution Isolation.
- Separate repository_id (lineage / repository-wide coordination) from workspace_id (active worktree state) while retaining project_id as a compatibility alias.
- Add `aips identity` for deterministic identity and workspace-fingerprint diagnostics.
- Move EPHEMERAL Run State to the canonical workspace namespace with lazy migration of legacy absolute-path-hash runs.
- Upgrade run checkpoints to version 2 with repository/workspace identity, branch, dirty fingerprint and workspace fingerprint.
- Mark resume STALE when uncommitted product workspace state changes even if Git HEAD is unchanged.
- Exclude AIPS-owned `.ai/` state from workspace fingerprints so checkpoints do not stale themselves.
- Coordinate Execution Isolation writers by repository_id + Change Boundary across Git worktrees and discover verifiable legacy ownership records.
- Keep Project Intelligence on the canonical workspace namespace with compatibility migration when required.
- Add Scenarios 116-120 and executable cross-worktree / resume-integrity lifecycle evidence.
- Raise conformance baseline to 120 total / 77 manual / 43 automated / 0 uncovered.

## 0.14.2

### Governance and Public Repository Hardening

- Normalize protected Git/GitHub publication command detection across executable paths, Git/GH global options, common environment/shell wrappers and compound protected commands.
- Keep approval semantics unchanged while requiring every detected protected publication operation in a compound command to be approved.
- Add focused governance command-normalization evidence to Scenario 099.
- Harden GitHub Actions with explicit read-only contents permission and immutable full-SHA action references.
- Add Dependabot coverage for Python and GitHub Actions dependencies.
- Add SECURITY.md and link it from the Human entry documentation.
- Reconcile Architecture Overview to describe current system state rather than historical version snapshots.
- Align PATCH versioning policy with backward-compatible bug fixes and hardening.
- License selection remains an explicit maintainer decision and is not changed by this release.

## 0.14.1

### Legacy Scenario Reconciliation

- Audit legacy Scenarios 001-095 against the current canonical System, Orchestration, Harness and Project Intelligence contracts.
- Reconcile stale preflight, Project Knowledge and runtime-instruction assumptions without changing Scenario IDs or paths.
- Align legacy Project Knowledge scenarios to Project Intelligence + SOURCE_REGISTRY while preserving `.ai/knowledge/` only for migration compatibility.
- Align Codex/Claude scenarios to managed composition, ownership-safe uninstall and separate context/enforcement capability truth.
- Add focused direct evidence for adapter composition, Project Intelligence lifecycle/freshness/migration and secret redaction.
- Promote only directly exercised legacy Scenarios from manual to deterministic/lifecycle coverage.
- Update conservative conformance baseline to 115 total / 77 manual / 38 automated / 0 uncovered (33.0% automated).
- No runtime behavior, Constitution, Role, Skill, Capability registry or Approval Gate change; architecture diagrams are N/A.

## 0.14.0

### Execution Isolation

- Add explicit `shared | worktree | sandbox` isolation to the existing Execution Profile without introducing a new Role, Skill or approval gate.
- Add real AIPS-owned Git worktree lifecycle with external ownership records and one ACTIVE writer per Change Boundary.
- Block cleanup of dirty worktrees, remove only AIPS-owned managed paths and preserve managed branches after cleanup.
- Report sandbox capability truthfully: without a verified provider, sandbox is UNSUPPORTED/BLOCKED and a temporary directory is never presented as a sandbox.
- Add `aips isolation resolve|create|status|remove`, Workspace Manifest isolation state and scenarios 111-115.
- Raise conservative Scenario Conformance baseline to 115 total / 95 manual / 20 automated / 0 uncovered.
- Update Agent/Human architecture contracts and affected system/lifecycle diagrams.

## 0.13.0

### Harness Conformance

- Add a machine-readable Scenario Conformance Registry mapping every acceptance scenario to coverage type and evidence.
- Distinguish deterministic, lifecycle, agent-eval, manual and uncovered coverage instead of treating scenario count as proof of conformance.
- Add deterministic conformance check/report tooling and `aips conformance check|report`.
- Conservatively classify legacy scenarios without explicit one-to-one executable evidence as manual rather than overstating automation.
- Add scenarios 106-110 and CI checks for complete/unique registry coverage, reporting and missing-evidence failure.
- Constitution, Roles, Skills, Capabilities and Approval Gates remain unchanged.


## 0.12.0

### Observable + Resumable Harness

- Extend existing workspace state with a durable workflow checkpoint contract instead of introducing a new workflow framework.
- Add deterministic run checkpoint/event/resume helpers for ATTACHED and EPHEMERAL project modes.
- Add append-only structured `EVENTS.jsonl` evidence that excludes prompts, chain-of-thought and secret values by contract.
- Bind checkpoints to project revision and return STALE on revision drift so resume cannot silently reuse obsolete evidence.
- Add `aips run checkpoint|event|resume|status` routing and scenarios 101-105 with lifecycle validation.
- Constitution, Roles, Skills, Capabilities and Approval Gates remain unchanged.


## 0.11.0

### Enforceable Governance

- Add machine-readable Approval Records with canonical SHA-256 proposal/scope fingerprints and stale-approval detection.
- Separate Runtime context capability from Governance Enforcement capability: ADVISORY / TOOL_GUARDED / ENFORCED / UNSUPPORTED.
- Add deterministic Git-publication guard primitives for native pre-tool integrations while keeping unsupported runtimes advisory.
- Add structured Turn Context explanation metadata without persisting chain-of-thought.
- Add backward-compatible workspace governance state and scenarios 096-100.
- Constitution, Roles, Skills, Capabilities and Approval Gate count remain unchanged.


## 0.10.0

### Self-Improvement Decision Quality

- Separate User Problem, Proposed Solution and Recommended AIPS Solution so a requested mechanism is evaluated rather than accepted as system architecture by default.
- Require evidence-based checks for existing coverage, reuse/extension candidates and lower-layer alternatives before introducing new abstractions.
- Expand System Improvement Review coverage for context/token cost, security/reliability, backward compatibility, scenarios/tests, Human/Agent docs, Architecture Diagram Impact and semantic Constitution impact.

### Additional Optimization Scope Integrity

- Add Additional Optimization Confirmation for improvements discovered beyond the currently approved request.
- Classify material optimization candidates as NOW / LATER / REJECT and disclose benefit plus scope impact.
- Require explicit Human confirmation before a NOW candidate may enter implementation scope; deferred candidates must not be implemented opportunistically.
- Require scope re-approval when an approved optimization materially expands the Change Boundary.

### Deterministic Regression Protection

- Strengthen Scenario 019 for Problem/Solution separation, reuse-first evaluation and additional-optimization scope control.
- Extend repository validation to enforce the Self-Improvement protocol, review-template and Scenario 019 contracts deterministically.

### Compatibility / Governance

- Backward-compatible orchestration change; no project migration required.
- Constitution unchanged.
- No new Role, Skill, Capability or Approval Gate.

## 0.9.0

### Turn-Aware Global Harness

- Upgrade Global Harness from session/bootstrap-oriented behavior to turn-aware context resolution.
- Keep one Harness contract while using runtime-native integration: Codex CONTEXT_ALWAYS, Claude Code UserPromptSubmit when verifiable, and Gemini CLI BeforeAgent.
- Compose AIPS through reversible managed instruction blocks/hooks/extensions without replacing user-owned Agent instructions or Skills.
- Separate integration status from runtime capability truth: TURN_NATIVE / CONTEXT_ALWAYS / SESSION_ONLY / MANUAL / UNSUPPORTED.

### Project Intelligence

- Replace Project Knowledge as the canonical reusable brownfield understanding layer while preserving legacy knowledge as migration evidence.
- Add PROJECT_INTELLIGENCE, SOURCE_REGISTRY, IMPACT_GRAPH and PROJECT_OVERRIDES contracts.
- Add read-only breadth-first discovery followed by evidence-based semantic enrichment; inventory alone remains PARTIAL until finalize reaches READY.
- Add runtime-aware source deduplication, branch/worktree/dirty-path freshness, one-writer atomic updates and targeted refresh.
- Add deterministic self-contained Project Intelligence Review HTML with secret redaction.
- Add External Project Intelligence Cache so EPHEMERAL projects can reuse understanding without creating project-local .ai state.
- Add validated External ↔ Local Intelligence migration across attach/detach.

### Existing-project Change Safety

- Add Change Impact Guard and per-change impact artifacts covering inputs, outputs, data, events, consumers, security boundaries, invariants and compatibility.
- Preserve valid project-native conventions while refusing to propagate unsafe or demonstrably broken legacy patterns.
- Reconcile actual diff against declared Change Impact and refresh only affected reusable Intelligence.

### Secret / Credential Safety

- Add Secret Handling protocol for secure runtime acquisition through workload identity, secret managers, CI stores, OS/runtime credential stores or environment injection.
- Prohibit real credentials in source, prompts, Project Intelligence, generated HTML, logs, fixtures, snapshots and review artifacts.
- Add deterministic high-confidence secret leakage checker with redacted path/line/detector/fingerprint evidence; detected values are never echoed.
- Add exposure containment/rotation guidance and release blocking for unresolved active production or SAL 3–4 credential exposure.

### Core Change Testing

- Add Impact-derived Core Change Testing contract and machine-readable test matrix.
- Require applicable evidence for every materially affected Change Boundary, with concrete N/A reasons for non-applicable checks.
- Recompute required tests when implementation scope expands and block completion/release on failing or missing required evidence.

### Skill Admission Governance

- Strengthen Capability Incubation with a New Skill admission contract.
- Require reuse-first search, narrow responsibility, triggers/non-triggers, inputs/outputs/boundaries, context/model cost, scenario evidence, unique ID/path and private-config checks.
- Keep project-specific conventions in Project Intelligence and one-off automation in project/run tooling instead of proliferating system Skills.

### Documentation / Architecture / Regression

- Refresh Human and Agent documentation for Turn Harness, Project Intelligence, secret handling, strict core-change testing and safe uninstall/cache behavior.
- Add Project Intelligence architecture diagram and update system/harness/lifecycle diagrams; Product Delivery diagram remains N/A because its lifecycle is unchanged.
- Extend acceptance scenarios through Scenario 095 and executable validator coverage for managed composition, Intelligence lifecycle/freshness, secret leakage, attach/detach migration, core test selection and Skill admission.
- Constitution unchanged; no new Role, Skill or approval Gate.

## 0.8.0

### Global Agent Harness

- Add a cross-Agent Global Harness with a minimal bootstrap and lazy AIPS orchestration.
- Add Runtime Adapter contracts and built-in integrations for Codex CLI, Claude Code and Gemini CLI plus a Generic Manual fallback.
- Use AUTOMATIC / MANUAL / NOT_DETECTED / CONFLICT / ERROR machine-specific coverage states.
- Preserve runtime-native/project instructions instead of replacing them with one global override.

### Non-invasive Installation and Ownership

- Add Harness Ownership Manifest and per-adapter state.
- Never overwrite existing user AGENTS/CLAUDE/GEMINI instruction files to gain automatic coverage.
- Record AIPS-owned runtime resources and remove only owned/unchanged resources.
- Preserve modified AIPS-created bootstrap files rather than deleting possible user content.
- Preserve ownership state when a runtime registration cannot be safely removed, enabling a later uninstall retry.
- Prevent destructive ~/.local/bin/aips name collisions.

### Ephemeral and Attached Project Modes

- Make EPHEMERAL the default for projects without .ai/.
- Stop preflight from implicitly attaching projects or creating persistent AIPS state.
- Keep ATTACHED persistence opt-in through explicit aips attach.
- Add deterministic `aips harness resolve` output for runtime, project root, instructions, Knowledge and State pointers.

### Harness Lifecycle CLI

- Add `aips harness install`, `uninstall`, `status`, `doctor` and `resolve`.
- Make `aips install` enable the Global Harness and `aips uninstall` remove AIPS-owned integrations first.
- Safely refresh/migrate the Harness after installed-system preflight updates.
- Document the v0.7 → v0.8 upgrade path.

### Architecture Diagram Integrity

- Add mandatory Architecture Diagram Impact Check to the existing Documentation Impact Gate for Large/Core changes.
- Update Maintainer Mermaid flows for Global Harness, runtime/project instruction composition, EPHEMERAL/ATTACHED lifecycle and current product delivery.
- Add a Global Harness SVG and refresh system, product-delivery and installation lifecycle SVGs.
- Require affected diagrams to be updated or explicitly marked N/A with a reason.

### Documentation and Regression Coverage

- Add Traditional Chinese Harness/installation/uninstallation guidance and explain exactly what AIPS preserves.
- Add scenarios through Scenario 069 for automatic/manual adapters, ownership-safe uninstall, EPHEMERAL behavior, instruction composition, diagram impact, upgrade migration and CLI collision safety.
- Extend existing orchestration only; no new Role, Skill or approval Gate.

## 0.7.0

### Quality-aware Product Planning

- Add Q1 Lightweight / Q2 Standard / Q3 Critical quality baselines.
- Evaluate Performance, Security, Usability, Reliability, Maintainability, Resource/Cost and Delivery Time for complete products.
- Convert vague quality expectations into measurable targets/budgets, verification methods and evidence.
- Use range + confidence for resource/cost/time estimates and refine after architecture decisions.
- Keep observability requirements provider-neutral until the production environment is known.

### Local Complete and Production Enablement

- Split complete-product delivery into LOCAL_COMPLETE and PRODUCTION_VERIFIED milestones.
- Default complete-product requests to a verified locally runnable system.
- Ask whether to continue to Production only after LOCAL_COMPLETE when production was not explicitly requested.
- Carry explicit production requests through Production Enablement without a redundant second prompt.
- Plan structured logs/health/metrics/traces/audit instrumentation before deployment and choose concrete ELK/Loki/Prometheus/Grafana/OpenTelemetry/managed services later.

### Persistent Project Knowledge

- Add a Project Knowledge layer under .ai/knowledge for stable, expensive-to-rediscover information.
- Prefer pointers to AGENTS/ADR/contracts/official docs instead of duplicating authoritative content.
- Distinguish FACT / INTERPRETATION / OBSERVED_CONVENTION and AUTHORITATIVE / DISCOVERED / APPROVED / STALE states.
- Add evidence/confidence, watched paths/signals, targeted refresh and optional promotion to authoritative project rules.
- Keep cached security knowledge below active security review requirements.

### Visual Consistency Repair

- Add V1 Focused Repair and V2 Product Consistency Sweep.
- Route whole-project vague visual cleanup requests to V2.
- Add representative routes, component inventory, UI consistency baseline and visual outlier detection.
- Require variant/exception classification before normalizing differences.
- Map material findings to DOM/component/computed-style/token root causes where tooling permits.
- Add state geometry stability and rendered before/after verification.
- Persist reusable visual knowledge in PROJECT_VISUAL_PROFILE.yaml.

### Regression Coverage

- Add scenarios through Scenario 056 for quality planning, local/production milestones, observability, project knowledge and V2 visual consistency.
- Extend repository validation to new Quality/Knowledge/Visual templates and workspace contracts.
- Extend existing roles/skills only; no new Role, Skill or Gate.


## 0.6.0

### Progressive Requirement Clarification

- Add READY / NEEDS_CLARIFICATION / BLOCKED requirement readiness.
- Stop broad implementation when material ambiguity remains.
- Prefer safe professional defaults for non-material details.
- Ask only the smallest useful blocking questions with concrete options/recommendations.

### External Context Resolution

- Add connector/MCP-first resolution for user-provided external URLs and references.
- Preserve pending task/source across authorization and resume afterward.
- Fall back to public web or other supported provider paths before asking users to paste/upload content.
- Persist source/retrieval provenance.

### Visual Implementation Polish

- Add Preserve Before Redesign and Consistency First defaults.
- Add rendered Visual Implementation Audit for alignment, typography, spacing, control geometry, icon baseline, states and responsive behavior.
- Prefer shared token/component fixes over page-specific pixel patches.
- Require screenshot/rendered verification when the UI environment can be run.

### Multi-Perspective Review & Learning

- Add risk-based review panels for large/core/high-risk changes using existing specialist roles.
- Use bounded read-only reviewer scopes and independent reviewer model routing.
- Normalize/deduplicate findings before returning them to the original Author.
- Keep the original Author as the writer; use targeted re-review after fixes.
- Extract run/project/system-capability lessons and require user-approved System Improvement before permanent capability changes.

### Installation & Project Lifecycle

- Add aips attach, detach and status.
- Keep aips init as a backward-compatible attach alias.
- Add reversible detach that archives .ai rather than deleting project AI state.
- Ensure preflight respects detached-workspace safety.
- Add scripts/uninstall.sh as the symmetric uninstall wrapper.
- Expand Traditional Chinese lifecycle documentation with install/attach/preflight/detach/uninstall/reinstall guidance and an SVG lifecycle diagram.

### Regression Coverage

- Add scenarios through Scenario 044 for clarification, connector authorization/fallback, visual polish, multi-review, learning feedback and lifecycle behavior.
- Extend repository validation to new protocols/templates and run attach/status/detach/reattach lifecycle checks.


## 0.5.0

### End-to-End Product Delivery

- Add a complete-product lifecycle from user intent/materials through guided planning, implementation, local verification, staging, Release Readiness, production promotion and post-deploy verification.
- Add root `PRODUCT.yaml` as the compact Product Manifest for Deployment Units, contracts, environments, commands, delivery and observability.
- Define Product Workspace as the discoverable System of Record for specifications, brand, code, tests, infrastructure, deployment and operational artifacts.
- Treat frontend/backend/worker components as independent Deployment Units without forcing separate Git repositories.
- Default to monorepo for coordinated product work; require evidence for multi-repo boundaries.

### Local, Staging and Production

- Add Local Environment, Deployment Plan and Operations Runbook templates.
- Make Local → CI → Staging → Production the default material production flow.
- Allow staging to be N/A for genuinely low-risk/simple products with a recorded reason.
- Define production completion as verified deployment plus applicable health, smoke, logs/metrics and recovery evidence.

### Release Readiness

- Add consolidated Release Readiness protocol and YAML contract for exact release candidates.
- Cover build, test, security, migration/recovery, infrastructure, staging, observability and documentation evidence.
- READY remains technical readiness and never bypasses required human/security approval.
- Apply the existing SAL 4 unresolved High/Critical hard floor without over-blocking lower SAL risk-accepted reviews.
- Material candidate changes invalidate affected readiness evidence.

### Deployment Automation

- Require complete products to create repeatable CI/CD/deployment automation appropriate to the target platform.
- Execute deployment automation when platform access and approval are available.
- Persist runnable automation and mark delivery BLOCKED when required platform access/credentials are unavailable.
- Keep production secrets outside source control.

### Deterministic Delivery Checks

- Add `scripts/check_release_readiness.py` to evaluate structured Release Readiness data before AI reasoning.
- Add READY/BLOCKED/SAL3-risk fixtures and repository validation coverage.

### Reuse and Documentation

- Extend existing Delivery Planner, Cloud Architect, SRE and `delivery-planning` Skill rather than adding new delivery/DevOps Roles.
- Update Product Creation, Planning Package, workspace state, Traditional Chinese Human Guide and architecture diagrams.
- Add product-delivery architecture SVG and scenarios through Scenario 034.


## 0.4.0

### Creative Intelligence

- Add reference-grounded Creative Direction for websites, UI, banners, hero visuals, social assets, presentations, product pages and campaigns.
- Add progressive Creative Calibration for vague visual language and aspect-level reference mixing.
- Add reusable Style Profiles as reference data rather than style-specific Skills/Roles.
- Add Visual Quality Review that adapts checks to the artifact type.
- Prioritize user-owned assets, accepted Brand/Visual Systems and explicit user intent before generic design inference.

### Brand System

- Add reusable Brand Foundation & Brand System protocol.
- Add compact BRAND_PROFILE.yaml for agent quick-load plus deeper human-readable brand guidance.
- Add Brand Foundation, Identity, Logo, Verbal, Application and Governance templates.
- Support temporary campaign overrides without silently mutating permanent brand policy.
- Reuse Product Manager/Product Designer instead of creating new Brand roles by default.

### Capability simplicity

- Add reuse-first Capability Incubation before creating or expanding Roles, Capabilities or Skills.
- Require comparison of existing responsibility, triggers, input/output, authority and review obligations.
- Prefer Reuse → Extend → New Skill → New Capability → New Role.
- Add regression checks against unknown Work Mode default roles and duplicate YAML keys.

### Deterministic Automation

- Add Deterministic Automation First for repeatable rule-based parsing, filtering, counting, validation and transformation.
- Prefer existing tools or small Shell/Python helpers before spending model reasoning/context on raw data.
- Standardize structured JSON/YAML summaries with raw evidence referenced separately.
- Define helper lifecycle: run-local → project reusable → system reusable only after demonstrated reuse.
- Add Minimum Sufficient Reasoning as a core principle.

### Human and Agent documentation

- Split Human and Agent documentation entry surfaces.
- Human-facing docs are now Traditional Chinese with English annotations for specialized terms.
- Add 5-minute Getting Started and Documentation Map.
- Keep Agent bootloader concise and protocol-driven.
- Add a source-controlled SVG architecture overview for new users.
- Extend Documentation Impact Gate to check both Human and Agent audiences.

### Regression coverage

- Add scenarios for vague visual requests, user-owned creative assets, mixed references, reusable Brand Systems, duplicate-role prevention, deterministic automation and documentation audience separation.
- Expand repository validation for creative/brand/style/automation artifacts and documentation integrity.

## 0.3.0

### Security assurance

- Add Risk-Proportional Security Assurance with Security Assurance Levels (SAL) 0–4.
- Separate Product Baseline SAL from Change Security Impact so low-risk changes in critical products remain lightweight.
- Add critical risk floors so financial/stored-value integrity cannot be averaged down.
- Add independent Security Engineer review and release gating for high/critical affected boundaries.
- Add threat-modeling, authorization-security, business-logic-abuse, financial-integrity and security-testing skills.
- Add security planning/review templates and Risk Profile schema.
- Treat payments, refunds, stored value, balances, redeemable points/credits/vouchers/coupons and similar value flows as security boundaries.
- Keep Security Assurance separate from Reliability Impact and Model Tier.

### System self-improvement governance

- Add a protected Constitution containing only fundamental human-authority, truth, safety, stop-the-line, scope-integrity and high-risk approval principles.
- Add System Self-Improvement Review for every proposed optimization to this AI Product System.
- Require analysis of appropriateness, overlap, simpler alternatives, additional optimization, compatibility, scenario/doc impact and Constitution semantics before implementation.
- Add Constitutional Change Gate with affected-Article/risk analysis and a second explicit approval.
- Prefer Skill/Template → Workflow/Work Mode → System/Orchestration → Governance → Constitution.

### Change and Git governance

- Add Core Change Approval Gate for semantically large/core changes before implementation.
- Add Git Publish Approval Gate with complete changed-file list, feature summary, validation evidence, atomic commit plan and target before remote publication.
- Group commits by logical capability/reviewability/revertability rather than by file.
- Require re-approval when approved implementation scope or publication plan materially drifts.
- Add security, core-change, Git-publish, self-improvement and constitutional regression scenarios.

## 0.2.0

- Add `aips` CLI with install, uninstall, init, update, preflight, doctor, validate and version commands.
- Add safe Update Preflight using a clean-worktree check, `git pull --ff-only`, divergence blocking and explicit major-version approval.
- Record exact AI Product System version and commit in each initialized project at `.ai/SYSTEM.yaml`.
- Add Documentation Impact Gate and source-controlled Mermaid architecture diagrams.
- Add GitHub Actions validation for repository integrity.
- Add Reproducible Planning Package for authoritative product/project planning.
- Add workspace-first persistence rule for primary planning tasks.
- Add two-stage approval: Planning Package Approval, then Implementation Readiness Approval.
- Add complete planning templates covering product, UX, key visual/visual system, architecture, API, implementation readiness and decisions/assumptions.
- Add installation/lifecycle and planning-gate regression scenarios.

## 0.1.0

- Initial governed AI Product System baseline.

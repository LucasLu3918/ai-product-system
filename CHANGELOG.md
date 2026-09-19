# Changelog

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

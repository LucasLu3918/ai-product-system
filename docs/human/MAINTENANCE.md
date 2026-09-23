# System Maintenance

## Documentation Impact Gate

Every system change must assess downstream documentation and behavior before completion.

| Area | Update when affected |
|---|---|
| `SYSTEM.md` | routing, planning gates, precedence, context or completion behavior changes |
| `orchestration/*` | detailed execution/model/instruction/planning behavior changes |
| `docs/ARCHITECTURE.md` | runtime flow, planning flow, boundaries or update lifecycle changes |
| `README.md` | Human first-entry behavior changes |
| `docs/GETTING_STARTED.md` | Human quick-start changes |
| `docs/USER_GUIDE.md` | Human-facing workflows/commands change |
| `docs/INSTALLATION.md` | Human installation/update lifecycle changes |
| `docs/ARCHITECTURE_OVERVIEW.md` | Human architecture overview changes |
| `docs/assets/*.svg` | Human-facing architecture/lifecycle diagram changes |
| `docs/HARNESS.md` | Global Harness / Adapter / ownership behavior changes |
| `harness/*` | Global Harness / Adapter contract changes |
| `AGENTS.md` | Agent bootloader changes |
| `examples/*` | a new behavior needs a practical example |
| `tests/scenarios/*` | routing/gate behavior changes or regressions need coverage |
| templates/schemas | persisted contract/state/planning/brand/creative/automation shapes change |
| `orchestration/CREATIVE_DIRECTION.md` | creative workflow changes |
| `orchestration/BRAND_SYSTEM.md` | brand workflow/precedence changes |
| `orchestration/CAPABILITY_INCUBATION.md` | Role/Skill creation/reuse behavior changes |
| `orchestration/SECRET_HANDLING.md` | credential acquisition/redaction/exposure behavior changes |
| `orchestration/CORE_CHANGE_TESTING.md` | core-change test-selection/completion behavior changes |
| `orchestration/DETERMINISTIC_AUTOMATION.md` | tool-vs-reasoning routing changes |
| `orchestration/PRODUCT_DELIVERY.md` | complete-product lifecycle changes |
| `orchestration/RELEASE_READINESS.md` | release/deployment readiness changes |
| `templates/product/*` | Product Manifest / workspace contract changes |
| `templates/delivery/*` | Local/deployment/release/runbook contract changes |
| `VERSION` | release version changes |
| `CHANGELOG.md` | every released behavioral change |

If an item is not affected, mark it N/A during change review rather than editing it unnecessarily.

## Architecture Diagram Impact Check

Every Large/Core Change must explicitly assess architecture-diagram impact as part of the existing Documentation Impact Gate. This is not a new approval gate.

Trigger examples: Runtime/Routing/Context-loading flow changes; Harness/Adapter/instruction precedence changes; Project persistence/workspace lifecycle changes; complete-product/Release lifecycle changes; major Security/Quality/Review lifecycle changes; Install/Update/Uninstall behavior changes; a major new subsystem or boundary.

Required review set:

- docs/ARCHITECTURE.md Mermaid;
- docs/ARCHITECTURE_OVERVIEW.md;
- docs/assets/system-overview.svg;
- docs/assets/harness-overview.svg when Harness is affected;
- docs/assets/product-delivery-overview.svg when delivery is affected;
- docs/assets/project-intelligence-overview.svg when Turn Context / Project Intelligence / Change Impact is affected;
- docs/assets/system-lifecycle.svg when install/project lifecycle is affected.

For every relevant diagram: Affected → update diagram + explanation; Not affected → record N/A + concrete reason.

A Large/Core Change that materially changes a documented architecture flow but leaves the corresponding diagram stale is documentation-incomplete and must not be released as complete.

## Self-improvement / Constitution / publish approval

Changes to this system first pass `orchestration/SYSTEM_SELF_IMPROVEMENT.md`.

If Constitution semantics are affected, the Constitutional Change Gate must complete before implementation. Material system changes also require Core Change Approval.

Before remote publication, present the Git Publish Proposal. A material difference from the approved implementation/publication plan requires re-approval.

Multi-file changes should normally be assembled into one coherent remote branch update after the logical change is complete. Avoid file-by-file remote commits/pushes that expose temporary incomplete repository states to CI. If incremental remote publication is necessary for collaboration or diagnosis, record that reason in the Git Publish Proposal.

## Release checklist

1. Confirm System Improvement Review and applicable Constitutional/Core Change approvals.
2. Run `aips validate`.
3. Review the Documentation Impact Gate.
4. For Large/Core changes, complete Architecture Diagram Impact Check.
5. Confirm Mermaid and affected Human SVG diagrams match actual behavior.
6. Build the Impact-derived Test Matrix for the final Change Boundary and execute every applicable check.
7. Confirm changed routing/gate behavior has scenario coverage.
8. Confirm planning/creative/brand/automation/product-delivery templates match their protocols when affected.
9. Confirm Human and Agent documentation audiences are synchronized when behavior affects them.
10. Confirm applicable secret/credential leakage and handling review is complete; secret-scan evidence must not echo secret values.
11. Update `VERSION` using SemVer.
12. Update `CHANGELOG.md`.
13. Ensure the system working tree is clean before publishing.
14. Prepare the Git Publish Proposal and obtain explicit approval.
15. Prefer independent review/PR for material system changes.

## Versioning

- MAJOR: incompatible governance/protocol/contract changes.
- MINOR: backward-compatible new behavior, role, skill, work mode, CLI capability or schema/planning extension.
- PATCH: backward-compatible bug fix, hardening, clarification, typo or non-behavioral documentation/evidence correction.

Major updates are not auto-applied by `aips preflight` without explicit `--allow-major`.


## Documentation audience

- Human docs use Traditional Chinese. Specialized terms include English on first use.
- Agent docs remain concise English unless a concrete reason requires otherwise.
- Do not maintain duplicate full Human guides in two languages by default.
- `docs/DOCUMENTATION_MAP.md` is the audience map.
- When behavior changes, explicitly check both Human and Agent documentation impact.

## Simplicity / reuse review

Before release, check:
- no unnecessary new Role when an existing Role can own the work;
- no new Skill that merely represents a visual style/artifact type;
- no duplicate Role/Skill IDs;
- repeated rules live in one authoritative protocol and are referenced elsewhere;
- bootloader/README remain short entry documents;
- deterministic data processing uses helpers when this materially reduces repeated model work.


## Product delivery consistency

When end-to-end delivery behavior changes, verify together:
- PRODUCT.yaml contract;
- Product Creation Work Mode;
- Planning Package;
- Local Environment / Deployment Plan / Runbook;
- Release Readiness;
- Security Assurance interaction;
- Human architecture overview;
- production scenarios and validator coverage.


## Subsystem consistency map

### Interaction / requirement / external context

When these behaviors change, review together:

- Requirement clarification → SYSTEM / ORCHESTRATOR / IMPLEMENTATION_GOAL / Human Guide / scenarios.
- External context resolution → connector-first protocol / provenance template / Human Guide / scenarios.
- Visual polish → Product Designer / Frontend Engineer / visual-quality-review / Design Work Mode / screenshots/state scenarios.
- Multi-perspective review → Quality Reviewer / code-review / Model Routing / Review templates / lesson persistence.

### Product delivery / quality / visual state

When product-delivery behavior changes, review together:

- QUALITY_PLANNING / QUALITY_PROFILE / Planning Package / Product Delivery / Product Manifest / Release Readiness;
- LOCAL_COMPLETE / Production Enablement / PRODUCTION_VERIFIED lifecycle;
- Project Visual Profile / Visual Audit / Product Designer / Frontend Engineer / visual-quality-review;
- Human Guide, product-delivery architecture diagram and applicable scenarios.

### Harness / Runtime adapters

When Harness behavior changes, review together:

- harness/BOOTSTRAP + HARNESS_PROTOCOL + ADAPTER_CONTRACT;
- Runtime Adapter registry/files;
- HARNESS_RESOLUTION + INSTRUCTION_RESOLUTION;
- bin/aips install/uninstall/preflight/resolve/status/doctor;
- README / GETTING_STARTED / INSTALLATION / HARNESS;
- system-overview / harness-overview / system-lifecycle SVG;
- Ephemeral/Attached scenarios and ownership regression evidence.

Never trade away user-owned instruction/Skill preservation merely to improve automatic coverage.

Install / Preflight lifecycle evidence should run against isolated temporary Git repositories and local bare remotes. System runtime artifacts such as Python `__pycache__/` / `*.py[cod]` must remain ignored so ordinary AIPS CLI execution cannot make the System repo fail its own clean-worktree preflight gate.

### Project Intelligence / Change Impact

When Project Intelligence behavior changes, review together:

- PROJECT_IDENTITY / PROJECT_INTELLIGENCE / CHANGE_IMPACT / Project Knowledge compatibility;
- TURN_HARNESS / HARNESS_RESOLUTION / INSTRUCTION_RESOLUTION;
- Project Intelligence templates + workspace MANIFEST/STATE;
- project_intelligence.py / turn_context_hook.py / bin/aips;
- README / GETTING_STARTED / PROJECT_INTELLIGENCE / USER_GUIDE;
- project-intelligence / system / lifecycle diagrams;
- freshness, source-registry, HTML, migration, single-writer and Change Impact evidence.

Legacy Project Knowledge remains compatibility input only. New reusable understanding belongs in Project Intelligence.

Focused Intelligence context evidence must distinguish storage deduplication from runtime-context deduplication. Do not promote conflict/override/change-impact/monorepo/migration Scenarios until their full contracts are actually enforced and directly exercised.

## Impact-derived regression testing

For every Large/Core Change, testing is derived from the final Change Boundary, not from a fixed minimum smoke suite.

Build and persist a matrix:

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|

Rules:

- every materially affected boundary has applicable evidence;
- N/A requires a concrete reason;
- public contract changes require contract/consumer coverage;
- persistence/schema changes require migration/rollback/recovery evidence when applicable;
- Runtime/Harness/CLI changes require executable lifecycle/regression tests;
- security-boundary or credential-handling changes require security/secret-leakage evidence;
- documentation/schema/template contract changes require structural validation;
- if implementation expands the Change Boundary, recompute the matrix;
- failing required tests block completion/release;
- never remove a relevant test merely to obtain a green result.

Prefer the strongest practical deterministic evidence for affected behavior while avoiding unrelated full-suite cost that adds no confidence.

## Governance enforcement consistency

When Approval Binding / Governance Enforcement changes, review together:

- Approval Record template + governance_guard.py;
- Git Publish/Core Change/System Improvement approval fields;
- Runtime adapter state/ownership and Claude/Gemini pre-tool hooks;
- TURN_CONTEXT_MANIFEST explanation metadata;
- Harness/System architecture diagrams;
- scenarios 096-100 and focused governance evidence.

Do not claim TOOL_GUARDED when the installed pre-tool guard is absent or unverifiable.

## Durable Run State consistency

When durable run state changes, review together:

- PROJECT_IDENTITY + RUN_RESUME;
- RUN_CHECKPOINT + workspace STATE;
- aips_identity.py + run_state.py + bin/aips run/identity routing;
- ATTACHED / EPHEMERAL storage and legacy migration;
- revision / branch / dirty workspace fingerprint behavior;
- EVENTS.jsonl redaction / no-transcript contract;
- resume/identity scenarios and executable lifecycle evidence;
- system/lifecycle diagrams.

Resume must never bypass current governance, security, impact or verification gates.

## Scenario Conformance consistency

When Scenario behavior/coverage changes, review together:

- tests/scenarios/*;
- tests/scenario_coverage.yaml;
- scripts/scenario_conformance.py + scripts/agent_eval.py;
- tests/agent_eval/cases/* + tests/agent_eval/results/*;
- tests/evidence/*;
- tests/validation/* + tests/validate_repository.py;
- orchestration/CONFORMANCE.md;
- docs/CONFORMANCE.md / USER_GUIDE;
- coverage claims in CHANGELOG/release evidence.

Before promoting legacy manual coverage: reconcile the Scenario to current canonical behavior, add direct evidence, then reclassify. For semantic behavior, Agent Eval requires an actual recorded observable Result bound to the exact Case fingerprint and passing deterministic scoring. Never infer automated coverage from Scenario count or an eval prompt alone.

## Execution Isolation consistency

When Execution Isolation behavior changes, review together:

- PROJECT_IDENTITY + EXECUTION_ISOLATION;
- execution-profile schema + workspace MANIFEST;
- execution_isolation.py + bin/aips isolation routing;
- repository-level writer ownership / workspace identity / dirty cleanup;
- truthful sandbox capability reporting;
- architecture docs/diagrams;
- scenarios 111-120 and identity/isolation lifecycle evidence.

## Public repository / CI consistency

`aips trajectory evaluate` 與 Scenario 167 是 Eval-as-CI 的 deterministic evidence；更新 trajectory schema、policy 或 publish wiring 時，必須同步執行 Integration Gate、Repository validation 與文件 impact closure。

Portable Command 變更必須同時驗證 Registry、renderer、CLI lifecycle、MCP read-only facade、ownership conflict 與相關 canonical documentation；版本更新不得把 Host-native capability 誤標為已驗證。
本機與 GitHub 必須透過 `scripts/publish_preflight.py` 共用 base/head、change class、canonical matrix 與 diff-aware documentation base。發布提案前先執行 `aips publish plan`，確認 protected branch 路由與 PR label；未帶 `AIPS_DOCS_DIFF_BASE` 的一般 validation 不得宣稱為 CI-parity 證據。

Browser evidence 同樣必須先通過 version 與 isolated-profile headless smoke probe；系統 Chrome 啟動層失敗應標記為 environment blocker，不得誤報成產品回歸。

Publication preflight must run against an exact, clean candidate. It verifies recursive documentation impact, placement rules, candidate head/base and Core Matrix binding before the expensive Integration Gate; a dirty workspace or stale candidate is blocked rather than silently treated as the PR revision.

When public repository hardening changes, review together:

- .github/workflows/validate.yml;
- .github/dependabot.yml;
- SECURITY.md;
- requirements.txt;
- immutable full-SHA action pinning;
- explicit least-privilege workflow permissions;
- validation trigger policy: automatic on PR synchronization and main pushes, manual via workflow_dispatch, not on every standalone feature-branch push;
- concurrency cancellation so a newer PR/main validation supersedes older in-progress work for the same ref/PR;
- atomic remote branch-update practice so CI receives coherent logical states instead of file-by-file intermediate states;
- validator contracts that check policy properties rather than freezing one dependency version.

## Validation architecture consistency

Portable Command contract 位於 `tests/validation/portable_commands_contracts.py`，涵蓋 registry、projection install、status 與修改檔案 conflict；它不授予 merge 或 release authority。
`tests/validate_repository.py` is the stable CI/user entrypoint. Internal validation is modular:

- `tests/validation/static_contracts.py` — schemas, indexes, documentation and static repository contracts;
- `tests/validation/runtime_contracts.py` — Harness / Runtime / Intelligence lifecycle checks;
- `tests/validation/governance_resume.py` — approval binding and durable-run behavior;
- `tests/validation/conformance_isolation.py` — Scenario Conformance, identity and isolation checks;
- `tests/validation/syntax_contracts.py` — shell syntax checks;
- `tests/evidence/*` — focused one-to-one executable evidence.

Keep the top-level validator as an aggregator. New substantial validation belongs in the narrowest existing module or a focused evidence runner rather than expanding the entrypoint back into a monolith.

`scripts/repository_preflight.py` 先跑快速文件／schema／diff 檢查；通過後才進入完整 lifecycle。環境缺少 localhost bind 或 browser 時回報 `ENVIRONMENT_BLOCKED`，不混稱產品測試失敗。



## Deterministic Scheduler / Integration Gate consistency

When deterministic scheduling or merge-candidate validation changes, review together:

- `orchestration/DETERMINISTIC_SCHEDULER.md` + `scripts/deterministic_scheduler.py`;
- `orchestration/INTEGRATION_GATE.md` + `scripts/integration_gate.py`;
- Task Graph / Validation Profile / Integration Gate Report contracts;
- Execution Isolation single-writer behavior and Run Resume semantics;
- Core Change Test Matrix reuse and exact-candidate fingerprinting;
- `bin/aips` scheduler / integration-gate / janitor routing;
- `.github/workflows/validate.yml` required `repository` aggregate compatibility;
- Scenario 135–136 lifecycle evidence and coverage registry;
- Human Architecture Overview / User Guide / Technology Guide.

Large/Core candidate 使用唯一 canonical `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`；版本化矩陣可保留作歷史，但不能取代 CI 實際讀取路徑。

Do not let the Scheduler make semantic scope decisions, and do not let Integration Gate PASS create merge/release authority.

## Branch lifecycle hygiene

Use `config/branch-lifecycle.yaml` and `scripts/branch_hygiene.py` before cleanup. Persistent operational branches are preserved; ephemeral branches become deletion candidates only after deterministic integration into `main`; unclassified branches are preserved by default. Integration recognition is conservative and squash-aware: direct ancestry is checked first, then per-commit patch equivalence, then a clean synthetic `git merge-tree --write-tree` whose result must be identical to the target tree. This catches multi-commit branches that were squash-merged without granting deletion authority. The policy is `report_only`: branch deletion remains an explicit maintenance action outside this classifier. In CI, `.github/workflows/branch-hygiene.yml` performs a full remote-ref fetch and runs `scripts/branch_hygiene.py --remote origin`, so scheduled/manual reports inspect the repository branch set rather than only the checkout's local branch. The workflow has `contents: read` only and publishes candidates to the GitHub Job Summary; it never deletes or rewrites refs.

## Repository Health / Architecture Drift consistency

Repository-wide architecture consistency is checked by scripts/repository_health.py using config/repository-health.yaml. The detailed contract is orchestration/REPOSITORY_HEALTH.md.

It reuses the Capability Map, Scenario Conformance and Integration Gate. The explicit major-subsystem inventory lives in config/architecture-surfaces.yaml and must account for every Capability Map entry exactly once. Review inventory required paths, canonical docs, validation bindings, bounded guard/gate discovery, tests/scenario_coverage.yaml evidence, and .github/workflows/validate.yml plus config/integration-gate.yaml wiring.

Run:

    python scripts/repository_health.py audit --config config/repository-health.yaml

PASS is consistency evidence only. Repository Health is Detect + Evidence + Human Review and has no automatic remediation, code-change, PR, merge, release or publication authority. Review evidence_binding together with the sorted input manifest: clean Git must report EXACT_REVISION/revision_reproducible=true; staged, unstaged or untracked state must report DIRTY_WORKTREE/revision_reproducible=false rather than pretending the current HEAD fully reproduces the audit. CI additionally uploads repository-health-report.json as exact-candidate evidence; this artifact is observational only and grants no authority.


## Repository Health 定期維護觀測

`.github/workflows/repository-health.yml` 會每週定期執行一次 Repository Health，亦支援手動 `workflow_dispatch`。執行時只讀取目前預設分支的精確 revision，產生 `repository-health-report.json`、上傳短期 GitHub Actions artifact，並把摘要寫入 Job Summary。

- PASS：只留下觀測證據，不建立 Issue。
- DRIFT_DETECTED：依 deterministic evidence fingerprint 去重；同一 fingerprint 最多保留一個 open drift Issue，之後讓 workflow 明確失敗以顯示需要 Human review。
- Workflow 只使用 GitHub 自身控制平面發布 artifact／Issue；Repository Health detector 本身仍不需要 `OPENAI_API_KEY`、`GEMINI_API_KEY` 或其他外部 Agent/provider credential。
- 此流程沒有 `contents: write`，不會自動修改程式碼、建立 implementation PR、merge、release 或自動修復 drift。

這個排程是 maintenance observation，不是新的治理 authority。正式變更仍走既有 System Self-Improvement、validation、PR、merge 與 release 流程。


## Evolution Effectiveness monthly maintenance

`.github/workflows/evolution-effectiveness.yml` runs monthly on day 2 after the normal monthly Radar review. It reads durable Radar Issues/comments and writes a bounded `Evolution Effectiveness [monthly] YYYY-MM` Issue.

- no review flags → the metrics Issue is reconciled and closed as completed;
- one or more deterministic review flags → the metrics Issue stays/reopens for Human review;
- the workflow uses only `contents: read` and `issues: write`;
- no external Agent/provider credential is required;
- no source weight, enable/disable state, source URL or repository config is changed automatically.

This is observational maintenance evidence. Any actual source-policy adjustment remains a normal reviewed repository change.


## Controlled branch cleanup

一般 Branch Hygiene 仍是 `report_only`。只有在 repository maintainer 明確批准的 one-time manifest 中，AIPS 才可刪除 remote branch。

`config/branch-cleanup-manifest.yaml` 會逐筆綁定 branch name、exact expected SHA 與 merged PR evidence。Protected-main cleanup job 在刪除前會重新驗證：

- branch 仍存在且 SHA 沒有漂移；
- lifecycle 是 `EPHEMERAL`；
- branch 已由 local Git integration proof，或 GitHub merged PR 的 exact head SHA/ref/base 證據，確認整合進 `main`；
- manifest authorization 是 `explicit_user_request + exact_manifest_only + one_time`。

若使用 GitHub merged-PR fallback，workflow 會重新讀取該 PR，確認 `merged_at`、head SHA、head ref 與 base ref 全部符合 manifest。任何一筆失敗都會在第一個 delete 前 block 整批。Persistent、unclassified、pending 或 manifest 外 branch 一律不刪。Scheduled/manual hygiene report 仍只有 `contents: read`；只有 protected-main cleanup job 在這份 exact manifest 範圍內取得 `contents: write`。
## Runtime Content Safety Boundary

Register every new persistence or publication sink in `config/content-safety.yaml`. Preserve the `sanitize → hash → persist` ordering for audit data and update scenarios when detector or sink policy behavior changes.

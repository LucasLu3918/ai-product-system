# 文件導覽

Runtime Context 行為契約位於 `orchestration/RUNTIME_CONTEXT.md`，範例輸出位於 `templates/runtime/RUNTIME_CONTEXT.yaml`；人類閱讀入口是架構總覽與 Technology Guide。

Retrieval internals and their compatibility facade are explained in ARCHITECTURE_OVERVIEW.md and PROJECT_INTELLIGENCE.md; lexical relations remain rebuildable candidates rather than canonical architecture facts.

Evolution's stable CLI and deterministic pre-analysis module are described in ARCHITECTURE_OVERVIEW.md and EVOLUTION_RADAR.md; the module split adds no install step.

Human Docs 依使用目的組織，而不是依版本號堆疊。

## Official Docs Site

文件開發工具的安全版本、限定覆寫與本機伺服器操作見 [Technology Guide](TECHNOLOGY_GUIDE.md#documentation-platform)；相依套件與鎖定檔變更的同步要求見 [Documentation Consistency](DOCUMENTATION_SYNC.md#official-docs-site)。

The docs-site workflow uses pinned setup-node v7 and upload-pages-artifact v5 on GitHub-hosted Ubuntu 24.04. Action upgrades include architecture, technology and documentation-sync updates; dependency PRs are subject to the same documentation closure as manual changes.

docs/human/ 是 canonical Human source，也是 VitePress site root。首頁為 index.md，網站提供 sidebar、local search 與 page outline。

Site build 永遠可由 CI 驗證；GitHub Pages 尚未在 repository 啟用時，deployment 會以 `SKIPPED_NOT_CONFIGURED` 誠實略過。啟用 Source = GitHub Actions 後，main push 會自動部署同一份 build artifact。Legacy `TECHNOLOGY_GUIDE.html` / `EVOLUTION_RADAR_OVERVIEW.html` 只保留舊連結相容，不再作為新增內容的 canonical target。

安裝與 CI gate 的 current behavior 會同步反映在 Getting Started、Installation、User Guide、Architecture 與 Technology Guide 的指定 topic sections。

## 文件角色

Git 發布模式與操作步驟以 [User Guide](./USER_GUIDE.md#git-publication-與-release) 為入口；安全保證、信任根部署與隔離限制以 [Security Assurance](./SECURITY_ASSURANCE.md#runtime-policy-enforcement) 為準。個人模式 PR merge 的逐次確認依賴 Claude Code 原生 `ask` 或啟用中的 Gemini AIPS extension `ask_user` policy；Codex 仍為 advisory。


The recursive impact report links source changes to required Human and Agent documents.


創作驗證分別記錄命令盤點、合成 tool/provider 測試、native host 驗證及真實模型推論。未提供權重時，品質／設備效能維持未驗證，不以流程通過推定改善成效。

新增的 `project_intelligence_promotion.py` 對應 Project Intelligence 文件；`repository_governance_snapshot.py` 對應 Security Assurance、Technology Guide 與 Scenario 209。

Prospective `aips docs impact --base HEAD --planned-path <path>` resolves sync and placement closure to a fixed point. Each triggered rule requires an update in its canonical topic; combined changes use the union of those topics. Validate every text anchor before applying the batch. Closure is scope evidence and never grants publication authority.

Publication preflight 保留 `scripts/publish_preflight.py` CLI facade；post-merge reconciliation 位於 `scripts/publish_post_merge.py`，由 Scenario 165 lifecycle evidence 驗證。

Project Intelligence 的 temporal query 維持原有 CLI 與 `project_intelligence.py` facade；內部 adapter 位於 `scripts/project_intelligence_temporal.py`，相容性由 Scenario 204 驗證。

Current behavior follows the topic sections in this map: installation and release, maintenance validation, Project Intelligence, Evolution, and security each point to one Human-facing explanation and its canonical Agent protocol.

Quality and validation governance is configured by `config/quality-ratchet.yaml`, `config/validation-graduation.yaml`, and `config/maintenance-reliability.yaml`; its human-facing behavior is summarized in Maintenance and the Technology Guide. Scenario 228 records progressive quality ratchet evidence in Conformance.

Exact-candidate browser toolchain selection is documented in Maintenance and Technology Guide; `tests/evidence/validator_registry_lifecycle.py` verifies the central validator registry and its fail-closed full-profile default.

`config/system-facts.yaml` 是 runtime、命令與 CI 相容性版本的 canonical facts；`scripts/system_facts.py` 產生 System Reference 的事實表格。安裝操作維護於 Installation，CI 與維護流程維護於 Maintenance，技術背景與限制維護於 Technology Guide；Scenario evidence 以 Conformance 為準。

GitHub branch cleanup、version-tag provenance 與 ruleset review 的 Human 指引位於 `MAINTENANCE.md`；Agent-facing read-only ruleset contract 位於 `orchestration/GITHUB_RULESET_POLICY.md`。

### 開始使用

- GETTING_STARTED.md：最短成功路徑。
- INSTALLATION.md：Install / Update / Uninstall。
- USER_GUIDE.md：目前產品使用方式。

### Agent 整合與核心概念

- HARNESS.md：native adapters + MCP。
- PROJECT_INTELLIGENCE.md：Project understanding / retrieval。
- SECURITY_ASSURANCE.md：SAL / security evidence。

Change Impact unknown dispositions are defined in the Project Intelligence Human topic and the canonical Agent protocol; Scenario Conformance records their lifecycle and rejection evidence.

Runtime action authorization is canonical in `config/runtime-policy.yaml`, `orchestration/schemas/runtime-action.yaml`, `scripts/runtime_policy.py` and `orchestration/RUNTIME_POLICY_ENFORCEMENT.md`; adapter limits and Scenario 177 evidence are documented in Harness, Security Assurance and Conformance.

Secret handling guidance covers the built-in mandatory publication-candidate scan in the existing Git Publication and Security Assurance topics. Provider scanners are optional defense-in-depth, not baseline dependencies.

GitHub API transfer integrity is documented in User Guide 的 Git Publication、Maintenance 的 CI consistency 及 Technology Guide 的驗證說明；`scripts/publication_transfer.py` 是 deterministic implementation，文件範圍由 `publication-transfer` placement rule 維護。

### 架構與技術

- ARCHITECTURE_OVERVIEW.md：目前 architecture。
- TECHNOLOGY_GUIDE.md：目前 technical choices。
- EVOLUTION_RADAR.md / EVOLUTION_RADAR_OVERVIEW.md：maintenance plane。

### Reference / Maintainers

- CONFORMANCE.md：Scenario / verification history。
- MAINTENANCE.md：system maintainer workflow。
- assets/maintenance-governance-overview.svg：Evolution、驗證影子計畫、branch、版本與 GitHub policy 的 Human review 邊界。
- Monthly maintenance reliability uses `scripts/maintenance_reliability.py` and `.github/workflows/maintenance-reliability.yml`; maintainer instructions are in MAINTENANCE.md and behavior evidence is Scenario 201 in CONFORMANCE.md.
- Workflow execution profiles are maintained in MAINTENANCE.md and TECHNOLOGY_GUIDE.md; `tests/evidence/python_bootstrap_action_lifecycle.py` verifies bootstrap, timeout rationale and evidence-preserving concurrency.
- DOCUMENTATION_SYNC.md：文件 consistency / placement contract。
- SYSTEM_REFERENCE.md：由已驗證 system facts registry 衍生的 command、capability、platform 與 runtime 表格。

## Agent / machine canonical 文件


Reusable task methods are canonical in `skills/<domain>/<skill>/SKILL.md`, with discoverability metadata in `skills/INDEX.yaml`. Scenario behavior is canonical in `tests/scenario_coverage.yaml` and `tests/scenarios/`; domain/platform reference notes live under `references/`.

OpenCode continues to use its existing signed-publication route for protected operations; per-call personal PR merge confirmation is implemented only by Claude Code and the active Gemini AIPS extension.

個人與高保證發布模式的機器執行規則位於 `scripts/publication_authority.py`、`scripts/governance_guard.py` 與 `orchestration/ORCHESTRATOR.md`；proposal 由 `templates/git-publish-proposal.md` 保留候選證據。


Publication canonical implementation 是 `scripts/governance_guard.py`、`publication_authority.py`、`publication_commands.py`；`publication_issuer.py` 僅供外部管理域部署。Human 接入指引位於 Security Assurance / Runtime Policy Enforcement，避免複製 signing policy。

Agent 任務 bench 重用 `tests/scenario_coverage.yaml` 與既有 Case；`templates/conformance/AGENT_TASK_BENCHMARK.yaml` 提供 Coding／Creative／Planning／Security 工作入口，結果使用既有 Result 範本，沒有第二份 Scenario Registry。

The candidate command and its review boundary are routed through canonical Project Intelligence guidance and its registered conformance evidence.

Creative prompt compiler、model capability evidence 與本機 vision advisory 的行為由 Creative Direction 和 Scenario 234/236/238 定義；Human 導覽與文件閉包由本圖及 Documentation Sync 維護。

Compiler implementation is maintained in `scripts/creative_prompt_compiler.py`; the stable `creative_execution` facade and exact-output evidence are described in Architecture Overview and Technology Guide.

Creative authorization and recovery behavior is canonical in `orchestration/CREATIVE_DIRECTION.md` and `harness/adapters/opencode/AGENTS.md`; user guidance is synchronized through the reusable character-artwork topics and Scenario 238.

Behavior-bearing modules, schemas and scenarios remain the source references for detailed execution and evidence contracts.


Creative authorization and multi-item execution are specified in `orchestration/CREATIVE_DIRECTION.md`, implemented by the OpenCode adapter and shared executor, and covered by Scenario 238; the Human usage entry is in User Guide.

Creative engine discovery and staged readiness are sourced from `scripts/creative_execution.py`; it checks installed MFLUX commands and the fixed loopback ComfyUI API without claiming model inference.

Project Diagnostics 的 Agent-facing read-only 與 UNVERIFIED 邊界保留在 `orchestration/PROJECT_INTELLIGENCE.md`、`harness/HARNESS_PROTOCOL.md` 與 OpenCode Adapter 指示中。

Z-Image Turbo generate 的 MFLUX 命令映射與固定 ComfyUI split-loader profile 真實來源是 `scripts/creative_execution.py` 和 `templates/creative/COMFYUI_Z_IMAGE_TURBO_API.json`；本機產圖與人工審查流程由 `orchestration/CREATIVE_DIRECTION.md` 說明。

角色圖片保留要求的媒材；以受限 configure 建立新的 Bundle，並載入校準、方向與視覺審查 skill。執行、圖片容器、人工審查與使用者接受分開回報。

創作可靠性 Core candidate 保留完整 Gate、媒材拒絕及取消授權回歸。損壞 PNG fixture 必須失敗；合成測試不能替代真實模型與人工品質驗收。

OpenCode adapter 的 runtime contract 與原生 acceptance 位於 [Harness 說明](HARNESS.md) 及 `harness/adapters/opencode/COMPATIBILITY.md`；治理仍保留 Shell/MCP 未覆蓋邊界。

OpenCode V2 adapter behavior is defined by `harness/adapters/opencode/AGENTS.md`, `COMPATIBILITY.md`, and `plugin.ts`; user-facing setup and capability limits are summarized in the Harness guide.

The character-art workflow is canonical in `orchestration/CREATIVE_DIRECTION.md`, the three existing design Skills, `scripts/character_artifacts.py`, the Creative Bundle executor/templates and Scenarios 234/236. User workflow and technical limits are described in USER_GUIDE.md and TECHNOLOGY_GUIDE.md; no duplicate Skill or provider integration surface is introduced.

Versioned creative preparation and fixed MFLUX operation mapping are documented in the User Guide and Technology Guide; the OpenCode tool boundary is recorded in Harness and `harness/adapters/opencode/COMPATIBILITY.md`.

OpenCode 的 managed 指示來源為 `harness/adapters/opencode/AGENTS.md`；原生驗證範圍見 [Harness](HARNESS.md)，canonical 紀錄為 `harness/adapters/opencode/COMPATIBILITY.md`。Skills 與 Commands 仍以原有 canonical registry 為準。

Runtime hook input and resolver failure contracts are canonical in the Harness protocol; user-facing behavior and recovery guidance live in HARNESS.md, SECURITY_ASSURANCE.md and INSTALLATION.md.

`SYSTEM_CORE.md` 是固定載入的精簡 AIPS 核心；`SYSTEM.md` 保留相容入口，任務所需協定由 Turn Context 指向 `orchestration/` 中的 canonical 文件。

主要模型與辅助路由規則見 `../../orchestration/MODEL_ROUTING.md`；Skill registry 維護見 `TECHNOLOGY_GUIDE.md`，可觀測覆蓋見 `CONFORMANCE.md`。

Pull-request validation policy and the advisory fast-feedback boundary are documented in [Maintenance](MAINTENANCE.md#validation-architecture-consistency) and [Scenario Conformance](CONFORMANCE.md#scenario-220--parallel-advisory-fast-feedback).


The generated System Reference records the runtime architecture inventory, including the public `bin/aips` launcher, its `scripts/aips_cli.sh` facade and the source modules under `scripts/aips_cli/`. Keep this inventory aligned with the implementation and its lifecycle validation.

REST/OpenAPI implementation evidence is specified by `orchestration/IMPLEMENTATION_RESOLUTION.md`, `scripts/openapi_contracts.py` and `templates/implementation/OPENAPI_EVIDENCE_REPORT.schema.json`; Human workflow guidance lives in `docs/human/USER_GUIDE.md` and Scenario 194.

Phase 3 deterministic enforcement is specified by the same Implementation Resolution and Integration Gate protocols, `scripts/implementation_enforcement.py` and `templates/implementation/IMPLEMENTATION_ENFORCEMENT_REPORT.schema.json`; Human workflow, security and conformance guidance lives in the User Guide, Security Assurance and Scenario 195.

`orchestration/IMPLEMENTATION_RESOLUTION.md` 定義實作解析流程；Profile 範本與 Go、PHP、Python、.NET 語言基線分別位於 `templates/implementation/` 和 `references/languages/`。

Phase 4 OpenAPI client generator 的 canonical contract 位於 `scripts/openapi_generator_adapter.py`、`templates/implementation/GENERATOR_ADAPTER_REPORT.schema.json` 與 Integration Gate lifecycle fixture。預覽不執行工具；只有明確的本機 `--execute` 會呼叫 Profile 固定的 generator。Scenario 196 維護其輸出 ownership、rollback 與安全邊界證據。

Phase 5 的可選執行報告核對位於 `scripts/implementation_enforcement.py` 與 Profile 範本；單一共用範例在 `examples/openapi-client-pilot/`，其中 `AI_ONBOARDING.md` 提供可依序執行的真實產品導入檢查表。Scenario 197 與 lifecycle 測試驗證其本機 API/client 流程；產品專屬證據由產品 repository 保存。

Task ownership 的 canonical contract 分布於 `orchestration/DETERMINISTIC_SCHEDULER.md`、`orchestration/RESOURCE_AUTHORIZATION.md`、`orchestration/RUN_DASHBOARD.md`、`orchestration/schemas/run-task-state.yaml` 與 Task Graph 範本；`config/documentation-placement.yaml` 維護對應 Human 文件閉包。

`orchestration/TELEMETRY_EXPORT.md` 與 `orchestration/schemas/telemetry-export.yaml` 定義 optional OpenTelemetry trace projection、欄位 allowlist、端點與降級行為；Human 操作說明由 User Guide、Technology Guide 與 Telemetry Export topic 提供。

`orchestration/EVAL_INTEROPERABILITY.md` 是外部 Promptfoo / PyRIT evidence 邊界、支援 subset、CLI、驗證與 Human finding promotion 的 machine canonical 文件。

Content safety 的 machine canonical 文件為 `config/content-safety.yaml`、`scripts/content_safety.py` 與 `orchestration/CONTENT_SAFETY_BOUNDARY.md`；Human-facing placement 由本專案的 documentation placement contract 維護。

`orchestration/TRAJECTORY_EVAL.md`、`templates/review/TRAJECTORY_TRACE.yaml` 與 `templates/review/TRAJECTORY_EVIDENCE.yaml` 是 Eval-as-CI trajectory contract 的 canonical machine-facing 文件。

Independent review isolation is defined across `orchestration/MULTI_REVIEW.md`, `orchestration/DETERMINISTIC_SCHEDULER.md`, `orchestration/INTEGRATION_GATE.md`, `orchestration/schemas/task-graph.yaml`, `orchestration/schemas/context-manifest.yaml`, `scripts/review_packet.py` and `scripts/review_evidence.py`. Human guidance lives in the User Guide, Technology Guide and Security Assurance. The mechanism is implemented but PR enforcement is currently disabled in the active Core Change Matrix; the placement rule keeps these surfaces synchronized.

Turn Context intent and scoped instruction selection are implemented in `scripts/turn_intent.py` and `scripts/project_intelligence.py`; event serialization and observed stage recording use `scripts/run_event_stream.py` and `scripts/observed_stage.py`. Eval freshness and externally trusted review receipts are defined by `scripts/agent_eval.py`, `scripts/review_attestation.py` and the validation dependency lock.

`orchestration/REQUIREMENT_CLARIFICATION.md` 和 `orchestration/PLANNING_PACKAGE.md` 定義需求澄清與規劃規則；`templates/planning-package/` 保存規劃 artifact 契約，`PLANNING_MANIFEST.yaml` 與 `scripts/planning_package_validate.py` 驗證 package graph、穩定 ID、跨 artifact 追溯與人工關卡證據。`PRODUCT_RESEARCH.md`、`DOMAIN_MODEL.md` 支援可執行規劃；`references/domains/INDEX.yaml` 指向按需載入的電商 reference pack。`REQUIREMENTS.yaml` 與 `scripts/requirements_traceability.py` 維護需求追溯結構。CLI 提供 JSON PASS/FAIL 與相應退出碼；語義判讀仍由既有角色負責。

Publication routing and validation contracts live in `orchestration/INTEGRATION_GATE.md`, `scripts/publish_preflight.py` and `scripts/repository_preflight.py`; Human workflows remain in User Guide and Maintenance. Scenario 165 in the shared registry maps their executable evidence.

Risk-adaptive Change Impact 的 Human 說明位於 `PROJECT_INTELLIGENCE.md` 的 Change Impact topic；風險政策、命令、證據與 READY 契約以 `orchestration/CHANGE_IMPACT.md` 為 Agent canonical source。Scenario 175 維護 traversal lifecycle coverage。

Structured unknown dispositions extend that same contract: repository-file evidence is hash-bound, traversal evidence is scope-bound, legacy unknown strings remain unresolved, and closure requires explicit Human review. Scenario 179 records the lifecycle evidence.

Agent 由 AGENTS.md / SYSTEM.md 進入，按需讀取 orchestration/、roles/、skills/。Official Docs Site 不複製這些 protocol 成第二份 Human source。

CLI entry-point and publication-preflight modularization map to this document, Architecture Overview, Maintenance, Technology Guide, User Guide, Conformance, Security Assurance, and the relevant orchestration contracts.

- Release-tag provenance policy is canonical in `config/version-tag-policy.yaml` and `orchestration/RELEASE_READINESS.md`; Scenario 208 defines its evidence contract.

Retrieval SQLite storage helpers are implemented in `scripts/retrieval_storage.py` and remain re-exported through the `scripts/retrieval_intelligence.py` facade. The existing Project Intelligence documentation closure covers both source modules.

## Shared canonical 文件

Human-facing runtime, diagnostics and governance guidance follows canonical topic placement.


Project Diagnostics 的操作與恢復流程以 [Project Intelligence](PROJECT_INTELLIGENCE.md) 為 Human canonical 文件；公開命令清單維持在 [System Reference](SYSTEM_REFERENCE.md)。

The reusable Python CI bootstrap contract lives with its composite action; per-workflow import profiles live in the caller, and package versions remain in requirements and constraints.

Shared deterministic JSON/hash, path and glob primitives are canonical in `scripts/aips_common/`; existing modules retain compatibility facades. Domain-owned governance fingerprints and runtime action digests remain outside this shared layer.

docs/ARCHITECTURE.md 可作 machine/human shared architecture artifact；CHANGELOG.md 是 release history。

`config/system-facts.yaml` 是公開命令與 runtime support 的 machine-readable source；`scripts/system_facts.py` 只產生 `SYSTEM_REFERENCE.md` 的事實表格，不生成 policy prose。Architecture Surface Inventory 維護 subsystem capability、canonical docs 和 validation bindings。


## 文件一致性

新拆出的四個 helper 與 Creative quality 摘要沿用既有 Facade 的 Placement／Sync 主題；Document Size Audit 的 reading_sections 僅導向原 H2，不生成第二份 Canonical Policy。

Project Intelligence relationship candidates are documented in the Project Intelligence and Architecture Overview sections; their scenario evidence is indexed in Conformance.

Runtime, diagnostics, creative provenance, CI planning, telemetry and governance changes follow the recursive Documentation Impact Gate. Its closure size is a review metric; it does not by itself authorize removing canonical placements.

本機創作設定與交付狀態由 Creative Direction、OpenCode compatibility 與 Scenario 236 共同描述；User Guide 提供操作順序。合成測試、本機命令可用與真實圖片驗收是不同證據。


Evolution Radar 人工相關性抽樣與評估行為以 `EVOLUTION_RADAR.md` / `EVOLUTION_RADAR_OVERVIEW.md` 為 Human 說明，`orchestration/CONFORMANCE.md` 與 Scenario 218 定義 Agent 驗證契約；placement 登錄於 `config/documentation-placement.yaml`。同月份 Issue reconciliation 的非取消排隊契約由 Scenario 207 lifecycle 驗證。

Dependency Update risk classification 的使用方式位於 Maintenance 與 Technology Guide；Agent 契約由 Scenario 221 定義，placement 登錄於 `config/documentation-placement.yaml`。

Release history keeps Unreleased and the latest five full releases in CHANGELOG.md; older complete sections live in docs/history/changelog/ while every version heading remains at the root as a stable link. Finalized notes move under the heading matching VERSION before readiness; a version heading alone does not prove a stable tag exists. The report-only size audit remains WARN-only and never moves files; archive placement is a manual, lossless documentation decision. For Plan26 Phase 7, `VERSION` and the newest heading are `0.81.0`; the PR only finalizes metadata and does not publish a tag or release.

Plan21 pre-hardening compatibility evidence is owned by `.aips/review/PLAN21_VALIDATION_TIMING_BASELINE.yaml` and `tests/evidence/plan21_contract_baseline.py`; the fixture and runner pin test contracts without becoming a runtime policy source.

`tests/validate_repository.py` documents the required CI evidence boundary: exact-candidate selection may skip optional OpenAPI lifecycle checks, while the required repository aggregate and Integration Gate continue to run. The selection variable is consumed by the runner and kept out of isolated lifecycle subprocesses.

The same exact-candidate plan controls browser-dependent visual and creative render validators. Keep the `needs_browser` decision, fail-closed full-profile default, explicit skipped timing evidence, and mandatory repository aggregate synchronized with the validator registry lifecycle.

執行環境恢復的操作說明分別由 Installation、Project Intelligence 與 Maintenance 承載；Technology Guide 提供共用工具位置，來源對應由既有 canonical placement 規則約束。

`config/documentation-placement.yaml` 登記 behavior-bearing source 與 canonical Human 文件落點。Required-files parity pilot 的實作說明位於 Maintenance 與 Technology Guide；架構導覽及規則變更說明位於 Architecture Overview 與 Documentation Sync。

VitePress renders the canonical Markdown files directly; local publication preflight uses the installed bundle and does not create or install a second documentation source.

文件位置契約的工作樹預覽與已提交候選檢查使用相同 canonical H2 規則；前者讓維護者在提交前修正段落，後者作為 CI 前置驗證證據。

文件影響以 `aips docs impact` 顯示的 trigger 與遞迴閉包為準；EARS validator 契約由 Scenario Conformance 維護，需求規劃功能則由 Requirement Planning 維護。

Publication Preflight preview displays the recursive documentation closure and the rule responsible for each required document; canonical Human and Agent guidance remains in its existing topic sections.

The read-only Parallel Run Dashboard is mapped across its implementation, orchestration and Human guidance documents; the projection remains observational and does not create a second authority surface.

Portable Command 行為變更需同步 Harness、Architecture Overview、Technology Guide、Installation／Getting Started 與維護文件的既有 topic；不得以生成 projection 取代 canonical documentation。
`harness/commands/REGISTRY.yaml` 定義 Portable Command ID、Host renderer 與 authority boundary；`harness/PORTABLE_COMMANDS.md` 是其人類可讀說明。
Workflow and integration-gate behavior is documented in the canonical Human guides and corresponding orchestration documents. Generated CI reports remain artifacts and are not treated as source documentation.

Behavior-bearing change 先由 Documentation Sync 判斷 required docs，再由 Documentation Placement 驗證 current-behavior 內容更新在 canonical section，而不是附加在尾端。任何落在 Technology Guide 廣域 trigger surface、但尚未映射到 placement rule 的新 source 會直接 fail closed；maintainer 必須先決定它屬於既有 topic，或明確新增新的 canonical topic。

Publication Preflight 由 Maintenance、User Guide、Architecture Overview 與 Technology Guide 的既有 CI／execution topics 說明；`bin/aips` 的發布指令落在 User Guide 的 Git Publication topic，而安裝文件只由 installer/bootstrap source 觸發。Agent contract 位於 Integration Gate、Core Change Testing 與 Orchestrator，不建立平行文件樹。

Publication Preflight 也管理 candidate head/base、changed-files hash、documentation closure 與 browser smoke probe；視覺證據優先使用 Playwright managed Chromium，系統 Chrome 啟動失敗歸類為環境阻擋。

Node documentation dependencies are locked by `package-lock.json` and installed with `npm ci` in validation and docs-site workflows. The publication plan reports the GitHub repository's enabled merge methods alongside its existing branch-protection and access diagnostics.

`orchestration/CONFORMANCE.md` 的 Runtime／MCP Scenario 行為由 harness placement rule 管理；變更時同步既有 Harness、Runtime Architecture 與 Runtime Technology 主題，不建立第二套 current-behavior 分類。

Temporal Project Intelligence 的 Human 說明由 `PROJECT_INTELLIGENCE.md` 負責；其 current/as-of/between/why 查詢、Git revision provenance、validity interval 與 supersession 語義，必須與 Agent protocol、Technology Guide 及 Conformance evidence 一起維護。

Execution Isolation provider changes map to Architecture Overview and Security Assurance, with usage in User Guide, optional dependency and runtime details in Technology Guide, verification history in Conformance, and canonical behavior in `orchestration/EXECUTION_ISOLATION.md` / `orchestration/ORCHESTRATOR.md`. The E2B registry stays disabled until source-transfer scope and adapter readiness are explicitly resolved.

**Plan19 architecture and runtime closure.**

Plan19 machine-readable authorities are `config/capability-registry.yaml` and `config/eval-freshness.yaml`; generated compatibility views are `config/architecture-surfaces.yaml` and `references/evolution/CAPABILITY_MAP.yaml`. Branch and monthly effectiveness evidence lives under `.aips/review/` and remains report-only.

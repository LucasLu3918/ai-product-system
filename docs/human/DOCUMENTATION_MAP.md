# 文件導覽

Runtime Context 行為契約位於 `orchestration/RUNTIME_CONTEXT.md`，範例輸出位於 `templates/runtime/RUNTIME_CONTEXT.yaml`；人類閱讀入口是架構總覽與 Technology Guide。

Retrieval internals and their compatibility facade are explained in ARCHITECTURE_OVERVIEW.md and PROJECT_INTELLIGENCE.md; lexical relations remain rebuildable candidates rather than canonical architecture facts.

Evolution's stable CLI and deterministic pre-analysis module are described in ARCHITECTURE_OVERVIEW.md and EVOLUTION_RADAR.md; the module split adds no install step.

Human Docs 依使用目的組織，而不是依版本號堆疊。

## Official Docs Site

官方文件網站面向使用者與維護者，操作說明以繁體中文為主。架構、Runtime、工具與狀態等專有名詞在首次出現時補上英文；命令、程式識別字、設定欄位和原因碼維持原文，方便直接比對。首頁依讀者目標提供安裝、使用、整合與維護入口；網站中的架構圖和流程圖必須對照目前程式、設定與 canonical 文件維護。

文件開發工具的安全版本、限定覆寫與本機伺服器操作見 [Technology Guide](TECHNOLOGY_GUIDE.md#documentation-platform)；相依套件與鎖定檔變更的同步要求見 [Documentation Consistency](DOCUMENTATION_SYNC.md#official-docs-site)。

The docs-site workflow uses pinned setup-node v7 and upload-pages-artifact v5 on GitHub-hosted Ubuntu 24.04. Action upgrades include architecture, technology and documentation-sync updates; dependency PRs are subject to the same documentation closure as manual changes.

docs/human/ 是 canonical Human source，也是 VitePress site root。首頁為 index.md，網站提供 sidebar、local search 與 page outline。

Site build 永遠可由 CI 驗證；GitHub Pages 尚未在 repository 啟用時，deployment 會以 `SKIPPED_NOT_CONFIGURED` 誠實略過。啟用 Source = GitHub Actions 後，main push 會自動部署同一份 build artifact。Legacy `TECHNOLOGY_GUIDE.html` / `EVOLUTION_RADAR_OVERVIEW.html` 只保留舊連結相容，不再作為新增內容的 canonical target。

安裝與 CI gate 的 current behavior 會同步反映在 Getting Started、Installation、User Guide、Architecture 與 Technology Guide 的指定 topic sections。

## 文件角色

Creative workflow 的新增 FLUX 3 Klein schema／payload 相容性證據位於 User Guide、Technology Guide 與 Scenario 236；Scenario 234/236 的角色創作流程沒有因此改變。

Model-agnostic ComfyUI workflow usage belongs in the User Guide, implementation and security limits in Technology Guide and Security Assurance, with Scenario 268 as the synthetic evidence anchor. Fixed FLUX 3 Klein `TextGenerate` runtime-schema and final-payload checks are documented in those same topics and Scenario 236; they prove interface compatibility, not MPS inference.

ComfyUI model profile registry 的 canonical 行為來源為 `scripts/creative_execution.py` 與 `templates/creative/COMFYUI_MODEL_PROFILES.yaml`。

Scenario 267 changes no Skill discovery, installation or upstream trust behavior; it is a separate runtime guard contract.


Matt Pocock upstream Skill 的清單與安裝處置由 pinned manifest 和 canonical registry 管理；Plan44 不增加上游 Skill 項目或改變預設路由。

Claude Code publication 的操作步驟位於 User Guide，安裝相容資訊位於 Installation，Agent 契約則位於 Harness adapter 文件。

Creative asset import uses the existing Creative Direction and Harness command surfaces; it does not add a Skill catalog entry or alter Skill Explorer behavior.


Plan41 的 commit 安全診斷由既有 Content Safety kernel、`governance_guard.py` 與唯讀 `safety_diagnostics.py` 共用實作；Human 操作與安全邊界由 User Guide、Security Assurance、Harness 及 Scenario 263 說明。
Plan47 的 injection rule、staged-line 範圍、例外與安全 recovery 仍由同一 scanner 實作；canonical boundary 在 `orchestration/CONTENT_SAFETY_BOUNDARY.md`，Scenario 266 記錄分類與完整密鑰掃描不變式。

Publication root-cause diagnostics and the optional Diagnostic ID lookup contract are implemented in the publication authority/planning/diagnostics and governance-audit modules; Human recovery steps live in User Guide, while native adapter and exact scenario boundaries live in Harness and Conformance.

Plan45 secret-scanner failure codes and pre-scan command validation are documented in User Guide, Security Assurance, Architecture Overview and Harness; exact privacy and no-execution behavior is covered by Scenario 261.

Publication Doctor recovery is documented in the User Guide, security authority boundary, Runtime adapter guidance and Scenario 260/261 evidence.

The User Guide remains the Human entry point for publication troubleshooting, while this map preserves canonical Skill Explorer and adapter-document ownership.

Scenario 265 is registered as content-safety evidence and does not change the upstream Skill inventory.

The Human User Guide describes publication recovery and retains the canonical Skill and Harness documentation links.

上游 Skill 安裝／解除安裝的操作流程以 `docs/human/USER_GUIDE.md` 為準；Host discovery 與來源邊界見 `docs/human/HARNESS.md`，維護驗證見本文件的 `Validation architecture consistency` 對應章節與 `docs/human/CONFORMANCE.md` Scenario 259。

上游 Skill 是否可安裝依 canonical ID 是否重複判定；disposition 描述整合背景，不限制使用者安裝。Codex 與 Claude Code 原生投影要求明確呼叫，Gemini 保留啟用前確認。

Resource Authorization 的 Human 操作與安全邊界見 User Guide、Security Assurance；Profile schema、Runtime enforcement、Creative loopback discovery 和 Scenario 262 的 canonical 實作對照見 orchestration references 與 Conformance。

Public CLI commands are documented under the owning user workflow and matching Scenario evidence. A shared dispatcher or Scenario registry does not make unrelated command domains part of that change.

Skill 的使用者搜尋入口是 <a href="./skill-catalog.html">Skill Explorer</a>；49 個 canonical AIPS Skills 與 38 個 vendored 上游來源分開呈現，來源清單固定 commit 並記錄本地路徑與 SHA-256。Skill routing 的 canonical 定義仍在各 `SKILL.md` 與 Registry；Scenario 259 記錄自動路由、實驗／選用與 `$grill-with-docs` 明確呼叫邊界。

Git 發布模式與操作步驟以 [User Guide](./USER_GUIDE.md#git-publication-與-release) 為入口；安全保證、信任根部署與隔離限制以 [Security Assurance](./SECURITY_ASSURANCE.md#runtime-policy-enforcement) 為準。一般個人模式 PR merge 依賴 Claude Code 原生 `ask` 或啟用中的 Gemini AIPS extension `ask_user` policy；明確 task-authorized 的 Claude `--auto` 可由同一候選檢查啟用 GitHub auto-merge，Gemini 仍逐次詢問。Codex 仍為 advisory。


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
- 專案內 AIPS 工作區維持預設停用；`attach`、`detach` 與本機 Git exclude 行為見 [User Guide / Existing Project](USER_GUIDE.md#existing-project)。

### Agent 整合與核心概念

- HARNESS.md：native adapters + MCP。
- Harness 的 Skills 跨 Agent 載入方式、MCP Resource 路徑與保留既有 Skill 的解除安裝規則集中於 [Global Harness](HARNESS.md#在-opencode-以外載入-aips-skills)；安裝入口見 [Installation](INSTALLATION.md)。
- Codex、Claude Code、Gemini CLI 原生 Skill 安裝、Host/scope 所有權與安全卸載流程見 [Installation](INSTALLATION.md) 與 [User Guide](USER_GUIDE.md#global-harness-與-mcp)；技術邊界見 [Technology Guide](TECHNOLOGY_GUIDE.md#quality--verification) 與 [Conformance](CONFORMANCE.md#scenario-233--public-cli-help-and-error-contracts)。canonical 實作位於 `scripts/native_skill_projection.py`，Portable Command 投影由 `scripts/portable_commands.py` 接入。
- PROJECT_INTELLIGENCE.md：Project understanding / retrieval。
- SECURITY_ASSURANCE.md：SAL / security evidence。

Change Impact unknown dispositions are defined in the Project Intelligence Human topic and the canonical Agent protocol; Scenario Conformance records their lifecycle and rejection evidence.

Runtime action authorization is canonical in `config/runtime-policy.yaml`, `orchestration/schemas/runtime-action.yaml`, `scripts/runtime_policy.py` and `orchestration/RUNTIME_POLICY_ENFORCEMENT.md`; adapter limits and Scenario 177 evidence are documented in Harness, Security Assurance and Conformance.

Secret handling guidance covers the built-in mandatory publication-candidate scan in the existing Git Publication and Security Assurance topics. Provider scanners are optional defense-in-depth, not baseline dependencies.

The built-in publication scanner validates `.m4a` container structure and scans metadata without decoding audio payloads; the 8 MiB limit and Git LFS/external-storage remediation are documented in User Guide and Security Assurance.

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


Plan36 publication diagnostics preserve this topic's existing behavior and authority boundaries.

Release history 更新（純依賴升級文件豁免，Scenario 221）已審查本區段：Skill 整合、Explorer 與重用行為不變。

Dependabot repository preflight 與 action 釘選同步（Scenario 221）：`scripts/repository_preflight.py`、文件同步 contracts 與 `scripts/documentation_sync.py` CLI 一律經由 `documentation_sync.evaluate_candidate` 判斷文件同步，與 docs-impact、placement 共用同一個 `pure_dependency_update`；不符合時完整規則照舊。驗證 contracts 不再複製 action commit SHA，改由 `dependency_impact.require_pinned_action` 檢查 action 名稱完全相符、40 碼完整 commit SHA、版本註解不低於已審查下限，以及成對 workflow 使用同一 SHA；evolution 設定改記 `action: openai/codex-action`。新 SHA 是否等於上游 tag 對應的 commit，仍由人工審查確認。

## Agent / machine canonical 文件

The fixed FLUX 3 Klein runtime-schema validator and its lifecycle evidence are maintained with `scripts/creative_execution.py`, `tests/evidence/creative_execution_lifecycle.py`, and Scenario 236; this does not add a character-artwork capability or alter its provenance flow.

Scenario 267 and the active `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` record the READY+STALE native-write policy and its retained denial cases.

Creative raster validation uses the shared AVIF metadata scanner in `scripts/creative_image_validation.py`; its format handling is not a Skill or new capability route.


Unsupported command details and native execution failure evidence use the existing publication and adapter contracts; they add no separate Runtime or Skill source.
Character artwork remains governed by Creative Direction and existing Harness adapters; Plan44 does not add a creative generation or asset-import source.

Claude Code publication guard 的版本門檻與安全診斷由 Harness adapter 文件及安裝指南共同記錄；行為驗收以 Scenario 261 為準。

Creative import command policy is owned by orchestration/CREATIVE_DIRECTION.md; executable evidence is tests/scenarios/264-creative-git-asset-import.md and its registered lifecycle.

Creative asset authorization remains canonical in Creative Direction and adapter protocols; Git publication Diagnostic ID tracing stays in the publication authority/ledger path and is not a creative permission source.

The plan39 source-to-topic mapping is maintained by the `plan39-comfyui-resource-authorization-diagnostics` placement rule and the `plan39-comfyui` documentation-sync entry; Scenario 262 is the verification-history anchor.

Dynamic model-agnostic ComfyUI workflows are implemented by `scripts/comfyui_workflow.py`, `scripts/comfyui_workflow_policy.py`, `scripts/comfyui_capabilities.py` and `scripts/creative_execution.py`. Human usage is in the User Guide, implementation and security boundaries are in the Technology Guide and Security Assurance, and Scenario 268 is the synthetic verification-history anchor; fixed profiles remain the default.

The Claude Code adapter documents one-shot retryable Doctor recovery; the OpenCode adapter retains explicit read-only recovery guidance.

Publication diagnosis is defined by the shared read-only contract, with native adapter behavior and recovery scenarios linked from canonical Human guidance.

Publication root-cause contract is implemented in scripts/publication_authority.py, scripts/publication_diagnostics.py and scripts/publication_planning.py; Claude Code agents consume this contract without creating a second permission gate.

Publication diagnosis is documented in the User Guide and Technology Guide, with runtime-specific instructions in Claude Code, Codex and OpenCode adapters. Scenario 260 records the privacy and authority boundary.

`skills/INDEX.yaml` 與各 `SKILL.md` 是 canonical Agent routing 的來源；`external-skills/matt-pocock/` 保存上游原始內容，並由固定版本清單的 `local_path`、SHA-256 與 disposition 對照。31 個非 canonical 上游 ID 可選擇安裝；七個同名 ID 使用 AIPS canonical。<a href="./skill-catalog.html">Skill Explorer</a> 是由 Registry 和 manifest 產生的 Human 檢索視圖。

Publication prepare/diagnose observations remain read-only and worktree-bound; follow the canonical Git publication procedure in USER_GUIDE.md and preserve native authority, candidate validation and host permissions.

Creative workspace asset import is described in USER_GUIDE.md and governed by orchestration/CREATIVE_DIRECTION.md. Git destinations remain denied unless the CLI candidate explicitly opts into a hash-bound, create-only import.


Cross-profile creative quality evidence is defined by the registered dataset and benchmark template, implemented by `scripts/creative_quality_benchmark.py`, and verified by Scenario 258. Human usage and technical boundaries are described in USER_GUIDE and TECHNOLOGY_GUIDE.

OpenCode host compatibility and unsupported effects: Harness, Installation, Technology Guide, and Scenario 235. Canonical Agent behavior is in harness/adapters/opencode/AGENTS.md and harness/adapters/opencode/COMPATIBILITY.md.

創作修正的 canonical contracts 位於 `scripts/creative_repair.py`、`orchestration/CREATIVE_DIRECTION.md` 與既有 OpenCode adapter；Human 操作入口仍為 USER_GUIDE／TECHNOLOGY_GUIDE，沒有新增全域 Role 或 Skill。


Reusable task methods are canonical in `skills/<domain>/<skill>/SKILL.md`, with discoverability metadata in `skills/INDEX.yaml`. Scenario behavior is canonical in `tests/scenario_coverage.yaml` and `tests/scenarios/`; domain/platform reference notes live under `references/`.

OpenCode continues to use its existing signed-publication route for protected operations; per-call personal PR merge confirmation is implemented only by Claude Code and the active Gemini AIPS extension.

個人與高保證發布模式的機器執行規則位於 `scripts/publication_authority.py`、`scripts/governance_guard.py` 與 `orchestration/ORCHESTRATOR.md`；proposal 由 `templates/git-publish-proposal.md` 保留候選證據。

M4A scanner structure validation is implemented in `scripts/m4a_inspection.py` and consumed by publication preview, `scripts/check_secret_leakage.py` and the staged commit guard; Scenario 240 protects candidate-tree/history and hook behavior.


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

ComfyUI model profile 與拓樸家族的真實來源是 `scripts/creative_execution.py`、`templates/creative/COMFYUI_MODEL_PROFILES.yaml` 及各家族固定 workflow template；目前包含 Z-Image Turbo 與 FLUX 3 Klein Base。可擴充 profile 只能重用已審核家族，新節點或家族仍需程式審核。本機產圖與人工審查流程由 `orchestration/CREATIVE_DIRECTION.md` 說明。

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

- Release-tag provenance policy is canonical in `config/version-tag-policy.yaml` and `orchestration/RELEASE_READINESS.md`; Scenario 208 defines its exact-candidate readiness contract and Scenario 214 covers stable install/update recovery evidence. Readiness never publishes a tag or release.

Retrieval SQLite storage helpers are implemented in `scripts/retrieval_storage.py` and remain re-exported through the `scripts/retrieval_intelligence.py` facade. The existing Project Intelligence documentation closure covers both source modules.


Publication diagnostics use `scripts/publication_authority.py`, `scripts/publication_planning.py`, and `scripts/repository_governance_snapshot.py` as machine sources; current behavior is explained in Git Publication, Security Assurance, Architecture Overview, and the Claude Code adapter.

Runtime Content Safety 的字型格式、上限、失敗原因與 Authority 邊界以 `orchestration/CONTENT_SAFETY_BOUNDARY.md` 為 canonical；Hook/CLI/候選掃描 evidence 記錄於 Scenario 263。

## Shared canonical 文件

Publication troubleshooting lives in the User Guide, with security contracts in Security Assurance and runtime adapter behavior in Harness; Scenarios 260/261 define the shared evidence contract.

Human-facing runtime, diagnostics and governance guidance follows canonical topic placement.


Project Diagnostics 的操作與恢復流程以 [Project Intelligence](PROJECT_INTELLIGENCE.md) 為 Human canonical 文件；公開命令清單維持在 [System Reference](SYSTEM_REFERENCE.md)。

The reusable Python CI bootstrap contract lives with its composite action; per-workflow import profiles live in the caller, and package versions remain in requirements and constraints.

Shared deterministic JSON/hash, path and glob primitives are canonical in `scripts/aips_common/`; existing modules retain compatibility facades. Domain-owned governance fingerprints and runtime action digests remain outside this shared layer.

docs/ARCHITECTURE.md 可作 machine/human shared architecture artifact；CHANGELOG.md 是 release history。

`config/system-facts.yaml` 是公開命令與 runtime support 的 machine-readable source；`scripts/system_facts.py` 只產生 `SYSTEM_REFERENCE.md` 的事實表格，不生成 policy prose。Architecture Surface Inventory 維護 subsystem capability、canonical docs 和 validation bindings。


## 文件一致性

Branch lifecycle behavior is maintained in [System Maintenance](MAINTENANCE.md#branch-lifecycle-hygiene) for Human operations and `orchestration/BRANCH_HYGIENE.md` for Agent authority and evidence rules; [Scenario 257](CONFORMANCE.md#scenario-199-branch-cleanup-proposal-evidence) records its conformance contract.

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

純依賴升級文件豁免（Scenario 221）：`scripts/dependency_impact.py` 的 `pure_dependency_update` 只在候選 diff 的每個檔案都是允許清單內的依賴清單（`.github/workflows/*.yml`、根目錄 `requirements*.txt`、`constraints/*.txt`）、且每一組變更行都只是同一個 action 的完整 SHA 釘選更新（版本註解不得降版），或 `name==version` 的嚴格升版時，判定為 `PURE_DEPENDENCY_UPDATE`。此時 Documentation Impact、Documentation Placement 與 Documentation Sync 只豁免文件要求，並在報告列出每個依賴的分類、風險與 `human_review_required`；混入任何其他行或檔案、降版、未釘選參照、規劃路徑、超過大小上限或判定失敗，一律回到完整規則。秘密掃描、內容安全、Core Change Test Matrix、Integration Gate、必要檢查與人工合併核准都不變，`automatic_merge_authorized` 仍為 false。

Dependabot repository preflight 與 action 釘選同步（Scenario 221）：`scripts/repository_preflight.py`、文件同步 contracts 與 `scripts/documentation_sync.py` CLI 一律經由 `documentation_sync.evaluate_candidate` 判斷文件同步，與 docs-impact、placement 共用同一個 `pure_dependency_update`；不符合時完整規則照舊。驗證 contracts 不再複製 action commit SHA，改由 `dependency_impact.require_pinned_action` 檢查 action 名稱完全相符、40 碼完整 commit SHA、版本註解不低於已審查下限，以及成對 workflow 使用同一 SHA；evolution 設定改記 `action: openai/codex-action`。新 SHA 是否等於上游 tag 對應的 commit，仍由人工審查確認。

文件同步路徑正規化（Scenario 221）：`documentation_sync.evaluate_changes` 只移除開頭一個 `./`（`removeprefix`），不再用 `lstrip("./")` 逐字元剝除；先前 `.github/workflows/x.yml` 會被改成 `github/workflows/x.yml`，使 `config/documentation-sync.yaml` 中所有 `.github/**` 觸發條件（Technology Guide、evolution-radar、publication-preflight、documentation-platform、execution-isolation 等）失效。修正後，人工修改 workflow 需同步對應文件；純依賴升級仍由 `evaluate_candidate` 先行豁免。

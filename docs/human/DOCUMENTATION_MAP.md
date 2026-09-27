# 文件導覽

Human Docs 依使用目的組織，而不是依版本號堆疊。

## Official Docs Site

docs/human/ 是 canonical Human source，也是 VitePress site root。首頁為 index.md，網站提供 sidebar、local search 與 page outline。

Site build 永遠可由 CI 驗證；GitHub Pages 尚未在 repository 啟用時，deployment 會以 `SKIPPED_NOT_CONFIGURED` 誠實略過。啟用 Source = GitHub Actions 後，main push 會自動部署同一份 build artifact。Legacy `TECHNOLOGY_GUIDE.html` / `EVOLUTION_RADAR_OVERVIEW.html` 只保留舊連結相容，不再作為新增內容的 canonical target。

安裝與 CI gate 的 current behavior 會同步反映在 Getting Started、Installation、User Guide、Architecture 與 Technology Guide 的指定 topic sections。

## 文件角色

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

### 架構與技術

- ARCHITECTURE_OVERVIEW.md：目前 architecture。
- TECHNOLOGY_GUIDE.md：目前 technical choices。
- EVOLUTION_RADAR.md / EVOLUTION_RADAR_OVERVIEW.md：maintenance plane。

### Reference / Maintainers

- CONFORMANCE.md：Scenario / verification history。
- MAINTENANCE.md：system maintainer workflow。
- DOCUMENTATION_SYNC.md：文件 consistency / placement contract。

## Agent / machine canonical 文件

`orchestration/TELEMETRY_EXPORT.md` 與 `orchestration/schemas/telemetry-export.yaml` 定義 optional OpenTelemetry trace projection、欄位 allowlist、端點與降級行為；Human 操作說明由 User Guide、Technology Guide 與 Telemetry Export topic 提供。

`orchestration/EVAL_INTEROPERABILITY.md` 是外部 Promptfoo / PyRIT evidence 邊界、支援 subset、CLI、驗證與 Human finding promotion 的 machine canonical 文件。

Content safety 的 machine canonical 文件為 `config/content-safety.yaml`、`scripts/content_safety.py` 與 `orchestration/CONTENT_SAFETY_BOUNDARY.md`；Human-facing placement 由本專案的 documentation placement contract 維護。

`orchestration/TRAJECTORY_EVAL.md`、`templates/review/TRAJECTORY_TRACE.yaml` 與 `templates/review/TRAJECTORY_EVIDENCE.yaml` 是 Eval-as-CI trajectory contract 的 canonical machine-facing 文件。

Independent review isolation is defined across `orchestration/MULTI_REVIEW.md`, `orchestration/DETERMINISTIC_SCHEDULER.md`, `orchestration/INTEGRATION_GATE.md`, `orchestration/schemas/task-graph.yaml`, `orchestration/schemas/context-manifest.yaml`, `scripts/review_packet.py` and `scripts/review_evidence.py`. Human guidance lives in the User Guide, Technology Guide and Security Assurance. The mechanism is implemented but PR enforcement is currently disabled in the active Core Change Matrix; the placement rule keeps these surfaces synchronized.

`orchestration/REQUIREMENT_CLARIFICATION.md` 和 `orchestration/PLANNING_PACKAGE.md` 定義需求澄清與規劃規則；`templates/planning-package/REQUIREMENTS.yaml` 與 `scripts/requirements_traceability.py` 定義可選需求追溯資料及其結構檢查，CLI 提供 JSON PASS/FAIL 與相應退出碼。EARS 語義判讀仍由需求審查負責。

Publication routing and validation contracts live in `orchestration/INTEGRATION_GATE.md`, `scripts/publish_preflight.py` and `scripts/repository_preflight.py`; Human workflows remain in User Guide and Maintenance. Scenario 165 in the shared registry maps their executable evidence.

Risk-adaptive Change Impact 的 Human 說明位於 `PROJECT_INTELLIGENCE.md` 的 Change Impact topic；風險政策、命令、證據與 READY 契約以 `orchestration/CHANGE_IMPACT.md` 為 Agent canonical source。Scenario 175 維護 traversal lifecycle coverage。

Structured unknown dispositions extend that same contract: repository-file evidence is hash-bound, traversal evidence is scope-bound, legacy unknown strings remain unresolved, and closure requires explicit Human review. Scenario 179 records the lifecycle evidence.

Agent 由 AGENTS.md / SYSTEM.md 進入，按需讀取 orchestration/、roles/、skills/。Official Docs Site 不複製這些 protocol 成第二份 Human source。

## Shared canonical 文件

docs/ARCHITECTURE.md 可作 machine/human shared architecture artifact；CHANGELOG.md 是 release history。


## 文件一致性

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

`orchestration/CONFORMANCE.md` 的 Runtime／MCP Scenario 行為由 harness placement rule 管理；變更時同步既有 Harness、Runtime Architecture 與 Runtime Technology 主題，不建立第二套 current-behavior 分類。

Temporal Project Intelligence 的 Human 說明由 `PROJECT_INTELLIGENCE.md` 負責；其 current/as-of/between/why 查詢、Git revision provenance、validity interval 與 supersession 語義，必須與 Agent protocol、Technology Guide 及 Conformance evidence 一起維護。

Execution Isolation provider changes map to Architecture Overview and Security Assurance, with usage in User Guide, optional dependency and runtime details in Technology Guide, verification history in Conformance, and canonical behavior in `orchestration/EXECUTION_ISOLATION.md` / `orchestration/ORCHESTRATOR.md`. The E2B registry stays disabled until source-transfer scope and adapter readiness are explicitly resolved.

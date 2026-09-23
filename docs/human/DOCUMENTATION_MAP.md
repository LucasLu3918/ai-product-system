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

### 架構與技術

- ARCHITECTURE_OVERVIEW.md：目前 architecture。
- TECHNOLOGY_GUIDE.md：目前 technical choices。
- EVOLUTION_RADAR.md / EVOLUTION_RADAR_OVERVIEW.md：maintenance plane。

### Reference / Maintainers

- CONFORMANCE.md：Scenario / verification history。
- MAINTENANCE.md：system maintainer workflow。
- DOCUMENTATION_SYNC.md：文件 consistency / placement contract。

## Agent / machine canonical 文件

Agent 由 AGENTS.md / SYSTEM.md 進入，按需讀取 orchestration/、roles/、skills/。Official Docs Site 不複製這些 protocol 成第二份 Human source。

## Shared canonical 文件

docs/ARCHITECTURE.md 可作 machine/human shared architecture artifact；CHANGELOG.md 是 release history。

## 文件一致性

Workflow and integration-gate behavior is documented in the canonical Human guides and corresponding orchestration documents. Generated CI reports remain artifacts and are not treated as source documentation.

Behavior-bearing change 先由 Documentation Sync 判斷 required docs，再由 Documentation Placement 驗證 current-behavior 內容更新在 canonical section，而不是附加在尾端。任何落在 Technology Guide 廣域 trigger surface、但尚未映射到 placement rule 的新 source 會直接 fail closed；maintainer 必須先決定它屬於既有 topic，或明確新增新的 canonical topic。

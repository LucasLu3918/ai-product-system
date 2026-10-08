---
layout: home

hero:
  name: "AI Product System"
  text: "跨 Agent Software Engineering Harness"
  tagline: "Roles · Skills · Project Intelligence · Deterministic Orchestration · MCP · Human-governed delivery"
  actions:
    - theme: brand
      text: 開始使用
      link: /GETTING_STARTED
    - theme: alt
      text: 安裝
      link: /INSTALLATION

features:
  - title: Agent-independent
    details: Native Runtime adapters 與 MCP access plane 共用同一套 AIPS canonical sources。
  - title: Progressive Disclosure
    details: 只載入任務需要的 Role、Skill、Protocol 與 Project evidence。
  - title: Deterministic Execution
    details: Scheduler、Isolation、Integration Gate 與 validators 分離 semantic planning 與固定規則。
  - title: Human Authority
    details: Git publish、merge、release、production 與核心治理決策保持 Human-controlled。
---

## 文件如何組織

本機角色插畫設定與排查請見 User Guide 的 Creative Direction、Style 與 Brand；命令盤點、流程測試、真實生成及人工品質審查分開驗收。

Creative Bundle 的操作方式見 [User Guide](USER_GUIDE.md#creative-directionstyle-與-brand)，技術限制見 [Technology Guide](TECHNOLOGY_GUIDE.md#local-character-artwork)；OpenCode adapter 的 canonical contract 位於 Agent 文件與 Conformance Scenario 236。

OpenCode 安裝、Session Context、creative asset profile、trace 與原生 acceptance 的操作說明集中於 [Harness](HARNESS.md)。

OpenCode Runtime Adapter 的使用方式見 [Harness](HARNESS.md)，執行邊界與 Scenario 235 見 [Conformance](CONFORMANCE.md)。

OpenCode 全域指示、原生 Skills／Commands、MCP 預覽與保守 ownership 操作見 [Harness](HARNESS.md)。

Creative Direction、EPHEMERAL 本機生成 Bundle、預檢、素材 provenance 與人工視覺審查流程見 [User Guide](USER_GUIDE.md#creative-directionstylebrand)；其執行邊界與 Scenario 236 見 [Conformance](CONFORMANCE.md#scenario-236--local-creative-bundle-execution)。

`CHANGELOG.md` 列出 0.74.0 候選內容；版本標籤與 release readiness 仍依 exact-main SHA 與獨立核准流程處理。

Prospective `aips docs impact --base HEAD --planned-path <path>` resolves sync and placement closure to a fixed point. Each triggered rule requires an update in its canonical topic; combined changes use the union of those topics. Validate every text anchor before applying the batch. Closure is scope evidence and never grants publication authority.

- **開始使用**：Install、First Project、Update、Uninstall。
- **使用指南**：產品交付、Existing Project、Security、Quality。
- **Agent 整合**：Global Harness、native adapters、MCP。
- **核心概念 / 架構**：Project Intelligence、Scheduler、Isolation、Governance；共用 deterministic hash/path/glob helper 維護於 `scripts/aips_common/`，相容輸出見 [Architecture Overview](ARCHITECTURE_OVERVIEW.md)。
- **Reference**：Scenario Conformance、SAL、Technology Guide。
- **Maintainers**：Documentation consistency 與 system maintenance。

版本歷史請看 repository 的 CHANGELOG；較早版本的完整內容位於 `docs/history/changelog/`，根目錄仍保留所有版本連結。最新的 capability registry、runtime telemetry、quality ratchet 與 Agent Eval freshness 架構說明見 [Architecture Overview](ARCHITECTURE_OVERVIEW.md) 與 [Scenario Conformance](CONFORMANCE.md)。維護者的 release readiness 與 tag approval 流程見 Maintenance；驗證歷史請看 Scenario Conformance。

目前主要實作遵循 Runtime 模型偏好，Skill registry 由 frontmatter 決定性產生。詳見 [技術指南](TECHNOLOGY_GUIDE.md) 與 [Conformance](CONFORMANCE.md)。

Reusable local character artwork reuses the Creative Direction Skills, provenance validation and deterministic typeset sheets; see [User Guide](USER_GUIDE.md#creative-directionstyle-與-brand) and [Scenario Conformance](CONFORMANCE.md#scenario-234--local-character-artwork-provenance-and-composition).

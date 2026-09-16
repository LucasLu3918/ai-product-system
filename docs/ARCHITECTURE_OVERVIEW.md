# 系統架構總覽

這份文件讓第一次接觸 AI Product System（AIPS）的使用者快速理解目前架構。

![AI Product System 架構總覽](assets/system-overview.svg)

## 1. Global Harness

![AIPS Global Harness](assets/harness-overview.svg)

安裝 AIPS 後，支援的 Agent Runtime 先取得 Minimal Bootstrap：

~~~text
Agent Runtime
→ Runtime Adapter
→ AIPS Minimal Bootstrap
→ Harness Resolve
→ Runtime + Project Instructions
→ AIPS Orchestration（需要時）
~~~

AIPS 不會為了自動接入覆寫使用者原有 Agent Instructions / Skills。安全自動接入不可行時會標示 MANUAL。

## 2. Project Mode

~~~text
Project without .ai/
→ EPHEMERAL
→ 使用 AIPS，但不持久化

aips attach
→ ATTACHED
→ 可使用 .ai State / Knowledge / Runs / Decisions
~~~

Preflight 不會再自動 Attach。

## 3. Project Knowledge + Instruction Composition

AIPS 組合 Runtime-native Instructions、Project AGENTS / ADR / Contracts / Docs、Project Knowledge 與 Current User Request。已經有權威資訊就存 Pointer，不重複掃描/複製整個專案。

## 4. Quality-aware Product Delivery

![完整產品交付流程](assets/product-delivery-overview.svg)

完整產品先做到 Quality Profile → Planning → Implementation → Local Verification → LOCAL_COMPLETE。只有 Production 在 Scope 時才接續 Production Enablement → Observability → Staging / Release Readiness → Production → Post-deploy Verification → PRODUCTION_VERIFIED。

## 5. Visual Consistency Repair

全專案「風格怪異」預設進入 V2 Product Consistency Sweep：Representative Routes → Component Inventory → Baseline → Outlier/Variant → Implementation Root Cause → Shared Fix → Before/After → Project Visual Profile。

## 6. 安裝與生命週期

![安裝與專案生命週期](assets/system-lifecycle.svg)

System / Harness / Project lifecycle 分離。解除 AIPS 只移除 AIPS-owned integrations；Project source、原本 Agent Instructions、Skills 與 .ai/ Workspace 都保留。

## 7. 架構圖同步規則

大型/Core Change 若改變 Routing、Instruction Composition、Persistence、Delivery、Install/Uninstall、Security/Quality lifecycle 或主要 Context flow，必須同步檢查：

- docs/ARCHITECTURE.md Mermaid
- docs/ARCHITECTURE_OVERVIEW.md
- docs/assets/system-overview.svg
- docs/assets/harness-overview.svg
- docs/assets/product-delivery-overview.svg
- docs/assets/system-lifecycle.svg

若某張圖不受影響，要在 Documentation Impact Review 明確標示 N/A + reason。

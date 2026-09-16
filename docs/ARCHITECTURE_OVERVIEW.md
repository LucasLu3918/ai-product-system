# 系統架構總覽

![AI Product System 架構總覽](assets/system-overview.svg)

AIPS v0.9 是 Turn-Aware Global Harness + Project Intelligence + Change Impact Guard。

## 1. Turn-Aware Global Harness

![AIPS Global Harness](assets/harness-overview.svg)

~~~text
User Prompt
→ Runtime-native integration
→ Compact Turn Context
→ Runtime/User Rules + Project Rules + Relevant Intelligence + AIPS Protocol
→ Agent Planning
~~~

Codex 以 CONTEXT_ALWAYS 為目標；Claude Code / Gemini CLI 在 native Hook 可驗證時提供 TURN_NATIVE。

## 2. Project Intelligence

![Project Intelligence](assets/project-intelligence-overview.svg)

第一次 Existing Project 需要廣泛理解或修改時，先 Read-only Bootstrap，再完成 Architecture / Data Flow / Modules / Contracts / DB / Events / Consumers / Conventions / Tests / Security / Operations 的 semantic enrichment，最後才 READY。

後續 Turn 只讀 relevant Intelligence；watched source 真正受影響時才 Targeted Refresh。

## 3. EPHEMERAL / ATTACHED

EPHEMERAL 不在 Project 建立 .ai/，Intelligence 可存在 AIPS External Cache；ATTACHED 使用 .ai/intelligence/。Attach/Detach 會 validated migrate/sync。

## 4. Existing Project Mutation

~~~text
Current Prompt
→ Relevant Intelligence
→ Change Boundary
→ IMPACT_GRAPH
→ CHANGE_IMPACT
→ Preserve Valid Native Conventions
→ Implementation
→ Tests / Review
→ Actual Diff vs Declared Impact
→ Targeted Intelligence Refresh
~~~

## 5. Quality-aware Product Delivery

![完整產品交付流程](assets/product-delivery-overview.svg)

v0.9 沒有改變 LOCAL_COMPLETE → optional Production Enablement → PRODUCTION_VERIFIED 的主生命週期。

## 6. Installation Lifecycle

![安裝與專案生命週期](assets/system-lifecycle.svg)

Uninstall 只移除 AIPS-owned Managed Blocks / Hooks / Extensions / CLI。User instructions、Skills、Project source、.ai/ 與 External Project Intelligence 預設保留。

## 7. Architecture Diagram Impact

v0.9 影響 system-overview、harness-overview、system-lifecycle、project-intelligence-overview 與 Maintainer Mermaid。product-delivery-overview 為 N/A，因產品交付生命週期本身沒有改變。
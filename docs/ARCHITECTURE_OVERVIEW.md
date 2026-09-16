# 系統架構總覽

這份文件讓第一次接觸 AI Product System 的使用者快速理解整體流程。

![AI Product System 架構總覽](assets/system-overview.svg)

## 簡單理解

1. **使用者意圖與決策（Human Intent & Approval）**：需求、素材、Scope 與最終決策。
2. **預檢與治理（Preflight & Governance）**：更新、風險、重大變更與規劃需求。
3. **專案知識（Project Knowledge）**：優先重用既有 AGENTS / ADR / Docs / Knowledge Index，不重複掃描整體 Repository。
4. **品質規劃（Quality Planning）**：Q1/Q2/Q3 基準下評估效能、安全、使用性、可靠性、維護性、成本與交付時間。
5. **路由（Routing）**：選擇最小 Work Mode、Role、Skill、Context、Model 與 Tool。
6. **執行與審核（Execution & Review）**：實作、驗證、Visual Consistency Repair、Independent / Multi-Perspective Review。
7. **可接手工作區（Persistent Workspace）**：保存規劃、Project Knowledge、Quality、Visual Profile、Decision 與 Run State。
8. **Git 發布確認（Publish Gate）**：Remote 發布前再次由使用者確認。

詳細技術架構請看 `docs/ARCHITECTURE.md`。

## 完整產品交付

完整產品預設先做到本地可運作、可測試、可審核：

~~~text
需求
→ Quality Profile
→ Planning
→ Implementation
→ Local Verification
→ LOCAL_COMPLETE
~~~

如果使用者一開始沒有要求正式上線，系統此時才詢問是否接續 Production Enablement。

~~~text
LOCAL_COMPLETE
→ Production Enablement
→ Infrastructure / CI/CD / Data / Recovery
→ Observability
→ Staging
→ Release Readiness
→ Production
→ Post-deploy Verification
→ PRODUCTION_VERIFIED
~~~

Observability 在 Architecture / Coding 階段先規劃 Structured Logs、Health Check、Metrics/Trace/Audit hooks；ELK、Loki、Prometheus、Grafana、OpenTelemetry 或 Managed Service 等具體選型等 Production 環境確認後再決定。

## Project Knowledge

新的 Agent 不必每次重新理解整體專案。

~~~text
AGENTS / ADR / Contract / Official Docs
→ Knowledge Index
→ 本次相關 Topic
→ 不足時才做 Targeted Discovery
~~~

已有權威文件就只建立 Pointer；只有重新探索成本高、跨任務穩定且缺少正式文件的知識才存進 `.ai/knowledge/`。

## Visual Consistency Repair

「請幫我調整這個專案風格怪異的部分」預設進入 V2 Product Consistency Sweep。

系統會使用 Representative Routes、Component Inventory、UI Consistency Baseline、Outlier/Variant 判斷、Implementation Root Cause 與 Before/After Render 驗證，而不是只改幾個局部 CSS。

可重用的專案視覺知識保存在 `docs/design/PROJECT_VISUAL_PROFILE.yaml`。

## 安裝與專案生命週期

![安裝與專案生命週期](assets/system-lifecycle.svg)

System Install 與 Project Attach 是不同層級。解除安裝 System 不會刪除產品；Detach Project 會保存可恢復的 AI Workspace。

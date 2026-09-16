# 系統架構總覽

這張圖用來讓第一次接觸 AI Product System 的使用者快速理解整體流程。

![AI Product System 架構總覽](assets/system-overview.svg)

## 簡單理解

1. **使用者意圖與決策（Human Intent & Approval）**：需求、素材、Scope 與最終決策。
2. **預檢與治理（Preflight & Governance）**：確認更新、風險、重大變更與規劃需求。
3. **路由（Routing）**：選擇最小 Work Mode、Role、Skill、Context、Model 與 Tool。
4. **專用流程（Protocols）**：需要時才載入 Planning、Creative、Brand、Security、Capability Incubation。
5. **確定性自動化（Deterministic Automation）**：固定規則資料先用工具/程式轉成結構化結果。
6. **執行與審核（Execution & Review）**：實作或生成後做獨立 Review。
7. **可接手工作區（Persistent Workspace）**：保存規劃、品牌、Decision、Run State。
8. **Git 發布確認（Publish Gate）**：Remote 發布前再次由使用者確認。

詳細技術架構請看 `docs/ARCHITECTURE.md`。

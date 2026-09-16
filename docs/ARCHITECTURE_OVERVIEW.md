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


## 完整產品交付流程

![完整產品交付流程](assets/product-delivery-overview.svg)

當需求是完整產品時，AI Product System 會從使用者需求一路協調到 Production，而不是把「產生程式碼」當成終點。

關鍵原則：

- Product Workspace 是整體 System of Record。
- `PRODUCT.yaml` 是 Agent 快速導航入口。
- Frontend / Backend 是 Deployment Units，不強迫拆成不同 Repository。
- Security 在 Planning 與 Release 都會驗證。
- Staging 是正式產品的預設中繼環境。
- Release Readiness 集中判斷 Production 技術條件。
- Production Done 必須包含部署後驗證與 Recovery 能力。

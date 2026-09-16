# AI Product System

AI Product System 是一套可重用的 AI 協作開發系統，讓不同 AI Agent 或人類團隊能依同一套規則規劃、設計、實作、審核與維護產品。

## 5 分鐘開始

~~~bash
mkdir -p ~/Developer
cd ~/Developer
gh repo clone LucasLu3918/ai-product-system
cd ai-product-system
./scripts/bootstrap.sh
aips doctor
~~~

初始化專案：

~~~bash
aips init /path/to/project
~~~

每次要修改專案前，先執行系統更新預檢（System Update Preflight）：

~~~bash
aips preflight /path/to/project
~~~

接著告訴 AI：

~~~text
使用 ai-product-system 處理目前專案。
先閱讀 ai-product-system/AGENTS.md，
並依系統流程執行本次需求。
~~~

## 你可以用它做什麼？

- 完整產品從需求、規劃、程式、測試、資安到 Production 交付（End-to-End Product Delivery）
- 新產品規劃與可重現規劃包（Reproducible Planning Package）
- 既有程式修改與獨立審核（Independent Review）
- 風險比例式資安審核（Risk-Proportional Security Assurance）
- 網站、Banner、主視覺、社群圖等創意方向（Creative Direction）
- 品牌基礎與品牌導引（Brand System）
- 效能、成本、交付與 Incident 等工作模式（Work Modes）
- 依風險與複雜度選擇最低足夠模型（Minimum Sufficient Intelligence）
- 能用固定規則處理的資料，優先交給確定性自動化（Deterministic Automation）

## 文件入口

### 一般使用者

1. [快速上手](docs/GETTING_STARTED.md)
2. [完整使用指南](docs/USER_GUIDE.md)
3. [安裝、更新與解除安裝](docs/INSTALLATION.md)
4. [系統架構總覽](docs/ARCHITECTURE_OVERVIEW.md)

### AI Agent

1. `AGENTS.md`
2. `SYSTEM.md`
3. 只載入本次需要的 `orchestration/`、Role 與 Skill

完整文件用途請看 [文件導覽](docs/DOCUMENTATION_MAP.md)。

## 核心原則

- 不把未知當成事實。
- 重大或核心修改先規劃、再確認、才實作。
- 新增 Role / Skill / Capability 前先搜尋並重用既有能力。
- 視覺設計先理解使用者素材、品牌與 Reference，不直接猜風格。
- 高風險功能使用更嚴格的資安與可靠性審核。
- 可用 Shell / 簡單程式確定產生的資料，先程式化再交回 AI。
- Git 遠端發布前先列出修改檔案、驗證結果與 Atomic Commit 計畫。
- Human Docs 與 Agent Docs 分流，但流程異動時必須同步更新。

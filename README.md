# AI Product System

AI Product System（AIPS）是一套可安裝、可解除的跨 Agent 軟體工程 Harness。安裝後，支援的 AI Agent Runtime 會先載入最小 AIPS Bootstrap，再依任務決定是否進入 AIPS 的規劃、實作、審核與交付流程。

## 5 分鐘開始

~~~bash
mkdir -p ~/Developer
cd ~/Developer
gh repo clone LucasLu3918/ai-product-system
cd ai-product-system
./scripts/bootstrap.sh
aips doctor
~~~

安裝完成後可檢查 Global Harness：

~~~bash
aips harness status
aips harness doctor
~~~

AIPS 不會覆寫你原本的 AGENTS.md、CLAUDE.md、GEMINI.md、Agent Config 或自訂 Skills。若某個 Runtime 已有使用者自訂的全域 instruction file，AIPS 會保留原檔並把該 Runtime 標示為 MANUAL，而不是強行修改。

專案可以直接用 Ephemeral Mode 工作；只有要保存 AIPS Project State / Knowledge 時才需 Attach：

~~~bash
aips attach /path/to/project
~~~

舊的 aips init <project> 仍保留相容性。

每次要修改專案前，先執行系統更新預檢（System Update Preflight）：

~~~bash
aips preflight /path/to/project
~~~

若目前 Agent 已顯示為 AUTOMATIC，日常使用不需要再手動貼「使用 ai-product-system」提示詞。直接和原本 Agent 對談即可。

需要確認某次 Session / Project 解析結果時：

~~~bash
aips harness resolve --cwd "$PWD"
~~~

## 你可以用它做什麼？

- 安裝後自動接入支援的 Codex / Claude Code / Gemini CLI Runtime（安全可逆時）
- 完整產品從需求、品質規劃、Local Complete 到可選的 Production Enablement（End-to-End Product Delivery）
- 新產品規劃與可重現規劃包（Reproducible Planning Package）
- 既有程式修改與獨立審核（Independent Review）
- 風險比例式資安審核（Risk-Proportional Security Assurance）
- 網站、Banner、主視覺、社群圖等創意方向（Creative Direction）
- 品牌基礎與品牌導引（Brand System）
- 效能、成本、交付與 Incident 等工作模式（Work Modes）
- Q1/Q2/Q3 風險比例式品質規劃（Quality Planning）
- 專案知識快取（Project Knowledge），避免不同 Agent 重複掃描整體專案
- V1/V2 視覺一致性修復（Visual Consistency Repair）
- 依風險與複雜度選擇最低足夠模型（Minimum Sufficient Intelligence）
- 能用固定規則處理的資料，優先交給確定性自動化（Deterministic Automation）

## 文件入口

### 一般使用者

1. [快速上手](docs/GETTING_STARTED.md)
2. [完整使用指南](docs/USER_GUIDE.md)
3. [安裝與解除](docs/INSTALLATION.md)
4. [Global Harness 與 Agent Adapter](docs/HARNESS.md)
5. [系統架構總覽](docs/ARCHITECTURE_OVERVIEW.md)

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


## 最短解除方式

~~~bash
aips uninstall
~~~

或：

~~~bash
./scripts/uninstall.sh
~~~

解除會移除 AIPS-owned Harness Adapter、CLI 與 AIPS config；不會刪除或改寫使用者既有 Agent instructions、custom Skills、專案原始碼或 Project .ai/ Workspace。完整說明請看 docs/INSTALLATION.md。

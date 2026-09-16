# 快速上手

這份文件給第一次使用 AI Product System（AIPS）的人。

## 1. 安裝

需求：Git、Python 3；私人 Repository 建議使用 GitHub CLI（gh）。

~~~bash
mkdir -p ~/Developer
cd ~/Developer
gh repo clone LucasLu3918/ai-product-system
cd ai-product-system
./scripts/bootstrap.sh
~~~

等同：

~~~bash
aips install
~~~

安裝會：

~~~text
Install AIPS Core / CLI
→ 建立 Global Harness Ownership Manifest
→ 偵測支援的 Agent Runtime
→ 安全可逆時安裝 AIPS-owned Adapter
→ 驗證
~~~

它不會覆寫既有的 AGENTS.md / AGENTS.override.md、~/.claude/CLAUDE.md、~/.gemini/GEMINI.md、Agent Runtime Config 或使用者/專案自訂 Skills。

如果既有檔案會被覆寫，該 Runtime 會改成 MANUAL，而不是修改你的設定。

## 2. 確認 Global Harness

~~~bash
aips doctor
aips harness status
aips harness doctor
~~~

你可能看到：

~~~text
codex: AUTOMATIC
claude-code: MANUAL
gemini-cli: AUTOMATIC
~~~

AUTOMATIC 代表 Agent 啟動時能安全載入 AIPS Minimal Bootstrap。

MANUAL 代表 Runtime 已偵測到，但 AIPS 為了保護既有使用者設定沒有自動修改它。

## 3. 平常怎麼使用

如果 Agent Adapter 是 AUTOMATIC：直接像原本一樣開啟 Codex / Claude Code / Gemini CLI 並對談，不需要每次貼「請使用 AIPS」。

AIPS Global Harness 只先載入極小 Bootstrap；一般知識聊天不會因此跑完整 Product Planning。當任務屬於軟體 / 產品 / 專案工作時，Agent 才逐步載入需要的 AIPS Context。

## 4. 專案不需要先 Attach

在 Git Project 內直接工作時，若沒有 .ai/：

~~~text
Project Mode = EPHEMERAL
~~~

可以使用 AIPS 流程與專案自己的 AGENTS/CLAUDE/GEMINI/ADR/Docs，但不建立永久 AIPS State。

需要保存 Project Knowledge、State、Runs 等資訊時才執行：

~~~bash
aips attach ~/Developer/projects/my-project
~~~

此後 Project Mode = ATTACHED。

## 5. 每次修改專案前

~~~bash
aips preflight ~/Developer/projects/my-project
~~~

Preflight 只安全更新/驗證 AIPS。若專案沒有 Attach，v0.8 起不會自動建立 .ai/。

## 6. 查看解析結果

~~~bash
aips harness resolve --cwd "$PWD"
~~~

可查看 AIPS version / bootstrap、Runtime / Adapter 狀態、Project Root、EPHEMERAL / ATTACHED、Project instructions、Runtime-native instruction pointers，以及 Project Knowledge / State 是否可用。

## 7. 解除專案持久化

~~~bash
aips detach ~/Developer/projects/my-project
~~~

.ai/ 會封存成 .ai.detached-*，產品程式碼不受影響。

## 8. 解除 AIPS

~~~bash
aips uninstall
~~~

或：

~~~bash
cd ~/Developer/ai-product-system
./scripts/uninstall.sh
~~~

解除會移除 AIPS-owned Adapter / Harness / CLI / config。

保留：

~~~text
✓ 使用者 AGENTS / CLAUDE / GEMINI instructions
✓ 使用者 custom Skills
✓ 專案 instructions / Skills
✓ 專案原始碼
✓ Project .ai/ Workspace
✓ System Git Repository（除非你之後自行刪除）
~~~

若連 AIPS Python Virtual Environment 一起移除：

~~~bash
aips uninstall --remove-venv
~~~

詳細生命週期請看 docs/INSTALLATION.md 與 docs/HARNESS.md。

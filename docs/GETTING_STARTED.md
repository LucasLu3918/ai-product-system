# 快速上手

這份文件給第一次使用 AI Product System 的人。

## 1. 安裝系統（Install）

完成 Git、Python 3 與 GitHub CLI（gh）設定後：

~~~bash
mkdir -p ~/Developer
cd ~/Developer
gh repo clone LucasLu3918/ai-product-system
cd ai-product-system
./scripts/bootstrap.sh
~~~

確認：

~~~bash
aips doctor
aips version
~~~

## 2. 連接專案（Attach Project）

~~~bash
aips attach ~/Developer/projects/my-project
~~~

舊指令 aips init <project> 仍可使用。

系統會建立：

~~~text
.ai/
├── PROJECT.md
├── STATE.yaml
├── MANIFEST.yaml
└── SYSTEM.yaml
~~~

## 3. 每次實作前

執行系統更新預檢（System Update Preflight）：

~~~bash
aips preflight ~/Developer/projects/my-project
~~~

它只會安全更新 AI Product System，不會擅自 git pull 你的產品專案。

## 4. 查看狀態

~~~bash
aips status ~/Developer/projects/my-project
~~~

可確認 System version、CLI、專案是否已 Attach，以及 Workspace 位置。

## 5. 開始交給 AI

~~~text
使用 ai-product-system 處理目前專案。

System:
~/Developer/ai-product-system

Target Project:
~/Developer/projects/my-project

先閱讀 AGENTS.md，再依 SYSTEM.md 路由。
如果需求還不夠明確，請先逐步引導我整理成可實作目標。
如果有更適合的做法、重大風險或 Blocking Unknown，
請先提出建議，不要直接實作。
~~~

## 6. 解除專案連接（Detach）

~~~bash
aips detach ~/Developer/projects/my-project
~~~

它不會刪除產品程式碼，也不會永久刪除 AI Workspace。

原本 .ai/ 會安全封存成：

~~~text
.ai.detached-YYYYMMDD-HHMMSS/
~~~

CLI 會顯示如何恢復。

## 7. 解除安裝系統（Uninstall）

~~~bash
cd ~/Developer/ai-product-system
./scripts/uninstall.sh
~~~

或：

~~~bash
aips uninstall
~~~

若連 System 的 Python Virtual Environment 一起移除：

~~~bash
./scripts/uninstall.sh --remove-venv
~~~

Repository 與產品專案都會保留。

詳細生命週期請看：[安裝與生命週期](INSTALLATION.md)

# 安裝、更新與解除安裝

本文件給人類使用者。

## 新電腦安裝

需要：
- Git
- Python 3
- GitHub CLI（`gh`，私人 Repository 建議使用）

~~~bash
mkdir -p ~/Developer
cd ~/Developer
gh repo clone LucasLu3918/ai-product-system
cd ai-product-system
./scripts/bootstrap.sh
~~~

如果 `~/.local/bin` 不在 PATH：

~~~bash
export PATH="$HOME/.local/bin:$PATH"
~~~

確認：

~~~bash
aips doctor
aips validate
aips version
~~~

## 初始化專案

~~~bash
aips init /path/to/project
~~~

它會建立最小的 AI Workspace，並將 AI Product System 的版本與 Commit 記錄到 `.ai/SYSTEM.yaml`。

## 每次實作前更新

執行系統更新預檢（System Update Preflight）：

~~~bash
aips preflight /path/to/project
~~~

安全規則：
- System repo 必須位於 `main`。
- Working tree 必須乾淨。
- 使用 `git pull --ff-only`。
- 不自動 merge / rebase。
- Major Version 更新需要明確確認。
- 不會自動更新 Target Project Git。

## 手動更新

~~~bash
aips update
~~~

## 診斷

~~~bash
aips doctor
~~~

## 驗證

~~~bash
aips validate
~~~

## 解除安裝

只移除 CLI 與設定：

~~~bash
aips uninstall
~~~

連驗證用 Virtual Environment 一起移除：

~~~bash
aips uninstall --remove-venv
~~~

Repository 與產品專案不會被自動刪除。

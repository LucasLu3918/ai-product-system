# 安裝與生命週期

本文件給人類使用者，說明 AI Product System 從安裝、連接專案、日常使用、解除連接到解除安裝的完整生命週期（Lifecycle）。

![AI Product System 安裝與生命週期](assets/system-lifecycle.svg)

## 1. 系統與專案是兩個不同層級

~~~text
~/Developer/
├── ai-product-system/        ← AI Product System
│   ├── bin/aips
│   ├── roles/
│   ├── skills/
│   └── ...
│
└── projects/
    └── my-product/           ← 你的產品
        ├── .ai/              ← Product AI Workspace
        └── ...
~~~

因此：

- Uninstall System 不等於刪除產品。
- Detach Project 不等於刪除產品程式碼。
- Product 的 .ai/ 不會因 System Uninstall 被自動刪除。

## 2. 安裝（Install）

需求：
- Git
- Python 3
- GitHub CLI（gh，私人 Repository 建議使用）

~~~bash
mkdir -p ~/Developer
cd ~/Developer
gh repo clone LucasLu3918/ai-product-system
cd ai-product-system
./scripts/bootstrap.sh
~~~

bootstrap.sh 是安裝入口，內部沿用同一套 CLI：

~~~bash
aips install
~~~

它會：
- 建立 System 專用 .venv；
- 安裝 Validator dependencies；
- 建立 ~/.local/bin/aips symlink；
- 建立 ~/.config/aips；
- 驗證 Repository。

如果 ~/.local/bin 不在 PATH：

~~~bash
export PATH="$HOME/.local/bin:$PATH"
~~~

確認：

~~~bash
aips doctor
aips validate
aips version
~~~

## 3. 連接專案（Attach）

~~~bash
aips attach /path/to/project
~~~

它會建立/更新最小 .ai/ Workspace，並記錄目前 AI Product System version + commit。

舊指令：

~~~bash
aips init /path/to/project
~~~

保留相容性，等同 Attach。

如果專案存在 .ai.detached-* 封存，Attach 會先停止並提示恢復既有 Workspace，避免意外建立另一份狀態。

## 4. 每次工作前（Preflight）

~~~bash
aips preflight /path/to/project
~~~

安全規則：
- System repo 必須位於 main；
- Working tree 必須乾淨；
- 使用 git pull --ff-only；
- 不自動 merge / rebase；
- Major Version 更新需要明確確認；
- 不會自動更新 Target Project Git；
- 更新後重新執行新版 CLI 並驗證；
- 更新專案 .ai/SYSTEM.yaml provenance。

## 5. 查看狀態（Status）

~~~bash
aips status /path/to/project
~~~

顯示：
- System path/version/commit；
- CLI 是否安裝；
- Project 是否 Attached；
- Workspace path；
- Project 記錄的 System version/commit；
- 若已 Detach，顯示最近封存的 Workspace。

## 6. 解除專案連接（Detach）

~~~bash
aips detach /path/to/project
~~~

預設採可復原解除（Reversible Detach）。

~~~text
.ai/
↓
.ai.detached-YYYYMMDD-HHMMSS/
~~~

不會：
- 刪除 Product source code；
- 永久刪除 AI Workspace；
- 修改產品 Git history。

恢復方式會由 CLI 輸出，概念上是：

~~~bash
mv /path/to/project/.ai.detached-YYYYMMDD-HHMMSS /path/to/project/.ai
aips attach /path/to/project
~~~

第一版不提供 detach 同時永久刪除 Workspace，避免 destructive lifecycle 變得不必要地複雜。

## 7. 更新（Update）

手動更新：

~~~bash
aips update
~~~

Major Version：

~~~bash
aips update --allow-major
~~~

產品工作建議仍使用：

~~~bash
aips preflight /path/to/project
~~~

## 8. 解除安裝（Uninstall）

### 保留 Repository 與 .venv

~~~bash
./scripts/uninstall.sh
~~~

或：

~~~bash
aips uninstall
~~~

會移除：
- ~/.local/bin/aips symlink；
- ~/.config/aips。

會保留：
- System Git Repository；
- System .venv；
- 所有產品；
- 所有 Project .ai/ / detached workspace。

### 連 .venv 一起移除

~~~bash
./scripts/uninstall.sh --remove-venv
~~~

或：

~~~bash
aips uninstall --remove-venv
~~~

## 9. 完整本機移除（Complete Local Removal）

先：

~~~bash
aips uninstall --remove-venv
~~~

確認產品與 Detached Workspace 都已妥善處理後，再由使用者明確刪除 System Repository：

~~~bash
rm -rf ~/Developer/ai-product-system
~~~

AIPS 不會在執行中的 Uninstall 自動刪除自己的 Git Repository。

## 10. 重新安裝（Reinstall）

如果 Repository 還在：

~~~bash
cd ~/Developer/ai-product-system
./scripts/bootstrap.sh
~~~

如果 Repository 已刪除：

~~~bash
cd ~/Developer
gh repo clone LucasLu3918/ai-product-system
cd ai-product-system
./scripts/bootstrap.sh
~~~

原產品不需要重新建立；依需求重新 Attach：

~~~bash
aips attach /path/to/project
~~~

## 11. 常用生命週期指令

~~~text
System
  ./scripts/bootstrap.sh
  aips install
  aips update
  aips doctor
  aips validate
  ./scripts/uninstall.sh
  aips uninstall

Project
  aips attach <project>
  aips status <project>
  aips preflight <project>
  aips detach <project>

Compatibility
  aips init <project>
~~~

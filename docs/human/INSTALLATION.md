# 安裝、更新與解除

AIPS 的 public lifecycle terminology 統一使用 **Install / Update / Uninstall**。bootstrap.sh 只保留為 backward-compatible wrapper，不再是新使用者文件的主要入口。

## macOS / Linux

~~~bash
curl -fsSL https://raw.githubusercontent.com/LucasLu3918/ai-product-system/main/scripts/install.sh | bash
~~~

Installer 會自行管理 AIPS system checkout、Python virtual environment、CLI 與可安全安裝的 Runtime integrations。使用者不需要先建立目錄、cd 或手動 git clone。

預設 managed system path：

~~~text
$XDG_DATA_HOME/aips/system
或
~/.local/share/aips/system
~~~

可用 AIPS_INSTALL_DIR 覆寫。

## Windows

目前正式支援 **Windows + WSL**，不宣稱 native PowerShell runtime 已完成。

在 PowerShell：

~~~powershell
irm https://raw.githubusercontent.com/LucasLu3918/ai-product-system/main/scripts/install.ps1 | iex
~~~

PowerShell launcher 會把安裝交給 WSL 內相同的 Linux installer，因此核心 install lifecycle 只有一份。安裝後請在 WSL terminal 執行 AIPS。

> Windows native PowerShell / CMD runtime 若未來實作，必須另有真實 lifecycle evidence 後才可標記為 supported。

## 驗證

~~~bash
aips version
aips doctor
aips harness status
aips mcp inspect
~~~

doctor 會檢查 system checkout、Python environment、CLI、Harness 與 MCP availability。

## Runtime integration

Native Runtime Adapter 與 MCP 是兩個互補平面：

- Codex / Claude Code / Gemini CLI：依可驗證能力安裝 AIPS-owned integration。
- MCP-compatible Host：可使用 aips mcp serve。
- MCP-only governance enforcement 仍為 ADVISORY；native pre-tool hook 才能提供已驗證的 stronger enforcement。

細節放在 [Global Harness 與 MCP](HARNESS.md)，不在 Installation 頁重複 implementation 細節。

## 更新

~~~bash
aips update
~~~

AIPS 只在 managed system checkout clean、history 可 fast-forward 時自動更新；major version 變更仍需要顯式處理。

Existing Project mutation 前：

~~~bash
aips preflight /path/to/project
~~~

## 解除安裝

~~~bash
aips uninstall
~~~

選配：

~~~bash
aips uninstall --remove-cache
aips uninstall --remove-cache --remove-venv
~~~

Windows + WSL 可從 WSL terminal 執行相同 aips uninstall；repository 亦保留 scripts/uninstall.ps1 作 recovery wrapper。

## 會保留什麼

預設不刪除：

- 使用者原本的 Agent instructions；
- custom Skills；
- Project source；
- Project .ai/ workspace；
- External Project Intelligence；
- third-party MCP client-owned configuration。

若 client 曾手動註冊 aips mcp serve，需在該 client 自己移除 registration；AIPS 不猜測或刪除 client-owned settings。

## 相容入口

~~~bash
./scripts/bootstrap.sh
./scripts/uninstall.sh
~~~

這些只保留給既有 checkout / recovery。新文件與新使用者一律使用 Install / Uninstall terminology。

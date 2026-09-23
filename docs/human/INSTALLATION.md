# 安裝、更新與解除

AIPS 的 public lifecycle terminology 統一使用 **Install / Update / Uninstall**。bootstrap.sh 只保留為 backward-compatible wrapper，不再是新使用者文件的主要入口。

## macOS / Linux

~~~bash
(
  set -e
  installer="$(mktemp)"
  trap 'rm -f "$installer"' EXIT
  curl -fsSL --output "$installer" https://raw.githubusercontent.com/LucasLu3918/ai-product-system/main/scripts/install.sh
  test -s "$installer"
  bash "$installer" --configure-shell
)
~~~

Installer 會自行管理 AIPS system checkout、Python virtual environment、CLI 與可安全安裝的 Runtime integrations。`--configure-shell` 會在 zsh／bash profile 寫入可辨識、可逆的 AIPS-owned `PATH` 區塊；使用者不需要先建立目錄、cd 或手動 git clone。若要自行管理 profile，使用 `--no-configure-shell`。

AIPS runtime 需要 Python 3.10 以上。Installer 會依序選擇可用的相容 Python；需要指定解譯器時可設定 `AIPS_PYTHON=/path/to/python3`。若既有 AIPS-owned `.venv` 使用較舊版本，install／update／preflight 在修復依賴時會用相容 Python 重建該環境。

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
$installer = Join-Path ([IO.Path]::GetTempPath()) ("aips-install-" + [guid]::NewGuid().ToString("N") + ".ps1")
try {
  Invoke-WebRequest -Uri https://raw.githubusercontent.com/LucasLu3918/ai-product-system/main/scripts/install.ps1 -OutFile $installer -ErrorAction Stop
  if (!(Test-Path -LiteralPath $installer) -or (Get-Item -LiteralPath $installer).Length -eq 0) { throw "AIPS installer download was empty." }
  Invoke-Expression ([IO.File]::ReadAllText($installer))
} finally {
  Remove-Item -LiteralPath $installer -ErrorAction SilentlyContinue
}
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

Maintainer 的發布前入口為 `aips docs impact` 與 `aips publish plan|preflight|post-merge`。一般使用者安裝不會自動執行 GitHub 查詢、重寫 branch 或取得 publication authority。

安裝流程本身會執行 **installation integrity validation**：確認必要 runtime dependency、核心 source contract 與 Human documentation placement 可用；它不會在一般使用者電腦重跑需要 Playwright/browser 等開發工具的完整 repository CI suite。

`aips doctor` 會檢查 system checkout、Python environment、必要的 PyYAML／MCP runtime dependencies、CLI、Harness 與 MCP availability；必要依賴不完整時會回傳失敗並提示重新執行 `aips install`。`aips update` 與 `aips preflight` 會在 managed installation 缺少必要依賴時自動依 `requirements.txt` 修復。Maintainer 若要執行完整 repository validation，使用 `aips validate`；正式 PR / main 仍以 GitHub Actions 的 Janitor / repository checks 為準。

## Runtime integration

Native Runtime Adapter 與 MCP 是兩個互補平面：

- Codex / Claude Code / Gemini CLI：依可驗證能力安裝 AIPS-owned integration。
- MCP-compatible Host：可使用 `aips mcp serve`；以 `aips mcp config --client cursor|windsurf|copilot|amp|codex|generic` 產生 review-only 設定。
- MCP-only governance enforcement 仍為 ADVISORY；native pre-tool hook 才能提供已驗證的 stronger enforcement。

產生設定只會輸出 JSON，不會寫入或覆蓋第三方 client-owned configuration；使用者確認後再依 Host 文件安裝設定。

細節放在 [Global Harness 與 MCP](HARNESS.md)，不在 Installation 頁重複 implementation 細節。

## 常見問題與排查

### `aips: command not found`

Installer 會建立 `~/.local/bin/aips`（或 `AIPS_BIN_HOME` 指定的路徑）。官方安裝命令使用 `--configure-shell`，為 zsh 的 `~/.zprofile` 或 bash 的適用 profile 加入 AIPS-owned block。未提供選項的互動式安裝會詢問；非互動式安裝只顯示操作提示，不會等待輸入。

可檢查或管理 shell integration：

~~~bash
"$HOME/.local/bin/aips" shell status
"$HOME/.local/bin/aips" shell install
"$HOME/.local/bin/aips" shell uninstall
~~~

重複執行 `shell install` 不會重複加入區塊。若 managed block 被修改，AIPS 會保留內容並回報 conflict；不會猜測或覆寫使用者調整。

先確認 CLI 存在，再把實際安裝路徑加入目前 shell：

~~~bash
ls -l ~/.local/bin/aips
export PATH="$HOME/.local/bin:$PATH"
aips doctor
~~~

安裝完成但尚未重開 terminal 時，Installer 也會顯示可直接執行的絕對路徑。使用自訂 `AIPS_BIN_HOME` 時，請使用該目錄下的 `aips` 路徑：

~~~bash
"$HOME/.local/bin/aips" doctor
"$HOME/.local/bin/aips" harness status
~~~

若選擇手動管理，將相同的 `export PATH=...` 加入使用中的 `~/.zprofile`、`~/.zshrc` 或 `~/.bashrc`，然後開啟新的 terminal。若使用 `AIPS_BIN_HOME`，請把該值加入 `PATH`，不要照抄 `~/.local/bin`。

### `aips harness status` 顯示 `codex: NOT_DETECTED`

這通常表示安裝當下找不到 Codex CLI 的命令路徑；不代表 AIPS 核心 checkout、MCP 或 Python environment 安裝失敗。Codex 已安裝後重新執行：

~~~bash
aips harness install
aips harness status
~~~

macOS 的 ChatGPT app 內建 Codex 路徑會自動偵測。若 Codex 安裝在自訂位置，可在該次命令指定：

~~~bash
CODEX_CLI_PATH="/path/to/codex" aips harness install
~~~

成功時應看到 `codex: AUTOMATIC capability=CONTEXT_ALWAYS`。`enforcement=ADVISORY` 是 Codex adapter 的誠實能力標示，表示它提供持久指示，不攔截 Host 的每一個原生工具呼叫。

### Harness 已安裝但狀態仍是 `NOT_DETECTED`

先檢查目前使用的命令與設定，再重新安裝 adapter：

~~~bash
command -v codex
aips doctor
aips harness install
aips harness doctor
~~~

若 `command -v codex` 沒有輸出，使用上面的 `CODEX_CLI_PATH`；若 CLI 已在桌面應用程式內而沒有獨立 shell 命令，AIPS 仍可使用可驗證的 app 內建路徑完成 Codex managed block。

### `aips harness status` 顯示 `Harness: active` 但沒有自動載入？

`Harness: active` 只代表 AIPS Global Harness ownership manifest 存在；每個 runtime 的 adapter 狀態要個別看。只有 `codex: AUTOMATIC` 且 capability 為 `CONTEXT_ALWAYS`，才代表 Codex 全域 managed instruction 已完成。完成後請開啟新的 Codex 工作階段，讓新的全域指示鏈載入。

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
aips uninstall --remove-shell-integration
~~~

預設解除安裝會移除 AIPS CLI symlink，再移除未遭修改的 AIPS-owned shell block。若 CLI 目錄仍含其他工具，PATH block 會保留，避免讓其他命令失去可發現性；確定要移除時使用 `--remove-shell-integration`。使用者自行建立的 PATH 設定不在 AIPS ownership 內，不會被刪除。

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

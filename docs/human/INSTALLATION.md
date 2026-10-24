# 安裝、更新與解除

本機 ComfyUI profile 是 AIPS 內建 registry 資料；安裝與 discovery 不會下載權重，也不代表推論相容性已驗證。新增 profile 必須符合 executor 已審核的拓樸家族與本機已安裝元件清單。

本指南整理 AIPS 的安裝生命週期（Install / Update / Uninstall）。支援 macOS、Linux 與 Windows + WSL；目前不宣稱 Windows 原生 PowerShell／CMD runtime 已支援。AIPS 需要 Python 3.12 以上。

尚無可驗證的穩定版標籤時，安裝與更新會停止，不會自行改用開發分支。只有在你選擇追蹤可變動開發版時，才明確指定 `main`。

## macOS / Linux

Creative ComfyUI `dynamic_local` workflow support reuses the installed AIPS executor and Python dependencies. It does not install ComfyUI, custom nodes, model weights, or a remote service; the local ComfyUI API and selected model files must already be available. Workflow scan and preflight are read-only, while workflow import is an explicit project-confined create-only operation.

安裝完成後，可在 Agent runtime 設定 `AIPS_ENFORCE_REQUIRED_CHECKS=1`，讓 AIPS 獨立要求可讀取的 Required Checks policy 與全部通過；不設定時只停用 AIPS 自身的門檻，GitHub 原生保護與 Runtime Content Safety 仍各自生效。

Managed Runtime hooks keep content-safety and publication checks fail-closed. Remote publication diagnostics are read-only; timeout output omits raw commands and exception text.

~~~bash
(
  set -e
  installer="$(mktemp)"
  trap 'rm -f "$installer"' EXIT
  curl -fsSL --retry 3 --retry-delay 2 --connect-timeout 15 --max-time 60 --output "$installer" https://raw.githubusercontent.com/LucasLu3918/ai-product-system/main/scripts/install.sh
  test -s "$installer"
  bash "$installer" --configure-shell
)
~~~

安裝器會管理 AIPS system checkout、Python virtual environment、CLI 與支援的 Runtime 整合。預設安裝路徑為 `$XDG_DATA_HOME/aips/system`，若未設定 `XDG_DATA_HOME` 則使用 `~/.local/share/aips/system`。可用 `AIPS_INSTALL_DIR` 指定其他 system checkout 路徑。

`--configure-shell` 會在 zsh 或 bash profile 加入有明確 AIPS 標記的 `PATH` 區塊，方便新終端找到 `aips`。若你自行管理 shell 設定，改用 `--no-configure-shell`。

## Windows

目前支援 Windows + WSL。在 PowerShell 執行安裝器後，請從 WSL terminal 使用 AIPS：

~~~powershell
$installer = Join-Path ([IO.Path]::GetTempPath()) ("aips-install-" + [guid]::NewGuid().ToString("N") + ".ps1")
try {
  Invoke-WebRequest -Uri https://raw.githubusercontent.com/LucasLu3918/ai-product-system/main/scripts/install.ps1 -OutFile $installer -ErrorAction Stop
  if (!(Test-Path -LiteralPath $installer) -or (Get-Item -LiteralPath $installer).Length -eq 0) { throw "AIPS installer download was empty." }
  & $installer
} finally {
  Remove-Item -LiteralPath $installer -ErrorAction SilentlyContinue
}
~~~

只有在明確選擇開發版時才加上 `-Channel main`。PowerShell 啟動器會將安裝交給 WSL 中的 Linux installer；這不代表原生 PowerShell 已支援。

## 驗證

~~~bash
aips version
aips doctor
aips harness status
aips mcp inspect
~~~

`aips doctor` 檢查 system checkout、Python runtime、必要套件及本機命令。OpenAPI generator 等選用能力有獨立安裝流程，不會因未安裝而使基本 AIPS 安裝失敗。

維護者要驗證完整 repository 時使用 `aips validate`。一般安裝不會在使用者電腦執行完整 CI，也不會連線修改 GitHub repository 設定。

## Runtime integration

ComfyUI model profiles 隨 AIPS registry 提供；固定 FLUX 3 Klein 執行前會檢查本機 `TextGenerate` schema 與最終 payload。安裝與 discovery 不下載權重；schema 通過不代表 MPS 或實際推論相容。

Creative ComfyUI `dynamic_local` workflow support reuses the installed AIPS executor and Python dependencies. It does not install ComfyUI, custom nodes, model weights, or a remote service; the local ComfyUI API and selected model files must already be available. Workflow scan and preflight are read-only, while workflow import is an explicit project-confined create-only operation.

一般專案不會自動建立 `.ai/`。只有明確執行 `aips attach <project>` 才會使用 project-local state；若專案位於 Git worktree，AIPS 會在本機 `info/exclude` 排除 `.ai/` 與 detach 封存目錄，不修改專案 `.gitignore`。

OpenCode 原生直接寫入在 Project Intelligence 為 READY、但 freshness 為 STALE 時，可依既有 L2 advisory 邊界繼續；系統仍會明確顯示過期狀態。freshness 為 UNKNOWN、準備度不足、指示來源權限衝突未解或目標路徑越界時，仍維持原有停止條件。詳細 allow／deny 契約見 Scenario 267。

Commit 時的 AVIF 中繼資料掃描採用內建且有界的解析器，不需安裝額外套件，也不新增原生 Runtime adapter 需求。

安裝或更新後，以 `aips harness status` 檢視可辨識的 Runtime，再依 Host 提示使用 `aips harness install` 或 `aips harness doctor`。解除整合可使用 `aips harness uninstall`；只移除 CLI 時使用 `aips uninstall`。

不同 Agent 的 Context、工具權限與原生 Hook 能力並不相同。安裝狀態或靜態探測只能說明設定狀態；有版本綁定的 Host 驗收才可證明指定環境中的行為。Codex 的部分防護維持 ADVISORY，不能視為作業系統層級的隔離。

MCP 設定可用 `aips mcp config --client <client>` 預覽。該命令不會替你寫入 Cursor、Copilot、Amp、Codex 或其他 Host 設定。

## 常見問題與排查

### `aips: command not found`

若剛完成安裝，先開啟新的 terminal。若安裝時使用 `--no-configure-shell`，請自行將安裝器顯示的 CLI 目錄加入 `PATH)，或使用絕對路徑執行 `aips doctor`。

### Runtime 顯示 `NOT_DETECTED`

確認 Agent 已安裝，並使用支援的本機 Runtime 版本。執行 `aips harness status` 和 `aips harness doctor` 查看探測到的設定與可恢復問題；缺少 Host 時不會自動建立不存在的整合。

### 顯示 `Harness: active`，但 Host 沒有載入

`active` 表示 AIPS 找到受管理設定，不能證明 Host 已讀取或執行它。重新啟動 Host、確認目前工作階段使用的設定路徑，並依該 Runtime 的驗收方式確認 Context 或 Hook 實際生效。

### 安裝或更新找不到穩定版

此時不要讓安裝器默默改追蹤 `main)。若你要使用開發版，重新執行安裝器並明確指定 `--channel main`。安裝完成後，更新會追蹤該明確選擇的 channel。

### 更新因本機變更或版本差異停止

先保存並檢視 system checkout 內的本機變更。遇到 major version 更新時，先閱讀 `CHANGELOG.md)，再使用 `aips update --allow-major` 明確同意。AIPS 不會以自動 merge、rebase 或 rollback 猜測如何處理分歧。

## 更新

~~~bash
aips update
~~~

穩定版 channel 只接受版本標籤與目標 commit 均通過驗證的版本。若目前是 `main` 開發版 channel，更新會以 fast-forward 方式同步遠端；工作樹髒污、歷史分歧或驗證失敗會停止。

若已有程式專案需要更新 AIPS 並執行系統 preflight：

~~~bash
aips system preflight /path/to/project
~~~

相容入口 `aips preflight` 仍可使用。preflight 會先更新 AIPS system checkout，再檢查專案，不會替專案執行未知修復。

## 解除安裝

~~~bash
aips uninstall
~~~

解除安裝會移除 AIPS 管理的 Runtime 整合與 CLI 連結。Shell `PATH` 區塊只會在安全條件成立時移除；若設定遭使用者修改或安裝目錄還有其他程式，AIPS 會保留區塊並提示處理方式。

下列選項用於明確擴大清除範圍：

- `--remove-shell-integration`：要求移除 AIPS 管理的 shell 區塊。
- `--remove-venv`：移除 AIPS 管理的 Python virtual environment。
- `--remove-cache`：刪除外部 Project Intelligence 快取。

## 會保留什麼

一般解除安裝會保留 AIPS system repository、專案原始碼、使用者撰寫的 Agent 指示與 Skills、專案內的 `.ai/` workspace，以及外部 Project Intelligence 快取。未經明確選項要求，AIPS 不會清除這些專案知識或 Python 環境。

## 相容入口

`scripts/uninstall.sh` 與 `scripts/uninstall.ps1` 保留為相容／復原入口；新安裝請使用本指南的 Install 流程。舊版 `bootstrap.sh` 也只保留相容用途，不是新的主要入口。

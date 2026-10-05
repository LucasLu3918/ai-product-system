# 快速上手

## 安裝 AIPS

macOS / Linux：

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

Windows 使用支援的 WSL 路徑，在 PowerShell 執行：

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

不需要先手動 clone repository 或切換到 AIPS 目錄。

AIPS runtime 需要 Python 3.12 以上；若系統同時安裝多個 Python，可用 `AIPS_PYTHON=/path/to/python3` 指定建立受管理 virtual environment 的版本。使用 `aips doctor` 可檢查 runtime 版本與安裝狀態。

`--configure-shell` 會為 zsh 或 bash 寫入具有 AIPS ownership 標記的 `PATH` 區塊；若要自行管理 shell profile，改用 `--no-configure-shell`。安裝後尚未重開 terminal 時，可直接使用安裝器顯示的絕對路徑，或依 [安裝排查](INSTALLATION.md#常見問題與排查) 操作。

## 驗證安裝

驗證安裝更新時，除了主線 repository SHA，也需核對註冊的安裝版 SHA。從已更新的 AIPS checkout 執行 `./bin/aips publish post-merge --fetch --sync-installed --apply` 可安全快轉兩者；髒工作樹、不同遠端或分歧的安裝版會停止並回報。

~~~bash
aips version
aips doctor
aips harness status
aips mcp inspect
aips commands list
~~~

需要檢視 Agent 執行路徑時，可使用 `aips trajectory evaluate --trace <trace.yaml> --mode shadow`；這只產生 observable evidence，不會授予 Git Publish 權限。

維護 repository 時，使用 `aips docs impact --base origin/main` 與 `aips publish plan --base origin/main` 先確認 CI-parity requirements；這些命令不會自行 merge 或發布。

若要連接 MCP Host，可先用 `aips mcp config --client cursor|windsurf|copilot|amp|codex|generic` 檢視 review-only JSON；AIPS 不會自動修改 Host 設定。
需要跨 Host 使用治理工作流時，可先預覽或安裝 Portable Command projection：`aips commands render aips.plan --host cursor`、`aips commands install --host cursor`。生成檔案由 AIPS ownership 管理，使用者修改後會保留並回報衝突。

## 開始工作

平常直接開啟你的 Agent / IDE。AIPS 會依 Runtime 能力使用 native adapter 或 MCP access plane。

~~~text
你的需求
→ AIPS Context / Routing
→ 只載入需要的 Role / Skill
→ Planning / Implementation
→ Review / Validation
→ Human-controlled publication / production
~~~

## Existing Project

平行實作時，先由 Deterministic Scheduler 派送 Task Graph，再在 AIPS worktree 綁定 task owner。Owner 狀態、lease 與實際變更路徑可從 Run Dashboard 檢視；enforcement 只有在 runtime guard 經驗證後才會提升。

For parallel local work, `aips run dashboard` provides a read-only repository-scoped view of known runs on `127.0.0.1`; it cannot mutate, approve, merge or publish.

Concurrent AIPS event writers share an append lock and sequence allocator, so events remain ordered when more than one local operation records evidence for the same run.

不需要先建立 .ai/。EPHEMERAL mode 可直接工作；只有需要 project-local persistent state 時才：

~~~bash
aips attach /path/to/project
~~~

## 更新

安裝後預設追蹤穩定版；尚無穩定版標籤時安裝器會提示並暫從 `main` 啟動。需要開發版時可在初次安裝選擇 `--channel main`。

~~~bash
aips update
~~~

Existing Project mutation 前建議：

~~~bash
aips preflight /path/to/project
~~~

需要查詢歷史架構時，可使用 `aips intelligence temporal --mode as-of --revision <sha>`；一般任務不需要載入完整 temporal history。

`aips update` 與 `aips preflight` 會檢查 managed installation 的必要 Python dependencies，只有缺漏時才依 `requirements.txt` 修復；直接從一般 source checkout 執行時不會隱式建立 `.venv`。

## 解除安裝

~~~bash
aips uninstall
~~~

預設會移除未遭修改且不影響共用 CLI 目錄的 AIPS-owned shell block。User instructions、Skills、Project source、Project .ai/ 與 External Project Intelligence 仍會保留。

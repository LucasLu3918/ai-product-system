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
  bash "$installer"
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

AIPS runtime 需要 Python 3.10 以上；若系統同時安裝多個 Python，可用 `AIPS_PYTHON=/path/to/python3` 指定建立受管理 virtual environment 的版本。

安裝器不會自動改寫 shell profile；若終端機找不到 `aips`，請依 [安裝排查](INSTALLATION.md#常見問題與排查) 將實際 CLI 路徑加入 `PATH`。
在同一個 terminal 尚未更新 `PATH` 時，可直接使用安裝器顯示的絕對路徑執行 `doctor` 與 `harness status`。

## 驗證安裝

~~~bash
aips version
aips doctor
aips harness status
aips mcp inspect
~~~

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

不需要先建立 .ai/。EPHEMERAL mode 可直接工作；只有需要 project-local persistent state 時才：

~~~bash
aips attach /path/to/project
~~~

## 更新

~~~bash
aips update
~~~

Existing Project mutation 前建議：

~~~bash
aips preflight /path/to/project
~~~

`aips update` 與 `aips preflight` 會檢查 managed installation 的必要 Python dependencies，只有缺漏時才依 `requirements.txt` 修復；直接從一般 source checkout 執行時不會隱式建立 `.venv`。

## 解除安裝

~~~bash
aips uninstall
~~~

預設保留 User instructions、Skills、Project source、Project .ai/ 與 External Project Intelligence。

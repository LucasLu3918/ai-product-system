# AI Product System

AI Product System（AIPS）是一套跨 Agent 的 Software Engineering Harness。它把 Roles、Skills、Project Intelligence、deterministic orchestration、security / quality governance 與 MCP interoperability 組合成可重用的工程系統。

## Install

### macOS / Linux

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

`--configure-shell` 會為 zsh 或 bash 寫入具有 AIPS ownership 標記的 `PATH` 區塊；解除安裝可安全辨識並移除。若要自行管理 shell profile，改用 `--no-configure-shell`。

### Windows

正式支援路徑為 **Windows + WSL**。在 PowerShell 執行：

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

安裝後在 WSL terminal 使用 AIPS。

### Verify

~~~bash
aips doctor
aips mcp inspect
~~~

不需要先建立資料夾、cd 或手動 git clone；installer 會管理 AIPS system checkout。

## Start using AIPS

安裝完成後，直接使用原本的 Codex、Claude Code、Gemini CLI，或把 AIPS MCP Server 接到支援 MCP 的 Host。

~~~bash
aips harness status
aips mcp inspect
~~~

AIPS 不取代既有 AGENTS.md、CLAUDE.md、GEMINI.md 或 custom Skills；只管理自己的可逆 integration。

## Update

~~~bash
aips update
~~~

Existing Project mutation 前可使用：

~~~bash
aips preflight /path/to/project
~~~

## Uninstall

~~~bash
aips uninstall
~~~

預設移除 AIPS-owned shell integration；若 CLI 目錄仍有其他工具則保留 PATH 設定並提示。使用者 instructions、Skills、Project source、Project .ai/ 與 External Project Intelligence 仍會保留。

## Documentation

正式 Human Documentation source 位於 docs/human/，並由 VitePress 建置為 Official Docs Site。

- [開始使用](docs/human/GETTING_STARTED.md)
- [安裝與解除](docs/human/INSTALLATION.md)
- [使用指南](docs/human/USER_GUIDE.md)
- [Global Harness / MCP](docs/human/HARNESS.md)
- [系統架構](docs/human/ARCHITECTURE_OVERVIEW.md)
- [Technology Guide](docs/human/TECHNOLOGY_GUIDE.md)
- [文件導覽](docs/human/DOCUMENTATION_MAP.md)

Release history 放在 CHANGELOG.md；Scenario / verification history 放在 docs/human/CONFORMANCE.md，不混入 current-behavior 使用文件。

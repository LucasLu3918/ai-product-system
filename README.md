# AI Product System

AI Product System（AIPS）是一套跨 Agent 的 Software Engineering Harness。它把 Roles、Skills、Project Intelligence、deterministic orchestration、security / quality governance 與 MCP interoperability 組合成可重用的工程系統。

## Install

### macOS / Linux

~~~bash
curl -fsSL https://raw.githubusercontent.com/LucasLu3918/ai-product-system/main/scripts/install.sh | bash
~~~

### Windows

正式支援路徑為 **Windows + WSL**。在 PowerShell 執行：

~~~powershell
irm https://raw.githubusercontent.com/LucasLu3918/ai-product-system/main/scripts/install.ps1 | iex
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

預設保留使用者 instructions、Skills、Project source、Project .ai/ 與 External Project Intelligence。

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

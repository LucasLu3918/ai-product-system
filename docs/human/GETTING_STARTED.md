# 快速上手

## 安裝 AIPS

macOS / Linux：

~~~bash
curl -fsSL https://raw.githubusercontent.com/LucasLu3918/ai-product-system/main/scripts/install.sh | bash
~~~

Windows 使用支援的 WSL 路徑，在 PowerShell 執行：

~~~powershell
irm https://raw.githubusercontent.com/LucasLu3918/ai-product-system/main/scripts/install.ps1 | iex
~~~

不需要先手動 clone repository 或切換到 AIPS 目錄。

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

## 解除安裝

~~~bash
aips uninstall
~~~

預設保留 User instructions、Skills、Project source、Project .ai/ 與 External Project Intelligence。

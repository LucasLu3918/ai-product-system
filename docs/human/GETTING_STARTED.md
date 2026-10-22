# 快速上手

這份指南帶你完成安裝、確認整合狀態，並開始第一項工作。AIPS 需要 Python 3.12 以上；Windows 使用 WSL。首次安裝不需要先 clone repository。

## 安裝 AIPS

目前若尚無已驗證的穩定版標籤，安裝程式會停止並要求明確選擇開發版 `main`。安裝器會驗證版本標籤與目標 commit；不會在穩定版不可用時靜默改用可變動分支。

macOS / Linux：

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

Windows 請在 PowerShell 執行安裝器；核心 runtime 會在 WSL 中安裝與執行：

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

如要自行管理 shell 設定檔，將安裝命令中的 `--configure-shell` 改為 `--no-configure-shell`。需要指定 Python 時，設定 `AIPS_PYTHON=/path/to/python3`。

## 驗證安裝

~~~bash
aips version
aips doctor
aips harness status
aips mcp inspect
aips commands list
~~~

`aips doctor` 檢查受管理的 AIPS checkout、Python 環境、必要相依套件與可用整合。各指令顯示的靜態狀態不等同於已完成 Host 內的行為驗收。

要連接 MCP 主機時，先以 `aips mcp config --client cursor|windsurf|copilot|amp|codex|generic` 預覽設定。這項操作只輸出建議內容，不會代替你修改 Host 設定。Portable Command 可先用 `aips commands render <command-id> --host <host>` 預覽，再依需要安裝。

## 開始工作

開啟平常使用的 Agent 或 IDE，直接描述你想完成的目標、限制條件與驗收方式。AIPS 會依 Runtime 可用能力提供任務相關脈絡；Agent 再依工作內容進行規劃、實作與驗證。

~~~text
需求與驗收方式
→ 任務脈絡與工作模式
→ 只載入相關 Role / Skill / Protocol
→ 規劃、實作與驗證
→ 人工審查及授權的交付決策
~~~

必要時可參考[使用指南](USER_GUIDE.md)了解產品交付、品質審查、Git 發布與其他流程。

## Existing Project

已有程式專案時，先檢視目前狀態與恢復建議：

~~~bash
aips project diagnose /path/to/project
aips project check /path/to/project
~~~

修改前仍須依專案原生指示、Project Intelligence、新變更影響與驗收要求執行。診斷只提供狀態與下一步，不會替你附加專案、刷新知識或執行修復。

一般工作不需要先建立 `.ai/`。AIPS 可在 EPHEMERAL 模式使用外部快取；只有確定需要專案內保存可重用狀態時，才執行：

~~~bash
aips attach /path/to/project
~~~

`attach` 仍須明確執行才會建立 `.ai/`。若目標位於 Git worktree，AIPS 會把 `.ai/` 與 `.ai.detached-*` 加入該 worktree 的 `.git/info/exclude`，保留在本機，不修改專案 `.gitignore`。這只忽略尚未追蹤的路徑；原本已追蹤的檔案不會因此解除追蹤。

`aips system preflight /path/to/project` 會更新並驗證 AIPS system checkout。更新前先確認該專案的工作樹狀態與變更範圍。

## 更新

~~~bash
aips update
~~~

一般安裝追蹤經驗證的穩定版。若尚無可用的穩定版標籤，請依安裝器明確指定 `--channel main`；Windows WSL 安裝器對應使用 `-Channel main`。

更新只會管理 AIPS 自己的安裝與 Runtime 整合。髒工作樹、遠端不一致或無法驗證的版本會停止並顯示原因。

## 解除安裝

~~~bash
aips uninstall
~~~

解除安裝會移除 AIPS 管理的 Runtime 整合與 CLI 連結。Shell `PATH` 區塊僅在可安全移除時一併清除；使用者修改過的設定或含有其他程式的目錄會保留。使用者指示、Skills、專案原始碼、專案 `.ai/` 與外部 Project Intelligence 會保留；只有明確指定 `--remove-cache` 才會刪除外部快取。

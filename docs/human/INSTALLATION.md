# 安裝、更新與解除

AIPS 的 public lifecycle terminology 統一使用 **Install / Update / Uninstall**。bootstrap.sh 只保留為 backward-compatible wrapper，不再是新使用者文件的主要入口。

Evolution deterministic pre-analysis ships as an internal Python module with the existing AIPS checkout; it adds no separate installation step or dependency.

## macOS / Linux

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

Installer 會自行管理 AIPS system checkout、Python virtual environment、CLI 與可安全安裝的 Runtime integrations。`--configure-shell` 會在 zsh／bash profile 寫入可辨識、可逆的 AIPS-owned `PATH` 區塊；使用者不需要先建立目錄、cd 或手動 git clone。若要自行管理 profile，使用 `--no-configure-shell`。

Install/update 會透過目錄鎖避免併發寫入，並對 Git clone/fetch 做有限次重試。首次 clone 先寫入安裝路徑旁的暫存目錄，只有在 channel 與 commit 驗證完成後才會提升。若鎖資訊顯示 stale，先確認沒有其他 AIPS install/update 程序，再手動清除錯誤訊息指出的 lock directory。

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
  & $installer
} finally {
  Remove-Item -LiteralPath $installer -ErrorAction SilentlyContinue
}
~~~

PowerShell launcher 會把安裝交給 WSL 內相同的 Linux installer，因此核心 install lifecycle 只有一份。安裝後請在 WSL terminal 執行 AIPS。

預設 channel 為 stable；第一個已驗證 release tag 出現前，安裝會停止。若明確要安裝開發版，請執行 `& $installer -Channel main`；Linux/macOS shell installer 對應使用 `--channel main`。

> Windows native PowerShell / CMD runtime 若未來實作，必須另有真實 lifecycle evidence 後才可標記為 supported。

## 驗證

AIPS 不會安裝影像引擎或模型。若已自行設定本機 MFLUX 或 loopback ComfyUI，可用 `aips creative preflight` 檢查 Bundle；檢查不會產生影像。

安裝後可用 `aips trajectory evaluate --trace <trace.yaml> --mode shadow` 驗證 trajectory evidence CLI；此命令不需要外部 provider API key。

~~~bash
aips version
aips doctor
aips harness status
aips mcp inspect
aips project check /path/to/project
aips project diagnose /path/to/project --format text
~~~

`aips project diagnose` 只讀彙整 `aips doctor`、專案智慧、Runtime/Harness 設定與 MCP 靜態能力，並提供 recovery next steps。它不會自動建立或更新快取；原生 Host 效果也不會因設定存在而被標記為已驗證。

Maintainer 的發布前入口為 `aips docs impact` 與 `aips publish plan|preflight|post-merge`。一般使用者安裝不會自動執行 GitHub 查詢、重寫 branch 或取得 publication authority。

安裝流程本身會執行 **installation integrity validation**：確認必要 runtime dependency、核心 source contract 與 Human documentation placement 可用；它不會在一般使用者電腦重跑需要 Playwright/browser 等開發工具的完整 repository CI suite。

`aips doctor` 會檢查 system checkout、Python environment、必要的 PyYAML／MCP runtime dependencies、CLI、Harness 與 MCP availability；必要依賴不完整時會回傳失敗並提示重新執行 `aips install`。`aips update` 與 `aips preflight` 會在 managed installation 缺少必要依賴時自動依 `requirements.txt` 修復。Maintainer 若要執行完整 repository validation，使用 `aips validate`；正式 PR / main 仍以 GitHub Actions 的 Janitor / repository checks 為準。

OpenAPI tooling 是選用相依套件，不會隨基本安裝自動下載。使用前執行 `aips openapi doctor`；若狀態為 `NOT_INSTALLED`，明確執行 `aips openapi install`，由 AIPS managed venv 安裝 `requirements-openapi.txt` 中的固定版本。基本 `aips doctor` 會顯示此選用能力狀態，但缺少它不會使一般 AIPS 安裝失敗。完成後可在產品 repository 執行 `aips openapi validate <spec> --repo-root .`。

Project Intelligence 的 temporal query 使用既有本機 CLI 與 Git，不需要額外安裝 Neo4j、外部資料庫或 provider credential。

- Stable release readiness additionally requires exactly one empty `## Unreleased` section; installers continue to require a verified stable tag.
## Runtime integration

選用 Z-Image Turbo 時，另外確認本機 MFLUX 提供 `mflux-generate-z-image-turbo` 且模型、tokenizer 權重完整；AIPS 安裝不會替你下載模型。

產圖流程新增 discover/configure，不安裝引擎或下載模型。更新 canonical AIPS 後重新執行 Harness 安裝並重啟 OpenCode，新 plugin 與創作 skill 才會重新投影；使用者自行修改的投影仍依 ownership 規則保留。

OpenCode V2 可提供受限的 creative execution tool；它只在明確創作／修改意圖下先做 preflight，再呼叫本機設定的引擎。

OpenCode's bounded creative tool uses the installed local AIPS runtime and does not install MFLUX, ComfyUI, or model weights. `prepare` only creates versioned local Profile/Bundle files; configure an already installed engine before preflight or explicit execution.

The ComfyUI Z-Image Turbo profile requires already-installed UNET, Qwen CLIP and VAE weights; `aips creative preflight` verifies their local API inventory without generating an image.

OpenCode 安裝流程自動偵測執行檔，建立受管理全域 `AGENTS.md`、Skills、三個 `aips-*` Commands；確認 V2 後另安裝受管理 AIPS plugin。設定根目錄依 `OPENCODE_CONFIG_DIR`、`XDG_CONFIG_HOME` 或預設 `~/.config/opencode`；既有同名或改動過的檔案保留並回報 CONFLICT。稍後安裝 OpenCode 可重新執行 `aips harness install`；MCP 另以 `aips mcp config --client opencode` 預覽。

執行 `aips harness doctor` 可檢查版本相容、投影完整性、Host discovery 與 Hook 執行證據。若 Plugin 更新後需重新載入，Doctor 會提示重跑 install、重啟 OpenCode 並建立新 Session；安裝和檔案存在不會被當成 Hook 已執行。V1 不會安裝 V2 Plugin，未知版本保留使用者設定並回報衝突。

Run Dashboard output continues to use the existing read-only projection contract; the shared canonical helper changes no installed runtime or persisted state.

安裝的 Runtime adapter 讀取固定 `SYSTEM_CORE.md` 和 Turn Context 的 task-specific protocol pointers；`SYSTEM.md` 相容入口仍保留，更新流程不得把完整 orchestration 文件加入常駐 context。

本次新增的治理 snapshot 不增加安裝相依；只有 operator 主動執行時才使用既有 `gh` CLI 與其登入狀態。

The public `bin/aips` entrypoint remains a thin launcher. Its resolved checkout contains `scripts/aips_cli.sh` and the `scripts/aips_cli/` implementation modules; installed symlinks resolve those modules relative to the installed AIPS checkout, regardless of the caller working directory.

Publication post-merge reconciliation 拆至 `scripts/publish_post_merge.py`，由既有 CLI facade 呼叫；使用相同 Python/Git runtime，不增加安裝步驟或相依套件。

Retrieval relation extraction uses the existing Python runtime and standard library; splitting its internal implementation adds no installation step or dependency.

Temporal query 使用既有 `aips intelligence temporal` 入口與 Python/Git runtime；實作拆至內部 adapter 不增加安裝步驟或相依套件。

AIPS runtime 最低支援 Python 3.12。PR 主 Gate 使用 Python 3.12；每週相容性 smoke workflow 驗證 Python 3.12、3.13、3.14。支援與測試版本由 `config/system-facts.yaml` 維護，並同步至 `pyproject.toml` 與本頁系統參考。Installer 會選擇 Python 3.14、3.13、3.12 或相容的 `python3`；需要指定解譯器時可設定 `AIPS_PYTHON=/path/to/python3`。低於 3.12 的 AIPS-owned `.venv` 會在 install／update／preflight 修復時重建；`aips doctor` 會指出不支援的 runtime 與修復方式。

Task ownership CLI 隨 AIPS CLI 一併提供，不需額外 runtime 套件。啟用前需建立 AIPS 管理的 Git worktree isolation；在不支援 native write guard 的 runtime，資源授權結果會明確維持 advisory。

The optional `aips run dashboard` command uses the existing Python runtime and loopback-only HTTP server; it adds no database, frontend dependency chain or mutation endpoint.

Validation installs the pinned `cryptography` dependency used to verify Ed25519 review receipts against trust anchors supplied outside the project checkout. No issuer is trusted by default.

安裝後可使用 `aips commands list` 檢視 Portable Command Registry；`aips commands render` 只預覽，`aips commands install --host <id>` 才建立 AIPS-owned projection。這些 projection 不會自動修改 Client-owned MCP 設定，也不提供 Runtime-native enforcement。
Native Runtime Adapter 與 MCP 是兩個互補平面：

- Codex / Claude Code / Gemini CLI：依可驗證能力安裝 AIPS-owned integration。
- MCP-compatible Host：可使用 `aips mcp serve`；以 `aips mcp config --client cursor|windsurf|copilot|amp|codex|generic` 產生 review-only 設定。
- MCP-only governance enforcement 仍為 ADVISORY；native pre-tool hook 才能提供已驗證的 stronger enforcement。

產生設定只會輸出 JSON，不會寫入或覆蓋第三方 client-owned configuration；使用者確認後再依 Host 文件安裝設定。

細節放在 [Global Harness 與 MCP](HARNESS.md)，不在 Installation 頁重複 implementation 細節。

## 常見問題與排查

`--source-checkout` 接受 Git 根目錄的 clone 或 linked worktree，安裝使用其已提交 HEAD；子目錄及非 AIPS 根目錄會拒絕。macOS Bash 3.2 的無選項安裝有獨立覆蓋。套件安裝回報 HTTP、proxy、DNS、TLS 或套件解析分類，不輸出可能含憑證的原始套件索引訊息；HTTP 403 應先查套件來源權限，不應直接重新登入 GitHub。

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

Managed installations use the stable channel by default and require a verified `vX.Y.Z` release tag. Before the first stable release is published, initial installation and updates stop without falling back to mutable `main`; use `--channel main` only when you explicitly want the development branch. The installer records the selected channel so later `aips update` follows the same policy. Release candidates can be checked with the read-only `release-readiness` workflow; publishing a tag remains a separate explicitly approved step.

~~~bash
aips update
~~~

AIPS 只在 managed system checkout clean、history 可 fast-forward 時自動更新；major version 變更仍需要顯式處理。

Existing Project mutation 前：

~~~bash
aips system preflight /path/to/project
~~~

`aips preflight /path/to/project` remains a backward-compatible alias. `aips project check /path/to/project` is read-only and reports attachment mode plus Project Intelligence freshness (`CURRENT`, `STALE` or `UNKNOWN`); it does not refresh or attach the Project.

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

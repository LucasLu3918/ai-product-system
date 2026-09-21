# 安裝與解除

AIPS v0.9 的安裝目標是：安裝一次，之後正常開 Agent 使用，不需要每次先執行 AIPS 指令。

![AIPS 安裝與生命週期](assets/system-lifecycle.svg)

## 安裝

~~~bash
mkdir -p ~/Developer
cd ~/Developer
gh repo clone LucasLu3918/ai-product-system
cd ai-product-system
./scripts/bootstrap.sh
~~~

安裝會 Validate AIPS、建立 CLI、偵測 Runtime、安裝/刷新可逆 Integration 並記錄 Ownership。

## Codex

若 `~/.codex/AGENTS.md` 已存在，AIPS 不取代它，只加入自己的 AIPS Managed Block。Capability 預期為 `CONTEXT_ALWAYS`。

## Claude Code

保留既有 `~/.claude/CLAUDE.md`，加入 AIPS Managed Block；在 `~/.claude/settings.json` 可安全解析時加入 AIPS `UserPromptSubmit` Hook。成功時 `TURN_NATIVE`，Hook 不可用但 block 可用時降為 `CONTEXT_ALWAYS`。

## Gemini CLI

使用 `aips-global-harness` Extension + `BeforeAgent` Hook；驗證成功時為 `TURN_NATIVE`。

實際狀態：

~~~bash
aips harness status
aips harness doctor
~~~

## EPHEMERAL

沒有 `.ai/`。AIPS 不修改 Project Workspace；Project Intelligence 可存在 `~/.config/aips/projects/<project-id>/intelligence/`。

## ATTACHED

~~~bash
aips attach /project
~~~

External Intelligence 會 validated migrate 到 `.ai/intelligence/`。Detach 會先 sync Intelligence 回 External Cache，再封存 `.ai/`。

## Update / Preflight

`aips preflight /project` 只更新 AIPS System，不更新 Product Git branch。v0.9 Harness refresh 只更新 AIPS-managed block/hook/extension。

## Uninstall

~~~bash
aips uninstall
~~~

移除 AIPS CLI、Managed Blocks、Claude Hook、Gemini Extension 與 Harness ownership/config。

預設保留 User instructions、Skills、Project source、Project `.ai/`、External Project Intelligence、AIPS repo 與 `.venv`。

只有明確：

~~~bash
aips uninstall --remove-cache
~~~

才移除 External Project Intelligence。要一起移除 `.venv`：

~~~bash
aips uninstall --remove-cache --remove-venv
~~~

## Modified Managed Block

如果使用者改過 AIPS Managed Block，Uninstall 會保留並報 Conflict，不會誤刪可能已屬於使用者的新內容。

## Project Intelligence

External Intelligence 被視為使用者累積的工作資料，因此預設 Uninstall 保留。Project-local `.ai/intelligence/` 也不會因 AIPS Uninstall 被刪除。

## v0.11 Governance Guard

安裝／刷新 Harness 時，Claude Code 在可安全修改 settings.json 的情況下會加入 AIPS-owned `PreToolUse` Bash guard；Gemini Extension 會註冊 `BeforeTool` guard。Uninstall 只移除 AIPS 自己的 hook。

`aips harness status` 會分開顯示 context capability 與 governance enforcement，避免把「能看到規範」誤認成「能技術阻擋」。

## MCP 接入

AIPS 安裝後會一起安裝官方 MCP Python SDK v2，因此本機可直接執行：

~~~bash
aips mcp inspect
aips mcp serve
~~~

v0.52 **不自動修改第三方 MCP Client 設定**。要接 Cursor / Codex 等 Client，先取得 review-only 範例：

~~~bash
aips mcp config --client cursor
aips mcp config --client codex
~~~

確認後再由你加入該 Client 自己的設定。這樣 AIPS Uninstall 不需要猜哪些第三方設定仍屬於使用者。

### MCP 解除

若曾手動把 `aips mcp serve` 註冊到 Cursor / Codex / 其他 Host，先從該 Host 移除那筆 AIPS MCP registration；接著正常執行 `aips uninstall` 即可移除 AIPS CLI / Harness-owned integrations。

v0.52 不會自動刪除 client-owned MCP config；既有 User instructions、Skills、Project source、Project Intelligence 仍依原本 preservation policy 保留。

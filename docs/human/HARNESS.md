# Global Harness 與 MCP

AIPS 的 Agent integration 分成 **Portable MCP Access Plane** 與 **Runtime-native Adapter Plane**。兩者讀取相同 canonical AIPS sources，但責任不同。

## Integration model

~~~text
AIPS Core
├─ MCP Access Plane
│  ├─ Resources
│  ├─ Prompts
│  └─ deterministic Tools
└─ Native Adapter Plane
   ├─ turn context
   └─ runtime-specific pre-tool guard
~~~

## Native Runtime Adapters

### Codex

以 persistent managed instruction 提供 CONTEXT_ALWAYS；安裝器會先檢查 `codex` 命令，再檢查 `CODEX_CLI_PATH`、`AIPS_CODEX_CLI_PATH` 與 macOS ChatGPT app 內建路徑。治理強度依實際可驗證能力回報，不因 MCP 存在而升級。

### Claude Code

可安全安裝時使用 UserPromptSubmit + PreToolUse；成功驗證後可提供 TURN_NATIVE / TOOL_GUARDED。

### Gemini CLI

使用 AIPS extension 的 BeforeAgent / BeforeTool。Runtime-specific observable-event capture 仍是獨立、受限、可驗證的 capability。

## MCP Interoperability

~~~bash
aips mcp inspect
aips mcp serve
~~~

MCP Resources 以 progressive disclosure 提供 Roles、Skills 與 selected orchestration；Prompts 組合 review/planning context；Tools 只暴露 bounded deterministic helpers。若 Host 只支援 Tools，可透過 `aips_capability_catalog`、`aips_capability_read`、`aips_workflow_context` 取得同一份 canonical 內容，不複製 Role／Skill registry，也不在 Server 內呼叫第二個模型。

所有 AIPS MCP Tools 都是無副作用操作，並宣告 read-only、non-destructive、idempotent、closed-world hints。這是目前 gateway 的契約描述，不等於 Host native tool guard。

新 Host 預設先使用 MCP。只有當該 Runtime 提供可驗證的 per-turn hook、pre-tool guard 或 runtime-specific event source，而且需求無法由 MCP 滿足時，才增加 native adapter；不能只因新增一個 Host 名稱就複製 adapter。

Review-only config 支援 Cursor、Windsurf、GitHub Copilot CLI、Amp、Codex 與 generic stdio。GitHub-hosted Copilot agent／code review 僅能使用 Tools，且執行環境必須真的能啟動 AIPS command；本機絕對路徑不能假裝成 hosted deployment。

`aips mcp inspect` 會輸出 machine-readable Host 相容性矩陣，區分 official config contract、MCP protocol、pinned CLI registration 與尚未執行的第三方 GUI。設定格式與協定驗證不能被表述成 GUI 實機驗證，也不包含 native guard。

MCP Server 不呼叫第二個 LLM，也不取得 Human approval、Git publish、merge、release、production 或 host-native tool interception authority。

## Capability truth

- AUTOMATIC：integration 安裝狀態。
- CONTEXT_ALWAYS：persistent instruction 每個工程 Turn 都要求取得 AIPS context。
- TURN_NATIVE：Runtime 有可驗證 per-turn native hook。
- TOOL_GUARDED：Runtime 有可驗證 pre-tool guard。
- ADVISORY：規範可見，但不能宣稱技術攔截所有 Host native tools。

`aips publish preflight` 是 repository publication／CI consistency 層，不是 MCP 或 native Harness capability；它不提升上述治理強度，也不取得 push、merge 或 release authority。

## Progressive disclosure

同步路徑只解析 identity、freshness、indexes 與 relevant pointers；重型 Project bootstrap、site build、semantic enrichment 不放進 hot path。

## Ownership 與解除

AIPS 只修改自己可辨識、可逆的 Managed Block / Hook / Extension。若內容被使用者修改到無法安全識別，uninstall 會保留並回報 conflict，不會暴力刪除。

Client-owned MCP config 不由 AIPS 自動寫入或刪除。

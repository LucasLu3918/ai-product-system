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

MCP Resources 以 progressive disclosure 提供 Roles、Skills 與 selected orchestration；Prompts 組合 review/planning context；Tools 只暴露 bounded deterministic helpers。

MCP Server 不呼叫第二個 LLM，也不取得 Human approval、Git publish、merge、release、production 或 host-native tool interception authority。

## Capability truth

- AUTOMATIC：integration 安裝狀態。
- CONTEXT_ALWAYS：persistent instruction 每個工程 Turn 都要求取得 AIPS context。
- TURN_NATIVE：Runtime 有可驗證 per-turn native hook。
- TOOL_GUARDED：Runtime 有可驗證 pre-tool guard。
- ADVISORY：規範可見，但不能宣稱技術攔截所有 Host native tools。

## Progressive disclosure

同步路徑只解析 identity、freshness、indexes 與 relevant pointers；重型 Project bootstrap、site build、semantic enrichment 不放進 hot path。

## Ownership 與解除

AIPS 只修改自己可辨識、可逆的 Managed Block / Hook / Extension。若內容被使用者修改到無法安全識別，uninstall 會保留並回報 conflict，不會暴力刪除。

Client-owned MCP config 不由 AIPS 自動寫入或刪除。

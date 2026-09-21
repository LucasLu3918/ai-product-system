# Global Harness 與 Turn-Aware Adapter

AIPS v0.9 的目標是：安裝一次後照原本方式使用 Codex / Claude Code / Gemini CLI；工程相關詢問自動取得 AIPS、使用者原本規則、Project 規則與 Project Intelligence。

![AIPS Global Harness](assets/harness-overview.svg)

## Same Harness Contract, runtime-native implementation

~~~text
User Prompt
→ Runtime-native mechanism
→ Compact Turn Context
→ Runtime/User + Project + Intelligence + AIPS
→ Agent Planning
~~~

### Codex

採 CONTEXT_ALWAYS。AIPS 在既有 `~/.codex/AGENTS.md` 內加入可逆 Managed Block，不取代原內容。

### Claude Code

優先使用 UserPromptSubmit Hook 提供 TURN_NATIVE，同時保留 Managed CLAUDE block 作 fallback；Hook 無法安全安裝時可降為 CONTEXT_ALWAYS。

### Gemini CLI

使用 namespaced AIPS Extension + BeforeAgent Hook，驗證成功時為 TURN_NATIVE。

## Status 與 Capability 分開

`AUTOMATIC` 表示 integration 已安裝；TURN_NATIVE / CONTEXT_ALWAYS 才描述每 Turn 能力。

## 每 Turn 不等於每 Turn重掃 Repository

同步路徑只做 identity、freshness quick check、Index / Source Registry 與 relevant pointers；重型 Bootstrap / HTML regeneration 不放在 Hook 裡。

## Runtime-aware Context Dedup

SOURCE_REGISTRY 記錄哪個 Runtime 已 native-load 哪些 Source。Storage 去重與 Runtime Context 去重分開處理。

## Fail Policy

一般對談 fail-soft；Existing Project mutation 缺必要 Instructions / Intelligence / Impact 時，對該 edit fail-closed。

## Ownership

AIPS 只管理自己的 Managed Block、Claude Hook、Gemini Extension。External Project Intelligence 預設保留。

## Governance Enforcement

v0.11 將「Context 是否能在每個 Turn 載入」與「是否能在 Tool 執行前阻擋」拆成兩個能力。

- Codex：目前以 `ADVISORY` 為安全預設。
- Claude Code：AIPS 同時組合 UserPromptSubmit 與 PreToolUse；兩者安裝成功時可回報 `TOOL_GUARDED`。
- Gemini CLI：Extension 使用 BeforeAgent + BeforeTool；驗證成功時可回報 `TOOL_GUARDED`。

第一階段只攔截 Git publication 類操作。Guard 只驗證 Approval Record，不取代 Human 決策。

## Gemini CLI AfterTool 可觀測事件 Trial

Gemini CLI adapter 現在多了一個 **opt-in** 的 `AfterTool` capture hook，作為 Scenario 142 的 runtime-specific Trial。

目前只監看：

- `read_file`
- `write_file`
- `replace`

而且預設關閉。只有同時設定 `AIPS_OBSERVABLE_EVENT_CAPTURE=1` 與明確的系統暫存路徑 sink 才會寫入 canonical metadata。

Hook 不保存 `tool_input`、`tool_response`、prompt、response、private reasoning 或 secret；capture 錯誤只降低 evidence completeness，不會 deny 或改寫 Gemini CLI 原本的 tool result。需要注意：Gemini CLI 的 hook 機制是同步等待，因此這不是「零 latency blocking」；Trial 明確記錄 `synchronous_hook=true` / `latency_path=synchronous`。未啟用 capture 時 shell wrapper 直接 allow，不啟 Python。

目前 CI 驗證的是官方 `AfterTool` input contract 與 extension wiring，尚未執行真實 Gemini CLI binary，所以仍為 `live_capture_verified=false`。

## Gemini CLI 真實執行階段驗證

Scenario 143 不再只 replay AfterTool-shaped JSON，而是由 CI 安裝固定的官方 Gemini CLI v0.60.0，link AIPS extension，讓 bundled CLI 真的執行 `read_file`、`write_file`、`replace`。

為了保持 deterministic 且不需要 Gemini API credential，model response 使用 Gemini CLI 官方 `--fake-responses` 測試介面。這仍是 **real CLI / real tool / real hook**，但不是 live provider inference。

Extension manifest 也正式宣告：

- `AIPS_OBSERVABLE_EVENT_CAPTURE`
- `AIPS_OBSERVABLE_EVENT_CAPTURE_SINK`

讓 Gemini CLI 的 extension environment sanitization 能合法傳遞這兩個非祕密控制值。

## Gemini Live Provider Session Gate

v0.34.0 已驗證真實 Gemini CLI / tool / extension hook，但 provider inference 仍是 fake-response。下一個 gate 必須把 provider credential 與未 merge 的 PR 程式碼隔離。

Human 已批准 bounded live-provider Trial，但目前 durable state 仍是 `PENDING_SECURE_PROVIDER_WORKFLOW`。只有受保護 main 上的 secret-backed verification 成功後，才可把 `live_provider_session_verified` 或 `provider_model_execution_verified` 設為 true。

## MCP 互通閘道

v0.52 將 Global Harness 拆成兩個互補接入平面：

~~~text
MCP-compatible Host
→ AIPS MCP（通用標準接入）
→ Resources / Prompts / deterministic Tools

有原生 Hook 的 Runtime
→ AIPS Native Adapter（能力補強）
→ TURN_NATIVE / PreTool Guard / TOOL_GUARDED
~~~

因此 Cursor、Copilot、Amp 或其他 MCP Host 不必先等 AIPS 為它們複製一整套 Role/Skill adapter，就能取得標準 AIPS 能力；但 MCP 本身不會因此取得 Host-native tool interception。

### 啟動與檢查

~~~bash
aips mcp inspect
aips mcp serve
~~~

`serve` 使用本機 stdio；MCP Server 不呼叫另一個 LLM，也不需要 OPENAI_API_KEY / GEMINI_API_KEY。

### Resources

先列 compact catalog，再按需讀取 `aips://roles/{role_id}`、`aips://skills/{skill_id}` 與 allowlisted `aips://protocol/{protocol_id}`。Role / Skill 仍只有一份真實來源，不會複製成 MCP 專用版本。

### Prompts 與 Tools

第一版 Prompts 包含 `security_review`、`architecture_review`、`code_review`、`delivery_plan`；真正的語意推理仍由 Host Model 執行。Tools 只暴露 bounded deterministic/read-only helper：`aips_system_info`、`aips_project_identity`、`aips_harness_context`、`aips_role_skill_bundle`、`aips_schedule`。

專案工具只允許 `AIPS_MCP_WORKSPACE` 範圍內路徑；`aips_role_skill_bundle` 只驗證明確給定的 ID，不假裝做語意選角。

### Client 設定

~~~bash
aips mcp config --client cursor
aips mcp config --client codex
aips mcp config --client generic
~~~

這些指令只輸出建議設定，不會偷偷修改 Cursor / Codex / 其他客戶端的設定檔。

### Governance truth

MCP-only 時 context access = `MCP_STANDARD`、governance enforcement = `ADVISORY`。MCP 一般不能攔截 Host 自己直接執行的 shell/file/git tool，因此 Claude/Gemini 等既有可驗證 native hooks 仍有獨立價值。

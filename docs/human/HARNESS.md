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

## Gemini CLI real-runtime capture verification

Gemini CLI observable-event capture 已從「只有 contract / fixture 驗證」提升到 narrow runtime verification。

Required CI 會安裝固定的 Gemini CLI v0.60.0，link AIPS extension，透過官方 `--fake-responses` 讓真正的 CLI 執行 `read_file / write_file / replace`，並檢查 AfterTool sink。

因此目前可以對這個明確範圍報告：

- real Gemini CLI binary execution：verified；
- AIPS extension loading：verified；
- real file-tool execution：verified；
- AfterTool live capture：verified；
- provider-backed Gemini model/API：未驗證。

Capture 仍預設關閉，也仍是 synchronous / non-enforcing；`decision=allow` 不具有 result-flow、remediation 或 Protected Human Authority。


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

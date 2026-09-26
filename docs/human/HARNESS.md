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

Runtime Policy 可由 PreToolUse 對 hook 收到且可正規化的動作執行 deny-by-default 檢查；命令列分類不代表可攔截 child process 或網路 socket。

### Gemini CLI

使用 AIPS extension 的 BeforeAgent / BeforeTool。Runtime-specific observable-event capture 仍是獨立、受限、可驗證的 capability。

BeforeTool 可執行相同的受支援 Runtime Policy 檢查；Codex 與不支援的 generic runtime 不宣稱強制執行。

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

Temporal Project Intelligence 的 historical query 由既有 deterministic CLI／Project Intelligence layer 提供；MCP 與 Runtime adapter 只傳遞 bounded context，不新增 Temporal Role、Gate 或 host-native authority。

## Capability truth

Runtime isolation behavior is reported only at the boundary supported by its registered evidence. Scenario Conformance inventory counts must be updated together with isolation lifecycle tests; registration does not prove that an unverified environment is isolated.

Repository Integration Gate commands run under the selected AIPS Python runtime, and test checks can bind an expected collected-test count so a no-op subprocess cannot masquerade as lifecycle evidence.

Trajectory Quality Gate 是 provider-neutral capability。Harness 可提供 observable events，但不應傳遞 private reasoning、secret 或 credential；評估結果仍由既有 Scenario Conformance 與 Human Authority 流程處理。

- AUTOMATIC：integration 安裝狀態。
- CONTEXT_ALWAYS：persistent instruction 每個工程 Turn 都要求取得 AIPS context。
- TURN_NATIVE：Runtime 有可驗證 per-turn native hook。
- TOOL_GUARDED：Runtime 有可驗證 pre-tool guard。
- ADVISORY：規範可見，但不能宣稱技術攔截所有 Host native tools。

`aips publish preflight` 是 repository publication／CI consistency 層，不是 MCP 或 native Harness capability；它不提升上述治理強度，也不取得 push、merge 或 release authority。每個 Remote Git 候選仍必須通過 credential-free strict secret scan，涵蓋 final tree 與完整 `base..head` commit history；worktree 或 sandbox 隔離不能取代這項檢查。

`aips isolation resolve --mode auto` is an execution-isolation resolver exposed through the existing CLI. It selects worktree for ordinary risk and requires verified sandbox capability for high/critical or untrusted execution; this is not a new Runtime adapter capability. The initial E2B registry stays disabled and its optional smoke workflow does not receive project source.

Independent review uses the canonical Scheduler and Integration Gate contracts through the existing runtime surfaces. The capability is implemented but PR enforcement is currently disabled in the active Core Change Matrix. Harness does not provide reviewer attestation itself: without a trusted runtime verifier, explicitly required evidence remains `UNVERIFIED` and blocks the Gate.

Runtime Content Safety Boundary 只在 AIPS-owned sink 或已驗證 native hook 上宣稱強制能力；MCP-only 或 unsupported host tools 維持 ADVISORY。安全掃描不會取得 Host-native tool interception 或 Human Authority。

## Progressive disclosure

Repository mutation workflows resolve AIPS Turn Context before analysis, then use targeted intelligence refresh and Change Impact evidence before editing; commit-time publication gates additionally enforce public-repository identity and content-safety policy.

同步路徑只解析 identity、freshness、indexes 與 relevant pointers；重型 Project bootstrap、site build、semantic enrichment 不放進 hot path。

## Ownership 與解除

AIPS 只修改自己可辨識、可逆的 Managed Block / Hook / Extension。若內容被使用者修改到無法安全識別，uninstall 會保留並回報 conflict，不會暴力刪除。

Client-owned MCP config 不由 AIPS 自動寫入或刪除。

## Portable Commands

The read-only `aips run dashboard` is a repository-scoped observation consumer and does not install a host integration or add mutation authority.

Portable Commands 將同一個 Canonical ID（例如 `aips.plan`）渲染成 Slash Command、Skill 或 generic MCP bootstrap。Registry 位於 `harness/commands/REGISTRY.yaml`，CLI 可檢視、預覽與管理 AIPS-owned projections：

~~~bash
aips commands list
aips commands render aips.plan --host cursor
aips commands install --host cursor
aips commands status
~~~

這些 projections 是薄包裝，不取代 Constitution、System 或 orchestration canonical sources，也不提供 Runtime-native enforcement、Git publish、merge、release、production 或 Human approval authority。使用者修改過的 projection 會保留並回報 `CONFLICT`。

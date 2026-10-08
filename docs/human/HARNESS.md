# Global Harness 與 MCP

AIPS 的 Agent integration 分成 **Portable MCP Access Plane** 與 **Runtime-native Adapter Plane**。兩者讀取相同 canonical AIPS sources，但責任不同。

本機 CLI 與 Runtime adapter 共用 checkout-root-aware 的 AIPS commands。`aips integration-gate` 使用已準備好的 Python 3.12 驗證環境；Publication Preflight 對文件候選直接呼叫已安裝的 VitePress bundle，不會自動安裝套件或連接 registry。

Runtime Context 統一解析驗證 Python 與 cache/config 路徑；它將 Playwright 套件、瀏覽器執行檔和實際啟動驗證分開回報，也不會宣稱未驗證的 sandbox 能力。

## Integration model

Runtime resolution keeps machine-readable results on stdout and diagnostics on stderr. Invalid adapter-state YAML is reported as an error; an unavailable Intelligence subprocess has a stable reason code instead of being confused with a successful empty result.

Standalone and shadow dependency-review artifacts retain exact base/head, run ID, actual JSON findings and outcome for 90 days. Parity compares canonical findings; missing outputs, different candidates or inaccessible artifacts stay UNKNOWN. Job success alone cannot promote the shadow. Record resolved toolchain fingerprints and repeat full Gates only for new changes or unresolved failures.

The public `bin/aips` command remains a thin launcher into the checkout-resolving `scripts/aips_cli.sh` facade. That facade loads the Harness, runtime, command and other shell modules from `scripts/aips_cli/` before dispatch, keeping installed symlink and source checkout behavior aligned.

Runtime resolution keeps machine-readable results on stdout and diagnostics on stderr. Invalid adapter-state YAML is reported as an error; an unavailable Intelligence subprocess has a stable reason code instead of being confused with a successful empty result.

GitHub-hosted maintenance workflows remain owned by repository CI outside a local Agent task or worktree lease. When they reconcile one monthly Issue, a repository/cohort queue preserves same-period runs without adding token scope or publication authority.

The Evolution pre-analysis module is an internal deterministic helper behind its existing CLI; it adds no Runtime Adapter, MCP tool, or Host integration.

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

### OpenCode

安裝時自動偵測 `opencode`，在設定根目錄建立受管理 `AGENTS.md`、27 個 canonical Skills 投影、三個原生 Commands；只在確認 OpenCode V2 後才安裝 `plugins/aips-opencode.ts`。description 由 Skill frontmatter 維護；相對 canonical 參照轉為已安裝 AIPS 路徑，其他資源依 canonical source directory 解析。

`aips harness install` 更新未遭使用者修改的投影；`aips harness doctor` 與 `python scripts/opencode_skill_projection.py check` 檢查 drift。重名、修改過的檔案、symlink、錯誤 manifest 均保留並回報衝突；解除安裝只移除已記錄且未改動的資源，失敗保留 ownership 供重試。使用者 JSON/JSONC、模型設定及專案內容保留。

MCP 使用 `aips mcp config --client opencode` 產生 v2 `mcp.servers.aips` 預覽；v1 使用 `--opencode-version 1`。預覽的 `AIPS_MCP_WORKSPACE` 固定為產生時的工作目錄，須依專案審閱後自行註冊。基本安裝不寫入 MCP 設定。

V2 Plugin 依每個 Session 的實際目錄解析 Harness 與 Project Intelligence；Context 大小上限為 12,000 bytes，寫入授權前會對目標路徑重查。`aips harness doctor` 分開回報投影、版本、Host discovery 與 Hook 執行狀態，並提示需要的安裝／重啟步驟。安裝成功仍不代表 Context 送達模型或 permission hook 已驗證。

EPHEMERAL 創意工作會唯讀掃描圖片與 SVG 的路徑、格式及檔案中繼資料，快取存放在專案外的使用者快取，且不建立 `.ai/`。可用 `aips creative scan --project PATH` 更新素材索引，用 `aips creative next-version --project PATH --target RELATIVE_ASSET` 建議下一個未使用的版本路徑；它不會寫入或覆蓋素材。執行證據可用 `aips harness trace --limit 20` 查看，事件檔不保存 prompt、憑證、素材內容、完整路徑或模型推理。

Shell 只放行可界定的唯讀命令形式，包含固定參數的 AIPS 診斷，會阻擋已知寫檔、子程序執行、設定注入及路徑逃逸選項。字串檢查不是程序沙箱；一般 MCP/custom tools 與外部程序副作用不在此 Hook 保護範圍。唯一例外是綁定目前 EPHEMERAL Session 的 `creative_execution`：它只讀取限定 Bundle，預檢後才可明確執行，輸出受限於宣告的新素材路徑。OpenCode v2.0.24 的隔離原生驗收已驗證 Context 請求與檔案 Allow/Deny；整體治理仍為 ADVISORY。

V2 plugin 會在每次 primary model dispatch 前呼叫既有 AIPS CLI，依 session、prompt、專案狀態、目標路徑和 instruction fingerprints 快取精簡 Context。`write/edit/patch` 權限再以實際資源路徑做第二階段檢查：L1 僅允許非 Git 資料夾中尚不存在且路徑受限的新創意資產；L2 需要 Project Intelligence `READY`、freshness `CURRENT` 且沒有未解權威衝突；L3 外部操作仍使用既有 Human approval gate。Shell 只允許受限唯讀命令；未知命令會被替換成失敗命令。

安裝狀態會分別回報 plugin、context hook 與 guard 狀態。成功安裝及 plugin registry 發現不代表每台主機的模型 Context 或 permission hook 都已執行；需依相符 runtime acceptance 判讀。任意 Shell 子程序、其他 MCP/custom tools、其他程式直接寫檔都不在已驗證範圍；Creative tool 的獨立 lifecycle evidence 不代表其他工具受保護，因此整體治理維持 ADVISORY。解除安裝只移除 digest 一致的 AIPS-owned plugin 和既有投影，使用者 JSON/JSONC 不變。


Managed AIPS installation channel selection controls system updates only. It does not change which Runtime Adapter is installed or grant a Host capability; continue to validate each adapter through its existing ownership manifest and capability evidence.

### Codex

以 persistent managed instruction 提供 CONTEXT_ALWAYS；安裝器會先檢查 `codex` 命令，再檢查 `CODEX_CLI_PATH`、`AIPS_CODEX_CLI_PATH` 與 macOS ChatGPT app 內建路徑。治理強度依實際可驗證能力回報，不因 MCP 存在而升級。

Codex PreToolUse 的 Plan19 probe 僅拒絕無害的本機合成命令；unsupported、malformed、timeout 與 error 路徑不構成完整 enforcement 證據，aggregate governance 維持 advisory。

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

CI MCP interoperability probes use the shared Python bootstrap with caller-declared import modules, checked-in requirements and tested constraints; this verifies the job environment without changing MCP server permissions or behavior.

Review-only config 支援 Cursor、Windsurf、GitHub Copilot CLI、Amp、Codex 與 generic stdio。GitHub-hosted Copilot agent／code review 僅能使用 Tools，且執行環境必須真的能啟動 AIPS command；本機絕對路徑不能假裝成 hosted deployment。

`aips mcp inspect` 會輸出 machine-readable Host 相容性矩陣，區分 official config contract、MCP protocol、pinned CLI registration 與尚未執行的第三方 GUI。設定格式與協定驗證不能被表述成 GUI 實機驗證，也不包含 native guard。

MCP Server 不呼叫第二個 LLM，也不取得 Human approval、Git publish、merge、release、production 或 host-native tool interception authority。

Temporal Project Intelligence 的 historical query 由既有 deterministic CLI／Project Intelligence layer 提供；MCP 與 Runtime adapter 只傳遞 bounded context，不新增 Temporal Role、Gate 或 host-native authority。

## Capability truth

Codex managed block 保留 Runtime／使用者選定的合格主要模型，並指向 bounded primary execution；不更改模型設定或擴大 tool guard 權限。

GitHub governance snapshot 是 repository operator 的唯讀工具，不是 runtime adapter 能力，也不擴張 Harness 的遠端寫入權限。

Host capability claims remain tied to native evidence for that Host and version. Advisory hook probes do not establish enforcement, and unknown Linux/WSL behavior stays unverified.

The managed AIPS CLI support floor is Python 3.12, with a separate scheduled 3.12–3.14 compatibility smoke. Runtime support facts are generated into System Reference and remain distinct from host-specific adapter capability.
The Evolution Radar maintenance capability preserves oversized Issue evidence in a bounded, digest-checked envelope; its monthly consumers restore the original body and report missing triage inputs as incomplete.


Scheduler-backed task ownership 記錄執行 owner、worktree isolation、lease 與 write-set reconciliation。這是協調與證據能力；只有 runtime 提供並驗證寫入攔截器後，才可宣稱工具寫入受到強制限制。

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

若執行環境已有獨立且受信任的簽發者，可將外部 trust store 交給 review validator／Integration Gate 驗證 Ed25519 receipt；trust store 不得放在候選 repository。AIPS 不簽發執行隔離或唯讀權限證明，也不因只有合法簽章格式就認定審查獨立。

Runtime Content Safety Boundary 只在 AIPS-owned sink 或已驗證 native hook 上宣稱強制能力；MCP-only 或 unsupported host tools 維持 ADVISORY。安全掃描不會取得 Host-native tool interception 或 Human Authority。

- The release-readiness check is evidence only: it never grants runtime capability or tag-writing authority.
## Progressive disclosure

Turn Context 固定載入精簡的 `SYSTEM_CORE.md`，再依任務選擇 canonical orchestration 路徑。Codex、Claude Code 與 Gemini hook 都取得路由指標；`SYSTEM.md` 保留相容索引，不是固定系統層。

Workflow and Runtime adapters keep validation observation collection behind the existing repository Gate; their read-only artifact reports do not enable host actions, skip checks, or add Git publication authority.

Repository mutation workflows resolve AIPS Turn Context before analysis, then use targeted intelligence refresh and Change Impact evidence before editing; commit-time publication gates additionally enforce public-repository identity and content-safety policy.

同步路徑只解析 identity、freshness、indexes 與 relevant pointers；重型 Project bootstrap、site build、semantic enrichment 不放進 hot path。

## Ownership 與解除

AIPS 只修改自己可辨識、可逆的 Managed Block / Hook / Extension。若內容被使用者修改到無法安全識別，uninstall 會保留並回報 conflict，不會暴力刪除。

Client-owned MCP config 不由 AIPS 自動寫入或刪除。

## Portable Commands

The read-only `aips run dashboard` is a repository-scoped observation consumer and does not install a host integration or add mutation authority.

Evolution maintenance commands are also exposed through the checkout-root-aware CLI: `aips evolution package`, `aips evolution analyze` and `aips evolution apply`. They share the resolved project runtime; the apply path remains bounded by the existing Human decision and trial authorization.

Portable Commands 將同一個 Canonical ID（例如 `aips.plan`）渲染成 Slash Command、Skill 或 generic MCP bootstrap。Registry 位於 `harness/commands/REGISTRY.yaml`，CLI 可檢視、預覽與管理 AIPS-owned projections：

~~~bash
aips commands list
aips commands render aips.plan --host cursor
aips commands install --host cursor
aips commands status
~~~

這些 projections 是薄包裝，不取代 Constitution、System 或 orchestration canonical sources，也不提供 Runtime-native enforcement、Git publish、merge、release、production 或 Human approval authority。使用者修改過的 projection 會保留並回報 `CONFLICT`。

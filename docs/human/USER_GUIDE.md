# AI Product System 使用指南

本文件描述 **目前如何使用 AIPS**。版本演進放在 `CHANGELOG.md`，Scenario / validation 歷史放在 [Scenario Conformance](CONFORMANCE.md)；current-behavior 文件不再以 `vX.Y` 章節追加新功能。

## 工作模式與基本流程

~~~text
需求
→ Resolve Context / Work Mode
→ 只載入需要的 Role / Skill
→ Planning / Execution
→ Independent Review / Validation
→ Human-controlled publication or production
~~~

低風險工作保持簡單；Large/Core、高價值 business logic、security boundary 或 production change 才提高 planning、review、evidence 與 validation 強度。

## 建立大型產品

例如「幫我設計並實作大型購物網站」：

~~~text
需求 / 素材
→ Product Definition
→ UX / API / Data / Architecture
→ Security & Quality Planning
→ Human Planning Review
→ Task Graph
→ Deterministic Scheduler
→ isolated parallel implementation
→ TDD / Security / Quality Review
→ LOCAL_COMPLETE
→ optional Production Enablement
~~~

AIPS 不要求 Frontend / Backend 一定拆成不同 repository；以 Deployment Unit、權限、Release Cycle、team boundary、shared contracts 與 operational ownership 判斷。

完整產品可使用 `PRODUCT.yaml` 作導航入口，描述 deployment units、contracts、database/migration、local/staging/production、build/test/security/smoke commands、release readiness 與 runbook。實際不需要的目錄不會為了形式硬建立。

### Product Delivery lifecycle

~~~text
Plan
→ Local
→ Automated Tests
→ Security Verification
→ Release Candidate
→ optional Staging
→ Release Readiness
→ Human Production Approval
→ Production
→ Health / Smoke / Logs / Metrics
~~~

`LOCAL_COMPLETE` 與 `PRODUCTION_VERIFIED` 是不同狀態；完成本地功能不等於已獲得 production authority。

## Existing Project

Existing Project mutation 前會解析 nearest instructions、Project Intelligence、Change Boundary 與 Impact Graph。沒有 `.ai/` 仍可使用 EPHEMERAL mode，Reusable Intelligence 存在 AIPS external cache。

需要 project-local persistent state：

~~~bash
aips attach /path/to/project
~~~

Detach 會先同步可重用 Intelligence，再封存 project-local workspace；不直接刪除使用者累積資料。

## Creative Direction、Style 與 Brand

Creative Direction 適用 Website、Landing Page、Banner、Hero、Social Post、Presentation、Product Page、UI、Campaign Visual 等工作。

風格判斷優先順序：

~~~text
本次明確需求
→ 使用者素材 / Reference
→ 已核准 Brand System
→ 已核准 Project Visual System
→ 本次 Creative Direction
→ 最新市場 Reference
→ 一般設計知識
~~~

「高質感、簡約、時尚」這類描述太抽象時，應先提出 2–3 個明顯不同方向做校準，而不是直接假設唯一風格。

Style Profile 是資料，不是 Skill，例如 Quiet Premium、Editorial Minimal、Modern Bento、Japanese Minimal、Cinematic Dark。單次 Campaign override 不會自動升級成永久 Brand rule。

Brand System 可涵蓋 Brand Intent、Audience / Positioning、Purpose / Mission / Vision、Values、Personality、Verbal Direction、Visual Direction、Logo System 與 Brand Application。未來做新素材時應先重用既有 Brand Profile，而不是重新猜風格。

## 需求釐清與 Planning

需求不足時採 progressive clarification：先問會改變產品方向、architecture、安全或交付成本的高資訊量問題，不為了流程而問全部細節。

會成為後續實作依據的大型需求應建立 reproducible Planning Package，常見內容：

- Product plan / scope；
- UX / user flow；
- Visual direction；
- API / data contract；
- technical architecture；
- security / quality plan；
- implementation readiness；
- assumptions / decisions。

對已釐清的功能行為，可使用 EARS 句型整理觸發條件、適用狀態、系統與可觀察回應。依情況選用恆常、事件、狀態、選配功能或異常行為句型；非功能需求保留量化目標和驗證方法，不必硬套 EARS。需要跨需求追溯時，可在 Planning Package 加入 `REQUIREMENTS.yaml`，把需求 ID 連到驗收條件與驗證方式。可用 `python scripts/requirements_traceability.py <package>/REQUIREMENTS.yaml --format json` 取得機器可讀的 PASS/FAIL；退出碼 0 代表結構檢查通過，非 0 代表檢查失敗。句型或 evidence 路徑都不代表測試已執行或通過。

Planning 核准後，再整理 Initial Implementation Items + Recommended Flow；Large/Core change 在 implementation 前需 Proposal-first 範圍與 Architecture Diagram Impact Check。

## Global Harness 與 MCP

Native Adapter 用來取得 runtime-specific hook / guard；MCP 提供跨 Host 標準接入。兩者共用 canonical Roles、Skills、Orchestration 與 Project Intelligence。

MCP-compatible Host 可以讀取 AIPS Roles / Skills / selected orchestration，並呼叫 bounded deterministic helpers。MCP Server 不執行第二個 LLM，也不取得 Human approval、Git publish、merge、release、production 或 host-native tool interception authority。

對完整支援 MCP 的 Host，優先使用 Resources / Prompts / Tools。對只提供 Tools 的 Host，使用 `aips_capability_catalog`、`aips_capability_read` 與 `aips_workflow_context` 取得同一份 canonical capability 與 Security／Architecture／Code Review、Delivery Plan context。

可用 `aips mcp config --client cursor|windsurf|copilot|amp|codex|generic` 產生 review-only 設定；輸出不會自動寫入第三方設定。`copilot` 指 GitHub Copilot CLI 的 local stdio 格式，hosted agent 仍需具備可執行的 AIPS runtime，不能直接沿用本機路徑。

MCP-only enforcement 誠實維持 `ADVISORY`；可驗證的 native pre-tool hook 才能回報 `TOOL_GUARDED`。

新增 Runtime 時先採 MCP；只有存在 MCP 無法提供的可驗證 hook／guard／event requirement，才建立 native adapter。

詳細請看 [Global Harness 與 MCP](HARNESS.md)。

## Roles、Skills 與重用

新增能力前依序檢查：

~~~text
Reuse existing Skill / Template
→ Extend Workflow
→ Extend System / Orchestration
→ New Capability
→ New Role only when responsibility truly differs
~~~

只有責任、決策邊界與 review obligation 真正不同時才新增 Role。專案自己的 conventions / rules 優先保存成 project-native knowledge，而不是無限制提升成 global Skill。

## Deterministic Automation

可用固定規則可靠完成的資料處理，優先交給 Shell / Python / existing tooling，例如 changed files、schema validation、大量 log summary、version extraction、duplicate scan、CSV / JSON transform。

~~~text
Raw data
→ deterministic helper
→ compact JSON / YAML evidence
→ model semantic reasoning
~~~

Architecture trade-off、Threat Model、視覺方向等主觀專業判斷不應為了省 token 被強行 deterministic 化。

## Deterministic Scheduler

LLM 負責 semantic planning；Scheduler 只接受已形成的 Task Graph，依 dependency、boundary、authorization、state 與 deterministic ordering 決定 dispatch，不自行發明 task、scope 或 approval。

Parallel task 必須先證明可安全並行；同一 change boundary 的 competing writer 不因想提高速度就被放行。

PR 驗證會把 Gate 與 Repository Health 報告放在 CI runner 的暫存位置，完成後再上傳 artifact。這讓驗證不會因產生報告檔而把 checkout 判定成 dirty，合併前看到的證據仍對應同一個 commit。

受保護分支的 `repository` required check 必須在 exact PR candidate 的 Integration Gate 成功後才會通過。

## Execution Isolation 與 Runtime Resource

Mutation 可依需要使用 shared workspace、AIPS-owned Git worktree 或 verified sandbox。沒有可驗證 sandbox provider 時，不把一般 temp directory 宣稱成 sandbox。

高／critical 風險或明確不受信任的執行可用 `aips isolation resolve --mode auto --risk high --data-class public` 檢查最低隔離要求。一般風險會選 worktree；高風險需要已啟用、證據新鮮且資料政策相符的 sandbox。找不到時顯示 `UNSUPPORTED`/`BLOCKED`，不會自動降級。E2B 目前停用，僅有合成資料 smoke verifier。

Parallel worktree 需要 dev/test server 時，Runtime Resource Lease 會為 isolation 配置 bounded TCP port，避免多 Agent 固定使用同一 port。

需要代理執行高風險外部動作時，Runtime Policy 會要求明確資料分類、目的地、Change Boundary 與有效核准；沒有驗證過的 sandbox 網路隔離時，動作會停止。

需要代理執行高風險外部動作時，Runtime Policy 會要求明確資料分類、目的地、Change Boundary 與有效核准；沒有驗證過的 sandbox 網路隔離時，動作會停止。

~~~text
Task
→ Worktree
→ Runtime Resource Lease
→ AIPS_PORT_<RESOURCE>
→ Agent / dev server
~~~

Lease candidate order deterministic；實際選到的 port 仍受當下 host occupancy 影響。Address-in-use race 使用 bounded reallocation，不無限 retry。

## Visual Polish 與 Product Consistency

畫面出現按鈕、標籤、留白、字級、alignment、responsive breakpoint 等不一致時，先讀既有 design tokens / component patterns / reference，再做 bounded consistency repair。

Visual Consistency Sweep 不等於重新設計整個產品。若現有 style 是使用者有意決策，應 preserve valid native style，而不是因模型偏好自行換風格。

RWD / accessibility / interaction state 應納入適用的 quality evidence。

## Security

AIPS 使用 Security Assurance Level（SAL）0–4。金流、點數、退款、authorization、可兌換優惠等高價值邏輯會提升 security assurance，檢查：

- replay / idempotency；
- race / double-spend；
- authentication / authorization；
- sensitive data / secret handling；
- audit / reconciliation；
- rollback / recovery；
- business invariants。

Secret / Key 不寫入 source、Prompt、log、Project Intelligence 或 ordinary evidence artifact。External provider credential 是 optional enhancement 時，不得變成 unrelated baseline / release prerequisite。

詳見 [Security Assurance](SECURITY_ASSURANCE.md)。

## Quality 與 Review

本地發佈預檢會先確認 Python／Ruff、loopback 與 Chromium 等 Integration Gate 條件，再做完整候選驗證；文件變更時也會檢查本地 Markdown 連結並建置 VitePress。用全域 CLI 驗證另一份 checkout 時加上 `--project-root <repo>`，讓腳本、設定與候選使用同一個 repo root。

### OpenTelemetry run traces

Record a lifecycle pair in the existing run event stream, then export or replay it:

```bash
aips telemetry record --project . --run-id RUN --kind phase --action started --operation-id plan-1 --name planning
aips telemetry record --project . --run-id RUN --kind phase --action completed --operation-id plan-1 --name planning
aips telemetry export --project . --run-id RUN --output /tmp/run-trace.json
aips telemetry replay --project . --run-id RUN --config ./telemetry-export.yaml --send
```

The shipped export config is disabled. Transmission requires a private config with `enabled: true`; HTTPS is required except for loopback testing. Keep optional authorization in the host environment variable named by `authorization_env`. Recorded values are limited to lifecycle IDs, fixed operation names, verified provider/model IDs, token counts and outcomes. Export omits prompt/output content, arguments, private reasoning and credentials. Unpaired markers show `TELEMETRY_DEGRADED`; this does not block the workflow. See [OpenTelemetry run export](./TECHNOLOGY_GUIDE.md#opentelemetry-run-export) for field limits and replay behavior; the canonical contract is `orchestration/TELEMETRY_EXPORT.md`.

### 外部 Eval / Red-Team 互通

可用 `aips eval` 匯出 Promptfoo 的 inline config、匯入 Promptfoo JSONL、匯入 PyRIT bridge，並驗證 evidence fingerprint。AIPS 不會執行外部工具設定；匯入結果只供檢視或訊號使用，不能直接通過或阻擋發布。需要把 finding 納入 regression 時，先由 Human 確認 finding 與最小重現案例，再輸出成 canonical Agent Eval Case，以 AIPS deterministic scorer 重新驗證。未設定外部 API key 也可執行全部本地驗證。

Change Impact unknown 只有在保留原始描述、具備可驗證 repository-file 或完整 traversal evidence，並有明確 Human review 時才能關閉。Legacy string、失效 evidence 與 scope mismatch 仍會阻擋實作。Disposition evidence is reviewed separately from implementation approval; exact changed-file reconciliation remains mandatory before READY.

獨立審查隔離機制已實作，但目前**未啟用為 PR 強制要求**；active Core Change Matrix 設為 `review_evidence.required: false`。待可信 runtime-attestation verifier 接通後，才可將矩陣設為 `true` 啟用。啟用後，沒有可信證據的必要審查會維持 `UNVERIFIED` 並阻擋 Gate。

只修改 EARS validator 契約時，文件影響限於 Scenario Conformance 與 Technology Guide；若改動需求追蹤功能、Planning Package 範本或 canonical requirements，仍須更新完整 Requirement Planning 文件閉包。

需要檢視 Agent 如何完成任務時，可使用 `aips trajectory evaluate --trace <trace.yaml> --mode shadow`。結果是 observable evidence；`BLOCK` 表示 deterministic risk，`WARN` 表示品質偏差，任何結果都不會自動授予 Git Publish 權限。

Quality Planning 依風險選擇最低足夠驗證。Implementation 完成後執行適用的：

- lint / type check；
- unit / integration / contract / E2E；
- regression；
- security verification；
- independent review；
- Integration Gate / Janitor；
- Repository Health / architecture consistency。

Core change 以 actual diff 重新對帳 Test Matrix，不能只依原始計畫宣稱完成。

`SELF_CHECK` 是實作者自己的驗證；`INDEPENDENT_REVIEW` 必須由不同執行身分，在唯讀、隔離的任務中審查精確候選版本。Review packet 只包含明確允許的候選差異、必要規格與驗證證據，並以 base/head、檔案清單和內容指紋綁定；不得傳入實作者對話、隱藏推理、scratchpad 或未列入 allowlist 的工作區內容。缺少可信 runtime attestation verifier、候選版本不符或執行身分重複時，結果是 `UNVERIFIED`，必要審查會阻擋 Integration Gate 與發布。

Integration Gate 只檢查證據格式、來源、候選綁定與確定性政策，不替代語意審查，也不授予合併或發布權限。

Visual evidence 預設優先使用 Playwright managed Chromium；系統 Chrome 只有在 `AIPS_BROWSER_PROVIDER=system` 或 managed browser 不可用時使用。Publication preflight 會先執行 browser smoke probe，啟動失敗會標記為 `ENVIRONMENT_BLOCKED`，不誤判成頁面測試失敗。

## Logging、Observability 與 Operations

正式產品依風險規劃 logs、metrics、health / smoke、alerts、runbook 與 rollback。Observability 的目的不是大量產生 log，而是讓重要 failure mode 可被定位與復原。

Production verification 應使用 observable evidence，不以「workflow 已執行」取代 service health / smoke / deployment state。

## Checkpoint / Resume

長流程在 material step 保存 durable checkpoint / event evidence。Resume 時重新比較 repository/workspace identity、HEAD、branch、dirty state 與 relevant approvals。

舊聊天內容不是 authoritative run state；若 workspace fingerprint 已變，先 refresh / revalidate 再接續。

### Parallel Run Dashboard

Use the read-only dashboard to inspect all known runs for the current repository, including runs in parallel worktrees:

```bash
aips run list --project .
aips run dashboard --project .
```

The dashboard is an observation surface. It shows workflow state, gate, last activity and workspace health, but it cannot approve, retry, cancel, merge or publish. `ACTIVE` means the last checkpoint reported an active workflow; it does not prove that an Agent process is still live. The local server binds only to `127.0.0.1`.

## Project Intelligence

Stable Intelligence 保存 Architecture、Data Flow、Modules、Contracts、Conventions、Testing、Security、Operations、Source Registry 與 Impact Graph。

Just-in-Time Retrieval 只帶入本次任務相關的 code、symbols、tests、history、graph evidence，避免每個 Turn 重掃整個 repository。Retrieval cache 是可重建 acceleration layer，不取得 governance authority。

詳見 [Project Intelligence](PROJECT_INTELLIGENCE.md)。

## Git Publication 與 Release

建立 Large/Core PR 前，先用 `aips publish preview` 檢查未提交文件位置與 Matrix 綁定，再用 `aips publish plan` 確認 GitHub CLI 認證與首次 PR 分類標籤。首次 `gh pr create` 應同時帶入 `--label aips:large-change` 或 `--label aips:core-change`。

Remote Git publication 前需有 current Human authorization 與適用 validation evidence。AIPS 會區分：

~~~text
local implementation
≠ git publication
≠ merge
≠ release
≠ production deployment
~~~

Agent、MCP、CI workflow 或 external analyzer 不能因為具有執行能力就自行取得上述 authority。

提交前可執行 `aips publish preview --base origin/main --change-class <standard|large|core>`，預覽已提交、暫存、未暫存及未追蹤檔案的文件閉包與矩陣綁定；必須先處理 `pending` 項目。`aips publish matrix-sync --base origin/main` 只更新 canonical Core Matrix 的 base/hash，更新後仍需重新檢視範圍與證據，再把矩陣標記為 READY。發布前再以 `aips publish preflight --base origin/main --head HEAD --change-class <standard|large|core> --output <report>` 執行與 CI 相同的 exact-candidate resolver。Large/Core PR 必須同步套用對應 label，並使用 `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`。受保護 `main` 由 `publish plan` 直接規劃 Pull Request，不先嘗試直推。

若 preview 回報 Matrix DRAFT、blocker、尚未核對差異或 base/hash 不符，先處理對應 `pending`；`READY_FOR_GATE` 只表示可進入正式 Gate。從原始碼 checkout 執行時使用 `./bin/aips`，以免讀到全域安裝版本的矩陣。

本地首次驗證可先執行 `python3.12 bin/prepare-local-validation`，之後用 `python3.12 bin/prepare-local-validation --check-only --run --base <base-sha> --head <head-sha> --change-class core` 執行同一候選的 Publication Preflight 與 Gate；驗證設定會暫存在 repository 外。建立 Large/Core PR 時同時使用 `gh pr create --label aips:large-change` 或 `--label aips:core-change`，讓首輪 CI 取得正確分類。

每個 Remote Git publication candidate 都會由 AIPS 內建秘密掃描器檢查 exact final tree 和 base 到 head 的 commit 歷史。找到秘密、歷史或候選內容無法完整掃描、policy 無效時，發布檢查會阻擋並只顯示遮蔽後位置與指紋；修正後須重新驗證。Gitleaks、GitGuardian 與 GitHub Secret Scanning 可作第二層防護，不需要它們的憑證才能通過 AIPS baseline。

Core Matrix 的 `changed_files_hash` 必須綁定相同 base/head 的完整變更檔案集合；精確候選通過 preflight 後才可請求 PR review。Integration Gate PASS 是驗證證據，不會代替明確的 merge 授權。


Preview 也會在昂貴驗證前檢查候選內容安全與允許的 Git email 身分；報告只提供命中類型與位置，不回顯敏感值。Context 則會先證明所選路徑與已知主題相關，並共同限制 Core、Recall 與 temporal evidence 的預算；Retrieval Index 無法開啟時提供穩定診斷與來源指標，不偽裝成已檢索成功。

若本機工作樹包含其他未提交變更，先建立乾淨 worktree 驗證候選；不要讓 unrelated diff 改變 changed-files hash 或 Repository Health 結果。

Squash merge 後可執行 `aips publish post-merge --fetch --apply --refresh-intelligence`。只有工作樹乾淨且 local／remote tree object 完全相同時，才會先建立 backup branch 再對齊；內容不同一律停止。

Release model 與版本歷史以 repository 的 current policy / CHANGELOG 為準。

## Evolution Radar

Technology Intelligence 位於 maintenance plane，不在一般工程 Turn hot path。

~~~text
public evidence
→ provenance / dedup
→ deterministic pre-analysis
→ optional semantic analysis
→ Human Decision
→ bounded Trial
→ normal System Improvement / Core Change / Publish gates
~~~

Trial PASS 不等於 ADOPT；recommendation 也不會自動修改 code、merge 或 release。

詳見 [Evolution Radar](EVOLUTION_RADAR.md)。

## Documentation

Human current behavior 以 topic-oriented 方式更新在 `docs/human/`。Official Docs Site 由同一份 Markdown source 透過 VitePress render，不建立第二份 canonical content。

文件責任：

~~~text
Current behavior / How-to / Explanation
→ docs/human/ 對應 topic section

Release / version history
→ CHANGELOG.md

Scenario / validation history
→ docs/human/CONFORMANCE.md
~~~

Documentation Placement Contract 會檢查 heading hierarchy、version/scenario-style heading 與 changed-line placement。新增功能不得只在 current-behavior 文件尾端追加 `vX.Y` / Scenario 說明；若確實需要新 topic，必須同時把 canonical section 加入 placement contract。
## Runtime Content Safety Boundary

Commit, pull request and release content is scanned before durable/public publication. A blocked result requires regenerating safe content; it is not silently rewritten. Runtime capability remains truthful: AIPS-owned sinks are enforced, native hooks may be tool-guarded, and unsupported host tools are advisory.

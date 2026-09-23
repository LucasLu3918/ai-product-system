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

Parallel worktree 需要 dev/test server 時，Runtime Resource Lease 會為 isolation 配置 bounded TCP port，避免多 Agent 固定使用同一 port。

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

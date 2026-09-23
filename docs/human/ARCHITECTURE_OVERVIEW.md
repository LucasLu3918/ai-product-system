# 系統架構總覽

AIPS 是跨 Agent Software Engineering Harness。這份文件只描述**目前架構**；版本歷史放 CHANGELOG，Scenario 證據歷史放 Conformance。

![AI Product System 架構總覽](assets/system-overview.svg)

## Runtime 與接入層

Portable Commands 以 Canonical ID（例如 `aips.plan`）將同一治理工作流渲染為 Slash Command、Skill 或 generic MCP bootstrap；它是 advisory access plane，不取代 Runtime-native Adapter 的 turn hook 或 pre-tool guard。

~~~text
User Prompt
→ MCP Access Plane 或 Runtime-native Adapter
→ Compact AIPS Context
→ Host Agent semantic reasoning
→ deterministic AIPS helpers / governed execution
~~~

MCP 提供 portability；native adapters 提供可驗證的 runtime hook / guard。兩者共用 canonical Roles、Skills、Orchestration 與 Project Intelligence。完整 MCP Host 使用 Resources／Prompts／Tools；tool-only Host 透過唯讀 capability/workflow Tools 取得同一 canonical context。新 Host 只有在需要 MCP 無法提供的 verified hook／guard／event source 時才新增 native adapter。

## Project Intelligence 與 Retrieval

Squash merge 後的 revision refresh 只有在舊／新 Git tree 完全一致時可自動更新 metadata；tree 不同時維持 semantic refresh required，避免把內容變更誤標為 CURRENT。

Existing Project 第一次需要廣泛理解或修改時，先 read-only bootstrap，再建立 Architecture / Data Flow / Modules / Contracts / Tests / Security / Operations 等 stable Intelligence。

後續 Turn 以 Just-in-Time Retrieval 取得 task-relevant code、symbols、tests、Impact Graph 與 Git history；retrieval cache 可重建，不取得治理 authority。

Temporal Project Intelligence 在既有層上增加 `TEMPORAL_ASSERTIONS.yaml`，以 Git revision ancestry 表達事實有效期間，以 provenance、observed metadata 與 supersession 表達架構演進。一般工作仍使用 Current Snapshot；只有歷史、backport、release branch 或 evolution 問題才執行 bounded temporal query。SQLite 只保存可重建投影，不是 canonical truth。

## Project Identity 與 Persistence

~~~text
repository_id
├─ main workspace      → workspace_id A
├─ feature workspace   → workspace_id B
└─ AIPS worktree       → workspace_id C
~~~

EPHEMERAL 把 durable reusable state 放在 AIPS external cache；ATTACHED 才使用 project-local .ai/。

## Planning 與 Product Delivery

大型產品先形成 Planning Package，再經 Human review 進入 implementation planning。產品生命週期維持：

~~~text
Plan
→ Local implementation
→ Tests / Security / Review
→ LOCAL_COMPLETE
→ optional Production Enablement
→ PRODUCTION_VERIFIED
~~~

Production、Git publication、merge 與 release authority 不因 Automation 或 MCP 而自動取得。

## Deterministic Execution

Publication Preflight provides a read-only working-tree preview with rule-by-rule documentation closure, and a matrix-binding command that invalidates prior readiness whenever the candidate base or changed-file hash changes.

### Parallel Run Dashboard

`scripts/run_projection.py` is a read-only projection over canonical checkpoint, event, scheduler/isolation and gate facts. CLI and browser consumers share the projection; the dashboard never becomes a second state machine or authority surface. Repository-scoped aggregation allows a maintainer to observe parallel worktrees while preserving existing workspace fingerprints and Resume semantics.

`aips commands render` 僅預覽，`install`／`upgrade` 只管理 AIPS-owned projection；ownership digest 會偵測使用者修改並保留衝突檔案。

Semantic planning 與 deterministic execution 分離：

- Deterministic Scheduler：依 Task Graph 決定可重現 dispatch。
- Execution Isolation：shared / worktree / verified sandbox。
- Runtime Resource Isolation：為 parallel worktree 協調 bounded TCP port lease。
- Integration Gate / Janitor：在 candidate merge 前執行適用 lint / type / test / repository validation。

Validation evidence 與 source checkout 分離保存。Gate 報告和 Repository Health 報告使用 runner 暫存路徑，完成後才上傳 artifact，讓 repository validation 看到的仍是 exact clean revision。

受保護分支會以 exact candidate 的 Gate 結果作為 `repository` aggregate 的合併前條件。

Local 與 GitHub 透過 Publication Preflight 解析同一 base/head、PR-label change class、canonical matrix 與文件 diff base。快速 repository preflight 先攔截文件與 schema drift，再執行昂貴 lifecycle。

Browser evidence 也屬於 deterministic environment contract：candidate preflight 會探測 Playwright managed Chromium 或明確選用的 system browser，執行最小 headless smoke probe；啟動層錯誤會以 `ENVIRONMENT_BLOCKED` 回報，避免與產品頁面回歸混淆。

## Security 與 Governance

Security Assurance Level（SAL）依產品 baseline 與 change impact 決定 review 強度。高價值 business logic、authorization、financial integrity 等 protected boundary 使用更嚴格 evidence。

Human Approval 維持最高決策權；machine-readable approval binding、resource authorization、audit chain / portable bundle / retention catalog 都只驗證與保存 authority evidence，不創造新的 authority。

## Scenario Conformance 與 Agent Eval

Scenario registry 明確標示 deterministic、lifecycle、agent_eval 或 manual evidence。需要 semantic judgment 的測試保存 observable result，不保存 private chain-of-thought。

Trajectory Quality Gate 在既有 Agent Eval 之上評估 observable Agent trajectory。Deterministic evaluator 負責 tool call、重複讀取、retry、ordering、authorization 與 required validation；可選的 LLM Judge 只產生 evidence，不具備單獨阻擋 Git Publish 的權限。Shadow mode 先產生 PASS/WARN/BLOCK 建議，最終仍由 Human Approval 決定發布。

## Evolution Radar

Evolution Radar 位於 maintenance plane：收集 public technical evidence、deterministic pre-analysis、provider-neutral semantic handoff、Human Decision、bounded Trial。Radar recommendations 不會自動修改 code、開 implementation PR、merge 或 release。

## Documentation Architecture
~~~text
docs/human/*.md
→ canonical Human source
→ VitePress renderer
→ Official Docs Site

CHANGELOG
→ version history

CONFORMANCE
→ verification history
~~~

Standalone HTML 不再是新增功能的 canonical target。Current behavior 必須更新到 topic-oriented canonical section；CI 會檢查 Human Docs heading structure 與 change placement。

## Official Docs Site

VitePress 只渲染 Human documentation。Agent canonical protocols 仍留在 SYSTEM.md、orchestration/、roles/、skills/，不因網站而複製。

Docs build 與 Pages hosting 分開驗證：PR / main 都能證明 VitePress build；只有 repository 已啟用 GitHub Pages（Source = GitHub Actions）時才 deploy。尚未啟用時 workflow 明確記錄 `SKIPPED_NOT_CONFIGURED`，不把「hosting 尚未設定」誤報成文件 build failure。

Documentation Placement 對 behavior-bearing source 採 fail-closed mapping：只要 source 落在 Technology Guide 的廣域同步 surface，就必須先命中 subsystem placement rule。這避免新功能以「文件最後補充說明」逃過 topic architecture。
## Runtime Content Safety Boundary

Before AIPS persists or publishes content, the sink-aware Runtime Content Safety Boundary applies deterministic secret/PII detection and records untrusted-content provenance. Diagnostic sinks redact; durable or public sinks block. This boundary complements, and does not replace, Human Authority and Git Publish Approval.

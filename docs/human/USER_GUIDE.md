# AI Product System 使用指南

本文件描述目前怎麼使用 AIPS，不記錄版本演進；版本歷史請看 CHANGELOG。

## 工作模式與基本流程

~~~text
需求
→ Resolve Context / Work Mode
→ 只載入需要的 Role / Skill
→ Planning / Execution
→ Independent Review / Validation
→ Human-controlled publication or production
~~~

低風險工作保持簡單；Large/Core 或高風險工作才提高 planning、security 與 validation 強度。

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

AIPS 不要求 Frontend / Backend 一定拆成不同 repository；以 Deployment Unit、權限、Release Cycle 與 team boundary 判斷。

## Existing Project

Existing Project mutation 前會解析 nearest instructions、Project Intelligence、Change Boundary 與 Impact Graph。沒有 .ai/ 仍可使用 EPHEMERAL mode。

需要 project-local persistent state：

~~~bash
aips attach /path/to/project
~~~

## Global Harness 與 MCP

Native adapter 用來取得 runtime-specific hook / guard；MCP 提供跨 Host 標準接入。

MCP-compatible Host 可以讀取 AIPS Roles / Skills / selected orchestration，並呼叫 deterministic helper。MCP-only enforcement 誠實維持 ADVISORY。

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

Style Profile 不是 Skill；單次 campaign override 也不會自動升級為永久 Brand rule。

## Planning 與 Core Change

會成為後續實作依據的大型需求應建立 reproducible Planning Package。Large/Core change 在 implementation 前需要 Proposal-first 範圍與 Architecture Diagram Impact Check。

Human current decision 優先於舊 planning artifact，但仍受 Platform / Safety / Legal constraint。

## Deterministic Scheduler

LLM 負責 semantic planning；Scheduler 只接受已形成的 Task Graph，依 dependency / boundary / authorization 決定 stable dispatch，不自行發明 task 或 approval。

## Execution Isolation 與 Runtime Resource

Parallel mutation 優先使用 AIPS-owned worktree。需要 dev/test server 時，runtime lease 會為 isolation 配置 bounded TCP port，避免多 Agent 使用固定 port 互撞。

Lease selection order deterministic；實際 port 仍受 host occupancy 影響。

## Security

AIPS 使用 SAL 0–4。金流、點數、退款、authorization、可兌換優惠等高價值邏輯會提升 security assurance，檢查 replay、idempotency、race、double-spend、authorization、audit / reconciliation 等風險。

Secret / Key 不寫入 source、Prompt、log、Project Intelligence 或 evidence artifact。

## Quality 與 Review

Quality planning 依風險選擇最低足夠驗證。Implementation 完成後執行適用 tests、independent review、security evidence 與 Integration Gate / Janitor。

## Checkpoint / Resume

長流程在 material step 保存 durable checkpoint / event evidence。Resume 時重新比較 workspace identity、HEAD、branch 與 dirty state；不把舊聊天內容當成 authoritative run state。

## Git Publication 與 Release

Remote publication 前需有 current Human authorization 與適用 validation evidence。Agent / MCP / workflow 不能自己取得 publish、merge、release 或 production authority。

## Project Intelligence

Stable Intelligence 保存 Architecture、Data Flow、Modules、Contracts、Conventions、Testing、Security、Operations 與 Impact Graph。JIT Retrieval 只帶入本次任務相關 evidence，避免每 Turn 重掃完整 repository。

## Evolution Radar

Technology intelligence 是 maintenance plane，不在一般工程 Turn hot path。Evidence → recommendation → Human Decision → bounded Trial → normal System Improvement / Core Change / Publish gates。

## Documentation

Human current behavior 按 topic 更新在 docs/human/；release history 放 CHANGELOG；Scenario / validation history放 Conformance。新功能不得只在 current-behavior 文件尾端追加 vX.Y 說明。

Official Docs Site 由相同 Markdown source 透過 VitePress render，不建立第二份內容。

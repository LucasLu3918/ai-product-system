# Project Intelligence 使用指南

Project Intelligence 是 AIPS 對既有專案建立的可重用理解層。

![Project Intelligence 流程](assets/project-intelligence-overview.svg)

## 第一次 Existing Project

Read-only Discovery 先建立 PARTIAL，再由 Agent 針對 Architecture、Data Flow、Modules、Contracts、DB/Events、Conventions、Testing、Security、Operations 做 evidence-based semantic enrichment；通過 finalize 才是 READY。

## 不重複正式文件

已有 AGENTS / CLAUDE / GEMINI / ADR / OpenAPI / Architecture Docs / Brand / Visual / Quality Artifact 時，只存 Pointer/Metadata。SOURCE_REGISTRY 同時記錄 Runtime visibility。

## 四份核心 Machine-readable 檔

- `PROJECT_INTELLIGENCE.yaml`：Identity / Branch / Worktree / State / Topic pointers。
- `SOURCE_REGISTRY.yaml`：Authoritative source / Scope / Hash / Runtime visibility。
- `IMPACT_GRAPH.yaml`：API / Module / DB / Event / Consumer graph。
- `PROJECT_OVERRIDES.yaml`：使用者核准、補充、例外、排除、Conflict。

## 三軸狀態

~~~yaml
readiness: READY | PARTIAL | BLOCKED
review: UNREVIEWED | REVIEWED | CHANGES_REQUESTED
freshness: CURRENT | STALE
~~~

## Human Review HTML

ATTACHED 位於 `.ai/intelligence/reviews/PROJECT_INTELLIGENCE_REVIEW.html`；EPHEMERAL 位於 AIPS External Cache。HTML self-contained、deterministic，只是 Review View。

## Freshness

不是任何 Commit 都全量 STALE。AIPS 比較 relevant Source Hash、watched paths、HEAD diff、dirty paths、Branch/Worktree 與 Schema，只 Targeted Refresh 受影響 Topic。

## Attach / Detach

Attach 將 External Intelligence validated migrate 到 `.ai/intelligence/`；Detach 先 validated sync 回 External Cache，再封存 `.ai/`。

## Change Impact

Mutation 前建立 CHANGE_IMPACT，涵蓋 Input / Output / Data / Events / Consumers / Security / Invariants / Compatibility / Tests；實作後以 Actual Diff 回頭核對。

## Preserve Valid Native Conventions

Explicit Rule → Formatter/Linter/Contract → Shared Abstraction → Majority Convention → Approved Intelligence → Framework Best Practice → AIPS Default。Unsafe/broken legacy pattern 不盲目複製。

## Sensitive Data

Intelligence / HTML 不保存實際 Password、Token、Private Key、Secret env value、Credential 或不必要的敏感 Payload。

## Monorepo

採 System-level + Target Component + Shared Impact relationships 的 Lazy Load，不因整體理解就載入所有 Component。

## Retrieval Intelligence：即時按需檢索

Project Intelligence 不再只依賴預先整理好的 Topic。AIPS 保留原本的穩定理解層，同時加入一個可以隨時重建的 Retrieval Intelligence 快取。

~~~text
穩定 Project Intelligence
Architecture / Impact Graph / Source Registry / Overrides
                    +
即時 Retrieval Intelligence
Code / Symbol / Test / Git History
                    ↓
          只挑本次任務需要的內容
~~~

例如修改退款邏輯時，系統可以優先帶入退款實作、相關測試、Impact Graph 關聯與過去相關 commit diff，而不是先把整個 orders 目錄或所有 Architecture Topic 塞進 Context。

目前核心採 Local-first Hybrid Retrieval：

- SQLite FTS lexical search；
- 程式 symbol 定義比對；
- test evidence 加權；
- Impact Graph 關聯加權；
- Git commit / diff history；
- Token Budget 限制。

Semantic/Embedding Provider 是可選擴充，不是必要依賴。沒有設定時會誠實標記 `NOT_CONFIGURED`，仍使用本機 deterministic / structural retrieval，不會假裝已做 embedding semantic search。

實際 index DB 放在 AIPS cache，屬於可刪除、可重建資料；`RETRIEVAL_INDEX.yaml` 只記錄版本、workspace、revision、provider 與 coverage，不會取代 repository code 或 Project Intelligence 成為 Source of Truth。

每個結果會保留 path + line（或 commit）、content hash、Git HEAD / dirty fingerprint，並先排除 credential / secret path、限制最大 Context Token。

## Retrieval Quality Evaluation：先量測，再決定下一項技術

AIPS 不會因為「Vector DB、Embedding、Tree-sitter、LSP 或 Sourcegraph 看起來更進階」就直接導入。下一步先使用 repository-specific benchmark，對照：

~~~text
v0.20-style Static Topic Context
                vs
v0.21 Local Hybrid Retrieval
                ↓
Precision@K / Recall@K / F1@K / MRR
Git History Recall
Irrelevant Context Rate
Token Usage
Observed Latency
~~~

其中 Static Topic baseline 是可重現的「v0.20-style」比較基準，不宣稱能逐字重建所有歷史 v0.20 Agent Turn。Benchmark 評的是「本次工程任務能否取得正確 repository evidence」，不是 Agent 整體任務品質。

Suite 會明確列出每個案例的 expected source paths、可選的 history term、baseline topic files、Top-K、Token Budget 與門檻。Benchmark 控制資料應放在 indexed product source 之外，或 ATTACHED project 的 `.ai/` workspace，避免 expected answer 本身被 FTS 找回而污染評估。

Case 另外分成：

- **required**：核心 regression gate；任何 threshold 失敗都會讓 evaluation / CI FAIL。
- **diagnostic**：刻意挑戰目前能力邊界的 stress case；仍會誠實保留 FAIL 與各 metric，但只記成 diagnostic gap，不會為了它直接阻擋 release，也不能把 FAIL 改寫成 PASS。

Diagnostic case 會標註 dimensions，例如 Go / TypeScript、monorepo/shared module、low lexical overlap、synonymy、cross-file call chain。Report 會彙總 gap IDs、gap dimensions 與 failed checks（例如 recall、history、context purity）；只有當某一類 gap 持續出現，才有足夠 evidence 討論 Tree-sitter/LSP、Embedding 或 Sourcegraph。

系統另外區分：

- **reference recall**：Topic 有提到某個 source path；
- **direct source recall**：實際把該 source evidence 取回 Context。

因此不會把「summary 裡有寫到檔名」誤算成已取得真正程式碼 evidence。

Latency 只記錄 observed value，不作為共享 CI 的 pass/fail 門檻；避免 runner 負載造成假 regression。Result fingerprint 只綁定 suite、repository revision / dirty state、deterministic metrics/checks 與 authority boundary；observed latency、machine-local path、index timestamp 不進 fingerprint，因此相同 evidence 不會因 runner 速度不同而變成另一份證據。

~~~bash
aips intelligence evaluate \
  --project /path/to/project \
  --suite retrieval-evaluation.yaml \
  --output retrieval-report.json
~~~

Benchmark 結果只是 evidence。它不會自動開啟 semantic provider、不會自行改 ranking 權重，也不會替 Human 決定下一步要使用 Tree-sitter/LSP、Embedding 或 Sourcegraph。

## Debug

一般使用不需執行；排錯可用 `aips intelligence status/render/finalize/impact-init/index/retrieve/evaluate`。

## Identity namespace

Project Intelligence follows `orchestration/PROJECT_IDENTITY.md`. EPHEMERAL storage is workspace-scoped by canonical `workspace_id`; repository-wide writer coordination belongs to the isolation layer and uses `repository_id`.

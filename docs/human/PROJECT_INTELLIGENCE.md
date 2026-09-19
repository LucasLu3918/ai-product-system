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

## Structural Retrieval：已採用的跨檔關係檢索

Structural Retrieval 已在 controlled Trial 通過 full corpus 並取得 Human Adoption Decision，因此現在成為正常 Retrieval Intelligence 的預設 lane。

~~~text
Exact Query Symbol
   ↓
Lexical Index 找引用它的 Bridge
   ↓
Bridge 內其他 Exact Identifier
   ↓
Indexed Symbol Definition
   ↓
Target Definition / Related Test
~~~

例如查詢只知道 `CheckoutCoordinator` 與「downstream allocation / rollback」，系統可以先找到 wiring file，再沿 wiring 中的 exact identifier 找到 inventory reservation definition，不需要 query 直接寫出 `ReserveStock`。

正式採用仍維持幾個邊界：

- Bridge discovery 使用既有 lexical index，不做無限制全庫掃描；
- target resolution 使用 indexed symbol table；
- bridge / identifier / target / test scan 都有 hard limit；
- retrieval evidence 會顯示 structural telemetry 與是否發生 truncation；
- 不新增 Tree-sitter、gopls/LSP、Sourcegraph 或 remote semantic dependency；
- 這是 exact-identifier relation graph，不宣稱 compiler-grade semantic resolution；
- Turn Context 與一般 `aips intelligence retrieve` 預設啟用；
- debug / regression 可用 `--no-structural` 明確關閉；
- Scenario 130 仍保留 explicit OFF/ON Trial replay；
- Retrieval Quality Evaluation 會量測目前已採用的 default behavior。

## Semantic Alias Expansion Candidate Trial：HOLD

Structural Retrieval 採用後，AIPS 先測了一個不需要 Embedding / Vector DB 的 deterministic alias expansion 候選，希望處理 low lexical overlap / synonymy。

這次完整 9-case corpus 的結論不是 PASS，而是 **FAIL / HOLD**：

- `auth-token-expiry`、Go receipt reconciliation、TypeScript session refresh 三個 required case 出現 regression；
- 原本 registration diagnostic baseline 已經 Recall@K=1.0，但 alias candidate 反而降低 source recall；
- `synonym-access-rotation` 仍沒有 source-recall 改善；
- 真正 semantic provider 全程仍正確顯示 `NOT_CONFIGURED`。

因此這個 alias candidate **不採用、不進 Turn Context default**。Scenario 132 會刻意重播這個失敗結果，要求 Trial 回傳 `HOLD`，避免後續只靠調權重把負向 evidence 洗成 PASS。

如果後續還要處理 semantic gap，下一個候選必須是 materially different 的方案，例如真正的 embedding / semantic provider；但開始之前需要另外做 Human review，明確決定 source-code 是否可送往 provider、使用 local 或 remote embedding、成本/快取/隱私/fallback 邊界。Scenario 132 不會自動啟用任何 provider。

## Remote Embedding Retrieval Trial Readiness（Scenario 133）

AIPS 接著準備真正的 remote embedding Trial，但仍然不改正式 Turn Context。

第一版 Trial 只允許傳送 **synthetic Retrieval Quality fixture**，不允許傳 AIPS repository / product source。Credential 沿用 protected CI secret reference，不寫進 source、log 或 report。

~~~text
Synthetic 9-case corpus
   ↓
正式 Retrieval baseline
   ↓
Remote Embedding candidate
   ↓
In-memory cosine ranking
   ↓
同一套 retrieval metrics
   ↓
PASS / FAIL / TRIAL_PENDING / TRIAL_BLOCKED
~~~

邊界：

- 正常 PR / main CI 不呼叫 remote embedding；
- 只有專用 Trial branch 或手動 workflow dispatch 才會嘗試；
- 沒有 `OPENAI_API_KEY` → `TRIAL_PENDING`；
- provider/network failure → `TRIAL_BLOCKED`；
- request、candidate chunks、remote characters 都有 hard limit；
- 不新增 Vector DB，向量只在 Trial runtime 暫存；
- 正常 Retrieval / Turn Context 仍完全不啟用 embedding lane；
- production source transfer 維持 false；
- 即使 Trial PASS，也只能進 Human Adoption Decision，不能自動採用。

第一個 adapter 使用 OpenAI embeddings endpoint，預設 model 為 `text-embedding-3-small`；model 可以用 repository variable 覆寫，但 provider 不因此成為 AIPS 必要依賴。

### 如何完成真實 Provider Trial

Dedicated workflow 會把 machine report 轉成 GitHub Job Summary，因此 **workflow 顯示 SUCCESS 不代表 Trial 已 PASS**。

操作順序：

1. 在 repository 的 GitHub Actions secrets 配置名稱為 `OPENAI_API_KEY` 的 repository secret；不要把 key 寫入 repository、Issue、PR 或 log。
2. 如需覆寫預設 model，可設定 repository variable `AIPS_RETRIEVAL_EMBEDDING_MODEL`；沒有設定時使用 `text-embedding-3-small`。
3. 重新執行 `retrieval-semantic-trial` workflow。
4. 直接查看 Job Summary：
   - `TRIAL_PENDING`：credential 仍不可用，provider 未執行；
   - `TRIAL_BLOCKED`：provider/network/config 有阻塞，維持 HOLD；
   - `FAIL`：品質不達標，保留負向 evidence，不採用；
   - `PASS`：只代表可以進 Human review，仍不能自動啟用 embedding。
5. 只有 `PASS` 且 Human 明確做出 Adoption Decision 後，才可另開正式 adoption change。

目前 normal Retrieval / Turn Context 與 production source-transfer policy 在上述流程中都不會改變。

## Provider-Neutral Local-First Embedding Trial（Scenario 134）

Scenario 133 的 remote adapter 與安全邊界保留，但不再把 remote credential 當成 semantic research 的預設前置條件。Scenario 134 將 embedding Trial 改成 **local-first / remote-optional**：

~~~text
Synthetic 9-case corpus
   ↓
正式 Retrieval baseline
   ↓
Provider selection
   ├─ local（default）→ pinned BGE model → runner-local inference
   └─ remote（optional）→ OpenAI-compatible embeddings
   ↓
In-memory cosine ranking
   ↓
同一套 retrieval metrics / thresholds
   ↓
PASS / FAIL / TRIAL_PENDING / TRIAL_BLOCKED
   ↓
Human Adoption Decision（PASS 也不自動採用）
~~~

預設 local provider：

- runtime dependency：pinned `sentence-transformers`；
- model：`BAAI/bge-small-en-v1.5`；
- model revision：固定 commit，不追隨 mutable `main`；
- dimensions：384；
- 不需要 `OPENAI_API_KEY`；
- 第一次 Trial 可從 Hugging Face 下載 model artifact，但 query / fixture embedding inference 在 GitHub Actions runner 內完成；
- `HF_HUB_DISABLE_TELEMETRY=1`；
- repository/product source transfer 仍為 false；
- model download/load/inference failure → `TRIAL_BLOCKED / HOLD`。

Remote provider 仍可透過 `AIPS_RETRIEVAL_EMBEDDING_PROVIDER=remote` 顯式選擇。只有這條 optional path 才需要 `OPENAI_API_KEY`；若缺少 credential 仍誠實回 `TRIAL_PENDING`。

正常 PR/main validation 不安裝 semantic Trial dependency、不下載 model、不執行 embedding；dedicated `retrieval-semantic-trial` 才安裝 `requirements-semantic-trial.txt` 並執行真正 embedding benchmark。

Scenario 134 不改 production Retrieval / Turn Context。Local Trial PASS 也只代表 evidence eligible for Human review；production embedding lane、cache、source-transfer policy 與 default enablement 都仍需另外 Human Adoption Decision。

## Debug

一般使用不需執行；排錯可用 `aips intelligence status/render/finalize/impact-init/index/retrieve/evaluate`。

## Identity namespace

Project Intelligence follows `orchestration/PROJECT_IDENTITY.md`. EPHEMERAL storage is workspace-scoped by canonical `workspace_id`; repository-wide writer coordination belongs to the isolation layer and uses `repository_id`.

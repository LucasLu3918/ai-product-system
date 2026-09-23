# Scenario Conformance

AIPS v0.13 開始把「Acceptance Scenario 有幾份」與「有多少真的有可追溯測試證據」分開。

## Coverage 類型

- `deterministic`：可由 deterministic helper / schema / rule test 驗證。
- `lifecycle`：需要多步驟執行流程的 executable test。
- `agent_eval`：需要 Agent / Model 行為評估。
- `manual`：規格存在且可人工檢查，但目前不宣稱 automated evidence。
- `uncovered`：尚無可接受 evidence；目前 release policy 不允許 uncovered。

## 指令

~~~bash
aips conformance check
aips conformance report
~~~

Registry 位於 `tests/scenario_coverage.yaml`。

## v0.13 Baseline

v0.13 發布時採保守分類：既有 001–095 若沒有明確的一對一 executable evidence，就維持 `manual`。這不是表示它們沒有任何 validator 關聯，而是 AIPS 不把間接相關檢查誇大成 Scenario-level automation。

Coverage percentage 是工程 evidence 指標，不是系統品質分數，也不能取代 risk-based testing。

## v0.14 Baseline

v0.14 新增 Scenario 111–115，全部都有直接 executable evidence：2 個 deterministic、3 個 lifecycle。若既有 001–095 不重新分類，release baseline 為 115 個 Scenario、95 manual、20 automated、0 uncovered。

## v0.14.1 Legacy Scenario Reconciliation

v0.14.1 重新核對 Scenario 001–095 與目前 canonical contracts，先修正規格漂移，再提升 automation evidence，避免把過時行為固定成自動化測試。

已修正的主要 drift 包含：

- Update Preflight：沒有 `.ai/` 的 Project 保持 EPHEMERAL，不再自動 Attach。
- Project Knowledge：新 reusable understanding 以 Project Intelligence + SOURCE_REGISTRY 為 canonical；`.ai/knowledge/` 僅保留 migration compatibility。
- Runtime instruction integration：Codex / Claude 使用 managed composition 保存既有使用者內容，不再因為檔案已存在就一律降為 MANUAL。
- Harness lifecycle：ownership 以 managed block / namespaced hook 為單位安全移除；使用者內容與 unrelated settings 必須保留。
- Runtime capability：Context Capability 與 Governance Enforcement 維持兩個獨立 truth axes。

新增 direct evidence：

- `tests/evidence/adapter_composition.py`
- `tests/evidence/project_intelligence_lifecycle.py`
- `tests/evidence/secret_safety.py`

只有這些 evidence 實際覆蓋的 legacy Scenario 才從 `manual` 提升為 `deterministic` / `lifecycle`。

v0.14.1 baseline：

~~~text
Total       115
Manual       77
Automated    38
Uncovered     0
Automated   33.0%
~~~

仍為 manual 的 Scenario 不代表失敗；它們通常包含需要 Agent judgment、Human decision、外部環境或跨文件語意評估的行為，目前不會為提高百分比而虛假標記為 automated。

## v0.15 Baseline

Canonical Project Identity / Resume Integrity 新增 Scenario 116–120，全部具 executable evidence：

~~~text
Total       120
Manual       77
Deterministic 15
Lifecycle    28
Agent Eval    0
Automated    43
Uncovered     0
Automated   35.8%
~~~

Identity/Resume evidence 同時驗證跨 worktree repository identity、dirty workspace STALE、legacy run migration、repository-wide Single Writer 與 Project Intelligence canonical namespace。

## v0.16 Agent Eval Conformance

需要 Agent 語意判斷的 Scenario 不再只能停留在 manual，也不會被硬改成 deterministic test。

流程：

~~~text
Eval Case
→ 任一 Provider / Runtime 的實際 Agent 執行
→ Observable structured response
→ Recorded Result
→ Case SHA-256 fingerprint binding
→ Deterministic rubric scoring
→ PASS / FAIL
~~~

AIPS Core 不在 CI 裡呼叫特定模型 API。CI 驗證的是已記錄的 observable Result 是否仍綁定目前 Case，以及 rubric 是否通過。

第一批 Agent Eval：

~~~text
017 Core Change Approval
019 System Self-Improvement
020 Constitutional Change
025 Avoid Duplicate Role
035 Requirement Clarification
041 Multi-Perspective Review
042 Author Fix / Targeted Re-review
094 New Skill Admission
~~~

另外新增 Scenario 121–125 驗證 Agent Eval framework 自身的 fingerprint、result binding、rubric、privacy/provider-neutral 與 lifecycle。

v0.16 baseline：

~~~text
Total         125
Manual         69
Deterministic  19
Lifecycle      29
Agent Eval      8
Automated      56
Uncovered       0
Automated     44.8%
~~~

Agent Eval Result 禁止保存 Chain-of-Thought、private reasoning、scratchpad 與 Secret-like value。Case 修改後舊 Result fingerprint 失效，必須重新執行 Agent，不可只改 fingerprint。

## v0.16.1 Focused Harness Evidence Maturity

不改 Harness 行為，只把已能以隔離 runtime fixture 真正重現的 legacy manual Scenario 升級為 lifecycle evidence：

~~~text
057 Global Harness Automatic Bootstrap
061 EPHEMERAL Project Does Not Auto-Attach
066 Gemini Namespaced Extension
067 Failed Adapter Uninstall Preserves Ownership
072 Gemini BeforeAgent Turn Context
073 Runtime Capability Truth
~~~

直接 evidence：`tests/evidence/harness_runtime_lifecycle.py`。

它驗證 managed composition、Gemini official extension link/uninstall、BeforeAgent、user GEMINI/settings preservation、EPHEMERAL resolve、Context Capability / Governance Enforcement truth，以及 uninstall failure → ownership preserved → safe retry。

v0.16.1 baseline：

~~~text
Total         125
Manual         63
Deterministic  19
Lifecycle      35
Agent Eval      8
Automated      62
Uncovered       0
Automated     49.6%
~~~

011 / 044 / 069 等仍維持 manual，直到有足夠隔離、完整的一對一 install/preflight evidence；不因鄰近 validator 而直接升級。

## v0.16.2 Install / Preflight Evidence Maturity

以完整隔離 fixture 實際執行 AIPS CLI，而不是只檢查 shell 文字：

~~~text
temporary AIPS Git repo
+ local bare origin
+ temporary product repo + bare origin
+ temporary HOME / XDG_CONFIG_HOME / AIPS_BIN_HOME
→ real aips preflight / attach / detach / uninstall / install
~~~

新增 direct evidence：`tests/evidence/install_preflight_lifecycle.py`。

它驗證：

- System repo 必須 clean 且在 main 才可自動 Update Preflight；
- 更新只允許 `git pull --ff-only`，diverged history 會停止；
- MAJOR version upgrade 必須顯式 `--allow-major`；
- 更新後會重新進入 updated CLI；
- EPHEMERAL project 不會被 preflight 自動 Attach；
- target product repository 不會被自動 pull；
- ATTACHED project 的 exact system version / commit provenance 會刷新；
- attach / status / detach / restore / uninstall lifecycle；
- default uninstall 保留 Project `.ai/`、External Intelligence、system repo 與 venv；
- explicit `--remove-cache --remove-venv` 才移除對應 AIPS-owned state；
- regular file / foreign symlink CLI collision 不會被覆寫；
- exact AIPS-owned CLI symlink 可安全重用。

Evidence 過程另外發現 Python import 產生的 `__pycache__/*.pyc` 會讓 System repo 被誤判 dirty，已透過標準 Python cache ignore 修正。

v0.16.2 baseline：

~~~text
Total         125
Manual         60
Deterministic  19
Lifecycle      38
Agent Eval      8
Automated      65
Uncovered       0
Automated     52.0%
~~~

Scenario 011 / 044 / 069 現在有直接 lifecycle evidence，才從 manual 升級；其餘 Scenario 仍依 evidence truthfulness 維持原分類。

## v0.16.3 Intelligence Context Evidence Maturity

新增 `tests/evidence/intelligence_context_lifecycle.py`，以隔離 Git project + XDG config 實際驗證：

- `SOURCE_REGISTRY.yaml` 保留 AGENTS / CLAUDE / GEMINI / official docs 為 pointer；
- `content_duplicated: false`，不把 authoritative source 複製成 derived Intelligence；
- Runtime native visibility 只標記真正由該 Runtime 自動載入的 instruction source；
- Turn Context 不重複注入 current Runtime 已 native-loaded 的 source；
- 非 native authoritative source 仍保留 targeted-load pointer；
- general knowledge / normal chat 可取得 compact Harness Context，但不會建立 `.ai/`、External Intelligence 或 Change Impact。

因此 Scenario 076 / 086 從 manual 升級為 lifecycle。

這次 audit 同時保留以下 Scenario 為 manual，因為目前 contract 尚未完整 deterministic enforce：

- 064：material instruction conflict surfacing；
- 082：new evidence 與 Project Override 的 contradiction conflict；
- 084：implementation 後 actual diff ↔ declared Change Impact reconciliation；
- 087：component-level monorepo lazy Intelligence selection；
- 088：legacy Project Knowledge migration 的 canonical artifact pointer mapping。

v0.16.3 baseline：

~~~text
Total         125
Manual         58
Deterministic  19
Lifecycle      40
Agent Eval      8
Automated      67
Uncovered       0
Automated     53.6%
~~~

## v0.16.4 Governance & Security Semantic Evidence Maturity

新增 5 組 provider-neutral Agent Eval，將目前仍需要 Agent semantic judgment 的高價值治理/安全 Scenario 從 manual 升級：

~~~text
018 Git Publish Approval
084 Change Impact Before Mutation
089 Secret Runtime Acquisition
091 Active Secret Exposure Blocks Release
095 New Skill Cannot Embed Private Configuration
~~~

這些 Scenario 不適合被簡化成「某個 helper 有跑」：

- 018 同時要求 publication plan、evidence、target 與 explicit approval/reapproval 行為；
- 084 要求 mutation 前 semantic impact + mutation 後 actual diff reconciliation；
- 089 要求安全 credential acquisition priority 與 missing credential fail-closed；
- 091 要求 active production/SAL3-4 exposure 阻擋 Release 並完成 rotation/revocation + exposure assessment；
- 095 要求 Skill admission 時把 private credential/config 移出 reusable Skill。

每組 evidence 都包含 exact Case fingerprint + 本次實際 GPT-5.6 Sol observable Result，CI 使用 deterministic rubric 驗證，不保存 Chain-of-Thought。

v0.16.4 baseline：

~~~text
Total         125
Manual         53
Deterministic  19
Lifecycle      40
Agent Eval     13
Automated      72
Uncovered       0
Automated     57.6%
~~~

## v0.16.5 Quality & Release Semantic Evidence Maturity

新增 6 組 Agent Eval：

~~~text
045 Quality Class Baseline
046 Quality Target Derivation
047 Local Complete Before Production
048 Explicit Production Request
049 Observability Before Vendor Selection
050 Audit Log for High-value Actions
~~~

它們驗證的是 Quality / Delivery decision，不把語意判斷假裝成 static schema test：

- Q2 是 typical production SaaS 的 baseline，但七個 quality dimensions 可獨立調整；
- 使用者不知道 p95 / RTO / RPO 時由 Agent 從 scale / failure impact / sensitivity / delivery / operations 推導 draft targets；
- 未明確要求 Production 時先完成 LOCAL_COMPLETE，再詢問是否繼續；
- 已明確要求 Production 時從一開始納入 infra / deployment / secret / recovery / observability，但仍必須先驗證 LOCAL_COMPLETE；
- Observability provider 未選定前保持 instrumentation provider-neutral；
- balance / points / refunds / role changes 使用獨立 Audit Log contract，不與一般 application logs 混為一談。

v0.16.5 baseline：

~~~text
Total         125
Manual         47
Deterministic  19
Lifecycle      40
Agent Eval     19
Automated      78
Uncovered       0
Automated     62.4%
~~~


## v0.16.6 Security & Production Readiness Semantic Evidence Maturity

新增 8 組 Agent Eval，涵蓋高風險金融邊界、低風險前端、critical product 的 cosmetic change、Security at Design/Release、Release Readiness、Production Verification、staging N/A 與 deployment access。

v0.16.6 baseline：

~~~text
Total         125
Manual         39
Deterministic  19
Lifecycle      40
Agent Eval     27
Automated      86
Uncovered       0
Automated     68.8%
~~~

核心原則維持 risk-proportional assurance：critical financial/stored-value boundary 使用 SAL4 floor；低風險 change 不因 product baseline 過度升級；production promotion 對 recovery、staging、security、health/smoke evidence fail-closed；缺少平台 access 時保留 runnable automation 但不得宣稱已部署成功。

## v0.16.7 Core Planning & Change Assurance Semantic Evidence Maturity

新增 9 組 Agent Eval：

~~~text
005 Existing Product Plan to Delivery
007 Adaptive DDD + Clean Architecture
009 Capability Gap
012 Documentation Impact Gate
013 Reproducible Planning Package
026 Deterministic Automation Before AI Parsing
027 Human / Agent Documentation Separation
092 Core Change Impact-derived Test Matrix
093 Core Change Scope Expansion Recomputes Tests
~~~

這批 evidence 驗證：

- 既有完整 planning 不重跑 discovery，只做 delivery sequencing；
- 小型 brownfield CRUD change 不為了方法論硬做 DDD / Clean Architecture rewrite；
- specialized capability gap fail-closed，generic role 不可猜；
- Core routing change 必須跑 Documentation Impact Gate 與 SemVer/scenario/diagram validation；
- primary product planning 需要 persistent workspace + reproducible package + Gate 1 / Gate 2；
- 大量 deterministic parsing 先使用 bounded tool/helper，再交給 AI reasoning；
- Human / Agent docs 分 audience 維護；
- Core Change test matrix 由 final Change Boundary 推導；
- material scope expansion 重新計算 tests/review/approval。

v0.16.7 baseline：

~~~text
Total         125
Manual         30
Deterministic  19
Lifecycle      40
Agent Eval     36
Automated      95
Uncovered       0
Automated     76.0%
~~~

## v0.16.8 Product & Visual Evidence Maturity

Promoted semantic evidence:

~~~text
001 Product Creation                         -> Agent Eval
003 Nordic Design Only                       -> Agent Eval
023 Mixed Reference Direction                -> Agent Eval
024 Create and Reuse a Brand System          -> Agent Eval
040 Visual Polish Redesign Escalation        -> Agent Eval
056 Project Visual Profile Reuse             -> Lifecycle
~~~

Scenario 056 now has executable design-state evidence through scripts/visual_profile.py and tests/evidence/visual_profile_lifecycle.py. The helper loads PROJECT_VISUAL_PROFILE.yaml first, validates last_verified_commit and watch paths against real Git history plus dirty state, returns REUSE when watched visual sources are unchanged, and returns TARGETED_REFRESH when shared visual sources changed. Missing/unusable baselines fail closed to FULL_DISCOVERY. Subjective visual archetypes remain inferred until approved.

The following visual scenarios intentionally remain manual:

~~~text
021 Vague Visual Request
022 User-owned Assets for Banner
039 Visual Polish Shared Component First
055 V2 Product Consistency Sweep
~~~

These scenarios require actual rendered composition, crop/safe-area, responsive/state or before/after visual evidence. The current repository-only validation harness has no verified renderer/screenshot provider, so text-only Agent Eval would not truthfully cover the full acceptance behavior.

v0.16.8 baseline:

~~~text
Total         125
Manual         24
Deterministic  19
Lifecycle      41
Agent Eval     41
Automated     101
Uncovered       0
Automated     80.8%
~~~

Architecture Diagram Impact: N/A. This release adds bounded evidence tooling beneath the existing Visual Polish / Project Visual Profile flow and does not change system topology.

## v0.16.9 Interaction & Context Evidence Maturity

Promoted evidence:

~~~text
008 Scoped Instruction Precedence             -> Agent Eval
010 Adaptive Subagent Model Routing            -> Agent Eval
036 Safe Default / No Unnecessary Question     -> Agent Eval
037 External Context Authorization Resume      -> Agent Eval
038 External Context Fallback                  -> Agent Eval
063 Normal Conversation Bypasses Heavy Flow    -> Lifecycle
065 Architecture Diagram Impact Required       -> Agent Eval
~~~

Scenario 063 reuses the executable `tests/evidence/intelligence_context_lifecycle.py` fixture: a general-knowledge turn is classified non-mutating, remains EPHEMERAL, and does not create project `.ai/`, External Project Intelligence, or Change Impact state.

Scenarios 008, 010, 036, 037, 038 and 065 use recorded observable Agent Eval responses bound to exact Case SHA-256 fingerprints and deterministic rubrics. The results contain no Chain-of-Thought/private reasoning/scratchpad or secret values.

The following roadmap targets intentionally remain manual in this release:

~~~text
064 Runtime + Project Instruction Composition
068 v0.7 -> v0.8 Harness Migration
082 Project Overrides Survive Refresh
~~~

Existing lifecycle evidence proves important adjacent behavior, but does not yet execute each complete acceptance contract: 064 still lacks direct material-conflict surfacing evidence; 068 lacks one end-to-end legacy-install-to-managed-Harness migration fixture; 082 lacks executable contradictory-discovery/approved-override conflict preservation.

v0.16.9 baseline:

~~~text
Total         125
Manual         17
Deterministic  19
Lifecycle      42
Agent Eval     47
Automated     108
Uncovered       0
Automated     86.4%
~~~

Architecture Diagram Impact: N/A. This release changes evidence/conformance metadata only and does not change runtime topology, Role, Skill, Capability, Approval Gate, or architecture behavior.

## v0.17.0 Project / Architecture Lifecycle Evidence Maturity

Promoted evidence:

~~~text
002 Existing REST API Change                    -> Agent Eval
006 Infrastructure Cost                        -> Agent Eval
029 Deployment Units vs Repository Strategy    -> Agent Eval
043 Review Learning Feedback                   -> Agent Eval
052 Project Intelligence Discovery             -> Agent Eval
088 Legacy Project Knowledge Migration         -> Lifecycle
~~~

Scenarios 002, 006, 029, 043 and 052 use observable Agent Eval responses bound to exact Case SHA-256 fingerprints and deterministic rubrics. Scenario 006 validates that recommendations require runtime-current price verification and explicitly avoids treating recorded fixture prices as current truth.

Scenario 088 executes a temporary Git project containing legacy `.ai/knowledge`, bootstraps canonical Project Intelligence, verifies migration provenance and pointer-over-copy authoritative sources, writes new reusable conclusions only to canonical Intelligence, finalizes READY, and confirms legacy knowledge remains byte-for-byte unchanged.

The following roadmap targets intentionally remain manual:

~~~text
004 API Performance
028 Complete Product to Production
054 Project Intelligence Promotion to Authoritative Source
087 Monorepo Lazy Intelligence
~~~

These scenarios require evidence that the current repository does not yet provide end to end: a reproducible benchmark/profile and measured p95; full staging-to-production lifecycle verification; approval-backed authoritative-source mutation and deduplication; and component-targeted monorepo lazy-loading execution. They remain manual rather than being partially promoted.

v0.17.0 baseline:

~~~text
Total         125
Manual         11
Deterministic  19
Lifecycle      43
Agent Eval     52
Automated     114
Uncovered       0
Automated     91.2%
~~~

Architecture Diagram Impact: N/A. This release changes evidence, conformance metadata and validation expectations only; it does not change runtime topology, Role, Skill, Capability, Approval Gate, Constitution, or canonical Project Intelligence behavior.

## v0.17.1 Residual Harness Migration Evidence Maturity

Promoted evidence:

~~~text
068 Legacy Installation to Managed Harness Migration -> Lifecycle
~~~

Scenario 068 now executes two temporary Git-system lifecycles. The installed-system path establishes managed Harness state, performs a remote AIPS update through `preflight`, proves the updated CLI is re-entered, refreshes managed adapter content, preserves pre-existing user instructions, and keeps a colliding foreign Gemini registration as `CONFLICT` / `MANUAL` without overwriting it. The plain-checkout path performs the same update/re-exec flow without an installation marker and proves no Global Harness state is registered implicitly.

Residual manual gap classification:

~~~text
004                         measured benchmark/profile evidence required
021 / 022 / 039 / 055       rendered/screenshot visual evidence infrastructure required
028                         complete staging-to-production delivery lifecycle required
054                         approval-backed authoritative promotion mutation required
064                         executable material instruction-conflict surfacing required
082                         contradictory discovery vs approved override preservation required
087                         component-targeted monorepo lazy-loading execution required
~~~

These remain manual rather than being promoted by partial or semantic-only evidence.

v0.17.1 baseline:

~~~text
Total         125
Manual         10
Deterministic  19
Lifecycle      44
Agent Eval     52
Automated     115
Uncovered       0
Automated     92.0%
~~~

Architecture Diagram Impact: N/A. This release adds executable evidence and conformance metadata only; it does not change runtime topology, Role, Skill, Capability, Approval Gate, Constitution, or managed Harness behavior.

## v0.18.0 Project Authority Reconciliation

Promoted evidence:

~~~text
082 Project Overrides Survive Refresh -> Lifecycle
~~~

Scenario 082 now executes a temporary Git project lifecycle: bootstrap Project Intelligence, persist approved overrides, advance repository evidence, bootstrap again, prove overrides survive, add later structured semantic discovery, reconcile it, persist a deterministic contradiction conflict, re-run reconciliation through the public CLI without duplication, and prove a mutating Turn Context surfaces the active authority conflict and fails closed.

The reconciler compares structured discovery assertions (`id` + `value` + evidence) with structured approved assertions. It does not parse arbitrary prose to manufacture semantic contradictions. This keeps Scenario 064 manual until direct material instruction-conflict detection has truthful executable evidence.

v0.18.0 baseline:

~~~text
Total         125
Manual          9
Deterministic   19
Lifecycle       45
Agent Eval      52
Automated      116
Uncovered        0
Automated      92.8%
~~~

Architecture Diagram Impact: N/A. v0.18.0 implements an already-defined Project Intelligence authority/reconciliation contract and adds no new system topology or governance layer.

## v0.18.1 Runtime / Project Instruction Conflict Composition

Promoted evidence:

~~~text
064 Runtime and Project Instruction Composition -> Lifecycle
~~~

The lifecycle fixture uses the same Project Authority conflict channel introduced in v0.18.0. It creates runtime-native `AGENTS.md` and an official ADR, records an unresolved material instruction conflict with source pointers and runtime scope, and resolves Turn Context for Codex. The evidence proves both sources remain present, `SOURCE_REGISTRY.yaml` resolves their authority/runtime visibility without copying content, derived Project Intelligence remains non-governing, precedence is explicit, runtime scoping prevents conflict leakage to another runtime, read-only work remains soft, and mutating work continues to fail closed through `unresolved_authority_conflict`. No semantic winner is invented automatically.

Residual manual Scenarios:

~~~text
004                         measured benchmark/profile evidence required
021 / 022 / 039 / 055       rendered/screenshot visual evidence infrastructure required
028                         complete staging-to-production delivery lifecycle required
054                         approval-backed authoritative promotion mutation required
087                         component-targeted monorepo lazy-loading execution required
~~~

v0.18.1 baseline:

~~~text
Total         125
Manual          8
Deterministic  19
Lifecycle      46
Agent Eval     52
Automated     117
Uncovered       0
Automated     93.6%
~~~

Architecture Diagram Impact: N/A. This release extends the existing Project Authority/context-resolution contract only; it introduces no runtime topology, Role, Skill, Capability category, Approval Gate or Constitution change.

## v0.18.2 Monorepo Lazy Intelligence

Promoted evidence:

~~~text
087 Monorepo Lazy Intelligence -> Lifecycle
~~~

Scenario 087 now executes a temporary Git monorepo with API, Admin and shared-auth areas. Project Intelligence is semantically enriched with explicit component and shared-relationship indexes. Turn Context with `--component api` resolves the system summary, API topic and shared auth relationship while proving the unrelated Admin topic is not preloaded. Context without an explicit component keeps component topics lazy. An unknown component fails explicitly rather than widening scope.

This release intentionally does not infer component identity from prompt text or folder-name heuristics and does not create a second Intelligence store.

v0.18.2 baseline:

~~~text
Total         125
Manual          7
Deterministic  19
Lifecycle      47
Agent Eval     52
Automated     118
Uncovered       0
Automated     94.4%
~~~

Residual manual gaps remain 004, 021, 022, 028, 039, 054 and 055.

Architecture Diagram Impact: N/A. This is an additive Project Intelligence selection contract and lifecycle-evidence change only; runtime topology and governance layers are unchanged.

## v0.18.3 Project Intelligence Promotion

Promoted evidence:

~~~text
054 Project Intelligence Promotion to Authoritative Source -> Lifecycle
~~~

Scenario 054 now executes a temporary Git project with a repeatedly confirmed derived invariant. The lifecycle proves recommendation is non-mutating, missing approval fails closed, a matching human/project approval in `PROJECT_OVERRIDES.yaml` permits creation of a new authoritative project document, `SOURCE_REGISTRY.yaml` records that source with promotion provenance and pointer-over-copy semantics, the duplicate derived topic file is removed, and Project Intelligence retains only an authoritative pointer. Existing authoritative targets are never overwritten automatically.

v0.18.3 baseline:

~~~text
Total         125
Manual          6
Deterministic  19
Lifecycle      48
Agent Eval     52
Automated     119
Uncovered       0
Automated     95.2%
~~~

Residual manual gaps remain 004, 021, 022, 028, 039 and 055.

Architecture Diagram Impact: N/A. This is an additive Project Intelligence / Project Authority lifecycle contract; runtime topology and governance layers are unchanged.



## Evolution / Human Documentation Namespace（Scenario 126–127）

目前 acceptance inventory 新增至 127 個 Scenario：

- **126 Evolution Radar Research With Human Decision**：使用 lifecycle evidence 驗證 bounded research、Semantic Analysis binding、Human Decision、Human-approved isolated Trial、scope/forbidden-path/no-commit guard、PASS/FAIL/BLOCKED Trial Report 與 Trial→ADOPT evidence binding。
- **127 Human Documentation Namespace**：使用 deterministic evidence 驗證永久 Human-only 文件集中於 `docs/human/`、shared canonical allowlist，以及外部 standalone Human artifact 的 registry + `HUMAN_` prefix 規則。

這兩項新增 coverage 都遵守既有原則：Scenario 數量只是規格 inventory；只有 direct evidence 真正覆蓋的行為才宣稱 automated coverage。

## Retrieval Intelligence（Scenario 128）

Scenario 128 新增 executable lifecycle evidence，驗證 Just-in-Time Retrieval Intelligence 不只是「有索引檔」：

- 會找出目標 implementation 與相關 tests；
- 可帶入符合任務的 Git history / diff evidence；
- 不把 unrelated module 塞進 bounded results；
- Dirty workspace 內容會先增量更新再被檢索；
- Secret / credential path 不會進入 index/output；
- 每筆結果都有 content hash + repository revision provenance；
- Token Budget 受到實際限制；
- 未設定 optional semantic provider 時明確回報 `NOT_CONFIGURED`，仍保留 local hybrid fallback。

目前 Scenario inventory 為 128，全部具有 deterministic / lifecycle / agent_eval automated evidence，manual 與 uncovered 都是 0。

## Retrieval Quality Evaluation（Scenario 129）

Scenario 129 用 temporary Git repository 真正執行 retrieval benchmark，而不是只檢查 YAML 是否存在。

測試會建立多組工程任務與 distractor files，並為每個 case 宣告：

- expected relevant source paths；
- relevant Git-history terms；
- v0.20-style static topic baseline；
- Top-K / Result Limit / Token Budget；
- Precision / Recall / MRR / history / irrelevant-context / direct-source delta 門檻。

CI 重新計算 Precision@K、Recall@K、F1@K、MRR、History Recall、Irrelevant Context Rate 與 token usage；Observed Latency 只記錄、不用來判定 CI PASS/FAIL，避免 shared runner 負載造成誤判。

這個 Scenario 也驗證 benchmark report 沒有權限自動：

- 啟用 Semantic / Embedding provider；
- 修改 ranking weights；
- 選擇 Tree-sitter / LSP / Sourcegraph；
- 變更 architecture 或 publication authority。

目前 Scenario inventory 為 **129**：20 deterministic + 55 lifecycle + 54 agent_eval，**129 / 129 automated、0 manual、0 uncovered**。

### Scenario 129 Corpus Maturity

Scenario 129 的 evidence corpus 進一步擴展為 9 cases：

- 6 個 **required** regression cases：Python、Go、TypeScript、SQL、monorepo/shared-module 與 test/history retrieval；
- 3 個 **diagnostic** stress cases：low lexical overlap / synonymy、cross-file call chain、credential-rotation 語意查詢。

Required case 失敗會照常 block CI；Diagnostic case 若未達 threshold，report 必須保留 FAIL 並彙總 gap dimensions，但不把探索性能力缺口誤當成 repository regression。這讓 CI 可以長期觀察「目前 local hybrid retrieval 做不到什麼」，又不必把 benchmark 門檻調低或假裝所有壓力案例都已解決。

## Structural Retrieval Candidate Trial（Scenario 130）

Scenario 130 把 v0.22.1 已發現的 cross-file structural gap 保留成可重播的 controlled candidate comparison。

同一個 temporary repository / 9-case corpus 明確跑：

- baseline：explicit structural OFF；
- candidate：explicit structural ON。

因此即使 Scenario 131 已正式採用 Structural Retrieval，Trial replay 仍能重現 adoption 前的比較，不會因 production default 改變而失去證據。

CI 要求：

- 6 個 required case 不得 regression；
- `cross-file-call-chain` baseline 必須仍能重現不完整 recall；
- structural candidate 必須把該 case 提升到完整 Recall@K；
- candidate ranking evidence 必須明確包含 `structural_reference_graph`；
- PASS 仍標記 `automatic_adoption=false`，Trial 本身不取得 merge/release authority。

## Structural Retrieval Adoption（Scenario 131）

Scenario 131 驗證 Human-approved adoption 後的正式行為：

- 一般 `aips intelligence retrieve` 預設 structural ON；
- Turn Context 預設 structural ON；
- evidence 明確顯示 `default_enabled=true`、`enabled=true` 與 traversal telemetry；
- `--no-structural` 可明確關閉 structural lane 做 debug / regression；
- 關閉 structural 不影響 lexical / symbol / test / Impact Graph / Git history 等其他 lanes；
- 不新增 Tree-sitter、LSP、Sourcegraph 或 remote provider dependency。

目前 Scenario inventory 為 **131**：20 deterministic + 57 lifecycle + 54 agent_eval，**131 / 131 automated、0 manual、0 uncovered**。

## Semantic Alias Expansion Candidate Trial（Scenario 132）

Scenario 132 保留 deterministic alias expansion 的完整負向 Trial evidence。

同一個 9-case corpus 比較：

- baseline：目前正式 Retrieval（包含 Structural Retrieval）；
- candidate：baseline + trial-only `semantic_alias_expansion`。

實測結果是 **FAIL / HOLD**：

- required regressions：`auth-token-expiry`、Go receipt reconciliation、TypeScript session refresh；
- registration baseline 已 Recall@K=1.0，但 candidate 造成 source-recall regression；
- `synonym-access-rotation` 仍無 source-recall improvement；
- semantic provider 仍是 `NOT_CONFIGURED`，沒有假裝跑過 Embedding。

CI 因此不是要求這個 candidate PASS，而是要求能穩定重播上述失敗、回傳 non-zero Trial status + `recommendation=HOLD`，並證明 `automatic_adoption=false` / `automatic_embedding_provider_enablement=false`。

這代表「先試 deterministic alias」研究項目已完成，答案是 **不採用**。若要研究真正 semantic/embedding retrieval，需另開 Human-reviewed Trial。

目前 Scenario inventory 為 **132**：20 deterministic + 58 lifecycle + 54 agent_eval，**132 / 132 automated、0 manual、0 uncovered**。

## Remote Embedding Retrieval Trial Readiness（Scenario 133）

Scenario 133 不要求正常 CI 呼叫外部 provider；它 deterministic 驗證「真實 embedding Trial 是否已安全準備好」。

驗證內容包括：

- secret 只透過 protected CI secret reference 注入；
- Trial 只可送 synthetic fixture，不可送 AIPS repository/product source；
- provider endpoint / model / dimensions / request limits 都有 machine contract；
- missing credential 必須回 `TRIAL_PENDING`；
- provider failure 必須回 `TRIAL_BLOCKED`；
- normal Retrieval / Turn Context 仍不啟用 embedding；
- Trial workflow 只綁定專用 feature branch + manual dispatch；
- workflow 會輸出 Human-readable GitHub Job Summary，明確區分 workflow SUCCESS 與 Trial PASS / FAIL / PENDING / BLOCKED；
- Summary 必須提供下一步，但不得輸出 credential 值；
- PASS / FAIL 都只是 evidence，Human Adoption Decision 仍是必要 gate。

目前 Scenario inventory 為 **133**：21 deterministic + 58 lifecycle + 54 agent_eval，**133 / 133 automated、0 manual、0 uncovered**。

## Provider-Neutral Local-First Embedding Trial（Scenario 134）

Scenario 134 將 Scenario 133 的 remote-only readiness 擴充為 local-first / remote-optional provider-neutral Trial，而且不改 production Retrieval。

Deterministic contract 會驗證：

- provider default 必須是 `local`；
- local runtime dependency 有明確 pin；
- local model = `BAAI/bge-small-en-v1.5`、384 dimensions，且 model revision 必須是 exact commit；
- local readiness 在沒有 `OPENAI_API_KEY` 時仍為 `READY`、credential_required=false、runner-local inference、inference_source_transfer=false；
- 顯式選擇 remote 且沒有 key 時仍為 `TRIAL_PENDING`；
- dedicated workflow 才安裝 semantic Trial dependency，normal PR/main validation 不執行 embedding model；
- Job Summary 對 local blocked 與 remote pending 提供不同且 truthful 的 operator guidance；
- repository source transfer、automatic provider/default enablement、production source transfer 與 adoption_without_human_decision 都維持 false。

目前 Scenario inventory 為 **134**：22 deterministic + 58 lifecycle + 54 agent_eval，**134 / 134 automated、0 manual、0 uncovered**。


## Deterministic Scheduler + Integration Gate（Scenario 135–136）

Scenario 135 用 lifecycle evidence 驗證多 Agent 工作不需要每一步再交給 LLM 協調：相同 Task Graph + state 必須得到相同 dispatch / fingerprint，dependency、max_parallel 與 Change Boundary lock 都由程式決定；cycle、stale/failed dependency 會 fail closed。

Scenario 136 用 temporary Git repository 真正建立 base/candidate commits，驗證 Integration Gate 綁定 exact base/head、changed-file hash 與 validation profile；HEAD 不符會 BLOCKED，required command 失敗會 FAIL，PASS 仍不取得 merge/release authority。

GitHub Actions 的 `repository` required check 保持相容，但改成只能在 `janitor` success 後通過。

目前 Scenario inventory 為 **136**：22 deterministic + 60 lifecycle + 54 agent_eval，**136 / 136 automated、0 manual、0 uncovered**。

## Agent Eval Repeatability（Scenario 137）

單次 Agent Eval PASS 只能證明「這一次」的 observable response 符合 rubric，不能代表相同任務重跑仍穩定。Scenario 137 因此沿用既有 Agent Eval Case / Result 契約，新增多次結果的一致性量測：每一筆都必須綁定同一個 Case fingerprint，先逐筆做 privacy / secret / stale validation 與 deterministic rubric scoring，再計算 repetitions、PASS rate、outcome consistency、unique observable-response fingerprints 與 exact response repeatability。

這個設計刻意把「答案文字是否完全一樣」和「行為是否持續符合契約」分開；不同措辭可以同時 PASS，但差異仍會被 fingerprint telemetry 看見。任何 stale/invalid evidence 都不能靠降低 pass-rate threshold 混過去。

CLI 可用：

~~~bash
aips conformance agent-eval consistency --case <case.yaml> --results-dir <runs/> --min-repetitions 5 --min-pass-rate 1.0
~~~

目前 Scenario inventory 為 **137**：22 deterministic + 61 lifecycle + 54 agent_eval，**137 / 137 automated、0 manual、0 uncovered**。


## v0.29 Resource-Scoped Agent Authorization

Scenario 138 新增 lifecycle evidence，驗證 default-DENY Resource Authorization Profile、明確 resource/operation grant、寫入操作 Change Boundary requirement、undeclared resource DENY、protected authority 不可由 profile 取得，以及 `runtime_enforced=false` 的 truthful reporting。

v0.29 capability candidate baseline：

~~~text
Total         138
Manual          0
Deterministic  22
Lifecycle      62
Agent Eval     54
Automated     138
Uncovered       0
Automated    100%
~~~

## Scenario 139 — Out-of-Band Agent Anomaly Evidence Evaluation

Scenario 139 新增一條**離線、deterministic、evidence-only** 的 anomaly benchmark，不把 anomaly detector 接到 production runtime。

固定 synthetic/sanitized corpus 共 11 cases（6 anomaly / 5 non-anomaly），直接重用 Resource Authorization Profile 作為授權真相，量測：

- TP / FP / TN / FN；
- precision / recall；
- false-positive rate / false-negative rate；
- 每個 case 的 detected anomaly types。

目前固定 fixture 的 evidence 為 TP=6、FP=0、TN=5、FN=0、precision=1.0、recall=1.0、FPR=0、FNR=0。這些數字只代表 source-controlled synthetic corpus，**不能外推為 production detection accuracy**。

Lifecycle 另外驗證 private reasoning / secret-like input 會 BLOCKED，且故意製造錯誤 expected label 時 benchmark 必須 FAIL。

輸出固定為 `POST_EXECUTION_EVIDENCE`、`runtime_enforced=false`、`critical_path=false`、`automatic_remediation=false`。PASS 只回傳 `HUMAN_REVIEW_TRIAL_EVIDENCE`，不代表 ADOPT 或 runtime integration approval。

目前 Scenario inventory 為 **139**：22 deterministic + 63 lifecycle + 54 agent_eval，**139 / 139 automated、0 manual、0 uncovered**。

## Scenario 140 — Agent Observable-Event Integration Controlled Trial

Scenario 140 把 v0.30.0 的 anomaly evaluator 往前推一層，但仍停留在 **replay-only Trial evidence**。

Human Decision 綁定 `main@e5e47b28a524352f7f549b49a40a294ddb50a364`，從 ASSESS 明確 override 到 TRIAL；Decision fingerprint 為 `sha256:3b3368af2d560a97e998500f680c48a14c1ed47fb496e54c0eac75cffc70ffb8`。

Trial 使用三種代表性 adapter-export dialect，把只允許的欄位正規化成 canonical observable event，再交給既有 Resource Authorization-backed Scenario 139 evaluator。任何未 mapping 的 raw field、private reasoning、secret-like value、stale Decision 都 fail closed。

12-case replay corpus 結果：

- TP=6 / FP=0 / TN=6 / FN=0；
- precision=1.0 / recall=1.0；
- FPR=0 / FNR=0；
- raw payload 不寫入 committed Trial report。

這些數字只代表 replay fixture。Trial 明確記錄 `live_capture_verified=false`、`runtime_enforced=false`、`critical_path=false`、`automatic_remediation=false`。

Trial status = **PASS**，但 recommendation 只有 `HUMAN_REVIEW_TRIAL_RESULT`，仍需另外的 Human Adoption Decision 才能進入正式 runtime integration / adoption review。

目前 Scenario inventory 為 **140**：22 deterministic + 64 lifecycle + 54 agent_eval，**140 / 140 automated、0 manual、0 uncovered**。

## Scenario 141 — Trial-backed Agent Anomaly Adoption Review

Scenario 141 把 Scenario 140 的 PASS Trial 接到一個**新的 current-baseline Human ADOPT Decision**，而不是重用 Issue #79 已 stale 的原始 Radar revision。

關鍵 binding：

- current adoption baseline：`main@a92a8d83c4cd6d2a04055312ebfa118d4df39f42` / v0.31.0；
- prior TRIAL Decision：`sha256:3b3368af2d560a97e998500f680c48a14c1ed47fb496e54c0eac75cffc70ffb8`；
- PASS Trial：`sha256:9270bab940c38558575490f4948589cf1ff3b6dc4477daf7eb0ff7caca4e187c`；
- Human ADOPT Decision：`sha256:c742a082dd00bd9e451810b5ce4640413e420b06acb97311db42112150b13f3e`；
- deterministic adoption binding：`sha256:1263e376a83926de458605f758b718fa6c7e0e3771d2ae19e6b53434f826ef89`。

ADOPT 的範圍只有「採用 live observable-event capture 的**設計方向**並完成 System Improvement Review」。本版本沒有 live runtime hook、沒有 runtime enforcement、沒有 automatic remediation，也沒有 semantic intent governance。

System Improvement Review 結論為 `SUITABLE_WITH_BOUNDS`：未來最小實作應延伸既有 Harness adapter，採 opt-in、metadata-only、POST_EXECUTION、out-of-band 設計；預設 disabled。

目前 Scenario inventory 為 **141**：22 deterministic + 65 lifecycle + 54 agent_eval，**141 / 141 automated、0 manual、0 uncovered**。

## Scenario 142 — Gemini CLI AfterTool Live-Capture Implementation Trial

Scenario 142 選擇 **Gemini CLI** 作為第一個 concrete runtime，因為目前 AIPS 已有 Gemini CLI extension 與 native hook integration，不另外建立 runtime framework。

本 Trial 新增真正的 `AfterTool` hook wiring，但 capture 預設仍為 disabled，只在顯式設定：

~~~bash
AIPS_OBSERVABLE_EVENT_CAPTURE=1
AIPS_OBSERVABLE_EVENT_CAPTURE_SINK=/tmp/aips-gemini-events.jsonl
~~~

時啟動。

v1 scope 僅涵蓋 `read_file|write_file|replace`，因此可以對 `network_used=false` 做誠實、deterministic 的 metadata mapping，不處理 shell / MCP / network tools。

Bounded fixture evidence：

- supported cases：6；
- captured：6；
- unexpected event loss：0；
- degraded / skipped cases：4；
- secret/private/raw leakage：0；
- raw payload persisted：false；
- capture subprocess overhead：CI 動態量測，8 samples，p95 必須 ≤ 1500 ms；repo 不提交會誤導的固定 runtime 數字。

Hook 永遠回傳 `decision=allow`，因此 capture failure 不會 deny 或改寫原 tool result，也不具 enforcement/remediation authority。不過 Gemini CLI 官方 hook execution 是同步的，所以 Trial 明確區分「無 flow-control authority」與「有同步 latency path」：`critical_path=false` 只指 authorization/result enforcement，並另外記錄 `synchronous_hook=true` / `latency_path=synchronous`。

CI 只驗證官方 AfterTool-shaped contract 與 source-controlled hook wiring；沒有執行真實 Gemini CLI binary，所以目前仍：

`live_runtime_execution_verified=false`、`live_capture_verified=false`。

目前 Scenario inventory 為 **142**：22 deterministic + 66 lifecycle + 54 agent_eval，**142 / 142 automated、0 manual、0 uncovered**。

## Scenario 143 — Gemini CLI Exact-Candidate Real-Runtime Verification

Scenario 143 使用固定的官方 Gemini CLI v0.60.0 bundled binary，實際跑完整 CLI → built-in tool → extension → AfterTool hook 路徑。

為了讓結果 deterministic 且不要求第三方 credential，model response 使用 Gemini CLI 官方 `--fake-responses` 測試介面；因此：

- `real_cli_binary_executed=true`
- `real_tool_execution_verified=true`
- `real_extension_hook_execution_verified=true`
- `live_runtime_execution_verified=true`
- Gemini CLI runtime-specific `live_capture_verified=true`
- 但 `fake_model_responses_used=true`
- `live_provider_session_verified=false`
- `provider_model_execution_verified=false`

驗證會真的執行 `read_file / write_file / replace`，確認 workspace mutation、3/3 canonical events、unexpected event loss=0、raw/private/secret leakage=0、disabled capture 不寫 sink，並將 workflow 綁定 exact PR head SHA。

Gemini extension manifest 同步宣告兩個 capture control env vars，避免 Gemini CLI 的 extension environment sanitization 在真實執行時把 opt-in 設定移除。

目前 Scenario inventory 為 **143**：22 deterministic + 67 lifecycle + 54 agent_eval，**143 / 143 automated、0 manual、0 uncovered**。

## Scenario 144 — Optional External Provider Credentials

Scenario 144 將外部 Agent / Provider credential 的新政策鎖成 deterministic conformance：AIPS 的正常運作不依賴外部 API Key，credential-dependent lane 只有在對應 credential 明確設定時才啟用。

驗證重點：

- 缺少 `GEMINI_API_KEY` 必須是 `SKIPPED_NOT_CONFIGURED`，不能視為 BLOCKED、FAIL 或 PASS；
- disabled report 必須保持 `provider_verification_enabled=false`、`required_for_release=false`；
- 沒有真實 provider evidence 時，`live_provider_session_verified=false`、`provider_model_execution_verified=false` 不得被改寫；
- 無 credential 時，provider-specific install 與 live provider/model execution 必須 SKIPPED；
- provider workflow 仍不得在 `pull_request` 事件取得 secret；
- 不得自動導入 OAuth、Vertex AI、GitHub OIDC / Workload Identity Federation 或其他 replacement login；
- 既有 Gemini CLI credential-free real-runtime / tool / AfterTool 驗證保持獨立可用；
- optional credential 缺失不阻擋 unrelated validation、merge 或 release。

目前 Scenario inventory 為 **144**：23 deterministic + 67 lifecycle + 54 agent_eval，**144 / 144 automated、0 manual、0 uncovered**。

## Scenario 145 — External Credential Dependency Guard

Scenario 145 把「外部 Agent / Provider Key 不得變成 AIPS baseline / release 必要條件」提升成 deterministic repository contract。

驗證內容：

- workflow / config / script 中出現的外部 credential 必須全部登記在 `config/external-credentials.yaml`；
- 新增未登記 Key 或未 allowlist consumer 會直接讓 repository validation 失敗；
- `GEMINI_API_KEY`、`OPENAI_API_KEY` 都固定為 optional，`required_for_baseline=false`、`required_for_release=false`；
- credential-consuming workflow 不得在 `pull_request` / `pull_request_target` surface 取得 external secret；
- Retrieval semantic Trial 的 default local path 不再取得 `OPENAI_API_KEY`，只有明確選 `remote` 的 step 才注入；
- Guard 只掃 source/config，不讀 secret value，也不執行 provider call；
- PASS 不授權 Human approval、merge、release、publication 或 credential creation。

目前 Scenario inventory 為 **145**：24 deterministic + 67 lifecycle + 54 agent_eval，**145 / 145 automated、0 manual、0 uncovered**。

## Scenario 146 — Evolution Radar Local Deterministic Pre-analysis

Scenario 146 將 Evolution Radar 的第一層 triage 做成完全 credential-free 的 deterministic lifecycle。

每次 weekly / monthly evidence 完成後，AIPS 會先用 source-controlled 規則分析「既有 title + evidence metadata」：

- topic category hints；
- 既有 AIPS Capability Map hints；
- recurrence bonus；
- title token Jaccard near-duplicate cluster；
- HIGH / MEDIUM / LOW Human review priority。

這個 priority 只是**閱讀順序**，不是 COVERED / HOLD / ASSESS / TRIAL / ADOPT 判斷。Local pre-analysis 必須維持：

- `semantic_suitability_inferred=false`；
- `recommendation_state_mutated=false`；
- semantic recommendation = `ANALYSIS_PENDING`；
- credential required = false；
- additional external network = false。

Lifecycle evidence 會重播相同輸入兩次並要求 artifact 完全一致，也驗證 near-duplicate、Capability Map references、tamper detection 與 Human review Issue embedding。

目前 Scenario inventory 為 **146**：24 deterministic + 68 lifecycle + 54 agent_eval，**146 / 146 automated、0 manual、0 uncovered**。

## v0.38 Repository Health Scenario

Scenario 147 covers the credential-free Repository Health / Architecture Drift detector as lifecycle evidence. The detector reuses the canonical Scenario Conformance registry/checker rather than introducing a second Scenario evidence model.

The released target for this increment is 147 automated Scenarios: 24 deterministic + 69 lifecycle + 54 agent_eval, with 0 manual and 0 uncovered. Repository Health PASS remains consistency evidence only and grants no code-change, PR, merge, release, publication or automatic-remediation authority.

## Scenario 148 — Repository Health Evidence Binding

Scenario 148 將 Repository Health 的 evidence truth 從「少數主要 digest」擴充成完整 deterministic input manifest。Capability targets、core surfaces、documentation bindings、Scenario inventory/evidence references、Scenario checker 與 Integration Gate contract files 都會進入 sorted manifest；存在的檔案記錄 SHA-256，不存在的 bound target 保留 `exists=false`。

同時 audit 明確區分 Git workspace：

- clean Git → `EXACT_REVISION` / `revision_reproducible=true`；
- staged / unstaged / untracked changes → `DIRTY_WORKTREE` / `revision_reproducible=false`；
- 非 Git fixture → `NO_GIT`。

Dirty workspace 本身不是 architecture drift，因此不會只因 dirty 就改成 `DRIFT_DETECTED`；但 evidence 不得再被描述成 exact-revision reproducible。相同 revision + workspace state + manifest + drift 會產生相同 evidence fingerprint。

目前 Scenario inventory 為 **148**：24 deterministic + 70 lifecycle + 54 agent_eval，**148 / 148 automated、0 manual、0 uncovered**。

## Scenario 149 — Repository Health Architecture Surface Inventory

Scenario 149 把 Repository Health 的「重大架構 surface」改成顯式、可驗證的 source-controlled inventory：`config/architecture-surfaces.yaml`。

目前 27 個 Capability Map ID 必須全部且只被分類一次；每個 major surface 同時綁定 required repository paths、canonical docs 與 validation paths。validation path 必須能追溯到 Scenario Conformance evidence，或是由 `tests/validate_repository.py` 匯入的 repository validator module。新增 capability 卻沒有分類、required path 消失、canonical doc 與 Capability Map 不一致，或 validation path 未被任何驗證入口綁定，都會產生 `architecture_surface_drift`。

`.github/workflows/validate.yml` 同時會產生 `repository-health-report.json` 並上傳為短期 CI artifact，供 exact-candidate review；artifact 只是 evidence，不具修復、PR、merge、release 或 publication authority。

目前 Scenario inventory 為 **149**：24 deterministic + 71 lifecycle + 54 agent_eval，**149 / 149 automated、0 manual、0 uncovered**。


## Scenario 150 — Repository Health 定期維護觀測

Scenario 150 驗證獨立的 Repository Health maintenance workflow：每週／手動執行、保存 deterministic JSON evidence、PASS 不建立 Issue、DRIFT_DETECTED 依 evidence fingerprint 去重通知並維持 workflow failure。此流程只有 Detect + Evidence + Human Review，沒有 contents-write、自動修復、implementation PR、merge 或 release authority。

目前 Scenario Conformance baseline 為 150 / 150 automated：24 deterministic、72 lifecycle、54 agent_eval、0 manual、0 uncovered。

## Scenario 151 — Evolution Radar 季度決定性檢視

Scenario 151 驗證 quarterly Radar 只聚合上一季三個月份的有效 monthly durable evidence，不重新抓取外部來源。Quarterly artifact 必須綁定 quarter/months、累積 recurrence，並把 recommendation 維持 `ANALYSIS_PENDING`，不得把 monthly semantic state 自動提升成季度採用結論。

目前 Scenario Conformance baseline 為 **151 / 151 automated**：24 deterministic、73 lifecycle、54 agent_eval、0 manual、0 uncovered。



## Scenario 152 — Technology Intelligence Expansion

Scenario 152 使用 Evolution Radar lifecycle evidence 驗證多社群研究擴充仍然 bounded 且受治理：至少 6 個 configured community sources、5 個成功來源健康門檻、每來源最多 8 筆、全域 raw signals 最多 50，並以 round-robin 保留來源多樣性。

Deterministic pre-analysis 進一步把 Human shortlist 限制為 12、semantic queue 限制為 10、actionable semantic recommendations 限制為 5；community-only evidence 不得直接產生 ADOPT，未進 semantic queue 的 signals 保持 ANALYSIS_PENDING。

目前 Scenario Conformance baseline 為 **152 / 152 automated**：24 deterministic、74 lifecycle、54 agent_eval、0 manual、0 uncovered。

## Scenario 153 — Evolution Evidence Quality and Primary Corroboration

Scenario 153 extends Technology Intelligence with a deterministic evidence-quality contract. Exact source provenance is converted into level 0–4 evidence strength without model inference: single-community discovery = 0, multi-community recurrence = 1, primary source = 2, primary + community = 3, and multiple primary sources = 4.

The minimum advisory ADOPT evidence level is 2. Semantic providers can assess only the evidence metadata produced by deterministic code; they cannot raise evidence strength. Monthly and quarterly rollups preserve the same provenance/quality semantics, and local pre-analysis may use only a bounded evidence-priority bonus.

Current automated inventory after Scenario 153:

- deterministic: 24
- lifecycle: 75
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 153 / 153

Evidence strength is advisory input only and grants no Human-decision, implementation, PR, merge, release or publication authority.



## Scenario 154 — Provider-neutral Controlled Trial Handoff

Scenario 154 keeps the Human-approved Controlled Trial contract usable when the optional OpenAI executor credential is unavailable. Provider resolution is bounded to `auto / openai-codex-action / handoff`; `auto` falls back to credential-free `TRIAL_HANDOFF_READY` instead of misclassifying a missing optional key as a failed experiment.

The handoff binds the exact baseline, Human Decision fingerprint, Trial fingerprint, approved scope/paths, forbidden paths, diff/file limits, worktree-isolation requirement and repository validation command. An external executor cannot self-assert PASS: AIPS deterministic scope/diff/repository validation remains required before PASS/FAIL Trial evidence exists.

Current automated inventory after Scenario 154:

- deterministic: 24
- lifecycle: 76
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 154 / 154

The handoff grants no PR, merge, release, publication or Human-adoption authority.


## Scenario 155 — Evolution Effectiveness Metrics and Feedback Loop

Scenario 155 validates a credential-free monthly effectiveness layer over durable weekly Evolution Radar evidence. It aggregates signal/duplicate volume, shortlist and semantic selection, semantic actionable states, Human Decisions, provider-neutral Trial handoffs, Trial outcomes and Trial→ADOPT bindings, then attributes downstream observations back to exact source provenance.

Per-source ratios are deterministic basis-point calculations. Low-yield, high-failure and zero-actionable conditions may emit Human-review flags only after minimum observation thresholds; automatic source weighting, enable/disable and configuration mutation remain forbidden.

Current automated inventory after Scenario 155:

- deterministic: 24
- lifecycle: 77
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 155 / 155

The monthly workflow requires no external Agent/provider credential and has only `contents: read + issues: write`. Effectiveness evidence cannot authorize implementation, PR, merge or release.


## Scenario 156 — Human-authorized Exact Branch Cleanup

Scenario 156 validates that normal branch hygiene stays report-only while a separately reviewed one-time manifest may delete only exact EPHEMERAL branch+SHA entries after complete-batch preflight. Any moved ref, non-ephemeral branch or non-integrated branch blocks the batch before deletion. Persistent/unclassified/pending branches remain preserved.

## Scenario 157 — Stale Evolution Issue Lifecycle Reconciliation

Scenario 157 binds Issue #79 to the current released truth, preserves COVERED and bounded ADOPT outcomes, keeps provider/model verification false where unproven, and marks semantic-intent governance DEFERRED. The stale Issue becomes ready to close; future positive progression requires fresh current-main evidence and a new Human Decision.

Current automated inventory after Scenario 157:

- deterministic: 24
- lifecycle: 79
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 157 / 157


## Scenario 158 — Verifiable Governance Audit Chain

Scenario 158 adds deterministic lifecycle evidence for long-lived AIPS governance auditability. Approval, security review, release and production boundary events can be canonicalized into a SHA-256 event hash and previous-chain binding. Editing or reordering evidence fails verification; suffix truncation is detectable when the auditor supplies a previously retained expected chain head/event count or an equivalent external checkpoint anchor.

HMAC-SHA256 authentication and Ed25519 signed checkpoints are optional secure-runtime layers. Their secrets/private keys are not baseline credentials and must not be persisted in Git, prompts, audit events or Actions artifacts. The audit ledger is evidence only and cannot create Human approval, merge, release, publication or production authority.

Current automated inventory after Scenario 158:

- deterministic: 24
- lifecycle: 80
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 158 / 158


## Scenario 159 — Portable Governance Audit Bundle

Scenario 159 validates offline transfer of v0.48 governance evidence without introducing a remote audit service. A deterministic bundle binds the exact repository revision, AUDIT.jsonl digest/event count/chain head, selected evidence digests and checkpoint public-key fingerprints. An exported ANCHOR binds that manifest and can be retained independently to detect later truncation or replacement.

Signed histories must verify with their public key before bundle creation. HMAC material and signing private keys are never persisted. Bundle verification detects tampered ledger/evidence/public key/anchor and missing files. The bundle remains evidence only and grants no approval, merge, release, publication or production authority.

Current automated inventory after Scenario 159:

- deterministic: 24
- lifecycle: 81
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 159 / 159


## Scenario 160 — Governance Audit Retention & Verification Policy

Scenario 160 adds deterministic provenance discovery and evidence-lifecycle review over existing portable Governance Audit Bundles. Catalog registration first verifies each bundle, records exact repository revision / chain head / manifest + anchor digests / evidence digests, and maintains a checkpoint key registry.

A checkpoint key ID may appear across multiple bundles only with the same public-key fingerprint; key rotation uses a distinct key ID. SAL 2+ operational defaults require an external retained anchor and SAL 4 registration requires signed checkpoint evidence.

Retention is advisory only. Expired full-bundle thresholds produce REVIEW_DUE plus a minimal digest record for Human review; the helper has no delete/compact operation, automatic_delete=false and deletion_authorized=false. Legal hold overrides time-based review. The configured day counts are operational defaults, not legal or regulatory retention requirements.

Current automated inventory after Scenario 160:

- deterministic: 24
- lifecycle: 82
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 160 / 160


## Scenario 161 — Parallel Runtime Port Isolation

Scenario 161 validates runtime-resource isolation for parallel AIPS-managed worktrees. Repository-scoped atomic lease coordination prevents duplicate AIPS port assignments, occupied host ports are skipped, Task Graph runtime requirements remain deterministic metadata, and the resulting environment manifest provides canonical AIPS port variables plus explicit aliases such as PORT.

Runtime resources have an independent lifecycle: a dirty worktree remains preserved while a stopped server lease can be released; clean isolation removal releases remaining leases; orphaned leases whose isolation is no longer ACTIVE can be reconciled. Bounded reallocation excludes the failed port for address-in-use recovery. v0.51 supports TCP only and grants no additional network, merge, release, publication or Human authority.

Current automated inventory after Scenario 161:

- deterministic: 24
- lifecycle: 83
- agent_eval: 54
- manual: 0
- uncovered: 0
- automated: 161 / 161

## Scenario 162 — MCP 互通閘道

Scenario 162 以官方 MCP Python Client 真正啟動 AIPS 的本機 stdio server，驗證 MCP 2026-07-28、Tools / Resources / Resource Templates / Prompts、Role/Skill 單一真實來源、Scheduler delegation、workspace 路徑隔離，以及 MCP-only 必須誠實回報 `ADVISORY`。

另外的 exact-candidate workflow 會安裝固定版 Codex CLI 0.155.1，以 `codex mcp add` / `codex mcp list` 驗證真實 Host 註冊路徑；不執行 provider inference，也不需要外部 Agent API Key。

目前 Scenario inventory：

- deterministic：24
- lifecycle：84
- agent_eval：54
- manual：0
- uncovered：0
- automated：**162 / 162**

## Scenario 163 — Human Documentation Site & Canonical Placement

Scenario 163 驗證 docs/human 是唯一 Human canonical source，VitePress 只負責 render/search/navigation；current-behavior 文件禁止 vX.Y / Scenario-style append headings，並用 deterministic placement mapping 驗證 subsystem change 是否真正修改對應 topic section。

Installation evidence 同時驗證 macOS/Linux managed installer、Windows WSL PowerShell launcher contract、bootstrap compatibility 與 Linux install/doctor/uninstall lifecycle。

目前 Scenario inventory：

- deterministic：24
- lifecycle：85
- agent_eval：54
- manual：0
- uncovered：0
- automated：**163 / 163**

## Scenario 164 — MCP Tool-Only Host Compatibility

Scenario 164 驗證只支援 MCP Tools 的 Host 仍能透過唯讀 catalog／read／workflow Tools 取得 canonical Roles、Skills、allowlisted protocols 與 Security／Architecture／Code Review、Delivery Plan context，不複製 registry，也不在 Server 內執行第二個模型。

官方 MCP Python Client lifecycle 同時驗證 tool annotations、錯誤 ID fail-closed、workspace confinement、protected authority 維持 false，以及 Cursor／Windsurf／GitHub Copilot CLI／Amp／Codex／generic review-only JSON。MCP 仍為 `ADVISORY`，native adapters 維持獨立。

目前 Scenario inventory：

- deterministic：24
- lifecycle：86
- agent_eval：54
- manual：0
- uncovered：0
- automated：**164 / 164**

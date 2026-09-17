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


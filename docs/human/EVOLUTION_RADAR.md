# Evolution Radar 持續演進研究

Evolution Radar 是 AIPS 的**研究、語意分析與建議層**，目的在於定期觀察外部技術訊號，找出可能值得評估的改進方向；它不是自動改版機制，也沒有權限自行修改 AIPS。

完整 Human 圖解版請閱讀 [`EVOLUTION_RADAR_OVERVIEW.html`](EVOLUTION_RADAR_OVERVIEW.html)，技術與專有名詞整理於 [`TECHNOLOGY_GUIDE.html`](TECHNOLOGY_GUIDE.html)。

## Weekly Signal Scan

GitHub Actions 每週執行 bounded scan：從 `config/evolution-sources.yaml` 讀取至少 5 個公開來源，每來源最多 5 筆；記錄來源、URL、日期與失敗來源；正規化 URL／標題、去重、建立 machine-readable evidence。若 repository 已安全配置 `OPENAI_API_KEY`，排程會以 pinned `openai/codex-action` 執行 read-only semantic analysis；沒有 credential、provider 執行失敗或輸出驗證失敗時，仍誠實保持 `ANALYSIS_PENDING`。最後才發布 `Evolution Radar [weekly] ...` GitHub Issue。

來源失敗會被記錄，不會推測補齊；0 個 actionable recommendation 是合法結果。

## Public-only 網路安全

`public_only: true` 是執行邊界：只接受 credential-free HTTPS；拒絕 localhost/private/link-local/reserved/non-global destination；DNS 後若任何位址非 global public 即 fail closed；連線使用已驗證 IP 並保留原 hostname 做 TLS/SNI；每個 redirect 重新驗證、拒絕 HTTPS downgrade；response bytes 與 redirect depth 都有上限。

## Monthly Deep Review

Monthly 不重跑 weekly，而是讀取前一月 Weekly Issues 的 evidence，重新去重並累積 recurrence，避免同一熱門主題每週都被當成新技術。

## Recommendation 狀態

- `COVERED`：AIPS 已有實質能力；
- `HOLD`：證據／成熟度／關聯性不足；
- `ASSESS`：值得進 System Improvement Review；
- `TRIAL`：值得 bounded experiment，但需明確批准 scope；
- `ADOPT`：證據支持改進方向，但仍只是建議；
- `ANALYSIS_PENDING`：只有 collection evidence，沒有可靠 semantic analyzer。

`TRIAL` / `ADOPT` 都不是 implementation approval。

## Provider-neutral Semantic Analysis（供應商中立語意分析）

Deterministic collector 負責 network safety、bounded collection、provenance、fingerprint、deduplication、recurrence、schema validation。是否值得導入則需要 semantic reasoning。

AIPS 使用：

- `scripts/evolution_analysis.py`
- `config/evolution-analyzer.yaml`
- `templates/evolution/EVOLUTION_ANALYSIS.yaml`
- `templates/evolution/EVOLUTION_ANALYZER_RESULT.schema.json`
- `templates/evolution/EVOLUTION_ANALYZER_PROMPT.md`
- `references/evolution/CAPABILITY_MAP.yaml`

可靠 Analyzer 必須把結果綁定 exact Radar `evidence_digest` + `repository_revision`，並對每個 signal 說明 current state、gap、benefit、cost/complexity、reliability/security、maturity、confidence、uncertainty、evidence refs、簡單案例、reuse/extension path 與 architecture-diagram impact。

如果沒有可靠 analyzer，必須維持 `ANALYSIS_PENDING`，不能因為熱門度／關鍵字自行產生 `ADOPT`。

Semantic provider 只產生 recommendation payload；`evidence_digest`、`repository_revision`、provider metadata 與所有 authority=false 欄位由 deterministic Python 包裝與驗證，避免模型自行改寫治理事實。Analyzer 使用 `:read-only` permission profile、`drop-sudo` safety strategy，且不取得 repository write authority。

## Human Decision Binding（人類決策綁定）

研究 Issue 本身不是批准。Human 使用 `.github/workflows/evolution-decision.yml` 明確指定：Radar Issue、signal fingerprint、`REJECT/HOLD/ASSESS/TRIAL/ADOPT`、reason，以及 TRIAL/ADOPT 的 exact approved scope。`TRIAL` 另外必須提供 repository-relative `approved_paths` globs，讓實驗的實際 diff 可被 deterministic guard 驗證。

Decision Record 會綁定 candidate、signal、evidence digest、baseline repository revision、CURRENT/STALE、advisory recommendation、Human decision、scope、actor/time、next action 與 decision fingerprint。

正向推進 `ASSESS/TRIAL/ADOPT` 若 baseline 已不是 current revision 會 fail closed。Human 仍可 override advisory recommendation，但 reason 必須以 `override:` 開頭留下 audit evidence。

| Human decision | next action |
|---|---|
| `REJECT` | `close_candidate` |
| `HOLD` | `continue_monitoring` |
| `ASSESS` | `system_improvement_review` |
| `TRIAL` | `controlled_trial_execution` |
| `ADOPT` | `system_improvement_review` |

Evolution Radar 與 Decision workflow 都只有 `contents: read` + `issues: write`，沒有 remote code-write / PR / merge / release authority。TRIAL Agent 只可在 GitHub-hosted runner 的 AIPS-managed isolated worktree 中做 ephemeral workspace mutation，且 checkout 不持久化 GitHub credentials。

## Human Authority

~~~text
Radar evidence / recommendation
→ Human Decision Record
→ System Self-Improvement Review
→ Core / Constitutional Gate（適用時）
→ Implementation + Tests + Review
→ Documentation Consistency Check
→ Git Publish Proposal
→ Human publication approval
→ PR / Merge / Release
~~~

## 手動執行

`evolution-radar` workflow 支援 `weekly` / `monthly`；`evolution-decision` workflow 用來記錄 Human Candidate Decision。

## 文件同步

Evolution Radar 的 scripts/config/template/workflow/reference 發生設定範圍內的異動時，Documentation Consistency Contract 會要求同步更新：

- `docs/human/EVOLUTION_RADAR.md`
- `docs/human/EVOLUTION_RADAR_OVERVIEW.html`
- `orchestration/EVOLUTION_RADAR.md`
- `orchestration/EXECUTION_ISOLATION.md`
- `docs/human/TECHNOLOGY_GUIDE.html`

詳細規則見 [`DOCUMENTATION_SYNC.md`](DOCUMENTATION_SYNC.md)。

## Human-approved Controlled Trial（受控實驗）

當 Human 選擇 `TRIAL`：

~~~text
Human Decision + approved scope + approved paths
→ verify CURRENT baseline + decision fingerprint
→ AIPS-managed Git worktree
→ Codex :workspace / no network / no persisted checkout credential
→ smallest reversible prototype
→ deterministic diff guard
   - approved path match
   - forbidden path rejection
   - max changed files / diff lines
   - no trial commit
→ repository validation
→ Trial Report comment
→ Human Adoption Decision
~~~

若 `OPENAI_API_KEY` 不存在、worktree isolation 建立失敗或 Agent 執行失敗，Trial 回報 `BLOCKED`，不會降級到 shared workspace。

Trial workspace 是 ephemeral evidence environment；它不直接成為正式實作 branch，也不會 push prototype。Human 看完 Trial Report 後仍需另外決定 Reject / Hold / Adopt。

### Trial → ADOPT Evidence Binding（實驗採用證據綁定）

如果 Human 是依據某次 PASS Trial 決定 `ADOPT`，可以在同一次 `evolution-decision` workflow 填入該 Trial Report 的 exact `trial_fingerprint`。系統會 deterministic 驗證：

- fingerprint 在同一 Radar Issue 中只對應一份合法 Trial Report；
- Trial 狀態必須是 `PASS`；
- Candidate、signal fingerprint 與 baseline revision 必須和新的 ADOPT Decision 完全一致；
- 最終只產生 `system_improvement_review` handoff，不取得 code-write、PR、merge、release authority。

Human 仍可不經 Trial 直接做 ADOPT，但這種情況不會被標記為「Trial-backed adoption」。

## 目前仍不包含

- Quarterly Evolution Review；
- Trial PASS 後自動 Adopt；
- 自動建立正式 implementation PR；
- 自動 merge；
- 自動 release。

`ADOPT` 仍只會 handoff 到既有 System Self-Improvement Review。正式實作、驗證與發布繼續受 Core / Constitutional / Git Publish gates 管理。

## v0.27 Provider-neutral handoff

每次 Radar 都先建立可重建的 semantic analysis package。OpenAI Codex Action 只是 optional adapter；沒有 `OPENAI_API_KEY` 時不再只留下「無法分析」資訊，而會在同一個 Issue 附上 provider-neutral handoff：

- exact repository revision / evidence digest / package digest；
- Capability Map、Analyzer Prompt、Result Schema 路徑；
- 可由 ChatGPT、其他已連線 Agent、local model 或其他 provider 產生結果；
- 最後仍由 deterministic finalize/apply 驗證結果是否綁定正確 evidence。

沒有真正語意結果時狀態仍是 `ANALYSIS_PENDING`，不會假裝已完成適配性判斷。

## v0.29 Current-main capability baseline and Issue #79 reassessment

Evolution Radar semantic comparison MUST use a Capability Map that reflects the exact current-main capabilities. After v0.29.0, `references/evolution/CAPABILITY_MAP.yaml` explicitly includes Resource-Scoped Agent Authorization so future analysis does not rediscover an already-covered least-privilege gap.

Issue #79 runtime-security reassessment is recorded in `references/evolution/ISSUE_79_RUNTIME_SECURITY_REASSESSMENT.yaml`. The record is advisory evidence only:

- Resource-Scoped Agent Authorization = `COVERED` on current main.
- Out-of-band Agent anomaly evidence remains `ASSESS`; it is a bounded Trial candidate only after an observable-event contract and deterministic evaluation corpus exist.
- Semantic intent governance remains `ASSESS`; any future Trial must be monotonic with deterministic authorization: semantic reasoning may only DENY / ESCALATE / narrow authority, never grant an operation denied by Resource Authorization.
- No assessment result grants implementation, runtime enforcement, automatic remediation, merge, release, publication, destructive operation or Human approval authority.

## Issue #79 — Agent Anomaly Evidence Evaluation（Scenario 139）

Out-of-band anomaly candidate 目前仍是 **ASSESS**，但其前置驗證已從「只有概念」提升為可重播 deterministic benchmark：

~~~bash
python scripts/agent_anomaly_evaluation.py evaluate \
  --profile tests/fixtures/agent_anomaly_evaluation/profile.yaml \
  --corpus tests/fixtures/agent_anomaly_evaluation/corpus.yaml
~~~

Evaluator 直接 reuse Resource Authorization，不新增權限系統。固定 corpus 同時包含正常成功、預期 DENY、一般失敗與已標記 anomaly；CI 計算 TP/FP/TN/FN、precision、recall、FPR、FNR。

這是 **evaluation evidence**，不是 Evolution Human Decision Record，也不是 production anomaly detector。PASS 只表示「這組 deterministic rule 在固定 synthetic corpus 上達到門檻」，下一步仍需 Human review 才能決定是否值得設計真正 observable-event integration Trial。

Semantic intent governance 仍維持 ASSESS，沒有在本 Scenario 順便加入。

## Issue #79 — Observable-Event Integration Trial（Scenario 140）

Repository maintainer 已在 current v0.30.0 baseline 上明確授權 anomaly candidate 由 ASSESS 進入 bounded TRIAL。Durable evidence：

- `references/evolution/ISSUE_79_AGENT_ANOMALY_TRIAL_BASELINE.yaml`
- `references/evolution/ISSUE_79_AGENT_ANOMALY_TRIAL_DECISION.yaml`
- `references/evolution/ISSUE_79_AGENT_OBSERVABLE_EVENT_TRIAL_RESULT.yaml`

Trial 不是 live runtime hook。它只 replay synthetic/sanitized representative adapter exports，將 whitelisted fields 正規化為 canonical observable events，再重用 Scenario 139 anomaly evaluator。

結果是 PASS（12 cases，TP=6 / FP=0 / TN=6 / FN=0），但只代表這組 replay corpus。AIPS 仍沒有 verified live capture、runtime enforcement 或 automatic remediation。

因此目前狀態是：

- Resource-Scoped Agent Authorization：COVERED；
- Out-of-band Agent anomaly：**TRIAL PASS → awaiting separate Human Adoption Decision**；
- Semantic intent governance：仍為 ASSESS，未隨本 Trial 導入。

## Issue #79 — Trial-backed Human ADOPT + System Improvement Review（Scenario 141）

v0.31.0 的 replay Trial 已 PASS，因此本輪不再重用 stale 的原始 Radar baseline，而是建立 v0.31.0 current-main adoption baseline，再記錄獨立 Human ADOPT Decision。

Durable evidence：

- `references/evolution/ISSUE_79_AGENT_ANOMALY_ADOPTION_BASELINE.yaml`
- `references/evolution/ISSUE_79_AGENT_ANOMALY_ADOPTION_DECISION.yaml`
- `references/evolution/ISSUE_79_AGENT_ANOMALY_ADOPTION_BINDING.yaml`
- `references/evolution/ISSUE_79_AGENT_ANOMALY_SYSTEM_IMPROVEMENT_REVIEW.yaml`

這次 ADOPT 的意思是「採用設計方向」，不是「已啟用 production capability」。

System Improvement Review 的最小解：

~~~text
runtime adapter
→ opt-in POST_EXECUTION metadata exporter
→ strict sanitizer / whitelist mapping
→ canonical observable event
→ bounded out-of-band evaluation
→ Human evidence review
~~~

未來若要真的接某個 runtime，必須另開 bounded implementation Trial，證明 runtime-native hook、資料清理、event-loss/overhead 與 exact candidate validation。

目前狀態：

- Resource-Scoped Agent Authorization：COVERED；
- Agent anomaly evaluator：COVERED as evidence lane；
- Observable-event replay integration：TRIAL PASS；
- Live observable-event capture：**ADOPTED DESIGN DIRECTION / NOT IMPLEMENTED**；
- Semantic intent governance：仍為 ASSESS。


# Evolution Radar 持續演進研究

Capability Map 也涵蓋 Runtime Context、驗證直譯器選擇與 runtime invariant matrix；Radar 用於比較演化訊號，不改寫其執行政策。

Evolution Radar 是 AIPS 的 maintenance plane。它把外部技術研究、evidence quality、Human Decision 與 bounded Trial 接回正常 System Self-Improvement / Core Change / Git Publish 流程，但本身不取得 implementation、merge 或 release authority。

## Weekly Signal Scan

Weekly collection 只讀 source-controlled allowlist 中的 public sources，保存 provenance、publication time、source class、normalized identity 與 dedup evidence。

## Evidence Quality

Turn Context routing 的變更應以 route lifecycle、compact Manifest、hook compatibility 與 fixed-core measurements 作為可重現證據；route coverage 不表示治理圖完整。

Community signal 主要用於 discovery；較高強度的 recommendation 需要 primary-source corroboration。Deterministic evidence level 不可被 semantic analyzer自行提高。

## Deterministic Pre-analysis

Evolution evidence keeps its existing digest facade while using the shared canonical JSON/hash implementation; the frozen lifecycle vectors protect stable fingerprints without changing Human relevance decisions.

The `evolution_analysis.py` command remains the entry point. Its deterministic, credential-free title and metadata pre-analysis is implemented in `evolution_preanalysis.py`; this internal split preserves existing outputs and review boundaries.

Pre-analysis now records deterministic exclusion reasons for signals that do not reach the shortlist or semantic queue (`NO_CATEGORY_MATCH`, `LOW_PRIORITY`, `SHORTLIST_CAP`, `DUPLICATE_SUPPRESSED`, and `SEMANTIC_CAP`). These explain the local classifier and queue behavior only; they do not assert that a signal is product news, already covered, or outside AIPS scope. Monthly source-yield flags still require complete pre-analysis evidence and Human review.

本機規則處理 category hint、capability mapping、near-duplicate grouping、review priority 與 funnel metrics。這些輸出不等於 semantic suitability，也不會改 recommendation state。

## Semantic Analysis

可靠 analyzer 必須把結果綁定 exact evidence digest + repository revision。沒有可靠 analyzer 或 credential 時保持 truthful ANALYSIS_PENDING / SKIPPED_NOT_CONFIGURED，不偽造 PASS。

## Human Decision Binding

Human Decision 綁定 candidate、evidence、baseline revision、scope、actor/time 與 decision fingerprint。若 baseline stale，positive decision 必須先重新取得 current-main evidence。

## Controlled Trial

TRIAL 只在 approved scope / paths 與 AIPS-owned isolation 中執行。Trial runner 驗證 forbidden paths、diff size、repository validation 與 evidence fingerprint；external executor 不可 self-assert PASS。

## Trial → ADOPT

Trial PASS 只提供 adoption review evidence。正式 ADOPT 必須是新的 Human Decision，並綁定 exact PASS trial fingerprint，再 handoff 到 System Self-Improvement Review。

## Optional Provider Credentials

External Agent/provider credentials 永遠是 optional enhancement；缺少 credential 不得阻擋 unrelated baseline/release。Secret 不進 Git、Issue body、Prompt、logs 或 ordinary evidence artifact。

## Effectiveness Feedback

OpenCode adapter 的採用證據分開記錄 projection lifecycle 與指定版本的 native discovery；未知平台與模型使用行為保持 UNVERIFIED。

Effectiveness evidence retains the existing digest facade over shared canonical JSON hashing; no trial ranking or Human disposition changes.

本機預分析會為未入選候選記錄可重現的排除原因與彙總計數，供人工檢視 shortlist 的資料價值；語意判斷與採納決策仍由既有流程負責。

Standalone and shadow dependency-review artifacts retain exact base/head, run ID, actual JSON findings and outcome for 90 days. Parity compares canonical findings; missing outputs, different candidates or inaccessible artifacts stay UNKNOWN. Job success alone cannot promote the shadow. Record resolved toolchain fingerprints and repeat full Gates only for new changes or unresolved failures.

When an analysis workflow uses the shared Python bootstrap, its caller declares the import profile and tested dependency constraints so missing imports fail visibly.

CLI module extraction preserves the existing public command surface; Evolution collection and effectiveness records remain unchanged by this internal refactor.

Maintenance suggestions about selective validation use the shadow cohort as evidence only; no Radar recommendation may activate validator skipping without a separate Human decision.

Monthly/quarterly reports separate pipeline completeness from content value. Missing source cohorts or incomplete periods remain UNKNOWN/incomplete; a complete period with no actionable recommendation is a valid zero-yield result. Validated analysis is persisted in the GitHub Issue body so scheduled runs retain the reviewed state.

The quarterly Radar rollup runs on day 3 of January, April, July and October, after the monthly Radar and Effectiveness reports have time to publish. Missing monthly evidence remains explicitly incomplete.

Monthly Effectiveness also tracks pre-analysis coverage for source-bearing weekly Issues. When a weekly Issue lacks pre-analysis, per-source shortlist yield is unavailable and the report names the missing Issue; it never interprets absent triage evidence as a zero shortlist. If a complete Issue body exceeds GitHub's size limit, the workflow stores a bounded, lossless zlib/Base64 envelope with a SHA-256 digest. Roll-up consumers restore and verify the complete original body before reading evidence; invalid or oversized archives are not accepted as evidence.

An unreadable archived weekly Issue remains visible in its title-derived monthly cohort and raises a separate Human-review flag. Oversized Issue bodies keep the summary readable while preserving the complete original report in the verified archive.

Operational observations from the read-only Parallel Run Dashboard may inform review, but never become automatic adoption or publication decisions.

The scheduled Python compatibility smoke is maintenance evidence about supported runtime behavior, not a Radar effectiveness metric or an automatic adoption signal.

Monthly / quarterly roll-up 量測 collected → shortlist → semantic → actionable → Trial → PASS → ADOPT、duplicate rate 與 failure evidence。Low-yield / high-failure 只產生 Human-review flags，不自動調整 source weights 或 enable/disable settings。Schedule 與相同月份的手動執行共用 repository/cohort queue；最多保留 100 筆 pending 執行，不取消執行中或排隊中的報告，自訂月份各自排隊。

`scripts/evolution_relevance.py` creates a reproducible monthly sample of 20 signal fingerprints and measures shortlist precision, shortlist recall, actionable yield, and per-source relevance yield against explicit Human labels. The sample does not copy article text, and the production label file starts empty; missing, uncertain, or incomplete labels keep the report `NOT_READY`. Evaluation never changes the shortlist, source policy, provider handoff, or `ANALYSIS_PENDING` state. A recommendation to review source policy still requires a separate Human decision.

- Release readiness is a separate deterministic evidence gate; Evolution metrics do not imply an empty Unreleased section or authorize a tag.
## Current Boundaries

`SYSTEM_CORE.md` 為固定核心；協定依 task classification 漸進載入。任務 route resolution 不代表完整 enforcement，也不改變各 Runtime 已驗證的治理強度。

Task ownership leases and dashboard projections are operational coordination evidence, not Radar signals or Human adoption decisions. They cannot promote a candidate or grant publication authority.

Runtime evidence changes preserve provenance: evaluation results state whether they match the current system, and operational spans reflect measured stage boundaries. Historical unbound results remain historical signals and cannot claim current effectiveness.

Plan19 的 2026-09 月報快照（`.aips/review/PLAN19_EVOLUTION_EFFECTIVENESS.yaml`）觀測到 100 筆 raw／unique signals、0 shortlist；100 筆仍為 `ANALYSIS_PENDING`，4 份 weekly Issue 缺少 pre-analysis，留下 5 個 source review flags。資料覆蓋不完整，這份報告不支持調整來源分數或權重。

GitHub Actions workflows 使用固定 Ubuntu 24.04 runner；Node runtime 相容性依賴各 action 的官方版本支援，artifact action 使用完整 SHA pin 並需在升級時重新驗證。

Trajectory Quality Gate 的 deterministic trace evidence 可作為 Agent 行為品質的觀測輸入，但不會自動產生演進採用決策；任何 provider 或 LLM Judge 建議仍須經 Human Decision 與既有受控 Trial 流程。

Portable Commands 是既有 Turn-Aware Global Harness 的低權限投影，不是新的 Capability ID，也不會自行升級 Runtime enforcement、Human approval 或 Git authority。新增 Host integration 仍須先經能力驗證與相容性證據。

Runtime Policy Enforcement 是決定性安全邊界；optional semantic provider 只能補充拒絕或升級人工審批，不能產生授權或覆蓋 policy DENY。採用外部語意 provider 仍須依本文件的 Human Decision 與 Controlled Trial 流程。
Evolution Radar 不做：

- 自動修改 AIPS code；
- 自動建立 implementation PR；
- 自動 merge / release；
- 自動提升 provider credential 為 baseline requirement；
- 以 deterministic keyword score 冒充 semantic adoption decision。

## Verification History

Scenario 230 保留固定核心 byte limit、相對 base 的縮減比例，以及十種分類和混合任務路由的驗證紀錄。

Scenario-by-scenario 的歷史與數值證據集中在 [Scenario Conformance](CONFORMANCE.md)。Current behavior 不再以 vX.Y / Scenario append 形式堆在本頁尾端。

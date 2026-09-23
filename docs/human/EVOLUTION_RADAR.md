# Evolution Radar 持續演進研究

Evolution Radar 是 AIPS 的 maintenance plane。它把外部技術研究、evidence quality、Human Decision 與 bounded Trial 接回正常 System Self-Improvement / Core Change / Git Publish 流程，但本身不取得 implementation、merge 或 release authority。

## Weekly Signal Scan

Weekly collection 只讀 source-controlled allowlist 中的 public sources，保存 provenance、publication time、source class、normalized identity 與 dedup evidence。

## Evidence Quality

Community signal 主要用於 discovery；較高強度的 recommendation 需要 primary-source corroboration。Deterministic evidence level 不可被 semantic analyzer自行提高。

## Deterministic Pre-analysis

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

Operational observations from the read-only Parallel Run Dashboard may inform review, but never become automatic adoption or publication decisions.

Monthly / quarterly roll-up 量測 collected → shortlist → semantic → actionable → Trial → PASS → ADOPT、duplicate rate 與 failure evidence。Low-yield / high-failure 只產生 Human-review flags，不自動調整 source weights 或 enable/disable settings。

## Current Boundaries

Trajectory Quality Gate 的 deterministic trace evidence 可作為 Agent 行為品質的觀測輸入，但不會自動產生演進採用決策；任何 provider 或 LLM Judge 建議仍須經 Human Decision 與既有受控 Trial 流程。

Portable Commands 是既有 Turn-Aware Global Harness 的低權限投影，不是新的 Capability ID，也不會自行升級 Runtime enforcement、Human approval 或 Git authority。新增 Host integration 仍須先經能力驗證與相容性證據。
Evolution Radar 不做：

- 自動修改 AIPS code；
- 自動建立 implementation PR；
- 自動 merge / release；
- 自動提升 provider credential 為 baseline requirement；
- 以 deterministic keyword score 冒充 semantic adoption decision。

## Verification History

Scenario-by-scenario 的歷史與數值證據集中在 [Scenario Conformance](CONFORMANCE.md)。Current behavior 不再以 vX.Y / Scenario append 形式堆在本頁尾端。

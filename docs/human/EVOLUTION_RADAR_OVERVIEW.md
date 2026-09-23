# Evolution Radar 流程總覽

Evolution Radar 是 AIPS 的 maintenance plane，用來研究外部技術變化，但不直接取得 implementation / merge / release authority。

## Signal Collection

Weekly scan 從 source-controlled allowlist 收集 bounded public evidence，保存 provenance、publication time、dedup identity 與 source class。

## Deterministic Pre-analysis

本機 deterministic rules 做 category hint、capability mapping、near-duplicate grouping 與 review priority。這不是 semantic suitability 或 adoption recommendation。

## Semantic Analysis

可靠 semantic analyzer 若可用，結果必須綁定 exact evidence digest + repository revision；不可用時保持 ANALYSIS_PENDING，不偽造 PASS。

## Human Decision

Human 可選 REJECT / HOLD / ASSESS / TRIAL / ADOPT。Positive decision 若 baseline 已 stale，必須先重新取得 current-main evidence。

## Controlled Trial

TRIAL 使用 approved scope / paths 與 AIPS-owned isolation。執行後檢查 forbidden paths、diff size、repository validation 與 evidence fingerprint。

## Trial → Adoption

Trial PASS 只表示 trial evidence 可供 review。正式 ADOPT 必須是新的 Human Decision，綁定 exact PASS fingerprint，再回到正常 System Self-Improvement / Core Change / Git Publish 流程。

## Provider Credentials

External provider credential 永遠是 optional enhancement，不得變成普通 Radar、baseline validation 或 release prerequisite。Missing credential 使用 truthful SKIPPED / PENDING state。

## Effectiveness Feedback

Agent trajectory evidence 可回饋至後續 regression scenario，但不具備自動修改、merge、release 或 publication authority。

Monthly / quarterly roll-up量測 collected → shortlist → semantic → actionable → Trial → PASS → ADOPT funnel 與 duplicate / failure evidence；指標只產生 Human-review flag，不自動改 source weight 或系統設定。
Portable Command Core 的 Registry、renderer、ownership conflict 與 MCP read-only contract 沿用既有 Harness capability；Host-native integration 維持後續候選。

## Verification History

Scenario-by-scenario 的演進與數值證據放在 [Scenario Conformance](CONFORMANCE.md)，不再把每個版本/Scenario追加到本頁尾端。

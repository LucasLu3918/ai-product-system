# Evolution Radar 流程總覽

Deterministic local pre-analysis remains available through the `evolution_analysis.py` facade; its implementation resides in `evolution_preanalysis.py` and does not grant semantic or publication authority.

本期資料會分開呈現 `pipeline_health`（來源 cohort、收集失敗、重複及期間完整性）與 `content_value`（訊號是否形成可採用建議）。來源缺漏或月份未結束時是資料不完整，不能解讀為零價值；來源完整但沒有可採取建議則是有效的零產出。通過 evidence digest 驗證的分析會寫回 GitHub Issue body，避免下一次排程遺失分析狀態。

本機命令沿用既有流程：`aips evolution package` 建立分析輸入、`aips evolution analyze` 完成分析、`aips evolution apply` 套用已核准決策。命令本身不授權程式碼變更或發布。

目前 Capability Map 納入 Runtime Context 與 runtime invariant matrix，供後續 Radar 比較與趨勢追蹤。

Evolution Radar 是 AIPS 的 maintenance plane，用來研究外部技術變化，但不直接取得 implementation / merge / release authority。

## Signal Collection

Offline relevance evaluation compares selected/rejected signals with explicit Human labels. Unlabeled or uncertain records produce `NOT_READY`; the evaluator reports metrics but never changes source policy.

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

GitHub Actions 的 Ubuntu runner 固定在 24.04，artifact upload action 維持已驗證的完整 SHA pin；runtime 升級需先驗證 action 與 runner 相容性。

## Provider Credentials

External provider credential 永遠是 optional enhancement，不得變成普通 Radar、baseline validation 或 release prerequisite。Missing credential 使用 truthful SKIPPED / PENDING state。

## Effectiveness Feedback

每月由 deterministic fingerprint 排序抽取 20 筆 signal 供 Human 標註；離線評估 shortlist precision/recall、actionable yield 與來源 relevance yield。資料不完整時維持 `NOT_READY`，結果只提供來源政策檢視建議，不會自動調整來源權重或 shortlist。
The monthly Effectiveness report leaves shortlist yield unavailable when a source-bearing weekly Issue lacks pre-analysis. Oversized weekly Issue bodies use a bounded SHA-256 checked archive restored before the monthly rollup reads evidence.

If archive verification fails, the monthly report names that unreadable Issue and keeps it under Human review; it is not silently omitted from the cohort.


Task ownership leases and Dashboard projection are execution operations, not Radar decisions. They cannot adopt a candidate, approve a Trial, or grant publication authority.

Effectiveness evidence distinguishes current system-bound evaluations from historical results without a source fingerprint. Optional operation spans report observed duration and outcome only when a matching run record is available.

The read-only Parallel Run Dashboard is an observation surface for parallel workflow state; it does not create an Evolution decision or merge authority.

Agent trajectory evidence 可回饋至後續 regression scenario，但不具備自動修改、merge、release 或 publication authority。

Runtime Policy Enforcement 不交由 Evolution Radar 語意分析授權；外部語意訊號只能收緊決定性決策，且 provider 仍屬 optional trial。

Monthly / quarterly roll-up量測 collected → shortlist → semantic → actionable → Trial → PASS → ADOPT funnel 與 duplicate / failure evidence；指標只產生 Human-review flag，不自動改 source weight 或系統設定。
Portable Command Core 的 Registry、renderer、ownership conflict 與 MCP read-only contract 沿用既有 Harness capability；Host-native integration 維持後續候選。

## Verification History

Scenario-by-scenario 的演進與數值證據放在 [Scenario Conformance](CONFORMANCE.md)，不再把每個版本/Scenario追加到本頁尾端。

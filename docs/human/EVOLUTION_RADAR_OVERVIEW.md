# Evolution Radar 流程總覽

Evolution Radar（演進雷達）負責蒐集外部技術訊號、整理證據並安排受控試驗，協助 AIPS 評估值得研究的改進。它不會自行修改系統、採納候選方案或授權發布。

流程會明確區分「資料是否完整」與「訊號是否有用」：來源資料缺漏時標示輸入不完整；來源完整但沒有可執行建議時，才記錄為零產出。指標與分析結果都供人審查，不會自動調整來源政策或系統設定。

## Signal Collection

每週從版本控制的來源清單蒐集有界公開資料，保存來源、發布時間、去重識別與來源類別等 provenance。採樣至少需要五個可用來源；每個來源最多取十筆，原始訊號總數最多五十筆。去重後未達目標時回報缺口，不以重複資料補足。

## Deterministic Pre-analysis

本機預分析使用固定規則整理類別、能力對應、相似訊號與檢視優先順序，並記錄可重現的排除原因。這些結果是排序線索，不會判斷方案是否值得採用，也不會代替語意分析或人類決策。

## Semantic Analysis

若使用語意分析，結果必須綁定完整的 evidence digest 與 repository revision。資料不足、分析服務不可用或來源無法驗證時，狀態維持 `ANALYSIS_PENDING` 或 `NOT_READY`，不會填入推測結果。

## Human Decision

人類審查者可選擇 `REJECT`、`HOLD`、`ASSESS`、`TRIAL` 或 `ADOPT`。正向決策必須使用目前仍有效的證據；若基準版本已過期，需先針對目前 main 重新取得證據。

## Controlled Trial

`TRIAL` 只能在核准範圍與檔案路徑內執行，並使用 AIPS 管理的隔離環境。完成後檢查禁止路徑、變更大小、repository validation 與 evidence fingerprint。Trial 結果證明的是該次受限試驗的觀測，不代表正式採納。

## Trial → Adoption

Trial 通過只表示證據可供審查。正式 `ADOPT` 必須由人類另行決定，並綁定該次 `PASS` fingerprint，再進入一般 System Self-Improvement、Core Change 與 Git Publish 流程。

## Provider Credentials

外部分析 Provider 的 credentials 是選用條件，不是一般 Radar、基準驗證或 release 的必要依賴。缺少 credentials 時明確回報 `SKIPPED` 或 `PENDING`，不會透過其他帳號或服務自動補足。

## Effectiveness Feedback

Core scanner hardening (including WebM metadata coverage) remains under its Core Change Matrix and publication Gate; passing those checks does not create an Evolution Trial or adoption decision.

Evaluation control data stays outside indexed product sources so expected answers cannot contaminate retrieval measurements; optimization decisions remain Human-reviewed.

每月可依 deterministic fingerprint 抽樣供人工標註，離線評估 shortlist precision／recall、可採取建議比例與來源關聯性。輸入不完整時維持 `NOT_READY`；分析只會提出檢視政策的建議，不會自動調整來源權重或候選清單。

每月與每季摘要會呈現蒐集、shortlist、semantic analysis、actionable 建議、Trial、PASS 與 ADOPT 的流程指標，也會標示重複或失敗資料。統計只提示人類檢視。缺少分析、歷史資料不完整或 evidence archive 無法驗證時，都會明確保留為未完成／待檢視。

## Verification History

逐項驗證案例與版本化證據見[情境驗證紀錄](CONFORMANCE.md)。歷史數字不代表未來趨勢；本機 fixture 或安裝狀態也不能證明模型品質、Runtime enforcement 或外部 Provider 的實際效果。


查看更多現行命令與證據要求，請閱讀 [Evolution Radar 使用指南](EVOLUTION_RADAR.md)。所有採納、實作與發布仍沿用各自的人類審查與授權流程。

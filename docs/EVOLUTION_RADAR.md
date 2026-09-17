# Evolution Radar 持續演進研究

Evolution Radar 是 AIPS 的**研究與建議層**，目的在於定期觀察外部技術訊號，找出可能值得評估的改進方向；它不是自動改版機制，也沒有權限自行修改 AIPS。

## 運作方式

### 每週 Signal Scan

GitHub Actions 每週執行一次 bounded scan：

1. 從 `config/evolution-sources.yaml` 讀取公開技術來源；
2. 至少配置 5 個來源；
3. 每個來源最多取 5 筆候選訊號；
4. 記錄來源、URL、發布／擷取時間與失敗來源；
5. 正規化 URL／標題並去除重複訊號；
6. 建立 machine-readable evidence；
7. 發布 `Evolution Radar [weekly] ...` GitHub Issue 供 Human review。

來源失敗會被記錄，不會用推測資料補齊。

### 每月 Deep Review

每月流程不是單純再跑一次 weekly scan，而是讀取先前 weekly Issue 中的 evidence，重新去重並累計 recurrence，形成月度 roll-up。

這可避免同一個熱門主題每週都被當成「全新技術」。

## Recommendation 狀態

Radar contract 支援：

- `COVERED`：AIPS 已經具備實質能力；
- `HOLD`：值得觀察，但證據／成熟度／關聯性不足；
- `ASSESS`：值得進一步進行 AIPS System Improvement Review；
- `TRIAL`：可能值得做 bounded experiment，但 experiment 需要另外批准；
- `ADOPT`：證據支持具體改進方向，但仍然只是建議；
- `ANALYSIS_PENDING`：目前只有 collection evidence，沒有可靠 semantic analyzer，因此不推論是否適合導入。

`TRIAL` 與 `ADOPT` 都**不是 implementation approval**。

## Provider-neutral truthfulness

Deterministic collector 能可靠完成：

- source config validation；
- bounded collection；
- provenance；
- fingerprint；
- deduplication；
- recurrence；
- evidence schema validation。

「技術是否真的值得導入 AIPS」需要 semantic reasoning。如果排程環境沒有可靠 analyzer，Radar 必須輸出 `ANALYSIS_PENDING`，不能因為文章熱門就自行產生 `ADOPT` 結論。

未來可以接不同 AI provider，但核心 evidence contract 不綁特定模型／廠商。

## Human Authority

Evolution Radar GitHub workflow 只需要：

- `contents: read`；
- `issues: write`。

它沒有 code-write / pull-request / merge / release authority。

真正的系統修改仍然必須走：

~~~text
Radar evidence / recommendation
→ Human 決策
→ System Self-Improvement Review
→ Core / Constitutional Gate（適用時）
→ Implementation + Tests + Review
→ Git Publish Proposal
→ Human publication approval
→ PR / Merge / Release
~~~

## 手動執行

GitHub Actions 的 `evolution-radar` workflow 支援 `workflow_dispatch`：

- `weekly`：執行當次 source scan；
- `monthly`：讀取既有 weekly Radar Issues 並建立月度 roll-up。

## 目前不包含

v0.19.0 初始範圍刻意不包含：

- Quarterly Evolution Review；
- 自動建立 experiment worktree；
- 自動修改程式碼；
- 自動建立 implementation PR；
- 自動 merge；
- 自動 release。

這些能力若未來需要，應重新進行 System Improvement Review，而不是從 Radar report 隱性取得權限。

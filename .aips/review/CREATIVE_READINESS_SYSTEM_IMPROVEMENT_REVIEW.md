# System Improvement Review: Creative Readiness and Diagnostics

**Appropriateness:** 有條件適合。這是 AIPS 核心創作執行邊界，必須遵守 Core Change matrix、exact-candidate Gate 與文件同步要求。

**User problem:** design5 中 ComfyUI 配置欄位無法由 OpenCode 工具傳遞；MFLUX 版本探測失敗容易被理解成引擎不可用；一般 discovery 不會找已啟動的本機 ComfyUI；Apple Silicon FP8 風險缺少靜態提示。

**Proposed solution:** 修 schema、增加引擎 discovery、MPS/FP8 相容性檢查、恢復指引、兩角色生成與品質/效能評估。

**Existing coverage:** executor 已支援 Z-Image Turbo 的四個 ComfyUI 欄位、loopback `/system_stats`/`/object_info` 預檢、固定工作流、`generate-set` 與雜湊驗證恢復；執行器已分開記錄推論、檔案有效性與人工視覺審查。

**Reuse / extension candidates:** `scripts/creative_execution.py`、`harness/adapters/opencode/plugin.ts`、現有 creative lifecycle/contract、Scenario 236、既有 `generate-set`、manifest 和 bounded trace。新增能力不需要另一個 Provider、命令、Role、Skill、Capability 或 Judge。

**Lower-layer alternative:** 在既有 executor 與 adapter 層修復 schema/診斷，不新增全域抽象。只探測固定 `127.0.0.1:8188`，保留使用者明確設定其他服務的既有 bundle preflight 行為。

**Context / token cost:** 僅增加按需的本機診斷欄位與文件，不增加常駐 Context、模型請求、提示詞保存或外部索引服務。

**Security / reliability:** 唯讀 loopback GET、固定命令、限時限量、無下載/外連/自動 inference；未取得 dtype/硬體證據時保留 `UNVERIFIED`。不改創作授權或輸出覆寫規則。

**Backward compatibility:** OpenCode schema 欄位為選填；Bundle v1、CLI、reason code、manifest/trace 與 generate-set 不變。

**Scenario / test impact:** 覆蓋 MFLUX 命令存在但版本探測失敗、ComfyUI reachable/unavailable、Z-Image Turbo 欄位傳遞、FP8/FP16/BF16/unknown dtype、工作流不提交、兩角色部分成功與可恢復。mock 不能宣稱實際推論成功。

**Human docs impact:** 更新 User Guide、Conformance、Architecture Overview、`docs/ARCHITECTURE.md`、Changelog 與 Version。

**Agent docs impact:** 僅當 OpenCode schema/使用方式改變時更新 adapter guidance；本次 schema 為補欄位，不改授權，檢查後可列 N/A。

**Architecture diagram impact:** 更新 `docs/ARCHITECTURE.md` 中既有 creative flow 的 discovery/readiness 標註；無新增或受影響的 SVG 圖。

**Constitution impact:** NO。理由：不改人類授權、資料優先序、停線規則或發布治理。

**Recommended AIPS solution:** 採用窄幅 executor/adapter 擴充；用狀態欄位明確區分 command、runtime、model、preflight 與 inference；Apple Silicon FP8 以證據觸發提示，未知保持未驗證；ComfyUI discovery 僅連固定 loopback。沿用 generate-set 和人工品質 review。

**Additional optimization candidates:** 無新增候選。真實硬體 benchmark、生成時間/記憶體比較與視覺品質評估列為另外的本機驗證工作；不在 deterministic CI 中執行模型，也不偽造結果。

**Expected scope:** `CREATIVE_READINESS_CORE_CHANGE_PROPOSAL.md` 所列程式、測試、Scenario 236、核心文件、矩陣與版本/變更紀錄。

**Risks:** loopback 埠可能有非 ComfyUI 服務；以端點格式驗證分類。FP8 檔名不一定揭露實際權重 dtype；警示不取代真實推論。受限環境可能無法跑完整本機 Gate。

**Approval:** 使用者在本 Codex 任務中確認「核准」；核准範圍如上，遠端發佈仍受 exact-candidate Git Publish Approval gate 約束。

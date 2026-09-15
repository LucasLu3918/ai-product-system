# 使用範例

以下範例展示「使用者怎麼說」以及系統預期如何路由。它們不是固定指令格式，自然語言即可。

## 範例 1：建立完整購物網站

**使用者**

> 我要製作一個購物網站。

**預期行為**

- Work Mode：Product Creation
- 先做需求探索，不直接寫程式。
- 只詢問會影響產品方向的關鍵資訊。
- 產生 PRD、UX、Architecture、Design、Implementation Plan 等必要成果。
- 先交由使用者檢視整體 Planning Package。
- 使用者核准後才進入 Implementation。
- 可測試行為預設使用 TDD，完成後由獨立 Reviewer 檢核。

---

## 範例 2：只做北歐風網站設計

**使用者**

> 幫我設計北歐風家具網站，提供 3 個不同樣式，不需要寫後端。

**預期行為**

- Work Mode：Design
- 載入 Visual / UX 相關角色與 Skill。
- 不載入 Backend、Database、DevOps 等無關內容。
- 需要時提出 2–3 種清楚不同的視覺方向。
- 將成果寫入 Workspace 的設計文件與必要視覺素材。
- 完成後請使用者檢視與選擇方向。

---

## 範例 3：修改既有 REST API

**使用者**

> 幫我在這個專案的 REST API 加入日期篩選功能。

**預期行為**

- Work Mode：Engineering Change
- Project State：Brownfield
- 先檢查 endpoint、handler/service/repository、相關 test 與專案慣例。
- 建立最小 Change Boundary。
- 只載入需要的 Backend / REST / Language Skill。
- 若存在更好的 API contract 選擇且會影響相容性，先提出方案等待決定。
- 實作後測試並由獨立 Reviewer 檢查。

---

## 範例 4：API 效能優化

**使用者**

> 幫我把 `/orders` API 的 p95 response time 壓到 2 秒以下。

**預期行為**

- Work Mode：Performance Optimization
- 先建立 baseline，再 profiling，不直接猜瓶頸。
- 初始只載入 Performance 相關能力。
- 若量測顯示 SQL 是主要瓶頸，再擴充 Database / SQL Profiling Skill。
- 優化後重新 benchmark，確認目標達成且沒有 regression。
- 無量測證據不得宣稱達標。

---

## 範例 5：已有產品規劃書，只排執行流程

**使用者**

> 我已經有完整產品規劃書，請幫我規劃製作流程與執行順序。

**預期行為**

- Work Mode：Delivery Planning
- 不重新做 Product Discovery，除非規劃書存在阻塞缺口。
- 分析需求依賴、Work Breakdown、Milestone、Critical Path 與主要風險。
- 輸出 Implementation Order / Delivery Plan。
- 不直接修改程式。

---

## 範例 6：估算雲端成本

**使用者**

> 幫我估算目前專案需要的環境、後端機器規格，以及 AWS、GCP 或其他託管服務大約多少錢，並推薦較適合的方案。

**預期行為**

- Work Mode：Cost Analysis
- 先整理流量、儲存、資料庫、網路、可用性等必要假設。
- 缺少關鍵 workload 時，以 Scenario + 明確 Assumption 呈現，不假裝是精確成本。
- 動態價格必須在執行當下重新查證。
- 比較 TCO、維運複雜度、擴充性與可靠性，不只看單一 VM 價格。
- 提供推薦方案與 Confidence。

---

## 範例 7：現有能力不足

**使用者**

> 幫我規劃大型 WebRTC 即時影音平台。

**假設目前沒有 WebRTC 專業 Skill**

**預期行為**

- 停止相關設計，不讓一般 Backend Role 猜測完成。
- 說明 Capability Gap。
- 先建議最小必要能力，例如 `realtime-media` Capability + `webrtc` / `stun-turn` / `media-scaling` Skills。
- 只有新的責任與決策權限真的需要獨立承擔時才建議建立專門 Role。
- 使用者確認後才新增並繼續原任務。

---

## 範例 8：系統發現更適合的做法

**使用者**

> 幫我把所有查詢都加 Redis，讓 API 變快。

**預期行為**

系統不直接大量加入 Cache，而先指出：

- 尚未證明目前瓶頸來自可被 Cache 改善的查詢。
- 全面 Cache 可能增加一致性、失效策略與維運成本。
- 推薦先量測慢點，再決定哪些讀取路徑值得 Cache。

因為這會實質改變架構與成本，所以先讓使用者選擇，再進入實作。

## 範例 9：DDD / Clean Architecture 不過度套用

**使用者**

> 在既有小型 CRUD API 加一個 nickname 欄位，程式設計套用 DDD 與 Clean Architecture。

**預期行為**

- 先檢查既有架構與 Change Boundary。
- 系統指出完整 DDD 重構對這個局部需求可能是過度設計。
- 建議保留既有架構，只套用必要的依賴邊界、測試與清楚的 domain naming。
- 因為這會改變使用者原本指定的架構做法，先等待使用者決定，再進入實作。
- 若是訂單、付款、庫存等複雜領域，才按需載入 DDD Skill 並評估 bounded context / aggregate。

## 範例 10：使用者指定與專案 AGENTS.md 衝突

**專案規則**

`AGENTS.md`：所有公開 API 使用 REST，不新增 GraphQL。

**使用者**

> 這個新查詢功能我希望改用 GraphQL。

**預期行為**

- 系統辨識到目前使用者指示與既有專案規則衝突。
- 若只是實作細節可局部處理；若引入第二套公開 API paradigm 會影響架構/維運，先列出影響與選項。
- 使用者確認後，本次任務依使用者決策執行。
- 若使用者只要求本次例外，不修改永久 `AGENTS.md`。
- 若使用者明確要求未來專案都支援 GraphQL，則將更新專案權威規則/ADR 納入工作成果。

## 範例 11：同一任務的 Subagent 使用不同模型等級

**使用者**

> 幫我優化訂單 API，並確認資料庫瓶頸與安全風險。

**預期行為**

- Primary Agent 先做範圍、風險與 profiling 規劃，不預先載入所有專業內容。
- 若量測顯示 SQL 是主要瓶頸，可建立唯讀 Database Subagent，只載入相關 query/schema + `sql-performance` Skill。
- 若 endpoint 涉及付款或敏感資料，可建立 Security Reviewer Subagent，只載入相關 contract/security context + `secure-design` Skill。
- 每個 Subagent 依自己的技術複雜度與風險獨立決定 Tier，不繼承 Primary Agent 的模型。
- 一般程式修改可使用 Tier 2；SQL 深度分析或安全檢核可能使用 Tier 3；只有真正 critical 的決策才升 Tier 4。
- Subagent 不得同時修改同一 Change Boundary；最終由單一 Writer 實作，Reviewer 獨立檢核。

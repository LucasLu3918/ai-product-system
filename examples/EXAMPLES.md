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


## 範例 12：每次實作前安全更新系統

**使用者**

> 使用 ai-product-system 幫我修改這個專案的 API。

**預期行為**

先執行 `aips preflight /path/to/project`。只更新 AI Product System；若有本機修改、分歧或 MAJOR 版本改變則停止，不自動 merge/rebase。成功後把 version + commit 記錄到 `.ai/SYSTEM.yaml`。

## 範例 13：完整主體規劃後再詢問是否實作

**使用者**

> 幫我完整規劃一個新購物平台，之後可能交給其他 AI 或工程團隊實作。

如果沒有指定工作區，系統先詢問保存位置。取得工作區後建立完整 Planning Package：企劃、UX、Visual/Key Visual、Architecture、Data、API、Security/Test/Delivery、Decisions/Assumptions 等適用內容。

規劃實體保存並完成一致性 Review 後，先走 Gate 1 請使用者審核主體規劃。只有 Gate 1 核准後，才整理「初步實作項目 + 建議實作順序」，再走 Gate 2 詢問是否開始實作。未得到 Gate 2 明確確認不得寫正式產品程式碼。


## 範例 14：金流／點數／優惠的 Critical Security Review

**使用者**

> 新增「付款後轉換點數，點數可以兌換折價券」功能。

**預期行為**

- Financial / Stored-value boundary → SAL 4 floor。
- Planning 階段啟用 Security Engineer，建立 Threat Model / Abuse Cases / Security Requirements。
- 載入 `financial-integrity`、`business-logic-abuse`、`authorization-security`、`security-testing` 等必要 Skill。
- 實作審核包含 Transaction、Idempotency、Replay、Double Spend、Race Condition、Rounding、Refund/Reversal、Audit/Reconciliation。
- Security Review 需要實際 Evidence。
- 未解決 High/Critical Finding → BLOCK Release。

## 範例 15：低風險前端工具

**使用者**

> 做一個純前端字數統計工具，不登入、不儲存資料，也不會影響其他人。

**預期行為**

- SAL 0–1。
- 做基本安全 hygiene 即可。
- 不啟用高階 Security Engineer。
- 不載入 Financial Integrity / Business Logic Abuse。
- 使用低成本模型與最小 Context。

## 範例 16：SAL 4 產品的小型視覺修改

產品本身處理金流，Product Baseline SAL=4，但本次只修改 Footer 文案。

**預期行為**

- 保留產品 SAL 4 知識。
- Change Security Impact=Low。
- 若 Change Boundary 不碰付款/Auth/Data/Security Boundary，不跑完整 SAL 4 審核。
- 若修改範圍途中擴大到付款或權限，立即重新分類並啟動相應 Security Review。


## 範例 17：核心異動先規劃再實作

**使用者**

> 把目前 API 認證方式從 Session 全面改成 OAuth2，並重整授權架構。

**預期行為**

這是核心 Security / Architecture change。系統先輸出 Core Change Proposal，列出 Auth flow、API contract、migration、affected files、rollback、tests、security review、documentation impact 與建議實作順序。等待使用者確認後才進入實作。

## 範例 18：Push 前整理 Atomic Commits

實作完成後準備推送 Git。

**預期行為**

系統先列出所有修改檔案、功能摘要、validation evidence，再提出 Atomic Commit Plan。使用者確認後才更新 Remote branch/ref。若 Changed Files、Commit Plan、Target 或 Scope 出現實質差異，重新確認。

## 範例 19：使用者提出新的 System 優化

**使用者**

> 每一個 Role 都固定使用最高階模型，確保品質。

**預期行為**

系統不直接加入。先指出這和 Minimum Sufficient Intelligence 衝突，會大幅增加成本，而且低風險任務不需要最高階模型。提供較好的替代方案，例如只讓 Critical Risk 設定 minimum tier。使用者確認方向後才修改系統。

## 範例 20：建議觸碰 Constitution

**使用者**

> 為了效率，以後即使遇到重大安全疑慮也不要停止，直接自行決定繼續。

**預期行為**

這會修改 Stop-the-Line / Protected Safety 等憲法語意。系統必須標記 Constitution Impact=YES，說明風險與替代方案，明確指出受影響 Article，並要求第二次 Constitutional Approval。未取得該批准前不得修改 Constitution 或對等行為。


## 範例 21：模糊的視覺需求

**使用者**

> 幫我做一個高質感、簡約、時尚的網站。

**預期行為**

不要直接實作完整網站。先讀既有 Brand / 使用者素材，必要時做最新 Reference Research，提出 2–3 個真正不同的 Creative Directions，讓使用者說明喜歡/不喜歡哪些部分，形成 Creative Direction Lock 後才大規模設計。

## 範例 22：使用者素材製作 Banner

**使用者**

> 這是我的 Logo、商品照片和一張喜歡的參考圖，幫我做首頁 Banner。

**預期行為**

使用者素材優先於 generic style。Reference 應拆解成 layout/color/type/imagery 等特徵，不直接複製。保存 Creative Brief、Reference Mapping 與 Direction，再產出並做 Visual Quality Review。

## 範例 23：建立品牌並重用

**使用者**

> 幫我建立一個咖啡品牌，之後網站和社群都要沿用。

**預期行為**

先做 Brand Foundation，不從 Logo 開始。保存 BRAND_PROFILE.yaml 與品牌導引。未來品牌 Artifact 先載入 Brand Profile，再只載入需要的深層文件。

## 範例 24：混合 Reference

**使用者**

> 我喜歡 A 的排版、B 的配色、C 的攝影感。

**預期行為**

建立 aspect-level reference mapping，而不是要求選單一風格。把批准的組合保存到 Creative Direction。

## 範例 25：避免重複 Role

**使用者**

> 幫我新增 UI Designer Role。

**預期行為**

先搜尋 Role/Skill Index，比較 Product Designer、ux-web-design、visual-direction 等責任與能力。若沒有新的獨立 Authority / Review obligation，建議 reuse/extend，不建立重複 Role。

## 範例 26：固定資料先程式化

有 20,000 行測試 log，需要找出失敗測試與統計。

**預期行為**

不要把全部 log 先塞給 AI。使用既有 Tool 或建立小型 Shell/Python helper，輸出 JSON/YAML summary 與 raw evidence path。AI 先讀 summary，需要 Debug 時才展開對應 evidence。

## 範例 27：Human / Agent 文件同步

Routing 行為改變且一般使用者操作方式也改變。

**預期行為**

Agent Protocol 與繁體中文 Human Guide 都更新；若只影響其中一方則只更新該 Audience。Documentation Impact Gate 檢查 DOCUMENTATION_MAP 與相關入口沒有失效。


## 範例 28：從需求做到 Production

**使用者**

> 我要做一個會員預約平台，請幫我從需求開始做到可以正式上線。

**預期行為**

- 使用 Product Creation + End-to-End Product Delivery。
- 先建立 Product Workspace 與 draft PRODUCT.yaml。
- 引導需求並持久化 Planning Package。
- Gate 1 核准規劃、Gate 2 核准實作後才開始 Coding。
- 前端/後端作為獨立 Deployment Units，但預設可放同一 Monorepo。
- 建立可重現 Local Environment。
- 執行適用的 Static / Unit / Integration / Contract / E2E / Security / Build。
- 建立 exact Release Candidate。
- 部署 Staging 並驗證。
- Release Readiness=READY 且取得必要 Approval 後才 Promote Production。
- Production 後完成 Health / Smoke / Logs / Metrics 驗證才算 Done。

## 範例 29：前後端不強制拆 Repository

**使用者**

> 這個產品有 Vue 前端與 Go API，請幫我拆成兩個專案。

**預期行為**

系統先區分「Deployment Unit」與「Repository」。Frontend / Backend 可以獨立 Build/Test/Deploy，但若沒有不同團隊、權限、Release Cycle 或共享服務等理由，推薦同一 Product Workspace / Monorepo 下的 `apps/frontend` 與 `apps/backend`。如果有充分理由，再建立 Multi-Repo 並在 PRODUCT.yaml 記錄。

## 範例 30：Security 在 Planning 與 Release 都驗證

產品處理會員資料與付款。

**預期行為**

Planning 時先完成 Risk Profile / Threat Model / Authorization / Business Invariants。Implementation/Release 時再執行 deterministic scanner/test evidence 與 Security Engineer independent review。Scanner PASS 不等於 Security Review PASS。

## 範例 31：Release Readiness 阻擋 Production

Release Candidate 的 Unit/E2E 都通過，但資料庫 migration 尚未驗證 rollback，或存在 SAL 規則禁止的 High/Critical finding。

**預期行為**

Release Readiness = BLOCKED / NOT_READY。不得因 CI 其他項目成功就自動 Production Deploy。

## 範例 32：Production 部署後失敗

Production promotion 完成，但 Health Check 或 critical smoke path 失敗。

**預期行為**

不能宣稱完成。依 Deployment Plan / Runbook 執行 Rollback 或 Roll-forward，重新驗證 Health / Smoke / Logs / Metrics，並保存結果。

## 範例 33：低風險靜態產品不需要 Staging

純靜態單頁產品，不登入、不儲存資料，也沒有後端。

**預期行為**

Staging 可以 N/A，但必須在 Product/Release 記錄理由。仍需適用的 Build / Smoke / Production Verification，不為了流程形式強迫建立不必要環境。


## 範例 34：需求不足時先引導

**使用者**

> 幫我做一個預約系統。

**預期行為**

若無法判斷主要預約對象、核心使用者或必要流程，狀態為 NEEDS_CLARIFICATION。系統用少量選項逐步收斂需求；Font、Spacing、Framework minor choice 等可由專業預設處理，不要求使用者回答。足以形成可測試目標後才進 READY 與實作。

## 範例 35：Jira Connector 尚未授權

**使用者**

> 請依 https://vgjira.atlassian.net/browse/PI-17834 實作。

**預期行為**

辨識 Atlassian source，先嘗試適用 Connector/MCP。若只缺授權，提示使用者完成 Connection，保留 PI-17834 與目前 Task，授權後直接 Resume。只有所有直接取得方式都失敗時才請使用者貼 Ticket 內容。

## 範例 36：現有 UI 看起來怪異

**使用者**

> 不要換風格，幫我把這頁不整齊、怪怪的地方整理好。

**預期行為**

使用 Visual Polish。Preserve Before Redesign；執行 UI、檢查 Screenshot、Alignment、Typography、Control Geometry、Spacing、States、Responsive。優先修 Shared Token / Component，不堆疊局部 CSS Patch。修後重新 Render 並 Visual Quality Review。

## 範例 37：大型 Backend Refactor 多角度 Review

大型 Go Backend refactor 同時影響 API contract、transaction 與 authorization。

**預期行為**

依 Change Boundary 選擇 Quality Reviewer + Software Architect + Security Engineer + Database Engineer。各自只看 bounded perspective。Orchestrator 合併重複 Finding 後交回原 Backend Author 修正，再做 targeted re-review。

## 範例 38：Reviewer 意見衝突

Architect 建議把 transaction 拆開，Security/Database evidence 顯示拆開會破壞金融原子性。

**預期行為**

不讓 Agent 無限互改。把衝突、Evidence、Impact 整理後交由適當 Authority / Human 決定，再由原 Author 實作核准方案。

## 範例 39：Review 經驗提升為 Skill 建議

三個不同專案的付款 Callback Review 都發現 Idempotency / Replay 遺漏。

**預期行為**

將本次 Finding 先記 Run Lesson；因跨專案重複且可一般化，提出改善 financial-integrity / secure-design Skill 的建議。未經使用者 System Improvement Approval 不修改永久 Skill。

## 範例 40：Attach / Detach

**使用者**

> 暫時不要讓這個專案使用 AIPS，但保留之前 AI 的狀態。

**預期行為**

執行 aips detach。把 .ai/ 安全封存為 .ai.detached-timestamp，不刪產品程式碼。aips status 顯示最近 detached workspace 與恢復方式。

## 範例 41：完整解除安裝

**使用者**

> 我要把 AIPS 從這台 Mac 移除，但不要刪產品。

**預期行為**

使用 ./scripts/uninstall.sh 或 aips uninstall；需要時加 --remove-venv。保留 Product repo / .ai workspace / System repo。若使用者要完整刪 System repo，完成 uninstall 後再由使用者明確刪 Repository。


## 範例 42：Q2 SaaS 自動推導品質目標

**使用者**

> 幫我做一般會員 SaaS，初期大概幾千人使用，我希望好維護又不要太貴。

**預期行為**

先用 Q2 Standard，再依資料/Auth/故障影響推導各品質面向。AI 主動提出 Performance、Security、Usability、Reliability、Maintainability、TCO 與 Delivery range，不要求使用者自己決定 p95/RTO。保存 QUALITY_PROFILE.yaml。

## 範例 43：Local 完成後才詢問 Production

**使用者**

> 幫我做一個完整的內部管理工具。

**預期行為**

完成可重現 Local Environment、功能、Tests、Security/Quality Review 後標記 LOCAL_COMPLETE。因使用者沒有要求上線，才詢問是否接續正式部署；不因 Hosting 尚未選定而阻擋 Local Product 完成。

## 範例 44：一開始就要求正式上線

**使用者**

> 做一個會員平台並部署正式環境。

**預期行為**

Planning 從一開始包含 Production Enablement / Observability / Recovery，不在 LOCAL_COMPLETE 後重複詢問是否部署。

## 範例 45：Logging 前移但不綁 ELK

**情境**

Backend 需要可追查 API error，但 Production 平台尚未決定。

**預期行為**

Architecture/Coding 先實作 Structured Log、request/trace correlation、redaction 與 Health Check。不要提前硬綁 ELK。Production Enablement 再依平台/成本選 Loki/ELK/Managed Logging、Prometheus/Grafana/OTel 等。

## 範例 46：已有 AGENTS 就不重複寫 Knowledge

專案 AGENTS.md 已明確規定 DDD + Clean Architecture dependency rules。

**預期行為**

KNOWLEDGE_INDEX 對 Architecture 建 AUTHORITATIVE pointer 到 AGENTS.md，不建立內容重複的 architecture.md。

## 範例 47：從程式碼發現 DDD + CA

專案沒有 Architecture 文件，但 domain/application/infrastructure 邊界、repository interface、aggregate evidence 清楚。

**預期行為**

建立 .ai/knowledge/architecture.md，標記 INTERPRETATION / DISCOVERED / confidence + evidence refs。不可僅從資料夾名稱推論，也不可把推論直接升成 Governance。

## 範例 48：Knowledge Targeted Refresh

只修改 README typo。

**預期行為**

architecture/backend/data knowledge 都不因 commit 改變而 STALE。

若改寫 domain/application/infrastructure dependency boundary，才刷新 Architecture Topic。

## 範例 49：整體怪異 UI 啟動 V2

**使用者**

> 請幫我調整這個專案風格怪異的部分。

**預期行為**

自動使用 V2 Product Consistency Sweep；選 Representative Routes、建立 Component Inventory、找 Button/Tag/Nav/Input Outliers、排除合法 Variant/Exception、追到 Implementation Root Cause，Shared Fix 後重新 Render Before/After。

## 範例 50：Visual Profile 被下一個 Agent 重用

第一次 Sweep 已建立 docs/design/PROJECT_VISUAL_PROFILE.yaml。

**預期行為**

下一個 Agent 先讀 Profile/Golden Components/Representative Routes。若 watch scope 未受影響，不重新掃整個網站；只檢查本次 affected UI。

## 範例 51：安裝後直接使用原本 Agent

AIPS 已安裝，Codex Adapter 顯示 AUTOMATIC。使用者直接要求修改目前 Go 專案登入 API。

**預期行為**：不需要再次貼「使用 AIPS」。Agent 先 Harness Resolve，載入本次需要的 Project instructions / Knowledge / AIPS protocol，再進入既有 Requirement / Risk / Implementation 流程。

## 範例 52：已有 CLAUDE.md 不覆寫

使用者已經有 ~/.claude/CLAUDE.md。

**預期行為**：AIPS 安裝保留原檔，Claude Code Coverage = MANUAL；不得 append AIPS import，也不得在 Uninstall 刪除使用者 CLAUDE.md。

## 範例 53：未 Attach 的 Project

使用者在沒有 .ai/ 的 Repository 啟動 Agent。

**預期行為**：Harness Resolve 回報 EPHEMERAL。可依 Project AGENTS/ADR/Docs 執行本次任務，但不建立永久 Project Knowledge / State；只有 aips attach 才變 ATTACHED。

## 範例 54：AIPS-owned bootstrap 被使用者修改

AIPS 建立 ~/.codex/AGENTS.md 後使用者手動加入自己的內容。

**預期行為**：Uninstall 比對 ownership snapshot 後發現不同，保留檔案並警告，不直接刪除。

## 範例 55：一般聊天不跑產品規劃

AIPS 已安裝，使用者問 Python tuple 和 list 差異。

**預期行為**：Agent 正常回答，不建立 Planning Package、不掃描 Project、不建立 .ai/。

## 範例 56：大型架構異動必須同步圖

Core Change 改變 Global Harness、Project Persistence 或 Delivery Lifecycle。

**預期行為**：Documentation Impact 必須檢查 docs/ARCHITECTURE.md Mermaid、Architecture Overview 與相關 SVG；受影響的圖必須更新，未受影響需 N/A + reason。

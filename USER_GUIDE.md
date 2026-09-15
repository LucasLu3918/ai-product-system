# 使用手冊

這套系統的目標是讓使用者用自然語言提出需求，系統自行選擇最小必要的角色、技能、知識與模型完成工作；如果需求還不適合直接實作，會先提出建議或問題，待使用者決定後再繼續。

## 1. 怎麼開始

直接描述你想完成的事即可，不需要指定角色、工作流程或模型。

例如：

- 「我要做一個購物網站。」
- 「幫我修改這個專案的 REST API，增加日期篩選。」
- 「幫我設計 3 種北歐風家具網站樣式。」
- 「把這支 API 的 p95 response time 壓到 2 秒以下。」
- 「我已有產品規劃書，幫我排製作流程。」
- 「估算這個專案需要的雲端環境與每月成本。」

## 2. 系統收到需求後會做什麼

```text
需求
→ 實作前檢查
→ 必要時提出更好的方案 / 問題 / 缺少能力
→ 使用者決策（只有真的會影響結果時）
→ 選擇工作模式
→ 載入最少必要 Role / Skill / Project Context
→ 選擇適合且成本合理的模型與工具
→ 執行
→ 獨立檢核
→ 儲存成果與狀態
```

## 3. 什麼情況系統會先停下來

系統不會因為小問題一直中斷，但下列情況會先詢問：

- 關鍵需求不明，可能導致做錯產品或功能。
- 有明顯更合適的做法，且不同選擇會實質影響結果。
- 會改變架構、公開 API、資料模型、安全邊界、成本或產品範圍。
- 動作具有高風險、破壞性或難以復原。
- 現有 Role / Capability / Skill 不足以可靠完成需求。

非阻塞問題會集中整理後一次詢問，不會一題一題打斷。

## 4. 如果系統發現有更好的做法

系統會先提供：

1. 目前需求的理解。
2. 發現的問題或可優化處。
3. 可選方案。
4. 推薦方案與理由。
5. 需要使用者決定的事項。

只有會實質影響結果的建議才會要求先決策；小型、等價且可逆的實作細節由系統自行處理。

## 5. 如果沒有適合的角色或技能

系統不會強迫最接近的角色硬做。

它會：

```text
偵測 Capability Gap
→ 說明缺少的專業能力
→ 判斷應新增 Skill、Capability 或 Role
→ 提出最小必要方案
→ 等待使用者確認
→ 建立後重新進行任務路由
```

原則是「能新增 Skill 就不新增 Role」；只有新的責任、權限或專業視角真的需要獨立承擔時，才建立新 Role。

## 6. 系統如何節省 Token

系統採 Progressive Loading：

```text
AGENTS.md
→ Work Mode
→ Primary Role
→ 必要 Capability / Skill
→ 相關 Project Context
→ 真的需要時才擴充
```

例如只做網站視覺設計時，不載入 Backend、Database、DevOps；修改 REST API 時，也不載入無關的 UX、品牌設計或整份 Repository。

模型選擇同樣遵守「Minimum Sufficient Intelligence」：先滿足隱私、工具、可靠性與能力需求，再從符合條件的模型中選擇較節省成本的方案。

## 7. 現有專案修改方式

對既有程式，預設流程是：

```text
確認需求
→ 檢查現有程式與慣例
→ 定義 Change Boundary
→ 必要測試 / Characterization Test
→ 實作
→ 測試
→ 獨立 Code Review
→ 更新 Workspace 狀態
```

系統不會因為看到其他程式碼可以改善，就順便做與需求無關的大型重構。

## 8. 新產品製作方式

新產品通常會經過：

```text
需求探索
→ Product Definition
→ UX / Visual / Architecture
→ 整體規劃文件與重要素材
→ Review
→ 使用者確認
→ Implementation
→ TDD / 適當測試策略
→ Independent Review
→ QA / Release Gate
```

規劃未通過使用者確認前，不直接進入正式程式實作。

## 9. 成果放在哪裡

AI Product System 本身保存「怎麼工作」；產品 Workspace 保存「這個產品是什麼」。

建議專案結構：

```text
project/
├── .ai/
│   ├── PROJECT.md
│   ├── STATE.yaml
│   └── MANIFEST.yaml
├── product/
├── design/
├── architecture/
├── planning/
├── src/
└── tests/
```

不同任務只建立真正需要的資料夾與成果，不強迫每個專案都有全部目錄。

## 10. 如何繼續上次工作

新的 Agent 應先讀：

1. `AGENTS.md`
2. `SYSTEM.md`
3. 專案 `.ai/STATE.yaml`
4. `.ai/MANIFEST.yaml`
5. 目前任務必要的文件

不需要重新載入整段聊天紀錄。

## 11. 建議的使用方式

描述「目標」比指定「怎麼做」更好，例如：

> 幫我把這支 API 的 p95 回應時間優化到 2 秒以下；先找出瓶頸，再提出方案，確認後實作。

如果你已經有明確限制，也直接附上：

> 不可改 API contract、不可增加 Redis、資料庫是 PostgreSQL、必須保持既有行為。

系統會把這些視為 Intent / Change Boundary 的一部分。

## DDD / Clean Architecture 怎麼使用

系統不會把 DDD 或 Clean Architecture 當成固定模板套在所有專案上。

- 小型 CRUD / 局部修改：沿用既有簡單架構，套用必要的依賴與測試原則即可。
- 中大型業務系統：視需要使用 Clean Architecture + Tactical DDD。
- 複雜多領域系統：必要時再使用 Strategic + Tactical DDD。
- CQRS、Event Sourcing、Microservices 等模式只有在需求證據支持時才載入或提出。

若架構選擇會明顯增加範圍、成本或影響既有 contract，系統會先提出建議，等你決定後才實作。

## 12. 修改既有專案時，專案規則怎麼套用

系統會先找適用的 `AGENTS.md`、ADR、Contract、Project Skill，再載入全域 Skill。

專案執行層的優先順序是：

```text
目前使用者明確指定 / 已確認決策
→ 最接近目標檔案的 AGENTS.md
→ 專案 ADR / Contract
→ 較上層的 AGENTS.md / Standards
→ Project-local Skill
→ Global Skill
```

例如 root 與 `backend/payment/AGENTS.md` 都適用時，Payment 目錄的規則較具體；但如果你明確要求本次採不同做法，系統會先說明重大衝突與影響，再依你的決策執行。

「這一次例外」只記在本次工作狀態，不會自動改寫整個專案規範。只有你確認「未來都改成這個規則」時，才會更新 `AGENTS.md`、ADR 或其他權威文件。

## 13. Subagent 與模型怎麼選

系統不會讓所有 Agent 都使用同一個高階模型，也不會讓 Skill 綁死某個模型名稱。

每個 Skill 只提供能力需求提示，例如需要多少推理、程式能力與可靠度；Router 再結合業務重要度、技術複雜度、失敗風險、資料敏感度與成本，為 Primary Agent 與每個 Subagent 分別選擇最低足夠的 Intelligence Tier。

```text
Tier 1  輕量：搜尋、整理、簡單分類
Tier 2  標準：一般 API / CRUD / 測試 / 程式修改
Tier 3  進階：架構、DDD、效能、DB、複雜除錯
Tier 4  關鍵推理：高風險安全、金融正確性、不可逆 migration、複雜分散式一致性
```

Subagent 只在確實能帶來專業分工、平行唯讀分析或獨立檢核時建立，而且必須有清楚的目標、範圍、Skill、輸出與權限。它只收到自己的最小 Context，不會複製整個主 Agent Context。

若任務途中發現比原先評估更困難或風險更高，Agent 應提出 escalation；困難決策完成後，後續例行工作可以 de-escalate 回較節省成本的模型。

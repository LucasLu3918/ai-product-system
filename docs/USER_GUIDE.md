# AI Product System 使用指南

本文件給人類使用者。AI Agent 請從根目錄的 `AGENTS.md` 開始。

## 1. 系統如何工作

~~~text
需求
→ 預檢（Preflight）
→ 判斷工作模式（Work Mode）
→ 只載入需要的 Role / Skill
→ 規劃 / 執行
→ 獨立審核（Independent Review）
→ 保存結果與狀態
~~~

系統的目標不是增加流程，而是讓高風險工作更嚴謹、低風險工作保持簡單。

## 2. 新產品與主體規劃

如果需求會成為整個產品未來實作依據，系統會建立可重現規劃包（Reproducible Planning Package）。

典型內容包含：
- 產品企劃
- 使用者與 Scope
- UX / Flow
- 視覺系統
- API / Data
- Architecture
- Security
- Testing / Delivery
- Implementation Plan

如果你沒有指定工作區，系統會先詢問保存位置。

規劃保存後：
1. 你先審核規劃。
2. 規劃核准後，系統整理「初步實作項目 + 建議順序」。
3. 你再次確認後才開始實作。

## 3. Creative Direction：不限網站

創意方向（Creative Direction）適用：
- Website / Landing Page
- Banner / Hero
- Social Post
- Presentation
- Product Page
- UI
- Campaign Visual

你可以提供自己的 Logo、照片、截圖、Reference、品牌文件或文字想法。

優先順序：

~~~text
你本次明確需求
→ 你的素材 / Reference
→ 已核准 Brand System
→ 已核准 Project Visual System
→ 本次 Creative Direction
→ 最新市場 Reference
→ AI 一般設計知識
~~~

當「高質感、簡約、時尚」這類描述太抽象時，系統不應直接做完整設計，而會先提出 2–3 個明顯不同的方向供你校準。

## 4. Style Profile

風格不是 Skill。

例如：
- Quiet Premium
- Editorial Minimal
- Modern Bento
- Japanese Minimal
- Cinematic Dark
- Soft Dimensional

它們只是風格資料（Style Profile）。需要時系統會再搜尋最新市場 Reference 或產生原創 Concept Preview。

因此未來新增流行風格，不需要增加新的 Agent。

## 5. Brand System

如果你要建立品牌，系統會先建立品牌基礎（Brand Foundation）：

~~~text
Brand Intent
→ Audience / Positioning
→ Purpose / Mission / Vision
→ Values / Personality
→ Verbal Direction
→ Visual Direction
→ Logo System
→ Brand Application
→ Brand Guide
~~~

建議保存：

~~~text
brand/
├── BRAND_PROFILE.yaml
├── BRAND_FOUNDATION.md
├── BRAND_IDENTITY.md
├── LOGO_SYSTEM.md
├── VERBAL_IDENTITY.md
├── BRAND_APPLICATION.md
└── BRAND_GOVERNANCE.md
~~~

未來說：

> 幫 ABC 品牌做一張中秋 Banner。

Agent 應先讀 ABC 的 `BRAND_PROFILE.yaml`，再依本次需求設計，不重新猜品牌風格。

## 6. 暫時突破品牌規範

可以使用暫時覆寫（Temporary Override）。

例如季節活動可以暫時提高 Accent Color 或插畫活潑程度，但 Logo 規則仍保持。除非你明確要求永久修改 Brand System，否則一次 Campaign 不會變成新的品牌規則。

## 7. 新增 Role / Skill / Capability

系統會先做重用檢查（Reuse Check）：

~~~text
Reuse
→ Extend
→ New Skill
→ New Capability
→ New Role
~~~

只有 Role 具有不同責任、決策權與 Review 義務時才建立新的 Role。

例如想新增「UI Designer」，系統會先比較現有 Product Designer 與 `ux-web-design` / `visual-direction`，避免重複。

## 8. 確定性自動化

如果某一步可以用固定規則可靠完成，例如：
- Git changed files 統計
- YAML / JSON 驗證
- 大量 Log 摘要
- 版本資訊提取
- 重複 ID 掃描
- CSV / JSON 轉換

系統應優先使用確定性自動化（Deterministic Automation）：

~~~text
Raw Data
→ Shell / Python / 既有工具
→ JSON / YAML Summary
→ AI 只讀需要的結果
→ AI 接續推理
~~~

工具使用範圍分為：

~~~text
Run-local
→ Project reusable
→ System reusable
~~~

只有真的多次重用，才升級成系統共用 Script。

主觀或需要專業判斷的問題，例如 Architecture tradeoff、Threat Model、視覺風格判斷，不應為了省 Token 強行程式化。

## 9. 資安

系統使用安全保證等級（Security Assurance Level, SAL）0–4。

低風險工具不會被迫跑重型 Security Review。

金流、儲值、點數、退款、可兌換優惠等高價值功能會提升安全等級，檢查 Idempotency、Replay、Double Spend、Race Condition、Authorization、Audit / Reconciliation 等風險。

## 10. 大型或核心修改

如果需求會影響核心 Architecture、公開 Contract、資料模型、Security Boundary、金流或大量跨模組內容，系統會先提供 Core Change Proposal。

你確認修改範圍後才開始實作。

## 11. AI Product System 自己的修改

你提出系統改善時，AI 應先評估：
- 是否真的需要？
- 目前是否已有相同能力？
- 有沒有更簡單方案？
- 是否造成 Role / Skill / Gate 膨脹？
- 是否有可一起優化的地方？

確認方向後才修改。

若會碰到 Constitution，會再進行一次明確的 Constitutional Change Approval。

## 12. Git 發布

Remote Git publication 前，系統會先列出：
- Changed Files
- 修改功能摘要
- Validation
- Review / Security Evidence
- Atomic Commit Plan
- Target branch / PR

你確認後才更新 Remote。

## 13. 文件分流

Human Docs 使用繁體中文，專有名詞第一次出現附英文。

Agent Docs 使用精簡英文，避免翻譯造成 Agent 路由歧義與 Token 浪費。

流程異動時，Documentation Impact Gate 必須確認兩邊是否都需要同步更新。

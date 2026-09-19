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


## 14. 完整產品交付（End-to-End Product Delivery）

如果你的需求是：

> 幫我從需求開始做成一個可以正式上線的完整產品。

系統會把它視為完整產品交付，而不是只產生 Code。

~~~text
你的需求 / 素材
→ 引導需求與規格
→ Product Workspace
→ PRODUCT.yaml
→ Planning Package
→ 規劃確認
→ Frontend / Backend / Data / Infrastructure
→ 本地環境（Local）
→ Automated Tests
→ Security Verification
→ Release Candidate
→ Staging
→ Release Readiness
→ Production
→ Health / Smoke / Logs / Metrics
~~~

### Product Workspace

建議一個完整產品有一個可被人類與 Agent 快速理解的根目錄：

~~~text
product/
├── PRODUCT.yaml
├── README.md
├── .ai/
├── docs/
├── brand/
├── apps/
│   ├── frontend/
│   └── backend/
├── database/
├── tests/
├── infra/
├── deployment/
└── scripts/
~~~

實際不需要的內容不會硬建立。

### Frontend / Backend 是否一定要兩個 Repository？

不用。

系統採用部署單元（Deployment Unit）概念。

例如：

~~~text
apps/frontend
apps/backend
~~~

兩者可以有各自的 Build / Test / Deploy，但仍放在同一個 Git Repository。

只有當團隊、權限、Release Cycle、服務共用或規模等因素真的需要時，才拆成 Multi-Repo。

因此：

> Independent Deployability ≠ Independent Repository

### PRODUCT.yaml

`PRODUCT.yaml` 是整個產品的導航入口，記錄：

- 有哪些 Deployment Units
- API / Event Contracts
- Database / Migration
- Brand Profile
- Local / Staging / Production
- Dev / Test / Security / Build / Smoke Commands
- Release Readiness
- Runbook / Rollback
- Health / Logs / Metrics / Alerts

新的 Agent 不需要重新閱讀完整聊天，就可以先從 PRODUCT.yaml 理解產品。

### Local Environment

完整產品必須提供一條明確的本地啟動與驗證方式。

例如：

~~~bash
make dev
make test
make security
make build
~~~

底層可以是 Docker Compose、Native Runtime 或其他工具；系統不會為了形式強迫使用 Docker。

### Security 不只在最後檢查

完整產品採用：

> 設計階段資安（Security by Design）＋驗證階段資安（Security by Verification）

規劃時處理 Risk Profile、Threat Model、Authorization 與 Business Invariants。

實作與 Release 時再執行適用的 Scanner / Test，並依 SAL 由 Security Engineer 做獨立判斷。

### Staging

正式產品預設流程：

~~~text
Local
→ CI
→ Staging
→ Verification
→ Production
~~~

低風險靜態產品如果不需要 Staging，可以標示 N/A 並記錄原因。

### 自動化部署（Deployment Automation）

完整產品不只產生 Deployment 文件。

如果目標平台與權限可用，系統應建立適合該專案的 CI/CD、Infrastructure / Deployment Config 或簡單部署 Script，先在 Staging 驗證，再依 Release Readiness 與風險規則 Promotion 到 Production。

如果目前沒有 Cloud / Hosting 權限或 Secret：

- 仍保存可執行的 Deployment Automation；
- 列出缺少的 Connection / Secret；
- 將 Deployment 標記為 BLOCKED；
- 不宣稱 Production 已完成。

### Release Readiness

Production 前不新增一堆零散 Gate，而是統一整理成發布就緒（Release Readiness）。

它會確認適用項目，例如：

- 所有 Deployment Units Build 成功
- Unit / Integration / Contract / E2E / Smoke
- Security Assurance
- Database Migration / Recovery
- Infrastructure
- Staging Verification
- Health / Logs / Metrics / Alerts
- Deployment / Rollback / Runbook

`READY` 代表技術條件已完成，但不會繞過既有的 Human Approval 或高風險規則。

### Production 完成條件

部署成功不代表 Done。

正式完成至少要確認適用的：

~~~text
Production Deploy
→ Health Check
→ Smoke Test
→ Critical User Path
→ Logs / Metrics
→ Error Check
→ Persist Evidence
~~~

失敗時依已定義策略 Rollback 或 Roll-forward。


## 15. 需求不明確時：循序釐清（Progressive Requirement Clarification）

如果你的需求還不足以安全實作，系統不應直接猜完整產品方向。

狀態只有：

~~~text
READY
NEEDS_CLARIFICATION
BLOCKED
~~~

原則：
- 可以用安全專業預設解決的細節，AI 自己處理；
- 只有會實質影響產品行為、Scope、Contract、Architecture、Security、Data、Cost 或 Recovery 的問題才詢問；
- 不使用長問卷；
- 優先提供 2–4 個具體選項與推薦方向；
- Blocking Unknown 沒解決前不開始大範圍實作。

例如：

> 幫我做一個預約網站。

系統應先引導「預約什麼、主要使用者、核心流程」等會改變產品方向的資訊，而不是要求你先決定 Database Schema 或 API Framework。

## 16. 外部連結與 Connector / MCP（External Context Resolution）

如果你提供 Jira、Confluence、Drive、GitHub 或其他外部系統連結，系統應先嘗試取得原始來源。

~~~text
User URL
→ Connected Connector / MCP
→ 需要授權？引導連線
→ 授權後從原任務 Resume
→ Public Web fallback
→ Other supported provider/API
→ 最後才請使用者貼內容 / 上傳檔案
~~~

例如：

~~~text
https://vgjira.atlassian.net/browse/PI-17834
~~~

如果 Atlassian Connector 存在但尚未授權，系統應先引導連線並保留目前任務，不應一開始就要求你複製 Jira 全文。

只有 Connector、公開頁面與其他支援方式都無法取得時，才請你提供必要的 Ticket 文字、Screenshot 或 Export。

## 17. 畫面怪異時：Visual Polish

如果你沒有要求換風格，只說：

> 幫我把這個專案看起來怪異、不整齊的地方調整好。

系統預設採：

> 保留後再重設（Preserve Before Redesign）  
> 一致性優先（Consistency First）

流程：

~~~text
讀取現有 Brand / Creative Direction
→ 啟動目前 UI
→ Screenshot / Rendered State
→ Visual Implementation Audit
→ 優先修 Token / Shared Component
→ 再處理真正的 Page-specific Exception
→ Screenshot / Responsive / State Verification
→ Visual Quality Review
~~~

預設檢查：
- Alignment / optical centering
- Typography / line-height
- Vertical rhythm / whitespace
- Button / Input / Tag 高度與 Padding
- Icon baseline / size
- Border / Radius / Shadow
- Active / Hover / Focus / Disabled
- Container edge breathing room
- Mobile / Tablet / Desktop
- 相同元件是否一致

不應用大量局部 top:-2px、transform 等 Patch 隱藏共用元件問題。

## 18. 核心異動：多專業審查（Multi-Perspective Review）

一般 Material Change 仍使用 Independent Review。

當異動涉及 Core Change、Auth/Authz、金流、Schema/Migration、Public API、Concurrency、大型 Refactor、Production Topology、SAL 3–4 等高影響範圍時，系統會依實際風險動態組成 Review Panel。

可能包含：
- Quality Reviewer
- Software Architect
- Security Engineer
- Database Engineer
- Performance Engineer
- Product Designer / Frontend Reviewer
- SRE / Cloud Architect

不是所有 Reviewer 每次都加入。

每個 Reviewer 只看自己的 bounded perspective，避免重複消耗 Token。

流程：

~~~text
Implementation Author
→ Multi-Perspective Review
→ Normalize + Deduplicate Findings
→ Consolidated Review Report
→ Original Author Fix
→ Tests
→ Targeted Re-review
→ PASS
~~~

Reviewer 預設不直接改程式，原 Author 負責修正。

## 19. Review 後的學習回饋

完成大型 Review 後，系統會整理 Lessons：

~~~text
Run Lesson
Project Lesson
System Capability Lesson
~~~

一次性的問題留在 Run。

專案特有的重要規則可建議提升成 Project ADR / Instruction / Invariant。

只有跨專案、重複發生、可一般化的問題，才建議改善 AI Product System 的 Skill / Role / Protocol。

系統不會因一次 Review 自動修改永久 Agent 能力，而會先把經驗與建議回饋給你，詢問是否啟動 System Improvement。


## 20. 品質規劃（Quality Planning）

完整產品預設會評估七個面向：

~~~text
Performance
Security
Usability
Reliability
Maintainability
Resource / Cost
Delivery Time
~~~

先使用 Q1 / Q2 / Q3 作為基準：

- Q1 Lightweight：個人工具、Static Site、Demo、低風險內部工具。
- Q2 Standard：一般 SaaS、會員平台、B2B、正式商業網站。
- Q3 Critical：金流、Stored Value、高敏感資料、高可用或重大營運影響。

Quality Class 只是 Baseline；個別面向可獨立提高或降低。例如 Q2 產品的 Security 可以提升到 Critical。

系統不應直接要求你決定 p95、RTO、RPO。它先詢問使用者類型、規模、故障影響、資料敏感度、交付與維運偏好，再提出 QUALITY_PROFILE.yaml。

品質要求盡量形成：

~~~text
需求
→ Target / Budget
→ 實作影響
→ Verification
→ Evidence
~~~

時間與成本使用 Range + Confidence，並在 Architecture 完成後重新估算。

## 21. LOCAL_COMPLETE 與 PRODUCTION_VERIFIED

完整產品預設先完成本地可運作版本：

~~~text
Planning
→ Implementation
→ Tests / Security / Quality Review
→ Local Verification
→ LOCAL_COMPLETE
~~~

如果一開始沒有要求正式上線，LOCAL_COMPLETE 後系統才詢問是否繼續 Production。

如果一開始已明確要求 Production，則不用重複詢問。

Production Enablement 會再處理：

~~~text
Infrastructure
CI/CD
Secrets
Domain / TLS
Database / Backup / Recovery
Observability
Staging
Release Readiness
Production
Post-deploy Verification
→ PRODUCTION_VERIFIED
~~~

## 22. Logging 與 Observability

Logging/Metric/Trace 的「需求與程式 instrumentation」在 Architecture / Coding 階段就規劃，不等部署後才補。

Production baseline：

~~~text
Structured Logs
+
Health Check
~~~

Metrics、Dashboard、Alert、Trace 依 Quality Profile 與風險決定。

金流、點數、退款、重要權限變更等高價值操作，應另外評估 Audit Log。

實際技術保持 Provider-neutral。等正式環境確定後，再依成本與維運需求選擇 ELK、Loki、Prometheus、Grafana、OpenTelemetry、Tempo、Jaeger 或 Managed Service。

## 23. Project Knowledge：避免重複掃描整個專案

第一次接觸陌生專案時，系統會先讀：

~~~text
AGENTS.md
ADR / Contract
Official Docs
PRODUCT / Brand / Visual / Quality artifacts
~~~

如果資訊已存在，就不重複建立文件，只在 Knowledge Index 保存 Pointer。

只有「重新探索成本高、跨任務穩定、且既有權威文件沒有」的資訊才放進：

~~~text
.ai/knowledge/
├── KNOWLEDGE_INDEX.yaml
├── architecture.md
├── backend.md
├── data.md
└── ...
~~~

實際只建立需要的 Topic。

知識分：

~~~text
FACT
INTERPRETATION
OBSERVED_CONVENTION
~~~

狀態分：

~~~text
AUTHORITATIVE
DISCOVERED
APPROVED
STALE
~~~

例如掃描 Go Backend 後發現 DDD + Clean Architecture，如果 AGENTS/ADR 已明確說明，就只存 Pointer；如果完全沒有文件，才保存 Evidence-based 的 architecture knowledge。

變更也不會讓所有知識失效。每個 Topic 可以監看相關 Path/Signal，只做 Targeted Refresh。

## 24. V2 Product Consistency Sweep

如果你說：

> 請幫我調整這個專案風格怪異的部分。

預設不是局部修幾個 CSS，而是 V2 Product Consistency Sweep：

~~~text
Representative Routes
→ Render
→ Component Inventory
→ UI Consistency Baseline
→ Visual Outlier Detection
→ Variant / Exception Check
→ DOM / Component / Computed Style / Token Root Cause
→ Shared Fix First
→ Before / After
→ Responsive + State Geometry
→ Visual QA
→ Update Project Visual Profile
~~~

不同不一定是 Bug。Hero CTA、small/default/large Button 等合法 Variant 會被保留。

當專案有穩定視覺知識時，保存到 docs/design/PROJECT_VISUAL_PROFILE.yaml；下一個 Agent 直接載入，不需要重新理解整個網站風格。


## 25. Global Agent Harness

v0.8 起，AIPS 可以在安全可逆的前提下接入支援的 Agent Runtime。日常仍是開啟原本 Agent 直接對談；Runtime Adapter 為 AUTOMATIC 時，遇到軟體/產品/專案任務才進入 AIPS。

AIPS 不會為了 Global Harness 覆寫既有 AGENTS.md、CLAUDE.md、GEMINI.md、Agent Config 或 Custom Skills；若自動接入會碰到使用者檔案，Runtime 改為 MANUAL。

沒有 `.ai/` 的 Project 預設 EPHEMERAL，不會被偷偷 Attach；但可使用 AIPS External Project Intelligence Cache 供後續 Agent 重用。需要 Project-local State 時才執行：

~~~bash
aips attach /path/to/project
~~~

查看解析：

~~~bash
aips harness resolve --cwd "$PWD"
~~~

解除：

~~~bash
aips uninstall
~~~

解除只處理 AIPS-owned integration；使用者/專案 instructions、Skills、source 與 .ai/ 都會保留。

## 26. Project Intelligence

v0.9 起，Existing Project 的長期理解層由 Project Knowledge 升級為 Project Intelligence。

第一次需要廣泛理解或實際修改既有專案時，Agent 先做 read-only bootstrap，再針對 Architecture、Data Flow、Modules、Conventions、Testing、Security 等做 evidence-based semantic enrichment；只有 `finalize` 通過才視為 READY。

已有 AGENTS / CLAUDE / GEMINI / ADR / Contract / 正式 Docs 的內容不複製，改用 SOURCE_REGISTRY Pointer。

EPHEMERAL Project 也能在 AIPS External Cache 保存 Intelligence，因此不需要 Attach 才能避免每次重新掃描。

Human Review HTML 讓使用者檢查 AI 對 Project 的理解。使用者的補充、例外與排除條件保存到 PROJECT_OVERRIDES.yaml。

任何 Existing Project mutation 在 Coding 前都要評估 Change Impact：Input、Output、Data、Events、Consumers、Security Boundary、Business Invariant、Compatibility、Tests 等；完成後再用 Actual Diff 回頭核對。

## 27. Secret / Key 安全

需要 API Key、Token、Password、Certificate 等敏感資訊時，AIPS 不應要求把 Secret 直接寫進程式或貼進 Prompt。

優先順序：

~~~text
Managed / Workload Identity
→ Secret Manager / Vault
→ Protected CI/CD Secret Store
→ OS / Runtime Credential Store
→ Runtime Environment
→ 必要時才使用未提交的 local secret file
~~~

程式只保存 Secret reference/config name。若沒有可安全取得的 Credential，該 authenticated operation 應標記 BLOCKED，而不是 hard-code。

Security Review 會檢查 Source/Config、Fixtures、Logs、Generated Intelligence/HTML 與 CI/Deployment artifacts 的 Secret leakage；scanner evidence 只輸出位置/fingerprint，不回顯 Secret value。

## 28. Core Change Test Matrix

大型或核心修改不能只因少數 Unit Test 綠燈就視為完成。

AIPS 依 final Change Boundary 判斷 Static、Unit、Integration、Contract、E2E、Security、Migration/Recovery、CLI/Harness、Docs/Schema 等哪些測試適用。

每個受影響 boundary 必須有 Evidence 或具體 N/A reason。若實作途中 Scope 擴大，就重新計算 Test Matrix；任何必要測試失敗都阻擋完成與 Release。

## 29. 新增 Skill

新增 Skill 前先搜尋 Skills/Capabilities Index 與最相近 Skill body。

只有真正存在跨專案、可重用而且責任清楚的能力缺口才新增。Framework 名稱、一次性工具、Project Convention、Style variant 不應因名稱不同就建立新 Skill。

New Skill Admission 至少要有：positive triggers、non-triggers、inputs、outputs、boundary、context cost、model requirements、reuse rationale、scenario evidence、unique ID/path，以及 secret/private-config check。

## v0.11 Approval Binding

大型／核心變更與 Git Publish 仍由 Human 決定。v0.11 新增的是「批准後可否機器驗證仍是同一個範圍」。

Approval Record 會記錄 proposal/scope fingerprint、branch、candidate commit、changed files 與允許的 protected operation。若 scope 漂移，狀態視為 `APPROVAL_STALE`。

可用 `aips intelligence context ... --explain` 查看結構化 routing 結果與 reasons；這不是 Chain-of-Thought。

## v0.12 Checkpoint / Resume

較長的工作可以使用 durable run state：

~~~bash
aips run checkpoint --project /path/to/project --run-id change-123 --protocol core-change --step implementation
aips run event --project /path/to/project --run-id change-123 --event tests_completed --status PASS
aips run resume --project /path/to/project --run-id change-123
~~~

ATTACHED 專案寫入 `.ai/runs/<run-id>/`；EPHEMERAL 只寫 External Cache，不會因此建立 `.ai/`。

如果 Git revision 已改變，resume 會回報 `STALE`，Agent 必須先重新檢查 freshness / impact / tests / approval，再繼續。

## v0.13 Scenario Conformance

Scenario 文件數量不再直接等同測試覆蓋率。

~~~bash
aips conformance check
aips conformance report
~~~

Report 會分開顯示 deterministic / lifecycle / agent_eval / manual / uncovered。只有前三者計入 automated coverage；manual 不會被包裝成自動化測試。

## v0.14 Execution Isolation

AIPS 現在可在 Execution Profile 中明確選擇執行隔離模式：

~~~text
shared
→ 使用目前 Project workspace
→ 可用，但不宣稱有隔離邊界

worktree
→ 建立真正的 Git worktree
→ AIPS 記錄 ownership / Change Boundary
→ 同一 Boundary 預設只允許一個 ACTIVE writer

sandbox
→ 只接受可驗證的外部 sandbox provider
→ 沒有 provider 時回報 UNSUPPORTED / BLOCKED
~~~

常用指令：

~~~bash
aips isolation resolve --project /path/to/project --mode worktree
aips isolation create --project /path/to/project --id change-123 --boundary orders
aips isolation status --project /path/to/project --id change-123
aips isolation remove --project /path/to/project --id change-123
~~~

Worktree 預設放在 AIPS 的 external config 目錄，不會在 Project source tree 裡建立額外資料夾。移除時如果發現未提交修改，AIPS 會停止清理並保留 workspace；clean worktree 移除後 branch 仍會保留，避免隱性刪除已提交成果。

## v0.15 Canonical Project Identity 與 Resume Integrity

AIPS 現在把「同一個 Repository」與「某一個 Worktree Workspace」分開識別：

~~~text
repository_id
→ 同一 Git repository lineage 共用

workspace_id
→ 每個 active worktree 各自不同
~~~

查看目前解析：

~~~bash
aips identity --project /path/to/project
~~~

用途：

- Project Intelligence / Run State 使用 workspace_id，避免不同 worktree 的狀態互相覆蓋；
- Isolation writer ownership 使用 repository_id + Change Boundary，避免從另一個 worktree 建立第二個 writer；
- Run checkpoint 會保存 workspace fingerprint，除了 HEAD 也包含 branch 與未提交產品修改；
- AIPS 自己寫入的 `.ai/` checkpoint/state 不會被算成產品 dirty drift；
- 舊版 EPHEMERAL run cache 會在安全且沒有 destination conflict 時 lazy migrate。

## v0.16 Agent Eval Conformance

有些 Scenario 無法用單純程式判斷，例如：

- 是否知道 Core Change 應先停下來等 Approval；
- 是否避免建立重複 Role / Skill；
- 是否只問真正阻塞的 Requirement；
- 是否選出正確且 bounded 的 Review Panel。

這些行為現在可使用 Agent Eval：

~~~bash
aips conformance agent-eval check
aips conformance agent-eval report
~~~

Agent Eval 不要求特定 Provider。Case 與 Agent 執行分離，Result 只保存可以觀察的決策，例如：

~~~text
status
selected reviewers
selected roles / skills
actions
artifacts
short summary
~~~

不保存 Chain-of-Thought 或 private reasoning。

每份 Result 都綁定 Case fingerprint：

~~~text
Case 改變
→ 舊 Result 變 STALE / FAIL
→ 重新執行 Agent
→ 記錄新的 observable Result
→ deterministic scoring
~~~

因此「只有 Eval Prompt」不算 automated coverage，必須有實際 Result 且 scoring PASS。


## Deterministic Scheduler / Integration Gate

當已批准的工作被拆成多個明確 Change Boundary，可用：

~~~bash
aips scheduler --graph TASK_GRAPH.yaml --state STATE.yaml --format yaml
~~~

Scheduler 只負責 dependency、固定排序、平行槽位與 boundary lock，不會代替 Human/Architect 做範圍或架構決策。

要在 merge 前驗證 exact candidate，可用：

~~~bash
aips integration-gate --profile VALIDATION_PROFILE.yaml --base <base-ref> --head <head-ref>
# janitor 是相同指令的別名
aips janitor --profile VALIDATION_PROFILE.yaml --base <base-ref> --head <head-ref>
~~~

大型/Core Change 若 profile 要求 Test Matrix，另外傳入 `--matrix CORE_CHANGE_TEST_MATRIX.yaml`。PASS 只是 validation evidence；Git publication、merge 與 release 仍遵循原本 Human Approval / Git Publish 流程。

## v0.27 Reliability Hardening

- Evolution Radar 若沒有 `OPENAI_API_KEY`，Issue 會提供 provider-neutral semantic handoff；你可以把同一份 evidence 交給已連線 ChatGPT、其他 Agent 或 local model，再用 deterministic binding 套回結果。
- Scheduler 的寫入 task 若沒有 Change Boundary 會直接 BLOCKED。純讀取 task 必須明確標示 `read_only: true` 才可省略 boundary。
- PR 的 Janitor 會重新抓 target branch tip；base 已前進時舊 candidate 不會沿用綠燈，而是要求重新驗證。

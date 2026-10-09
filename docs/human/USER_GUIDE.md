# AI Product System 使用指南

Local validation 會依共用 Runtime Context 選擇符合 Gate 需求的 Python；涉及核心執行環境時，Integration Gate 另驗證 runtime invariant matrix。

Evolution pre-analysis continues to use `evolution_analysis.py` as its existing command entry point; the internal implementation split requires no new user command.

本文件描述 **目前如何使用 AIPS**。版本演進放在 `CHANGELOG.md`，Scenario / validation 歷史放在 [Scenario Conformance](CONFORMANCE.md)；current-behavior 文件不再以 `vX.Y` 章節追加新功能。

## 工作模式與基本流程

~~~text
需求
→ Resolve Context / Work Mode
→ 只載入需要的 Role / Skill
→ Planning / Execution
→ Independent Review / Validation
→ Human-controlled publication or production
~~~

低風險工作保持簡單；Large/Core、高價值 business logic、security boundary 或 production change 才提高 planning、review、evidence 與 validation 強度。

## 建立大型產品

例如「幫我設計並實作大型購物網站」：

~~~text
需求 / 素材
→ Product Definition
→ UX / API / Data / Architecture
→ Security & Quality Planning
→ Human Planning Review
→ Task Graph
→ Deterministic Scheduler
→ isolated parallel implementation
→ TDD / Security / Quality Review
→ LOCAL_COMPLETE
→ optional Production Enablement
~~~

AIPS 不要求 Frontend / Backend 一定拆成不同 repository；以 Deployment Unit、權限、Release Cycle、team boundary、shared contracts 與 operational ownership 判斷。

完整產品可使用 `PRODUCT.yaml` 作導航入口，描述 deployment units、contracts、database/migration、local/staging/production、build/test/security/smoke commands、release readiness 與 runbook。實際不需要的目錄不會為了形式硬建立。

### Product Delivery lifecycle

~~~text
Plan
→ Local
→ Automated Tests
→ Security Verification
→ Release Candidate
→ optional Staging
→ Release Readiness
→ Human Production Approval
→ Production
→ Health / Smoke / Logs / Metrics
~~~

`LOCAL_COMPLETE` 與 `PRODUCTION_VERIFIED` 是不同狀態；完成本地功能不等於已獲得 production authority。

## Existing Project

Existing Project mutation 前會解析 nearest instructions、Project Intelligence、Change Boundary 與 Impact Graph。沒有 `.ai/` 仍可使用 EPHEMERAL mode，Reusable Intelligence 存在 AIPS external cache。

需要 project-local persistent state：

~~~bash
aips attach /path/to/project
~~~

Detach 會先同步可重用 Intelligence，再封存 project-local workspace；不直接刪除使用者累積資料。

## Creative Direction、Style 與 Brand

Project Diagnostics 只報告既有狀態，不會建立 Creative Bundle、啟動本地生成器或替代角色視覺驗收。

已安裝 Z-Image Turbo 權重時，可使用 MFLUX 專用 generate 命令。建議 8 步；此配對不支援 edit、ControlNet 或其他 Z-Image 變體。

ComfyUI 也可用 `model_profile: z-image-turbo` 執行同一模型：設定需明列 UNET、Qwen CLIP、VAE 權重檔名，並使用 AIPS 隨附的固定 API 工作流。Preflight 會向 loopback ComfyUI 核對三項本機模型清單；此配對僅支援 generate。

先用 `aips creative discover --project PROJECT` 盤點，再由工具 prepare 建立角色規範。`aips creative configure --project PROJECT --bundle RELATIVE.yaml` 從 stdin 接收 allowlisted JSON，回傳新的 Bundle 路徑；以該路徑 preflight，通過後才 execute。OpenCode 可直接使用相同 action。缺少模型或生成失敗時回報受阻，不改交 SVG；精緻插畫先校準代表性樣圖，完成後逐張檢查身份、人物結構、材質、光影與風格。

Creative Direction 適用 Website、Landing Page、Banner、Hero、Social Post、Presentation、Product Page、UI、Campaign Visual 等工作。

風格判斷優先順序：

~~~text
本次明確需求
→ 使用者素材 / Reference
→ 已核准 Brand System
→ 已核准 Project Visual System
→ 本次 Creative Direction
→ 最新市場 Reference
→ 一般設計知識
~~~

「高質感、簡約、時尚」這類描述太抽象時，應先提出 2–3 個明顯不同方向做校準，而不是直接假設唯一風格。

Style Profile 是資料，不是 Skill，例如 Quiet Premium、Editorial Minimal、Modern Bento、Japanese Minimal、Cinematic Dark。單次 Campaign override 不會自動升級成永久 Brand rule。

Brand System 可涵蓋 Brand Intent、Audience / Positioning、Purpose / Mission / Vision、Values、Personality、Verbal Direction、Visual Direction、Logo System 與 Brand Application。未來做新素材時應先重用既有 Brand Profile，而不是重新猜風格。

### 可重複使用的角色美術

角色素材沿用 `creative-calibration`、`visual-direction` 與 `visual-quality-review`。以 `CHARACTER_PROFILE.yaml` 記錄身份特徵與本機參考圖雜湊，以 `STYLE_PROFILE.yaml` 記錄媒材、構圖和文字規則；姿勢、表情、配件分開產出，避免一次生成後難以替換。預設使用已存在的本機 ComfyUI MCP；Apple Silicon 可選用 MFLUX。流程不安裝引擎、不下載模型，也不使用雲端或付費 API。清單需記錄精確模型版本、Runtime、授權來源與本機執行狀態。

使用 `python scripts/character_artifacts.py validate MANIFEST --project PROJECT` 驗證檔案、路徑、尺寸、雜湊和來源；使用 `compose` 以 SVG 組成設定表並排上繁體中文標籤。輸出不覆寫既有檔案。這些檢查不會判斷角色是否一致或畫面是否合格，仍需人工依核准的角色與風格設定逐張審查；效能數據只有實際量測後才能填入。

若要直接執行本機生成，可先用 OpenCode `creative_execution` 工具的 `prepare` 動作，或 `aips creative prepare` 建立版本化工作目錄，內含 README、Character Profile、Style Profile 與草稿 Bundle。準備流程只在明確素材 scope 建立固定的新檔，不覆寫；先補上已安裝引擎、模型版本與授權來源，再執行 `aips creative preflight --project PROJECT --bundle BUNDLE.yaml`。MFLUX Adapter 依固定能力表呼叫 FLUX.1、FLUX.2 Klein、Qwen Image Edit 2511 或 Z-Image Turbo 專用命令；FLUX.1 一次一張參考圖，只有支援 `--image-paths` 的 FLUX.2/Qwen edit 才接受最多八張專案內參考圖。ComfyUI 僅連線 loopback；一般 checkpoint 工作流維持既有限制，Z-Image Turbo 使用固定分離載入器工作流，兩者都拒絕自訂節點。預檢會核對本機工作流與模型清單，不會生成素材；缺少引擎會回報 `BLOCKED_NO_ENGINE`。確認後，以 `aips creative execute` 明確執行。輸出限於 EPHEMERAL 非 Git workspace 中指定 scope 的新 PNG/JPEG/WEBP 與 provenance manifest，不覆寫現有檔案、不下載模型。ComfyUI 編輯時須先將單張參考圖放入本機 input，且預檢會核對位元組雜湊。生成結果的視覺審查初始為 `PENDING`，請由獨立人工對照角色與風格規範檢查後，才用 `aips creative review` 記錄 PASS 或 REVISE；`aips creative trace` 只顯示原因碼、耗時、重試次數與雜湊。

## 需求釐清與 Planning

需求不足時採 progressive clarification：先問會改變產品方向、architecture、安全或交付成本的高資訊量問題，不為了流程而問全部細節。

會成為後續實作依據的大型需求應建立 reproducible Planning Package，常見內容：

- Product plan / scope；
- UX / user flow；
- Visual direction；
- API / data contract；
- technical architecture；
- security / quality plan；
- implementation readiness；
- assumptions / decisions。

新的完整規劃可在 package 根目錄加入 `PLANNING_MANIFEST.yaml`，逐項記錄 artifact 路徑、適用性、狀態與依賴；既有沒有 manifest 的 package 繼續沿用原流程。`python scripts/planning_package_validate.py <package> --format json` 會檢查依賴環、路徑、穩定 ID、需求到下游 artifact 的追溯，以及 Gate 1 / Gate 2 證據格式。它只檢查結構，不替人判斷研究、UX、架構或核准。研究需要可查證依據時使用 `PRODUCT_RESEARCH.md`；領域行為重要時使用 `DOMAIN_MODEL.md`。電商需求符合觸發條件時，先讀 `references/domains/ecommerce/OVERVIEW.md`，再只載入相關模組，並將未決政策留在決策紀錄。

對已釐清的功能行為，可使用 EARS 句型整理觸發條件、適用狀態、系統與可觀察回應。依情況選用恆常、事件、狀態、選配功能或異常行為句型；非功能需求保留量化目標和驗證方法，不必硬套 EARS。需要跨需求追溯時，可在 Planning Package 加入 `REQUIREMENTS.yaml`，把需求 ID 連到驗收條件與驗證方式。可用 `python scripts/requirements_traceability.py <package>/REQUIREMENTS.yaml --format json` 取得機器可讀的 PASS/FAIL；退出碼 0 代表結構檢查通過，非 0 代表檢查失敗。句型或 evidence 路徑都不代表測試已執行或通過。

Planning 核准後，再整理 Initial Implementation Items + Recommended Flow；Large/Core change 在 implementation 前需 Proposal-first 範圍與 Architecture Diagram Impact Check。

實作 REST API 時，AIPS 會先確認 OpenAPI／其他契約的權威性，再依專案契約、架構、工具鏈、測試方式和相似程式範例形成有來源的 Implementation Profile。新專案的技術和架構選擇須由使用者確認。局部範例不會自動變成全域規則；無法確認是否由 generator 管理的檔案會先受到保護。

新專案若尚未選擇技術，AIPS 會先檢查硬性限制，再依團隊、產品、既有系統、交付與維護需求提出少量候選和取捨；語言與框架分開選擇。架構建議同時看複雜度訊號與反向訊號，並分開說明 Clean Architecture、DDD 與部署方式。重要選擇由使用者確認後，才會整理到 Implementation Profile。

## Global Harness 與 MCP

診斷中的 MCP inspect 是靜態設定檢查，不會呼叫遠端或本機 MCP Tool；沒有原生 Host 證據時仍顯示 UNVERIFIED。

OpenCode `creative_execution` tool 與 `aips creative` CLI 共用本機執行器；ComfyUI Z-Image Turbo 需使用固定 API workflow 與已安裝權重，preflight 只查核，不會產生圖片。

OpenCode 創作 tool 支援 discover/configure，產圖意圖、原生檔案 guard 與 Shell effect policy 維持不同檢查；重新投影後仍須驗證實際 host hooks。

OpenCode V2 的 creative execution tool 只接受明確創作或修改意圖，並在執行前要求 Bundle preflight 通過。

OpenCode V2 may use the managed plugin for Session-scoped Context, supported direct-file checks, and the structured `creative_execution` tool. In EPHEMERAL creative projects, its explicit `prepare` action creates a versioned README/Profile/Bundle set in a selected scope; `preflight` checks a local Bundle without starting generation, and `execute` is explicit and create-only. `aips creative scan --project PATH` indexes existing image/SVG metadata in the user cache; `aips creative next-version --project PATH --target RELATIVE_ASSET` suggests a new path and never writes it. `aips harness trace` and `aips creative trace` show privacy-limited events. Arbitrary Shell effects and other MCP/custom tools remain outside the guard; inspect adapter status before relying on runtime enforcement.

Native Adapter 用來取得 runtime-specific hook / guard；MCP 提供跨 Host 標準接入。兩者共用 canonical Roles、Skills、Orchestration 與 Project Intelligence。

MCP-compatible Host 可以讀取 AIPS Roles / Skills / selected orchestration，並呼叫 bounded deterministic helpers。MCP Server 不執行第二個 LLM，也不取得 Human approval、Git publish、merge、release、production 或 host-native tool interception authority。

對完整支援 MCP 的 Host，優先使用 Resources / Prompts / Tools。對只提供 Tools 的 Host，使用 `aips_capability_catalog`、`aips_capability_read` 與 `aips_workflow_context` 取得同一份 canonical capability 與 Security／Architecture／Code Review、Delivery Plan context。

可用 `aips mcp config --client cursor|windsurf|copilot|amp|codex|generic` 產生 review-only 設定；輸出不會自動寫入第三方設定。`copilot` 指 GitHub Copilot CLI 的 local stdio 格式，hosted agent 仍需具備可執行的 AIPS runtime，不能直接沿用本機路徑。

MCP-only enforcement 誠實維持 `ADVISORY`；可驗證的 native pre-tool hook 才能回報 `TOOL_GUARDED`。

新增 Runtime 時先採 MCP；只有存在 MCP 無法提供的可驗證 hook／guard／event requirement，才建立 native adapter。

詳細請看 [Global Harness 與 MCP](HARNESS.md)。

## Roles、Skills 與重用

新增能力前依序檢查：

~~~text
Reuse existing Skill / Template
→ Extend Workflow
→ Extend System / Orchestration
→ New Capability
→ New Role only when responsibility truly differs
~~~

只有責任、決策邊界與 review obligation 真正不同時才新增 Role。專案自己的 conventions / rules 優先保存成 project-native knowledge，而不是無限制提升成 global Skill。

## Deterministic Automation

可用固定規則可靠完成的資料處理，優先交給 Shell / Python / existing tooling，例如 changed files、schema validation、大量 log summary、version extraction、duplicate scan、CSV / JSON transform。

~~~text
Raw data
→ deterministic helper
→ compact JSON / YAML evidence
→ model semantic reasoning
~~~

Architecture trade-off、Threat Model、視覺方向等主觀專業判斷不應為了省 token 被強行 deterministic 化。

## Deterministic Scheduler

discover/preflight 是唯讀操作；configure 會建立版本化檔案，execute 才會啟動 provider。排程與狀態不可將這些不同效果混為完成產圖。

Creative Profile/Bundle setup is an explicit user action; image generation is never started as a background scheduled task.

Scheduler fingerprints retain their existing raw digest format through the shared canonical helper; task graph ordering and execution ownership are unchanged.

LLM 負責 semantic planning；Scheduler 只接受已形成的 Task Graph，依 dependency、boundary、authorization、state 與 deterministic ordering 決定 dispatch，不自行發明 task、scope 或 approval。

Parallel task 必須先證明可安全並行；同一 change boundary 的 competing writer 不因想提高速度就被放行。

PR 驗證會把 Gate 與 Repository Health 報告放在 CI runner 的暫存位置，完成後再上傳 artifact。這讓驗證不會因產生報告檔而把 checkout 判定成 dirty，合併前看到的證據仍對應同一個 commit。

受保護分支的 `repository` required check 必須在 exact PR candidate 的 Integration Gate 成功後才會通過。

Installation entrypoint workflow 保留既有 pull request 路徑與平台檢查，並以近期 job P95 加安全倍數設定明確逾時；逾時會作為該 job 的失敗呈現，不改變 required check 或 Human 核准權限。

## Execution Isolation 與 Runtime Resource

主要實作預設保留符合條件的已選模型；輔助工作可依風險使用較低 tier，但必要 reviewer 獨立性仍須滿足。一般 Data Modeling 先處理概念、ownership、關係與生命週期，只有選用 DDD 時才要求 Aggregate／Bounded Context。

執行 `aips integration-gate` 前，準備完整 Python 3.12 環境並以 `AIPS_VALIDATION_PYTHON` 或 `AIPS_VALIDATION_VENV` 指定；缺少依賴時命令會先停止並列出診斷。文件候選另需 Node 24+（可用 `AIPS_NODE_BINARY` 指定）和 checkout 內已安裝的 VitePress；預檢不會自動安裝套件或連接 registry.

Mutation 可依需要使用 shared workspace、AIPS-owned Git worktree 或 verified sandbox。沒有可驗證 sandbox provider 時，不把一般 temp directory 宣稱成 sandbox。

高／critical 風險或明確不受信任的執行可用 `aips isolation resolve --mode auto --risk high --data-class public` 檢查最低隔離要求。一般風險會選 worktree；高風險需要已啟用、證據新鮮且資料政策相符的 sandbox。找不到時顯示 `UNSUPPORTED`/`BLOCKED`，不會自動降級。E2B 目前停用，僅有合成資料 smoke verifier。

Parallel worktree 需要 dev/test server 時，Runtime Resource Lease 會為 isolation 配置 bounded TCP port，避免多 Agent 固定使用同一 port。

需要代理執行高風險外部動作時，Runtime Policy 會要求明確資料分類、目的地、Change Boundary 與有效核准；沒有驗證過的 sandbox 網路隔離時，動作會停止。

需要代理執行高風險外部動作時，Runtime Policy 會要求明確資料分類、目的地、Change Boundary 與有效核准；沒有驗證過的 sandbox 網路隔離時，動作會停止。

~~~text
Task
→ Worktree
→ Runtime Resource Lease
→ AIPS_PORT_<RESOURCE>
→ Agent / dev server
~~~

Lease candidate order deterministic；實際選到的 port 仍受當下 host occupancy 影響。Address-in-use race 使用 bounded reallocation，不無限 retry。

## Visual Polish 與 Product Consistency

畫面出現按鈕、標籤、留白、字級、alignment、responsive breakpoint 等不一致時，先讀既有 design tokens / component patterns / reference，再做 bounded consistency repair。

Visual Consistency Sweep 不等於重新設計整個產品。若現有 style 是使用者有意決策，應 preserve valid native style，而不是因模型偏好自行換風格。

RWD / accessibility / interaction state 應納入適用的 quality evidence。

## Security

AIPS 使用 Security Assurance Level（SAL）0–4。金流、點數、退款、authorization、可兌換優惠等高價值邏輯會提升 security assurance，檢查：

- replay / idempotency；
- race / double-spend；
- authentication / authorization；
- sensitive data / secret handling；
- audit / reconciliation；
- rollback / recovery；
- business invariants。

Secret / Key 不寫入 source、Prompt、log、Project Intelligence 或 ordinary evidence artifact。External provider credential 是 optional enhancement 時，不得變成 unrelated baseline / release prerequisite。

詳見 [Security Assurance](SECURITY_ASSURANCE.md)。

## Quality 與 Review

Project Diagnostics 的輸出只能協助定位下一步，不取代獨立 Review、必要測試、完整 Integration Gate 或 Git 發布核准。

本機 Z-Image Turbo 產圖也須分開確認檔案有效性、角色／畫風品質與人工接受；引擎執行成功不會自動將人工審查改為 PASS。

創作驗證分別記錄命令盤點、合成 tool/provider 測試、native host 驗證及真實模型推論。未提供權重時，品質／設備效能維持未驗證，不以流程通過推定改善成效。

創作 manifest 的 Human visual review 與軟體獨立 review evidence 是不同契約。圖片容器或 tool fixture 通過不會自動產生視覺 PASS 或使用者接受。

Local synthetic checks cover preparation and adapter boundaries only. Review each generated image against the approved identity/style profiles before recording a visual PASS.

每個 creative manifest 初始 review 狀態為 `PENDING`；請由獨立人工檢視輸出與角色／風格設定後，再記錄 `PASS` 或 `REVISE`。

Validation Shadow records proposed skips while every required validator still runs; current evidence is not sufficient to activate selective execution.

OpenCode 可用 `aips harness doctor` 檢查投影完整性、版本探測、Host discovery 與 Hook 狀態；CONFLICT 需先檢視保留下來的使用者內容。Plugin install、Host discovery、context hook execution、permission hook execution 與 pre-tool enforcement 各自回報，不能由檔案檢查推定。`aips harness trace` 僅輸出受限事件、決策與耗時，不保存 prompts 或素材內容。macOS OpenCode v2.0.24 的隔離 loopback mock 已驗證原生 Context 與 permission hook；其他主機仍需相符驗收。整體治理維持 ADVISORY，MCP/custom tools 和任意 Shell effects 不宣稱受保護。

CI 固定準備完整 Python 驗證套件，文件變更也會執行必要安裝／preflight lifecycle。候選路徑仍決定 Node、Chromium 與可選 evidence；未通過 `repository` 必要檢查時，不可合併，不能用本地 PASS 或略過驗證代替。

Review packet and evidence fingerprints preserve their established `sha256:` representation; the shared helper extraction adds no approval authority.

Context routing 的 Scenario 230 驗證核心大小、路由涵蓋、hook/manifest 契約與缺少來源時 fail-closed；它不取代 exact-candidate Integration Gate。

主要實作保留合格的 Runtime／使用者模型；Skill frontmatter 產生相容 v1 INDEX，決定性 lifecycle 與人工模型政策驗收分開記錄。

Agent Eval freshness 依變更路徑與明確的行為依賴挑選受影響案例，只標示需要更新 evidence 的案例，不會自動執行 Eval；Scenario 192、193、224 仍為人工驗收。

Plan17 regression evidence covers numeric diff headers, four browser/OpenAPI combinations, mandatory aggregates, reusable caller keys/permissions, explicit Python and isolated children, recursive placement, signed identity/immutable proposal rejection and atomic deletion races. Missing or malformed capability plans retain the full profile. A latest cancelled check stays INCOMPLETE; replaced old checks are reported as SUPERSEDED.

The shared Python CI bootstrap checks each caller-declared import profile and dependency consistency; it complements the required full repository Gate.


Publication commands remain available through `bin/aips` and the existing `scripts/aips_cli.sh` entrypoint. The facade loads its internal command modules from the selected AIPS checkout before dispatch, preserving the same command arguments and results for source and installed entrypoints.

Validation optimizations must preserve the full Integration Gate and execute every unique lifecycle evidence script at least once; the maintenance guide describes the local exact-candidate workflow.

Validation observation and graduation reports are advisory. If collection dependencies or artifacts are missing, the evidence stays `NOT_READY`; the full repository Gate still runs, and no validator is skipped.


REST/OpenAPI 變更可用 `python scripts/openapi_contracts.py validate <spec> --repo-root .` 驗證 OpenAPI 3.0／3.1／3.2；只接受 repository root 內的本機 `$ref`，不會連線載入 URL。`compare <canonical-baseline> <candidate> --baseline-authority canonical` 會分類明確的破壞性／相容性變更，無法可靠分類的差異回報 `UNKNOWN`。`run-contract-tests` 以 argv 執行專案原生測試並綁定 JUnit、operation ID coverage、規格雜湊與 Git revision；`verify-evidence` 可找出內容或 revision 已改變的舊報告。AIPS 不替專案判斷測試斷言是否足夠，也不會自動核准破壞性 API 變更。

Phase 3 可在 Implementation Profile 的 `enforcement` 區段指定適用路徑、語言 Profile、所有權、生成來源與專案原生檢查。先用 `python scripts/implementation_enforcement.py inspect IMPLEMENTATION_PROFILE.yaml --repo-root . --base <base-sha> --head HEAD --mode report` 檢視缺口；完成命令證據收集後改用 `--mode enforce`。命令收集需明確執行 `run-command ... --command-id <id> --execute`，宣告為 deterministic 的命令還需 `--repeat 2`。Gate 只驗證目前候選的證據，不會執行 Profile 內的命令；所有權未知、必要證據缺少或過期時不能通過。

本地發佈預檢會先確認 Python／Ruff、loopback 與 Chromium 等 Integration Gate 條件，再做完整候選驗證；文件變更時也會檢查本地 Markdown 連結並建置 VitePress。用全域 CLI 驗證另一份 checkout 時加上 `--project-root <repo>`，讓腳本、設定與候選使用同一個 repo root。

### Phase 4：本機 OpenAPI client generator

只有專案已確認 canonical OpenAPI、目前 Phase 2 驗證證據及 repository-local generator 後，才可在 Profile 設定 `generation.enabled: true`、`policy: boundary_only` 和 `generation.adapters`。預設執行 `python scripts/openapi_generator_adapter.py IMPLEMENTATION_PROFILE.yaml --repo-root . --adapter-id <id>` 只預覽，不會啟動 generator。檢查路徑、版本、輸出 allowlist 與證據後，使用者明確執行同一命令並加上 `--execute` 才會在本機產生並套用 client 檔案。

執行器只接受 Profile 固定的可執行檔雜湊和 argv，不使用 shell，並以暫存副本、逾時及檔案／位元組上限執行。它只會替換 Phase 3 ownership/hash 記錄仍吻合的產物。CI 與 Integration Gate 不執行 Profile 指定的 generator。此流程不提供 OS sandbox，也不代表生成 client 已通過語義或整合測試；仍需依專案測試流程驗證。

### Phase 5：真實產品驗收與共用參考案例

沒有可用的真實產品時，可先執行 `python3 tests/evidence/openapi_client_pilot_lifecycle.py`。此案例在暫存 Git 專案內建立 Widgets API 與產生的 Python client，檢查 OpenAPI、生成確定性、ownership、操作覆蓋、授權、錯誤及 Unicode 傳輸。Profile 可設定 `enforcement.generator_reports: [{adapter_id: <id>, report: evidence/generator.json}]`，讓 Phase 3 檢查未追蹤的 Phase 4 執行報告；報告缺少或過期時，已啟用的檢查會阻擋候選。執行器與 Gate 仍不會自動執行專案 generator。

多個產品共用這一份 AIPS 工作流程範例。各產品應在自己的 repository 保存 canonical 契約、Profile、client、產生報告與專案原生驗收測試；獨立 API/client 邊界可各有本地驗收套件。只有不同技術或架構暴露共通缺口時，才擴充 AIPS 參考案例。參考案例的 PASS 不代表其他產品已完成語義驗收。

### OpenTelemetry run traces

Record a lifecycle pair in the existing run event stream, then export or replay it:

```bash
aips telemetry record --project . --run-id RUN --kind phase --action started --operation-id plan-1 --name planning
aips telemetry record --project . --run-id RUN --kind phase --action completed --operation-id plan-1 --name planning
aips telemetry export --project . --run-id RUN --output /tmp/run-trace.json
aips telemetry replay --project . --run-id RUN --config ./telemetry-export.yaml --send
```

The shipped export config is disabled. Transmission requires a private config with `enabled: true`; HTTPS is required except for loopback testing. Keep optional authorization in the host environment variable named by `authorization_env`. Recorded values are limited to lifecycle IDs, fixed operation names, verified provider/model IDs, token counts and outcomes. Export omits prompt/output content, arguments, private reasoning and credentials. Unpaired markers show `TELEMETRY_DEGRADED`; this does not block the workflow. See [OpenTelemetry run export](./TECHNOLOGY_GUIDE.md#opentelemetry-run-export) for field limits and replay behavior; the canonical contract is `orchestration/TELEMETRY_EXPORT.md`.

### 外部 Eval / Red-Team 互通

可用 `aips eval` 匯出 Promptfoo 的 inline config、匯入 Promptfoo JSONL、匯入 PyRIT bridge，並驗證 evidence fingerprint。AIPS 不會執行外部工具設定；匯入結果只供檢視或訊號使用，不能直接通過或阻擋發布。需要把 finding 納入 regression 時，先由 Human 確認 finding 與最小重現案例，再輸出成 canonical Agent Eval Case，以 AIPS deterministic scorer 重新驗證。未設定外部 API key 也可執行全部本地驗證。

Change Impact unknown 只有在保留原始描述、具備可驗證 repository-file 或完整 traversal evidence，並有明確 Human review 時才能關閉。Legacy string、失效 evidence 與 scope mismatch 仍會阻擋實作。Disposition evidence is reviewed separately from implementation approval; exact changed-file reconciliation remains mandatory before READY.

獨立審查隔離機制已實作，但目前**未啟用為 PR 強制要求**；active Core Change Matrix 設為 `review_evidence.required: false`。待可信 runtime-attestation verifier 接通後，才可將矩陣設為 `true` 啟用。啟用後，沒有可信證據的必要審查會維持 `UNVERIFIED` 並阻擋 Gate。

只修改 EARS validator 契約時，文件影響限於 Scenario Conformance 與 Technology Guide；若改動需求追蹤功能、Planning Package 範本或 canonical requirements，仍須更新完整 Requirement Planning 文件閉包。

需要檢視 Agent 如何完成任務時，可使用 `aips trajectory evaluate --trace <trace.yaml> --mode shadow`。結果是 observable evidence；`BLOCK` 表示 deterministic risk，`WARN` 表示品質偏差，任何結果都不會自動授予 Git Publish 權限。

Quality Planning 依風險選擇最低足夠驗證。Implementation 完成後執行適用的：

- lint / type check；
- unit / integration / contract / E2E；
- regression；
- security verification；
- independent review；
- Integration Gate / Janitor；
- Repository Health / architecture consistency。

Core change 以 actual diff 重新對帳 Test Matrix，不能只依原始計畫宣稱完成。

`SELF_CHECK` 是實作者自己的驗證；`INDEPENDENT_REVIEW` 必須由不同執行身分，在唯讀、隔離的任務中審查精確候選版本。Review packet 只包含明確允許的候選差異、必要規格與驗證證據，並以 base/head、檔案清單和內容指紋綁定；不得傳入實作者對話、隱藏推理、scratchpad 或未列入 allowlist 的工作區內容。缺少可信 runtime attestation verifier、候選版本不符或執行身分重複時，結果是 `UNVERIFIED`，必要審查會阻擋 Integration Gate 與發布。

Integration Gate 只檢查證據格式、來源、候選綁定與確定性政策，不替代語意審查，也不授予合併或發布權限。

Visual evidence 預設優先使用 Playwright managed Chromium；系統 Chrome 只有在 `AIPS_BROWSER_PROVIDER=system` 或 managed browser 不可用時使用。Publication preflight 會先執行 browser smoke probe，啟動失敗會標記為 `ENVIRONMENT_BLOCKED`，不誤判成頁面測試失敗。
Publication Preflight 會分開呈現 Python modules、loopback 與 browser 診斷；對應 lifecycle evidence 固定 module probe，再驗證 loopback/browser 阻擋情境，避免把主機環境差異誤判為產品失敗。

The supported command remains `aips` (or `bin/aips` from a source checkout). The public launcher forwards commands and arguments to the checkout implementation; command names, output, and environment selection remain unchanged by the internal module split.

Observation reports help people judge evidence quality; `NOT_READY` means the cohort is incomplete, not that collection failed or that selective validation is approved. Dependency Review remains blocking through its standalone check while a separate shadow records parity before any reviewed required-path change.

## Logging、Observability 與 Operations

創作可靠性 Core candidate 保留完整 Gate、媒材拒絕及取消授權回歸。損壞 PNG fixture 必須失敗；合成測試不能替代真實模型與人工品質驗收。

Context diagnostics 只記錄 route categories、protocol IDs/paths 與解析狀態，不保存原始 prompt 或私有 reasoning。
Monthly Effectiveness names weekly Issues missing local pre-analysis and leaves their complete-cohort shortlist yield unavailable. Oversized Radar Issues keep the full original evidence in a verified archive for scheduled rollups.

Execution Profile 的 per-run cost budget 是 advisory metadata。Telemetry 只記錄 runtime 實際提供的 usage/source/confidence；缺少 token 數或可驗證價格時保留 unknown，不呼叫 provider、不估算成本。


已有 AIPS Run checkpoint 時，可對 `aips intelligence context`、`aips intelligence retrieve` 或 Integration Gate 加上 `--observe-run-id <id>`，自動記錄 AIPS 自己實際觀察到的操作起迄。這些紀錄不推算模型 token 或成本；記錄失敗會標示降級，不改變主要指令的判定。

正式產品依風險規劃 logs、metrics、health / smoke、alerts、runbook 與 rollback。Observability 的目的不是大量產生 log，而是讓重要 failure mode 可被定位與復原。

Production verification 應使用 observable evidence，不以「workflow 已執行」取代 service health / smoke / deployment state。 AIPS 的 daily Validation Observation Collector uses a provisional 15-minute timeout from a two-run sample of about 31 seconds and avoids concurrency groups that could discard pending scheduled or manual evidence. Monthly Evolution Effectiveness serializes only same-period Issue updates and retains queued runs.

開始執行前，先確認 Task Graph 可排程，為任務建立 AIPS worktree isolation，再用 `aips run owner claim` 綁定派送結果：

```bash
aips run owner claim --project <worktree> --run-id <unique-run-id> \
  --graph TASK_GRAPH.yaml --state <shared-scheduler-state.yaml> \
  --task-id <task-id> --execution-id <runtime-execution-id> \
  --isolation-id <active-aips-worktree-id> --runtime codex
aips run owner heartbeat --project <worktree> --run-id <unique-run-id> \
  --state <shared-scheduler-state.yaml> --task-id <task-id> \
  --execution-id <runtime-execution-id>
aips run owner reconcile --project <worktree> --run-id <unique-run-id> \
  --state <shared-scheduler-state.yaml> --task-id <task-id> \
  --execution-id <runtime-execution-id>
```

Scheduler 從 graph 取得 write set、Boundary 與 dependencies；claim 只接受當下 dispatch 的 task。`reconcile` 會以 claim 時記錄的 base revision 比對 staged、unstaged 與 untracked 檔案。租約過期且有 dirty files 時，先檢視再使用 `aips run owner recover` 並提供原因；接手 dirty 工作還要加 `--accept-dirty`。過界 diff 會將 task 標成 BLOCKED，不能完成。Owner lease 是協調證據，當前 enforcement capability 仍為 ADVISORY。

### Parallel Run Dashboard

Use the read-only dashboard to inspect all known runs for the current repository, including runs in parallel worktrees:

```bash
aips run list --project .
aips run dashboard --project .
```

The dashboard is an observation surface. It shows workflow state, gate, last activity and workspace health, but it cannot approve, retry, cancel, merge or publish. `ACTIVE` means the last checkpoint reported an active workflow; it does not prove that an Agent process is still live. The local server binds only to `127.0.0.1`.

有 ownership state 時，dashboard 也顯示 task owner、lease/recovery、Boundary、worktree、dirty files、dependencies、heartbeat 與 enforcement capability。舊 run 沒有 owner 時顯示 `UNASSIGNED`，檢視不會改變其狀態。

## Checkpoint / Resume

Run projection fingerprints preserve their existing facade and canonical digest bytes after helper consolidation; run state and resume authority remain governed by the existing contracts.

Standalone and shadow dependency-review artifacts retain exact base/head, run ID, actual JSON findings and outcome for 90 days. Parity compares canonical findings; missing outputs, different candidates or inaccessible artifacts stay UNKNOWN. Job success alone cannot promote the shadow. Record resolved toolchain fingerprints and repeat full Gates only for new changes or unresolved failures.

長流程在 material step 保存 durable checkpoint / event evidence。Resume 時重新比較 repository/workspace identity、HEAD、branch、dirty state 與 relevant approvals。

舊聊天內容不是 authoritative run state；若 workspace fingerprint 已變，先 refresh / revalidate 再接續。

## Project Intelligence

遇到 Project Intelligence 狀態不完整時，可先執行 `aips project diagnose <path>` 查看 reason code、下一步與重新驗證命令。診斷不會自動 bootstrap、refresh、attach 或修復；請先檢視建議，再明確執行相應操作。

Turn Context 顯示固定核心與本回合選取的 canonical protocol routes；路由清單只提供指引，變更前仍須完成 Change Impact 與正式核准。

`aips intelligence context --project . --runtime codex --prompt '...'` 預設顯示精簡 YAML；`--full` 顯示完整診斷。可用 `--target-path src/file.py` 限定指示範圍，或用 `--intent read|write` 明確標示本次意圖。JSON 輸出維持完整格式，供既有整合使用。

Stable Intelligence 保存 Architecture、Data Flow、Modules、Contracts、Conventions、Testing、Security、Operations、Source Registry 與 Impact Graph。

Just-in-Time Retrieval 只帶入本次任務相關的 code、symbols、tests、history、graph evidence，避免每個 Turn 重掃整個 repository。Retrieval cache 是可重建 acceleration layer，不取得 governance authority。

詳見 [Project Intelligence](PROJECT_INTELLIGENCE.md)。

Retrieval index persistence is an internal, rebuildable cache boundary in `scripts/retrieval_storage.py`; existing commands and imports continue through the `retrieval_intelligence.py` compatibility facade.

## Git Publication 與 Release

Core creative workflow changes use the normal exact-candidate Gate and Git Publish Approval flow; neither validation nor matrix readiness authorizes remote publication or merge.

Release tagging, dependency PR merges, and branch deletion remain separate operations with their own evidence and Human approval; a successful maintenance report cannot perform them.

Publication preflight retains its existing CLI and raw canonical hash output through the shared helper; exact-candidate and Human merge authority boundaries remain unchanged.

可用 `python scripts/repository_governance_snapshot.py --repo OWNER/REPOSITORY` 檢視 GitHub rulesets 與 branch protection；此快照唯讀，遇到不可讀設定會標示 UNKNOWN，不會替代 PR 核准或發布流程。

Scheduled maintenance summaries are evidence, not permission to change source, merge, release or delete branches. When reviewing workflow reliability, distinguish an operational error from an incomplete observation cohort; inspect the run summary and bounded artifact, and retain separate observation runs for later comparison.

Publication preflight 只檢查 exact candidate 所選的環境能力；候選未選 browser 驗證時 `NOT_REQUIRED` 不會阻擋，選用 browser 時 loopback 或瀏覽器檢查失敗仍會 fail closed。Required repository Gate 與 secret scan 維持必要條件。

CI 可依精確變更路徑略過未使用的 OpenAPI 套件安裝，但仍執行 publication-preflight lifecycle。已安裝 validator 時會跑 OpenAPI help 與 contract smoke；未安裝時會驗證 CLI 提供明確設定指引、沒有 traceback，也不會輸出不完整驗證檔。這不略過 required repository aggregate。

Pull requests may show an early advisory repository-preflight result while the required full validation continues. A fast-lane finding is diagnostic feedback and does not replace the required repository check.

Post-merge reconciliation 的實作拆分不改變既有指令、快轉安全條件或人工合併權限。

For a Large/Core change, complete documentation closure, the reviewed Core Change Test Matrix, candidate secret scanning, full repository validation, and the exact-candidate Integration Gate before asking for publication approval. Create the PR with its `aips:core-change` label on the initial request; merging and release tagging remain separate Human decisions.

Repository validation keeps running every validator while shadow reports assess future selective-validation safety. Coverage, governance complexity, and reliability data are review signals; they do not bypass the normal Gate or authorize automatic source changes.

Managed installs default to stable releases when verified `vX.Y.Z` tags are available; use `--channel main` only to opt into development updates. The first release tag still requires its separate explicit release approval.

The exact-candidate PR Gate uses Python 3.12 as its required baseline. A separate weekly compatibility workflow reports lifecycle smoke results for Python 3.12–3.14; it supplements the PR Gate and does not replace exact-candidate validation.

Core/Large changes publish a fingerprinted Core Change Test Matrix with each applicable boundary's local evidence. The read-only version-tag check requires the exact merged main SHA and leaves release approval/tag creation separate; ruleset policy comparison requires a complete current snapshot and performs no GitHub settings write.

CI 會依 exact candidate paths 決定是否安裝 Node、browser 與 OpenAPI 選用工具；未知路徑使用完整工具鏈。每個候選仍執行必要的 secret scan、repository validation 與 exact-candidate Integration Gate。

發布前可執行 `aips publish checks --pr <number> --head <sha>`，區分最新的失敗、等待、取消及跳過；這份摘要不授予合併權限。合併後從已更新 checkout 執行 `./bin/aips publish post-merge --fetch --sync-installed --apply`，核對本機 main 與註冊安裝版同步。Phase 12E 真實 REST 驗收暫緩；AIPS 只作 CLI、安裝、快取與發布驗收。

`aips validate --help` 只顯示說明，不執行驗證；未知參數會明確失敗。`aips docs impact --base <ref>` 使用目前 AIPS checkout；從其他目錄呼叫時加上 `--project-root <repo>`。先用 `aips publish preview` 檢查未提交文件閉包，再固定候選執行完整 Gate。

本地驗證設定隔離會保留原本 GitHub 設定位置。自行設定暫存 `XDG_CONFIG_HOME` 時，先以 `GH_CONFIG_DIR` 指定原本的 gh 設定目錄；`AUTH_CONFIGURATION_UNVERIFIED` 表示設定位置待確認，不應直接重新登入。`prepare-local-validation --check-only` 先確認 Python 3.12 venv 身分，再檢查依賴、Node、localhost 與 browser；依 named diagnostic 修復並重跑同一檢查。

在產品 repository 使用 `aips openapi validate <spec> --repo-root .` 或 `aips openapi generator <profile> --repo-root . --adapter-id <id>` 可呼叫安裝版工具，無須複製 AIPS scripts。generator 預設僅 preview；明確授權後才加 `--execute`。

OpenAPI 驗證器為選用套件：先執行 `aips openapi doctor` 確認狀態，再明確執行 `aips openapi install` 安裝固定版本。套件缺少時 validator 會提示安裝方式，不會直接輸出 Python traceback；基本 AIPS 安裝不會自動下載這些套件。

Run publication commands inside the target AIPS checkout or pass `--project-root <repo>`. Inspect the printed source, target and Python before proceeding. For repeated local checks, reuse the prepared venv with `--check-only`; use `--wheelhouse` for offline Python packages when needed. Unrelated label checks pass only with matching successful full Gate evidence; otherwise rerun the full candidate workflow. Read CI documentation-failure and timing summaries before requesting external artifact-storage access.


建立 Large/Core PR 前，先用 `aips publish preview` 檢查未提交文件位置與 Matrix 綁定，再用 `aips publish plan` 確認 GitHub CLI 認證與首次 PR 分類標籤。`gh pr create` 可同時帶入 `--label aips:large-change` 或 `--label aips:core-change`，讓 `opened` 事件採用預期分類；後續只有這兩種分類標籤的新增或移除會取代舊驗證並按最新 labels 執行，無關標籤會跳過 Gate 且不取消進行中的驗證。

`publish plan` 會查詢 repository settings 並列出目前允許的 `merge_commit`、`squash` 或 `rebase` 方法，讓操作者選用 GitHub 實際支援的合併方式。API 網路中斷與 repository 權限不足會分別回報；兩者都不會授予合併權限。

Remote Git publication 前需有 current Human authorization 與適用 validation evidence。AIPS 會區分：

~~~text
local implementation
≠ git publication
≠ merge
≠ release
≠ production deployment
~~~

Agent、MCP、CI workflow 或 external analyzer 不能因為具有執行能力就自行取得上述 authority。

提交前可執行 `aips publish preview --base origin/main --change-class <standard|large|core>`，預覽已提交、暫存、未暫存及未追蹤檔案的文件閉包與矩陣綁定；必須先處理 `pending` 項目。`aips publish matrix-sync --base origin/main` 只更新 canonical Core Matrix 的 base/hash，更新後仍需重新檢視範圍與證據，再把矩陣標記為 READY。發布前再以 `aips publish preflight --base origin/main --head HEAD --change-class <standard|large|core> --output <report>` 執行與 CI 相同的 exact-candidate resolver。Large/Core PR 必須同步套用對應 label，並使用 `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`。受保護 `main` 由 `publish plan` 直接規劃 Pull Request，不先嘗試直推。

若用 GitHub Connector／API 建立 PR 分支，先確認 `aips publish environment` 可執行完整驗證；文件範圍確定後重新執行 `publish preview`。本地候選提交與 preflight 通過後，執行 `python scripts/publication_transfer.py prepare --base <base-sha> --repository <owner/name>`，核對 `origin` 與預期目的地。建立遠端 blob 與 tree 後，將 GitHub 回傳的 `repository`、`base_sha`、`tree_sha` 及逐檔 `blobs` SHA 寫入倉庫外的暫存 JSON，再執行同腳本的 `verify --base <base-sha> --repository <owner/name> --receipt <receipt.json>`。只有 `READY_TO_PUBLISH` 才能建立遠端 commit／branch；若主分支已移動，先重建候選並重驗。`publish plan` 的 `gh` 認證狀態不代表 Connector 的認證狀態，Connector 連線需在發佈工具側另行確認。

若 preview 回報 Matrix DRAFT、blocker、尚未核對差異或 base/hash 不符，先處理對應 `pending`；`READY_FOR_GATE` 只表示可進入正式 Gate。全域安裝的 `aips publish matrix-sync` 會選用目前 AIPS checkout；從其他目錄執行時必須傳 `--project-root <repo>`，避免寫入安裝目錄。從原始碼 checkout 執行時亦可使用 `./bin/aips`。

本地首次驗證可先執行 `python3.12 bin/prepare-local-validation --venv <validation-venv>`，之後用相同 `--venv` 加上 `--check-only --run --base <base-sha> --head <head-sha> --change-class core` 執行同一候選的 Publication Preflight 與 Gate；驗證設定會暫存在 repository 外。文件候選另需讓 Node.js 位於 `PATH`，並先在 checkout 安裝 `package.json` 的 VitePress 相依套件。建立 Large/Core PR 時同時使用 `gh pr create --label aips:large-change` 或 `--label aips:core-change`，讓首輪 CI 取得正確分類。

若已有完整的 Python 驗證環境，直接呼叫 `scripts/publish_preflight.py run` 也會讓巢狀 Python 命令優先使用該執行檔所在環境；執行前仍應先檢查模組與瀏覽器是否齊備。

開發時先跑受影響測試，候選 commit 固定後再跑一次上述完整 Gate；其中已包含 `tests/validate_repository.py`。本機 `.timing.json` 與 CI 的 `repository-validation-timing` artifact 可用來找出最慢項目，不須為取得時間資料重跑完整驗證。

每個 Remote Git publication candidate 都會由 AIPS 內建秘密掃描器檢查 exact final tree 和 base 到 head 的 commit 歷史。找到秘密、歷史或候選內容無法完整掃描、policy 無效時，發布檢查會阻擋並只顯示遮蔽後位置與指紋；修正後須重新驗證。Gitleaks、GitGuardian 與 GitHub Secret Scanning 可作第二層防護，不需要它們的憑證才能通過 AIPS baseline。

Core Matrix 的 `changed_files_hash` 必須綁定相同 base/head 的完整變更檔案集合；精確候選通過 preflight 後才可請求 PR review。Integration Gate PASS 是驗證證據，不會代替明確的 merge 授權。


Preview 也會在昂貴驗證前檢查候選內容安全與允許的 Git email 身分；報告只提供命中類型與位置，不回顯敏感值。Context 則會先證明所選路徑與已知主題相關，並共同限制 Core、Recall 與 temporal evidence 的預算；Retrieval Index 無法開啟時提供穩定診斷與來源指標，不偽裝成已檢索成功。

若本機工作樹包含其他未提交變更，先建立乾淨 worktree 驗證候選；不要讓 unrelated diff 改變 changed-files hash 或 Repository Health 結果。

合併後可執行 `aips publish post-merge --fetch --apply --refresh-intelligence`；從其他目錄執行時加上 `--project-root <repo>`。全域 CLI 以安裝版的安全對齊邏輯操作指定 checkout，即使 checkout 本身仍含舊版腳本也能處理安全快轉。工作樹乾淨且本地 `main` 是遠端目標的祖先時，工具先建立 backup branch，再以 `git merge --ff-only` 同步；若提交歷史已分歧，只有兩邊 tree object 完全相同時才採用有備份的既有對齊方式，其他情況一律停止。

Release model 與版本歷史以 repository 的 current policy / CHANGELOG 為準。

- A release candidate is not readiness evidence while `CHANGELOG.md` has entries under `## Unreleased`. After finalized notes move under the matching `VERSION` heading, the read-only check can establish readiness; tag publication remains a separate explicit decision.
## Evolution Radar

Technology Intelligence 位於 maintenance plane，不在一般工程 Turn hot path。

~~~text
public evidence
→ provenance / dedup
→ deterministic pre-analysis
→ optional semantic analysis
→ Human Decision
→ bounded Trial
→ normal System Improvement / Core Change / Publish gates
~~~

Trial PASS 不等於 ADOPT；recommendation 也不會自動修改 code、merge 或 release。

詳見 [Evolution Radar](EVOLUTION_RADAR.md)。

## Documentation

Human current behavior 以 topic-oriented 方式更新在 `docs/human/`。Official Docs Site 由同一份 Markdown source 透過 VitePress render，不建立第二份 canonical content。

文件責任：

~~~text
Current behavior / How-to / Explanation
→ docs/human/ 對應 topic section

Release / version history
→ CHANGELOG.md（目前版本與穩定版號錨點）
→ docs/history/changelog/（較早版本的完整內容）

Scenario / validation history
→ docs/human/CONFORMANCE.md
~~~

Documentation Placement Contract 會檢查 heading hierarchy、version/scenario-style heading 與 changed-line placement。新增功能不得只在 current-behavior 文件尾端追加 `vX.Y` / Scenario 說明；若確實需要新 topic，必須同時把 canonical section 加入 placement contract。
## Runtime Content Safety Boundary

Commit, pull request and release content is scanned before durable/public publication. A blocked result requires regenerating safe content; it is not silently rewritten. Runtime capability remains truthful: AIPS-owned sinks are enforced, native hooks may be tool-guarded, and unsupported host tools are advisory.

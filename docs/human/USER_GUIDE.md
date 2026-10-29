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

明確初始化外部 Project Intelligence（不建立專案內 AIPS 檔案）：

~~~bash
aips attach /path/to/project
~~~

AIPS 安裝後不會自動接管專案 Hook。使用 `aips project mode show` 檢查目前模式，或明確啟用：

~~~sh
aips project mode set assist --project /path/to/project
aips project mode set enforce --project /path/to/project --scope git_push,gh_pr_merge
~~~

缺少設定時為 `off`；`observe` 與 `assist` 不會因 AIPS 專案層治理阻擋或替 Host 放行。硬內容安全掃描在所有模式都會執行，安全 findings 不會降級成提醒。`enforce` 只套用明列動作，且設定存在使用者層 XDG 目錄，不會寫入專案。`aips status <project>` 會同時顯示獨立的 optional governance mode。

所有新 Intelligence、checkpoint 與 Change Impact 草稿都保存在使用者層。`aips detach` 是相容入口，不會搬移或刪除資料；停用 optional governance 請使用 `aips project mode set off --project <path>`。既有 `.ai/` 會保留為唯讀 legacy 資料。

## Creative Direction、Style 與 Brand

Content scanning does not decode creative media or establish visual quality, license, provenance, or Human acceptance.

ComfyUI workflow 的資源授權依明確 profile 與 grant 驗證；模型探索只使用固定 loopback API，診斷不會自動提交工作。

OpenCode 的 Context 上限也適用於本機 Creative 工作；超限時維持 fail-closed，不投遞 Context 或支援的原生檔案寫入，修復後再重試。

Claude Code 發布寫法調整不影響 Creative 流程；提交產出素材仍經相同 commit 內容安全掃描，Prepare 掃描證據（30 分鐘、綁定 PR）不授權任何創作輸出。

Publication scan evidence applies only to a Git candidate Secret Scan. It does not cache creative review, authorize asset import, or change image-generation provenance.

Creative outputs in Git workspaces retain their existing guard, even while ordinary confined local L2 source writes may proceed with READY but STALE Project Intelligence.

Creative assets using static AVIF pass the bounded EXIF/XMP safety scan described in Runtime Content Safety; this does not establish visual quality or licensing.

Publication failure diagnostics describe Git execution only; they do not establish creative intent or authorize generated assets.

Creative 輸出若要 Git 發布仍須走獨立 publication guard；創作授權不取代發布授權。

Creative font files pass through the shared bounded metadata scan when staged or included in publication candidates; it screens embedded text and does not approve licenses or visual quality.

Commit Content Safety remains separate from Creative Runtime grants and does not create provider or asset-import authority.

Git publication Diagnostic IDs are governance evidence only; they do not inspect creative assets or authorize generation, asset publication, or merge.

Publication Doctor recovery is separate from Creative Direction, asset generation and visual-review decisions.

The OpenCode publication adapter reports the same bounded, safe recovery guidance as the shared diagnostic contract.

Creative grants never confer Git merge authority; publication recovery diagnostics must remain separate from creative quality and asset acceptance.

Creative generation and asset import retain their existing grants; a later Git publication uses the separate read-only repository diagnosis and approval flow described under Git Publication 與 Release.

上游 Writing Fragments → Beats → Shape 是獨立的明確選用流程，不會因一般寫作或創意工作自動套用；完整 Skill 狀態可在 <a href="./skill-catalog.html">Skill Explorer</a> 查看。

發布前使用 `aips publish prepare --worktree <candidate-root> --title <title> --body-file <file>`；原生工具必須使用輸出的 `cwd` 與精確 `argv`。`--expected-fingerprint` 可拒絕舊觀察，`--host-denied` 只回報 Host 拒絕。每次續行重新查詢遠端分支與 PR；PLANNED 不是授權，也不是完整 Integration Gate PASS。

To bring an existing image or SVG into a creative workspace, use `aips creative import-candidate` to review a source hash and absent destination, then `aips creative import --candidate FILE --accept-hash SHA256` to revalidate and create the exact file without overwrite. Git destinations remain rejected by default. For a user-selected Git worktree, explicitly add `--allow-git-destination` to candidate creation; the candidate then binds the Git mode, source and destination hashes, and exact target. The source must be in a non-Git EPHEMERAL workspace, and the destination must be the worktree root. Import remains create-only and never stages or commits; use the separate Git publication process for publication.

OpenCode acceptance applies only to the reported host version and source. A successful Context or file-hook check does not cover arbitrary Shell processes, MCP/custom tools, or writes initiated outside OpenCode; the report marks these effects UNSUPPORTED and grants no additional authority.

指出「疤痕畫在頭髮上」會形成版本綁定的缺陷回饋；明確要求「重出一張哈利」可在同一 Session 取得新的單張修正授權。`quality-check` 逐項檢查必要特徵與禁止錯置；只有明確要求自動修正才可使用 `quality-loop`，最多兩次修正，預設 native 時間上限十分鐘。

Ordinary generation grants permit bounded `quality-check` of manifests produced by that grant; historical/unrelated images require explicit review intent. This does not authorize regeneration, and `review-assist` retains its separate explicit-review contract. Inspect required criteria before delivery; without an installed local reviewer, report UNVERIFIED and request Human inspection.

Creative task grants remain separate from Git authority; the personal PR merge confirmation flow is described under Git Publication 與 Release.

Creative grant 僅涵蓋已核准創作範圍；成品若要 commit／push／PR，需另依 Git Publication 與 Release 流程取得 signed external grant。

ComfyUI 已接受工作後若逾時或輪詢失敗，AIPS 會讀取本機 queue：自己送出且仍在排隊的工作以確切 ID 移除；自己送出且正在執行的工作以指定 `prompt_id` 中斷；其他工作一律不碰，也不自動重送，並回報重新檢查後的 `job_state`。AIPS 重啟後可執行 `aips creative recover`，只處理本機 ledger 記錄為 AIPS 擁有且已超過自身逾時的工作。先檢查 Provider 狀態，再明確重試。

使用 `templates/creative/QUALITY_BENCHMARK.json` 與 `templates/creative/CREATIVE_QUALITY_DATASET.yaml` 記錄本地 trial。資料集提供三種角色 archetype、六類案例，共 18 個 profile-case 覆蓋格；每筆 v2 evidence 指定 `profile_id`、`case_id` 與 `COMPLETE`／`FAILED`。失敗另分 model、check、compiler 階段與受限 reason code。以 `python scripts/creative_quality_benchmark.py --project <workspace> --evidence <report.json>` 核對輸出及雜湊。角色、服裝、構圖、參考圖編輯與恢復由人工分別評分；user acceptance 獨立記錄。缺漏維持 UNKNOWN，v1 舊 evidence 可讀但 coverage 為 UNVERIFIED。資料集是覆蓋矩陣，不是生成結果或品質標籤。

Impact candidates are advisory software discovery evidence and do not authorize creative asset changes.

The prompt compiler extraction does not change the creative workflow, model selection, or review steps described here.


Creative manifests keep model inference, Human visual review and user acceptance as distinct evidence.


Project Diagnostics 只報告既有狀態，不會建立 Creative Bundle、啟動本地生成器或替代角色視覺驗收。

已安裝 Z-Image Turbo 權重時，可使用 MFLUX 專用 generate 命令。建議 8 步；此配對不支援 edit、ControlNet 或其他 Z-Image 變體。

ComfyUI 也可用 `model_profile: z-image-turbo` 執行同一模型：設定需明列 UNET、Qwen CLIP、VAE 權重檔名，並使用 AIPS 隨附的固定 API 工作流。Preflight 會向 loopback ComfyUI 核對三項本機模型清單；此配對僅支援 generate。模型可透過 `templates/creative/COMFYUI_MODEL_PROFILES.yaml` 擴充，但只能沿用已審核的拓樸家族；FLUX 3 Klein Base 為另一個固定 workflow profile。 需要未列入系統 profile 的已安裝模型時，可用 `aips creative profile draft --model-id <id> --base-profile <系統 profile>` 產生未核准草稿，再於互動式終端機執行 `aips creative profile approve <local-profile-id>`；草擬不會下載權重（Scenario 271）。

FLUX 3 Klein Base 與 Distilled 共用已審核 workflow；Base 使用 50 steps / CFG 3.5，Distilled 使用 16 steps / CFG 1。預檢會讀取本機 `/object_info/TextGenerate`，檢查工作流欄位、型別、範圍及 `sampling_mode` Dynamic Combo 選項 schema。送往 ComfyUI API 的值是 schema 中選取的選項鍵（例如 `"off"`）；ComfyUI 會在執行層重建節點所需的巢狀值。AIPS 在唯一一次 `/prompt` 前也會核對最終序列化工作流的節點、欄位與連線。ComfyUI 執行錯誤只回報安全摘要，不回傳原始訊息、提示、路徑或 traceback，也不會自動重送失敗工作。

明確選擇 `dynamic_local` 的 edit workflow 可設定有序參考圖並提供相同順序的本機 staged 檔名。Qwen Image 2.1 以 `image_1` 至 `image_8` map 支援最多八張；Qwen Image Edit Plus 以連續的 `image1` 至 `image3` 端口支援最多三張。每張上限 12 MiB、合計上限 25 MiB；預檢逐張比對來源與 staged bytes。模型 profile 不會啟用編輯能力或改變此參考圖邊界。

需要使用其他已安裝模型時，可在 Bundle 明確選擇 `workflow.mode: dynamic_local` 並提供專案內 API workflow JSON。`aips creative workflows scan` 只讀取本機 loopback `/object_info` 與工作流，`inspect` 回傳 privacy-bounded 狀態摘要，`import` 以 create-only 方式將來源複製到專案內；這三個工作流 CLI 子命令只輸出固定狀態，不回顯節點名稱、模型檔名、Runtime 版本、提示內容或工作流細節。一般 `creative discover` 保留有限且核准 loader 的模型目錄，但不列出節點清單。`preflight` 會核對節點 schema、圖連線、明確輸入綁定及本機 loader 模型。只允許 runtime 標示的 ComfyUI core nodes；API、custom、未知節點及隱含模型／參考圖選擇都會拒絕。動態模式不會自動替換固定 profile，也不下載權重；執行仍須明確要求，timeout 後不自動重送。合成驗證不代表實際推論或品質已驗證。

先用 `aips creative discover --project PROJECT` 盤點，再由工具 prepare 建立角色規範。Discovery 只檢查已安裝的 MFLUX 命令／版本，並對固定 `127.0.0.1:8188` 的 ComfyUI 做唯讀 API 探測；不連 LAN 或外網，也不送出生成工作。只查固定 GET 路徑，核對 loopback IP、Port、Path、Method，停用 Proxy 並拒絕 Redirect；回傳核准內建載入器的有限模型名稱清單，不列出任意節點。狀態分開呈現命令、runtime、模型目錄、preflight 與 inference；服務回應或模型檔名存在都不代表推論已驗證。錯誤以 `status`、`phase`、`reason_code`、`source`、`retryable`、`trace_id` 和 `recovery.action` 提供繁中排除指引；HTTP 只顯示狀態碼，不輸出回應本文、認證資訊或本機 Profile 路徑。Apple Silicon 會標示 MPS 為靜態候選，FP8 權重可提出 advisory；FP16/BF16 名稱也不代表已支援，仍須另外執行並驗證實際推論才能確認相容性。

Creative Bundle 可選 `asset_preset: character | background | texture | ui_ornament`，使用共用角色、背景、材質紋理或 UI 裝飾提示指引。Preset 只影響提示組合，會將版本雜湊記入輸出 manifest；不選 Provider、不授權生成，也不改變既有 Workflow、人工視覺審查與使用者接受流程。

`aips creative configure --project PROJECT --bundle RELATIVE.yaml` 從 stdin 接收 allowlisted JSON，回傳新的 Bundle 路徑；以該路徑 preflight，通過後才 execute。OpenCode 可直接使用相同 action。缺少模型或生成失敗時回報受阻，不改交 SVG；精緻插畫先校準代表性樣圖，完成後逐張檢查身份、人物結構、材質、光影與風格。

多個 Bundles 可用 `templates/creative/CREATIVE_JOB_MANIFEST.yaml` 列入工作清單，再執行 `aips creative generate-set --project PROJECT --manifest MANIFEST.yaml`；每項分別預檢，失敗後會繼續並保存結果，重跑時僅略過雜湊仍吻合的已完成項目。OpenCode 原生授權只來自目前提示，並依提示中的明確數量限制生成項目。

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

明確要求多位角色各自產圖時，授權會依角色／輸出數量設上限。創作中的短風格選擇可延續目前 Session 的有限回合；取消、切換工作、擴大範圍或超過數量後需重新提出明確要求。缺少本機引擎時會提供原因與恢復方式，不會自動下載模型或改用雲端服務。

角色素材沿用 `creative-calibration`、`visual-direction` 與 `visual-quality-review`。以 `CHARACTER_PROFILE.yaml` 記錄身份特徵與本機參考圖雜湊，以 `STYLE_PROFILE.yaml` 記錄媒材、構圖和文字規則；姿勢、表情、配件分開產出，避免一次生成後難以替換。預設使用已存在的本機 ComfyUI MCP；Apple Silicon 可選用 MFLUX。流程不安裝引擎、不下載模型，也不使用雲端或付費 API。清單需記錄精確模型版本、Runtime、授權來源與本機執行狀態。

執行時會把 Bundle brief、Character acceptance criteria、Style prompt constraints 與選用的 collection style lock 編譯成有界 Prompt，並記錄輸入 Profile 與編譯結果雜湊。可選的 `MODEL_CAPABILITY_PROFILE.yaml` 只依已記錄且經人工審查的能力證據提出模型建議，不會替你切換模型。

使用 `python scripts/character_artifacts.py validate MANIFEST --project PROJECT` 驗證檔案、路徑、尺寸、雜湊和來源；使用 `compose` 以 SVG 組成設定表並排上繁體中文標籤。輸出不覆寫既有檔案。這些檢查不會判斷角色是否一致或畫面是否合格，仍需人工依核准的角色與風格設定逐張審查；效能數據只有實際量測後才能填入。

如需產生視覺檢查建議，可明確呼叫 `aips creative review-assist --project PROJECT --manifest MANIFEST.json --model INSTALLED_OLLAMA_VISION_MODEL`。此功能只連本機 `127.0.0.1:11434` 上已安裝的 Ollama 模型，另存 advisory review 報告，不修改生成 manifest，也不代表 Human review 或使用者接受。

若要直接執行本機生成，可先用 OpenCode `creative_execution` 工具的 `prepare` 動作，或 `aips creative prepare` 建立版本化工作目錄，內含 README、Character Profile、Style Profile 與草稿 Bundle。準備流程只在明確素材 scope 建立固定的新檔，不覆寫；先補上已安裝引擎、模型版本與授權來源，再執行 `aips creative preflight --project PROJECT --bundle BUNDLE.yaml`。MFLUX Adapter 依固定能力表呼叫 FLUX.1、FLUX.2 Klein、Qwen Image Edit 2511 或 Z-Image Turbo 專用命令；FLUX.1 一次一張參考圖，只有支援 `--image-paths` 的 FLUX.2/Qwen edit 才接受最多八張專案內參考圖。ComfyUI 僅連線 loopback；一般 checkpoint 工作流維持既有限制，Z-Image Turbo 使用固定分離載入器工作流，兩者都拒絕自訂節點。預檢會核對本機工作流與模型清單，不會生成素材；缺少引擎會回報 `BLOCKED_NO_ENGINE`。確認後，以 `aips creative execute` 明確執行。輸出限於 EPHEMERAL 非 Git workspace 中指定 scope 的新 PNG/JPEG/WEBP 與 provenance manifest，不覆寫現有檔案、不下載模型。ComfyUI 編輯時須先將單張參考圖放入本機 input，且預檢會核對位元組雜湊。生成結果的視覺審查初始為 `PENDING`，請由獨立人工對照角色與風格規範檢查後，才用 `aips creative review` 記錄 PASS 或 REVISE；`aips creative trace` 只顯示原因碼、耗時、重試次數與雜湊。


Plan36 publication diagnostics preserve this topic's existing authority boundaries.

Creative 寫入在 Git 工作區仍維持既有的 Project Intelligence 防護；Scenario 269 只調整一般回合的 refresh 與索引提示，不放寬創作輸出。

## 需求釐清與 Planning

Scenario 266 binds injection review to added candidate lines while Secret/PII scanning still covers the full candidate diff.



需求階段可載入產品研究與遊戲設計技能；先釐清平台、輸入、核心循環、進程、失敗／重試與可及性。研究或 playtest 規劃須先定義參與同意、資料最小化與證據限制。

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

The shared publication scanner is an AIPS service boundary; it does not change native Runtime adapter capabilities.

安裝 AIPS CLI 不會註冊 Runtime adapter；`aips harness status` 初始回報 `OFF`。需要個人整合時才執行 `aips harness install`。更新只刷新可驗證的啟用記錄；`UNKNOWN` 會保留原狀。`aips harness uninstall` 移除可驗證的外部整合並保留本機 ownership／額外資料，標記 `OFF`。

Creative ComfyUI workflows use the separate AIPS Creative execution contract; Qwen reference binding does not expand Host adapter permissions.

OpenCode 顯示 `context_compaction_over_budget` 時，先以 `aips intelligence context --runtime opencode --project "$PWD" --prompt "<task>" --full --explain --format json` 檢視，再執行 `aips intelligence refresh-plan --project "$PWD"`。僅更新受影響的 Intelligence 主題後重試；修復前支援的 native file writes 維持拒絕。診斷不包含 prompt 或 section 內容，且不涵蓋一般 Shell/MCP 寫入。

Claude Code 的 managed publication Hook 在八秒內完成檢查；逾時會以安全 phase 與耗時回報 fail-closed 拒絕，不會自動重試。受保護的 push 前先執行 `aips publish prepare`，讓 Hook 使用 30 分鐘內、綁定精確候選的私有掃描證據；Prepare 會為它規劃的 push 或 PR 建立各自綁定的證據。Claude Code 的標準發布寫法見 `harness/adapters/claude-code/CLAUDE.md`。

FLUX 3 Klein 的 `TextGenerate` runtime schema 檢查由既有 Harness executor 執行，並在唯一一次 ComfyUI `/prompt` 請求前驗證最終工作流；預檢不會啟動生成。

Creative workflow commands remain explicit user-facing actions routed through the existing CLI and host authorization; schema inspection alone never submits a ComfyUI job.

Creative runtime 由共用 Harness executor 執行；model profile 資料只選用程式已審核的 topology family，不會增加工具或權限。
FLUX 3 Klein Base/Distilled 的資料型 profile 與動態 ComfyUI 參考圖綁定都沿用現有 Harness action grant；只有明確授權的 Creative execute 才能提交本機工作流。

OpenCode keeps direct writes confined to the project and requires READY Project Intelligence without unresolved instruction conflicts. STALE freshness alone is advisory for this local L2 case; external actions retain the existing Human gate.

The staged commit safety Hook also scans bounded AVIF metadata; its denial is a content-safety result and does not grant or change native tool authority.

Claude 的 Bash 失敗觀察位於 managed Harness hook，僅提供執行結果診斷，不改變 Host 權限或發布授權。

Claude Code publication guard 依 host 版本採用 fail-closed hook 設定；安裝指南說明舊版與未知版本的相容行為。

Creative asset import is a dedicated CLI workflow, separate from OpenCode native file permissions. Git destinations require the explicit, hash-bound import opt-in described under Creative Direction.

Publication Hook and Prepare share safe reason codes and candidate observations; their lifecycle fields remain separate from native Host permission and Human authorization.

Resource and creative Runtime Hook errors include a stable reason code and bounded recovery step; this diagnostic context does not grant a write or generation action.

The Claude Code Hook performs one read-only Publication Doctor check for explicitly retryable remote errors; Codex and OpenCode retain their existing observation behavior.

Native runtime publication denials return allowlisted diagnostic metadata only; they do not execute a publication command or grant authority.

Claude Host Auto Mode classifier denial and AIPS PreToolUse rejection are different failure sources; the read-only publication recovery report cannot resolve native permissions.

Native adapters may report Publication Doctor findings and safe next steps, but those observations do not grant Git publication, merge or policy-change authority.

其他 Agent 透過 MCP Resource `aips://catalog/skills` 取得目錄，再按需載入 `aips://skills/<skill-id>`；Host 的 MCP 設定須由使用者依官方方式註冊。解除安裝依 Harness ownership manifest 與內容摘要，只清除 AIPS 管理且未被修改的投影，保留原有或有衝突的 Skill。

Codex、Claude Code 與 Gemini CLI 也可使用 `aips skills install <skill-id> --host <host>` 安裝原生 Skill，或使用 `aips commands install aips.grill-me --host <host>` 建立原生命令入口。安裝紀錄與 Host-specific 移除方式詳見 [Harness 指南](HARNESS.md)。

發布前使用 `aips publish prepare --worktree <candidate-root> --title <title> --body-file <file>`；原生工具必須使用輸出的 `cwd` 與精確 `argv`。`--expected-fingerprint` 可拒絕舊觀察，`--host-denied` 只回報 Host 拒絕。每次續行重新查詢遠端分支與 PR；PLANNED 不是授權，也不是完整 Integration Gate PASS。

OpenCode adapter setup and version-bound evidence are separate. Consult the report's unsupported-effect states before relying on a native permission hook.

For personal-mode PR merges, the runtime adapter presents a per-operation confirmation with the validated PR, candidate SHA, and required-check state.

Git publication uses the runtime adapter’s supported hook surface. Claude and Gemini have native command hooks; Codex remains advisory, so users needing enforced isolation must use an externally protected high-assurance setup.


`aips approval` 由現有 CLI dispatch 提供；Hook 設定與 external issuer readiness 分開驗證。Codex/OpenCode ADVISORY 不因新簽章介面升級為 universal process enforcement。

For existing-project discovery, `aips intelligence impact-candidates --seed-path <path>` reports unreviewed source-backed relationships only; review evidence never grants mutation authority.

本次 prompt compiler 內部抽離不改變 OpenCode 原生工具、授權、安裝步驟或 creative 操作流程；原有 `creative_execution` facade 仍供既有呼叫端使用。

OpenCode creative tool 只有目前使用者明確提出視覺審查時才授予 `review-assist`；此權限與產圖數量及使用者接受分開。

OpenCode 對話中的創作延續只保留 Session root、有限回合與剩餘輸出數等結構化狀態，每次回覆仍重新判斷授權；不保存舊提示文字，也不以 Context 或 transcript 恢復權限。取消、切換工作、擴大範圍或達到數量上限後，需重新明確提出要求。

OpenCode V2 Creative writes use the current native user prompt for authorization; tool Context and prior transcript messages cannot renew a cancelled request.

診斷中的 MCP inspect 是靜態設定檢查，不會呼叫遠端或本機 MCP Tool；沒有原生 Host 證據時仍顯示 UNVERIFIED。

OpenCode `creative_execution` tool 與 `aips creative` CLI 共用本機執行器；ComfyUI Z-Image Turbo 需使用固定 API workflow 與已安裝權重，preflight 只查核，不會產生圖片。

OpenCode 創作 tool 支援 discover/configure，產圖意圖、原生檔案 guard 與 Shell effect policy 維持不同檢查；重新投影後仍須驗證實際 host hooks。

Creative discovery is read-only: it probes installed MFLUX commands and only the fixed `127.0.0.1:8188` ComfyUI API, while keeping model inference and image quality unverified.

OpenCode V2 的 creative execution tool 只接受明確創作或修改意圖，並在執行前要求 Bundle preflight 通過。

OpenCode V2 may use the managed plugin for Session-scoped Context, supported direct-file checks, and the structured `creative_execution` tool. In EPHEMERAL creative projects, its explicit `prepare` action creates a versioned README/Profile/Bundle set in a selected scope; `preflight` checks a local Bundle without starting generation, and `execute` is explicit and create-only. `aips creative scan --project PATH` indexes existing image/SVG metadata in the user cache; `aips creative next-version --project PATH --target RELATIVE_ASSET` suggests a new path and never writes it. To transfer an asset, first run `aips creative import-candidate --source-project SOURCE --source RELATIVE_ASSET --destination-project WORKSPACE --target RELATIVE_ASSET`; review the returned candidate SHA-256 and destination check, then run `aips creative import --candidate CANDIDATE_FILE --accept-hash SHA256` to recheck the source and create the destination file without overwriting. The candidate cache stores paths and hashes, not asset bytes. `aips harness trace` and `aips creative trace` show privacy-limited events. Arbitrary Shell effects and other MCP/custom tools remain outside the guard; inspect adapter status before relying on runtime enforcement.

Native Adapter 用來取得 runtime-specific hook / guard；MCP 提供跨 Host 標準接入。兩者共用 canonical Roles、Skills、Orchestration 與 Project Intelligence。

MCP-compatible Host 可以讀取 AIPS Roles / Skills / selected orchestration，並呼叫 bounded deterministic helpers。MCP Server 不執行第二個 LLM，也不取得 Human approval、Git publish、merge、release、production 或 host-native tool interception authority。

對完整支援 MCP 的 Host，優先使用 Resources / Prompts / Tools。對只提供 Tools 的 Host，使用 `aips_capability_catalog`、`aips_capability_read` 與 `aips_workflow_context` 取得同一份 canonical capability 與 Security／Architecture／Code Review、Delivery Plan context。

可用 `aips mcp config --client cursor|windsurf|copilot|amp|codex|generic` 產生 review-only 設定；輸出不會自動寫入第三方設定。`copilot` 指 GitHub Copilot CLI 的 local stdio 格式，hosted agent 仍需具備可執行的 AIPS runtime，不能直接沿用本機路徑。

MCP-only enforcement 誠實維持 `ADVISORY`；可驗證的 native pre-tool hook 才能回報 `TOOL_GUARDED`。

新增 Runtime 時先採 MCP；只有存在 MCP 無法提供的可驗證 hook／guard／event requirement，才建立 native adapter。

詳細請看 [Global Harness 與 MCP](HARNESS.md)。

Turn Context 只列出這一回合真正需要的準備步驟：READY+STALE 的 Intelligence 在任務相關主題未受影響時只是提示，不要求 refresh；唯讀或未選到主題的回合不會要求建立 Retrieval 索引。修改既有專案時仍須處理 Change Impact。

## Roles、Skills 與重用

The Matt Pocock Skill Explorer remains a separate discovery workflow and does not alter publication scanner policy.

Qwen Image Edit Plus support extends the existing workflow contract and does not add a Role, Skill, or Skill Explorer permission.

透過 OpenCode 使用 Role 或 Skill 時，Turn Context 必須先通過 12,000-byte 投影檢查；超限診斷不改變 Skill 目錄、安裝或授權。

The JSON error result is a CLI contract only; it does not add a Role or Skill permission and cannot authorize a Git operation.

Publication denial recipes are CLI guidance only; they add no Role or Skill permission and cannot authorize a Git operation.

Publication guard 重用既有的 command authority 與 Secret Scan；scan evidence 只是短效候選證據，不會新增 Role、Skill 或 Git 操作權限。

這次 FLUX 3 Klein 修復只調整 Creative executor 與其預檢，不新增或改變 Roles、Skills 或 Skill Explorer 行為。

The `creative workflows` CLI is a separate workflow utility and does not add or change the Skills catalog or Skill Explorer behavior.

Model profile registry 是 Creative runtime 設定，不會安裝 Skills，也不改變 Skill routing。
本次新增的 Distilled profile 與一至八張動態參考圖只擴充既有 Creative runtime 資料契約，不新增 Skill、Role、catalog 項目或安裝路由。

Skill installation remains independent of project state. `aips attach` only initializes or imports external user state; it does not change project files, Git configuration, hooks or ignore rules.

Scenario 267 changes no Skill discovery or installation behavior; its lifecycle exercises Project Intelligence freshness and the OpenCode direct-write guard.

Content-safety controls remain separate from skill discovery, installation, and author trust decisions.


Publication scanner diagnostics do not add Skill discovery, routing, installation or ownership behavior; use the Git Publication and Runtime Content Safety sections for their recovery contract.

The optional Matt Pocock Skill Explorer and its install controls remain separate from media validation; AVIF support adds no Skill, Role, or capability route.

Plan44 沿用既有 Skill Explorer inventory 與列出預設，不新增 Skill、Role 或上游目錄項目。

Runtime adapter 的安全能力依各 host 的實際版本判定，不能由 Skill 或能力目錄推定。

Skill Explorer manages reusable instructions; creative asset import is a separate asset workflow and does not install or modify Skills.

`aips safety diagnose commit` is an independent read-only CLI; it adds no Skill inventory, Skill Explorer route, or installation behavior.

Publication diagnostic lookup is an explicit CLI capability in the existing Git workflow; it does not add or change Skill discovery, routing, installation, or ownership.

Upstream Skill discovery and installation remain governed by the pinned canonical inventory and ownership-safe projection lifecycle; Creative asset presets are not Skills and do not alter that registry.

The Skill Explorer remains a read-only catalog; publication Doctor changes do not alter Skill discovery, selection or installation.

Publication Doctor uses the existing runtime adapter boundary and does not alter Skill discovery or routing.

Optional Skills and Human Skill Explorer are independent of PR publication diagnostics; no Skill installation may silently change merge authority.

Skills and portable commands can direct users to the core `aips publish doctor` CLI for repository setup; installing a Skill does not grant publication or merge authority.

使用 <a href="./skill-catalog.html">Skill Explorer</a> 依名稱、用途或分類搜尋 49 個目前可用的 AIPS Skills，並複製提示範例。Explorer 與 `aips skills list --include-upstream` 也列出 Matt Pocock 上游 38 項 vendored Skills、來源摘要、路由處置與安裝資格；31 項可安裝，7 項同名技能使用 AIPS canonical 版本。`disposition` 描述與 AIPS 的整合關係，使用者仍可自行決定是否安裝上游副本。`$grill-with-docs` 是獨立明確呼叫 Skill，不會由一般規劃或寫文件需求自動觸發。Writing Fragments、Beats、Shape 維持明確要求才使用。

終端機可執行 `aips skills list` 查看繁中分組清單；CLI 可獨立於 Runtime adapter 啟用狀態使用。以 `--capability <id>`、`--trigger <trigger>` 篩選，`--include-upstream` 加入上游 38 項、路由處置、安裝資格與本地來源路徑，`--locale en` 切換英文，`--group-by category|status|source` 切換分組，`--format json` 輸出機器可讀資料。此命令只讀取 Skill 中繼資料，不會修改 Skill 或索引。

將 AIPS Skills 安裝為 Host 原生 Skills，可使用 `aips skills install <skill-id> --host codex|claude|gemini`。Codex 與 Gemini 共用 `~/.agents/skills`；Claude Code 使用 `~/.claude/skills`。加入 `--scope workspace --project <path>` 可改裝在指定專案；以 `aips skills status` 檢查紀錄，以 `aips skills uninstall <skill-id> --host <host>` 移除。安裝紀錄位於 AIPS XDG config 下的 `skills/ownership.json`，記錄 Host、路徑及逐檔摘要。重複安裝會更新同一份 AIPS-owned 投影，不會覆寫無主控記錄的原生 Skill。卸載只刪除摘要仍吻合的檔案；修改檔案與額外資源會保留。

上游清單可用 `aips skills list --include-upstream --group-by status` 瀏覽。使用 `aips skills install --upstream <skill-id> --host <host>` 安裝任一非 canonical 上游原生 Skill；`aips skills install --upstream --all --host <host>` 會安裝 31 項、略過 7 個由 AIPS canonical 提供的同名技能。Codex 可用 `$<skill-id>`、Claude Code 可用 `/<skill-id>` 明確呼叫；Gemini CLI 會在啟用前請求確認。以 `aips skills status --upstream` 檢查，再用 `aips skills uninstall --upstream <skill-id> --host <host>` 或 `aips skills uninstall --upstream --all --host <host>` 解除。這些操作沿用來源專屬 ownership 紀錄；不覆寫原有 agent Skill，也不會執行上游腳本或修改 agent hooks。

Portable Command 也能提供原生 Skill 入口。例如在 Codex 執行 `aips commands install aips.grill-me --host codex`，再呼叫 `$grill-me`；Claude Code 使用 `/grill-me`，Gemini CLI 可用 `/skills list` 確認；若是已開啟的 Gemini session，執行 `/skills reload` 後再呼叫 `/grill-me`。以 `aips commands status --host <host>` 檢查，使用 `aips commands uninstall aips.grill-me --host <host>` 精確移除該命令；`aips commands uninstall --host <host>` 則移除該 Host 的全部 Portable Commands。一般請求不會自動啟動訪談。MCP 仍可作為另一種載入方式，詳見 [Harness 指南](HARNESS.md#在-opencode-以外載入-aips-skills)。


新增能力前依序檢查：

~~~text
Reuse existing Skill / Template
→ Extend Workflow
→ Extend System / Orchestration
→ New Capability
→ New Role only when responsibility truly differs
~~~

只有責任、決策邊界與 review obligation 真正不同時才新增 Role。專案自己的 conventions / rules 優先保存成 project-native knowledge，而不是無限制提升成 global Skill。


Plan36 publication diagnostics preserve this topic's existing authority boundaries.

Release history 更新（純依賴升級文件豁免，Scenario 221）已審查本區段：Skill 整合、Explorer 與重用行為不變。

`aips intelligence gc` 是新的維護指令，與 Skills CLI 分開：預設為 dry run，列出專案路徑已不存在的外部 Intelligence store；確認後加上 `--yes` 才會刪除，且不會刪除路徑仍存在或無法驗證的 store。

新 worktree 沒有外部 Intelligence store 時，`aips intelligence bootstrap` 會先嘗試從同一 repository 的 READY store 複製一份（copy-on-write，來源只讀）；來源不安全或複製失敗時退回正常初始化，並在 observations 中標示 `intelligence_seed_fallback`。

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

Scheduler 依明確 task graph 與 ownership 狀態執行；缺少可驗證的 task owner 或 resume 證據時，應停止並回報原因。

The Scheduler does not choose ComfyUI node mappings; Scenario 236 verifies Qwen reference binding separately from task ordering and resume state.

Creative 執行仍由既有 executor 明確呼叫；FLUX 3 Klein 的 schema 預檢只驗證最終 payload，不會建立排程工作或重送失敗工作。

ComfyUI workflow 與 sampler 設定由固定 profile 決定；registry 擴充只能填入該 topology family 核准的值。

Creative quality evidence does not alter Scheduler ownership, output budgets, or the Human decision required for publication.

創作延續狀態只協助短風格選擇，不會排程或自動重試生成。每次產圖仍需明確執行動作，並通過本機引擎 preflight。

discover/preflight 是唯讀操作；configure 會建立版本化檔案，execute 才會啟動 provider。排程與狀態不可將這些不同效果混為完成產圖。

Creative Profile/Bundle setup is an explicit user action; image generation is never started as a background scheduled task.

Scheduler fingerprints retain their existing raw digest format through the shared canonical helper; task graph ordering and execution ownership are unchanged.

LLM 負責 semantic planning；Scheduler 只接受已形成的 Task Graph，依 dependency、boundary、authorization、state 與 deterministic ordering 決定 dispatch，不自行發明 task、scope 或 approval。

Parallel task 必須先證明可安全並行；同一 change boundary 的 competing writer 不因想提高速度就被放行。

PR 驗證會把 Gate 與 Repository Health 報告放在 CI runner 的暫存位置，完成後再上傳 artifact。這讓驗證不會因產生報告檔而把 checkout 判定成 dirty，合併前看到的證據仍對應同一個 commit。

受保護分支的 `repository` required check 必須在 exact PR candidate 的 Integration Gate 成功後才會通過。

Installation entrypoint workflow 保留既有 pull request 路徑與平台檢查，並以近期 job P95 加安全倍數設定明確逾時；逾時會作為該 job 的失敗呈現，不改變 required check 或 Human 核准權限。

## Execution Isolation 與 Runtime Resource

平行工作透過獨立 worktree 與 runtime resource 配額隔離；隔離狀態可觀測，但不會擴大專案或 Host 權限。

ComfyUI 操作須同時通過 Resource Authorization 與 Runtime Policy。Runtime Policy 可將目的地限制到精確 host、port、method 與 path；profile 缺漏或目的地不符時，應先修正受信任設定與授權範圍，不要重試被拒絕的請求。

Qwen Edit Plus references remain project-staged, hash-verified, and submitted only through the existing local loopback ComfyUI boundary.

FLUX 3 Klein 仍使用固定本機 ComfyUI workflow；`TextGenerate` 的 live schema 與最終序列化欄位會在 loopback `/prompt` 前核對，MPS 推論狀態獨立保留為未驗證。

Dynamic ComfyUI discovery is restricted to the configured loopback service, and import writes only a new workflow file within the selected project.

ComfyUI profile 只使用固定 loopback endpoint 與 allowlisted workflow；新增模型仍須通過完整本機元件 inventory preflight。

ComfyUI Resource Authorization remains independent of AVIF container inspection and does not authorize reading or transferring media assets.

Resource Authorization requires an explicit matching kind, selector and operation; network actions additionally need a true network grant and matching destination constraints.

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

Qwen Edit Plus local fixtures verify workflow contracts only; visual quality, Human review, and user acceptance remain independent evidence.

最終工作流驗證與節點執行結果分開回報；synthetic lifecycle 通過不代表 FLUX 3 Klein 已在 Apple Silicon MPS 完成推論或 VAE 解碼。

Dynamic workflow synthetic lifecycle evidence verifies request and recovery contracts only; real model inference, hardware compatibility and visual quality remain unverified until separately observed.

Scenario 266 records content-safety verification while preserving existing maintenance and publication authority boundaries.


Scenario 266 provides local deterministic safety evidence; it does not substitute for independent review or grant approval.


Commit diagnostics expose redacted evidence only; any independent review remains governed by the candidate Core Change Matrix.

Publication lifecycle observations are not independent-review evidence and do not satisfy a Human review or a native Host decision.

Creative presets add bounded prompt guidance only. They do not select a model, authorize generation or replace the existing workflow preflight and Human review.
FLUX 3 Klein Distilled 的 synthetic lifecycle 與多參考圖綁定測試只驗證本機契約；不能取代獨立視覺審查、使用者接受或真實推論觀測。

Publication authority tests cover the shared target-policy observation and the Claude-only bounded recovery path; they do not imply a change to Skill evaluation.

Skill Explorer 可搜尋可用的 AIPS 任務方法；上游方法的採納狀態與選用條件以卡片標示，Writing workflow 仍須明確指定。

Plan29 #6 is reviewed as a scoped Core Change: its exact source and destination checks, direct lifecycle evidence, and candidate matrix are reviewed before the PR Gate.

Creative benchmark v2 is read-only evidence after an explicitly run local trial. Its coverage matrix does not rate images or replace Human visual review or user acceptance.

OpenCode native acceptance is not evidence of production model quality, generated-image quality or user acceptance.

指出「疤痕畫在頭髮上」會形成版本綁定的缺陷回饋；明確要求「重出一張哈利」可在同一 Session 取得新的單張修正授權。`quality-check` 逐項檢查必要特徵與禁止錯置；只有明確要求自動修正才可使用 `quality-loop`，最多兩次修正，預設 native 時間上限十分鐘。


使用瀏覽器 E2E、觀測性、遷移和 LLM 安全技能時，依受影響邊界與風險挑選驗收；需主張玩家體驗時，確保計畫包含適當人工或 playtest 證據。

Agent Eval 報告的 `observed_task_outcomes` 是額外的任務觀察，與 rubric 通過率分開。模型 token／成本沒有可靠資料時顯示 UNKNOWN；Creative 影像有效性不能替代你的視覺評分與接受。

Review bounded Impact Graph candidates with their source path and line. Dynamic relationships remain unknown, and candidate output does not alter canonical coverage.

Review assistance is an optional local second opinion. Inspect the actual image and approved Profile yourself; model findings cannot complete visual review or user acceptance.

CI 會依候選安裝完整 Python 驗證套件以執行必要的 repository fixtures；只有 Node、文件建置與 Chromium 等執行工具依變更路徑安裝。

創作授權、Bundle／輸出 provenance、人工視覺審查與使用者接受是不同證據；通過程式 Gate 不代表角色品質已驗收，也不會自動取得 Git 合併權限。

Creative output integrity, human visual review and user acceptance remain separate states; a successful local batch does not mark image quality as approved.

Project Diagnostics 的輸出只能協助定位下一步，不取代獨立 Review、必要測試、完整 Integration Gate 或 Git 發布核准。

品質基線與模組預算用於避免既有 debt 增長；coverage 報告維持 report-only，不代表整體覆蓋率門檻或人工品質驗收。

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

Real-task comparison uses a Human-selected fixed cohort and the same case fingerprints for baseline and candidate. Keep task completion, human corrections/false positives, Trajectory Eval security findings, and directly observed telemetry separate; retain failures, and leave missing observations `UNKNOWN`. Existing fixtures do not establish an empirical baseline. See [Scenario 229 — Agent Eval Freshness Selection](./CONFORMANCE.md#scenario-229-agent-eval-freshness-selection).

Plan17 regression evidence covers numeric diff headers, four browser/OpenAPI combinations, mandatory aggregates, reusable caller keys/permissions, explicit Python and isolated children, recursive placement, signed identity/immutable proposal rejection and atomic deletion races. Missing or malformed capability plans retain the full profile. A latest cancelled check stays INCOMPLETE; replaced old checks are reported as SUPERSEDED.

The shared Python CI bootstrap checks each caller-declared import profile and dependency consistency; it complements the required full repository Gate.


Publication commands remain available through `bin/aips` and the existing `scripts/aips_cli.sh` entrypoint. The facade loads its internal command modules from the selected AIPS checkout before dispatch, preserving the same command arguments and results for source and installed entrypoints.

Validation optimizations must preserve the full Integration Gate and execute every unique lifecycle evidence script at least once; the maintenance guide describes the local exact-candidate workflow.

Validation observation and graduation reports are advisory. The report exposes validator-level precision, recall, false-negative rate and confusion counts; an empty denominator is `null`, not a zero-risk result. If collection dependencies, PR attribution or artifacts are missing, the evidence stays `NOT_READY`; the full repository Gate still runs, and no validator is skipped.


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

The shipped export config is disabled. Transmission requires a private config with `enabled: true`; HTTPS is required except for loopback testing. Keep optional authorization in the host environment variable named by `authorization_env`. Recorded values are limited to lifecycle IDs, fixed operation names, verified provider/model IDs, runtime, Human governance decision, bounded quality finding delta, coarse outcomes and token counts. Export omits prompt/output content, arguments, private reasoning and credentials. Unpaired markers show `TELEMETRY_DEGRADED`; this does not block the workflow. See [OpenTelemetry run export](./TECHNOLOGY_GUIDE.md#opentelemetry-run-export) for field limits and replay behavior; the canonical contract is `orchestration/TELEMETRY_EXPORT.md`.

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


Plan36 publication diagnostics preserve this topic's existing authority boundaries.

Dependabot repository preflight 與 action 釘選同步（Scenario 221）：`scripts/repository_preflight.py`、文件同步 contracts 與 `scripts/documentation_sync.py` CLI 一律經由 `documentation_sync.evaluate_candidate` 判斷文件同步，與 docs-impact、placement 共用同一個 `pure_dependency_update`；不符合時完整規則照舊。驗證 contracts 不再複製 action commit SHA，改由 `dependency_impact.require_pinned_action` 檢查 action 名稱完全相符、40 碼完整 commit SHA、版本註解不低於已審查下限，以及成對 workflow 使用同一 SHA；evolution 設定改記 `action: openai/codex-action`。新 SHA 是否等於上游 tag 對應的 commit，仍由人工審查確認。

ComfyUI 工作恢復的 lifecycle fixture 只驗證 queue 讀取、確切 ID 刪除與不中斷非 AIPS 工作，屬於恢復安全證據，不代表 Agent 任務成果或品質。

## Logging、Observability 與 Operations

The Parallel Run Dashboard projects run state; it is separate from exact-candidate Content Safety scanning.

Run dashboard 只投影外部持久化的 run state 與事件；不得把執行紀錄寫入專案目錄或暴露原始敏感輸出。

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

Checkpoint 與 resume state 儲存在 AIPS 使用者狀態目錄，並以專案身分命名空間隔離；附加或解除專案不會清除使用者資料。

For Creative `generate-set`, the job result records each Bundle independently; reruns skip only completed outputs whose saved Bundle, output and provenance hashes still match.

Run projection fingerprints preserve their existing facade and canonical digest bytes after helper consolidation; run state and resume authority remain governed by the existing contracts.

Standalone and shadow dependency-review artifacts retain exact base/head, run ID, actual JSON findings and outcome for 90 days. Parity compares canonical findings; missing outputs, different candidates or inaccessible artifacts stay UNKNOWN. Job success alone cannot promote the shadow. Record resolved toolchain fingerprints and repeat full Gates only for new changes or unresolved failures.

長流程在 material step 保存 durable checkpoint / event evidence。Resume 時重新比較 repository/workspace identity、HEAD、branch、dirty state 與 relevant approvals。

舊聊天內容不是 authoritative run state；若 workspace fingerprint 已變，先 refresh / revalidate 再接續。

## Project Intelligence

`aips attach`、`aips detach` 與 preflight 不會寫入 `.ai/`、`.aips/`、`.git/info/exclude`、Git hooks 或專案設定。若既有 `.ai/` 含有 Intelligence，明確執行 attach/bootstrap 會驗證後複製到外部 user state，保留原始內容供審核及回復。

遷移舊 repo 資料時，先執行 `aips migrate-state --project <path> --dry-run` 檢視 Git-listed、未追蹤與 ignored 路徑；`possible_durable_knowledge` 是保守提示，仍需逐項審核。確認備份目的地位於 repo 外後，`--apply --backup-to <absolute-path> --confirm-repository-id <exact-id>` 會先產生私密、checksum 驗證的備份，再只從 Git index 解除 `.ai/`、`.aips/` 追蹤，保留工作目錄內容。若需回復 index，使用命令回報的 `git restore --staged -- .ai .aips`；備份不會自動刪除。


診斷的 Recovery Plan 按既有狀態提供檢查、補主題、finalize 或 refresh 順序。每步都標示操作種類與所需授權；計畫供檢視，不會自動執行或改變 Project Mode。

When creative Impact Graph edges are unavailable, use the documented scoped consumer review and keep repository-wide coverage marked partial.

Change Impact 需把創作授權 adapter、policy、executor、呼叫者與消費者納入 bounded traversal；只完成種子範圍不能宣稱 repository-wide graph 完整。

Project diagnose provides the next read-only inspection or recovery pointer; users choose whether to run a suggested repair.


遇到 Project Intelligence 狀態不完整時，可先執行 `aips project diagnose <path>` 查看 reason code、下一步與重新驗證命令。診斷不會自動 bootstrap、refresh、attach 或修復；請先檢視建議，再明確執行相應操作。

Turn Context 顯示固定核心與本回合選取的 canonical protocol routes；路由清單只提供指引，變更前仍須完成 Change Impact 與正式核准。

`aips intelligence context --project . --runtime codex --prompt '...'` 預設顯示精簡 YAML；`--full` 顯示完整診斷。可用 `--target-path src/file.py` 限定指示範圍，或用 `--intent read|write` 明確標示本次意圖。JSON 輸出維持完整格式，供既有整合使用。

Stable Intelligence 保存 Architecture、Data Flow、Modules、Contracts、Conventions、Testing、Security、Operations、Source Registry 與 Impact Graph。

Just-in-Time Retrieval 只帶入本次任務相關的 code、symbols、tests、history、graph evidence，避免每個 Turn 重掃整個 repository。Retrieval cache 是可重建 acceleration layer，不取得 governance authority。

詳見 [Project Intelligence](PROJECT_INTELLIGENCE.md)。

Retrieval index persistence is an internal, rebuildable cache boundary in `scripts/retrieval_storage.py`; existing commands and imports continue through the `retrieval_intelligence.py` compatibility facade.

## Git Publication 與 Release

使用 `git -C <path> push` 時，`<path>` 以執行命令時的 cwd 為基準解析；AIPS 將候選 SHA、ref 與掃描綁定到該目標工作樹。無效、缺漏或動態路徑會在候選檢查前拒絕。

原生推送可使用完整候選 SHA 與完整分支 ref，或 `git push -u/--set-upstream origin <目前分支>`。分支縮寫只接受所選工作樹目前分支，並正規化為已觀測的完整 HEAD SHA/ref；裸分支名稱、`HEAD` 或其他分支仍拒絕。語法支援不代表授權，掃描、遠端政策與 Human approval 仍照常執行。

一般 personal publication 只推送已提交的 candidate SHA/ref。本機未提交修改會保留並顯示為工作樹診斷，不會被自動加入候選，也不會單獨阻擋該 commit；遠端授權、完整內容掃描與 GitHub 保護仍適用。

WebM files have no path exceptions. Strict candidate scanning validates bounded EBML structure, scans declared text metadata and skips media payloads; malformed or oversized files block publication.

Publication preflight scans the exact candidate tree and commit history. The scanner fails closed on oversized or unreadable content and keeps provider-token, private-key and high-entropy literal detection enabled.

For workflow dependency PRs, keep action references on verified immutable SHAs and preserve the validation toolchain contract; merge only the exact candidate after the required `repository` check passes.

### Claude Code 發布 Hook 遠端逾時

Hook 遇到可重試的遠端觀測失敗時會立即拒絕並提供安全診斷，不會在同步 Hook 中等待 Doctor。請在同一候選工作樹執行唯讀命令 `aips publish doctor --worktree . --format json`；完成排除後重新執行 Prepare。逾時表示尚未完成遠端驗證，不代表授權或已執行。

SSH remotes such as `git@github.com:<owner>/<repo>.git` are not treated as email addresses, but any other email in a commit or diff is still blocked. If a commit is blocked for an email, remove the real address or use clearly fake test data; do not split the string to get past the scanner.

Content-safety PASS is candidate evidence only and does not authorize PR merge or change publication mode.


Personal publication rejects unsupported literal command forms before candidate inspection and reports scanner policy, Git-object and file-read failures with stable redacted `SECRET_SCAN_*` codes. These failures remain blocked and non-authorizing.

AVIF content-safety checks do not replace the publication mode, Human review or merge approval described here.

Claude Code v2.1.295+ 的 publication guard 在 Hook 啟動失敗時使用 `onFailure: block`；舊版/未知版只回報限制並保留相容設定，diagnostic 不會授權重試或合併。

Commit-safety findings provide recovery guidance only; exact-candidate approval, Required Checks, and Human authority still govern publication and merge.

Runtime Hook diagnostics are advisory recovery context. They do not approve publication or bypass the candidate Gate and native Host confirmation.

When diagnosing a feature branch, `aips publish doctor` checks policy on the remote default branch by default; `--branch` explicitly selects a policy target. The report separately shows the candidate branch and never authorizes publication. Transient recovery re-runs read-only evidence collection only.

### Claude Code 合併失敗的真實原因與安全恢復

若 `aips publish prepare` 或 `aips publish diagnose` 在 CLI 邊界遇到本機例外，搭配 `--format json` 會在 stdout 回傳結構化 `BLOCKED` 診斷，列出穩定 `reason_code`、允許的 `error_class`，以及 OS 錯誤的 errno 類別和安全復原步驟；原始例外文字、路徑與命令不會輸出。退出碼仍為 2，`authorized` 與 `executed` 均為 false。文字模式仍將原始錯誤寫到 stderr。

建議先在信任的互動式終端機執行 `aips publish doctor --project-root <repo> --pr <number> --format json`；要檢查格式，使用 `aips publish diagnose --worktree <repo> --command '<literal-gh-pr-merge>' --format json`。這兩個指令均為唯讀，不能當作已完成合併或取得 Host 授權。新版 `prepare`／`diagnose` 會提供 `recovery` 建議，其中 `authorized: false`、`executed: false`；只允許針對明確暫時性狀態重試唯讀觀察。

- `MERGE_HEAD_PIN_REQUIRED`：必須讀取當前 PR HEAD 並加上 `--match-head-commit` 的完整 SHA；`MERGE_HEAD_MISMATCH` 代表提供過期或錯誤的 SHA。
- `MERGE_OPTION_FORBIDDEN`：不能附上 `--admin` 或 `--delete-branch`，合併和分支清理需分開授權。
- `REQUIRED_CHECKS_UNCONFIGURED` 只能由完整的政策證據確認；`REQUIRED_CHECKS_POLICY_UNVERIFIED` 表示政策查證不足，不能說成 CI 還在跑。
- `REQUIRED_CHECKS_MISSING` 表示應觀察的必要檢查不存在，`REQUIRED_CHECKS_PENDING` 表示實際觀察到進行中的檢查；兩者都阻擋合併。
- `HOST_MERGE_WITHOUT_REVIEW` 來自 Claude Code Host Auto Mode，不是 GitHub 或 AIPS 核心出錯。由使用者透過原生確認流程處理。若 Host 允許唯讀指令，可用 `aips publish prepare ... --host-denied --host-denial-class merge-without-review` 回報**已觀察到**的分類；不得為了繞過分類器而改寫命令。
- `HOST_READ_ONLY_DENIED` 代表 Host 阻擋唯讀診斷，可改由受信任的使用者終端機查詢，不能自行推定 Host 權限已恢復。

Personal Mode 的逐次合併確認和 High-Assurance Mode 的外部 signed grant 不同。所有原始 stderr、敏感 URL 和機密欄位應限制曝光；維持穩定錯誤碼、來源、可行的排除方式及完成後驗證。每次真正執行合併前仍須重新確認 head/base/checks 與人類授權。



`aips publish diagnose --worktree <candidate-root> --command '<literal-command>'` 可辨識 `PUSH_SOURCE_NOT_EXACT_SHA`、`INVALID_TARGET_REF`、`WORKTREE_DIRTY`、`BASE_NOT_ANCESTOR`、`CONTENT_SCAN_BLOCKED` 與 metadata 問題。`prepare` 的高保證流程輸出精確 lease 命令與 `AUTHORITY_REQUIRED`，仍須由外部 issuer 核准；模式設定存在但無效時不降級。`--merge-intent` 僅記錄當次任務意圖，不能取代使用者或 Host 授權。

首次設定或 PR 卡住時，可執行 `aips publish doctor --project-root <repo> [--pr <number>] --format yaml`。Doctor 只讀檢查 GitHub CLI 登入、repository merge methods、branch protection/ruleset 可見性、Required Checks 與指定 PR/head/checks，並列出安全的下一步。Required Checks 會明確回報未設定、權限未知、失敗、執行中、缺少／跳過、取消、PR head/base 過期或 GitHub 網路／限流／伺服器錯誤；任何空白或不可見證據都會阻擋，不會自動調整保護規則。GitHub 對 skipped check 的結果保留為 provider 成功，AIPS 仍以 `MISSING` 阻擋發布。Claude Code Hook 只會在可重試的網路、限流或伺服器錯誤時自動執行一次唯讀 Doctor。`aips publish diagnose` 也接受 literal `gh pr merge`，依 `AIPS_ENFORCE_REQUIRED_CHECKS=1` 設定驗證 Required Checks；預設仍驗證 PR、完整 head SHA、base 與 merge method，但標示 AIPS check gate 未啟用。Doctor 繼續回報即時政策／checks 狀態。輸出 `authorized: false`、`executed: false`，不執行 merge、不消耗 grant。Codex/OpenCode 的診斷仍不取代原生工具權限或 GitHub 保護。

`aips publish doctor --worktree <candidate-root> --worktree-details` 是唯讀診斷，可選擇 `--branch <name>` 與 `--pr <number>`，輸出分階段證據、穩定原因碼、HTTP status、端點及已遮蔽的錯誤摘要。dirty 明細只列 repo-relative staged／modified／deleted／untracked 路徑與處理建議，不讀檔案內容、不會 stash、刪除或忽略檔案。HTTP 404 只有在分支存在且 effective-rules 證據完整時，才可判定沒有作用中的分支規則；當 `branch.protected` 為 true 而 classic protection 回覆 403 時，Required Checks policy 為 `UNKNOWN_PERMISSION`，並保留這個狀態與診斷。一般 Doctor 不會因權限不足或未設定 Required Checks 阻擋個人分支發布；只有 `AIPS_ENFORCE_REQUIRED_CHECKS=1` 的嚴格驗證會把未知／未設定狀態列為 blocker，merge 驗證仍對未知狀態 fail closed。`ALREADY_MERGED` 會導向 exact-head post-merge reconciliation，不會再次規劃 push、建 PR 或 merge。診斷與 `retryable` 欄位都不授予發布權限；主機拒絕、Human approval 或 GitHub 原生 required checks 仍依原流程處理。

若開發 workspace 有未交付素材，保留原檔並建立獨立乾淨的工程分支 worktree，再將該 root 明確傳給 `prepare` 與原生 tool。素材清單至少記錄路徑、用途、SHA-256、大小、授權與部署來源；母帶需獨立備份，正式音訊經壓縮與音質驗收。Git LFS／物件儲存由專案決定，且部署必須驗證實體檔案可取得。Scanner 的文字、binary 與來源政策限制要各別診斷，不因檔案大小推論授權失敗。

`.m4a` 可作為 Git 內的音訊素材，限 8 MiB 且須通過容器品牌與 atom 結構檢查；AIPS 掃描其中 metadata，不將 `mdat` 音訊內容當文字解碼。格式偽裝、metadata secret、內容安全命中或超過 8 MiB 都會阻擋發布；較大的音訊請使用 Git LFS 或外部物件儲存，並在 repository 保留可追溯的 asset pointer／部署說明。既有文字掃描上限與其他二進位格式政策維持適用。

TTF、OTF、WOFF 與 WOFF2 字型也可通過有界 metadata 掃描；AIPS 會核對檔案簽章、格式、副檔名及解壓大小，並掃描字型名稱與廠商欄位。缺少解析套件、格式偽裝、損毀、超出上限或 metadata 命中 Secret／PII／Injection 規則時，commit 與發布都會阻擋。字型輸入上限為 8 MiB、宣告解壓上限為 32 MiB。

發布前使用 `aips publish prepare --worktree <candidate-root> --title <title> --body-file <file>`；原生工具必須使用輸出的 `cwd` 與精確 `argv`。成功完成完整候選／歷史 Secret Scan 後，Prepare 會在 private user cache 寫入 30 分鐘有效的掃描 evidence，精確綁定 repo/worktree、base/head、operation、remote、full target ref、remote OID、diff、scanner 與 policy。Hook 每次仍重驗 Git／遠端／目標；缺少、過期、毀損或不相符 evidence 會拒絕並要求重新 Prepare。此 evidence 不授權推送，完整候選／歷史掃描仍由 Prepare 和 final Integration Gate 執行。`--expected-fingerprint` 可拒絕舊觀察，`--host-denied` 只回報 Host 拒絕，`--auto-merge` 只規劃 GitHub `--auto`，要求非空且全部通過的 required checks，並保留原生 Human 授權。每次續行重新查詢遠端分支與 PR；PLANNED 不是授權，也不是完整 Integration Gate PASS。個人模式可使用明確完整 SHA/ref，或帶 `-u`／`--set-upstream` 的目前工程分支縮寫；後者會綁定至已觀測的完整 HEAD SHA 與 full branch ref，並仍須通過唯一 origin、掃描與既有授權檢查。

Prepare 與 `aips publish diagnose` 會並列候選驗證、授權與執行狀態。`PLANNED` 代表只完成規劃；`AWAITING_AUTHORITY` 代表需要 Human grant；Hook 的 `AUTHORIZED` 只代表 AIPS Hook 放行，Host 仍可能拒絕且指令尚未執行；`EXECUTED` 只能由實際執行結果確認。`next_step: PUSH`、掃描通過或觀測指紋都不會授予權限。診斷包含安全的 worktree ID、候選 SHA、完整 target ref、publication mode 與 AIPS 版本／revision，僅供核對環境，不作為授權憑證。未知錯誤會回報 `INTERNAL_DIAGNOSTIC_GAP`；已知分支目標不一致會回報 `PUSH_TARGET_BRANCH_MISMATCH`，並提供繁中排除步驟。

Diagnostic ID 只有在使用者已設定既有 `AIPS_GOVERNANCE_AUDIT_LEDGER` 時，才會寫入 allowlist 欄位並可用 `aips publish diagnose --diagnostic-id <UUID> --format json` 查詢。查詢會驗證 hash chain；未設定時顯示 `NOT_CONFIGURED`，不會自動建立新 ledger。Trace 寫入失敗不會改變 Hook 的允許／拒絕決定，也不輸出原始指令或例外內容。

`aips publish diagnose` 對 pipe、多重命令與 Shell 包裝語法維持拒絕；`git push -u/--set-upstream origin <目前分支>` 只在分支符合目前工程 branch policy 時接受，並以唯讀方式正規化至目前候選 SHA/ref。裸分支、`HEAD` 或其他分支仍拒絕。診斷會在既有穩定錯誤碼下提供 `detail_code` 與安全修正指引，不會授權推送。Claude Code 的 `PostToolUseFailure:Bash` 另外回報已開始執行的原生工具失敗階段、固定錯誤分類及可解析的 exit code；原始 Host 錯誤與命令不會進診斷，Hook 不會重試或授權。PreToolUse 拒絕仍標示 `NOT_EXECUTED`。

`branch-hygiene.yml` 的報告會依 branch SHA、目前 main、local checkout 與 PR 狀態列出 `KEEP`、`SUPERSEDED`、`REBASE_REQUIRED` 或 `CLEANUP_CANDIDATE`。這些分類供維護者檢視，不會自動 merge、rebase、關閉 PR 或刪除 branch；清理仍須逐筆核准 exact manifest。

預設個人模式會在程式修改與驗證完成後，自行推送工程分支並建立／更新指向遠端預設分支的 PR；不需設定簽發服務。只有使用者明確要求 local-only／不發布時才停在本機。一般 PR merge 時，Claude Code 會顯示原生確認並列出 PR、base/head SHA 與 AIPS Required Checks 強制狀態；設定 `AIPS_ENFORCE_REQUIRED_CHECKS=1` 時才要求 AIPS 確認 required checks 通過。Gemini CLI 透過互動式 extension policy 每次要求確認。若目前任務明確授權合併，且 `gh pr merge --auto` 通過相同候選驗證，Claude Code 可啟用 GitHub auto-merge 而不再要求第二次 Claude 確認；GitHub 仍會等待 checks 與 repository policy，Gemini 仍逐次詢問。Codex Hook 仍是 advisory，無法保證攔截直接 merge 命令。直接推送保護分支、刪除分支與發行不屬於個人模式。
Claude/Gemini Hook 會遞迴分類命令參數及 unquoted heredoc 內的 `$(...)`／反引號替換，因此安全的查詢命令可留在同一次 Shell 呼叫。替換只供 AST 分析、不會由 Hook 執行；發布仍須使用明確 SHA、ref、repository 和既有核准流程。


部署管理者信任根會選擇高保證模式；此時每個 push、PR create、merge 各需獨立一次性 grant。`aips approval propose/status/verify` 提供精確提案與外部簽章驗證。完整部署、CLI 範例與安全取捨見 [Security Assurance](./SECURITY_ASSURANCE.md#runtime-policy-enforcement)。

Plan26 Phase 7 的 PR 只整理 `0.81.0` 版本與 Changelog，並為 exact-candidate readiness 留下空白 `Unreleased`；合併 PR 不會建立 tag 或 GitHub Release。

Core creative workflow changes use the normal exact-candidate Gate and selected Git publication mode; validation or matrix readiness alone does not authorize a merge into `main`.

During GitHub validation, isolated CLI fixtures receive the installed validation interpreter through `AIPS_VALIDATION_PYTHON`; its workflow contract runs before the deterministic Gate and does not grant publication or merge authority.

The required validation workflow keeps PR runs for different event actions in separate concurrency groups. Adding the Core/Large classification label therefore cannot cancel the `opened` validation run; the required `repository` check and normal branch protection remain in force.

Release tagging, dependency PR merges, and branch deletion remain separate operations with their own evidence and Human approval; a successful maintenance report cannot perform them.

Publication preflight retains its existing CLI and raw canonical hash output through the shared helper; exact-candidate and Human merge authority boundaries remain unchanged.

可用 `python scripts/repository_governance_snapshot.py --repo OWNER/REPOSITORY` 檢視 GitHub rulesets 與 branch protection；此快照唯讀，遇到不可讀設定會標示 UNKNOWN，不會替代 PR 核准或發布流程。

Scheduled maintenance summaries are evidence, not permission to change source, merge, release or delete branches. When reviewing workflow reliability, distinguish an operational error from an incomplete observation cohort; inspect the run summary and bounded artifact, and retain separate observation runs for later comparison.

Publication preflight 只檢查 exact candidate 所選的環境能力；候選未選 browser 驗證時 `NOT_REQUIRED` 不會阻擋，選用 browser 時 loopback 或瀏覽器檢查失敗仍會 fail closed。Required repository Gate 與 secret scan 維持必要條件。

CI 可依精確變更路徑略過未使用的 OpenAPI 套件安裝，但仍執行 publication-preflight lifecycle。已安裝 validator 時會跑 OpenAPI help 與 contract smoke；未安裝時會驗證 CLI 提供明確設定指引、沒有 traceback，也不會輸出不完整驗證檔。這不略過 required repository aggregate。

Pull requests may show an early advisory repository-preflight result while the required full validation continues. A fast-lane finding is diagnostic feedback and does not replace the required repository check.

Post-merge reconciliation 的實作拆分不改變既有指令、快轉安全條件或人工合併權限。

For a Large/Core change, complete documentation closure, the reviewed Core Change Test Matrix, candidate secret scanning, full repository validation, and the exact-candidate Integration Gate before publication. Create the PR with its `aips:core-change` label on the initial request. Merge into `main` only when the task requests it. AIPS Required Checks enforcement is opt-in with `AIPS_ENFORCE_REQUIRED_CHECKS=1`; GitHub native protection remains effective. Release tagging remains separate.

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

提交前可執行 `aips publish preview --base origin/main --change-class <standard|large|core>`，預覽已提交、暫存、未暫存及未追蹤檔案的文件閉包與矩陣綁定；必須先處理 `pending` 項目。`aips publish matrix-sync --base origin/main` 只更新 canonical Core Matrix 的 base/hash，更新後仍需重新檢視範圍與證據，再把矩陣標記為 READY。發布前再以 `aips publish preflight --base origin/main --head HEAD --change-class <standard|large|core> --output <report>` 執行與 CI 相同的 exact-candidate resolver。Large/Core PR 必須同步套用對應 label，並使用 `docs/qa/CORE_CHANGE_TEST_MATRIX.yaml`。受保護 `main` 由 `publish plan` 直接規劃 Pull Request，不先嘗試直推。

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

The Claude/Gemini publication guard denies only command forms that could commit or publish: read-only commands with a dynamic directory or repository option, a dynamic path to a literal non-Git executable, `gh api` GET requests, local `git lfs` subcommands and repository-defined read-only Git aliases pass, while dynamic git/gh/shell executables, dynamic `-c`/`--config-env`/`--exec-path` values, API writes, publishing LFS subcommands and aliases that expand to commit or publication still fail closed (Scenario 099). Untracked files are listed in publication diagnostics but no longer make the worktree `DIRTY`; uncommitted tracked changes still block push and PR.

純依賴升級文件豁免（Scenario 221）：`scripts/dependency_impact.py` 的 `pure_dependency_update` 只在候選 diff 的每個檔案都是允許清單內的依賴清單（`.github/workflows/*.yml`、根目錄 `requirements*.txt`、`constraints/*.txt`）、且每一組變更行都只是同一個 action 的完整 SHA 釘選更新（版本註解不得降版），或 `name==version` 的嚴格升版時，判定為 `PURE_DEPENDENCY_UPDATE`。此時 Documentation Impact、Documentation Placement 與 Documentation Sync 只豁免文件要求，並在報告列出每個依賴的分類、風險與 `human_review_required`；混入任何其他行或檔案、降版、未釘選參照、規劃路徑、超過大小上限或判定失敗，一律回到完整規則。秘密掃描、內容安全、Core Change Test Matrix、Integration Gate、必要檢查與人工合併核准都不變，`automatic_merge_authorized` 仍為 false。

發布 preflight 的 `git_identity` 只在候選 commit 的 author 欄位接受 GitHub App 機器人 noreply 格式（`<數字 ID>+<slug>[bot]`，`identity.allowed_bot_author_patterns`）；committer 與本機 `user.email` 仍只接受一般 noreply。`commit_messages` PII 掃描前，`identity.trailer_identities` 的精確 trailer 身分（目前只有 Dependabot 的 `Signed-off-by: dependabot[bot]` 與 GitHub support 位址）只在同一機器人撰寫之 commit 的最後 trailer 區塊以 `git-identity-metadata` 取代；`pii.email.v2` 不變，其他位址仍會擋下，政策格式錯誤時 fail closed，機器人身分不授予任何權限。

Profile 開關預設為嚴格（`~/.config/aips/profile.yaml` 不存在時全部使用預設值）；只能由人在互動式終端機執行 `aips profile show` 查看、`aips profile set <key> <true|false>` 切換並輸入確認片語，代理無法寫入該檔或執行 `aips profile set`。目前可切換的開關為 `claude_coauthor_trailer`（發布閘門 PII 掃描放行最後 trailer 區塊中確切的 Claude 共同作者行，其他電子郵件仍攔截）與 `post_merge_refresh`（READY 但 STALE 且任務相關主題受影響時，每個 store 每個 HEAD 最多背景執行一次 `aips intelligence refresh`），兩者預設皆為關閉，啟用後會列在 Turn Context 的 `aips_profile_non_default=`。

發布守門測試的合成掃描 fixture（`tests/test_publication_authority.py::scanner_fixture_assignment`）每次執行都把 16 個十六進位數字各放兩次後隨機排列，Shannon 熵固定為 4.0、高於 `generic-secret-assignment` 的 3.25 門檻，因此偵測結果不再隨機；原本直接使用 uuid4 hex 約有 0.7% 機率低於門檻而造成偶發失敗。掃描器規則與門檻不變。

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

A structured publication error is not evidence of a successful content-safety or Secret Scan; incomplete scans continue to block publication.

Quoted-heredoc PR text is still scanned by content safety; a secret or PII finding in it blocks the command.

Publication scan evidence 只代表完整 Secret Scan 曾對精確候選通過，不改變內容安全政策；Prepare 和最終 Integration Gate 仍會執行完整候選與歷史掃描。

The generic secret-assignment check ignores only the documented generated-password and parameterized SQL expression shapes. JSON evidence is scanned up to 8,000,000 bytes, other text up to 2,000,000 bytes, and larger inputs block publication. WebM files have no path exceptions; declared text metadata is scanned under a configurable 32 MiB default bound while media payloads are skipped.

Imported ComfyUI workflow JSON is untrusted project content and remains subject to content-safety review; schema validation does not make it trusted instructions.

Runtime Content Safety remains independent from Required Checks policy. AIPS enforces Required Checks only when `AIPS_ENFORCE_REQUIRED_CHECKS=1`; GitHub native protections remain effective either way.

Publication timeout output remains content-safe by omitting raw command and exception text; a denial remains `NOT_EXECUTED` until existing authority checks succeed.

Plan45 scanner failures use stable `SECRET_SCAN_*` codes and safe recovery guidance; unsupported literal commands are rejected before scanning and never execute. This preserves the existing fail-closed content-safety policy.

Static `.avif` files use bounded EXIF/XMP metadata inspection across staged commit, candidate/history scans, publication preview and Creative raster validation. The existing 8 MiB file and 1 MiB metadata caps apply; animated, malformed, spoofed or unsupported item structures fail closed. Diagnostics distinguish signature mismatch, unsupported features, uninspectable metadata, resource limits and malformed containers, with a safe next step for each. The parser is local and has no optional AVIF inspector dependency. Encoded image data is never decoded as text, and this check does not establish AV1 decodability or visual quality.

PostToolUseFailure 診斷只輸出 allowlist 類別與 exit code，不保存 Host 原始錯誤或命令內容。

Hook 對非預期授權例外 fail closed，僅顯示安全診斷 ID 與 allowlist 例外類別，不顯示原始例外文字。

字型檔案會先核對 TTF、OTF、WOFF 或 WOFF2 簽章、副檔名與解壓上限，再以有界解析器掃描名稱及廠商中繼資料；格式偽裝、解析錯誤、缺少套件、超限或命中 Secret／PII／Injection 都會 fail closed。這項內容檢查不授予 Git 或執行權限。

本機可用 `aips safety diagnose commit --worktree <repo> --message-file <path> [--format json|text]` 查詢 commit 安全結果。它與 Hook 共用掃描器且只讀暫存候選；拒絕摘要不含命中值，Secret／PII／Injection 仍阻擋，未知格式或掃描不完整仍拒絕。

一般程式碼中的 `run`、`data` 等名稱不再單獨觸發 Injection；commit 與 publication candidate 的 Injection 判斷依新增 diff 行與來源上下文進行，Secret 和 PII 仍掃描完整暫存檔或候選 diff。診斷會列出安全的原因、階段、規則／指紋、檔案與行號及排除步驟。模糊訊號需人工審查；核准例外僅限單一規則、檔案、指紋、sink 與期限。

Commit, pull request and release content is scanned before durable/public publication. A blocked result requires regenerating safe content; it is not silently rewritten. Runtime capability remains truthful: AIPS-owned sinks are enforced, native hooks may be tool-guarded, and unsupported host tools are advisory.

The commit guard accepts quoted-delimiter heredoc messages, literal `git add` commands joined by `&&`, `-a`/`-am` and `--amend`, and scans worktree content the commit would include; secret, PII and ambiguous injection (`REVIEW`) findings still block at commit (Scenario 169).

守衛現在放行唯讀指令與 Claude Code 標準的 commit 寫法（引號定界符 heredoc、`git add … && git commit`、`-a`、`--amend`），即將加入 commit 的內容仍會被掃描。`publish ship` 只推送已提交候選；tracked 未提交修改與 untracked 檔案留在本機並顯示為診斷資訊，不會單獨阻擋該候選。

含 Git 遠端字串（例如 scp 寫法的 `git` 服務帳號）的檔案不再因 `CONTENT_PII_BLOCKED` 被擋（規則 `pii.email.v2`）；其他 email、個人帳號的遠端與相似字元仍會阻擋，不需要也不允許用 `chr(64)` 等寫法繞過。

純依賴升級文件豁免（Scenario 221）：`scripts/dependency_impact.py` 的 `pure_dependency_update` 只在候選 diff 的每個檔案都是允許清單內的依賴清單（`.github/workflows/*.yml`、根目錄 `requirements*.txt`、`constraints/*.txt`）、且每一組變更行都只是同一個 action 的完整 SHA 釘選更新（版本註解不得降版），或 `name==version` 的嚴格升版時，判定為 `PURE_DEPENDENCY_UPDATE`。此時 Documentation Impact、Documentation Placement 與 Documentation Sync 只豁免文件要求，並在報告列出每個依賴的分類、風險與 `human_review_required`；混入任何其他行或檔案、降版、未釘選參照、規劃路徑、超過大小上限或判定失敗，一律回到完整規則。秘密掃描、內容安全、Core Change Test Matrix、Integration Gate、必要檢查與人工合併核准都不變，`automatic_merge_authorized` 仍為 false。

Dependabot commit 的機器人 noreply author 與最後一行精確的 `Signed-off-by` trailer 屬於 Git 身分 metadata，由 `config/git-publication.yaml` 決定，不是 PII 例外；`pii.email.v2` 與其他位址仍會擋下，機器人身分不授予權限。

Scenario 269 只更新 `aips intelligence gc` 的 CLI help golden vectors；內容安全偵測、sink policy 與 commit 掃描不變。

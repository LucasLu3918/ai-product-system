# AIPS 技術指南（Technology Guide）

本指南整理 AIPS 目前採用的技術與能力邊界，供需要理解系統運作方式的讀者查閱。操作步驟集中在[使用指南](USER_GUIDE.md)；Runtime、函式、CLI、設定欄位及狀態識別字保留英文，首次出現時補充中文用途。能力狀態應依 canonical 設定、程式與驗證證據判讀。


獨立審查 receipt 的 Ed25519 驗簽使用 Python `cryptography`，版本固定於驗證依賴。受信任公鑰清單由執行環境在候選 repository 外提供；未提供時不宣稱已驗證 runtime 隔離。Context、Retrieval 與 Integration Gate 的操作耗時來自實際起迄事件，不推估模型 token。

Retrieval relation candidates are built by a small standard-library module behind the established Python facade. They remain rebuildable lexical evidence and do not claim compiler-grade call resolution.

這份文件解釋 AIPS **目前採用的技術與架構選擇**。版本時間線不放在這裡。

## Runtime & Integration

OpenCode checks direct native-write targets against Project Intelligence readiness, freshness, instruction authority and project-root confinement; READY+STALE freshness is advisory for local L2 source writes only.

Scenario 266 findings remain untrusted content and do not grant Runtime Context or action authority.


Harness commit hooks route staged AVIF through the shared metadata safety scanner; native runtime enforcement remains bounded to each adapter's documented capabilities.

The creative import CLI is routed by the existing AIPS command facade. Its explicit Git destination opt-in is independent of OpenCode native permission acceptance.

The publication diagnostic contract distinguishes stable blocker reason, source phase, safe recovery, candidate/runtime binding, and independent plan, authorization, Host and execution states. Optional trace storage writes only allowlisted fields to an explicitly configured hash-chained ledger; lookup verifies the chain before returning a record.

The publication Doctor shares the structured API observer and labels the candidate branch independently from target policy, retaining bounded, sanitized endpoint and status evidence.

OpenCode's optional native acceptance records host version, platform, plugin digest and conservative runtime-source digest. It marks arbitrary Shell process effects, MCP/custom-tool effects and out-of-process writes UNSUPPORTED; missing fields in older reports remain UNVERIFIED.

The OpenCode creative adapter exposes the shared Z-Image Turbo profile and component filenames. Discovery and failure recovery remain local-only; command, runtime, model inventory, preflight and inference readiness are distinct evidence.

OpenCode V2 registers a bounded creative tool that requires explicit intent. Its `prepare` action creates versioned character/style Profiles and an unconfigured Bundle in a non-Git EPHEMERAL scope; `preflight` remains read-only and `execute` requires a ready Bundle. Existing-asset import rejects Git destinations by default; `aips creative import-candidate --allow-git-destination` provides an explicit, hash-bound create-only path to the exact Git worktree root from a non-Git EPHEMERAL source. It does not stage or commit.


### Turn-Aware Global Harness

OpenCode V2 keeps a 12,000-byte UTF-8 Context cap. Irreducible compact-projection overflow returns a stable reason, byte counts and at most three fixed section-size entries; supported native file writes deny before ordinary manifest policy evaluation. Prompts, section values and paths are excluded, and Shell/MCP effects remain outside the verified guard.

The OpenCode V2 adapter derives Context from the active Session root, caps the compact manifest at 12,000 bytes, and reports bounded hook timings without persisting prompts or file contents.

AIPS 將 Runtime/User instructions、Project rules、Project Intelligence 與 AIPS protocol 組合成 bounded context。不同 Runtime 使用各自可驗證的 integration strategy。

Adapter resolvers keep JSON/YAML results on stdout and diagnostics on stderr. Invalid adapter-state data is an explicit error; unavailable optional Intelligence subprocesses use a stable reason code and are not reported as an empty successful result.

### MCP Interoperability Gateway

MCP 提供 local stdio portable access plane，公開 Resources / Prompts / deterministic Tools。Tool-only Hosts 另以 read-only catalog/read/workflow Tools 取得相同 canonical capability context；所有 Tools 都宣告 non-destructive、idempotent、closed-world hints。Host model 負責 semantic reasoning；MCP Server 不呼叫第二個 LLM。

Cursor、Windsurf、GitHub Copilot CLI、Amp、Codex 與 generic 設定只產生 review-only payload。MCP 是新 Host 的預設接入；只有 verified per-turn hook、pre-tool guard 或 runtime-specific event source 需求才擴充 native adapter。

### Progressive Disclosure

Role、Skill、Protocol 與 Project evidence 只在 task relevant 時載入，避免把整個 system context 常駐每個 Turn。

Canonical AIPS Skills 可從 MCP Resource 按需載入，也可由 `aips skills install` 投影成 Codex、Claude Code、Gemini CLI 原生 Skills；Portable Commands 可用同一 ownership manifest 提供 Host 原生命令入口。安裝記錄 Host、scope、來源與逐檔 SHA-256；重複安裝不建立副本，移除只刪除仍吻合摘要的 AIPS-owned 檔案。投影契約與 lifecycle 測試驗證目錄、格式及所有權，不宣稱已驗證各 Host 實際載入。

## Project Understanding

The project lifecycle keeps `.ai/` opt-in and records `.ai/` plus `.ai.detached-*` in the target Git worktree's local `info/exclude`. This leaves shared `.gitignore` files untouched; ignore rules do not untrack paths already in the index.

Turn Context retains Project Intelligence freshness and refresh guidance. A READY but STALE result is advisory for confined local L2 source writes; UNKNOWN or non-READY state remains fail-closed.

Turn Context also reports the active profile line (`aips_profile=strict` by default); `aips profile show` and `aips profile set` are the only profile surfaces, and the agent cannot write the switch.

Publication diagnostics remain tied to the exact Change Impact candidate, while transient recovery repeats read-only evidence collection only.

`aips project diagnose` 的 `recovery_plan` 列出原因、步驟相依、操作種類與所需授權，保持唯讀。`aips intelligence impact-candidates --max-depth 3` 提供最多三層候選關係；同目錄 import 可解析，但動態呼叫及全域 coverage 限制仍需人工覆核。

The compact Project Intelligence Context projection remains behind the public facade; diagnostic recovery suggestions do not execute automatically.

Impact candidate discovery is exposed by the same CLI and remains report-only: source-backed imports, literal dispatch, tests and documentation references do not update canonical graph edges or coverage.


`aips project diagnose` aggregates existing Project Intelligence readiness, Runtime/Harness status and MCP static inspection. It reports safe recovery actions without invoking them.

OpenCode V2 receives the existing compact Context Manifest before model dispatch. Its readiness and path checks consume Project Intelligence output without adding a separate Role, Skill, or local-write policy engine.

Project Intelligence promotion 將候選資格與目標路徑限制拆成 helper，並由 facade 維持舊呼叫介面及人工核准邊界。

### Project Intelligence

The fixed AIPS policy layer is the bounded `SYSTEM_CORE.md`; Turn Context selects canonical orchestration pointers by task and reports route status without storing prompt text. `SYSTEM.md` remains the compatibility entry. Mutation routing fails closed when a required protocol source is missing.

Stable semantic cache 保存 Architecture、Data Flow、Modules、Contracts、Tests、Security、Operations、Source Registry 與 Impact Graph。

每回合使用 bounded layered context：衍生的 Project Core capsule、task-relevant Recall 與按需 Archive pointers。Capsule 帶 source digest 且不是 canonical truth；缺少時回退到來源指標。唯讀 `aips intelligence context-audit` 可檢查 stale hash、孤兒指標、秘密路徑及 authority conflicts。

### Canonical Project Identity

Repository lineage 與 workspace identity 分離，確保 main、feature worktree 與 AIPS-managed worktree 的 durable state 不互相誤用。

### Retrieval Intelligence

The local relation index is a disposable candidate graph. Changes to extraction semantics require an index schema bump and full re-extraction; raw source is parsed only in memory for syntax-sensitive call names, while persisted content remains redacted.

Local hybrid retrieval 組合 lexical、symbols、structural relation、tests、Impact Graph 與 Git history。Optional semantic / embedding trial 不會因存在就變成 baseline requirement。

若 Retrieval 回報 `RETRIEVAL_CACHE_WRITE_ACCESS_DENIED`，代表舊索引需要刷新但 Runtime 無法寫入 SQLite cache 或 sidecar；授予 cache 寫入能力，或為該 Runtime 設定可寫的 `XDG_CACHE_HOME` 後重試。舊索引維持 stale，不會以唯讀快照冒充 current。

### Change Impact Guard

Existing Project mutation 前先宣告並授權 Change Boundary，使用 `IMPLEMENTATION_APPROVED` 進入核准範圍；實作後對帳 actual diff 與 declared impact，只有完整記錄 reconciliation evidence 才能標記 `READY`。

## Execution

In JSON mode, failed local `prepare` and `diagnose` calls return stable, redacted errors; text output and successful schemas remain compatible.

Personal publication parses Shell words with NUL-marked expansions, so quoted literal `$` and backticks remain data while real expansions deny.

The Claude Code publication Hook fails closed immediately after retryable remote errors and provides a separate read-only Doctor command; it does not wait for Doctor inside the synchronous Hook. Prepare reports timeouts with stable, redacted diagnostics.

Creative writes in Git workspaces retain their existing Project Intelligence guard; Scenario 267's stale advisory covers ordinary local L2 source writes only.

Content-safety PASS is candidate evidence only and does not authorize PR merge or change publication mode.


Scenario 266 provides local deterministic safety evidence; it does not substitute for independent review or grant approval.


Scenario 266 binds injection review to added candidate lines while Secret/PII scanning still covers the full candidate diff.

Guard classification stays syntax-only: bashlex parses the command, quoted-delimiter `$(cat <<'EOF' …)` messages are inlined as literal words, `git add --dry-run` previews what a chained `git add` would stage, and `git config --get alias.<name>` reads alias definitions. None of these write the index, configuration or remote.


The publication preflight scans bounded AVIF EXIF/XMP metadata, while Creative raster validation accepts only structures supported by the shared registry; ComfyUI Resource Authorization remains a separate boundary.

Publication preflight diagnoses literal commands and exact candidates without executing push, PR or merge actions; unsupported forms retain their stable refusal reason with a bounded detail code.
Security-sensitive hook output is allowlisted and excludes raw command and exception text; native execution failures remain observations without retry or authority.
The existing deterministic publication planner, squash-tree proof, merged recovery and Branch Hygiene cleanup manifest remain the canonical implementations; Plan44 adds no parallel workflow.
Claude `PostToolUseFailure:Bash` reports the observed execution phase, fixed category and parsed exit code, while PreToolUse denial remains `NOT_EXECUTED`.
Creative publication diagnostics remain Git evidence and do not authorize generated assets or change character artwork workflows.
Personal publication mode remains bound to the approved task, exact candidate and required checks; detail guidance cannot authorize a merge.
Independent review remains separate from publication diagnostics, which do not establish reviewer isolation or approval.

Claude Code managed publication guard 依實際版本路由：v2.1.295+ 設定 `onFailure: block`，舊版/未知版維持相容設定並警示。

Creative import candidates bind source and destination hashes and write only an absent target; Git imports require explicit opt-in and never stage or commit.

Font assets in creative workflows use the same bounded metadata safety scanner at commit and publication boundaries; this does not add a rendering, licensing, or authorization capability.

The Git diagnostic ledger records only allowlisted publication metadata; it does not inspect creative assets, call a generator, or grant creative execution.

The Doctor observation does not retry workflow execution or execute publication commands; merge Authority re-reads the target policy before accepting required checks.

Claude Code publication denials use the native Hook response with allowlisted diagnostic fields; command input and credential-bearing provider output are excluded.

Publication recovery re-observes the exact PR HEAD and base before mutations, and never upgrades a read-only plan into authority.

Skill Explorer 是離線生成的靜態 HTML，使用原生瀏覽器搜尋、分類與複製功能。49 個 canonical AIPS Skills 經 registry 路由；38 個 Matt Pocock 原始 Skills 保留在 `external-skills/matt-pocock/` 並列出來源摘要與 disposition。31 個非 canonical ID 可由使用者選擇安裝；7 個同名項目沿用 AIPS canonical 版本。Disposition 保留為整合背景，不限制安裝。Codex 與 Claude Code 原生投影要求明確呼叫；Gemini 保留啟用前確認。`$grill-with-docs` 保持獨立且明確呼叫；瀏覽頁面本身不執行任何 Skill。

`publication_planning.py` 重用 authority、candidate/history scan 與 GitHub PR evidence，提供 read-only `prepare` / `diagnose`。指紋包含 worktree、HEAD/base、remote/PR、policy 與 PR body digest；任何漂移需重新規劃，不能用診斷代碼放行。

`publication_diagnostics.py` 提供共享的穩定錯誤分類與只讀 GitHub Doctor。`aips publish diagnose` 接受 `gh pr merge` 並重用唯一的 publication authority 驗證精確 PR 與 SHA；`aips publish doctor` 觀察 auth、repository merge methods、branch protection/ruleset visibility、PR 與 required checks。權限不足維持 `UNKNOWN_PERMISSION`／`UNAVAILABLE` 診斷；只在 `AIPS_ENFORCE_REQUIRED_CHECKS=1` 時，未知或未設定 Required Checks 才成為 Doctor blocker，strict merge 驗證對未知狀態仍 fail closed。

The local creative CLI supports `import-candidate` followed by explicit `import --accept-hash`; it rechecks source bytes and refuses existing destinations.


OpenCode's bounded Shell command policy does not sandbox arbitrary subprocess effects. Acceptance records MCP/custom-tool effects and out-of-process writes as unsupported.

創作修正重用 `creative_execution` 與 `creative_repair`：`feedback` 記錄缺陷、`repair` 複製版本化 Profiles／Bundle、`compare` 提供 hash-bound 前後對照、`quality-check` 以本地 vision 檢查整體及四個細節裁切。Pillow 12.3.0 是固定影像解碼依賴。

Ordinary generation grants permit bounded `quality-check` of manifests produced by that grant; historical/unrelated images require explicit review intent. This does not authorize regeneration, and `review-assist` retains its separate explicit-review contract. Inspect required criteria before delivery; without an installed local reviewer, report UNVERIFIED and request Human inspection.

Personal PR merge confirmation is handled by the Claude/Gemini runtime adapters and does not change Creative Bundle execution or acceptance boundaries.

Approval CLI 在既有 dispatch 中提出 high-assurance exact-operation proposal；既有 creative grant、Intelligence readiness 與 scheduler evidence 各保留原權限。Personal mode 不建立簽章授權，也不將一般 Human task authorization 描述成外部簽章。

公開 Python Facade 保留同一函式／例外物件，Discovery、Query Terms、Creative Trace 與 Asset Validation 分別處理有界掃描、查詢詞、隱私 trace 與影像容器驗證。任意 MCP／自訂工具仍不在原生檔案 Guard 的驗證範圍。

Impact candidate extraction is bounded and read-only; its source references remain unreviewed and are not execution or approval evidence.

The shared validation-path inventory classifies known roots and prefixes for both CI planners. Each planner keeps its own risk and validator-selection semantics; unknown or malformed paths continue to select full validation.

The local Creative `generate-set` executor preflights configured Bundles one at a time, records per-item outcomes, and resumes only when prior output and provenance hashes still match. OpenCode V2 receives mutation authority from native prompt admission, not Context.

`aips project diagnose` 不會啟動 Creative Bundle 或模型；創作生成仍由既有受限的明確使用者請求路徑執行。

MFLUX 固定命令表新增 Z-Image Turbo generate：`mflux-generate-z-image-turbo`。CLI 不傳任意額外參數；步數沿用明確 Bundle 設定，模型與 tokenizer 仍須預先完整安裝，本流程不下載。ComfyUI 也支援限定的 Z-Image Turbo generate profile：固定 UNETLoader、CLIPLoader (`lumina2`)、VAELoader 與 AIPS 內建 API 拓樸，preflight 逐項核對本機模型清單；不支援任意 split-loader 工作流或 edit。

本機創作支援 discover/prepare/configure/preflight/execute：設定採 allowlist 與 create-only Bundle，native Context envelope 經正規化再作使用者授權。PNG 容器檢查涵蓋 CRC、終止與 bounded decompression；JPEG/WEBP 僅作 bounded container checks，不能代替實際看圖或完整解碼。

Local creative execution supports MFLUX through fixed argv and ComfyUI through a loopback-only allowlisted workflow. It is explicit, create-only, and never downloads weights. ComfyUI model declarations live in `templates/creative/COMFYUI_MODEL_PROFILES.yaml` and may reuse only executor-reviewed topology families; profiles on the audited FLUX 3 Klein topology declare bounded sampler settings, with Base at 50 steps / CFG 3.5 and Distilled at 16 steps / CFG 1. Dynamic edit workflows can bind one to eight ordered local references, subject to per-file and aggregate size caps and per-file hash checks.

The fixed FLUX 3 Klein preflight validates `TextGenerate` fields and values against the live `/object_info/TextGenerate` schema, including the `COMFY_DYNAMICCOMBO_V3` option schema and selected API option key. The API payload sends the key (for example, `"off"`); ComfyUI reconstructs the nested value used by the node implementation. AIPS binds this check to the final serialized workflow and verifies fixed nodes and links before the single `/prompt` request. Execution failures retain bounded node ID/type, exception class and safe missing/unexpected-argument summaries; raw provider text remains suppressed. These checks do not establish successful MPS inference. Audited topology templates (`templates/creative/COMFYUI_TOPOLOGY_TEMPLATES.yaml`) describe the Z-Image and FLUX 3 Klein node graphs as data; a user-local profile may reference only one of them and can never add a node, input or endpoint (Scenario 271).

ComfyUI Bundles may opt into `workflow.mode: dynamic_local` with a project-relative API JSON workflow. The executor reads bounded `/object_info` schemas, validates graph links and required fields, permits only nodes whose runtime module identifies them as ComfyUI core nodes, and requires explicit bindings for prompt, seed, dimensions, output and any reference input. Loader model choices must exist in the corresponding local inventory. The `creative workflows scan|import|inspect` commands are read-only except import, which is project-confined and create-only. These three commands emit fixed status acknowledgements instead of node inventories, workflow bodies or provider responses; other Creative CLI actions retain their structured response contract. This is a local schema compatibility path, not a guarantee that arbitrary checkpoints or model architectures will run successfully.

Ordinary ComfyUI discovery contacts only `127.0.0.1:8188`, uses fixed bounded GET paths, reports a capped allowlisted model catalog, disables proxies and refuses redirects. Every ComfyUI request validates a literal loopback IP, explicit port, method and path before connecting. Provider errors retain only safe HTTP status and structured reason/recovery metadata. Apple Silicon reports MPS as a static candidate; FP8 is an advisory warning, and neither FP16/BF16 metadata nor an available MPS backend proves actual inference compatibility.

`templates/creative/CREATIVE_ASSET_PRESETS.yaml` supplies shared character, background, texture and UI ornament prompt guidance. The selected preset and registry hash are recorded in the execution manifest; presets do not select a provider or authorize generation.

System changes keep the exact-candidate repository Gate enabled while any selective-validation proposal remains report-only until its complete observation cohort is reviewed.

### Local character artwork

After an explicit local trial, the read-only benchmark can summarize profile-case coverage and separately record raster validity, model outcome, Human visual review and user acceptance. It does not launch a provider or validate host hook behavior.

Prompt admission counts requested outputs before generation; a short style selection may receive a fresh grant only through bounded root-bound Session state. Engine discovery distinguishes command presence, version-probe health and unverified inference, and recovery guidance never implies a fallback or download.

The optional local character-art executor accepts an already-installed MFLUX CLI or a loopback ComfyUI API workflow restricted to built-in nodes. A closed model/operation registry maps FLUX.1, FLUX.2 Klein, Qwen Image Edit 2511 and Z-Image Turbo to fixed executable arguments or the registered split-loader topology. FLUX.1 edit accepts one reference, while FLUX.2/Qwen edit commands with `--image-paths` accept up to eight bounded references. ComfyUI edit accepts one to eight ordered, explicitly bound local references and verifies each staged file against its source hash; the Z-Image Turbo profile is generate-only and checks its UNET, CLIP and VAE against the local API inventory. It disables HTTP proxying and redirects, uses offline model-hub flags, scopes create-only PNG/JPEG/WEBP output to a non-Git EPHEMERAL bundle, strips ComfyUI text metadata that can contain prompts, and records profile/workflow/input/output hashes, model revision, runtime version and license source. Preparation creates versioned fixed Profile/Bundle files without overwrite and leaves engine provenance unconfigured. Preflight does not generate; missing local engines return `BLOCKED_NO_ENGINE`. No runtime or weights are installed, and no image is sent to a cloud provider. Existing Comfy MCP guidance remains available when that user-managed route better fits the project.

Profile-driven prompt compilation includes character acceptance criteria, style constraints and an optional collection style lock; manifests keep hashes instead of compiled prompt text. Capability profiles produce advisory recommendations only. Optional visual assistance calls only an already-installed Ollama vision model over loopback and emits a separate report with no review or acceptance authority.

The pure prompt compiler and model recommendation helpers live in `scripts/creative_prompt_compiler.py`; `scripts/creative_execution.py` re-exports the same function objects for existing callers. Golden output fingerprints and facade-identity checks guard behavior-preserving extraction.

The shared helper package consolidates canonical hashes, repository-relative paths and caller-specific glob matching; existing module facades preserve current call sites and outputs.

Task-specific routes keep product-delivery, visual, security, testing, API/data, planning, documentation and publication procedures progressive; the general mutation fallback includes Orchestrator, Change Impact and Quality Planning.

`scripts/repository_governance_snapshot.py` 是選擇性、唯讀的 operator snapshot；若 `gh` 不可讀取任一設定面，結果標為 UNKNOWN。

Standalone and shadow dependency-review artifacts retain exact base/head, run ID, actual JSON findings and outcome for 90 days. Parity compares canonical findings; missing outputs, different candidates or inaccessible artifacts stay UNKNOWN. Job success alone cannot promote the shadow. Record resolved toolchain fingerprints and repeat full Gates only for new changes or unresolved failures.

CLI 發布診斷優先選擇完整 Python 3.12 驗證環境，再以既有環境診斷一次列出缺少的 yaml、ruff、mypy、Playwright、OpenAPI、JSON Schema 與 cryptography。`runtime_cache.py` 同時服務 Retrieval 與發布工具的 gh 呼叫；`package_install.py` 提供明確安裝的安全錯誤分類。CI 只快取 pip 下載，不重用整個 Gate PASS。

GitHub Actions job 的逾時依最近成功執行的 P95、明示安全倍數與向上取整方式設定；installation entrypoint 的 Unix/Linux/Windows jobs 目前採 5/10/10 分鐘，依 2026-10-06 02:53–11:34 UTC 最近十次成功執行計算。只在工作共用狀態且不會丟失必要證據時才設定 concurrency。

`validate.yml` uses a per-PR, per-event-action concurrency key. This prevents PR lifecycle events such as `opened` and `labeled` from cancelling one another while allowing a newer run of the same action to replace stale validation.

本機 Integration Gate 會先選用完整的 Python 3.12 驗證環境。文件變更的 VitePress 建置需要 Node 24+ 與既有 `node_modules/vitepress/bin/vitepress.js`；Node 不在 `PATH` 時可用 `AIPS_NODE_BINARY` 指定，預檢不會自動安裝套件或連接 registry.

產品使用安裝版 `aips openapi` 時，validator 與 `jsonschema` 是固定版本的選用相依套件。`aips openapi doctor` 檢查 managed venv，`aips openapi install` 才執行安裝；缺少套件時契約命令在呼叫 validator 前提供修復提示。

Deterministic Scheduler 可將派送 task 綁定到 AIPS worktree、runtime execution、Boundary/write set 與 renewable lease。完成時比對 lease base 到目前工作樹的實際 Git diff；過期 dirty task 需明確 recovery，未驗證的 write guard 一律維持 advisory。

本機驗證入口先確認 Python 3.12、requirements、venv 寫入位置、ruff、mypy、Playwright、localhost 與瀏覽器探測，失敗時給出對應修復命令。Publication Preview 可在 commit 前檢查工作樹文件 H2 placement 與 Matrix base/hash；正式 Gate 維持 exact-candidate 驗證。

Core、Recall 與 temporal evidence 共用硬預算；Index 開啟或查詢失敗時提供穩定診斷與修復提示，並回退至 canonical source pointers。`READY` 對帳綁定 Git base/head、乾淨且位於 head 的工作樹、實際 binary diff digest、變更路徑與宣告範圍；僅填狀態或人工提供 digest 不構成證據。

本地發布驗證可由 `bin/prepare-local-validation` 在 repository 外的暫存目錄準備 Python 3.12 venv、與 CI 相同的四份 requirements（包含 OpenAPI validator）及 Chromium；`--check-only --run --base <sha> --head <sha>` 使用同一 `--venv` 執行既有 `publish_preflight.py`，並把驗證設定放在暫存 `XDG_CONFIG_HOME`。缺少套件時錯誤會指出實際選用的 venv；文件建置另需 Node.js 與 checkout 的 VitePress 相依套件。檢索索引使用 `XDG_CACHE_HOME` 下可重建的 SQLite 快取；SQLite 唯讀連線或首次查詢因 sandbox 失敗時，沒有 live WAL 才可複製穩定來源並驗證暫時快照。無法安全讀取時先查 runtime 權限，持續失敗才重建，不改寫 canonical Intelligence。

直接執行 Publication Preflight 的 `run` 入口也會將目前 Python 執行檔所在目錄放在子程序 `PATH` 最前面，使巢狀 `python3` 呼叫沿用已檢查的驗證環境。

CI 的文件建置使用 Node 24、npm lockfile version 3 和 `npm ci --ignore-scripts`；`actions/setup-node` 以 `package-lock.json` 為快取鍵。更新 `package.json` 相依套件時需一併更新 lockfile，並驗證 `npm ci` 與 `npm run docs:build`。

驗證原始碼 checkout 時以 `./bin/aips` 呼叫本地 CLI；受限執行環境先由 `prepare-local-validation` 檢查 localhost 與瀏覽器能力，再解讀完整驗證的結果。

`prepare-local-validation --check-only --run` 會在 Gate 報告旁產生 `.timing.json`，記錄 repository validator 的模組與 lifecycle 耗時。CI 使用同一環境變數輸出報告並上傳 artifact；它是可觀測性資料，不取代任何 Gate 判定。

Temporal Change Impact 可依 Git revision 還原當時有效的 assertion 與 Impact Graph edge；canonical YAML 保留真實來源，SQLite 只作可重建的 query projection。這延伸現有 Project Intelligence，不引入外部 Graph Database。

Portable Command projections use ownership and digest checks to preserve user edits; the same Canonical Registry and renderer serve CLI and MCP without granting protected-operation authority.

### Deterministic Automation

可用固定規則完成的工作優先交給 Shell / Python / existing tooling，再把 compact structured evidence交給 model。

### Deterministic Scheduler

Planning 與 Scheduling 分離。Scheduler 根據 Task Graph dependency / boundary / state 做 deterministic dispatch。

### Execution Isolation

支援 shared、AIPS-owned Git worktree、verified sandbox。沒有可驗證 provider 時不把普通 temp directory 假裝成 sandbox。`aips isolation resolve --mode auto` 依風險選擇 worktree 或要求 sandbox；資料分類與最低隔離要求也參與 provider matching。E2B Python SDK 位於 optional `requirements-sandbox.txt`，目前只提供 synthetic smoke verifier，registry 預設停用且不接收專案檔案。

### Runtime Resource Isolation

Parallel worktree 可取得 repository-scoped TCP port lease；跨 process allocation serialized，並保留 bounded address-in-use recovery。

### Integration Gate / Janitor

The Gate can require an expected unittest count for commands whose success output includes the collected-test summary; absent or mismatched counts fail the check.

`aips publish preview` includes untracked and uncommitted paths in documentation and Core Matrix planning. `aips publish matrix-sync` resolves the current AIPS checkout or an explicit `--project-root`, updates its candidate binding and returns the matrix to DRAFT for review.

Matrix readiness checks are shared with the exact-candidate Gate: status, blockers, actual-diff reconciliation and base/hash must all pass before preview reports `READY_FOR_GATE`.

Merge candidate 依 change class 與 actual diff 執行 lint、type、test、repository validation 與 Core Change Matrix。

CI 在強制候選秘密掃描後先執行輕量 repository preflight，再安裝完整相依套件與 Chromium。Integration Gate 與 Repository Health 證據寫入 runner 的暫存目錄，再上傳為 artifact；驗證期間不會把報告檔寫入 checkout，避免證據輸出改變工作樹而誤判為不可重現。

Publication Preflight 是 Local／CI 共用的 candidate resolver，並在完整 Gate 前執行 diff-aware repository preflight。Change class 來自明確參數或 PR labels；Large/Core 只接受 canonical Matrix path。遠端保護查詢與 environment probe 只產生 evidence，不取得 publication authority。

Validation workflow 的 concurrency group 以 PR number 識別；新候選及 Core/Large 分類標籤變更會取消同 PR 進行中的舊 run，並以最新 label payload 選擇 Gate。無關標籤會跳過 Janitor，且不取消目前驗證。main push 使用分開的 ref group，可取代同 branch 舊 push。

Browser runtime 以 Playwright managed Chromium 為首選，system Chrome 透過 `AIPS_BROWSER_PROVIDER=system` 明確選用或作 auto fallback。Preflight 會執行 version 與 isolated-profile headless smoke probe；binary 存在但無法啟動時，結果是 `ENVIRONMENT_BLOCKED` 而非產品測試失敗。

Remote Git publication uses the built-in credential-free candidate scanner in strict mode. The Integration Gate binds the final-tree and commit-history scan to candidate, policy and scanner fingerprints; provider tools remain optional.

### Parallel Run Dashboard

The first dashboard implementation uses Python stdlib HTTP, static HTML/CSS/Vanilla JavaScript and polling. It has no frontend dependency chain, database, WebSocket or mutation endpoint. API output is a whitelist and excludes prompts, reasoning, raw output, secrets and raw paths.
The Retrieval Intelligence SQLite persistence boundary is `scripts/retrieval_storage.py`; the public compatibility facade remains `scripts/retrieval_intelligence.py`. The placement and documentation-sync rules map both modules to the existing Project Intelligence topic.



Plan36 publication diagnostics preserve this topic's existing behavior and authority boundaries.

純依賴升級文件豁免（Scenario 221）：`scripts/dependency_impact.py` 的 `pure_dependency_update` 只在候選 diff 的每個檔案都是允許清單內的依賴清單（`.github/workflows/*.yml`、根目錄 `requirements*.txt`、`constraints/*.txt`）、且每一組變更行都只是同一個 action 的完整 SHA 釘選更新（版本註解不得降版），或 `name==version` 的嚴格升版時，判定為 `PURE_DEPENDENCY_UPDATE`。此時 Documentation Impact、Documentation Placement 與 Documentation Sync 只豁免文件要求，並在報告列出每個依賴的分類、風險與 `human_review_required`；混入任何其他行或檔案、降版、未釘選參照、規劃路徑、超過大小上限或判定失敗，一律回到完整規則。秘密掃描、內容安全、Core Change Test Matrix、Integration Gate、必要檢查與人工合併核准都不變，`automatic_merge_authorized` 仍為 false。

Dependabot commit 的機器人 noreply author 與最後一行精確的 `Signed-off-by` trailer 屬於 Git 身分 metadata，由 `config/git-publication.yaml` 決定，不是 PII 例外；`pii.email.v2` 與其他位址仍會擋下，機器人身分不授予權限。

Scenario 269 changes Turn Context preparation wording only; creative execution, external actions and the native write guard keep their existing controls.

## Security & Governance

The only WebM exceptions are the three exact Dewhollow Gate 1 evidence paths listed in `config/secret-scan.yaml`; all other WebM paths and near-matches remain subject to strict candidate scanning.

Personal publication runs an exact-candidate and full-history scan. Only the documented generated-password and parameterized SQL forms are treated as non-literal values; provider tokens, private keys and high-entropy literals remain detectable. The content-safety conformance suite verifies that oversized or incomplete inputs block publication.

Personal PR merge keeps exact PR/head/base and mergeability validation. AIPS Required Checks enforcement is opt-in through `AIPS_ENFORCE_REQUIRED_CHECKS=1`; GitHub's own configured protection remains authoritative. Independent-review evidence is a separate check.

Remote publication errors remain denied until fresh evidence and existing authority checks pass; timeout output omits raw command and exception text.

Independent review evidence and personal publication authority remain unchanged by AVIF metadata inspection; ComfyUI resource grants remain a separate boundary.

Plan42 只擴充既有 commit 與 publication content scanner：候選字型中繼資料先經大小、簽章及格式驗證，再套用相同 Secret／PII／Injection 規則；publication approval 與 runtime permission 決策維持原有路徑。

Commit denial diagnostics stay within the existing content-safety scanner and do not alter creative-provider execution or Resource Authorization.

Unclassified publication failures map to `INTERNAL_DIAGNOSTIC_GAP` with a safe error class. Diagnostic lookup excludes raw commands and provider output, never creates a default ledger, and cannot authorize or execute publication.

`branch.protected` is cross-checked with classic protection and effective rules; unknown permission evidence blocks and carries sanitized source/status metadata.

The read-only `aips publish doctor` uses the shared structured GitHub API observer, distinguishes candidate/source and target policy branches, and reports bounded sanitized response metadata. `governance_guard` returns safe diagnostic identifiers and fields in Claude Code PreToolUse denials.

Git publication 使用 bashlex shell AST 與 cryptography Ed25519。預設 personal mode 以共用 Hook 驗證內容、乾淨候選、工程分支與明確操作；一般 PR merge 要求 Claude 原生 `ask` 或 Gemini interactive `ask_user`、精確 head SHA、預設 base 與 passing required checks。明確 task-authorized 的 `gh pr merge --auto` 經相同候選驗證後可由 Claude 啟用 GitHub auto-merge，不再要求第二次 Claude 確認；Gemini 仍要求 `ask_user`，GitHub 仍套用 checks 與 repository policy。Gemini policy 涵蓋 default/autoEdit/yolo；Codex hook 維持 ADVISORY 且不能保證攔截直接 merge。安裝固定的 root-owned trust config 會啟用 high-assurance mode，並要求外部 HTTPS issuer 與 transactional single-use ledger。fixture 簽章只驗證高保證協定。Git push 的 server lease 與 GH head pin/base preexecution observation 分別記錄於 scope。

`feat/` is an accepted engineering branch prefix. `--auto-merge` requests GitHub auto-merge only after AIPS confirms a non-empty passing required-check set; exact head binding and native Human authorization remain required.

The publication parser recursively classifies command substitutions in arguments and unquoted heredoc bodies without executing them. Quoted/escaped text remains literal; dynamic executable, subcommand and Git context values still fail closed. Explicit SHA/ref/repository binding and publication approvals remain required.

Creative traces omit prompts, local absolute paths, image bytes, credentials, and workflow bodies; the configured ComfyUI adapter disables proxies and redirects.

GitHub governance snapshot 只呼叫讀取 API，輸出完整設定證據與穩定 fingerprint，不具設定修改或發布權限。

### Security Assurance Level

SAL 0–4 依 product baseline 與 current change boundary 決定 assurance 強度。

### Secret Handling

Credentials 只能來自安全 runtime source；不進 Git、Prompt、logs、Project Intelligence 或 ordinary evidence。


### Resource-Scoped Authorization

Agent mutation 只在 approved resource boundary 中有效；default deny 與 evidence binding 不等於 Human decision。

### Enforceable Governance

Malformed hook envelopes fail closed with the adapter-specific denial response. Broad exception handling at enforcement boundaries records the exception chain to stderr and returns a sanitized failure; it never converts an enforcement failure into an allow decision.

可驗證 native Runtime hooks 可以在 protected operation 前檢查 approval binding；MCP-only 不宣稱攔截 Host native tools。

Runtime Policy Enforcement uses a versioned action envelope and deny-by-default policy. Claude/Gemini hooks are `TOOL_GUARDED` only for normalized actions they receive; Codex remains `ADVISORY`, and high-risk external egress additionally requires a verified sandbox boundary.

### Governance Audit Evidence

Hash chain、portable audit bundle、external anchor、key fingerprint 與 retention catalog提供可驗證 provenance；不創造 approval authority。

Content-safety detector changes are versioned (for example `pii.email.v2`) and bound to Scenario 266 with a fixed corpus; they never add a PII exception path.

## Quality & Verification

Scenario 261 regression coverage checks JSON and text error paths while preserving exit status and publication authority.

Scenario 261 regression coverage includes quoted-heredoc PR bodies and content-safety scanning of the exact heredoc text.

The Creative lifecycle test uses synthetic local providers to verify Base/Distilled profile settings and one-to-eight ordered staged-reference bindings. It does not certify real inference, image quality, independent review or user acceptance.

Scenario 263 records the three exact Dewhollow WebM evidence-path exceptions and regression coverage that keeps near-matches and other WebM files under strict scanning.

Skill Explorer 的文件映射不影響 Creative runtime；本次增加的 FLUX 3 Klein 驗證只涵蓋 live `TextGenerate` schema 與最終 payload 相容性，MPS 推論仍未驗證。

The `creative workflows scan|import|inspect` routes are an explicit CLI contract; they do not modify the Skills CLI or Skill Explorer catalog.

Creative lifecycle evidence includes fixed ComfyUI model profile families, local component inventory checks and rejection of unreviewed topology families.


Scenario 044 verifies the attach/detach ignore contract; it does not alter Skill Explorer routing or native Skill installation behavior.

Scenario 097/260 cover the strict opt-in Required Checks behavior and read-only Doctor contract; AIPS enforcement is controlled by `AIPS_ENFORCE_REQUIRED_CHECKS=1`.

Scenario 260/261 and the Core Change Matrix verify no inline Hook Doctor call, timeout redaction, and exact-candidate publication recovery.

Scenario 267 lifecycle evidence checks the READY+STALE allow case and the retained independent denials.

Scenario 266 records content-safety verification while preserving existing maintenance and publication authority boundaries.


Content-safety controls remain separate from skill discovery, installation, and author trust decisions.


Publication command-form and scanner recovery behavior is covered by the exact candidate Core Matrix and Scenario 261; it does not change the Skill Explorer contract or publication authority.

The Matt Pocock Skill Explorer lifecycle remains independent of the AVIF media-format registry and its security checks.

Scenario 259 and the Matt Pocock Skill Explorer inventory remain unchanged; Scenario 261 verifies command detail codes and bounded native failure observations.

Scenario 261 驗證 Claude Code 版本路由、Hook fail-closed 與診斷內容的隱私邊界。

Scenario 264 verifies the creative import CLI and create-only lifecycle, including unchanged Git index bytes. Skill Explorer checks remain separate even though both lifecycle contracts share an evidence runner.

The commit-safety lifecycle is registered with repository validation; its read-only CLI cannot substitute for publication or independent-review checks.


Scenario 261 verifies publication diagnostic CLI and Hook fields separately from Skill Explorer generation and upstream Skill routing; no Skill inventory or default routing behavior changes.

Creative error envelopes use bounded diagnostics and stable recovery codes. ComfyUI tests use loopback fixtures; static MPS and dtype metadata never count as inference evidence. The User Guide's upstream Skill commands and Scenario 259 remain backed by the canonical registry and ownership-safe projection lifecycle.

Publication diagnostics contract tests preserve GitHub's successful skipped-check outcome separately from AIPS's stricter blocked decision.

The exact-candidate matrix checks policy-branch selection, HTTP error classes, safe Hook diagnostics and read-only retry classification.

Required Checks classify an empty result as UNCONFIGURED only when protection is independently confirmed empty; an unknown policy stays blocked and cannot be inferred from passing optional CI.

Upstream Skill projections are validated by the isolated `skills_cli_lifecycle.py` evidence: all non-canonical records are installable, canonical IDs are skipped, ownership is source-scoped across Hosts, and modified or unowned files survive uninstall. Codex and Claude invocation controls are projected from native metadata. This fixture validates local lifecycle behavior; it does not claim live Agent discovery.

CLI lifecycle coverage includes Publication Doctor's stable diagnostics and confirms that documentation or Skill discovery never grants merge authority.

`aips skills list` reads canonical Skill frontmatter through the read-only Skill index, supports exact capability and trigger filters, and emits text or JSON. Its lifecycle evidence covers listing, filters, output, invalid arguments and empty results without changing the generated index.

Scenario 233 also verifies native Skill and Portable Command projection contracts for Codex, Claude Code and Gemini CLI, including ownership-safe uninstall. These deterministic checks cover generated paths and files, not live Host discovery or invocation.

The Skill Explorer is a static generated artifact from the canonical Skill registry and pinned source dispositions. Its deterministic validator checks inventory and routing metadata; it does not claim semantic model quality.

The catalog contract verifies all 49 canonical Skills, all 38 vendored source paths and SHA-256 entrypoint digests, the 31/7 upstream installability split, overlap-based dispositions, and trigger-backed automatic routes. `$grill-with-docs` remains explicit-only in its native projection.

`publication_planning.py` 重用 authority、candidate/history scan 與 GitHub PR evidence，提供 read-only `prepare` / `diagnose`。指紋包含 worktree、HEAD/base、remote/PR、policy 與 PR body digest；任何漂移需重新規劃，不能用診斷代碼放行。

Claude Code publication Hook 使用八秒 hard deadline，結構化拒絕會記錄安全 phase 與 elapsed milliseconds。Prepare 完整掃描通過後，最多 30 分鐘的非授權 scan evidence 存在 private user cache，綁定 repository/worktree、base/head、push target、remote tip、diff、scanner 與 policy digest；Hook 每次重驗 live Git/remote state，並對缺少、過期、毀損或漂移 evidence fail closed。完整 candidate/history scan 仍是 Prepare 與 Integration Gate 必要步驟。

The OpenCode integration lifecycle exercises candidate tampering, source drift, path and symlink rejection, destination races, cache privacy, and end-to-end CLI dispatch.


OpenCode host acceptance verifies runtime integration only; it does not measure generated-image quality, production model quality or real-task outcomes.

Stable release readiness is an exact-candidate, read-only decision. Scenario 214 covers stable install, main-channel fast-forward, and unchanged installed state after a divergent update is rejected; creating a release tag remains a separate approval.

Large/Core candidate validation binds its test evidence and documentation closure to the exact diff in the Core Change Matrix. The read-only branch lifecycle report is a maintenance signal; it does not replace exact-candidate publication checks or authorize a Git mutation.

創作修正重用 `creative_execution` 與 `creative_repair`：`feedback` 記錄缺陷、`repair` 複製版本化 Profiles／Bundle、`compare` 提供 hash-bound 前後對照、`quality-check` 以本地 vision 檢查整體及四個細節裁切。Pillow 12.3.0 是固定影像解碼依賴。

Canonical Skill frontmatter defines routing metadata and the generated version 1 skills/INDEX.yaml remains the consumer view. Skills load only when relevant. Scenarios 241–256 are manual semantic expectations; the Skill Index lifecycle separately checks deterministic metadata generation and compatibility. The additions use existing Capabilities, and the browser-game reference keeps DOM/SVG implementation detail out of global Skill metadata.

Repository validation and the exact-candidate Integration Gate establish candidate fitness. Personal publication permits guarded engineering-branch push and PR creation, plus ordinary per-call confirmed PR merge through Claude Code and Gemini CLI native controls after exact head/default-base and required-check validation. A task-authorized Claude `--auto` merge uses the same guard and lets GitHub complete after policy/checks pass; Gemini still asks. Codex remains advisory.


Publication Core candidate 執行完整 repository／secret／docs Gate 與 signed-grant regression。Synthetic issuer、review 或 creative lifecycle evidence 不建立 production signing trust root。

The shared Python bootstrap preserves optional constraints on macOS Bash 3.2 by prepending them to its non-empty requirements argument array. Its lifecycle executes the actual shell body for constrained/unconstrained inputs, exact argument quoting and fail-closed empty requirements.

以觀察到的數值計算 P50／P95，缺值維持 UNKNOWN。OpenCode 驗收綁定 Host 版本、平台與 Plugin／驗收程式雜湊；Agent 任務完成、人工修正與誤判另行記錄，不能從 rubric PASS 推算。Creative trial 先核對本地影像與雜湊，再呈現人工角色、服裝、構圖、編輯與恢復評分。

Impact candidate checks preserve source provenance, report budget truncation and unresolved dynamic relationships, and prove canonical graph state and global coverage remain unchanged.

Creative visual assistance writes a separate advisory report; its findings do not replace independent Human review, user acceptance, or measured real-model quality evidence.

CI 在 tested constraints 下安裝四份驗證 requirements 的完整 Python 套件，供必要 repository lifecycle fixtures 使用。精確候選計畫可以省略 Node、文件建置及 Chromium 執行環境；候選秘密掃描、repository validation 與 Integration Gate 仍是必要檢查。沒有模組基準時，coverage 僅供報告。

`validate.yml` scopes concurrency to a PR and event action. Distinct `opened` and classification `labeled` runs remain independent, while a newer run for the same action can replace stale validation.

The current Ruff baseline is 687 findings. Zero-finding modules use a terminal zero budget. Coverage remains report-only: the bounded Project Intelligence relation-candidate lifecycle records 45.5% combined statement-and-branch coverage for its helper module; it does not imply repository-wide coverage or establish a minimum.

When isolated validation fixtures need the optional Python modules, the workflow passes the provisioned interpreter through `AIPS_VALIDATION_PYTHON` before running the deterministic Gate; a workflow contract protects this handoff.

The Core Creative verification path covers native prompt admission and revocation, bounded multi-item recovery, local-only engine probes, documentation closure and the exact committed candidate.

`aips project diagnose <path>` 聚合既有只讀檢查，Lifecycle evidence 驗證 text/YAML/JSON、隱私遮蔽、失敗情境與不寫入行為。這份診斷不取代各 subsystem 的權威檢查或精確候選 Gate。

創作驗證分別記錄命令盤點、合成 tool/provider 測試、native host 驗證及真實模型推論。未提供權重時，品質／設備效能維持未驗證，不以流程通過推定改善成效。

Creative quality benchmark v2 使用 prompt-free、三種角色 archetype × 六種案例資料集，逐 profile-case 顯示 coverage，並分開彙總 model、check、compiler 失敗。輸出 raster 必須是專案內有效檔案且 SHA-256 相符。Human 視覺評分、user acceptance、runtime attestation 各自獨立；版本 1 證據保留讀取相容性，但不提供 dataset coverage。Fixture 只驗證資料契約，不證明生成品質或真實模型成功率。

Creative lifecycle checks use synthetic engines and loopback fixtures; they verify command contracts and confinement, not model quality, hardware performance or visual fidelity.

Scenario 236 and the creative lifecycle verify provider boundaries, provenance, rollback, trace privacy, and pending human review; synthetic output does not establish visual quality.

OpenCode validation separates install and discovery from Session Context delivery and permission-hook execution; claims remain limited to the tested host and version.

OpenCode Adapter 使用 ownership digest、安全路徑檢查與原子寫入管理全域 AGENTS、canonical Skills、Commands 及 V2 plugin。V2 plugin 在 primary dispatch 注入 compact Turn Context，permission hook 檢查受支援的直接檔案資源，Shell 限制為 bounded read-only allowlist。L1 允許非 Git workspace 的 confined 新 creative asset；L2 要求 Project Intelligence READY/CURRENT；L3 外部動作沿用 Human approval。獨立的 creative import CLI 預設拒絕 Git 目的地；顯式 opt-in 只允許雜湊綁定、由非 Git EPHEMERAL 來源寫入精確 Git worktree root，且不會 stage 或 commit。Lifecycle 涵蓋版本、重裝、衝突、漂移、損壞 manifest、symlink、中斷恢復與解除。Plugin discovery 已由 OpenCode 2.0.24 registry 驗證；模型 Context delivery 與 permission action 尚未驗證，Governance 維持 ADVISORY，MCP/custom tools 和 out-of-process writes 不在 guard 範圍。OpenCode 是目前唯一會安裝 AIPS 原生 Skill 投影的 Host；其他 Host 透過 MCP Resource 或按需讀取 canonical source 載入，並依 ownership 記錄與摘要比對安全移除。

必要的 repository lifecycle 會在隔離 fixture 中重新解析完整 Python 3.12 環境，所以 CI 固定安裝四份驗證 requirements，包含 Playwright 與 OpenAPI Python 模組。精準路徑計畫仍控制 Node 設定、Chromium 下載及可選 OpenAPI evidence；`ci_validation_plan_contracts.py` 另驗證文件變更也不可省略 Python 套件，並拒絕條件安裝、漏裝及無條件下載 Chromium 的回歸。

Shared deterministic helpers live in `scripts/aips_common/`; existing consumers keep compatibility facades. Golden lifecycle evidence pins raw/prefixed digest bytes and the distinct path/glob normalization modes. A separate focused pytest workflow checks those contracts without changing the required repository Gate. This refactor does not establish complete caller/consumer graph coverage.

Scenario 231 adds a weekly/manual, pinned OSV dependency inventory and nonblocking full-history Gitleaks comparison with the existing project scanner. These observations do not replace the exact-candidate required secret scan or repository Gate; repository-wide Impact Graph coverage remains partial.

Scenario 230 and the exact-candidate Core Matrix cover route selection, hook/manifest compatibility, missing-source behavior, fixed-core byte ceiling and measured reduction against the base layer.

Skill 路由 metadata 以 `SKILL.md` frontmatter 為唯一來源；修改後執行 `python scripts/skill_index.py --write`，預設不帶旗標只檢查 drift。tier 欄位仍保留供既有 consumers 使用，不會自動降低主要模型。REST／visual 執行細節按需載入既有 orchestration protocol。

品質債務 ratchet 追蹤 Ruff 與 mypy 基線，修改大型 facade 時要求債務下降；coverage 目前仍為 report-only。

Plan19 將 quality budgets 綁定每個模組，讓 touched-code findings 不增加；coverage 只回報 direct coverage baseline。Capability Registry 生成相容的 surface inventory 與 Capability Map；Agent Eval freshness 依行為依賴列出 stale cases，不會自動執行 Eval。

Plan17 regression evidence covers numeric diff headers, four browser/OpenAPI combinations, mandatory aggregates, reusable caller keys/permissions, explicit Python and isolated children, recursive placement, signed identity/immutable proposal rejection and atomic deletion races. Missing or malformed capability plans retain the full profile. A latest cancelled check stays INCOMPLETE; replaced old checks are reported as SUPERSEDED.

Shared Python workflow bootstrap accepts an explicit import profile, checks imports and runs `pip check` under the repository tested constraints.

Repository Health has a provisional ten-minute job limit from three successful 14–19-second samples. Monthly reliability queues up to 100 same-cohort Issue updates, uses the shared composite bootstrap, and has no guessed timeout before a successful duration is observed. Evolution Effectiveness uses the same 100-entry, non-cancelling queue for same-period Issue reconciliation. Validation Observation retains its 15-minute limit and preserves each run as separate evidence.

Pull requests receive an early repository-preflight summary from a separate bounded job. The result is advisory and the complete required repository validation still runs independently.

The repository validator derives optional evidence from the exact-candidate CI plan. OpenAPI-dependent lifecycle checks, including implementation enforcement, are skipped only when `needs_openapi` is false; without a valid plan the full profile runs. `tests/validation/mcp_interoperability_contracts.py` selects the full Node, browser and OpenAPI toolchain because required repository lifecycle preflight checks need those dependencies. The required `publish_preflight_lifecycle.py` evidence still runs in either case: action-level OpenAPI help and validation smoke require both optional modules, while the missing-module path checks top-level help and a deterministic fail-closed diagnostic. The plan is not inherited by isolated contract and lifecycle subprocesses. The required repository aggregate, secret scan and Integration Gate remain blocking.

Dependency update planning uses `config/dependency-policy.yaml` and `scripts/dependency_impact.py`. `plan` recommends class-specific validation; semantic runtime changes include retrieval regression and a semantic trial, while unknown packages require human review. It is advisory and grants no automatic merge authority.

`scripts/document_size_audit.py` reports tracked documentation and evidence file sizes; items above 50,000 bytes receive non-blocking `WARN` status. The report does not alter or archive files.

CLI architecture: `bin/aips` resolves the checkout and forwards all arguments to the thin `scripts/aips_cli.sh` facade. The facade resolves its own checkout and loads implementation modules from `scripts/aips_cli/` before dispatch, preserving installed-symlink and source-checkout behavior independent of the caller working directory. Publication policy helpers in `scripts/publish_preflight_policy.py` are deterministic and receive the repository root explicitly; `scripts/publish_preflight.py` owns environment probes, Git reads, candidate evaluation, and CLI output. Repository validation imports the registered validator modules through `tests/validation/registry.py` in a declared order.

The existing `evolution_analysis.py` CLI is a compatibility facade; deterministic local pre-analysis is implemented in `evolution_preanalysis.py` with the same outputs and authority boundaries.

Post-merge publication reconciliation uses the existing Python/Git runtime behind the `publish_preflight` facade; extracting it adds no dependency or public command.

Scenario 204 的 module-extraction evidence 會檢查 Project Intelligence temporal adapter 仍由原 facade 暴露，並固定 current-mode 欄位與 digest 格式。

Validation quality improves gradually: a Ruff baseline blocks debt growth, mypy remains scoped to selected modules, Coverage.py reports branch evidence without a premature percentage gate, and deterministic Hypothesis properties cover stable SemVer selection. The read-only Validation Observation Collector installs its pinned PyYAML dependency before collecting the shadow cohort; full validation remains mandatory while that cohort is assembled. Its graduation report measures validator-level run/skip precision, recall and false-negative rate, preserving null when a denominator is empty. Missing run-to-PR links are recovered through exact-SHA lookup only when one same-repository PR matches. The collector uses a provisional 15-minute timeout from a two-run, 31-second timing sample; this is a conservative bound, not a reliable P95. It has no concurrency group because pending scheduled or manual evidence must not be replaced.

The Validation Taxonomy audit keeps shadow selection and graduation class/path declarations aligned and reports drift without editing either policy.

The repository required-files policy has a versioned parallel manifest at `config/repository-contract.yaml`. Strict parsing and lifecycle fixtures compare its required path set and missing-file findings with `tests/validation/static_contracts.py`; the existing Python list remains authoritative during the parity pilot.

The repository validator imports browser-dependent visual and creative render validators only when the exact-candidate plan requires a browser. A missing or invalid plan keeps the full profile; a planned skip is explicit lifecycle evidence and does not remove the repository aggregate.
Offline Evolution precision and recall use explicit Human relevance labels; missing labels remain `NOT_READY` and never change source-selection policy.

Managed AIPS CLI requires Python >=3.12. The required PR Gate tests Python 3.12; a weekly compatibility smoke workflow exercises 3.12, 3.13, and 3.14 from `config/system-facts.yaml`. An explicit `AIPS_PYTHON` must satisfy the floor; doctor identifies an unsupported managed environment, and install/update repair recreates only an AIPS-owned venv.

Runtime adapter discovery prefers an available CLI and then an explicit runtime-path fallback. Shell `PATH` integration remains opt-in and ownership-marked. `aips doctor`, `aips shell status`, `aips harness status`, and `aips harness doctor` report CLI, shell, runtime-dependency, and Harness state; a plain source checkout does not create a venv implicitly.
Monthly Effectiveness requires complete pre-analysis coverage before treating source shortlist yield as known. Oversized GitHub Issue content uses a bounded zlib/Base64 envelope with a SHA-256 digest; consumers restore the complete body before parsing. Corrupt and over-limit archives remain unavailable evidence.


The maintenance plane separates Evolution pipeline completeness from content value, publishes validator-scope shadow/replay without skipping checks, and binds branch cleanup proposals to exact branch/main/merged-PR evidence. Version-tag readiness and GitHub ruleset comparison are read-only; each protected operation still uses its separate approval path.

Runtime Context 由 `scripts/runtime_context.py` 統一解析驗證 Python 與 runtime 路徑；Runtime invariant matrix 會驗證宣告維度的完整值對覆蓋。

Publication CLI 的 help 不啟動完整驗證。docs impact 與 publication 共用 active-checkout routing；OpenAPI CLI 則呼叫安裝版工具並明確傳入 product root。驗證環境會核對 Python 3.12 的 venv prefix，保留原本 GitHub 設定位置，並把設定位置未確認與網路／依賴／localhost／browser 阻擋分開呈現。

Publication routing uses an explicit project root or the current AIPS Git checkout; the selected validation Python also serves Intelligence commands. Label-only aggregates require matching prior full Janitor success via actions-read metadata and candidate-bound run titles. CI reports documentation precheck failures, Gate duration and the slowest ten repository checks in Step Summaries. setup-node v7 uses Node 24 and Pages artifact v5 delegates to artifact v7 on Ubuntu 24.04. Existing npm caches and check-only prepared environments reduce installation work while PR/main validation stays complete.

When a validation contract executes a Python helper directly, that invocation also checks syntax; retain separate compilation only for files not executed by that validation path.

Repository validation assigns each lifecycle to one owner module so the same fixture is not started twice. `runtime_contracts` owns `intelligence_context_lifecycle.py`; the MCP lifecycle owns all six advertised client configuration checks, including JSON shape and no-automatic-change assertions.

Phase 4 的 generator adapter 以 `scripts/openapi_generator_adapter.py` 在本機明確執行；Profile 必須引用 canonical OpenAPI Phase 2 evidence，並固定本地 executable digest、version、argv、輸入與輸出 allowlist。預覽預設不執行工具，Gate 只驗證 fixture。成功後由 Profile ownership 與 Phase 3 generation records 綁定輸入、工具版本和輸出雜湊；這是可追溯性證據，仍需專案原生測試確認 client 行為。

Phase 5 可讓 Phase 3 inspector 核對 Phase 4 的未追蹤執行報告，並以 `examples/openapi-client-pilot/` 的 Widgets 案例驗證一條可重現的本機 API/client 流程。該案例使用受限的專案本地 generator，並不指定所有產品的語言或工具；每個真實產品仍由自己的契約和整合測試負責驗收。

REST/OpenAPI evidence uses optional pinned dependencies from `requirements-openapi.txt` and `scripts/openapi_contracts.py` for offline specification validation, repository-local reference checks, conservative compatibility classification, project-native JUnit coverage and revision freshness. Contract commands run without a shell and retain output digests rather than raw streams. Unknown changes and stale reports never qualify as PASS; operation-name coverage does not establish assertion quality.

Phase 3 uses `scripts/implementation_enforcement.py` and `templates/implementation/IMPLEMENTATION_ENFORCEMENT_REPORT.schema.json` for an exact-candidate, versioned evidence report. It reuses Python, PyYAML and JSON Schema dependencies already needed by repository validation. Explicit `run-command` collection uses argv, a declared timeout, a minimal environment and at most 1 MiB of hashed output; the Integration Gate calls inspection only. Command reports are current-run artifacts and must not be committed as proof of a later revision.

Publication Preflight reports the script root and Git root, checks Python/Ruff and only the loopback/browser capabilities selected by the exact-candidate plan before expensive Gate work, and runs changed-Markdown link checks plus a VitePress build for documentation candidates. VitePress normally resolves from the checkout; `AIPS_VITEPRESS_NODE_MODULES` may select an absolute external dependency directory, whose installed version must equal the candidate `package-lock.json` pin. In external mode, the build uses a temporary Node ESM resolver for package imports from candidate documentation configuration and removes it after the build. This keeps a clean candidate free of local dependency files and performs no install or registry access. An unselected browser check returns `NOT_REQUIRED` without blocking; a selected probe still fails closed. `--project-root <repo>` binds an installed CLI to another source checkout. Post-merge reconciliation runs the installed script against that checkout so a stale target script cannot block a safe fast-forward; other candidate calculations run from the selected checkout.

`scripts/publication_transfer.py` adds a read-only GitHub API transfer boundary. `prepare` derives the exact changed Git blob identities and final tree from one clean local candidate commit, and checks the explicit destination against `origin`. `verify` compares a receipt of GitHub-created blob and tree SHAs with that same local candidate before any commit or ref mutation. It returns `BLOCKED` on missing, truncated, stale or mismatched identities and never contacts GitHub or updates refs itself. The existing strict candidate-history scanner remains the publication content gate.

### OpenTelemetry run export

`aips telemetry record` appends bounded lifecycle metadata to existing run events. `aips telemetry export --output` builds a deterministic offline OTLP/HTTP JSON projection; `aips telemetry replay --config <yaml> --send` transmits only when the supplied config explicitly enables export. Remote endpoints require HTTPS and the optional authorization value comes from a host environment variable. Prompt, output, tool arguments, private reasoning and credentials are excluded. Unpaired lifecycle evidence is reported as `TELEMETRY_DEGRADED`; it does not alter AIPS execution or Gate results. GenAI fields follow the immutable snapshot recorded in `orchestration/schemas/telemetry-export.yaml`. Scenario 181 verifies this boundary and does not replace deterministic validation or review evidence.

已處置的 Change Impact unknown 必須同時保留原始描述、處置決定、可驗證的 repo 內檔案或 traversal evidence，以及 Human review。Legacy string unknown、Open disposition、失效 digest 或不匹配的 seed scope 都維持 fail closed；seed-scoped evidence 不改變 repository-wide coverage。

Independent-review task, packet and evidence contracts are implemented as an opt-in capability. PR enforcement is currently disabled in the active Core Change Matrix because no trusted runtime-attestation verifier is connected; setting `review_evidence.required: true` without one remains fail-closed.

Change Impact traversal 使用本地可重建索引與 canonical Impact Graph，並以 depth/node/edge budgets 限制成本。動態關係、索引失效、圖涵蓋不足與截斷必須輸出為不確定狀態；不要把 lexical candidates 當成編譯器解析或完整性證明。

Validation workflow 先執行輕量文件影響檢查，再安裝完整依賴與 Playwright；EARS validator-only 變更使用 Scenario Conformance 閉包，規劃功能與範本變更維持完整 Requirement Planning 閉包。

Public command, platform, runtime, optional-dependency, validation and documentation facts are registered in `config/system-facts.yaml`; capability surfaces remain in `config/architecture-surfaces.yaml`. `scripts/system_facts.py` deterministically derives factual tables in System Reference while policy and explanatory prose stay in canonical topic documents. `pyproject.toml` records Ruff/mypy and Python compatibility; `constraints/tested.txt` identifies the exact repository-validation dependency set used by CI.

Repository validation classifies exact candidate paths before provisioning optional Node, browser and OpenAPI toolchains. Unknown paths use the complete toolchain. The Integration Gate, mandatory secret scan and repository validation remain required for every candidate.

Branch hygiene emits deterministic SHA, PR, age and integration proposals; cleanup requires an exact one-time manifest whose main baseline matches the current target. Any absent row blocks the complete batch as replay or partial-state evidence; a mid-run remote failure reports completed deletions and requires a newly reviewed manifest before retry. CI selects optional Node, browser and OpenAPI toolchains from exact changed paths and fails closed to the full profile on unknown input.

Eval-as-CI / Trajectory Quality Gate 以 provider-neutral trace 產生 observable evidence。Deterministic violations 可形成 `BLOCK`，效率偏差形成 `WARN` 或 `DEGRADED`；shadow mode 不授予 Git Publish 權限，Human Authority 仍是最後決策者。

### Scenario Conformance

Scenario 261 now also covers explicit publication error classification, safe Prepare/Hook binding, lifecycle-state separation, and optional verified Diagnostic ID lookup. These deterministic checks do not claim live Host confirmation or publication execution.

Scenario registry 將 evidence 分成 deterministic、lifecycle、agent_eval、manual，不用「檔案存在」冒充 automated coverage。

### Agent Evaluation

外部 Eval adapter 位於 `scripts/eval_interop.py`，使用無第三方框架 runtime 依賴的 bounded parser；Promptfoo static subset、PyRIT versioned bridge、risk profiles 與 finding promotion 都沿用 Agent Eval Case/Result 和既有 Gate authority。輸入格式與限制見 `orchestration/EVAL_INTEROPERABILITY.md`。

需要 semantic judgment 的 case 使用 provider-neutral observable-result contract，不保存 private reasoning。

Real-task outcome comparisons reuse current, case-bound Agent Eval observations, shadow Trajectory Eval evidence, and genuinely observed telemetry. The fixed-cohort protocol keeps success, rework, security, and missing/failed runs separate; absent baseline or candidate evidence remains `NOT_READY`/`UNKNOWN`. See [Scenario 229 — Agent Eval Freshness Selection](./CONFORMANCE.md#scenario-229-agent-eval-freshness-selection).

### Repository Health

Architecture Surface、documentation mapping、validation contract 與 drift evidence用 deterministic audit 檢查。

Documentation audience 掃描忽略 Git 已明確忽略的本機 metadata；未被忽略的未知 docs-root entry 仍 fail closed。

獨立程式碼審查以 `SELF_CHECK` 與 `INDEPENDENT_REVIEW` 分開建模。Scheduler 建立唯讀隔離任務；review packet 以 allowlist、大小／路徑限制和檔案指紋固定審查輸入。Evidence 必須綁定精確 base/head、packet 與不同 execution ID，並由可信 runtime attestation verifier 驗證。沒有可用 verifier 時維持 `UNVERIFIED`，必要審查在 Integration Gate fail closed；靜態結構檢查不能冒充簽章驗證或語意判斷。
Publication Preflight 的 lifecycle evidence 固定 Python module probe，再分別模擬 loopback 與 browser blocker，讓環境診斷測試不依賴主機是否安裝 optional modules。

The observation collector reports readiness separately from collection health: `NOT_READY` succeeds as evidence collection, while API/artifact failures, absent reports and unknown states fail. Dependency Review shadow runs alongside full validation but does not change the required result; promotion requires same-candidate parity and separate review.

- Release-readiness changes require lifecycle cases for an empty, non-empty, missing, duplicated, malformed, and unavailable Unreleased section.

The publication doctor normalizes branch existence, effective GitHub rules, classic protection, ruleset, and worktree evidence into phase-specific diagnostics. Its JSON remains observational and keeps Human and native-host authority outside the diagnostic result.

純依賴升級文件豁免（Scenario 221）：`scripts/dependency_impact.py` 的 `pure_dependency_update` 只在候選 diff 的每個檔案都是允許清單內的依賴清單（`.github/workflows/*.yml`、根目錄 `requirements*.txt`、`constraints/*.txt`）、且每一組變更行都只是同一個 action 的完整 SHA 釘選更新（版本註解不得降版），或 `name==version` 的嚴格升版時，判定為 `PURE_DEPENDENCY_UPDATE`。此時 Documentation Impact、Documentation Placement 與 Documentation Sync 只豁免文件要求，並在報告列出每個依賴的分類、風險與 `human_review_required`；混入任何其他行或檔案、降版、未釘選參照、規劃路徑、超過大小上限或判定失敗，一律回到完整規則。秘密掃描、內容安全、Core Change Test Matrix、Integration Gate、必要檢查與人工合併核准都不變，`automatic_merge_authorized` 仍為 false。

Dependabot repository preflight 與 action 釘選同步（Scenario 221）：`scripts/repository_preflight.py`、文件同步 contracts 與 `scripts/documentation_sync.py` CLI 一律經由 `documentation_sync.evaluate_candidate` 判斷文件同步，與 docs-impact、placement 共用同一個 `pure_dependency_update`；不符合時完整規則照舊。驗證 contracts 不再複製 action commit SHA，改由 `dependency_impact.require_pinned_action` 檢查 action 名稱完全相符、40 碼完整 commit SHA、版本註解不低於已審查下限，以及成對 workflow 使用同一 SHA；evolution 設定改記 `action: openai/codex-action`。新 SHA 是否等於上游 tag 對應的 commit，仍由人工審查確認。

文件同步路徑正規化（Scenario 221）：`documentation_sync.evaluate_changes` 只移除開頭一個 `./`（`removeprefix`），不再用 `lstrip("./")` 逐字元剝除；先前 `.github/workflows/x.yml` 會被改成 `github/workflows/x.yml`，使 `config/documentation-sync.yaml` 中所有 `.github/**` 觸發條件（Technology Guide、evolution-radar、publication-preflight、documentation-platform、execution-isolation 等）失效。修正後，人工修改 workflow 需同步對應文件；純依賴升級仍由 `evaluate_candidate` 先行豁免。
發布守門測試的合成掃描 fixture（`tests/test_publication_authority.py::scanner_fixture_assignment`）每次執行都把 16 個十六進位數字各放兩次後隨機排列，Shannon 熵固定為 4.0、高於 `generic-secret-assignment` 的 3.25 門檻，因此偵測結果不再隨機；原本直接使用 uuid4 hex 約有 0.7% 機率低於門檻而造成偶發失敗。掃描器規則與門檻不變。

Scenario 269 lifecycle evidence covers task-scoped Turn Context preparation (READY+STALE related vs unrelated topics, read-only index status, hook wording) and the dry-run-by-default `aips intelligence gc` in a temporary config directory; Change Impact and existing hard stops stay unchanged.

## Product Delivery

Publication diagnostics do not change Human approval, Host permission, Required Checks, merge policy or execution authority.

Publication transfer parses GitHub remotes from the literal `git@github.com:<owner>/<repo>.git` form and from `https`/`ssh` URLs. The scanner's `git`-only SSH exemption does not relax any other email finding, so transfer code should not hide remote strings behind string assembly.

Scenario 266 covers versioned injection classification, added-line checks, full-blob secret/PII scanning, and safe recovery diagnostics.


The current lucas-lab main policy requires pull requests and the `verify` and `visual-audit` checks, and disallows force pushes and deletion.

Publication guidance separates target policy evidence from candidate identity and never treats diagnostic recovery as authorization to publish.

Product Delivery 把 requirement、planning、implementation、security、quality、release readiness、staging / production verification串成可追蹤生命週期，但 Production Enablement 仍需要 Human authority。

Planning Package 可用 EARS 結構表達適合的功能需求，並以 optional `REQUIREMENTS.yaml` 維護需求 ID、驗收條件與驗證方式的連結。`scripts/requirements_traceability.py` 支援 JSON PASS/FAIL 輸出與成功／失敗退出碼，供自動化工具判斷結構檢查結果。EARS 只約束敘述結構；semantic review 和實際驗證仍走既有澄清、品質規劃與 evidence 流程。 v2 package 可選 `PLANNING_MANIFEST.yaml` 與 `scripts/planning_package_validate.py` 檢查 artifact 狀態、適用性、依賴 DAG、穩定參照、requirements traceability 與雙階段人工核准證據；沒有 manifest 的舊 package 保持相容。`PRODUCT_RESEARCH.md`、`DOMAIN_MODEL.md`、experience、visual 與 API 範本形成跨文件契約。電商參考資料由 `references/domains/INDEX.yaml` 依觸發條件延遲載入；不適用於其他領域的規則不會變成全域前提。

Implementation Resolution 先釐清 REST/OpenAPI authority，再依既有專案證據或新專案的 Human-confirmed 選型建立 Implementation Profile。Go、PHP、Python、.NET 語言 Profile 提供穩定基線，專案規則與工具鏈仍優先。結構驗證器只檢查欄位、來源和 ownership 衝突，不判斷架構或技術建議是否正確；未取得驗證證據時回報 `UNVERIFIED`。

## Evolution & Maintenance

Publication timeout and Hook recovery changes stay bound to Scenario 260/261, documentation placement closure and the exact-candidate Core Matrix.

The 0.83.0 release record includes a candidate-bound Core Change Matrix and exact-candidate Gate evidence.

Branch Hygiene reconciles the current main SHA, exact remote branch heads, local checkout activity, and read-only PR merge state. It emits `KEEP`, `SUPERSEDED`, `REBASE_REQUIRED`, and `CLEANUP_CANDIDATE` as review guidance. The scheduled workflow only reports; any cleanup still requires its existing one-time exact-manifest authorization.

Evolution Radar deterministic pre-analysis 會輸出 shortlist 與排除原因計數；採納與 trial 仍須遵循既有人工決策政策。

Evolution relevance evaluation uses a reproducible monthly sample of 20 signal fingerprints and explicit Human labels. It reports shortlist precision/recall, actionable yield and source yield offline; incomplete labels remain `NOT_READY`, and policy changes still require a Human decision.

Plan19 的月報將未分析 signals 與缺少 pre-analysis 的 Issue 列為 coverage gaps；結果不改變 source scores 或 ranking。

### Evolution Radar

定期收集 public-source technology evidence、dedup / provenance、deterministic pre-analysis、semantic handoff 與 Human Decision。


### Controlled Trial

TRIAL 只能在 approved scope/path 與 isolated workspace內執行；PASS 仍不是 ADOPT。

### Evidence Quality

Community signal 可用於 discovery，但高強度 adoption recommendation需要 primary-source corroboration。

### Monthly Maintenance Reliability

The monthly reliability workflow measures validation outcomes and runtime distributions, explicit hotfix labels, repeated change surfaces, bounded operational failure hints, exact-SHA escaped regressions and files per merged change. Incomplete history stays UNKNOWN and prompts Human review. GitHub Actions uses read-only Actions, contents and pull-request access plus Issue write access to publish a bounded report; it has no remediation, source change, PR, merge or release authority.

Plan21 Phase 0 records one exact-main full-validation timing observation and pins existing digest, CLI and glob contracts. Treat the timing as a baseline sample only; future optimization claims require comparable candidate and environment evidence.

## Documentation Platform

Publication CLI behavior is documented in the User Guide and linked to its Scenario 261 conformance evidence.

The Claude Code standard publication recipe lives in the Claude Code adapter and is linked to Scenario 261.

Project lifecycle guidance is placed in the canonical Existing Project, Installation and Architecture topics; Scenario 044 is the lifecycle evidence source.

OpenCode stale-freshness 行為須在 Human Harness、Project Intelligence 指南、adapter 契約與 Scenario 267 中保持一致。

官方文件網站面向使用者與維護者，操作指引、概念及導覽以繁體中文撰寫；專有名詞首次出現時補上英文原名。程式碼、指令、API／設定欄位、路徑、狀態與原因碼保留 canonical 拼法，方便搜尋與複製。首頁採任務導覽；架構圖與流程圖須符合目前程式與設定，並附繁體中文替代文字及圖說。

文件網站固定使用 VitePress 1.6.4；`package.json` 只覆寫 `vitepress` 引入的 Vite 為 6.4.4，由 Vite 自身宣告的 `esbuild ^0.25.0` 提供修補版本，不另行強制覆寫 esbuild。這個 Vite 版本超出 VitePress 1.6.4 原本宣告的 Vite 5 範圍，因此更新時必須重新驗證相容性；上游穩定版原生支援已修補工具鏈後，再評估移除覆寫。

以 Node 24 執行 `npm ci --no-audit --no-fund --ignore-scripts`、`npm audit` 與 `npm run docs:build`，並確認 `npm ls vite esbuild`、開發、預覽與熱更新。`npm run docs:dev` 綁定 `127.0.0.1`，停用跨來源 HTTP 存取並保留 Vite 主機檢查。VitePress 1.6.4 的靜態預覽忽略 host 設定，因此 `npm run docs:preview` 改由已修補的 `vite preview` 提供 `.vitepress/dist`，明確綁定 `127.0.0.1` 並保留 Vite 預設 Host／CORS 限制；網站 base 仍是 `/ai-product-system/`，clean URLs、搜尋與導覽需一併驗證。勿以 `--host 0.0.0.0`、對外 port mapping、tunnel、`cors: true` 或 `allowedHosts: true` 放寬存取；確有遠端開發需求時，另行評估存取控制與明確允許清單。正式網站只部署 build 後的靜態產物。

### Human Documentation Source

docs/human/*.md 是 Human canonical source。Current behavior 依 domain section維護；CHANGELOG 保留 Unreleased 與最近五個完整版本，較早的完整 release sections 由 `docs/history/changelog/` 人工封存並保留根目錄版本錨點。Plan26 Phase 7 將目前累積的 release notes 對齊 `VERSION` `0.81.0`，並留下空白 Unreleased。Stable tag 僅在 exact-candidate readiness 通過且取得獨立 Human 核准後建立；Conformance 保存驗證歷史。

### VitePress

Official Docs Site 使用 VitePress 1.6.x stable line，提供 sidebar、local search、per-page outline 與 GitHub Pages static deployment。Renderer 不成為另一份 Source of Truth。

Documentation Placement 將每個 behavior-bearing source 綁到 canonical Human topic；Technology Guide 的廣域 trigger surface若出現尚未映射的新 source，CI 會 fail closed，要求先更新 placement contract。每條已知 subsystem rule 也明確限制 Technology Guide 可修改的 domain，因此版本新增功能不能再任意 append 到文件尾端。
## Runtime Content Safety Boundary

The JSON fallback is non-authorizing and cannot substitute for a successful full candidate and history scan.

PR-bound scan evidence is non-authorizing and cannot substitute for the full candidate and history scan.

The shared publication scanner recognizes only the documented generated-password and parameterized SQL forms as non-literal assignment values. Known provider tokens, private keys and high-entropy literals remain detectable, and oversized text or JSON remains fail-closed under its configured finite bound. The only WebM exceptions are the three exact Dewhollow Gate 1 evidence paths listed in `config/secret-scan.yaml`; there is no extension-wide exemption, and the 2,000,000-byte text limit remains unchanged. The same exact relative paths are excluded in any repository using the shared policy.

The optional `AIPS_ENFORCE_REQUIRED_CHECKS=1` merge gate does not change the content-safety scanner contract or candidate scanning.

The Hook and Prepare timeout diagnostics expose stable allowlisted fields only; raw commands, endpoint values and exception text remain omitted.

Publication validation checks the literal command form before candidate inspection; the existing scanner then checks the exact tree and reachable history. Stable `SECRET_SCAN_*` failures remain fail-closed and redact raw exception details.

AVIF uses the same 8 MiB media cap and a 1 MiB metadata cap; unsupported or animated structures fail closed and the AV1 payload is not decoded as text.

非預期授權例外會被拒絕；Hook 和 opt-in ledger 只保留 allowlist 例外類別，不保留原始錯誤文字。
The shared commit candidate scanner backs both the native Hook and `aips safety diagnose commit`. Format-aware metadata extraction is bounded for PNG, JPEG, WebP, M4A and MP3; unknown binary and scanner failures return stable safe diagnostics and fail closed.

The provider-neutral `scripts/content_safety.py` kernel supplies deterministic secret and baseline PII detection, provenance-aware injection signals, and sink-aware `ALLOW`, `REDACT`, `BLOCK` and `REVIEW` decisions without requiring an external model or API credential.

Versioned injection rules distinguish instruction override, exfiltration, agent execution and ambiguous wording. Git commit scanning evaluates changed lines with source context, while Secret/PII checks cover the full staged blob. The shared read-only diagnostic returns stable rule/finding IDs and actionable recovery without matched text. Exact, expiring exceptions require approval evidence and cannot bypass Secret, PII or scanner-failure blocks.

Commit 與發布掃描支援有界的 TTF/OTF/WOFF/WOFF2 metadata；fontTools/Brotli 缺失、格式偽裝、解析錯誤或資源超限都 fail closed。

`pii.email.v2` is a deterministic regex plus Git remote grammar check: only the exact ASCII `git` userinfo of an scp-like or `ssh://` remote is excluded, and PII has no exception path.

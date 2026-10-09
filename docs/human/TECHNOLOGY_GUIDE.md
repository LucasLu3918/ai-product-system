# AIPS Technology Guide

獨立審查 receipt 的 Ed25519 驗簽使用 Python `cryptography`，版本固定於驗證依賴。受信任公鑰清單由執行環境在候選 repository 外提供；未提供時不宣稱已驗證 runtime 隔離。Context、Retrieval 與 Integration Gate 的操作耗時來自實際起迄事件，不推估模型 token。

Retrieval relation candidates are built by a small standard-library module behind the established Python facade. They remain rebuildable lexical evidence and do not claim compiler-grade call resolution.

這份文件解釋 AIPS **目前採用的技術與架構選擇**。版本時間線不放在這裡。

## Runtime & Integration

OpenCode V2 registers a bounded creative tool that requires explicit intent. Its `prepare` action creates versioned character/style Profiles and an unconfigured Bundle in a non-Git EPHEMERAL scope; `preflight` remains read-only and `execute` requires a ready Bundle.


### Turn-Aware Global Harness

The OpenCode V2 adapter derives Context from the active Session root, caps the compact manifest at 12,000 bytes, and reports bounded hook timings without persisting prompts or file contents.

AIPS 將 Runtime/User instructions、Project rules、Project Intelligence 與 AIPS protocol 組合成 bounded context。不同 Runtime 使用各自可驗證的 integration strategy。

Adapter resolvers keep JSON/YAML results on stdout and diagnostics on stderr. Invalid adapter-state data is an explicit error; unavailable optional Intelligence subprocesses use a stable reason code and are not reported as an empty successful result.

### MCP Interoperability Gateway

MCP 提供 local stdio portable access plane，公開 Resources / Prompts / deterministic Tools。Tool-only Hosts 另以 read-only catalog/read/workflow Tools 取得相同 canonical capability context；所有 Tools 都宣告 non-destructive、idempotent、closed-world hints。Host model 負責 semantic reasoning；MCP Server 不呼叫第二個 LLM。

Cursor、Windsurf、GitHub Copilot CLI、Amp、Codex 與 generic 設定只產生 review-only payload。MCP 是新 Host 的預設接入；只有 verified per-turn hook、pre-tool guard 或 runtime-specific event source 需求才擴充 native adapter。

### Progressive Disclosure

Role、Skill、Protocol 與 Project evidence 只在 task relevant 時載入，避免把整個 system context 常駐每個 Turn。

## Project Understanding

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

Local hybrid retrieval 組合 lexical、symbols、structural relation、tests、Impact Graph 與 Git history。Optional semantic / embedding trial 不會因存在就變成 baseline requirement。

若 Retrieval 回報 `RETRIEVAL_CACHE_WRITE_ACCESS_DENIED`，代表舊索引需要刷新但 Runtime 無法寫入 SQLite cache 或 sidecar；授予 cache 寫入能力，或為該 Runtime 設定可寫的 `XDG_CACHE_HOME` 後重試。舊索引維持 stale，不會以唯讀快照冒充 current。

### Change Impact Guard

Existing Project mutation 前先宣告並授權 Change Boundary，使用 `IMPLEMENTATION_APPROVED` 進入核准範圍；實作後對帳 actual diff 與 declared impact，只有完整記錄 reconciliation evidence 才能標記 `READY`。

## Execution

The local Creative `generate-set` executor preflights configured Bundles one at a time, records per-item outcomes, and resumes only when prior output and provenance hashes still match. OpenCode V2 receives mutation authority from native prompt admission, not Context.

`aips project diagnose` 不會啟動 Creative Bundle 或模型；創作生成仍由既有受限的明確使用者請求路徑執行。

MFLUX 固定命令表新增 Z-Image Turbo generate：`mflux-generate-z-image-turbo`。CLI 不傳任意額外參數；步數沿用明確 Bundle 設定，模型與 tokenizer 仍須預先完整安裝，本流程不下載。ComfyUI 也支援限定的 Z-Image Turbo generate profile：固定 UNETLoader、CLIPLoader (`lumina2`)、VAELoader 與 AIPS 內建 API 拓樸，preflight 逐項核對本機模型清單；不支援任意 split-loader 工作流或 edit。

本機創作支援 discover/prepare/configure/preflight/execute：設定採 allowlist 與 create-only Bundle，native Context envelope 經正規化再作使用者授權。PNG 容器檢查涵蓋 CRC、終止與 bounded decompression；JPEG/WEBP 僅作 bounded container checks，不能代替實際看圖或完整解碼。

Local creative execution supports MFLUX through fixed argv and ComfyUI through a loopback-only allowlisted workflow. It is explicit, create-only, and never downloads weights.

System changes keep the exact-candidate repository Gate enabled while any selective-validation proposal remains report-only until its complete observation cohort is reviewed.

### Local character artwork

The optional local character-art executor accepts an already-installed MFLUX CLI or a loopback ComfyUI API workflow restricted to built-in nodes. A closed model/operation registry maps FLUX.1, FLUX.2 Klein, Qwen Image Edit 2511 and Z-Image Turbo to fixed executable arguments or the registered split-loader topology. FLUX.1 edit accepts one reference, while FLUX.2/Qwen edit commands with `--image-paths` accept up to eight bounded references. ComfyUI edit accepts one staged hash-checked reference; the Z-Image Turbo profile is generate-only and checks its UNET, CLIP and VAE against the local API inventory. It disables HTTP proxying and redirects, uses offline model-hub flags, scopes create-only PNG/JPEG/WEBP output to a non-Git EPHEMERAL bundle, strips ComfyUI text metadata that can contain prompts, and records profile/workflow/input/output hashes, model revision, runtime version and license source. Preparation creates versioned fixed Profile/Bundle files without overwrite and leaves engine provenance unconfigured. Preflight does not generate; missing local engines return `BLOCKED_NO_ENGINE`. No runtime or weights are installed, and no image is sent to a cloud provider. Existing Comfy MCP guidance remains available when that user-managed route better fits the project.

The shared helper package consolidates canonical hashes, repository-relative paths and caller-specific glob matching; existing module facades preserve current call sites and outputs.

Task-specific routes keep product-delivery, visual, security, testing, API/data, planning, documentation and publication procedures progressive; the general mutation fallback includes Orchestrator, Change Impact and Quality Planning.

`scripts/repository_governance_snapshot.py` 是選擇性、唯讀的 operator snapshot；若 `gh` 不可讀取任一設定面，結果標為 UNKNOWN。

Standalone and shadow dependency-review artifacts retain exact base/head, run ID, actual JSON findings and outcome for 90 days. Parity compares canonical findings; missing outputs, different candidates or inaccessible artifacts stay UNKNOWN. Job success alone cannot promote the shadow. Record resolved toolchain fingerprints and repeat full Gates only for new changes or unresolved failures.

CLI 發布診斷優先選擇完整 Python 3.12 驗證環境，再以既有環境診斷一次列出缺少的 yaml、ruff、mypy、Playwright、OpenAPI、JSON Schema 與 cryptography。`runtime_cache.py` 同時服務 Retrieval 與發布工具的 gh 呼叫；`package_install.py` 提供明確安裝的安全錯誤分類。CI 只快取 pip 下載，不重用整個 Gate PASS。

GitHub Actions job 的逾時依最近成功執行的 P95、明示安全倍數與向上取整方式設定；installation entrypoint 的 Unix/Linux/Windows jobs 目前採 5/10/10 分鐘，依 2026-10-06 02:53–11:34 UTC 最近十次成功執行計算。只在工作共用狀態且不會丟失必要證據時才設定 concurrency。

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


## Security & Governance

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

## Quality & Verification

The Core Creative verification path covers native prompt admission and revocation, bounded multi-item recovery, local-only engine probes, documentation closure and the exact committed candidate.

`aips project diagnose <path>` 聚合既有只讀檢查，Lifecycle evidence 驗證 text/YAML/JSON、隱私遮蔽、失敗情境與不寫入行為。這份診斷不取代各 subsystem 的權威檢查或精確候選 Gate。

創作驗證分別記錄命令盤點、合成 tool/provider 測試、native host 驗證及真實模型推論。未提供權重時，品質／設備效能維持未驗證，不以流程通過推定改善成效。

Creative lifecycle checks use synthetic engines and loopback fixtures; they verify command contracts and confinement, not model quality, hardware performance or visual fidelity.

Scenario 236 and the creative lifecycle verify provider boundaries, provenance, rollback, trace privacy, and pending human review; synthetic output does not establish visual quality.

OpenCode validation separates install and discovery from Session Context delivery and permission-hook execution; claims remain limited to the tested host and version.

OpenCode Adapter 使用 ownership digest、安全路徑檢查與原子寫入管理全域 AGENTS、canonical Skills、Commands 及 V2 plugin。V2 plugin 在 primary dispatch 注入 compact Turn Context，permission hook 檢查受支援的直接檔案資源，Shell 限制為 bounded read-only allowlist。L1 允許非 Git workspace 的 confined 新 creative asset；L2 要求 Project Intelligence READY/CURRENT；L3 外部動作沿用 Human approval。Lifecycle 涵蓋版本、重裝、衝突、漂移、損壞 manifest、symlink、中斷恢復與解除。Plugin discovery 已由 OpenCode 2.0.24 registry 驗證；模型 Context delivery 與 permission action 尚未驗證，Governance 維持 ADVISORY，MCP/custom tools 和 out-of-process writes 不在 guard 範圍。

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

Validation quality improves gradually: a Ruff baseline blocks debt growth, mypy remains scoped to selected modules, Coverage.py reports branch evidence without a premature percentage gate, and deterministic Hypothesis properties cover stable SemVer selection. The read-only Validation Observation Collector installs its pinned PyYAML dependency before collecting the shadow cohort; full validation remains mandatory while that cohort is assembled. The collector uses a provisional 15-minute timeout from a two-run, 31-second timing sample; this is a conservative bound, not a reliable P95. It has no concurrency group because pending scheduled or manual evidence must not be replaced.

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

Scenario registry 將 evidence 分成 deterministic、lifecycle、agent_eval、manual，不用「檔案存在」冒充 automated coverage。

### Agent Evaluation

外部 Eval adapter 位於 `scripts/eval_interop.py`，使用無第三方框架 runtime 依賴的 bounded parser；Promptfoo static subset、PyRIT versioned bridge、risk profiles 與 finding promotion 都沿用 Agent Eval Case/Result 和既有 Gate authority。輸入格式與限制見 `orchestration/EVAL_INTEROPERABILITY.md`。

需要 semantic judgment 的 case 使用 provider-neutral observable-result contract，不保存 private reasoning。

### Repository Health

Architecture Surface、documentation mapping、validation contract 與 drift evidence用 deterministic audit 檢查。

Documentation audience 掃描忽略 Git 已明確忽略的本機 metadata；未被忽略的未知 docs-root entry 仍 fail closed。

獨立程式碼審查以 `SELF_CHECK` 與 `INDEPENDENT_REVIEW` 分開建模。Scheduler 建立唯讀隔離任務；review packet 以 allowlist、大小／路徑限制和檔案指紋固定審查輸入。Evidence 必須綁定精確 base/head、packet 與不同 execution ID，並由可信 runtime attestation verifier 驗證。沒有可用 verifier 時維持 `UNVERIFIED`，必要審查在 Integration Gate fail closed；靜態結構檢查不能冒充簽章驗證或語意判斷。
Publication Preflight 的 lifecycle evidence 固定 Python module probe，再分別模擬 loopback 與 browser blocker，讓環境診斷測試不依賴主機是否安裝 optional modules。

The observation collector reports readiness separately from collection health: `NOT_READY` succeeds as evidence collection, while API/artifact failures, absent reports and unknown states fail. Dependency Review shadow runs alongside full validation but does not change the required result; promotion requires same-candidate parity and separate review.

- Release-readiness changes require lifecycle cases for an empty, non-empty, missing, duplicated, malformed, and unavailable Unreleased section.
## Product Delivery

Product Delivery 把 requirement、planning、implementation、security、quality、release readiness、staging / production verification串成可追蹤生命週期，但 Production Enablement 仍需要 Human authority。

Planning Package 可用 EARS 結構表達適合的功能需求，並以 optional `REQUIREMENTS.yaml` 維護需求 ID、驗收條件與驗證方式的連結。`scripts/requirements_traceability.py` 支援 JSON PASS/FAIL 輸出與成功／失敗退出碼，供自動化工具判斷結構檢查結果。EARS 只約束敘述結構；semantic review 和實際驗證仍走既有澄清、品質規劃與 evidence 流程。 v2 package 可選 `PLANNING_MANIFEST.yaml` 與 `scripts/planning_package_validate.py` 檢查 artifact 狀態、適用性、依賴 DAG、穩定參照、requirements traceability 與雙階段人工核准證據；沒有 manifest 的舊 package 保持相容。`PRODUCT_RESEARCH.md`、`DOMAIN_MODEL.md`、experience、visual 與 API 範本形成跨文件契約。電商參考資料由 `references/domains/INDEX.yaml` 依觸發條件延遲載入；不適用於其他領域的規則不會變成全域前提。

Implementation Resolution 先釐清 REST/OpenAPI authority，再依既有專案證據或新專案的 Human-confirmed 選型建立 Implementation Profile。Go、PHP、Python、.NET 語言 Profile 提供穩定基線，專案規則與工具鏈仍優先。結構驗證器只檢查欄位、來源和 ownership 衝突，不判斷架構或技術建議是否正確；未取得驗證證據時回報 `UNVERIFIED`。

## Evolution & Maintenance

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

文件網站固定使用 VitePress 1.6.4；`package.json` 只覆寫 `vitepress` 引入的 Vite 為 6.4.4，由 Vite 自身宣告的 `esbuild ^0.25.0` 提供修補版本，不另行強制覆寫 esbuild。這個 Vite 版本超出 VitePress 1.6.4 原本宣告的 Vite 5 範圍，因此更新時必須重新驗證相容性；上游穩定版原生支援已修補工具鏈後，再評估移除覆寫。

以 Node 24 執行 `npm ci --no-audit --no-fund --ignore-scripts`、`npm audit` 與 `npm run docs:build`，並確認 `npm ls vite esbuild`、開發、預覽與熱更新。`npm run docs:dev` 綁定 `127.0.0.1`，停用跨來源 HTTP 存取並保留 Vite 主機檢查。VitePress 1.6.4 的靜態預覽忽略 host 設定，因此 `npm run docs:preview` 改由已修補的 `vite preview` 提供 `.vitepress/dist`，明確綁定 `127.0.0.1` 並保留 Vite 預設 Host／CORS 限制；網站 base 仍是 `/ai-product-system/`，clean URLs、搜尋與導覽需一併驗證。勿以 `--host 0.0.0.0`、對外 port mapping、tunnel、`cors: true` 或 `allowedHosts: true` 放寬存取；確有遠端開發需求時，另行評估存取控制與明確允許清單。正式網站只部署 build 後的靜態產物。

### Human Documentation Source

docs/human/*.md 是 Human canonical source。Current behavior 依 domain section維護；CHANGELOG 保留 Unreleased 與最近五個完整版本，較早的完整 release sections 由 `docs/history/changelog/` 人工封存並保留根目錄版本錨點。Stable tag 僅在 exact-candidate readiness 通過且取得獨立 Human 核准後建立；Conformance 保存驗證歷史。

### VitePress

Official Docs Site 使用 VitePress 1.6.x stable line，提供 sidebar、local search、per-page outline 與 GitHub Pages static deployment。Renderer 不成為另一份 Source of Truth。

Documentation Placement 將每個 behavior-bearing source 綁到 canonical Human topic；Technology Guide 的廣域 trigger surface若出現尚未映射的新 source，CI 會 fail closed，要求先更新 placement contract。每條已知 subsystem rule 也明確限制 Technology Guide 可修改的 domain，因此版本新增功能不能再任意 append 到文件尾端。
## Runtime Content Safety Boundary

The provider-neutral `scripts/content_safety.py` kernel supplies deterministic secret and baseline PII detection, provenance-aware injection signals, and sink-aware `ALLOW`, `REDACT`, `BLOCK` and `REVIEW` decisions without requiring an external model or API credential.

# System Maintenance

Runtime Context 或 Integration Gate 改動時，執行 Scenario 198、完整 repository validation 與 exact-candidate Integration Gate，並維護 Change Impact 和 CORE_CHANGE_TEST_MATRIX 證據。

Retrieval relation extraction changes preserve the legacy `retrieval_intelligence.py` entry points. Run the focused extraction lifecycle, retrieval lifecycle and full repository Gate; lexical traversal uncertainty remains explicit.

Evolution pre-analysis extraction likewise retains `evolution_analysis.py` as its CLI/import facade. The focused Radar lifecycle and module-identity checks preserve deterministic output and Human decision authority.

## Documentation Impact Gate

Every system change must assess downstream documentation and behavior before completion.

| Area | Update when affected |
|---|---|
| `SYSTEM.md` | routing, planning gates, precedence, context or completion behavior changes |
| `orchestration/*` | detailed execution/model/instruction/planning behavior changes |
| `docs/ARCHITECTURE.md` | runtime flow, planning flow, boundaries or update lifecycle changes |
| `README.md` | Human first-entry behavior changes |
| `docs/GETTING_STARTED.md` | Human quick-start changes |
| `docs/USER_GUIDE.md` | Human-facing workflows/commands change |
| `docs/INSTALLATION.md` | Human installation/update lifecycle changes |
| `docs/ARCHITECTURE_OVERVIEW.md` | Human architecture overview changes |
| `docs/assets/*.svg` | Human-facing architecture/lifecycle diagram changes |
| `docs/HARNESS.md` | Global Harness / Adapter / ownership behavior changes |
| `harness/*` | Global Harness / Adapter contract changes |
| `AGENTS.md` | Agent bootloader changes |
| `examples/*` | a new behavior needs a practical example |
| `tests/scenarios/*` | routing/gate behavior changes or regressions need coverage |
| templates/schemas | persisted contract/state/planning/brand/creative/automation shapes change |
| `orchestration/CREATIVE_DIRECTION.md` | creative workflow changes |
| `orchestration/BRAND_SYSTEM.md` | brand workflow/precedence changes |
| `orchestration/CAPABILITY_INCUBATION.md` | Role/Skill creation/reuse behavior changes |
| `orchestration/SECRET_HANDLING.md` | credential acquisition/redaction/exposure behavior changes |
| `orchestration/CORE_CHANGE_TESTING.md` | core-change test-selection/completion behavior changes |
| `orchestration/DETERMINISTIC_AUTOMATION.md` | tool-vs-reasoning routing changes |
| `orchestration/PRODUCT_DELIVERY.md` | complete-product lifecycle changes |
| `orchestration/RELEASE_READINESS.md` | release/deployment readiness changes |
| `templates/product/*` | Product Manifest / workspace contract changes |
| `templates/delivery/*` | Local/deployment/release/runbook contract changes |
| `VERSION` | release version changes |
| `CHANGELOG.md` | every released behavioral change |

If an item is not affected, mark it N/A during change review rather than editing it unnecessarily.

## Architecture Diagram Impact Check

Every Large/Core Change must explicitly assess architecture-diagram impact as part of the existing Documentation Impact Gate. This is not a new approval gate.

Trigger examples: Runtime/Routing/Context-loading flow changes; Harness/Adapter/instruction precedence changes; Project persistence/workspace lifecycle changes; complete-product/Release lifecycle changes; major Security/Quality/Review lifecycle changes; Install/Update/Uninstall behavior changes; a major new subsystem or boundary.

Required review set:

- docs/ARCHITECTURE.md Mermaid;
- docs/ARCHITECTURE_OVERVIEW.md;
- docs/assets/system-overview.svg;
- docs/assets/harness-overview.svg when Harness is affected;
- docs/assets/product-delivery-overview.svg when delivery is affected;
- docs/assets/project-intelligence-overview.svg when Turn Context / Project Intelligence / Change Impact is affected;
- docs/assets/system-lifecycle.svg when install/project lifecycle is affected.

For every relevant diagram: Affected → update diagram + explanation; Not affected → record N/A + concrete reason.

A Large/Core Change that materially changes a documented architecture flow but leaves the corresponding diagram stale is documentation-incomplete and must not be released as complete.

## Self-improvement / Constitution / publish approval

Changes to this system first pass `orchestration/SYSTEM_SELF_IMPROVEMENT.md`.

If Constitution semantics are affected, the Constitutional Change Gate must complete before implementation. Material system changes also require Core Change Approval.

Before remote publication, present the Git Publish Proposal. A material difference from the approved implementation/publication plan requires re-approval.

Multi-file changes should normally be assembled into one coherent remote branch update after the logical change is complete. Avoid file-by-file remote commits/pushes that expose temporary incomplete repository states to CI. If incremental remote publication is necessary for collaboration or diagnosis, record that reason in the Git Publish Proposal.

## Release checklist

1. Confirm System Improvement Review and applicable Constitutional/Core Change approvals.
2. Run `aips validate`.
3. Review the Documentation Impact Gate.
4. For Large/Core changes, complete Architecture Diagram Impact Check.
5. Confirm Mermaid and affected Human SVG diagrams match actual behavior.
6. Build the Impact-derived Test Matrix for the final Change Boundary and execute every applicable check.
7. Confirm changed routing/gate behavior has scenario coverage.
8. Confirm planning/creative/brand/automation/product-delivery templates match their protocols when affected.
9. Confirm Human and Agent documentation audiences are synchronized when behavior affects them.
10. Confirm applicable secret/credential leakage and handling review is complete; secret-scan evidence must not echo secret values.
11. Update `VERSION` using SemVer.
12. Update `CHANGELOG.md`.
13. Ensure the system working tree is clean before publishing.
14. Prepare the Git Publish Proposal and obtain explicit approval.
15. Prefer independent review/PR for material system changes.

## Versioning

Python support facts live in `config/system-facts.yaml` and are mirrored in `pyproject.toml`. The required PR Gate tests Python 3.12; the weekly compatibility workflow smoke-tests 3.12, 3.13, and 3.14. Runtime-floor changes must keep System Reference, installation guidance, Technology Guide, and Scenario 210 aligned.

- MAJOR: incompatible governance/protocol/contract changes.
- MINOR: backward-compatible new behavior, role, skill, work mode, CLI capability or schema/planning extension.
- PATCH: backward-compatible bug fix, hardening, clarification, typo or non-behavioral documentation/evidence correction.

Major updates are not auto-applied by `aips preflight` without explicit `--allow-major`.

`tests/validation/versioning_contracts.py` verifies one leading `Unreleased` heading, unique strictly descending SemVer release headings, and `VERSION` equal to the newest release. Keep runtime dependency ranges in requirements files; `constraints/tested.txt` records the exact CI-tested set. Python support is declared separately from the tested Python version in `pyproject.toml` and `config/system-facts.yaml`.

`scripts/version_tag_policy.py` checks `VERSION`, exact candidate/main SHA, any existing tag destination, and that `CHANGELOG.md` has exactly one empty `## Unreleased` section. Missing, duplicate, malformed, or non-empty sections block readiness. READY still requires separate explicit release approval; merging a PR does not create a version tag or backfill historical tags.

## System facts and validation planning


`config/system-facts.yaml` and `config/architecture-surfaces.yaml` are the source for factual command/capability tables in `docs/human/SYSTEM_REFERENCE.md`. Run `python scripts/system_facts.py --write` after changing those facts and `--check` in validation. Keep explanatory prose in its canonical topic documents.

CI derives optional Node, browser and OpenAPI provisioning from exact candidate paths using `scripts/ci_validation_plan.py`. Unknown paths select the full toolchain. The plan only skips unrelated optional setup and its isolated lifecycle evidence; mandatory secret scanning, fast preflight, repository validation and the exact-candidate Integration Gate remain required.

## Documentation audience

- Human docs use Traditional Chinese. Specialized terms include English on first use.
- Agent docs remain concise English unless a concrete reason requires otherwise.
- Do not maintain duplicate full Human guides in two languages by default.
- `docs/DOCUMENTATION_MAP.md` is the audience map.
- When behavior changes, explicitly check both Human and Agent documentation impact.

## Simplicity / reuse review

Before release, check:
- no unnecessary new Role when an existing Role can own the work;
- no new Skill that merely represents a visual style/artifact type;
- no duplicate Role/Skill IDs;
- repeated rules live in one authoritative protocol and are referenced elsewhere;
- bootloader/README remain short entry documents;
- deterministic data processing uses helpers when this materially reduces repeated model work.


## Product delivery consistency

When end-to-end delivery behavior changes, verify together:
- PRODUCT.yaml contract;
- Product Creation Work Mode;
- Planning Package;
- Local Environment / Deployment Plan / Runbook;
- Release Readiness;
- Security Assurance interaction;
- Human architecture overview;
- production scenarios and validator coverage.


## Subsystem consistency map

### Interaction / requirement / external context

Implementation Resolution changes update `orchestration/IMPLEMENTATION_RESOLUTION.md`, its profile and language references, the structural validator, and Scenario 193 evidence together. Preserve contract authority, evidence provenance, ownership protection and `UNVERIFIED` semantics; a profile does not authorize migration or publication.


When these behaviors change, review together:

- Requirement clarification and Planning Package v2 → SYSTEM / ORCHESTRATOR / research, plan, requirement, experience, visual, domain, API and manifest templates / structural validator / reusable roles and skills / lazy domain references / Human Guide / architecture map / scenarios.
- External context resolution → connector-first protocol / provenance template / Human Guide / scenarios.
- Visual polish → Product Designer / Frontend Engineer / visual-quality-review / Design Work Mode / screenshots/state scenarios.
- Multi-perspective review → Quality Reviewer / code-review / Model Routing / Review templates / lesson persistence.

### Product delivery / quality / visual state

When product-delivery behavior changes, review together:

- QUALITY_PLANNING / QUALITY_PROFILE / Planning Package / Product Delivery / Product Manifest / Release Readiness;
- LOCAL_COMPLETE / Production Enablement / PRODUCTION_VERIFIED lifecycle;
- Project Visual Profile / Visual Audit / Product Designer / Frontend Engineer / visual-quality-review;
- Human Guide, product-delivery architecture diagram and applicable scenarios.

### Harness / Runtime adapters

When Harness behavior changes, review together:

- harness/BOOTSTRAP + HARNESS_PROTOCOL + ADAPTER_CONTRACT;
- Runtime Adapter registry/files;
- HARNESS_RESOLUTION + INSTRUCTION_RESOLUTION;
- bin/aips install/uninstall/preflight/resolve/status/doctor;
- README / GETTING_STARTED / INSTALLATION / HARNESS;
- system-overview / harness-overview / system-lifecycle SVG;
- Ephemeral/Attached scenarios and ownership regression evidence.

Never trade away user-owned instruction/Skill preservation merely to improve automatic coverage.

Install / Preflight lifecycle evidence should run against isolated temporary Git repositories and local bare remotes. System runtime artifacts such as Python `__pycache__/` / `*.py[cod]` must remain ignored so ordinary AIPS CLI execution cannot make the System repo fail its own clean-worktree preflight gate.

### Project Intelligence / Change Impact

When Project Intelligence behavior changes, review together:

- PROJECT_IDENTITY / PROJECT_INTELLIGENCE / CHANGE_IMPACT / Project Knowledge compatibility;
- TURN_HARNESS / HARNESS_RESOLUTION / INSTRUCTION_RESOLUTION;
- Project Intelligence templates + workspace MANIFEST/STATE;
- project_intelligence.py / turn_context_hook.py / bin/aips;
- README / GETTING_STARTED / PROJECT_INTELLIGENCE / USER_GUIDE;
- project-intelligence / system / lifecycle diagrams;
- freshness, source-registry, HTML, migration, single-writer and Change Impact evidence.

Legacy Project Knowledge remains compatibility input only. New reusable understanding belongs in Project Intelligence.

Focused Intelligence context evidence must distinguish storage deduplication from runtime-context deduplication. Do not promote conflict/override/change-impact/monorepo/migration Scenarios until their full contracts are actually enforced and directly exercised.

## Impact-derived regression testing

Phase 4 generator adapter 維護需同步檢查 Profile schema、OpenAPI evidence、命令執行邊界、allowlist、Phase 3 generation records、原子回復、Scenario 196 與 Integration Gate fixture。Gate 僅執行隔離的假 generator lifecycle，不呼叫專案設定的實際 generator。更換 generator 或 version 時應重新審查 executable hash、版本輸出、argv 與生成差異，並執行專案原生測試。Phase 5 的 `generator_reports` 是 Profile 自願啟用的未追蹤本機報告；維護時檢查 schema/fingerprint、Git 祖先、Profile 前後雜湊、工具版本與 argv、輸入與輸出及 generation records。執行 `tests/evidence/openapi_client_pilot_lifecycle.py` 確認本機服務、client、證據鏈及負面路徑；新增產品不自動複製 AIPS 範例。

For every Large/Core Change, testing is derived from the final Change Boundary, not from a fixed minimum smoke suite.

Build and persist a matrix:

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|

Rules:

- every materially affected boundary has applicable evidence;
- N/A requires a concrete reason;
- public contract changes require contract/consumer coverage;
- persistence/schema changes require migration/rollback/recovery evidence when applicable;
- Runtime/Harness/CLI changes require executable lifecycle/regression tests;
- security-boundary or credential-handling changes require security/secret-leakage evidence;
- documentation/schema/template contract changes require structural validation;
- if implementation expands the Change Boundary, recompute the matrix;
- failing required tests block completion/release;
- never remove a relevant test merely to obtain a green result.

Prefer the strongest practical deterministic evidence for affected behavior while avoiding unrelated full-suite cost that adds no confidence.

## Governance enforcement consistency

When Approval Binding / Governance Enforcement changes, review together:

- Approval Record template + governance_guard.py;
- Git Publish/Core Change/System Improvement approval fields;
- Runtime adapter state/ownership and Claude/Gemini pre-tool hooks;
- TURN_CONTEXT_MANIFEST explanation metadata;
- Harness/System architecture diagrams;
- scenarios 096-100 and focused governance evidence.

Do not claim TOOL_GUARDED when the installed pre-tool guard is absent or unverifiable.

## Durable Run State consistency

Task ownership lease 與共用 Scheduler state 必須以同一 task/execution identity 維持一致。過期 dirty work 不可自動重派；recovery 保留原 base revision 和 write set，最終以該 base 的完整 Git diff 對帳。

The Parallel Run Dashboard reads canonical checkpoints and related evidence through one sanitized projection. Keep it observational: approval, retry, cancellation, merge and publication remain outside the dashboard.

Event changes must preserve a single serialized sequence across run-state and telemetry writers. Observed Context, Retrieval and Gate stages record actual operation boundaries; when evidence is unavailable, observation is degraded and the original operation result is preserved.

When durable run state changes, review together:

- PROJECT_IDENTITY + RUN_RESUME;
- RUN_CHECKPOINT + workspace STATE;
- aips_identity.py + run_state.py + bin/aips run/identity routing;
- ATTACHED / EPHEMERAL storage and legacy migration;
- revision / branch / dirty workspace fingerprint behavior;
- EVENTS.jsonl redaction / no-transcript contract;
- resume/identity scenarios and executable lifecycle evidence;
- system/lifecycle diagrams.

Resume must never bypass current governance, security, impact or verification gates.

## Scenario Conformance consistency

When Scenario behavior/coverage changes, review together:

- tests/scenarios/*;
- tests/scenario_coverage.yaml;
- scripts/scenario_conformance.py + scripts/agent_eval.py;
- tests/agent_eval/cases/* + tests/agent_eval/results/*;
- tests/evidence/*;
- tests/validation/* + tests/validate_repository.py;
- orchestration/CONFORMANCE.md;
- docs/CONFORMANCE.md / USER_GUIDE;
- coverage claims in CHANGELOG/release evidence.

Before promoting legacy manual coverage: reconcile the Scenario to current canonical behavior, add direct evidence, then reclassify. For semantic behavior, Agent Eval requires an actual recorded observable Result bound to the exact Case fingerprint and passing deterministic scoring. Never infer automated coverage from Scenario count or an eval prompt alone.

## Execution Isolation consistency

The local Integration Gate selects a complete Python 3.12 validation environment and reports missing dependencies before candidate scanning. For documentation changes it requires Node 24+ and the already-installed VitePress bundle, invokes that bundle directly, and never installs packages or contacts a registry. The E2B artifact workflow pins the Node 24 upload action; its existing synthetic-data and least-privilege boundaries remain in force.

When Execution Isolation behavior changes, review together:

- PROJECT_IDENTITY + EXECUTION_ISOLATION;
- execution-profile schema + workspace MANIFEST;
- execution_isolation.py + bin/aips isolation routing;
- repository-level writer ownership / workspace identity / dirty cleanup;
- truthful sandbox capability reporting;
- architecture docs/diagrams;
- scenarios 111-120 and identity/isolation lifecycle evidence.

The provider-neutral registry binds runtime class, data class, egress, mounts, credential scope, TTL and evidence freshness. A provider is available only when enabled, integration status is ready and fresh registry-bound verification passes. The initial E2B candidate remains disabled; its manual `main` smoke workflow uses only synthetic input and requires prior written provider-test consent.

High-risk external runtime actions also require an exact, unexpired Approval Record and fresh verified network-egress enforcement. A hook alone is not a sandbox; missing provider proof blocks the action.

High-risk external runtime actions also require an exact, unexpired Approval Record and fresh verified network-egress enforcement. A hook alone is not a sandbox; missing provider proof blocks the action.

## Public repository / CI consistency

Evolution Effectiveness reports incomplete pre-analysis coverage instead of calling absent triage a zero shortlist. Oversized scheduled Radar Issues preserve the full UTF-8 body in a bounded digest-checked archive restored before monthly parsing.

外部 Intelligence metadata 不可寫時，可重建 metadata 保存在快取旁並回報 `CACHE_ONLY`；索引 freshness 仍由實際候選比對，canonical 來源與 graph 不會被替代。以 `aips publish checks --pr <number> --head <sha>` 查看最新 workflow/check 結果：舊 `CANCELLED` 不覆蓋較新的成功；目前取消、缺少必要 `repository`、等待或失敗均不會成為 PASS。PR 與 main 的 Gate 仍綁定各自候選；CI pip 快取以 requirements 雜湊作鍵，安裝與完整 Gate 每輪照常執行。合併後另核對註冊安裝版的 commit。

`installation-entrypoints` jobs are independent and retain their existing PR paths and read-only permissions. Review their 5/10/10-minute limits when runtime evidence changes; the limits use 15× per-job P95 from the ten latest successful runs and upward five-minute rounding. Do not add cancellation concurrency unless shared state requires it and required evidence remains observable.

Read-only scheduled workflow limits use observed run timing and an explicit safety margin. Repository Health's three completed runs took 14, 14 and 19 seconds; its ten-minute job limit is provisional because the sample is small. The monthly reliability workflow uses the shared Python bootstrap and queues up to 100 same-cohort Issue reports without cancelling a running or pending report. It has no timeout until a successful run provides a timing baseline. The Validation Observation Collector keeps its existing 15-minute limit and no concurrency group so each scheduled/manual shadow observation remains available. Evolution Effectiveness queues up to 100 pending schedule/manual writes to the same period Issue without cancelling any report; explicitly selected periods remain separate.

排查 `AUTH_CONFIGURATION_UNVERIFIED` 時先確認 `GH_CONFIG_DIR` 與 `XDG_CONFIG_HOME` 的設定選擇，再檢查登入；不要複製憑證。Local preparation 保留原本 gh 設定目錄並拒絕不屬於指定 Python 3.12 venv 的執行檔。文件異動先用 preview 查閉包；docs impact 須解析正確 checkout。重用準備好的環境，候選固定後執行一次完整本地 Gate，保留 PR 與 main CI；以既有 timing evidence 評估慢項目。

Use `aips publish environment` from the intended checkout and inspect its source/target/Python diagnostic before validation. Reuse an existing environment with `python3.12 bin/prepare-local-validation --venv <path> --check-only`; a local `--wheelhouse <path>` supports offline Python dependency installation. Browser downloads remain separate prerequisites. GitHub logs/artifacts may redirect to external storage; keep domain approval explicit and use bounded Check summaries for initial diagnosis.

The validation workflow installs the optional pinned `requirements-openapi.txt` set before running repository checks, so offline OpenAPI lifecycle tests use the same validator version in local and CI runs.

Retrieval cache failures distinguish read access from stale-index refresh writes. A `RETRIEVAL_CACHE_WRITE_ACCESS_DENIED` result means SQLite could not open the rebuildable cache for update; allow cache and sidecar writes or set `XDG_CACHE_HOME` to a location writable by the current runtime, then retry. Keep invalid-index rebuilds (`--force`) for an index explicitly reported `INVALID`; do not use them to bypass ordinary sandbox write restrictions. Project Intelligence semantic refresh remains separate and must still re-read changed authoritative sources.

提交前的 `aips publish preview --base <sha> --change-class <class>` 會檢查工作樹（含未追蹤檔）的文件 H2 placement、Core Matrix base/hash 綁定與 PR 首次建立所需標籤。若 CLI 認證失效，`aips publish plan` 回報 `AUTH_REQUIRED` 與重新登入步驟，不會輸出憑證內容；最終 Gate 仍以乾淨的已提交候選執行。

The working-tree preview scans candidate additions and complete untracked files. The exact committed candidate still receives the mandatory final-tree and commit-history scan in Integration Gate.

Publication preflight treats an optional environment capability as `NOT_REQUIRED` when the exact candidate plan does not select it; only a selected browser check can block on loopback or browser readiness. Required repository validation, candidate secret scanning and the Integration Gate remain mandatory.

When publication preflight changes, keep the working-tree preview, content safety findings, configured Git identity checks and exact-candidate resolver aligned with CI.

The optional OpenAPI validator is installed only by `aips openapi install` into the managed AIPS venv using pinned `requirements-openapi.txt`; basic installation stays network-minimal. Keep `aips openapi doctor`, `aips doctor`, actionable missing-dependency errors and product-root CLI validation aligned. The `installation-entrypoints` workflow must prove fresh-install missing status, explicit setup and real validation from an independent product directory on Linux, plus dependency-free lifecycle contracts on Linux and macOS. Windows coverage describes the supported WSL launcher contract only.

Every publication candidate also runs the built-in strict secret scan before dependency installation in GitHub Actions and during local publication preflight. The Integration Gate repeats the scan as required candidate-bound evidence. Both use `config/secret-scan.yaml`, scan final content plus `base..head` history, ignore no inline bypass markers and fail closed on incomplete input. Keep the single `repository` required-check context; the Janitor aggregate continues to carry failures.

Before committing, `aips publish preview --base <base> --change-class <class>` reports documentation closure with the rule responsible for each required file and checks the candidate Core Matrix binding. After reviewing the final change boundary, `aips publish matrix-sync --base <base>` can refresh the canonical matrix base/hash fields. This does not mark the matrix ready or reconciled.

`aips trajectory evaluate` 與 Scenario 167 是 Eval-as-CI 的 deterministic evidence；更新 trajectory schema、policy 或 publish wiring 時，必須同步執行 Integration Gate、Repository validation 與文件 impact closure。

Portable Command 變更必須同時驗證 Registry、renderer、CLI lifecycle、MCP read-only facade、ownership conflict 與相關 canonical documentation；版本更新不得把 Host-native capability 誤標為已驗證。
本機與 GitHub 必須透過 `scripts/publish_preflight.py` 共用 base/head、change class、canonical matrix 與 diff-aware documentation base。發布提案前先執行 `aips publish plan`，確認 protected branch 路由與 PR label；未帶 `AIPS_DOCS_DIFF_BASE` 的一般 validation 不得宣稱為 CI-parity 證據。

本地首次執行 Gate 前，以 Python 3.12 執行 `python3.12 bin/prepare-local-validation`。它在系統暫存目錄建立獨立 venv，安裝與 CI 相同的四份 requirements（包含 OpenAPI validator）和 Playwright Chromium，接著檢查 `ruff`、`mypy`、瀏覽器及 localhost。之後可執行 `python3.12 bin/prepare-local-validation --check-only --run --base <base-sha> --head <head-sha> --change-class core`，用既有環境執行 exact-candidate Publication Preflight 與 Gate；它會將 `PATH` 指向 venv，並以暫存 `XDG_CONFIG_HOME` 隔離測試設定。若輸出 `ENVIRONMENT_BLOCKED`，先依診斷修復執行環境，再判讀程式測試結果。`--check-only` 不安裝套件；Gate 報告路徑可用 `--output` 指定。開發時先跑受影響測試；候選 commit 固定後只執行這一次完整 Gate，不需另外先跑 `tests/validate_repository.py`。Validator 直接執行 Python helper 或 lifecycle 腳本時，同一路徑不需再對該檔案另跑 `py_compile`；相同 lifecycle 在完整 validator 中只執行一次。包裝器會另輸出 `.timing.json`，列出每個 contract 模組與 lifecycle 的耗時；CI 也會保留 `repository-validation-timing` artifact 供比較。

直接呼叫 `scripts/publish_preflight.py run` 時，也會讓子程序優先使用目前 `sys.executable` 所在的 Python 目錄。先用 `--check-only` 檢查已準備好的 venv 與瀏覽器，再跑確切候選的完整 Gate；這可避免子程序從原始 `PATH` 誤用缺少依賴的 Python，並避免因此重跑完整驗證。GitHub 僅需既有 allowlist；不要為本機依賴準備擴大永久網路權限。

建立已核准的 Large/Core PR 時，在 `gh pr create` 同一命令附上 `--label aips:large-change` 或 `--label aips:core-change`，讓首次 `opened` 事件即使用正確分類。PR number 共用併發群組；較新的 PR action 會取代同 PR 舊 run，並按最新 labels 執行。檢查最新候選 SHA 的 required aggregate，避免把被取代的執行判成測試失敗。

若 Turn Context 回報 `RETRIEVAL_CACHE_WRITE_ACCESS_DENIED`，先確認目前 Runtime 可寫入 `XDG_CACHE_HOME` 下的 SQLite 檔案、父目錄及 sidecar；沙盒不允許時，為該 Runtime 指定可寫的 `XDG_CACHE_HOME`，再重試檢索。只有索引明確回報 `INVALID` 才以 `--force` 重建。唯讀連線失敗仍依 `RETRIEVAL_CACHE_ACCESS_DENIED` 檢查讀取權限；`SEMANTIC_REFRESH_REQUIRED` 表示來源內容變更，須依 Project Intelligence 流程檢視受影響語意主題。

公開 PR 的每個新 commit 都要使用 GitHub noreply author 與 committer 身分，並避免在 commit message、Co-authored-by trailer 與差異內容寫入個人資料。先在 GitHub **Settings → Emails** 開啟 **Keep my email addresses private**，讓 GitHub 網頁/API 合併使用 noreply；再從同頁複製 GitHub 提供的 noreply 位址，執行 `git config --local user.email "<noreply 位址>"`。以 `git log -1 --format='%ae%n%ce'` 確認本機 author/committer；不要把實際位址貼進 issue、PR 描述或驗證輸出。發布 preflight 會檢查候選範圍內的所有 commit message 與身份欄位。

PR 建議使用 GitHub merge commit 合併，避免 squash 產生未受本機檢查的 co-author trailer；確認帳號已啟用 email privacy 後，執行 `gh pr merge <PR 編號> --merge`。GitHub 不接受 `--author-email` 指定 noreply 的 merge commit author；啟用 email privacy 後由 GitHub 自動選用 noreply。維護者可在 GitHub repository **Settings → General → Pull Requests** 關閉 **Allow squash merging**，讓設定與發布政策一致。若政策尚未設定，合併前須確認選擇 **Create a merge commit**。

Validation workflow 先執行快速文件影響檢查與強制候選秘密掃描，再以同一 base/head 執行 `repository_preflight.py`；三者通過後才安裝完整驗證相依套件與 Playwright。測試契約檔 `tests/validation/ears_requirement_contracts.py` 僅要求 Scenario Conformance 文件閉包；修改需求規劃功能、範本或 canonical requirement 文件仍會觸發完整 Requirement Planning 文件閉包。GitHub Actions runner 固定 Ubuntu 24.04，artifact action 固定至官方 v7.0.1 完整 SHA；升級前須確認 runner image 與 action Node runtime 支援狀態。

Browser evidence 同樣必須先通過 version 與 isolated-profile headless smoke probe；系統 Chrome 啟動層失敗應標記為 environment blocker，不得誤報成產品回歸。

Publication preflight must run against an exact, clean candidate. It verifies recursive documentation impact, placement rules, candidate head/base and Core Matrix binding before the expensive Integration Gate; a dirty workspace or stale candidate is blocked rather than silently treated as the PR revision.

For GitHub API or Connector publication, use the exact-candidate transfer guard before creating a remote commit or updating any branch ref. First run `aips publish environment`; resolve `ENVIRONMENT_BLOCKED` in a capable validation environment before interpreting the full suite. After the final changed-file list is known, run `aips publish preview --base <base-sha>` and close its documentation and Matrix requirements. Commit the candidate and run `aips publish preflight --base <base-sha> --head HEAD --output <report>`.

Run `python scripts/publication_transfer.py prepare --base <base-sha> --repository <owner/name>` in that clean checkout. It rejects a GitHub `origin` that differs from the explicit destination, a stale or dirty candidate, and API candidates with more than one commit. Upload the listed changed blobs using their complete local bytes; check every returned blob SHA. Create the proposed tree from the exact remote base tree and check its returned SHA. Record the GitHub responses in a temporary JSON receipt containing `repository`, `base_sha`, `tree_sha`, and `blobs` (path-to-SHA for every changed non-deleted path). Run `python scripts/publication_transfer.py verify --base <base-sha> --repository <owner/name> --receipt <receipt.json>`; only `READY_TO_PUBLISH` permits creating the remote commit and ref. Recheck the remote `main` SHA immediately before the ref update; a moved base requires a new local candidate and verification. Never repair a malformed published intermediate commit with another commit: the strict candidate-history scan will still reject it. Keep the receipt outside the repository and do not place credentials or file contents in it.

When public repository hardening changes, review together:

- .github/workflows/validate.yml;
- .github/dependabot.yml;
- SECURITY.md;
- requirements.txt;
- immutable full-SHA action pinning;
- explicit least-privilege workflow permissions;
- validation trigger policy: automatic on PR synchronization and main pushes, manual via workflow_dispatch, not on every standalone feature-branch push;
- concurrency cancellation so a newer candidate or classification-label validation supersedes older work, while unrelated PR label events skip the expensive Gate and cannot cancel active candidate validation;
- atomic remote branch-update practice so CI receives coherent logical states instead of file-by-file intermediate states;
- validator contracts that check policy properties rather than freezing one dependency version.
Publication Preflight 的 lifecycle fixture 會固定 Python module probe 成功，再分別模擬 loopback 與 browser 失敗，確保環境阻擋診斷不受 optional module availability 干擾；這不變更 runtime 行為。

## Validation architecture consistency

Shared Python CI bootstrap callers must declare their requirement files, tested constraints, and import smoke tests; the action runs `pip check` and does not own package versions.

`tests/validate_repository.py` classifies every OpenAPI-dependent lifecycle, including `implementation_enforcement_lifecycle.py`, under the exact candidate's optional-toolchain plan. When `needs_openapi` is false it skips those optional checks; an absent or invalid plan retains the full validation profile. The runner consumes `AIPS_CI_VALIDATION_PLAN` itself and removes it before loading contracts or launching lifecycle subprocesses, so selection metadata cannot change isolated test behavior. Secret scanning, the required repository aggregate and the Integration Gate remain mandatory.

`tests/evidence/publish_preflight_lifecycle.py` itself stays in the required aggregate under both plans. It runs OpenAPI action-level help and contract smoke only when both `openapi_spec_validator` and `jsonschema` are available; otherwise it checks top-level help and the clear missing-dependency error, with no traceback or output artifact.

The document-size audit measures tracked documentation and evidence against a 50,000-byte threshold. Oversized items are reported as non-blocking `WARN`; use the measurements to inform a later Human layering decision. The audit does not archive or move files.

Dependency updates can be classified with `python scripts/dependency_impact.py plan --ecosystem pip --name <package>`. The policy recommends evidence for each known dependency class; unknown packages default to `UNCLASSIFIED` / `HIGH`. Recommendations do not change Dependabot behavior, approve updates, or permit automatic merges.

Post-merge 的本地 `main` 與 managed installation 同步位於 `scripts/publish_post_merge.py`；`scripts/publish_preflight.py` 維持舊 CLI facade。維護此邊界時，執行 publication-preflight 與 module-extraction lifecycle，再跑完整 Core Integration Gate。

Scenario 204 的 module-extraction lifecycle 核對既有 facade 與 temporal current-mode 契約，讓內部拆分維持可回歸驗證。

Selective Validation remains in `FULL_RUN_SHADOW` until an exact-artifact cohort covers at least 30 days, enough unique pull requests, zero false-negative skips, conservative full-validation fallbacks, and deterministic full-run sampling. Each validation run retains one combined observation for 90 days. The daily Validation Observation Collector installs PyYAML from `constraints/tested.txt` before reading completed `validate.yml` runs with read-only Actions access, deduplicates reruns to the latest record per pull request, and calls `scripts/validation_graduation.py`; missing dependencies or missing, expired, cancelled, mismatched, or failed-attribution evidence blocks graduation. If a full validation fails without a validator-specific failure record, all predicted skips are conservatively treated as failed. The evaluator reports `READY_FOR_HUMAN_REVIEW` only; a Human must separately decide whether to enable selective execution. The collector never changes which checks run. Its job has a provisional 15-minute timeout: the available sample contains only two runs at about 31 seconds, too few for a reliable P95. Reassess the bound as more timing evidence accumulates. The scheduled and manual collector runs have no concurrency group because replacing a pending run could discard evidence.

`scripts/validation_taxonomy.py` checks that `config/validation-scope.yaml` and `config/validation-graduation.yaml` declare the same unique full-validation classes and path prefixes. Missing, malformed, duplicate, or divergent declarations fail closed; this audit is read-only and never enables selective execution.

`config/repository-contract.yaml` is a versioned parallel mirror of the legacy `required_files` list in `tests/validation/static_contracts.py`. The strict parser and lifecycle fixture require exact path-set parity and identical missing-file findings; the legacy list remains authoritative during this pilot. Other lists and authority cutover require a separate reviewed change.

The validation environment records exact Coverage.py and Hypothesis versions. Coverage reports branch measurements for the stable release selector without enforcing a percentage until touched-module baselines are established. Hypothesis property checks use deterministic settings. Ruff may not exceed its measured repository baseline of 872 findings; selected mypy modules keep the existing zero-error bound. Expand either scope only with a measured baseline and a small reviewed ratchet.

Repository Health reports advisory counts for workflows, validation modules, policy files and Integration Gate steps. These counts provide governance-complexity trend context and never affect health status or create a new gate. Monthly reliability reports continue collecting bounded evidence; SLO thresholds remain deferred until at least three complete monthly cohorts exist, then require human review and can only raise review flags.

Supply-chain checks use Dependency Review on PRs to block newly introduced high or critical vulnerabilities, configured CodeQL default setup for `actions` and `python`, and weekly advisory OpenSSF Scorecard reporting. The CodeQL initial validation run is asynchronous; verify its result and subsequent analysis before treating scan findings as available. Dependency Review and Scorecard actions remain pinned to full commit SHAs.

New installations request the stable channel by default and pin an exact `vX.Y.Z` tag only after verifying its commit and `VERSION`. Until a verified stable tag exists, stable installation fails closed with an explicit `--channel main` development-channel suggestion; source-checkout CI and development users pass that opt-in explicitly. Creating the first release tag remains governed by the separate signing and release approval policy.

OpenAPI validation and evidence lifecycle checks are included in the repository validation entry point; installing `requirements-openapi.txt` is required for that full validation profile.

Portable Command contract 位於 `tests/validation/portable_commands_contracts.py`，涵蓋 registry、projection install、status 與修改檔案 conflict；它不授予 merge 或 release authority。
`tests/validate_repository.py` is the stable CI/user entrypoint. Internal validation is modular:

Pull requests also run a bounded repository-preflight job in parallel with the existing validation path. Its exact-candidate findings are advisory; the required `repository` aggregate continues to depend on the complete Janitor Integration Gate and always runs the full repository validation. Label-only events skip this fast job.

- `tests/validation/static_contracts.py` — schemas, indexes, documentation and static repository contracts;
- `tests/validation/runtime_contracts.py` — Harness / Runtime / Intelligence lifecycle checks;
- `tests/validation/governance_resume.py` — approval binding and durable-run behavior;
- `tests/validation/conformance_isolation.py` — Scenario Conformance, identity and isolation checks;
- `tests/validation/syntax_contracts.py` — shell syntax checks;
- `tests/evidence/*` — focused one-to-one executable evidence.

External Eval / Red-Team Interoperability contracts are checked by `tests/validation/eval_interop_contracts.py`; focused unit and lifecycle runners are invoked by the repository validator. Keep the top-level validator as an aggregator and preserve the lifecycle evidence's isolated local HTTP fixture.

Keep the top-level validator as an aggregator. New substantial validation belongs in the narrowest existing module or a focused evidence runner rather than expanding the entrypoint back into a monolith.

When registering a lifecycle scenario, update the conformance inventory assertions in `conformance_isolation.py` and the canonical Human/Agent conformance records in the same change. The current release inventory is 37 deterministic, 128 lifecycle and 54 agent_eval scenarios (219 automated, 2 manual, 221 total).

`scripts/repository_preflight.py` 先跑快速文件／schema／diff 檢查；通過後才進入完整 lifecycle。環境缺少 localhost bind 或 browser 時回報 `ENVIRONMENT_BLOCKED`，不混稱產品測試失敗。

The public `bin/aips` launcher must remain a small argument-preserving handoff to `scripts/aips_cli.sh`; preserve source-checkout and installed-symlink entry paths. Keep that facade limited to runtime path setup and ordered loading of the `scripts/aips_cli/` modules; keep module extraction behavior-preserving and verify it from an unrelated working directory. Keep publication policy calculations in `scripts/publish_preflight_policy.py`, with Git and environment orchestration in `scripts/publish_preflight.py`. Validator imports belong to the explicit ordered `tests/validation/registry.py`; preserve import order, timing labels, error aggregation order, and the single execution owner for lifecycle evidence.

`.github/actions/aips-python-bootstrap` centralizes pinned Python setup, declared requirements/constraints and pip cache inputs for the MCP interoperability and Repository Health pilots. These workflows retain their read-only permissions and triggers. `scripts/github_ruleset_policy.py` compares complete supplied snapshots only; missing admin/bypass evidence is UNKNOWN, and the report never writes or activates repository settings.

Validation Observation treats a completed `NOT_READY` report as collected evidence, while operational errors remain blocking and `--require-ready` provides strict readiness behavior. The full repository Gate remains enabled. Dependency Review shadow results are recorded against the same candidate; the standalone high-severity check stays authoritative through the 2–4 week parity window.

Internal Retrieval Intelligence module extraction must preserve the `retrieval_intelligence.py` facade and its existing lifecycle behavior. `tests/evidence/module_extraction_lifecycle.py` verifies the storage helper exports; retrieval lifecycle and repository validation cover the existing index contract.

## Deterministic Scheduler / Integration Gate consistency

Phase 3 enforcement changes also update `scripts/implementation_enforcement.py`, its versioned report schema, Scenario 195 and the existing Integration Gate profile/lifecycle evidence. Check report-only behavior before enabling path-scoped enforcement in a project; a missing current-run command report or stale generated/OpenAPI hash must not turn into PASS. Generated hashes verify recorded provenance, not generator execution.

Keep the local publication route on one explicit checkout. Its preflight checks Python/Ruff, loopback and browser readiness before lifecycle validation, then checks changed Markdown links and builds VitePress for documentation candidates. Use `--project-root <repo>` when the installed CLI validates a separate source checkout. Core/Large labels belong on the initial PR creation request when using `gh`; a connector that cannot set labels atomically requires the label event and its own fresh CI result. After merge, update a clean local `main` with fast-forward-only when it is behind `origin/main`; preserve a backup before reconciliation and block dirty or divergent histories.


Preview 對 Core Matrix 套用與 Gate 相同的就緒條件：可執行狀態、無 blockers、實際差異已核對、base/hash 相符。同步後若仍是 DRAFT 或有待處理項目，先完成審查並清除已解決的 blocker；`READY_FOR_GATE` 不是正式 Gate PASS。

在原始碼 checkout 驗證尚未安裝的修改時，使用 `./bin/aips`，避免全域安裝的 CLI 指向另一份系統程式碼或 Matrix。受限 sandbox 若禁止 localhost bind，先用 `prepare-local-validation` 辨識 `ENVIRONMENT_BLOCKED`；恢復該能力後重新執行完整驗證，不略過測試。

被 concurrency 取消的舊 CI run 不執行 `repository` 彙總 job，現行 run 的 Janitor 失敗仍讓彙總 job 失敗。無關 PR 標籤事件會跳過 Janitor；只有該事件明確屬於無關標籤，且最新完整 Janitor 已成功、run title 綁定同一 PR/head/base/change class 時，`repository` aggregate 才以記錄在 Step Summary 的 no-op 成功結束。缺漏、失敗、取消、尚未完成或 stale evidence 均阻擋；Actions metadata 只需 repository job 的 `actions: read` 權限。檢查同一候選 SHA 的最新 required aggregate。

When deterministic scheduling or merge-candidate validation changes, review together:

- `orchestration/DETERMINISTIC_SCHEDULER.md` + `scripts/deterministic_scheduler.py`;
- `orchestration/INTEGRATION_GATE.md` + `scripts/integration_gate.py`;
- `orchestration/MULTI_REVIEW.md`, review packet/evidence helpers, and Context Manifest / Task Graph review contracts;
- `templates/review/REVIEW_REPORT.md` / evidence template and Integration Gate report contract;
- Task Graph / Validation Profile / Integration Gate Report contracts;
- Execution Isolation single-writer behavior and Run Resume semantics;
- Core Change Test Matrix reuse and exact-candidate fingerprinting;
- `bin/aips` scheduler / integration-gate / janitor routing;
- `.github/workflows/validate.yml` required `repository` aggregate compatibility;
- Scenario 135–136 lifecycle evidence and coverage registry;
- Human Architecture Overview / User Guide / Technology Guide.

Large/Core candidate 使用唯一 canonical `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`；版本化矩陣可保留作歷史，但不能取代 CI 實際讀取路徑。

Do not let the Scheduler make semantic scope decisions, and do not let Integration Gate PASS create merge/release authority.

## Branch lifecycle hygiene

Use `config/branch-lifecycle.yaml` and `scripts/branch_hygiene.py` before cleanup. Persistent operational branches are preserved; common short-lived prefixes are classified as ephemeral; unclassified branches are preserved by default. The report includes current SHA, matching merged PR state, branch age, integration status and a cleanup review recommendation. Integration recognition is conservative and squash-aware: direct ancestry is checked first, then per-commit patch equivalence, then a clean synthetic `git merge-tree --write-tree` whose result must be identical to the target tree. The policy is `report_only`; scheduled and main-push reports publish proposals and never delete refs. Cleanup requires a separate explicit workflow dispatch on protected `main` with `apply_cleanup=true`, plus the exact one-time reviewed manifest.


## Repository Health / Architecture Drift consistency

Repository-wide architecture consistency is checked by scripts/repository_health.py using config/repository-health.yaml. The detailed contract is orchestration/REPOSITORY_HEALTH.md.

It reuses the Capability Map, Scenario Conformance and Integration Gate. The explicit major-subsystem inventory lives in config/architecture-surfaces.yaml and must account for every Capability Map entry exactly once. Review inventory required paths, canonical docs, validation bindings, bounded guard/gate discovery, tests/scenario_coverage.yaml evidence, and .github/workflows/validate.yml plus config/integration-gate.yaml wiring.

Run:

    python scripts/repository_health.py audit --config config/repository-health.yaml

PASS is consistency evidence only. Repository Health is Detect + Evidence + Human Review and has no automatic remediation, code-change, PR, merge, release or publication authority. Review evidence_binding together with the sorted input manifest: clean Git must report EXACT_REVISION/revision_reproducible=true; staged, unstaged or untracked state must report DIRTY_WORKTREE/revision_reproducible=false rather than pretending the current HEAD fully reproduces the audit. CI additionally uploads repository-health-report.json as exact-candidate evidence; this artifact is observational only and grants no authority.


## Repository Health 定期維護觀測

`.github/workflows/repository-health.yml` 會每週定期執行一次 Repository Health，亦支援手動 `workflow_dispatch`。執行時只讀取目前預設分支的精確 revision，產生 `repository-health-report.json`、上傳短期 GitHub Actions artifact，並把摘要寫入 Job Summary。

- PASS：只留下觀測證據，不建立 Issue。
- DRIFT_DETECTED：依 deterministic evidence fingerprint 去重；同一 fingerprint 最多保留一個 open drift Issue，之後讓 workflow 明確失敗以顯示需要 Human review。
- Workflow 只使用 GitHub 自身控制平面發布 artifact／Issue；Repository Health detector 本身仍不需要 `OPENAI_API_KEY`、`GEMINI_API_KEY` 或其他外部 Agent/provider credential。
- 此流程沒有 `contents: write`，不會自動修改程式碼、建立 implementation PR、merge、release 或自動修復 drift。

這個排程是 maintenance observation，不是新的治理 authority。正式變更仍走既有 System Self-Improvement、validation、PR、merge 與 release 流程。


## Evolution Effectiveness monthly maintenance

`.github/workflows/evolution-effectiveness.yml` runs monthly on day 2 after the normal monthly Radar review. It reads durable Radar Issues/comments and writes a bounded `Evolution Effectiveness [monthly] YYYY-MM` Issue.

- no review flags → the metrics Issue is reconciled and closed as completed;
- one or more deterministic review flags → the metrics Issue stays/reopens for Human review;
- the workflow uses only `contents: read` and `issues: write`;
- no external Agent/provider credential is required;
- no source weight, enable/disable state, source URL or repository config is changed automatically.

This is observational maintenance evidence. Any actual source-policy adjustment remains a normal reviewed repository change.


## Monthly maintenance reliability

`.github/workflows/maintenance-reliability.yml` runs on day 3 each month after Evolution Effectiveness and supports a manual calendar-month selection. `scripts/maintenance_reliability.py` collects at most 10 pages of 100 validation runs and merged PRs, at most 200 failed-run job details, and at most 1,000 changed paths per PR.

- The report records eligible PR validation pass rate, median/P95 runtime, explicit normalized Hotfix labels, repeated paths, keyword-based failure categories, exact merge-SHA `main` push failures, and changed-file-count median/P95.
- Truncated or unavailable history, missing run timestamps or missing changed-file counts make dependent values `UNKNOWN` and set a review flag. Failure categories are name-based hints, not root-cause findings.
- The workflow publishes a Job Summary, a 90-day bounded artifact and one deduplicated monthly review Issue. It stores normalized metadata and paths, not logs, prompts, secrets or raw API responses.
- Permissions are limited to `actions: read`, `contents: read`, `pull-requests: read` and `issues: write`. The workflow cannot edit source, open implementation PRs, merge or release; all remediation requires the normal Human-reviewed change process.
- `tests/evidence/maintenance_reliability_lifecycle.py` covers metric definitions, exact-SHA matching, incomplete input handling and API response shapes. Scenario 201 records its acceptance boundary.

Candidate validation derives optional browser provisioning from the exact changed paths. The repository validator skips browser-dependent render lifecycle checks only when a valid CI plan declares `needs_browser: false`; an absent or invalid plan retains the full validation profile. The required repository aggregate, secret scan, preflight and Integration Gate remain mandatory.


## Controlled branch cleanup

一般 Branch Hygiene 仍是 `report_only`。只有在 repository maintainer 明確批准的 one-time manifest 中，AIPS 才可刪除 remote branch。

`config/branch-cleanup-manifest.yaml` 會逐筆綁定 branch name、exact expected SHA 與 merged PR evidence。Protected-main 人工 dispatch cleanup job 在刪除前會重新驗證：

- branch 仍存在且 SHA 沒有漂移；
- manifest 的 `baseline_main_sha` 必須等於此次檢查的目前 `main` tip；
- lifecycle 是 `EPHEMERAL`；
- branch 已由 local Git integration proof，或 GitHub merged PR 的 exact head SHA/ref/base 證據，確認整合進 `main`；
- manifest authorization 是 `explicit_user_request + exact_manifest_only + one_time`。

若使用 GitHub merged-PR fallback，workflow 會重新讀取該 PR，確認 `merged_at`、head SHA、head ref 與 base ref 全部符合 manifest。任何一筆失敗都會在第一個 delete 前 block 整批。清單中已有缺失的 branch 也會使整批拒絕，作為重播或上次部分執行的訊號；刪除途中若遇遠端錯誤，報告會列出已完成項目並停止，後續必須重新檢查 refs 並取得新的人類審核 manifest。Persistent、unclassified、pending 或 manifest 外 branch 一律不刪。排程、push 與未啟用 cleanup 的人工 dispatch 都只有 `contents: read`；只有 protected-main 上明確啟用 cleanup 的 job 在這份 exact manifest 範圍內取得 `contents: write`。
一般 cleanup report 另外產生 fingerprint-bound proposal，列出 branch SHA、merged PR、merged date 與產生報告時的 main SHA。Proposal 本身不會擴大既有 exact-manifest authority；main baseline 或 branch 狀態變更後須重新產生並 review。


## Runtime Content Safety Boundary

Register every new persistence or publication sink in `config/content-safety.yaml`. Preserve the `sanitize → hash → persist` ordering for audit data and update scenarios when detector or sink policy behavior changes.

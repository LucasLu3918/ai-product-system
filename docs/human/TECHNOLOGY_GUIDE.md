# AIPS Technology Guide

這份文件解釋 AIPS **目前採用的技術與架構選擇**。版本時間線不放在這裡。

## Runtime & Integration

### Turn-Aware Global Harness

AIPS 將 Runtime/User instructions、Project rules、Project Intelligence 與 AIPS protocol 組合成 bounded context。不同 Runtime 使用各自可驗證的 integration strategy。

### MCP Interoperability Gateway

MCP 提供 local stdio portable access plane，公開 Resources / Prompts / deterministic Tools。Tool-only Hosts 另以 read-only catalog/read/workflow Tools 取得相同 canonical capability context；所有 Tools 都宣告 non-destructive、idempotent、closed-world hints。Host model 負責 semantic reasoning；MCP Server 不呼叫第二個 LLM。

Cursor、Windsurf、GitHub Copilot CLI、Amp、Codex 與 generic 設定只產生 review-only payload。MCP 是新 Host 的預設接入；只有 verified per-turn hook、pre-tool guard 或 runtime-specific event source 需求才擴充 native adapter。

### Progressive Disclosure

Role、Skill、Protocol 與 Project evidence 只在 task relevant 時載入，避免把整個 system context 常駐每個 Turn。

## Project Understanding

### Project Intelligence

Stable semantic cache 保存 Architecture、Data Flow、Modules、Contracts、Tests、Security、Operations、Source Registry 與 Impact Graph。

每回合使用 bounded layered context：衍生的 Project Core capsule、task-relevant Recall 與按需 Archive pointers。Capsule 帶 source digest 且不是 canonical truth；缺少時回退到來源指標。唯讀 `aips intelligence context-audit` 可檢查 stale hash、孤兒指標、秘密路徑及 authority conflicts。

### Canonical Project Identity

Repository lineage 與 workspace identity 分離，確保 main、feature worktree 與 AIPS-managed worktree 的 durable state 不互相誤用。

### Retrieval Intelligence

Local hybrid retrieval 組合 lexical、symbols、structural relation、tests、Impact Graph 與 Git history。Optional semantic / embedding trial 不會因存在就變成 baseline requirement。

### Change Impact Guard

Existing Project mutation 前先宣告並授權 Change Boundary，使用 `IMPLEMENTATION_APPROVED` 進入核准範圍；實作後對帳 actual diff 與 declared impact，只有完整記錄 reconciliation evidence 才能標記 `READY`。

## Execution

Core、Recall 與 temporal evidence 共用硬預算；Index 開啟或查詢失敗時提供穩定診斷與修復提示，並回退至 canonical source pointers。`READY` 對帳綁定 Git base/head、乾淨且位於 head 的工作樹、實際 binary diff digest、變更路徑與宣告範圍；僅填狀態或人工提供 digest 不構成證據。

本地發布驗證可由 `bin/prepare-local-validation` 在 repository 外的暫存目錄準備 Python 3.12 venv、CI requirements 與 Chromium；`--check-only --run --base <sha> --head <sha>` 使用同一環境執行既有 `publish_preflight.py`，並把驗證設定放在暫存 `XDG_CONFIG_HOME`。檢索索引使用 `XDG_CACHE_HOME` 下可重建的 SQLite 快取，路徑不可寫時應修復快取設定並重建，不改寫 canonical Intelligence。

Temporal Change Impact 可依 Git revision 還原當時有效的 assertion 與 Impact Graph edge；canonical YAML 保留真實來源，SQLite 只作可重建的 query projection。這延伸現有 Project Intelligence，不引入外部 Graph Database。

Portable Command projections use ownership and digest checks to preserve user edits; the same Canonical Registry and renderer serve CLI and MCP without granting protected-operation authority.

Runtime adapter 偵測會優先使用命令列，再使用明確的 runtime path fallback。Shell `PATH` 整合採 explicit opt-in：互動式安裝詢問，`--configure-shell` 明確啟用，`--no-configure-shell` 明確略過；AIPS 以 ownership-marked block 與外部 metadata 實作冪等安裝及保守解除。CLI link、discoverability、shell integration、必要 Python runtime dependencies 與 Harness managed block 狀態由 `aips doctor`、`aips shell status`、`aips harness status` 與 `aips harness doctor` 分別驗證。Managed installation 會選擇 Python 3.10+（可由 `AIPS_PYTHON` 指定），並在 update／preflight 時只於依賴缺漏或既有 AIPS-owned `.venv` 解譯器過舊時修復；plain source checkout 不會隱式建立 `.venv`。

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

`aips publish preview` includes untracked and uncommitted paths in documentation and Core Matrix planning. `aips publish matrix-sync` updates the candidate binding and returns the matrix to DRAFT for review.

Merge candidate 依 change class 與 actual diff 執行 lint、type、test、repository validation 與 Core Change Matrix。

CI 在強制候選秘密掃描後先執行輕量 repository preflight，再安裝完整相依套件與 Chromium。Integration Gate 與 Repository Health 證據寫入 runner 的暫存目錄，再上傳為 artifact；驗證期間不會把報告檔寫入 checkout，避免證據輸出改變工作樹而誤判為不可重現。

Publication Preflight 是 Local／CI 共用的 candidate resolver，並在完整 Gate 前執行 diff-aware repository preflight。Change class 來自明確參數或 PR labels；Large/Core 只接受 canonical Matrix path。遠端保護查詢與 environment probe 只產生 evidence，不取得 publication authority。

Browser runtime 以 Playwright managed Chromium 為首選，system Chrome 透過 `AIPS_BROWSER_PROVIDER=system` 明確選用或作 auto fallback。Preflight 會執行 version 與 isolated-profile headless smoke probe；binary 存在但無法啟動時，結果是 `ENVIRONMENT_BLOCKED` 而非產品測試失敗。

Remote Git publication uses the built-in credential-free candidate scanner in strict mode. The Integration Gate binds the final-tree and commit-history scan to candidate, policy and scanner fingerprints; provider tools remain optional.

### Parallel Run Dashboard

The first dashboard implementation uses Python stdlib HTTP, static HTML/CSS/Vanilla JavaScript and polling. It has no frontend dependency chain, database, WebSocket or mutation endpoint. API output is a whitelist and excludes prompts, reasoning, raw output, secrets and raw paths.

## Security & Governance

### Security Assurance Level

SAL 0–4 依 product baseline 與 current change boundary 決定 assurance 強度。

### Secret Handling

Credentials 只能來自安全 runtime source；不進 Git、Prompt、logs、Project Intelligence 或 ordinary evidence。


### Resource-Scoped Authorization

Agent mutation 只在 approved resource boundary 中有效；default deny 與 evidence binding 不等於 Human decision。

### Enforceable Governance

可驗證 native Runtime hooks 可以在 protected operation 前檢查 approval binding；MCP-only 不宣稱攔截 Host native tools。

### Governance Audit Evidence

Hash chain、portable audit bundle、external anchor、key fingerprint 與 retention catalog提供可驗證 provenance；不創造 approval authority。

## Quality & Verification

Change Impact traversal 使用本地可重建索引與 canonical Impact Graph，並以 depth/node/edge budgets 限制成本。動態關係、索引失效、圖涵蓋不足與截斷必須輸出為不確定狀態；不要把 lexical candidates 當成編譯器解析或完整性證明。

Validation workflow 先執行輕量文件影響檢查，再安裝完整依賴與 Playwright；EARS validator-only 變更使用 Scenario Conformance 閉包，規劃功能與範本變更維持完整 Requirement Planning 閉包。

Eval-as-CI / Trajectory Quality Gate 以 provider-neutral trace 產生 observable evidence。Deterministic violations 可形成 `BLOCK`，效率偏差形成 `WARN` 或 `DEGRADED`；shadow mode 不授予 Git Publish 權限，Human Authority 仍是最後決策者。

### Scenario Conformance

Scenario registry 將 evidence 分成 deterministic、lifecycle、agent_eval、manual，不用「檔案存在」冒充 automated coverage。

### Agent Evaluation

需要 semantic judgment 的 case 使用 provider-neutral observable-result contract，不保存 private reasoning。

### Repository Health

Architecture Surface、documentation mapping、validation contract 與 drift evidence用 deterministic audit 檢查。

Documentation audience 掃描忽略 Git 已明確忽略的本機 metadata；未被忽略的未知 docs-root entry 仍 fail closed。

## Product Delivery

Product Delivery 把 requirement、planning、implementation、security、quality、release readiness、staging / production verification串成可追蹤生命週期，但 Production Enablement 仍需要 Human authority。

Planning Package 可用 EARS 結構表達適合的功能需求，並以 optional `REQUIREMENTS.yaml` 維護需求 ID、驗收條件與驗證方式的連結。`scripts/requirements_traceability.py` 支援 JSON PASS/FAIL 輸出與成功／失敗退出碼，供自動化工具判斷結構檢查結果。EARS 只約束敘述結構；semantic review 和實際驗證仍走既有澄清、品質規劃與 evidence 流程。

## Evolution & Maintenance

### Evolution Radar

定期收集 public-source technology evidence、dedup / provenance、deterministic pre-analysis、semantic handoff 與 Human Decision。

### Controlled Trial

TRIAL 只能在 approved scope/path 與 isolated workspace內執行；PASS 仍不是 ADOPT。

### Evidence Quality

Community signal 可用於 discovery，但高強度 adoption recommendation需要 primary-source corroboration。

## Documentation Platform

### Human Documentation Source

docs/human/*.md 是 Human canonical source。Current behavior 依 domain section維護；CHANGELOG 保存版本歷史；Conformance 保存驗證歷史。

### VitePress

Official Docs Site 使用 VitePress 1.6.x stable line，提供 sidebar、local search、per-page outline 與 GitHub Pages static deployment。Renderer 不成為另一份 Source of Truth。

Documentation Placement 將每個 behavior-bearing source 綁到 canonical Human topic；Technology Guide 的廣域 trigger surface若出現尚未映射的新 source，CI 會 fail closed，要求先更新 placement contract。每條已知 subsystem rule 也明確限制 Technology Guide 可修改的 domain，因此版本新增功能不能再任意 append 到文件尾端。
## Runtime Content Safety Boundary

The provider-neutral `scripts/content_safety.py` kernel supplies deterministic secret and baseline PII detection, provenance-aware injection signals, and sink-aware `ALLOW`, `REDACT`, `BLOCK` and `REVIEW` decisions without requiring an external model or API credential.

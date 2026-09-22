# AIPS Technology Guide

這份文件解釋 AIPS **目前採用的技術與架構選擇**。版本時間線不放在這裡。

## Runtime & Integration

### Turn-Aware Global Harness

AIPS 將 Runtime/User instructions、Project rules、Project Intelligence 與 AIPS protocol 組合成 bounded context。不同 Runtime 使用各自可驗證的 integration strategy。

Runtime adapter 偵測會優先使用命令列，再使用明確的 runtime path fallback；安裝器不會因找不到 shell `PATH` 就改寫使用者 profile。CLI 路徑與 managed block 狀態由 `aips doctor`、`aips harness status` 與 `aips harness doctor` 分別驗證。

### MCP Interoperability Gateway

MCP 提供 local stdio portable access plane，公開 Resources / Prompts / deterministic Tools。Host model 負責 semantic reasoning；MCP Server 不再呼叫第二個 LLM。

### Progressive Disclosure

Role、Skill、Protocol 與 Project evidence 只在 task relevant 時載入，避免把整個 system context 常駐每個 Turn。

## Project Understanding

### Project Intelligence

Stable semantic cache 保存 Architecture、Data Flow、Modules、Contracts、Tests、Security、Operations、Source Registry 與 Impact Graph。

### Canonical Project Identity

Repository lineage 與 workspace identity 分離，確保 main、feature worktree 與 AIPS-managed worktree 的 durable state 不互相誤用。

### Retrieval Intelligence

Local hybrid retrieval 組合 lexical、symbols、structural relation、tests、Impact Graph 與 Git history。Optional semantic / embedding trial 不會因存在就變成 baseline requirement。

### Change Impact Guard

Existing Project mutation 前先宣告 Change Boundary，實作後再把 actual diff 與 declared impact 對帳。

## Execution

### Deterministic Automation

可用固定規則完成的工作優先交給 Shell / Python / existing tooling，再把 compact structured evidence交給 model。

### Deterministic Scheduler

Planning 與 Scheduling 分離。Scheduler 根據 Task Graph dependency / boundary / state 做 deterministic dispatch。

### Execution Isolation

支援 shared、AIPS-owned Git worktree、verified sandbox。沒有可驗證 provider 時不把普通 temp directory 假裝成 sandbox。

### Runtime Resource Isolation

Parallel worktree 可取得 repository-scoped TCP port lease；跨 process allocation serialized，並保留 bounded address-in-use recovery。

### Integration Gate / Janitor

Merge candidate 依 change class 與 actual diff 執行 lint、type、test、repository validation 與 Core Change Matrix。

CI 會把 Integration Gate 與 Repository Health 證據寫入 runner 的暫存目錄，再上傳為 artifact；驗證期間不會把報告檔寫入 checkout，避免證據輸出改變工作樹而誤判為不可重現。

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

### Scenario Conformance

Scenario registry 將 evidence 分成 deterministic、lifecycle、agent_eval、manual，不用「檔案存在」冒充 automated coverage。

### Agent Evaluation

需要 semantic judgment 的 case 使用 provider-neutral observable-result contract，不保存 private reasoning。

### Repository Health

Architecture Surface、documentation mapping、validation contract 與 drift evidence用 deterministic audit 檢查。

## Product Delivery

Product Delivery 把 requirement、planning、implementation、security、quality、release readiness、staging / production verification串成可追蹤生命週期，但 Production Enablement 仍需要 Human authority。

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

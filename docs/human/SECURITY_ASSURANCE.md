# Security Assurance

Runtime Context 僅回報必要路徑、能力旗標與選擇原因；不得序列化環境變數、token、憑證檔案內容或含機密的命令輸出。

Security review depth is proportional to the actual product/feature risk. The system does not apply the same heavy security process to every change.

## Core model

Project Diagnostics 只輸出 allowlisted 狀態、穩定 reason code 與建議，不複製 Doctor 原始輸出、憑證、prompt 或來源片段；靜態 Runtime/MCP 能力不得升格為原生執行證據。

The creative executor confines writes to a declared non-Git EPHEMERAL output directory, uses create-only raster outputs, and contacts only an explicitly configured local engine.

The OpenCode native guard is a narrow runtime check, not an operating-system sandbox. Claims remain ADVISORY until direct permission-hook execution is verified; MCP/custom tools and other processes remain outside its boundary.


~~~text
Product / Feature
→ Risk Profile
→ Product Baseline SAL + Change Security Impact
→ Effective Security Assurance Level
→ Required Security Skills / Reviewer
→ Appropriate Model Tier
→ Security Evidence
→ Release Gate
~~~

SAL means **Security Assurance Level**. It is not a model tier and it is not a simple average score.



## Risk profile dimensions

Evaluate only dimensions relevant to the current product/change:

- financial / stored-value impact;
- authorization criticality;
- sensitive/personal data;
- fraud / business-logic abuse potential;
- external exposure (public API, webhook, upload, third-party integration);
- blast radius;
- irreversibility / recoverability;
- concurrency / integrity risk;
- auditability requirements;
- availability / reliability impact.

Record security assurance and reliability impact separately.

## Assurance levels

### SAL 0 — Minimal

Examples: static public content, no login, no sensitive data, no shared side effects.

Required: normal secure defaults only. No independent Security Engineer by default.

### SAL 1 — Low

Examples: low-impact personal tools, harmless frontend utilities.

Required: basic input/dependency/secret hygiene. Independent security review normally unnecessary.

### SAL 2 — Standard

Examples: authenticated CRUD, ordinary SaaS user data.

Required: authentication/authorization/data-handling review as applicable. Security Reviewer is conditional on the affected boundary.

### SAL 3 — High

Examples: privileged admin operations, sensitive data, public upload/webhook, high-impact API, broad cross-user effects.

Required when affected:
- threat model;
- independent Security Engineer review;
- authorization review;
- abuse-case analysis;
- audit logging strategy;
- security test plan;
- release security evidence.

### SAL 4 — Critical

Examples:
- payments, refunds, settlement;
- stored value / wallets;
- points, credits, vouchers or coupons convertible to economic value;
- redemption / transfer / withdrawal;
- financial state transitions;
- high-impact security boundaries where compromise could cause material loss.

Required:
- planning-stage security review;
- implementation-stage security review;
- financial/business-logic integrity analysis;
- concurrency/idempotency/replay/double-spend review where applicable;
- independent Security Engineer;
- strong security test evidence;
- unresolved High/Critical findings block release.

## Critical risk floors

Do not allow averaging to reduce a critical dimension.

Examples:

- financial/stored-value integrity = Critical → minimum SAL 4;
- high-impact privileged control plane = Critical → minimum SAL 3 (or 4 when economic/material harm is possible);
- broad exposure of highly sensitive data = Critical → minimum SAL 3/4 based on impact.

The Security Engineer records the floor and rationale.

## Product baseline vs change impact

創作可靠性 Core candidate 保留完整 Gate、媒材拒絕及取消授權回歸。損壞 PNG fixture 必須失敗；合成測試不能替代真實模型與人工品質驗收。

OpenCode local file admission is limited to directly intercepted native operations and confined resources. Readiness checks do not provide OS sandboxing and do not cover MCP/custom tools or out-of-process writes.

Change Impact approval authorizes only its reviewed scope; partial graph coverage is recorded as a limitation and reconciled against the exact candidate before publication.

Creative authorization changes traverse the OpenCode adapter, Python policy/executor, direct callers and output consumers; scoped evidence may establish only the reviewed boundary and cannot upgrade partial repository-wide coverage.

Task routing 只縮小本回合載入的 canonical 協定範圍，不會降低 SAL、授權需求、Change Impact 深度、必要測試或 Human approval。

Repository governance snapshot 透過已驗證的 `gh` 讀取 repository rulesets 與 branch protection，保留完整回應與明確 UNKNOWN 狀態；它不修改 GitHub 設定，也不代替發布核准。

Changes to validation orchestration preserve candidate secret scanning and required aggregate checks; removing redundant syntax or lifecycle invocations does not reduce security coverage.

Change Impact unknown dispositions are security-relevant evidence: closed records require current in-repository or complete scoped traversal evidence and explicit Human review. Legacy strings, stale hashes, out-of-root paths, incomplete traversals and mismatched scopes remain unresolved and fail closed.

The Phase 12 installation CLI Matrix keeps `review_evidence.required: false`; installation and contract lifecycle results are not independent semantic review or runtime attestation.

A high-risk product does not automatically require a deep SAL 4 review for every cosmetic change.

A Planning Package manifest may mark a security artifact not applicable only with a scope-specific reason. That structural status cannot lower the product SAL floor, waive an applicable security boundary review, or infer regulatory/payment compliance; preserve those decisions in the security plan and human review.

Maintain:

~~~yaml
assurance:
  product_baseline_sal: 4
  reliability_impact: 4
  change_security_impact: 1
  impacted_security_boundaries: []
  effective_sal: 1
~~~

For each change:

1. start from the product baseline and known protected assets;
2. identify which assets/boundaries are actually touched by the Change Boundary;
3. classify the change-local risk;
4. apply any critical risk floor from the impacted boundary;
5. derive Effective SAL.

If a footer text change in a payment platform does not touch any sensitive boundary, review can stay light. A change to payment state, balance, points, coupons, authorization or settlement inherits the appropriate high-risk floor.

Implementation Profile validation is structural assurance only. It preserves unresolved contract authority and unknown file ownership as blockers, and does not establish that a technology choice is safe, that verification passed, or that a migration is approved. Apply the existing SAL and Change Impact review to the actual implementation boundary.

## High-value business logic is a security boundary

For economic-value features, security review includes more than classic vulnerabilities.

Review cases such as:

- duplicate redemption / double spend;
- replayed requests or events;
- missing idempotency;
- race conditions;
- negative balance / overflow / precision / rounding;
- unauthorized cross-account access;
- coupon/referral/promotion abuse;
- refund/reversal inconsistencies;
- payment cancelled but value already granted;
- transaction/event partial failure;
- duplicate message consumption;
- audit gaps and repudiation.

## External sandbox execution


The initial E2B candidate is disabled by default and limited to synthetic or explicitly approved `public` data. Its optional API key is exposed only to a manual workflow on `main` after the operator confirms prior written provider consent. No provider key, Git publication credential or production credential is sent to the guest. The candidate uses deny-all egress, no host mounts, bounded lifetime and no publication authority.

Provider documentation and AIPS-observed integration behavior are separate evidence. A smoke-test receipt checks creation, execution, denied public egress, TTL, destruction and an unchanged host fixture; it does not prove the provider's hypervisor implementation. Registry changes or expired evidence block selection. A sandbox result remains untrusted until host-side path/content validation and existing Integration/Security gates pass.

`internal`, `confidential` and `restricted` data are blocked by the initial policy. Enabling another class requires a provider, region/BYOC, contractual data-handling review and explicit policy update. A successful smoke test alone does not make that policy change.

## Review phases

### Planning security review

SAL 3–4 planning reviews evaluate:

- assets and trust boundaries;
- threat/abuse model;
- authorization model;
- data sensitivity;
- financial/business invariants;
- API/data architecture;
- audit and observability requirements;
- recovery/rollback expectations.

### Implementation security review

Review actual:

- code;
- data transactions;
- concurrency/idempotency;
- authorization/validation;
- sensitive logs;
- secrets/config;
- tests and failure paths.

## Release Security Gate

The Gate proves candidate fitness but grants no publication or merge authority. Personal mode uses the configured `origin` as its target and accepts that a same-account Agent can rewrite `.git/config`; select high assurance or an externally protected identity anchor when that threat must be resisted.


External signed publication grant 與 validation／secret-scan evidence 一起綁定 exact candidate；Human release approval、production issuer readiness 與 GH base/tag CAS 限制需各自確認，不能由 fixture 結果推定。

原生 write Guard 的成功不會讓任意 MCP／自訂工具取得等效權限。外部動作與未知 effect 維持原 Human Gate 或 UNSUPPORTED；本地驗收報告沒有發布、發行或刪除分支權限。

Read-only Impact Graph candidates do not replace the exact-candidate secret scan, satisfy a security gate, or grant publication authority.

Core creative candidates keep local vision review opt-in, use the fixed loopback endpoint with proxy and redirects disabled, and include exact-candidate privacy and authorization evidence.

CI 在 tested constraints 下提供必要 lifecycle fixtures 使用的完整 Python 套件；候選秘密掃描及 `repository` 必要檢查不變，Node 與 Chromium 只在候選需要時安裝。

Branch and release readiness reports do not grant branch deletion, release/tag creation or merge authority.

Publication CI exports the fully provisioned Python executable as `AIPS_VALIDATION_PYTHON` after optional validation dependencies are installed, so isolated candidate fixtures use the intended environment. The workflow contract verifies this handoff precedes the deterministic Gate; strict candidate scanning and merge authority remain separate controls.


Creative Core candidates also verify grant revocation, Session-root confinement, prompt privacy, local-only discovery and create-only output recovery before publication.

Project Diagnostics PASS 不能提升 SAL、證明獨立審查或取代精確候選 Gate；未確認的 Runtime／MCP 效果維持 UNVERIFIED。

創作驗證分別記錄命令盤點、合成 tool/provider 測試、native host 驗證及真實模型推論。未提供權重時，品質／設備效能維持未驗證，不以流程通過推定改善成效。

The creative execution manifest and trace are covered by the candidate review; local image bytes and raw prompts are excluded from trace, and no external image endpoint is supported.

The new preparation path writes only fixed, new files within a non-Git EPHEMERAL scope and does not install an engine, select model weights, or perform image inference.

OpenCode evidence is host/version-scoped and does not establish OS sandboxing, MCP/custom-tool safety, or arbitrary Shell effect control; Core publication still requires the exact-candidate gate.

A blocked Unreleased/changelog check keeps the candidate out of release publication even when an unrelated maintenance PR is valid.

OpenCode 候選仍須 exact-candidate secret scanning、Core Matrix 與 required PR checks。ADVISORY instruction 不是原生 pre-tool enforcement 證據。

文件候選的 CI 也固定安裝完整 Python 驗證套件，避免安裝／migration fixture 因缺少 Playwright 或 OpenAPI 模組而無法執行必要檢查。Chromium 仍依候選需求下載；候選秘密掃描、完整 repository Gate 與明確合併授權維持原順序及阻擋規則。

Plan21 shared hash/path helpers preserve existing evidence formats and do not change fail-closed policy, authorization decisions, or publication gates.

`SYSTEM_CORE.md` 保留發布與合併邊界；Turn Context 路由和 hook 輸出皆為上下文指標，不得解讀為 publication authority。

Publication scanning excludes only validated numeric Git index/mode metadata; paths, added/removed/context lines and unknown headers remain scanned. Branch deletion verifies GitHub RS256 issuer, repository, protected main, workflow SHA, dispatch event and a proposal-bound audience. Runner flags alone grant no authority; tokens remain in memory.

Release readiness checks bind version, changelog, installer and tag policy to an exact candidate but do not create a release or tag; release publication requires separate Human authorization. Quality ratchet reports are maintenance evidence only and do not grant security assurance, publication or merge authority.

The shared CI bootstrap validates module names as Python identifiers before import, uses checked-in requirement files and constraints, and fails on inconsistent dependencies.

Scheduled reporting workflows keep repository/content permissions read-only except for narrowly scoped Issue reconciliation. A timeout bounds resource use but does not grant authority; concurrency may serialize identical-revision or same-cohort work, while distinct observation evidence remains independently reviewable. Evolution Effectiveness queues only writes to the same period Issue and preserves every pending report.

The installation-entrypoint workflow grants `contents: read` only. Its bounded per-job timeout fails that job without granting publication authority, changing the required repository Gate, or cancelling a separate run.

The parallel PR fast-feedback job has read-only repository permissions, checks the exact candidate and has no publication authority. Its outcome is advisory; mandatory secret scanning and the complete required repository gate remain in the existing validation path.

Publication environment probes fail closed only for capabilities selected by the exact candidate plan. Accepting `NOT_REQUIRED` for an unselected browser probe grants no permission and does not bypass the required repository Gate, secret scan or Human publication authority.

Omitting OpenAPI validator packages from an exact-path toolchain plan changes only OpenAPI-specific test smoke. The publication-preflight lifecycle remains required and verifies that validation stops with a clear missing-dependency diagnostic before writing output; the candidate secret scan and repository Gate remain mandatory.

The separate Validation Observation Collector also uses read-only Actions/content permissions and installs PyYAML from the tested constraints before collecting bounded evidence. Its artifact is advisory and cannot replace secret scanning, the required repository Gate, or Human review.

The publication CLI facade loads its implementation modules from the same resolved AIPS checkout before dispatch. Candidate secret scanning and the Integration Gate continue to inspect the complete candidate; module loading does not add publication authority or alter credential handling.

Post-merge reconciliation retains its clean-worktree, remote ancestry and fast-forward checks in `scripts/publish_post_merge.py`. The compatible CLI facade grants no merge, reset or release authority.

Remote Git candidates receive a credential-free strict scan over the exact final tree and complete candidate history. Release readiness checks are read-only; the tag target/SHA/VERSION checks do not verify cryptographic signatures, and the first release decision remains a separate Human-controlled step.

The public repository runs GitHub Dependency Review on pull requests (blocking newly introduced high or critical vulnerabilities) as an exact-candidate shadow alongside the required `repository` aggregate. Its standalone check remains authoritative until parity is observed and a separate reviewed change switches the canonical required path. CodeQL default setup for `actions` and `python`, and scheduled OpenSSF Scorecard reporting complement candidate secret scanning: dependency review detects vulnerable dependency deltas, CodeQL analyzes source vulnerabilities, and Scorecard reports repository supply-chain posture. Scorecard remains advisory; none of these workflows can merge, publish, or change source. Dependency Review and Scorecard actions are pinned to immutable commits with read-only permissions except the narrowly scoped SARIF upload token.

The weekly/manual security inventory adds a pinned OSV Scanner cross-ecosystem inventory and a full-history Gitleaks shadow comparison against the existing project scanner. It reports outcomes for maintainer review without PR comments or a Gitleaks artifact; failures and mismatches stay advisory. The existing required candidate secret scan and repository Gate remain the release controls, and CodeQL configuration is verified through GitHub's default setup.

The scheduled Python compatibility workflow uses `contents: read` and pinned checkout/setup-python actions. Its smoke result is supplementary; it cannot replace the exact-candidate PR Gate or grant publication authority.

Repository protection assessments are evidence-only: `scripts/repository_governance_snapshot.py` reads the GitHub rulesets and branch-protection endpoints with the local `gh` identity, fingerprints the returned evidence, and marks either unreadable endpoint `UNKNOWN`. The snapshot command has no API write path, and the comparator cannot weaken branch protection or activate a ruleset. The candidate publication flow still performs the mandatory secret scan and preserves the required `repository` Gate.

Changed-path CI planning can omit unrelated optional tools, but every publication candidate still runs the mandatory candidate secret scan, repository validation and exact-candidate Integration Gate. Unknown paths select the full toolchain.

For SAL 3–4 affected changes, persist SECURITY_REVIEW.md.

Allowed decisions:

- PASS
- PASS WITH RISK
- REQUEST CHANGES
- BLOCK

At SAL 4, unresolved High/Critical findings are **BLOCK**. They may not be downgraded to comments without an explicit accepted risk decision and applicable governance.

- The read-only readiness check blocks missing, duplicated, malformed, or non-empty `## Unreleased` sections and never creates or moves tags.
## Model routing

SAL informs, but does not equal, Model Tier.

Typical guidance:

- SAL 0–1: no dedicated high-tier security agent by default;
- SAL 2: Tier 2–3 where review is needed;
- SAL 3: Security Reviewer normally minimum Tier 3;
- SAL 4: Security Reviewer Tier 3–4; critical decisions may impose Tier 4.

Privacy, complexity, tools, context and total task cost remain part of model routing.


## Secret and credential safety

Optional creative vision review accepts only bounded local image bytes and an already-installed Ollama model over fixed loopback; proxying, redirects, cloud egress and content-bearing traces are excluded.

Creative admission stores only action grants, output limits and a prompt digest in memory; raw prompts are not written to job results or traces. Local engine discovery is version-only and does not download models or fall back to cloud providers.

Account usage windows do not expose task/model token traces; record those values only when an official per-task source supplies them.

OpenCode MCP 設定只提供 review-only 預覽，不匯入憑證、不變更模型；server workspace 固定於產生設定時的專案路徑。

Turn Context route resolution 不記錄原始 prompt；路由錯誤不得透過序列化診斷輸出敏感輸入。

Evolution local pre-analysis remains credential-free, external-network-free, read-only advisory evidence. Moving its implementation behind the existing facade adds no execution, publication, or Human-decision authority.
Public Radar Issue archives are treated as untrusted input. Restoration verifies SHA-256, limits decompressed output to 8 MiB and rejects malformed payloads before evidence parsers consume them; no credential data is included in the archive.


快取恢復不改 sandbox 權限、不複製 GitHub 憑證，也不修改明確的快取或認證設定。自動暫存 fallback 必須是目前使用者的私有目錄，拒絕 symlink；套件下載原始 stdout/stderr 只在程序記憶體中分類，不寫入持久紀錄或公開診斷。安裝同步限乾淨、同遠端與 ancestor fast-forward，禁止 reset 分歧安裝版。

隔離 AIPS 的設定目錄時，GitHub 登入查找需保留原本的設定位置；只傳遞 `GH_CONFIG_DIR` 路徑參照，不複製或列印憑證。設定位置待確認、檔案寫入、localhost 綁定、browser 啟動與 DNS／網路阻擋應分別診斷；任一測試使用較高權限成功，不代表已放寬預設沙盒政策。

The repository aggregate has read-only Actions metadata access to bind label-only success to an actual passing full Gate for the same PR/head/base/class. Failure and missing evidence stay blocking. CI diagnostic summaries contain required repository document paths and bounded test timing rather than raw authentication output or signed artifact URLs. Network allowlists remain explicit: GitHub API connectivity does not imply authorization for Azure Blob redirects. Use writable temporary cache roots for restricted runtimes; do not broaden network access to solve filesystem denial.

Required validation groups are isolated by PR event action, so a classification-label event cannot cancel an `opened` run and leave the required check without evidence. Same-action replacement remains bounded to that PR, and this scheduling change does not alter read-only workflow permissions or branch protection.

Publication Preflight places the selected Python directory first in child `PATH`, reducing unintended interpreter selection. This does not change credential handling, domain allowlists or Git publication authority. The scheduled validation-observation workflow keeps repository token permissions read-only and bounds its job to a provisional 15 minutes; its evidence artifacts remain advisory.



OpenAPI evidence validation is offline, confines local references to the repository root, invokes contract test commands without a shell, and stores output digests instead of raw stdout/stderr. These controls do not assert that the project test assertions are semantically sufficient.

Phase 3 treats unknown ownership as protected and rejects repository-path traversal or symlink escape. Explicit project-command collection refuses shell/inline code, has a timeout and keeps digest-only bounded output; the Gate does not execute candidate Profile commands. Generated-file input/output hashes and unsigned command reports provide consistency evidence only. Enforced projects must collect command reports in the current trusted run; committed reports are rejected, and Human review still decides contract authority, breaking changes and semantic quality.


Independent-review signatures use Ed25519 keys from a host-managed trust store outside the candidate repository. Without that trust anchor, review evidence remains `UNVERIFIED`; signature-shaped fields alone do not establish trusted runtime isolation.

OpenTelemetry authorization values are resolved from a named host environment variable only. They are not copied into run evidence, trace attributes or exporter errors.

外部 Eval / Red-Team 匯入採 allowlist、大小/深度限制、來源 SHA-256 與 fingerprint；YAML alias、重複鍵、自訂標籤、程式碼 provider、未知欄位、secret-like 值與 private reasoning 都會 fail closed。Promptfoo / PyRIT 不列為 AIPS 執行相依套件，也不會由 AIPS 自動執行；外部結果不能取得發布權限。詳見 `orchestration/EVAL_INTEROPERABILITY.md`。

`aips publish plan` 對失效的 GitHub CLI 認證回報 `AUTH_REQUIRED`，對 DNS／網路受限回報 `NETWORK_UNAVAILABLE`；兩者都不回傳 CLI stderr 或 token，並給出不同修復步驟。PR 分類標籤可在首次建立時帶入；Core/Large 分類標籤的新增或移除會觸發最新分級驗證，其他標籤事件不會取消進行中的 run，並略過完整 Gate。

Publication preflight reports the selected checkout root and safe environment status; browser stderr and local executable paths are not copied into its report. These diagnostics do not replace the exact-candidate secret scan or authorize publication.

The preflight's GitHub repository metadata request is read-only. It reports enabled merge methods and classifies network or repository-access errors without emitting raw CLI diagnostics or credential values; this status does not authorize publication or merging.

Publication preview 對 Matrix 未就緒原因只回報固定類別，不輸出 blocker 內容。PR lifecycle events 不會互相取消；被新 `synchronize` 取代的舊 revision 不會執行 required aggregate，而目前候選的 Janitor 失敗仍維持 fail closed。分支保護與 required `repository` context 不因併發調整而改變。

Use `orchestration/SECRET_HANDLING.md` whenever code, tests, deployment or an external integration needs credentials.

Security review verifies:

- no credential value is persisted in source, committed config, generated Intelligence/HTML, logs, fixtures, snapshots or review evidence;
- runtime acquisition uses an approved secure source;
- logs/traces/error paths redact sensitive headers/fields;
- secret scanning evidence exists where practical for general review; every Remote Git publication candidate also passes the mandatory credential-free exact-candidate scan. CI 會在這項掃描通過後執行 repository preflight，兩者都早於完整相依套件與瀏覽器安裝。

The built-in publication scan checks the final tree and all candidate commits from base to head, uses strict mode without inline bypass, and fails closed when the scan or history is incomplete. Its redacted report is bound to the scanner and policy hashes. External secret-scanning providers remain optional defense-in-depth.

若目前要求的操作明確需要 credential，且沒有 credential-free 路徑，該操作為 BLOCKED。若 credential 被宣告為 optional，則必須使用該能力定義的 `SKIPPED_NOT_CONFIGURED` / `ANALYSIS_PENDING` / `TRIAL_PENDING` 等非 PASS 狀態，且不得因此阻擋無關的 baseline validation 或 release。永遠不得以 hard-coded credential 取代缺失的 secret。

AIPS 另外使用 External Credential Dependency Guard（`config/external-credentials.yaml` + `scripts/external_credential_guard.py`）確保外部 Agent/provider Key 不會被新增成 baseline/release 必要條件，也不會暴露給 pull-request code。

For SAL 3–4 or production credentials, an active exposed credential is release-blocking until containment and required rotation/revocation are complete.

The `bin/aips` launcher resolves its own symlink target before forwarding arguments to the AIPS checkout. Security-sensitive validation, installation, and publication behavior remains in the checkout implementation; static checks and installed-entrypoint lifecycle tests cover both paths. The validator registry is explicit and ordered so security checks cannot disappear through implicit discovery.
Retrieval index storage is disposable local cache state. Refactoring its persistence helpers must preserve read-only query behavior, live-WAL refusal, source-stability checks and integrity-verified snapshots; no canonical project data or credentials are stored there.


## 可驗證治理稽核證據

高風險流程可使用 orchestration/GOVERNANCE_AUDIT.md，把 Approval、Security Review、Release Readiness、Production Promotion / Verification 等關鍵事件綁定 exact candidate 與 evidence digest。

- SAL 0–1：通常不要求。
- SAL 2：protected publish / release 可使用 credential-free SHA-256 hash chain。
- SAL 3：auditability 屬於 affected boundary 時，應保存 approval + security + release chain evidence。
- SAL 4：production-relevant governance evidence 應使用 authenticated events 與定期 asymmetric signed checkpoint；等效替代控制需有治理紀錄。

AIPS baseline 不因此要求 HMAC key、signing key 或外部 Agent/provider credential。HMAC secret 與 signing private key 必須來自安全 Runtime Source，不得寫入 Git、Prompt、log、ledger 或 Actions artifact。


## 可攜式 Governance Audit Bundle

當 SAL 3–4 或長期稽核需求需要把治理證據交給不同維護者、離線媒體或事後稽核者時，可將既有 Governance Audit Chain 匯出成 portable bundle。

Bundle 應綁定 exact Git revision、ledger event count / chain head、所選驗證或部署證據的 SHA-256，以及 checkpoint public key fingerprint。HMAC secret 與 signing private key 永遠不得被打包。

高保證情境應將 `ANCHOR.json` 與 bundle 分離保存或分發；只把 anchor 放在 bundle 內，無法單獨證明整包資料沒有被攻擊者重新製作。若 ledger 含 Ed25519 checkpoint，建立 bundle 時必須先以對應 public key 驗證成功。

Portable bundle 是 Security / Governance evidence，不是新的核准機制。


## Governance Audit Retention / Key Rotation

Portable Audit Bundles may be registered in a deterministic catalog so auditors can locate evidence by release/deployment subject, repository revision, chain head or checkpoint key ID.

The default retention durations in config/governance-audit-retention.yaml are AIPS operational defaults only; they are not legal or regulatory retention requirements. Project, contractual, legal-hold and jurisdiction-specific obligations may require longer retention.

SAL 2+ default registration requires an independently retained anchor. SAL 4 requires signed checkpoint evidence. Reusing one checkpoint key ID with a different public-key fingerprint is treated as a verification failure; rotation should use a new key ID while preserving the old public key/fingerprint long enough to verify historical checkpoints.

The retention helper never deletes evidence or grants compaction authority. Expiry only creates a Human-review action and a minimal digest record.
## Runtime Content Safety Boundary

Creative traces and tool responses exclude raw prompts, image bytes, credentials, arbitrary workflow bodies, and absolute local paths; remote image egress is not supported.

Publication scanning excludes only validated numeric Git index/mode metadata; paths, added/removed/context lines and unknown headers remain scanned. Branch deletion verifies GitHub RS256 issuer, repository, protected main, workflow SHA, dispatch event and a proposal-bound audience. Runner flags alone grant no authority; tokens remain in memory.

The Parallel Run Dashboard is loopback-only and read-only. Its projection cannot approve, retry, cancel, merge or publish, and content safety remains enforced before durable or public sinks.

AIPS applies a sink-aware Runtime Content Safety Boundary before AIPS-owned content is persisted or before candidate publication content is approved. Secrets are redacted from diagnostic sinks and blocked from durable/public sinks; deterministic PII is context- and sink-aware; external content is marked with provenance and prompt injection is reported as a signal. This boundary does not replace Human Authority, Publish Approval, native runtime hooks or repository-side secret protection.

## Runtime Policy Enforcement

### Git publication: 個人模式與高保證模式

預設的 `personal` 模式適用於個人快速開發。當 `/etc/aips/publication-authority.yaml` 不存在時，Agent 在完成既有候選／秘密掃描與明確命令檢查後，可推送至自己的工程分支並建立或更新指向遠端預設分支的 PR；使用者明確指定 local-only／不發布時則不推送。個人模式 Hook 不授權 PR merge。只有任務明確要求合併時，任務執行者才能在確認 PR 指向預設分支、head SHA 符合候選且 GitHub required checks 通過後合併。此模式接受一般個人帳號下 Agent 使用現有 GitHub 權限發布，不提供外部簽章隔離保證。

個人模式只允許目前的工程分支推送至同名遠端分支，而且只接受 fetch/push URL 相同的唯一 `origin`；支援普通 push 或精確 `--force-with-lease`。建立 PR 也限工程分支並只能以遠端即時公告的預設分支為目標。掃描起點取自遠端 HEAD 與預設分支即時 SHA，不採信本機可改寫的 `origin/HEAD`；需先取得該 SHA 對應的物件，否則拒絕發布。個人模式 Hook 拒絕合併 PR、直接推送預設分支、刪除分支、tag/release、未知命令或不乾淨／無法驗證的候選。`git commit` 的既有 staged content scan、遠端候選秘密掃描、必要本地 Gate 與 PR required checks 保持適用。個人模式不建立 `APPROVED` 紀錄或簽章。

個人模式以使用者目前設定的 `origin` 作為目標。相同帳號下的 Agent 能改寫工作區 `.git/config`，所以此模式無法保證 Agent 未把 `origin` 指向其他倉庫，也不提供抵禦惡意 Agent 外傳原始碼的隔離。使用者選擇此取捨以免快速開發前置部署可信服務；若需抵禦此風險，必須切換高保證授權或提供 Agent 無權修改的遠端身分錨點。

未來若部署高保證服務，管理者建立固定信任根即選擇 `high_assurance`。只要該路徑存在，授權便要求外部簽署的 v2 單次 grant；內容錯誤、權限不安全或服務失效一律 fail closed，不會退回個人模式。舊版有效 trust config 持續代表高保證模式。

這項個人模式是效率與隔離保證間的明確取捨。Claude／Gemini 的原生 Hook 在能力範圍內檢查命令；Codex 仍為 ADVISORY，不能宣稱 OS 級或跨工具攔截。

`aips approval propose` 建立 PENDING v2 提案；Agent 不簽發 APPROVED。
核准綁定 common Git directory／worktree 的雜湊身分、branch、完整 candidate／base SHA、
NUL-delimited files、binary diff digest、push URL、完整 argv、ref、force/delete、
遠端 tip、有效期限與 grant ID。沒有 upstream 仍以明確 base 計算差異。

範例（使用實際 SHA／ref；每次操作分別核准）：

~~~sh
aips approval propose --operation git_push --base <base-sha> --command 'git push --force-with-lease=refs/heads/feature:<expected-tip> origin <candidate-sha>:refs/heads/feature'
aips approval status --approval <signed-record.yaml> --operation git_push --command '<same-literal-command>'
aips approval verify --approval <signed-record.yaml> --operation git_push --command '<same-literal-command>'
~~~

新分支的 `<expected-tip>` 為空，保留結尾冒號。提案加入確切驗證／secret-scan evidence，
由外部管理者獨立確認 Human 身分與完整提案，再簽發。每份 grant 只涵蓋一個操作；
push、PR create、PR merge 需不同紀錄。status/verify 唯讀；PreToolUse 的 consume
在放行前原子消耗。執行失敗、timeout、取消或範圍變動必須重新簽發；不自動重試發布。
有效期限最多一小時，預設十五分鐘；服務回應含 fresh nonce 且最多六十秒。

**接入信任根**：由系統管理者在 `/etc/aips/publication-authority.yaml` 配置，
檔案與所有父路徑須 root-owned 且沒有 group/other write 權限。這不是 Agent 的部署步驟；
不可用 repo、使用者可寫的 external YAML 或環境變數替換 trust root。

~~~yaml
version: 1
endpoint: https://issuer.example.invalid
issuers:
  operator-key-id: <base64-encoded-32-byte-Ed25519-public-key>
~~~

**外部 issuer**：`scripts/publication_issuer.py` 是獨立管理主機的 reference service，
不是 Agent grant tool。私鑰、SQLite ledger、管理者 terminal 與 Human authentication
都必須在 Agent 無權存取的信任域；本機同 UID 的外部檔案不足以建立隔離。
管理者先以自有可信 UI／terminal 核准 exact proposal 和 evidence，再呼叫 grant。
HTTP API 沒有 grant endpoint；只提供 TLS 的 `/status`、`/consume`。

Issuer host 配置（root-owned、不允許 Agent 寫入；私鑰 mode 0600）：

~~~yaml
private_key: /etc/aips/issuer/replace-me-key.pem
key_id: operator-key-id
database: /var/lib/aips-issuer/grants.sqlite
tls_certificate: /etc/aips/issuer/server.crt
tls_private_key: /etc/aips/issuer/server.key
bind: 127.0.0.1
port: 8443
~~~

管理者在獨立 issuer host 執行：

~~~sh
python3 scripts/publication_issuer.py --config /etc/aips/issuer.yaml grant --proposal <reviewed-proposal.yaml> --approved-by <authenticated-human-id> --ttl 900
python3 scripts/publication_issuer.py --config /etc/aips/issuer.yaml serve
~~~

使用受信任 CA 的 HTTPS certificate（標準 TLS 驗證）；如使用 reverse proxy，必須保護
admin UI、request size／rate、timeout 與 TLS。AIPS 不產生 production signing key，
不配置人類登入，也不將 fixture key 認作 production authority。私鑰輪替由管理者更换
issuer key ID／公鑰；刪除舊公鑰撤銷舊 grant。Ledger 備份不能恢復已用授權為未用。

Client POST JSON：`version: 1`、fresh `nonce`、完整 signed `record`、
`record_digest`、`action_digest`。digest 為 canonical JSON（排序 keys、UTF-8、
無空白 separators）的 SHA-256。Service assertion 簽章涵蓋除 signature 外的所有欄位：
`version`、`nonce`、`grant_id`、相同兩個 digest、`result`、`expires_at`。
result 僅 `AVAILABLE` 或 `CONSUMED` 對應該操作；其他結果／重放／逾時一律拒絕。
signature 使用 `algorithm: ed25519`、`issuer_key_id`、`value_b64`。
Ledger 以 SQLite `BEGIN IMMEDIATE` 與 record digest 強制單次消耗，並行只能一個成功。

**作用域限制**：Git push 必須單一明確 SHA/refspec 與 exact-tip force-with-lease，
拒絕 unconditional force、mirror、followTags、隱含／多目標 ref。PR merge 必須 explicit
repo／PR number／merge method／match-head-commit；禁止 auto/admin/delete-branch。
GitHub merge base 與既存 release tag 是 preexecution observation，沒有 Git lease
等價 CAS；scope 的 `remote_state_enforcement` 明確記錄此限制。要求 atomic base/tag
不變的環境必須另用受控平台機制，不能把此觀測當成原子保證。

**相容性與復原**：unsigned v1 Git record 即使 fingerprint 正確也拒絕，需重新提出並簽發。
非 publication 的 runtime-policy legacy binding API 保留。從子目錄尋找時以 worktree root
解析 env／STATE／ACTIVE pointer；common-directory fallback 使用獨立 worktree ID 目錄，
簽章亦綁定該 ID，絕不自動共享權限。查找／簽章／service 錯誤僅輸出類型，不洩漏 payload。

**Shell／commit**：AST 只看實際命令，包括 command/process substitution；quoted heredoc
及 literal 文字不當作執行。未支援的 shell stdin/file、dynamic executable、Git alias、
env split-string、unquoted publication glob/tilde、未解析的 message expansion 一律 fail closed。
Git send-pack/http-push/receive-pack 與未綁定的 GitHub API／其他 mutation workflow 也拒絕旁路。
這是 command gate，
不是任意 Python／MCP／子程序的完整 OS sandbox。Codex/OpenCode 仍為 ADVISORY。
提交需 standalone `git commit`、明確 message/file 与已暫存內容；-a/amend/editor 等
未支援模式須改成先 stage、再 explicit message 的操作。只有 message 最後合法
Co-Authored-By trailer 的 email 可豁免 PII，原訊息 SECRET 與實際 staged blob 掃描仍執行。
唯讀 `git tag`／list／verify 不消耗 publication grant。

Creative prompt grants are recalculated from each current user response and bounded Session state; cancellation, scope expansion, unrelated work or exhausted output budgets revoke continuation without relying on transcript history.

OpenCode permission decisions refresh Context after session changes and retain fail-closed behavior on timeout or missing authorization evidence. Telemetry may record bounded runtime, governance, quality and outcome enums; prompts, images, credentials and reasoning are excluded.

Creative configure 僅接固定設定欄位並建立新版本，不開放一般 YAML 寫入。引擎仍受 local-only、offline 與 scope 限制；唯讀能力盤點不執行 provider。取消後不保留生成授權，外部工具寫入仍不在原生 guard 保證內。

OpenCode direct file permissions have separate V2 acceptance evidence; the native file guard does not intercept MCP/custom tools, arbitrary Shell subprocesses, or writes from other programs, so overall adapter governance remains ADVISORY.

Synthetic or advisory Host probes remain explicitly advisory and do not establish native policy enforcement on another platform.

Native hook adapters reject malformed input explicitly and fail closed if policy evaluation or audit persistence fails. Diagnostic logging goes to stderr; response envelopes contain a stable failure code without exposing exception text or other sensitive details.

主要模型偏好與輔助 tier 路由仍受既有 privacy、capability floor、SAL 與 reviewer independence 限制。Financial Integrity Skill 引用本文件的 SAL authority，不另外建立政策來源。

Local environment diagnostics report missing runtime/module names and remediation without exposing credentials or invoking package installation. GitHub workflow action references remain pinned to immutable commit SHAs with their declared Node runtime reviewed.

An opted-in Phase 5 generator report is ephemeral execution evidence. The inspector checks its fingerprint, revision ancestry, pinned tool and inputs, output hashes and ownership records; missing or stale evidence blocks that Profile. The shared Widgets pilot uses a local fixture token and does not establish authentication or security assurance for another product.

本機 OpenAPI generator adapter 只接受 Profile 綁定的 repository-local executable、精確 SHA-256、argv 與宣告輸入；預覽及 Integration Gate 不會執行 generator。使用者加上 `--execute` 才會啟動本機子程序。輸入以唯讀副本 staging，執行有 timeout 與產物數量／容量限制，且既有產物必須仍符合 Phase 3 ownership 與 hash。這些控制降低誤覆寫與參數注入風險，但不構成 OS sandbox；不可信 executable 仍可能存取目前使用者權限內的資源。只執行已審查及固定版本的工具。

Scheduler ownership 的 write-set authorization 目前明確標記 `ADVISORY`，不代表 runtime 已攔截檔案寫入。Task completion 仍會以 staged、unstaged 與 untracked diff 做 fail-closed 範圍檢查；不符時維持 `BLOCKED`，dirty recovery 需有人提供原因並確認接手。

The independent-review isolation mechanism is present but not enabled as a default PR requirement. The active Core Change Matrix keeps `review_evidence.required: false` until a trusted runtime-attestation verifier is configured; explicitly required reviews still fail closed when that proof is unavailable.

Before a supported tool action executes, Runtime Policy Enforcement checks the action envelope against Resource Authorization and the deterministic runtime policy. The result is `ALLOW`, `DENY`, `REQUIRE_APPROVAL` or `BLOCKED`; policy conflicts use deny-overrides. An approval binds the exact action and policy digests, destination, data labels, Change Boundary and expiry.

SAL3/4 external egress also needs a verified native hook and a fresh provider receipt proving network allowlist enforcement. The current sandbox registry has no eligible verified egress provider, so these actions remain blocked. A pre-tool shell hook cannot observe every script, child process or SDK network call.

An optional semantic provider may deny or escalate an otherwise allowed action. Its result is bound to the action digest and never overrides a deterministic denial or creates Human approval. NeMo Guardrails is not a required dependency or authorization engine.

Independent review evidence is accepted only for the exact candidate and bounded review packet. The reviewer must have a distinct execution identity and read-only authority; implementation transcripts, hidden reasoning, scratchpads and raw traces are excluded. A trusted runtime attestation verifier must validate reviewer identity and execution claims. Until one is configured, evidence remains `UNVERIFIED` and any policy-required review blocks the Gate; a self-declared signature field is not proof.
Publication Preflight 的環境診斷 lifecycle 會隔離 Python module probe，並獨立驗證 loopback/browser capability blockers；主機限制不會被記成 policy enforcement 或產品安全行為變更。

Repository validation 的時間 artifact 只記錄檢查名稱、結果和耗時，不儲存測試輸出或秘密。早期候選秘密掃描、Gate 內的強制掃描及 PR/main 的完整驗證均維持必要條件。

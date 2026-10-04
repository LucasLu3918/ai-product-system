# Security Assurance

Runtime Context 僅回報必要路徑、能力旗標與選擇原因；不得序列化環境變數、token、憑證檔案內容或含機密的命令輸出。

Security review depth is proportional to the actual product/feature risk. The system does not apply the same heavy security process to every change.

## Core model

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

Changed-path CI planning can omit unrelated optional tools, but every publication candidate still runs the mandatory candidate secret scan, repository validation and exact-candidate Integration Gate. Unknown paths select the full toolchain.

For SAL 3–4 affected changes, persist SECURITY_REVIEW.md.

Allowed decisions:

- PASS
- PASS WITH RISK
- REQUEST CHANGES
- BLOCK

At SAL 4, unresolved High/Critical findings are **BLOCK**. They may not be downgraded to comments without an explicit accepted risk decision and applicable governance.

## Model routing

SAL informs, but does not equal, Model Tier.

Typical guidance:

- SAL 0–1: no dedicated high-tier security agent by default;
- SAL 2: Tier 2–3 where review is needed;
- SAL 3: Security Reviewer normally minimum Tier 3;
- SAL 4: Security Reviewer Tier 3–4; critical decisions may impose Tier 4.

Privacy, complexity, tools, context and total task cost remain part of model routing.


## Secret and credential safety

快取恢復不改 sandbox 權限、不複製 GitHub 憑證，也不修改明確的快取或認證設定。自動暫存 fallback 必須是目前使用者的私有目錄，拒絕 symlink；套件下載原始 stdout/stderr 只在程序記憶體中分類，不寫入持久紀錄或公開診斷。安裝同步限乾淨、同遠端與 ancestor fast-forward，禁止 reset 分歧安裝版。

隔離 AIPS 的設定目錄時，GitHub 登入查找需保留原本的設定位置；只傳遞 `GH_CONFIG_DIR` 路徑參照，不複製或列印憑證。設定位置待確認、檔案寫入、localhost 綁定、browser 啟動與 DNS／網路阻擋應分別診斷；任一測試使用較高權限成功，不代表已放寬預設沙盒政策。

The repository aggregate has read-only Actions metadata access to bind label-only success to an actual passing full Gate for the same PR/head/base/class. Failure and missing evidence stay blocking. CI diagnostic summaries contain required repository document paths and bounded test timing rather than raw authentication output or signed artifact URLs. Network allowlists remain explicit: GitHub API connectivity does not imply authorization for Azure Blob redirects. Use writable temporary cache roots for restricted runtimes; do not broaden network access to solve filesystem denial.

Publication Preflight places the selected Python directory first in child `PATH`, reducing unintended interpreter selection. This does not change credential handling, domain allowlists or Git publication authority.



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

The Parallel Run Dashboard is loopback-only and read-only. Its projection cannot approve, retry, cancel, merge or publish, and content safety remains enforced before durable or public sinks.

AIPS applies a sink-aware Runtime Content Safety Boundary before AIPS-owned content is persisted or before candidate publication content is approved. Secrets are redacted from diagnostic sinks and blocked from durable/public sinks; deterministic PII is context- and sink-aware; external content is marked with provenance and prompt injection is reported as a signal. This boundary does not replace Human Authority, Publish Approval, native runtime hooks or repository-side secret protection.

## Runtime Policy Enforcement

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

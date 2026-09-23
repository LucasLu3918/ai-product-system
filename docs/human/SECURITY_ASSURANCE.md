# Security Assurance

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

A high-risk product does not automatically require a deep SAL 4 review for every cosmetic change.

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

Use `orchestration/SECRET_HANDLING.md` whenever code, tests, deployment or an external integration needs credentials.

Security review verifies:

- no credential value is persisted in source, committed config, generated Intelligence/HTML, logs, fixtures, snapshots or review evidence;
- runtime acquisition uses an approved secure source;
- logs/traces/error paths redact sensitive headers/fields;
- secret scanning evidence exists where practical.

若目前要求的操作明確需要 credential，且沒有 credential-free 路徑，該操作為 BLOCKED。若 credential 被宣告為 optional，則必須使用該能力定義的 `SKIPPED_NOT_CONFIGURED` / `ANALYSIS_PENDING` / `TRIAL_PENDING` 等非 PASS 狀態，且不得因此阻擋無關的 baseline validation 或 release。永遠不得以 hard-coded credential 取代缺失的 secret。

AIPS 另外使用 External Credential Dependency Guard（`config/external-credentials.yaml` + `scripts/external_credential_guard.py`）確保外部 Agent/provider Key 不會被新增成 baseline/release 必要條件，也不會暴露給 pull-request code。

For SAL 3–4 or production credentials, an active exposed credential is release-blocking until containment and required rotation/revocation are complete.


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

## Runtime Content Safety Boundary

AIPS applies a sink-aware Runtime Content Safety Boundary before AIPS-owned content is persisted or before candidate publication content is approved. Secrets are redacted from diagnostic sinks and blocked from durable/public sinks; deterministic PII is context- and sink-aware; external content is marked with provenance and prompt injection is reported as a signal. This boundary does not replace Human Authority, Publish Approval, native runtime hooks or repository-side secret protection.

# Changelog

## 0.5.0

### End-to-End Product Delivery

- Add a complete-product lifecycle from user intent/materials through guided planning, implementation, local verification, staging, Release Readiness, production promotion and post-deploy verification.
- Add root `PRODUCT.yaml` as the compact Product Manifest for Deployment Units, contracts, environments, commands, delivery and observability.
- Define Product Workspace as the discoverable System of Record for specifications, brand, code, tests, infrastructure, deployment and operational artifacts.
- Treat frontend/backend/worker components as independent Deployment Units without forcing separate Git repositories.
- Default to monorepo for coordinated product work; require evidence for multi-repo boundaries.

### Local, Staging and Production

- Add Local Environment, Deployment Plan and Operations Runbook templates.
- Make Local → CI → Staging → Production the default material production flow.
- Allow staging to be N/A for genuinely low-risk/simple products with a recorded reason.
- Define production completion as verified deployment plus applicable health, smoke, logs/metrics and recovery evidence.

### Release Readiness

- Add consolidated Release Readiness protocol and YAML contract for exact release candidates.
- Cover build, test, security, migration/recovery, infrastructure, staging, observability and documentation evidence.
- READY remains technical readiness and never bypasses required human/security approval.
- Apply the existing SAL 4 unresolved High/Critical hard floor without over-blocking lower SAL risk-accepted reviews.
- Material candidate changes invalidate affected readiness evidence.

### Deployment Automation

- Require complete products to create repeatable CI/CD/deployment automation appropriate to the target platform.
- Execute deployment automation when platform access and approval are available.
- Persist runnable automation and mark delivery BLOCKED when required platform access/credentials are unavailable.
- Keep production secrets outside source control.

### Deterministic Delivery Checks

- Add `scripts/check_release_readiness.py` to evaluate structured Release Readiness data before AI reasoning.
- Add READY/BLOCKED/SAL3-risk fixtures and repository validation coverage.

### Reuse and Documentation

- Extend existing Delivery Planner, Cloud Architect, SRE and `delivery-planning` Skill rather than adding new delivery/DevOps Roles.
- Update Product Creation, Planning Package, workspace state, Traditional Chinese Human Guide and architecture diagrams.
- Add product-delivery architecture SVG and scenarios through Scenario 034.


## 0.4.0

### Creative Intelligence

- Add reference-grounded Creative Direction for websites, UI, banners, hero visuals, social assets, presentations, product pages and campaigns.
- Add progressive Creative Calibration for vague visual language and aspect-level reference mixing.
- Add reusable Style Profiles as reference data rather than style-specific Skills/Roles.
- Add Visual Quality Review that adapts checks to the artifact type.
- Prioritize user-owned assets, accepted Brand/Visual Systems and explicit user intent before generic design inference.

### Brand System

- Add reusable Brand Foundation & Brand System protocol.
- Add compact BRAND_PROFILE.yaml for agent quick-load plus deeper human-readable brand guidance.
- Add Brand Foundation, Identity, Logo, Verbal, Application and Governance templates.
- Support temporary campaign overrides without silently mutating permanent brand policy.
- Reuse Product Manager/Product Designer instead of creating new Brand roles by default.

### Capability simplicity

- Add reuse-first Capability Incubation before creating or expanding Roles, Capabilities or Skills.
- Require comparison of existing responsibility, triggers, input/output, authority and review obligations.
- Prefer Reuse → Extend → New Skill → New Capability → New Role.
- Add regression checks against unknown Work Mode default roles and duplicate YAML keys.

### Deterministic Automation

- Add Deterministic Automation First for repeatable rule-based parsing, filtering, counting, validation and transformation.
- Prefer existing tools or small Shell/Python helpers before spending model reasoning/context on raw data.
- Standardize structured JSON/YAML summaries with raw evidence referenced separately.
- Define helper lifecycle: run-local → project reusable → system reusable only after demonstrated reuse.
- Add Minimum Sufficient Reasoning as a core principle.

### Human and Agent documentation

- Split Human and Agent documentation entry surfaces.
- Human-facing docs are now Traditional Chinese with English annotations for specialized terms.
- Add 5-minute Getting Started and Documentation Map.
- Keep Agent bootloader concise and protocol-driven.
- Add a source-controlled SVG architecture overview for new users.
- Extend Documentation Impact Gate to check both Human and Agent audiences.

### Regression coverage

- Add scenarios for vague visual requests, user-owned creative assets, mixed references, reusable Brand Systems, duplicate-role prevention, deterministic automation and documentation audience separation.
- Expand repository validation for creative/brand/style/automation artifacts and documentation integrity.

## 0.3.0

### Security assurance

- Add Risk-Proportional Security Assurance with Security Assurance Levels (SAL) 0–4.
- Separate Product Baseline SAL from Change Security Impact so low-risk changes in critical products remain lightweight.
- Add critical risk floors so financial/stored-value integrity cannot be averaged down.
- Add independent Security Engineer review and release gating for high/critical affected boundaries.
- Add threat-modeling, authorization-security, business-logic-abuse, financial-integrity and security-testing skills.
- Add security planning/review templates and Risk Profile schema.
- Treat payments, refunds, stored value, balances, redeemable points/credits/vouchers/coupons and similar value flows as security boundaries.
- Keep Security Assurance separate from Reliability Impact and Model Tier.

### System self-improvement governance

- Add a protected Constitution containing only fundamental human-authority, truth, safety, stop-the-line, scope-integrity and high-risk approval principles.
- Add System Self-Improvement Review for every proposed optimization to this AI Product System.
- Require analysis of appropriateness, overlap, simpler alternatives, additional optimization, compatibility, scenario/doc impact and Constitution semantics before implementation.
- Add Constitutional Change Gate with affected-Article/risk analysis and a second explicit approval.
- Prefer Skill/Template → Workflow/Work Mode → System/Orchestration → Governance → Constitution.

### Change and Git governance

- Add Core Change Approval Gate for semantically large/core changes before implementation.
- Add Git Publish Approval Gate with complete changed-file list, feature summary, validation evidence, atomic commit plan and target before remote publication.
- Group commits by logical capability/reviewability/revertability rather than by file.
- Require re-approval when approved implementation scope or publication plan materially drifts.
- Add security, core-change, Git-publish, self-improvement and constitutional regression scenarios.

## 0.2.0

- Add `aips` CLI with install, uninstall, init, update, preflight, doctor, validate and version commands.
- Add safe Update Preflight using a clean-worktree check, `git pull --ff-only`, divergence blocking and explicit major-version approval.
- Record exact AI Product System version and commit in each initialized project at `.ai/SYSTEM.yaml`.
- Add Documentation Impact Gate and source-controlled Mermaid architecture diagrams.
- Add GitHub Actions validation for repository integrity.
- Add Reproducible Planning Package for authoritative product/project planning.
- Add workspace-first persistence rule for primary planning tasks.
- Add two-stage approval: Planning Package Approval, then Implementation Readiness Approval.
- Add complete planning templates covering product, UX, key visual/visual system, architecture, API, implementation readiness and decisions/assumptions.
- Add installation/lifecycle and planning-gate regression scenarios.

## 0.1.0

- Initial governed AI Product System baseline.

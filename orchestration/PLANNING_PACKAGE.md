# Reproducible Planning Package

Use this protocol when the task creates or materially revises the **primary definition of a product/project**. Examples: a new product, a major redesign, a new platform, a major architecture/product plan, or a plan that future implementers will rely on.

Do not use it for a small bugfix, isolated API change, narrow research task, or local refactor.

## Workspace first

Before producing the authoritative planning package, resolve where it will be persisted.

- If the user explicitly provided a workspace/repository/path, use it.
- If no workspace was specified, **ask for the target workspace before creating the authoritative package**.
- Do not treat the chat transcript as the System of Record.

## Required planning artifacts

Create the smallest complete set that allows another competent AI agent or human team to reproduce substantially the same intended product.

Recommended package:

```text
planning/
├── PLANNING_INDEX.md
├── PRODUCT_PLAN.md
├── EXPERIENCE_DESIGN.md
├── VISUAL_SYSTEM.md
├── TECHNICAL_ARCHITECTURE.md
├── API_SPEC.md
├── IMPLEMENTATION_PLAN.md
├── DECISIONS_ASSUMPTIONS.md
└── security/                 # required artifacts for SAL 3–4 when applicable
```

Artifacts that are genuinely not applicable must be marked **N/A with a reason**, not silently omitted.

### PLANNING_INDEX.md

- package purpose, version and status;
- links to every authoritative artifact;
- owner/reviewer/approval state;
- applicable/N/A matrix;
- reproducibility checklist;
- unresolved blocking decisions.

### PRODUCT_PLAN.md

- vision and problem statement;
- target users/personas;
- goals and non-goals;
- scope and release boundary;
- functional and non-functional requirements;
- user stories / acceptance criteria;
- business rules and key terminology;
- constraints and success metrics.

### EXPERIENCE_DESIGN.md

- information architecture;
- key user journeys and flows;
- screen/page inventory;
- interaction states;
- responsive/accessibility behavior;
- UX rationale and edge cases.

### VISUAL_SYSTEM.md

- visual direction and reference language;
- **key visual / hero visual definition**;
- typography, color, spacing, iconography and imagery rules;
- component/design-token guidance;
- visual consistency rules;
- required asset list and generation/source notes.

When visual generation tools are available and a main visual is part of the product, persist representative key-visual assets alongside this document. If an actual visual cannot be generated in the current environment, the plan must clearly identify that missing artifact before being called fully approved.

### TECHNICAL_ARCHITECTURE.md

- system context and major components;
- Clean Architecture/DDD profile where justified;
- data model and storage;
- integrations;
- security/trust boundaries;
- observability;
- performance/scalability assumptions;
- deployment/runtime topology;
- failure/rollback considerations;
- Mermaid diagrams when useful.

### API_SPEC.md

When an API exists or is planned:

- endpoint/operation list;
- method/path/purpose;
- authentication/authorization;
- request/response schema;
- validation;
- errors/status codes;
- pagination/filtering/idempotency/versioning as applicable;
- examples;
- compatibility rules.

Prefer a machine-readable contract (OpenAPI/AsyncAPI/etc.) when appropriate, with the Markdown document explaining decisions. If there is no API, mark N/A.

### Security assurance artifacts

Classify Product Baseline SAL and Reliability Impact during planning.

- SAL 0–2: security requirements may remain in Technical Architecture when that is sufficient.
- SAL 3–4: persist the applicable security package under `planning/security/` using `templates/security/`:
  - SECURITY_PLAN.md
  - THREAT_MODEL.md
  - ABUSE_CASES.md
  - SECURITY_REVIEW.md (review evidence; planning status may remain pending until review)

For SAL 4 economic-value features, explicitly define financial/business invariants, authorization, transaction/idempotency/replay/concurrency rules, audit/reconciliation and recovery.

### IMPLEMENTATION_PLAN.md

This file initially describes **implementation readiness**, not permission to start coding:

- workstreams/components;
- dependencies;
- risks;
- testing strategy;
- milestones;
- migration/rollout/rollback;
- Definition of Done;
- expected implementation artifacts.

### DECISIONS_ASSUMPTIONS.md

Track:

- FACT;
- ASSUMPTION;
- PROPOSAL;
- ACCEPTED DECISION;
- UNKNOWN;
- deferred decisions.

No silent assumptions.

## Gate 1 — Planning Package Approval

After the package is physically persisted:

1. run cross-role consistency review, including Security Engineer planning review when Effective SAL requires it;
2. show the user the package location and concise summary;
3. surface unresolved material issues;
4. ask the user to approve/revise the **planning package**.

Do **not** begin implementation merely because planning is complete.

## Gate 2 — Implementation Readiness Approval

Only after Gate 1 is approved:

1. derive a concrete **Initial Implementation Items** list;
2. propose the **Recommended Implementation Flow / Order**;
3. identify first milestone, dependencies, tests/review and risky steps;
4. ask whether the user wants to proceed with implementation;
5. wait for explicit confirmation.

Only after Gate 2 approval may implementation begin.

## Reproducibility standard

The package is sufficient only when another competent agent/team can answer, without relying on the original chat:

- What are we building and why?
- Who is it for?
- What is in/out of scope?
- What should it look/feel like?
- What are the key flows/screens?
- What are the contracts/APIs/data rules?
- What architecture/security/performance constraints and Security Assurance Level apply?
- What decisions/assumptions remain?
- How should it be built, tested, security-reviewed, reviewed and released?
- Which artifacts are authoritative?

If those answers require hidden chat context, the planning package is incomplete.

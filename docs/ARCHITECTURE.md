# Architecture

These diagrams are source-controlled architecture artifacts. Update them when the corresponding flow changes.

## Runtime flow

```mermaid
flowchart TD
    U[User Request] --> UP[System Update Preflight]
    UP -->|clean + compatible| P[Task Preflight]
    UP -->|dirty/diverged/major change| STOP[Stop and ask for resolution]
    P --> PP{Primary planning task?}
    PP -->|yes| WS{Workspace specified?}
    WS -->|no| ASK[Ask user for planning workspace]
    WS -->|yes| PLAN[Create complete Planning Package]
    ASK --> PLAN
    PLAN --> REV[Cross-role consistency review]
    REV --> G1[Gate 1: Human approves Planning Package]
    G1 --> IR[Initial Implementation Items + Recommended Flow]
    IR --> G2[Gate 2: Human approves implementation]
    PP -->|no| D{Material decision?}
    G2 --> W[Intent + Work Mode]
    D -->|yes| H[Recommendation + Human Decision]
    H --> W
    D -->|no| W
    W --> PS[Project State]
    PS --> RA[Risk / Assurance Classification]
    RA --> I[Instruction Discovery]
    I --> C[Minimal Context Manifest]
    C --> R[Role + Skill Resolution]
    R --> E[Execution Profile]
    E --> S{Subagents useful?}
    S -->|yes| SA[Bounded Subagents with isolated context]
    S -->|no| M[Model + Tool Routing]
    SA --> M
    M --> X[Execute inside Change Boundary]
    X --> V[Independent Review]
    V --> A[Artifact / Quality Gate]
    A --> ST[Persist State + System Version/Commit]
```

## Primary planning package

```mermaid
flowchart LR
    R[Request] --> W[Resolve Workspace]
    W --> P[Product Plan]
    W --> UX[Experience Design]
    W --> VS[Visual System + Key Visual]
    W --> API[API / Contract]
    W --> TA[Technical Architecture]
    W --> IP[Implementation Readiness]
    W --> DA[Decisions / Assumptions]
    P --> IDX[Planning Index]
    UX --> IDX
    VS --> IDX
    API --> IDX
    TA --> IDX
    IP --> IDX
    DA --> IDX
    IDX --> CR[Cross-role Review]
    CR --> G1[Gate 1]
    G1 --> II[Initial Implementation Items + Recommended Flow]
    II --> G2[Gate 2]
```

## Risk-proportional security assurance

~~~mermaid
flowchart TD
    R[Product / Change] --> RP[Risk Profile]
    RP --> PB[Product Baseline SAL]
    RP --> CI[Change Security Impact]
    PB --> B{Protected boundary touched?}
    CI --> B
    B -->|no| L[Lightweight effective review]
    B -->|yes| F[Apply critical risk floors]
    F --> SAL[Effective SAL 0-4]
    SAL -->|0-1| BASE[Secure defaults / basic hygiene]
    SAL -->|2| STD[Conditional security review]
    SAL -->|3| SR[Independent Security Engineer + evidence]
    SAL -->|4| CR[Critical Security Review]
    CR --> FI[Financial / Business Integrity checks]
    FI --> G{High/Critical unresolved?}
    G -->|yes| BLOCK[BLOCK Release]
    G -->|no| PASS[Security Gate Pass]
~~~

Security Assurance Level is distinct from Reliability Impact and Model Tier. A critical product may still have a low Effective SAL for a cosmetic change that touches no protected boundary.

## Existing-project instruction resolution

```mermaid
flowchart TD
    A[System Safety / Governance] --> U[Current Explicit User Decision]
    U --> N[Nearest Scoped AGENTS.md]
    N --> ADR[Accepted ADR / Contract]
    ADR --> B[Broader Project Standards]
    B --> PS[Project-local Skills]
    PS --> GS[Global Skills]
    GS --> INF[Agent Inference]
```

## Update preflight

```mermaid
flowchart TD
    C[Mutating implementation requested] --> G{System repo clean?}
    G -->|no| STOP[Stop: resolve local changes]
    G -->|yes| F[git fetch origin/main]
    F --> M{Major version changed?}
    M -->|yes| H[Stop: review release notes + explicit allow]
    M -->|no| FF{Fast-forward possible?}
    H --> FF
    FF -->|no| STOP2[Stop: no auto merge/rebase]
    FF -->|yes| P[git pull --ff-only]
    P --> RE[Re-exec updated CLI]
    RE --> VAL[Validate system]
    VAL --> REC[Record version + commit in .ai/SYSTEM.yaml]
    REC --> OK[Implementation may begin]
```

Any change to runtime flow, planning gates, precedence, model routing, workspace contract, CLI lifecycle or release behavior must pass the Documentation Impact Gate in `docs/MAINTENANCE.md`.


## System self-improvement and constitutional governance

~~~mermaid
flowchart TD
    U[User System Suggestion] --> R[System Improvement Review]
    R --> F[Fit / overlap / simplification / extra optimization / compatibility]
    F --> C{Constitution impact?}
    C -->|no| D[Recommended Direction]
    D --> UA{User approves direction?}
    UA -->|no| REV[Revise / stop]
    UA -->|yes| CORE{Large / Core change?}
    C -->|yes| CC[Constitutional Change Proposal]
    CC --> AR[Articles + risks + lower-layer alternative]
    AR --> CA{Explicit Constitutional Approval?}
    CA -->|no| REV
    CA -->|yes| CORE
    CORE -->|yes| CP[Core Change Proposal]
    CP --> CPA{User approves scope?}
    CPA -->|no| REV
    CPA -->|yes| I[Implement]
    CORE -->|no| I
    I --> V[Tests / Review / Documentation Impact]
    V --> GP[Git Publish Proposal]
    GP --> PA{User approves publication?}
    PA -->|no| HOLD[Hold remote publication]
    PA -->|yes| PUSH[Push / PR / Release]
    PUSH --> DRIFT{Material drift?}
    DRIFT -->|yes| GP
    DRIFT -->|no| DONE[Complete]
~~~

The Constitution is the highest internal authority. Prefer lower-layer changes whenever they solve the problem.


## Creative direction and brand reuse

~~~mermaid
flowchart TD
    U[User Creative Request] --> B{Approved Brand System?}
    B -->|yes| BP[Load BRAND_PROFILE first]
    B -->|no| A[Use user assets / references]
    BP --> A
    A --> R{Direction already clear?}
    R -->|no| RR[Runtime Reference Research]
    RR --> D[2-3 Differentiated Directions]
    D --> C[Progressive Calibration]
    C --> L[Creative Direction Lock]
    R -->|yes| L
    L --> G[Design / Generate]
    G --> V[Visual Quality Review]
    V --> O[Persist artifact + direction/evidence]
~~~

Styles are reference data, not skills. Brand knowledge is project knowledge, not a global skill.

## Capability incubation

~~~mermaid
flowchart LR
    N[New capability request] --> S[Search Role/Capability/Skill indexes]
    S --> O{Overlap?}
    O -->|high| R[Reuse]
    O -->|partial| E[Extend existing]
    O -->|low| K[Create minimal Skill]
    K --> T[Scenario + Trial]
    T --> P{Distinct responsibility + authority + review?}
    P -->|no| K2[Keep as Skill/Capability]
    P -->|yes| ROLE[Promote Role]
~~~

The system prefers reuse and extension over duplicate knowledge.

## Deterministic automation

~~~mermaid
flowchart TD
    X[Task step] --> D{Rule-based and verifiable?}
    D -->|no| AI[AI reasoning]
    D -->|yes| ET{Existing tool?}
    ET -->|yes| RUN[Run tool]
    ET -->|no| H[Create small Shell/Python helper]
    H --> RUN
    RUN --> S[Structured JSON/YAML summary]
    S --> AI2[AI reads summary]
    AI2 --> RAW{Need raw evidence?}
    RAW -->|yes| E[Open targeted evidence]
    RAW -->|no| DONE[Continue]
~~~

Helper lifetime is run-local → project reusable → system reusable only after demonstrated reuse.

## Documentation audiences

~~~mermaid
flowchart LR
    CHANGE[Behavior Change] --> H{Human usage affected?}
    CHANGE --> A{Agent behavior affected?}
    H -->|yes| HD[Update Traditional Chinese Human Docs]
    A -->|yes| AD[Update concise Agent Docs]
    HD --> M[Documentation Impact Gate]
    AD --> M
~~~

Human and Agent docs are separate entry surfaces but share one behavior source.


## End-to-end product delivery

~~~mermaid
flowchart TD
    U[User Request / Assets] --> D[Guided Discovery]
    D --> PW[Product Workspace + PRODUCT.yaml]
    PW --> PP[Planning Package]
    PP --> G1[Gate 1: Planning Approval]
    G1 --> IR[Implementation Readiness]
    IR --> G2[Gate 2: Implementation Approval]
    G2 --> DU[Deployment Units]
    DU --> L[Local Environment]
    L --> T[Automated Test Pipeline]
    T --> S[Security + Independent Review]
    S --> RC[Exact Release Candidate]
    RC --> ST{Staging applicable?}
    ST -->|yes| SD[Deploy Staging]
    SD --> SV[Smoke / E2E / Security / Migration Verification]
    SV --> RR[Release Readiness]
    ST -->|no with reason| RR
    RR --> READY{READY?}
    READY -->|no| FIX[Fix / re-verify]
    FIX --> T
    READY -->|yes| AP{Production approval required?}
    AP -->|yes| HA[Human Approval]
    HA --> PROD[Production Promotion]
    AP -->|no| PROD
    PROD --> PV[Health / Smoke / Logs / Metrics]
    PV --> OK{Healthy?}
    OK -->|yes| DONE[Persist Production State + Evidence]
    OK -->|no| REC[Rollback / Roll-forward]
    REC --> PV
~~~

A complete product is not complete when code is generated. Production completion requires applicable post-deploy verification and a known recovery path.

## Product workspace and deployment units

~~~mermaid
flowchart LR
    P[Product Workspace] --> M[PRODUCT.yaml]
    P --> DOC[Docs / Brand / Decisions]
    P --> F[Frontend Deployment Unit]
    P --> B[Backend Deployment Unit]
    P --> W[Worker / Job Deployment Unit]
    P --> DB[Database / Migrations]
    P --> I[Infra / Deployment]
    F --> R{Repository strategy}
    B --> R
    W --> R
    R -->|default| MONO[Monorepo]
    R -->|evidence-driven| MULTI[Multi-Repo]
~~~

Independent deployability does not imply independent repositories.

## Release readiness

Release Readiness consolidates evidence for one exact candidate:

~~~text
Build
+ Static / Unit / Integration / Contract / E2E / Smoke
+ Security Assurance
+ Migration / Recovery
+ Infrastructure
+ Staging
+ Observability
+ Deployment / Runbook / Rollback
= READY / NOT_READY / BLOCKED
~~~

READY is technical readiness. It never bypasses required human/security approval.

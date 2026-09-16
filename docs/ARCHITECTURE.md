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

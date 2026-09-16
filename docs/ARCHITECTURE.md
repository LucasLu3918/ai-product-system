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
    PS --> I[Instruction Discovery]
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

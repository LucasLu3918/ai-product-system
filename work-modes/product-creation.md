# Product Creation

Use for a new product or major greenfield initiative.

Flow:

```text
Discovery
→ Resolve Planning Workspace
→ Product Definition
→ UX / Visual / Key Visual
→ API / Data / Architecture / Security / Test / Delivery Planning
→ Persist Reproducible Planning Package
→ Cross-role Consistency Review
→ Gate 1: Human Planning Package Approval
→ Derive Initial Implementation Items + Recommended Implementation Flow
→ Gate 2: Human Implementation Readiness Approval
→ Implementation
```

If the user has not specified where the authoritative planning package should be stored, ask for the target workspace before producing it. Chat is not the System of Record.

Ask only blocking questions at each stage. Propose professional defaults instead of asking users to supply expert architecture decisions they may not know.

Use `orchestration/PLANNING_PACKAGE.md` and `templates/planning-package/`.

The planning package must be complete enough that another competent AI agent or human team can build substantially the same intended product without relying on hidden chat context. API documentation, product plan, experience design, visual system/key visual, technical architecture, implementation planning and explicit decisions/assumptions are required when applicable; non-applicable artifacts must be marked N/A with reason.

Implementation begins only after both approval gates.

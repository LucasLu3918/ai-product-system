# Scenario 013 — Reproducible Planning Package and Two-stage Approval

Request: 「幫我完整規劃一個新購物平台，之後可能交給其他 AI 或工程團隊實作。」 No workspace is specified.

Expected:

- classify as a primary product planning/product creation task;
- before creating the authoritative plan, ask where the planning package should be persisted;
- do not treat chat as the final System of Record;
- after workspace is supplied, persist a complete planning package with product plan, UX, visual/key visual, technical architecture, API contract when applicable, implementation-readiness plan, and decisions/assumptions;
- mark genuinely non-applicable artifacts N/A with reason;
- review cross-document consistency;
- Gate 1: ask user to approve/revise the persisted Planning Package;
- do not implement after Gate 1 automatically;
- after Gate 1 approval, derive Initial Implementation Items and Recommended Implementation Flow;
- Gate 2: ask whether to proceed with implementation and wait for explicit confirmation;
- another competent agent/human should be able to reproduce substantially the same product without original chat history.

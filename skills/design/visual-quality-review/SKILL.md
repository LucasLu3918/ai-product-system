---
id: visual-quality-review
capability: design
estimated_context_cost: medium
---

# Visual Quality Review

Independently review an implemented/generated visual artifact against approved Creative Direction, Brand System, Project Visual Profile and implementation consistency.

## Common checks

- hierarchy/composition;
- typography/line-height;
- alignment / optical centering;
- spacing/vertical rhythm/edge breathing room;
- control geometry/internal padding;
- icon size/baseline;
- border/radius/shadow consistency;
- color/contrast;
- responsive/crop/safe-area behavior;
- repeated-component consistency;
- default/hover/focus/active/selected/disabled states;
- state geometry stability.

## Existing UI / V2 review

Use `orchestration/VISUAL_POLISH.md`.

For V2:

- review representative routes;
- compare component inventory to the consistency baseline;
- treat outliers as candidates, not automatic bugs;
- confirm valid variants/exceptions;
- require root-cause evidence for material findings where tooling permits;
- require rendered before/after evidence when renderable;
- do not PASS with unexplained material findings;
- verify Project Visual Profile freshness when reusable visual knowledge changed.

Return PASS / PASS WITH COMMENTS / REQUEST CHANGES / BLOCK with concrete evidence and recommendations.

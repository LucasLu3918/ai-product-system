---
id: visual-quality-review
capability: design
estimated_context_cost: medium
---

# Visual Quality Review

Independently review an implemented/generated visual artifact against its approved Creative Direction, Brand System and implementation consistency.

## Common checks

- hierarchy and composition;
- typography and line-height;
- alignment / optical centering;
- spacing, vertical rhythm and edge breathing room;
- control geometry and internal padding;
- icon size/baseline;
- border/radius/shadow consistency;
- color/contrast;
- imagery/icon consistency;
- brand adherence;
- must-have / must-avoid traits;
- asset usage;
- responsive/crop/safe-area behavior;
- hover/focus/active/disabled states;
- repeated-component consistency.

## Artifact-specific checks

- website/UI: tokens, shared components, layout, responsive states, overflow and state stability;
- banner/hero: focal point, headline/CTA readability, safe area, crop;
- social asset: thumbnail readability, platform crop, brand recognition.

For existing UI polish, use `orchestration/VISUAL_POLISH.md`: preserve the approved direction, find shared root causes first, and verify rendered screenshots/states before PASS.

Return PASS / PASS WITH COMMENTS / REQUEST CHANGES / BLOCK with concrete evidence and recommendations.

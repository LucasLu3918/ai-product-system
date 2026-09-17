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

## Rendered evidence integrity

Use `templates/design/VISUAL_AUDIT.yaml` as the existing audit/evidence container rather than creating a parallel visual-evidence subsystem.

For every material rendered capture, record:

- target route/artifact;
- viewport dimensions and label;
- interaction state;
- captured artifact path;
- relevant input assets;
- provider-neutral capture provenance including provider, source revision and capture time.

Record the independent Visual Quality Review decision and observable checks separately from deterministic evidence integrity. A screenshot file existing is never equivalent to a visual-quality PASS.

When the project can provide rendered artifacts, validate the evidence envelope with:

~~~text
python scripts/visual_evidence.py <VISUAL_AUDIT.yaml> --project <project>
~~~

This helper may reject missing artifacts, incomplete provenance, missing required viewport/state coverage, a PASS without before/after evidence, or a closed finding without implementation root-cause evidence. It does **not** inspect pixels or infer visual quality; quality remains a Visual Quality Review judgment backed by the rendered evidence.

Return PASS / PASS WITH COMMENTS / REQUEST CHANGES / BLOCK with concrete evidence and recommendations.

---
id: visual-quality-review
description: Review rendered visual quality, consistency and usability with evidence and actionable
  findings.
capability: design
estimated_context_cost: medium
triggers:
- visual_review
- brand_consistency_review
- creative_direction_review
- character_artwork_review
model_requirements:
  reasoning: high
  coding: none
  reliability: high
  minimum_tier: 2
  preferred_tier: 3
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

For Planning Package review, also compare the selected visual direction to approved product context, UX screens and stable requirement references. Report mismatches as review findings; do not let a deterministic package validator claim visual quality.

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

## Evidence protocol

Load the rendered evidence integrity section of `orchestration/VISUAL_POLISH.md` when reviewing rendered captures or closing material findings. A screenshot file or deterministic envelope PASS does not prove visual quality. Keep the independent review decision separate.

Return PASS / PASS WITH COMMENTS / REQUEST CHANGES / BLOCK with concrete evidence and recommendations.

For character-art manifests, separately inspect identity-feature consistency, pose/expression variation boundaries, style adherence, Chinese label rendering, source lineage, crop/presentation, and model-license suitability. Deterministic manifest or hash PASS proves evidence integrity only; compare the actual generated assets to the approved Character and Style Profiles before making a quality decision. Treat generation failures and unavailable local runtimes as explicit limitations, not visual PASS.

For local generated assets, inspect each rendered output against the approved Character Profile, Style Profile and Creative Direction. A valid hash, completed execution, or deterministic lifecycle test does not establish visual quality. Keep the execution manifest review `PENDING` until an independent human has inspected the image; record PASS or REVISE with concrete evidence.

Load this Skill at rendered review time. Inspect the actual image at full composition and detail scale for character identity, anatomy/hands, style adherence, costume materials, lighting, crop and artifacts. Container validity, synthetic fixtures and execution success are separate evidence. Compare the manifest-bound profile hashes, keep visual review PENDING until independent Human PASS/REVISE, and keep user acceptance separate. If image decoding/rendering is unavailable or quality fails, report that limitation and revise within the authorized scope instead of claiming completion.

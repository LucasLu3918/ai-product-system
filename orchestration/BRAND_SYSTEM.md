# Brand System Protocol

Use when the user wants to create/refine a reusable brand, or when a creative artifact must follow an existing brand.

## Principles

- Brand strategy comes before logo generation.
- User intent and owned assets are first-class inputs.
- Persist brand knowledge so future agents do not depend on the original chat.
- Load BRAND_PROFILE.yaml first; open deeper documents only when needed.
- A one-off campaign deviation is a scoped override, not a permanent brand mutation.
- Reuse Product Manager/Product Designer unless a distinct Brand role is proven necessary.

## Brand creation flow

~~~text
Brand Intent
→ Guided Discovery
→ Foundation / Positioning / Audience
→ Brand Personality + Verbal Direction
→ 2–3 Visual / Identity Directions
→ User Calibration
→ Logo / Visual Identity System
→ Brand Application Rules
→ Persist Brand System
→ Brand Consistency Review
~~~

Do not require non-expert users to know terms such as positioning, archetype or tone-of-voice in advance. Translate simple user answers into professional brand language.

## Brand package

Recommended:

~~~text
brand/
├── BRAND_INDEX.md
├── BRAND_FOUNDATION.md
├── BRAND_IDENTITY.md
├── LOGO_SYSTEM.md
├── VERBAL_IDENTITY.md
├── BRAND_APPLICATION.md
├── BRAND_GOVERNANCE.md
├── BRAND_PROFILE.yaml
└── assets/
    └── logo/
~~~

Mark non-applicable sections N/A with a reason.

## Future artifact routing

For a request such as “create a banner for Brand X”:

1. locate approved Brand System;
2. load BRAND_PROFILE.yaml;
3. load required assets;
4. open deeper brand docs only when needed;
5. create the current Creative Brief;
6. research/calibrate only what is not already decided by brand rules;
7. generate/design;
8. run Visual Quality / Brand Consistency review.

## Priority

1. current explicit user request;
2. explicit temporary approved brand override;
3. accepted Brand System;
4. accepted project Visual System / Creative Direction;
5. user-provided references/assets;
6. current market reference research;
7. generic design knowledge.

A current user request that materially conflicts with a permanent Brand System must be surfaced. Treat a one-task exception as temporary unless the user explicitly approves a permanent brand update.

## Campaign override

Record only the current scope:

~~~yaml
brand_override:
  scope: current_campaign
  reason: null
  allowed_changes: []
  protected_rules: []
~~~

Do not silently write this back into the permanent Brand System.

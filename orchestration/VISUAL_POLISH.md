# Visual Implementation Polish

Use when an existing UI looks awkward, inconsistent, misaligned or visually unfinished and the user did not ask for a redesign.

## Defaults

**Preserve Before Redesign** — keep the approved brand/creative direction unless evidence shows the direction itself is the problem.

**Consistency First** — prefer consistent typography, spacing, geometry, component behavior and state treatment.

## Modes

### V1 — Focused Repair

Use when the user identifies a specific component/page/problem.

~~~text
Target
→ load visual baseline
→ render/inspect
→ map symptom to implementation
→ root cause
→ shared/local fix
→ re-render
→ verify
~~~

### V2 — Product Consistency Sweep

Use by default for requests such as:

- “fix the weird parts of this project”;
- “make the UI consistent”;
- “clean up awkward buttons/tags/navigation”.

~~~text
Load existing Visual Knowledge/Profile
→ check staleness
→ discover representative routes/layout families
→ run application
→ capture rendered evidence
→ build Component Inventory
→ inspect DOM / computed style / tokens where available
→ build or refresh UI Consistency Baseline
→ detect visual outliers
→ validate variant / semantic exception
→ map material outlier to component/style/token
→ classify root cause
→ shared token/component fix first
→ re-render
→ before/after review
→ responsive/state matrix
→ remaining material findings?
   ├─ yes → next bounded repair round
   └─ no  → PASS
→ update Project Visual Knowledge
~~~

Do not downgrade a whole-project consistency request into a few arbitrary CSS edits.

## Input precedence

~~~text
Explicit user requirement
→ Approved Brand System
→ PROJECT_VISUAL_PROFILE / approved Visual System
→ Existing design tokens
→ Shared/Golden components
→ Majority pattern in current UI
→ professional default
~~~

Do not use generic taste when project evidence exists.

## Component Inventory

For V2, identify applicable repeated UI primitives and their variants, for example:

- Button;
- Tag / Chip / Badge;
- Input / Select / Textarea;
- Navigation item / Tab;
- Icon button;
- Card;
- Heading/body text;
- Modal/Popover;
- form controls.

Capture implementation references and, where practical, rendered/computed characteristics:

- height/min-height;
- padding;
- font size/weight/line-height;
- radius/border/shadow;
- icon size/alignment;
- layout alignment;
- state geometry.

Use deterministic inventory for repeatable CSS/token/value extraction when useful, then let design reasoning classify meaning.

## UI Consistency Baseline

If a canonical visual/design artifact exists, use it.

Otherwise infer a draft baseline from:

1. existing tokens;
2. shared components;
3. repeated majority patterns;
4. professional defaults only for unresolved gaps.

Do not ask the user for pixel values that can be safely inferred.

Persist the reusable result in the project visual profile.

## Visual Outlier Detection

An outlier is a review candidate, not automatically a bug.

~~~text
Observed difference
→ documented/semantic variant?
   ├─ yes → valid
   └─ no
      → approved exception?
         ├─ yes → valid
         └─ no → potential finding
~~~

Examples of suspicious outliers:

- isolated control height/radius/padding;
- selected state changing overall geometry;
- one tag family using a different baseline;
- one navigation item touching a divider;
- arbitrary offsets/transforms compensating for shared layout.

## Root Cause Mapping

A material visual finding should be traced, when tooling permits, to:

- rendered symptom;
- DOM/element;
- component/source;
- CSS rule/class;
- computed style;
- design token/variable;
- inheritance/layout mechanism;
- pseudo-element/state rule.

Avoid solving a shared layout issue with a page-specific nudge.

## Shared root cause first

Prefer:

1. design token / CSS variable;
2. shared component;
3. defined component variant;
4. page-specific adjustment only for a real exception.

Avoid accumulating arbitrary pixel nudges, transforms or selector-specific patches.

## State Geometry Stability

Review applicable:

- default;
- hover;
- focus;
- active;
- selected;
- disabled.

State changes should not unexpectedly shift width, height, padding, baseline or position.

Intentional state geometry changes must be a defined variant/interaction behavior.

## Rendered evidence

When the application can render, source-only review cannot PASS.

Use:

- before evidence;
- after evidence;
- representative desktop;
- mobile;
- tablet when materially different;
- relevant interaction states.

If rendering is unavailable and visual correctness cannot be verified, use BLOCKED or REQUEST CHANGES rather than claiming success. Ask for the smallest missing runtime/screenshot evidence.

## Representative routes

Do not blindly screenshot every route.

For V2:

1. discover routes/layout families;
2. select representative pages for dashboard/list/detail/form/auth/settings/etc. as applicable;
3. add directly affected pages;
4. after shared fixes, smoke-check additional routes when useful.

Persist representative routes for reuse.

## Project Visual Knowledge

Use `docs/design/PROJECT_VISUAL_PROFILE.yaml` as the canonical quick-load artifact when visual consistency knowledge is worth persisting.

It may contain:

- direction/archetype and confidence;
- tokens/typography/spacing;
- component variants;
- Golden Components;
- representative routes;
- state rules;
- valid exceptions;
- must-avoid patterns;
- verified commit/watch scope.

Subjective style labels remain `inferred` until approved. Objective facts can be persisted directly.

If an existing authoritative Visual System already contains equivalent information, prefer a pointer rather than duplication through `orchestration/PROJECT_KNOWLEDGE.md`.

## Deterministic Project Visual Profile freshness

When docs/design/PROJECT_VISUAL_PROFILE.yaml exists, evaluate its reusable design-state before rescanning the whole UI:

~~~text
python scripts/visual_profile.py status --project <project> --format json
~~~

The helper must load the profile first and compare last_verified_commit plus watch.paths against real Git history and dirty state.

- REUSE: watched visual sources are unchanged. Reuse Golden Components, representative routes, state rules and approved exceptions; do not rebuild the full baseline.
- TARGETED_REFRESH: watched tokens/shared components/global visual sources changed. Refresh only the affected visual knowledge and then perform the required rendered checks.
- FULL_DISCOVERY: the profile is missing, explicitly stale, lacks a usable baseline/watch scope, or its baseline cannot be reconciled safely.

This helper is design-state freshness evidence only. It never replaces rendered before/after, responsive, crop/safe-area or interaction-state review when the application can render.

## Completion

V2 cannot PASS until applicable:

- representative routes inspected;
- component inventory established;
- material outliers classified;
- variants/exceptions respected;
- shared root causes fixed first;
- rendered before/after evidence reviewed;
- responsive/state stability verified;
- no unexplained material visual finding remains;
- visual knowledge/profile refreshed if affected.

If consistency repair reveals the underlying direction itself is wrong, stop and return to Creative Direction / Calibration rather than silently redesigning.

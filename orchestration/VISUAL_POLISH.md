# Visual Implementation Polish

Use when an existing UI looks awkward, inconsistent, misaligned or visually unfinished and the user did not ask for a redesign.

## Defaults

**Preserve Before Redesign** — keep the approved brand/creative direction unless the evidence shows the direction itself is the problem.

**Consistency First** — when no special instruction exists, prefer consistent spacing, typography, geometry, component behavior and state treatment across the product.

## Trigger examples

- “This page looks weird.”
- “Please clean up inconsistent styling.”
- buttons/tags/nav items look visually off;
- text/icon baselines do not align;
- controls touch container edges;
- hover/active/focus states shift layout;
- desktop/mobile implementations drift from the approved design.

## Polish loop

~~~text
Load Brand / Visual / Creative Direction
→ Run the current UI
→ Capture/inspect rendered states
→ Visual Implementation Audit
→ Find shared root cause
→ Fix Token / Shared Component first
→ Fix page-specific exception only when justified
→ Re-render
→ Screenshot / Responsive / State verification
→ Visual Quality Review
→ repeat only for remaining material findings
~~~

## Audit checklist

Check applicable items:

- alignment and optical centering;
- typography size/weight/line-height;
- vertical rhythm and whitespace;
- control height and internal padding;
- icon size/baseline/stroke consistency;
- border/radius/shadow consistency;
- container/edge breathing room;
- active/hover/focus/disabled states;
- responsive wrapping/overflow;
- repeated-component consistency;
- contrast/accessibility;
- visual hierarchy.

## Shared root cause first

Prefer:
1. design token / CSS variable;
2. shared component;
3. component variant;
4. page-specific adjustment only when the page is genuinely exceptional.

Avoid accumulating one-off pixel nudges, transforms or selector-specific overrides that merely hide a shared inconsistency.

## Rendered evidence

Do not declare visual polish complete from source inspection alone when the environment can be rendered.

Verify representative:
- desktop;
- mobile;
- tablet when materially different;
- default / hover / focus / active / disabled states when relevant.

Use screenshots or browser-rendered evidence. Compare against the approved visual system and user-provided references, not generic personal taste.

## Escalate to redesign only when needed

If fixing consistency cannot satisfy the user because the underlying visual direction is wrong, stop and return to Creative Direction / Calibration rather than silently redesigning.

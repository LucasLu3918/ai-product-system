# Scenario 056 — Project Visual Profile Reuse

A previous V2 sweep created docs/design/PROJECT_VISUAL_PROFILE.yaml.

Expected:
- next Agent loads it before rescanning the whole UI;
- reuse Golden Components, representative routes, state rules and exceptions;
- if watched visual sources are unchanged, do not rebuild the entire baseline;
- if shared tokens/components changed, targeted refresh the profile;
- subjective style archetype remains inferred until approved.

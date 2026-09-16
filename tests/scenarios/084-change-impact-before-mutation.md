# Scenario 084 — Change Impact Before Mutation

An existing-project mutation changes an API, persistence shape and emitted event.

Expected:
- load relevant Project Intelligence before editing;
- define the Change Boundary;
- assess applicable Input / Output / Data / Event / Consumer / Security / Invariant / Migration / Test / Observability / Documentation impact;
- persist the Change Impact artifact and make required impact READY before mutation;
- implement only within the declared boundary;
- reconcile the actual diff against declared impact afterward;
- if material impact expands beyond the declared/approved boundary, stop affected continuation, update impact, rerun required verification and obtain scope reapproval when required;
- refresh affected Intelligence after the verified change.

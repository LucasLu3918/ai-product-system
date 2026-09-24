# Scenario 084 — Change Impact Before Mutation

An existing-project mutation changes an API, persistence shape and emitted event.

Expected:
- load relevant Project Intelligence before editing;
- define the Change Boundary;
- assess applicable Input / Output / Data / Event / Consumer / Security / Invariant / Migration / Test / Observability / Documentation impact;
- persist the Change Impact artifact and complete scope review before mutation;
- record user scope authorization and use IMPLEMENTATION_APPROVED to begin the approved work;
- implement only within the declared boundary;
- reconcile the actual diff against declared impact afterward;
- mark READY only after recording full base/head SHAs, confirming a clean checkout and head match, hashing the actual binary Git diff, recording its exact changed-file set, checking all changed paths against declared target_paths, and attaching Impact Graph review/evidence;
- reject READY when a revision is unresolved, the digest/path set is forged or incomplete, HEAD differs, or the worktree is dirty;
- if material impact expands beyond the declared/approved boundary, stop affected continuation, update impact, rerun required verification and obtain scope reapproval when required;
- refresh affected Intelligence after the verified change.

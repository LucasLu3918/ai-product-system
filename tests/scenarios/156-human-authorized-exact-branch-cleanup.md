# Scenario 156 — Human-authorized Exact Branch Cleanup

## Intent

AIPS MAY delete integrated ephemeral remote branches only when an explicit Human-authorized one-time manifest binds each exact branch name and SHA. General branch hygiene remains report-only.

## Expected behavior

- keep ordinary branch classification and scheduled hygiene reporting read-only;
- preserve `main`, persistent operational branches, unclassified branches, and non-integrated branches;
- require an exact cleanup manifest with `explicit_user_request`, `exact_manifest_only`, and `one_time=true`;
- bind every approved deletion to branch name, full expected SHA, and merged-PR evidence;
- preflight the complete batch before any deletion;
- block the entire batch if any present ref moved, is not EPHEMERAL, or is not deterministically integrated into `main`;
- treat already-absent approved refs as idempotent `ALREADY_ABSENT`;
- allow deletion only from the protected-main push cleanup job;
- give only that cleanup job `contents: write`; scheduled/manual report jobs remain `contents: read`;
- never delete a branch that is absent from the exact manifest;
- preserve Human authority for any future cleanup manifest.

## Rationale

Repository branch residue should be removable without turning a read-only classifier into broad autonomous deletion authority.

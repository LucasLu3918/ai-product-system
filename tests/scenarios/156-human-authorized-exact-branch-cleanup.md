# Scenario 156 — Human-authorized Exact Branch Cleanup

## Intent

AIPS MAY delete integrated ephemeral remote branches only when an explicit Human-authorized one-time manifest binds each exact branch name and SHA. General branch hygiene remains report-only.

## Expected behavior

- keep ordinary branch classification and scheduled hygiene reporting read-only;
- preserve `main`, persistent operational branches, unclassified branches, and non-integrated branches;
- require an exact cleanup manifest with `explicit_user_request`, `exact_manifest_only`, and `one_time=true`;
- require `baseline_main_sha` to match the current target branch tip before any deletion;
- bind every approved deletion to branch name, full expected SHA, and merged-PR evidence;
- preflight the complete batch before any deletion;
- accept either local deterministic integration proof or revalidated GitHub merged-PR evidence whose merged state, exact head SHA/ref, and base ref match the manifest;
- block the entire batch if any present ref moved, is not EPHEMERAL, or is not deterministically integrated into `main`;
- reject any absent manifest ref before deleting any other branch; missing refs indicate replay or a partially applied manifest and require a newly reviewed exact list;
- if a remote deletion fails after earlier rows succeeded, report the rows already deleted, stop immediately, and block replay of the original manifest;
- allow deletion only from an explicit workflow dispatch on protected `main` with `apply_cleanup=true`;
- give only that cleanup job `contents: write`; scheduled, push-triggered and ordinary manual report jobs remain `contents: read`;
- never delete a branch that is absent from the exact manifest;
- preserve Human authority for any future cleanup manifest.

## Rationale

Repository branch residue should be removable without turning a read-only classifier into broad autonomous deletion authority.

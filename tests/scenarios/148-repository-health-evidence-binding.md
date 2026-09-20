# Scenario 148 — Repository Health Evidence Binding and Dirty Workspace Truth

## Goal

Repository Health evidence must identify every source-controlled file that can affect the configured audit, bind those inputs deterministically, and truthfully distinguish an exact clean Git revision from a dirty or non-Git workspace.

## Given

- Repository Health already performs credential-free deterministic drift detection;
- the audit reads Capability Map targets, configured capability surfaces, bounded discovered guard/gate files, documentation bindings, Scenario Conformance inputs/evidence references, and Integration Gate/repository-validation contract files;
- local developer workspaces may contain staged, unstaged, or untracked changes.

## Then

- the report contains a sorted complete input manifest with path, role, existence state, and sha256 digest for every existing bound file;
- missing bound files remain visible in the manifest with exists=false and digest=null;
- the manifest has a deterministic digest;
- an evidence fingerprint binds repository revision, workspace binding state, dirty paths, input-manifest digest, and drift result;
- a clean Git workspace reports EXACT_REVISION and revision_reproducible=true;
- a dirty Git workspace reports DIRTY_WORKTREE and revision_reproducible=false without falsely calling the evidence exact-revision reproducible;
- a non-Git fixture reports NO_GIT rather than inventing a revision;
- restoring identical content returns the exact same deterministic report/fingerprint;
- dirty-state truth does not automatically mutate files or grant implementation/PR/merge/release/publication authority.

## Boundary

Dirty workspace state is evidence metadata, not architecture drift by itself. Version 1 remains Detect + Evidence + Human Review only. No external Agent/provider credential or network call is introduced.

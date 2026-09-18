# Scenario 128 — Just-in-Time Retrieval Intelligence

For an initialized existing project, AIPS keeps Project Intelligence as the stable evidence/authority layer and uses a rebuildable Retrieval Intelligence cache to assemble task-specific repository evidence.

A retrieval turn must:

- retrieve the relevant implementation and associated test evidence without preloading unrelated modules;
- include relevant Git history when the task terms match a prior change;
- preserve path/line or commit provenance, content hash and current workspace revision;
- honor a bounded token budget;
- incrementally refresh changed or dirty files before returning evidence;
- exclude secret/credential paths from indexing and output;
- degrade truthfully when no optional semantic provider is configured;
- expose the bounded result through the Turn Context Manifest without making the retrieval cache a source of truth.

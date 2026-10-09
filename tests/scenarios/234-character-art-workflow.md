# Scenario 234: Local Character Artwork Provenance and Composition

## Given

- a character identity profile referencing hashed local SVG/PNG identity sources;
- a style profile with stable rendering guidance and a typeset-label policy;
- optional collection style-lock constraints and character acceptance criteria;
- separate character artwork files and a manifest containing local runtime/model/license provenance.

## When

- the artwork validator inspects the manifest and local files;
- the deterministic composer creates a character sheet;
- optional Creative Evidence links the manifest bytes by SHA-256.

## Then

- paths remain within the project and symlink escapes are rejected;
- SVG active content and malformed PNG chunks are rejected;
- dimensions, file hashes, reference lineage, provider, egress policy, and license provenance are checked;
- Traditional Chinese labels are typeset into stable SVG output and repeated composition is byte-identical;
- existing source/output files are never overwritten;
- a passing structural result explicitly does not infer character identity fidelity or visual quality.
- compiled prompts are deterministic and bounded; profile hashes identify the source inputs without retaining prompt text in execution manifests;
- model capability advice requires local availability, verified license and human-reviewed quality evidence and never changes the selected model;
- optional local vision assistance writes an advisory-only report and cannot mark Human review or user acceptance complete.

## Evidence boundaries

The lifecycle uses synthetic fixtures only. It does not install or invoke ComfyUI/MFLUX, download model weights, call cloud/paid APIs, evaluate actual character consistency, or claim device performance. Real outputs require a separate visual-quality-review and measured runtime evidence.

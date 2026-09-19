# Scenario 134 — Provider-Neutral Local-First Embedding Retrieval Trial

After Scenario 133 proves the remote embedding Trial boundary, AIPS may remove remote credentials as the default blocker by introducing a provider-neutral embedding Trial whose default provider executes locally.

The infrastructure must:

- default to a local embedding provider that requires no API credential;
- pin the local embedding runtime dependency, model identifier and exact model revision;
- allow model artifact download on the dedicated Trial runner while keeping embedding inference runner-local;
- keep AIPS repository/product source transfer forbidden; only the committed synthetic Retrieval Quality fixture participates in the Trial;
- retain the existing remote OpenAI-compatible adapter as an explicit optional provider selected through configuration/environment, not as the default dependency;
- keep missing remote credentials truthful as `TRIAL_PENDING`, while local model dependency/download/runtime failures become `TRIAL_BLOCKED`;
- reuse the same 9-case corpus, current Retrieval baseline, quality thresholds and required-case regression checks without weakening them;
- keep vectors ephemeral/in-memory and avoid introducing a Vector DB;
- keep normal Pull Request/main validation and normal Retrieval/Turn Context free from embedding model execution;
- publish provider mode, execution location, credential requirement, privacy boundary and next action in the Human-readable Job Summary;
- permit PASS or FAIL as evidence only, with no automatic provider/default enablement;
- require a separate Human Adoption Decision before any production embedding lane or production source transfer is enabled.

# Scenario 133 — Remote Embedding Retrieval Trial Readiness

After the deterministic Semantic Alias Expansion candidate is held, AIPS may prepare a real remote embedding Retrieval candidate Trial without changing normal Retrieval Intelligence.

The infrastructure must:

- reuse an approved protected CI secret reference instead of storing a credential in repository content;
- use a provider adapter with an explicit endpoint/model contract and bounded request/chunk/input limits;
- transfer only the committed synthetic Retrieval Quality fixture during the Trial; AIPS repository/product source transfer remains forbidden;
- keep normal Pull Request and main validation free from external embedding calls;
- run automatically only on the dedicated Trial feature branch or by explicit workflow dispatch;
- report missing credentials as `TRIAL_PENDING` and provider/runtime failures as `TRIAL_BLOCKED`;
- keep normal Retrieval/Turn Context unchanged and keep provider/default enablement false;
- preserve the current 9-case corpus, Structural Retrieval baseline and required-case regression checks;
- permit PASS or FAIL as evidence, but never convert either result into automatic adoption;
- require a separate Human Adoption Decision before any embedding lane or production source transfer is enabled.

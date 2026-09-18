# Scenario 130 — Structural Retrieval Candidate Trial

AIPS can replay the pre-adoption Structural Retrieval candidate comparison against the committed Retrieval Quality corpus. The trial remains evidence of why the capability was adopted; it does not itself grant adoption or publication authority.

The candidate trial must:

- explicitly disable structural retrieval for the baseline and explicitly enable it for the candidate, independent of the current production default;
- seed from exact symbol definitions and follow exact identifier references through one bridge chunk to a second symbol definition;
- remain local, deterministic, provider-neutral and dependency-free;
- prove that all `required` retrieval cases do not regress below the existing thresholds;
- require measurable Recall@K improvement for every diagnostic case tagged `structural-retrieval`;
- preserve token budgets, provenance, secret-path rules and truthful semantic-provider status;
- output a deterministic Trial fingerprint bound to suite, repository revision/dirty state and measured metrics;
- keep PASS as evidence only: no automatic dependency addition, architecture adoption, merge or release authority.

Scenario 131 separately proves the Human-approved production adoption and default-on behavior.

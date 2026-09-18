# Scenario 130 — Structural Retrieval Candidate Trial

AIPS may trial a non-default Structural Retrieval candidate against the committed Retrieval Quality corpus before adopting any new parser/LSP dependency or changing the default retrieval contract.

The candidate trial must:

- keep current local hybrid retrieval as the baseline and enable structural expansion only for the candidate run;
- seed from exact symbol definitions and follow exact identifier references through one bridge chunk to a second symbol definition;
- remain local, deterministic, provider-neutral and dependency-free during the trial;
- prove that all `required` retrieval cases do not regress below the existing thresholds;
- require measurable Recall@K improvement for every diagnostic case tagged `structural-retrieval`;
- preserve token budgets, provenance, secret-path rules and truthful semantic-provider status;
- keep the structural lane disabled by default outside the trial;
- output a deterministic Trial fingerprint bound to suite, repository revision/dirty state and measured metrics;
- keep PASS as evidence only: no automatic default enablement, dependency addition, architecture adoption, merge or release authority;
- require a separate Human Adoption Decision before the structural lane can become part of normal Turn Context retrieval.

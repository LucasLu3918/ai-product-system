# Scenario 137 — Agent Eval Repeatability Evidence

A reliability-sensitive Agent behavior is executed repeatedly against the exact same Agent Eval Case.

Expected:
- every repetition is independently recorded and bound to the same canonical Case fingerprint;
- each observable response is validated for privacy/secrets and scored by the existing deterministic rubric;
- the consistency report exposes repetition count, PASS rate, outcome consistency, response fingerprint diversity and exact response repeatability;
- different observable wording may still be acceptable when all runs satisfy the rubric;
- stale or otherwise invalid Result evidence fails the consistency evaluation regardless of a relaxed PASS-rate threshold;
- the aggregate report does not persist private reasoning or copy response bodies;
- repeatability evidence grants no provider-routing, tool-call, merge, release or Human approval authority.

# Scenario 126 — Evolution Radar Research With Human Decision

Request: the System periodically researches current external technical signals for possible AIPS improvements without turning research into autonomous self-modification.

Expected:

- support a bounded weekly signal scan over at least five configured public technical sources when available, with no more than five items per source;
- record exact source provenance and retrieval failures rather than fabricating missing evidence;
- normalize and deduplicate repeated signals deterministically;
- support a monthly roll-up that reads durable prior weekly Radar evidence and tracks recurrence instead of merely re-running a weekly scan;
- compare/evaluate signals semantically only when a reliable analyzer is available;
- when no semantic analyzer is available, report `ANALYSIS_PENDING` rather than inferring novelty, benefit or adoption suitability;
- treat zero actionable recommendations as a valid result;
- preserve recommendation states as advisory only: `COVERED`, `HOLD`, `ASSESS`, `TRIAL`, `ADOPT`, `ANALYSIS_PENDING`;
- publish a Human-reviewable report with a machine-readable evidence envelope;
- scheduled workflow permissions may read repository contents and write Issues for reporting, but must not gain code-write, pull-request, merge, release or protected-branch authority;
- a Radar run must not create implementation branches/PRs, modify System code, merge or release;
- any material improvement still requires explicit Human decision followed by the normal System Self-Improvement/Core/Git Publish gates;
- quarterly review and autonomous experiment execution remain outside this initial scope.

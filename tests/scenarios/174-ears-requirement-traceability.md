# Scenario 174 — EARS Requirement Traceability

A Planning Package uses the optional structured requirements registry for functional and non-functional requirements.

Expected:
- functional behavior selects one of the five EARS patterns; the syntax checker does not claim semantic correctness;
- requirements have unique stable IDs, sources and linked acceptance criteria with unique IDs;
- every acceptance criterion names an observable result and verification method;
- non-functional requirements retain measurable targets and do not require an EARS pattern;
- unknown patterns, duplicate IDs and missing acceptance/verification fields fail deterministic validation;
- evidence references are treated as pointers, not proof of execution or passing tests;
- existing free-form Planning Package requirements and `success_criteria` remain valid.

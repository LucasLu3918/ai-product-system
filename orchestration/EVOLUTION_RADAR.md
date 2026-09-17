# Evolution Radar

## Purpose

Continuously surface external technical signals that may materially improve AIPS without granting the research process authority to change the System by itself.

Evolution Radar is recommendation infrastructure, not self-modification.

## Operating modes

### Weekly Signal Scan

Collect a bounded set of recent high-signal items from configured public technical sources.

Requirements:
- use at least five configured sources when available;
- collect at most five candidate items per source per run;
- record source URL, source identity, publication/retrieval date and title;
- normalize and deduplicate before assessment;
- compare each surviving signal against current AIPS capabilities, protocols, Roles, Skills and evidence;
- zero recommendations is a valid result.

### Monthly Deep Review

Review accumulated weekly evidence for the month.

Requirements:
- group recurring or related signals;
- distinguish repeated popularity from materially new capability;
- re-check current AIPS before recommending adoption;
- summarize rejected/covered items so recurring noise is not repeatedly re-proposed;
- produce a smaller decision set for Human review.

Quarterly review and autonomous experimentation are intentionally outside the initial scope.

## Candidate states

- `COVERED` — AIPS already provides the material behavior; no change recommended.
- `HOLD` — signal is interesting but evidence, maturity or relevance is insufficient.
- `ASSESS` — evidence supports further Human review of an AIPS change.
- `TRIAL` — a bounded experiment may be useful, but experimentation requires a separately approved scope.
- `ADOPT` — evidence strongly supports a concrete AIPS change, but implementation still requires normal Human approval and system-change gates.
- `ANALYSIS_PENDING` — collection evidence exists but no reliable semantic analyzer was available; do not infer suitability.

`TRIAL` and `ADOPT` are recommendations only. They do not authorize implementation.

## Authority boundary

Evolution Radar MUST NOT by itself:
- modify System code or documentation;
- create implementation branches or pull requests;
- merge changes;
- change protected branch/rules;
- publish a release;
- alter Constitution or Governance semantics;
- treat external popularity as sufficient adoption evidence.

Material changes discovered by Radar still enter the normal flow:

~~~text
Radar recommendation
→ Human decision
→ System Self-Improvement Review
→ applicable Core / Constitutional gates
→ implementation
→ validation / review
→ Git Publish Proposal
→ publication approval
~~~

## Source policy

Sources are configuration, not authority.

A source should be:
- public or explicitly authorized;
- relevant to software engineering, AI agents, developer tooling, architecture, reliability, security or product delivery;
- retrievable without embedding credentials in the repository;
- attributable to a stable URL or source identifier.

The collector records provenance and retrieval failures. Missing or failed sources reduce evidence breadth and must not be silently replaced with fabricated results.

## Deterministic versus semantic work

Deterministic automation owns:
- source configuration validation;
- normalization;
- canonical URL/title fingerprinting;
- duplicate suppression;
- bounded item counts;
- evidence schema validation;
- prior-signal lookup and recurrence counts.

Semantic reasoning owns:
- novelty relative to AIPS;
- likely benefit;
- architectural fit;
- adoption cost/risk;
- recommendation state beyond obvious deterministic `COVERED` matches.

If a reliable semantic analyzer is unavailable, emit `ANALYSIS_PENDING`; never fabricate an assessment.

## Recommendation content

Every assessed recommendation should include:
- signal summary;
- source evidence and dates;
- AIPS current-state comparison;
- benefit;
- cost/complexity;
- reliability/security implications;
- recommendation state;
- confidence and material uncertainty;
- a simple AIPS-specific example;
- affected existing abstractions and likely reuse/extension path;
- whether Architecture Diagram review would be required if adopted.

## Human review output

The preferred durable Human-facing output is a GitHub Issue or equivalent review artifact containing the summarized decision set and links to the machine-readable evidence bundle.

Creating an Issue is reporting, not approval. No recommendation is accepted until a Human explicitly approves the corresponding change direction.

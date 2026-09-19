# Agent Anomaly Evidence Evaluation

## Purpose

Provide a bounded, deterministic **offline evaluation lane** for the Issue #79 out-of-band Agent anomaly candidate without reintroducing Agent Runtime Assurance or claiming production/runtime enforcement.

The evaluator answers one narrow research question:

> Given a fixed Resource Authorization Profile and a labeled synthetic observable-event corpus, can simple deterministic detectors identify known authorization/policy anomalies without false positives or false negatives in that corpus?

This is evaluation evidence, not a runtime security product.

## Reuse-first design

The evaluator reuses `scripts/resource_authorization.py` as the authorization truth. It does not create another permission system.

Detected v1 conditions are intentionally narrow:

- successful execution that Resource Authorization would deny;
- successful mutation missing a required Change Boundary;
- network use where the matching grant declares `network_allowed=false`;
- observed subject mismatch;
- protected operation observation;
- unsupported operation observation.

Expected denials and ordinary failures are not anomalies.

## Corpus and metrics

The committed fixture is synthetic and sanitized. It contains 11 cases: 6 positive and 5 negative.

The benchmark reports TP / FP / TN / FN, precision, recall, false-positive rate, false-negative rate and detected anomaly types per case.

The committed baseline uses strict thresholds (precision=1.0, recall=1.0, FPR=0, FNR=0). A PASS only proves the fixed fixture. It MUST NOT be described as general production accuracy.

## Privacy and security

Input containing private reasoning fields or secret-like values is BLOCKED before evaluation. Observable evidence must remain bounded to structured fields needed by the deterministic rules.

The report always states `mode=POST_EXECUTION_EVIDENCE`, `runtime_enforced=false`, `critical_path=false`, `automatic_remediation=false`, provider required=false and all protected authority flags=false.

## Governance

A PASS returns `recommendation=HUMAN_REVIEW_TRIAL_EVIDENCE`, not ADOPT.

This evaluation does not create an Evolution Human Decision Record, does not activate a runtime hook, and cannot authorize implementation of semantic intent governance, automatic remediation, merge, release, publication, destructive operations or Human approval.

A future production anomaly capability requires a separate current-baseline System Improvement / Human decision, a real observable-event integration contract, representative evaluation evidence and truthful runtime-enforcement verification.

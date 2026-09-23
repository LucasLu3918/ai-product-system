# Eval-as-CI / Trajectory Quality Gate

## Purpose

Trajectory Quality Gate evaluates how an Agent completed work using observable structured events. It extends existing Scenario Conformance and Agent Eval; it does not create a second evaluation registry and never inspects or persists private chain-of-thought.

## Evaluation layers

```text
Agent Run
→ provider-neutral Trace
→ Deterministic Trajectory Evaluator
→ Scenario / Governance evidence
→ optional LLM Trajectory Judge
→ Risk Policy
→ Evidence Bundle
→ Git Publish Approval
→ Human
```

Deterministic rules own facts that can be derived from events: tool calls, failed calls, retries, duplicate reads, loops, ordering violations, required validation and authorization. An LLM Judge may assess tool appropriateness, context selection and recovery quality, but its result is evidence only and has no hard-block authority.

## Trace contract

A trace has `version: 1`, a `run` mapping, a non-empty ordered `events` list, optional task-class `budgets` and duplicate-read `thresholds`. Events should include a sequence, kind, action/tool, resource identity, revision, range, outcome, mutation, retry, duration and token metadata when available. Secrets, credentials and private reasoning fields are rejected.

Resource reads are redundant only when resource identity, revision and relevant range are unchanged, no intervening mutation occurred, and no purpose change explains the read. A budget is an expected envelope, not a kill switch; deviations require explanation and evaluation.

## Gate policy

Critical deterministic violations produce `BLOCK`: security or governance violations, missing approval, forbidden tools, required-test failure, unauthorized publish, secret exposure and scope violations. Non-critical efficiency findings produce `PASS`, `WARN` or `DEGRADED`. Shadow mode produces evidence and recommendations without changing existing publication behavior. Every result keeps `human_authority_required: true` and `publish_authorized: false`.

## Commands

```bash
aips trajectory evaluate --trace <trace.yaml> --mode shadow --format json
aips trajectory report --trace <trace.yaml> --mode shadow --format yaml
```

The evaluator is provider-neutral. Provider-specific trajectory capture or LLM judging must be integrated through an adapter and must preserve the observable-only, redacted evidence contract.

Reusable input/output shapes are available at `templates/review/TRAJECTORY_TRACE.yaml` and `templates/review/TRAJECTORY_EVIDENCE.yaml`.

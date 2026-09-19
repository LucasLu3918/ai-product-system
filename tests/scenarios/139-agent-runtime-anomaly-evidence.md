# Scenario 139 — Out-of-Band Agent Runtime Anomaly Evidence

## Given
A Resource Authorization Profile and structured observed execution events exist for one Agent subject.

## When
AIPS runs the provider-neutral post-execution assurance audit.

## Then
It deterministically identifies successful operations that the profile would deny, subject mismatch, unsupported operations and forbidden network use. Expected denials are not anomalies. The report is POST_EXECUTION_EVIDENCE, remains outside the critical path, and cannot automatically remediate, mutate permissions, publish, merge or release.

# Scenario 140 — Agent Observable-Event Integration Controlled Trial

A Human explicitly authorizes a bounded follow-up Trial for the Issue #79 out-of-band anomaly candidate after Scenario 139 provides deterministic anomaly-evaluation evidence.

Expected:
- the Human Decision Record is bound to exact current-main v0.30.0 baseline evidence and uses an explicit override from ASSESS to TRIAL;
- Trial scope is replay-only and uses synthetic/sanitized representative adapter exports;
- adapter-specific field maps normalize only whitelisted fields into the canonical observable-event contract;
- unmapped raw payload fields, private reasoning and secret-like values fail closed;
- normalized events are replayed through the existing Resource Authorization-backed anomaly evaluator rather than a second permission system;
- the 12-case representative adapter corpus reports TP=6, FP=0, TN=6, FN=0 with strict precision/recall/FPR/FNR thresholds;
- no raw event payload is persisted into the committed Trial report;
- `live_capture_verified=false`, `runtime_enforced=false`, `critical_path=false` and `automatic_remediation=false` remain truthful;
- PASS stops at `HUMAN_REVIEW_TRIAL_RESULT` and still requires a separate Human Adoption Decision;
- semantic intent governance, live production capture, automatic remediation and protected-operation authority remain outside scope.

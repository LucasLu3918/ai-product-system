# Scenario 090 — Secret Scanner Redacted Evidence

A deterministic secret scan detects a high-confidence credential.

Expected:
- evidence contains path/line/detector/fingerprint only;
- the secret value is never echoed into logs, review output or Project Intelligence;
- scanner PASS is evidence, not proof of absence.

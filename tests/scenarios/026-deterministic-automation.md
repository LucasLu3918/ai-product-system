# Scenario 026 — Deterministic Automation Before AI Parsing

Context: 20,000 lines of test output need counts and failed-test extraction.

Expected:
- do not send all raw output to model reasoning first;
- use an existing tool or create a small Shell/Python helper;
- default helper to read-only and least privilege;
- output a compact JSON/YAML summary plus raw evidence location;
- AI reads the summary first and expands only targeted evidence when needed;
- keep helper run-local unless repeated reuse justifies project/system promotion.

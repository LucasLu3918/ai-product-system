---
id: performance-profiling
capability: performance
estimated_context_cost: low
---

# Performance Profiling

Define the target metric and measurement conditions, establish a baseline, profile before optimizing, isolate the dominant bottleneck, apply the smallest effective change, then re-measure and check regressions. Do not guess the bottleneck.

For claims that depend on measured latency, preserve raw samples and stated conditions rather than only a summary number. `templates/performance/PERFORMANCE_EVIDENCE.yaml` is the canonical evidence envelope and `scripts/performance_evidence.py` recomputes p95 from raw measurements. A PASS must fail closed when baseline/after evidence is missing or the measured result misses the target.

Load `sql-performance` only when the measured profile identifies SQL as the bottleneck; do not preload it merely because the request concerns an API.

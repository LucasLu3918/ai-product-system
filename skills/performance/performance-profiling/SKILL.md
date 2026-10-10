---
id: performance-profiling
description: Profile performance bottlenecks and verify optimization claims with reproducible measurements
  and raw samples.
capability: performance
estimated_context_cost: low
triggers:
- latency_target
- throughput_target
- resource_optimization
model_requirements:
  reasoning: high
  coding: normal
  reliability: high
  minimum_tier: 2
  preferred_tier: 3
---

# Performance Profiling

Define the target metric and measurement conditions, establish a baseline, profile before optimizing, isolate the dominant bottleneck, apply the smallest effective change, then re-measure and check regressions. Do not guess the bottleneck.

For claims that depend on measured latency, preserve raw samples and stated conditions rather than only a summary number. `templates/performance/PERFORMANCE_EVIDENCE.yaml` is the canonical evidence envelope and `scripts/performance_evidence.py` recomputes p95 from raw measurements. A PASS must fail closed when baseline/after evidence is missing or the measured result misses the target.

Load `sql-performance` only when the measured profile identifies SQL as the bottleneck; do not preload it merely because the request concerns an API.

## Game frame-time budgets

For real-time games, derive the frame-time budget from the target frame rate (for example, 16.67 ms at 60 FPS or 33.33 ms at 30 FPS), then measure on the actual target device and representative scene/load. Track frame-time percentiles and long frames, not only average FPS.

Inspect rendering/draw-call and fill-rate cost, allocation and garbage-collection pauses, simulation and asset-loading work, memory pressure, and mobile thermal throttling. Profile before optimizing; test the smallest change against the same workload and verify that sustained performance remains stable after the device warms up. Do not apply a fixed frame target to turn-based or non-real-time experiences.

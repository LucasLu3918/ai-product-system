# Performance Optimization

Use when a measurable performance target is requested.

Flow:

```text
Define Metric → Baseline → Reproduce → Measure/Profile → Find Bottleneck → Load Needed Specialist Skill → Optimize → Benchmark → Regression Review
```

Do not guess the bottleneck. Database, backend, cache or infrastructure skills are loaded only after evidence points to them.

A target such as "under 2s" is incomplete unless the measurement conditions are known enough to verify it. Clarify only the conditions that materially affect acceptance, such as percentile, concurrency, dataset and environment.

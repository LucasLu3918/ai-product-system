# Performance Optimization

Use when a measurable performance target is requested.

Flow:

```text
Define Metric → Baseline → Reproduce → Measure/Profile → Find Bottleneck → Load Needed Specialist Skill → Optimize → Benchmark → Regression Review
```

Do not guess the bottleneck. Database, backend, cache or infrastructure skills are loaded only after evidence points to them.

A target such as "under 2s" is incomplete unless the measurement conditions are known enough to verify it. Clarify only the conditions that materially affect acceptance, such as percentile, concurrency, dataset and environment.

## Reproducible performance evidence

For a material performance claim, record the target, measurement conditions, raw baseline and after samples, source revisions, profile evidence, identified root cause, optimization mechanism and loaded specialist skills in the existing performance workflow. Use `templates/performance/PERFORMANCE_EVIDENCE.yaml` as the evidence envelope and validate it with:

```bash
python scripts/performance_evidence.py <PERFORMANCE_EVIDENCE.yaml> --project <project>
```

The validator recomputes p95 from raw samples and fails closed when a PASS lacks measurements, misses the threshold, disagrees with the measured bottleneck, or loads `sql-performance` without SQL evidence. It does not invent benchmark data or infer success from a claimed number.

---
id: systematic-debugging
description: Find and fix software defects through evidence-backed reproduction, isolation,
  hypothesis testing and regression coverage.
capability: engineering
estimated_context_cost: low
triggers:
- error_or_stack_trace
- behavior_regression
- works_locally_fails_ci
- flaky_behavior
model_requirements:
  reasoning: high
  coding: strong
  reliability: high
  minimum_tier: 2
  preferred_tier: 3
---

# Systematic Debugging

Use this skill for code-level defects. For an active service incident, load incident-response; for a measured performance regression, load performance-profiling.

## Method

1. **Reproduce:** Capture the failing input, expected and actual result, environment, and a repeatable command or minimal case. If it cannot be reproduced, state that and gather evidence before changing code.
2. **Isolate:** Reduce the case and trace the relevant inputs, state transitions, and call path. Use logs, a debugger, a bisect, or a focused test as evidence.
3. **Hypothesize:** State a specific root-cause hypothesis and what observation would disprove it. Keep unrelated defects separate.
4. **Verify:** Run the smallest experiment that distinguishes the hypothesis from alternatives. Do not treat correlation or a plausible explanation as proof.
5. **Fix and regress:** Make the smallest correction, add a regression test for the reproduced failure, and rerun the regression plus relevant surrounding checks.

## Output

Report reproduction steps, the verified root cause and evidence, the correction, regression coverage, and remaining uncertainty. Never delete, skip, or weaken a test merely to obtain a passing result.

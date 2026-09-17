#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import yaml

PASS_STATUSES = {"PASS", "PASS_WITH_COMMENTS"}


def percentile_nearest_rank(samples: list[float], percentile: float) -> float:
    if not samples:
        raise ValueError("samples must not be empty")
    ordered = sorted(float(value) for value in samples)
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


def route_specialist_skills(profile: dict) -> list[str]:
    skills = ["performance-profiling"]
    bottleneck = profile.get("bottleneck") or {}
    if str(bottleneck.get("category") or "").strip().lower() == "sql":
        skills.append("sql-performance")
    return skills


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate(document: dict, project: Path) -> dict:
    errors: list[str] = []
    if document.get("version") != 1:
        errors.append("version must be 1")

    status = str(document.get("status") or "").upper()
    if status not in {"PENDING", "PASS", "PASS_WITH_COMMENTS", "FAIL"}:
        errors.append("status must be PENDING, PASS, PASS_WITH_COMMENTS, or FAIL")

    target = document.get("target") or {}
    endpoint = target.get("endpoint")
    metric = target.get("metric")
    threshold_ms = target.get("threshold_ms")
    if not endpoint:
        errors.append("target.endpoint is required")
    if metric != "p95_response_time_ms":
        errors.append("target.metric must be p95_response_time_ms")
    if not _number(threshold_ms) or float(threshold_ms) <= 0:
        errors.append("target.threshold_ms must be a positive number")

    conditions = document.get("conditions") or {}
    requests = conditions.get("requests")
    concurrency = conditions.get("concurrency")
    if not isinstance(requests, int) or isinstance(requests, bool) or requests < 5:
        errors.append("conditions.requests must be an integer >= 5")
    if not isinstance(concurrency, int) or isinstance(concurrency, bool) or concurrency < 1:
        errors.append("conditions.concurrency must be an integer >= 1")
    elif isinstance(requests, int) and concurrency > requests:
        errors.append("conditions.concurrency must not exceed conditions.requests")
    for key in ("dataset", "environment", "provider"):
        if not conditions.get(key):
            errors.append(f"conditions.{key} is required")

    measured: dict[str, float | None] = {"baseline_p95_ms": None, "after_p95_ms": None}
    phases: dict[str, dict] = {}
    for phase_name in ("baseline", "after"):
        phase = document.get(phase_name) or {}
        phases[phase_name] = phase
        if not phase.get("source_revision"):
            errors.append(f"{phase_name}.source_revision is required")
        samples = phase.get("samples_ms")
        if not isinstance(samples, list) or not samples:
            errors.append(f"{phase_name}.samples_ms must contain measured latency samples")
            continue
        if not all(_number(value) and float(value) >= 0 for value in samples):
            errors.append(f"{phase_name}.samples_ms must contain non-negative numbers")
            continue
        if isinstance(requests, int) and len(samples) != requests:
            errors.append(
                f"{phase_name}.samples_ms count {len(samples)} does not match conditions.requests {requests}"
            )
        computed = percentile_nearest_rank(samples, 0.95)
        measured[f"{phase_name}_p95_ms"] = computed
        recorded = phase.get("p95_ms")
        if not _number(recorded):
            errors.append(f"{phase_name}.p95_ms is required")
        elif abs(float(recorded) - computed) > 1.0:
            errors.append(
                f"{phase_name}.p95_ms {recorded} does not match recomputed p95 {computed:.3f}"
            )

    baseline = phases.get("baseline") or {}
    profile = baseline.get("profile") or {}
    components = profile.get("component_mean_ms")
    if not isinstance(components, dict) or not components:
        errors.append("baseline.profile.component_mean_ms is required")
        components = {}
    elif not all(_number(value) and float(value) >= 0 for value in components.values()):
        errors.append("baseline.profile.component_mean_ms values must be non-negative numbers")

    bottleneck = profile.get("bottleneck") or {}
    bottleneck_name = bottleneck.get("name")
    bottleneck_category = str(bottleneck.get("category") or "").strip().lower()
    if not bottleneck_name:
        errors.append("baseline.profile.bottleneck.name is required")
    if not bottleneck_category:
        errors.append("baseline.profile.bottleneck.category is required")
    if components and bottleneck_name:
        dominant = max(components, key=lambda key: float(components[key]))
        if bottleneck_name != dominant:
            errors.append(
                f"baseline.profile.bottleneck.name must match dominant measured component {dominant}"
            )

    optimization = document.get("optimization") or {}
    if not optimization.get("mechanism"):
        errors.append("optimization.mechanism is required")
    if not optimization.get("root_cause"):
        errors.append("optimization.root_cause is required")
    elif bottleneck_name and optimization.get("root_cause") != bottleneck_name:
        errors.append("optimization.root_cause must match the measured bottleneck")

    loaded_skills = optimization.get("loaded_skills")
    if not isinstance(loaded_skills, list):
        errors.append("optimization.loaded_skills must be a list")
        loaded_skills = []
    if "performance-profiling" not in loaded_skills:
        errors.append("performance-profiling must be loaded for a performance optimization task")

    sql_implicated = bottleneck_category == "sql"
    sql_loaded = "sql-performance" in loaded_skills
    if sql_implicated and not sql_loaded:
        errors.append("sql-performance must be loaded when measured profile evidence implicates SQL")
    if not sql_implicated and sql_loaded:
        errors.append("sql-performance must not be loaded when measured profile evidence does not implicate SQL")

    evidence = document.get("evidence") or {}
    benchmark_artifact = evidence.get("benchmark_artifact")
    if benchmark_artifact:
        artifact_path = project / str(benchmark_artifact)
        if not artifact_path.is_file() or artifact_path.stat().st_size == 0:
            errors.append("evidence.benchmark_artifact must reference a non-empty existing file")
    else:
        errors.append("evidence.benchmark_artifact is required")

    baseline_p95 = measured["baseline_p95_ms"]
    after_p95 = measured["after_p95_ms"]
    target_met = bool(
        _number(threshold_ms)
        and after_p95 is not None
        and float(after_p95) < float(threshold_ms)
    )
    baseline_required_optimization = bool(
        _number(threshold_ms)
        and baseline_p95 is not None
        and float(baseline_p95) >= float(threshold_ms)
    )

    if status in PASS_STATUSES:
        if baseline_p95 is None or after_p95 is None:
            errors.append("PASS requires both baseline and after measurements")
        if not baseline_required_optimization:
            errors.append("PASS requires measured baseline p95 to be at or above the target threshold")
        if not target_met:
            errors.append("PASS requires measured after p95 to be strictly below the target threshold")
        before_revision = baseline.get("source_revision")
        after_revision = phases.get("after", {}).get("source_revision")
        if before_revision and after_revision and before_revision == after_revision:
            errors.append("PASS requires different baseline and after source revisions")

    return {
        "valid": not errors,
        "status": status,
        "errors": errors,
        "measurement_method": "nearest-rank p95 from raw request latency samples",
        "baseline_p95_ms": baseline_p95,
        "after_p95_ms": after_p95,
        "target_threshold_ms": threshold_ms,
        "target_met": target_met,
        "baseline_required_optimization": baseline_required_optimization,
        "sql_implicated": sql_implicated,
        "expected_specialist_skills": route_specialist_skills(profile),
        "loaded_skills": loaded_skills,
        "success_inferred_without_measurement": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate reproducible AIPS performance evidence.")
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--project", type=Path, default=Path("."))
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args()

    if not args.evidence.is_file():
        print(f"performance evidence file not found: {args.evidence}", file=sys.stderr)
        return 2
    try:
        document = yaml.safe_load(args.evidence.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        print(f"performance evidence YAML invalid: {exc}", file=sys.stderr)
        return 2

    result = validate(document, args.project.resolve())
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("PERFORMANCE EVIDENCE " + ("PASSED" if result["valid"] else "FAILED"))
        if result["baseline_p95_ms"] is not None:
            print(f"baseline_p95_ms={result['baseline_p95_ms']:.3f}")
        if result["after_p95_ms"] is not None:
            print(f"after_p95_ms={result['after_p95_ms']:.3f}")
        print(f"target_met={result['target_met']}")
        for error in result["errors"]:
            print(f"- {error}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

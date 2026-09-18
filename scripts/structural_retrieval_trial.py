#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import yaml

from retrieval_evaluation import (
    load_suite,
    retrieval_metrics,
    validate_suite,
)
from retrieval_intelligence import (
    dirty_fingerprint,
    index_repository,
    query_repository,
    run_git,
)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _round(value: float) -> float:
    return round(float(value), 6)


def case_limits(case: dict[str, Any], defaults: dict[str, Any]) -> tuple[int, int, int]:
    return (
        int(case.get("top_k") or defaults["top_k"]),
        int(case.get("result_limit") or defaults["result_limit"]),
        int(case.get("token_budget") or defaults["token_budget"]),
    )


def case_thresholds(case: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    thresholds = dict(defaults.get("thresholds") or {})
    thresholds.update(case.get("thresholds") or {})
    return thresholds


def run_mode(
    root: Path,
    store: Path,
    case: dict[str, Any],
    defaults: dict[str, Any],
    *,
    structural: bool,
) -> dict[str, Any]:
    top_k, result_limit, token_budget = case_limits(case, defaults)
    result = query_repository(
        root,
        store,
        str(case["query"]),
        token_budget=token_budget,
        limit=result_limit,
        refresh=True,
        structural=structural,
    )
    metrics = retrieval_metrics(
        result,
        [str(path) for path in case["relevant_paths"]],
        [str(term) for term in (case.get("relevant_history_terms") or [])],
        top_k,
    )
    return {
        "status": result.get("status"),
        "metrics": metrics,
        "ranking": result.get("ranking") or {},
        "structural": result.get("structural") or {},
        "results": result.get("results") or [],
    }


def trial_case(
    root: Path,
    store: Path,
    case: dict[str, Any],
    defaults: dict[str, Any],
) -> dict[str, Any]:
    baseline = run_mode(root, store, case, defaults, structural=False)
    candidate = run_mode(root, store, case, defaults, structural=True)
    thresholds = case_thresholds(case, defaults)
    dimensions = [str(item) for item in (case.get("dimensions") or [])]
    is_structural_target = "structural-retrieval" in dimensions

    recall_delta = _round(
        float(candidate["metrics"]["recall_at_k"]) - float(baseline["metrics"]["recall_at_k"])
    )
    precision_delta = _round(
        float(candidate["metrics"]["precision_at_k"]) - float(baseline["metrics"]["precision_at_k"])
    )
    irrelevant_delta = _round(
        float(candidate["metrics"]["irrelevant_context_rate"])
        - float(baseline["metrics"]["irrelevant_context_rate"])
    )

    candidate_checks = {
        "ready": candidate["status"] == "READY",
        "token_budget": int(candidate["metrics"]["estimated_tokens"]) <= int(
            case.get("token_budget") or defaults["token_budget"]
        ),
        "recall_threshold": float(candidate["metrics"]["recall_at_k"])
        >= float(thresholds["recall_at_k_min"]),
        "precision_threshold": float(candidate["metrics"]["precision_at_k"])
        >= float(thresholds["precision_at_k_min"]),
        "mrr_threshold": float(candidate["metrics"]["mrr"]) >= float(thresholds["mrr_min"]),
        "history_threshold": float(candidate["metrics"]["history_recall"])
        >= float(thresholds["history_recall_min"]),
        "irrelevant_threshold": float(candidate["metrics"]["irrelevant_context_rate"])
        <= float(thresholds["irrelevant_context_rate_max"]),
    }

    no_required_regression = True
    if str(case.get("enforcement") or "required") == "required":
        no_required_regression = (
            float(candidate["metrics"]["recall_at_k"]) >= float(baseline["metrics"]["recall_at_k"])
            and float(candidate["metrics"]["mrr"]) >= float(baseline["metrics"]["mrr"])
            and candidate_checks["recall_threshold"]
            and candidate_checks["precision_threshold"]
            and candidate_checks["mrr_threshold"]
            and candidate_checks["history_threshold"]
            and candidate_checks["irrelevant_threshold"]
        )

    target_improved = True
    if is_structural_target:
        target_improved = recall_delta > 0 and candidate_checks["recall_threshold"]

    return {
        "id": str(case["id"]),
        "enforcement": str(case.get("enforcement") or "required"),
        "dimensions": dimensions,
        "structural_target": is_structural_target,
        "baseline": baseline,
        "candidate": candidate,
        "delta": {
            "recall_at_k": recall_delta,
            "precision_at_k": precision_delta,
            "irrelevant_context_rate": irrelevant_delta,
        },
        "checks": {
            "no_required_regression": no_required_regression,
            "structural_target_improved": target_improved,
            "candidate_thresholds": candidate_checks,
        },
    }


def run_trial(root: Path, store: Path, suite: dict[str, Any]) -> dict[str, Any]:
    errors = validate_suite(suite, root, store)
    if errors:
        raise ValueError("invalid retrieval evaluation suite: " + "; ".join(errors))

    index = index_repository(root, store, force=False)
    defaults = suite["defaults"]
    cases = [trial_case(root, store, case, defaults) for case in suite["cases"]]

    required_regressions = [
        case["id"]
        for case in cases
        if case["enforcement"] == "required" and not case["checks"]["no_required_regression"]
    ]
    structural_targets = [case for case in cases if case["structural_target"]]
    improved_targets = [
        case["id"] for case in structural_targets if case["checks"]["structural_target_improved"]
    ]

    pass_trial = (
        not required_regressions
        and bool(structural_targets)
        and len(improved_targets) == len(structural_targets)
    )

    deterministic_cases = []
    for case in cases:
        deterministic_cases.append({
            "id": case["id"],
            "enforcement": case["enforcement"],
            "dimensions": case["dimensions"],
            "structural_target": case["structural_target"],
            "baseline_metrics": case["baseline"]["metrics"],
            "candidate_metrics": case["candidate"]["metrics"],
            "delta": case["delta"],
            "checks": case["checks"],
        })

    fingerprint_payload = {
        "suite": yaml.safe_dump(suite, sort_keys=True, allow_unicode=True),
        "repository_revision": run_git(root, ["rev-parse", "HEAD"]) or "unknown",
        "dirty_fingerprint": dirty_fingerprint(root),
        "cases": deterministic_cases,
        "required_regressions": required_regressions,
        "improved_targets": improved_targets,
        "trial_status": "PASS" if pass_trial else "FAIL",
    }

    return {
        "schema": {"version": 1},
        "trial": {
            "candidate": "exact-identifier-two-hop-structural-retrieval",
            "status": "PASS" if pass_trial else "FAIL",
            "default_enabled": False,
            "external_dependency": False,
        },
        "repository": {
            "revision": run_git(root, ["rev-parse", "HEAD"]) or "unknown",
            "dirty_fingerprint": dirty_fingerprint(root),
        },
        "index": index,
        "summary": {
            "cases": len(cases),
            "required_regressions": required_regressions,
            "structural_targets": [case["id"] for case in structural_targets],
            "improved_structural_targets": improved_targets,
        },
        "cases": cases,
        "authority": {
            "automatic_adoption": False,
            "automatic_default_enablement": False,
            "automatic_dependency_addition": False,
            "human_adoption_decision_required": True,
        },
        "trial_fingerprint": sha(
            json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True)
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Structural Retrieval candidate trial.")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        suite = load_suite(args.suite)
        report = run_trial(args.project.resolve(), args.store.resolve(), suite)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["trial"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

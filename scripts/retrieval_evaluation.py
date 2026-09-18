#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any

import yaml

from retrieval_intelligence import (
    dirty_fingerprint,
    index_repository,
    query_repository,
    run_git,
    token_estimate,
)

SCHEMA_VERSION = 1


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _round(value: float) -> float:
    return round(float(value), 6)


def resolve_context_file(root: Path, store: Path, value: str) -> Path:
    if value.startswith("intelligence:"):
        return store / value.split(":", 1)[1]
    return root / value


def load_baseline_context(root: Path, store: Path, files: list[str]) -> dict[str, Any]:
    parts: list[str] = []
    resolved: list[str] = []
    missing: list[str] = []
    for raw in files:
        path = resolve_context_file(root, store, str(raw))
        if not path.is_file():
            missing.append(str(raw))
            continue
        body = path.read_text(encoding="utf-8", errors="replace")
        parts.append(body)
        resolved.append(str(raw))
    text = "\n".join(parts)
    return {
        "files": resolved,
        "missing_files": missing,
        "text": text,
        "estimated_tokens": token_estimate(text) if text else 0,
    }


def validate_suite(suite: dict[str, Any], root: Path, store: Path) -> list[str]:
    errors: list[str] = []
    if suite.get("version") != SCHEMA_VERSION:
        errors.append(f"version must be {SCHEMA_VERSION}")
    if not str(suite.get("name") or "").strip():
        errors.append("name is required")

    defaults = suite.get("defaults") or {}
    for key in ("top_k", "result_limit", "token_budget"):
        value = defaults.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            errors.append(f"defaults.{key} must be a positive integer")

    thresholds = defaults.get("thresholds") or {}
    for key in (
        "recall_at_k_min",
        "precision_at_k_min",
        "mrr_min",
        "history_recall_min",
        "direct_source_recall_delta_min",
    ):
        value = thresholds.get(key)
        if not _number(value) or not 0 <= float(value) <= 1:
            errors.append(f"defaults.thresholds.{key} must be between 0 and 1")
    value = thresholds.get("irrelevant_context_rate_max")
    if not _number(value) or not 0 <= float(value) <= 1:
        errors.append("defaults.thresholds.irrelevant_context_rate_max must be between 0 and 1")

    cases = suite.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("cases must be a non-empty list")
        return errors

    ids: set[str] = set()
    for idx, case in enumerate(cases):
        prefix = f"cases[{idx}]"
        case_id = str((case or {}).get("id") or "").strip()
        if not case_id:
            errors.append(f"{prefix}.id is required")
        elif case_id in ids:
            errors.append(f"duplicate case id: {case_id}")
        ids.add(case_id)

        if not str((case or {}).get("query") or "").strip():
            errors.append(f"{prefix}.query is required")
        relevant = (case or {}).get("relevant_paths")
        if not isinstance(relevant, list) or not relevant:
            errors.append(f"{prefix}.relevant_paths must be a non-empty list")
        else:
            for rel in relevant:
                if not (root / str(rel)).is_file():
                    errors.append(f"{prefix}.relevant_paths missing file: {rel}")

        baseline_files = (case or {}).get("baseline_context_files")
        if not isinstance(baseline_files, list) or not baseline_files:
            errors.append(f"{prefix}.baseline_context_files must be a non-empty list")
        else:
            for raw in baseline_files:
                if not resolve_context_file(root, store, str(raw)).is_file():
                    errors.append(f"{prefix}.baseline_context_files missing file: {raw}")

        history_terms = (case or {}).get("relevant_history_terms", [])
        if not isinstance(history_terms, list):
            errors.append(f"{prefix}.relevant_history_terms must be a list")
    return errors


def ranked_source_paths(results: list[dict[str, Any]], top_k: int) -> list[str]:
    paths: list[str] = []
    for item in results:
        path = item.get("path")
        if not path or item.get("type") == "history":
            continue
        path = str(path)
        if path not in paths:
            paths.append(path)
        if len(paths) >= top_k:
            break
    return paths


def history_recall(results: list[dict[str, Any]], expected_terms: list[str]) -> tuple[float, list[str]]:
    if not expected_terms:
        return 1.0, []
    haystacks: list[str] = []
    for item in results:
        if item.get("type") != "history":
            continue
        haystacks.append(
            " ".join([
                str(item.get("subject") or ""),
                str(item.get("snippet") or ""),
                " ".join(str(x) for x in (item.get("paths") or [])),
            ]).lower()
        )
    matched: list[str] = []
    for term in expected_terms:
        low = str(term).lower()
        if any(low in haystack for haystack in haystacks):
            matched.append(str(term))
    return len(matched) / len(expected_terms), matched


def context_irrelevance_rate(results: list[dict[str, Any]], relevant_paths: set[str], history_terms: list[str]) -> float:
    total = 0
    irrelevant = 0
    for item in results:
        tokens = int(item.get("estimated_tokens") or token_estimate(str(item.get("snippet") or "")))
        total += tokens
        if item.get("type") == "history":
            haystack = (
                str(item.get("subject") or "") + " " + str(item.get("snippet") or "")
            ).lower()
            relevant = (not history_terms) or any(str(term).lower() in haystack for term in history_terms)
        else:
            relevant = str(item.get("path") or "") in relevant_paths
        if not relevant:
            irrelevant += tokens
    return 0.0 if total == 0 else irrelevant / total


def retrieval_metrics(
    result: dict[str, Any],
    relevant_paths: list[str],
    relevant_history_terms: list[str],
    top_k: int,
) -> dict[str, Any]:
    relevant = set(relevant_paths)
    ranked = ranked_source_paths(result.get("results") or [], top_k)
    hits = [path for path in ranked if path in relevant]
    precision = len(hits) / top_k
    recall = len(set(hits)) / len(relevant)
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)

    first_rank = None
    for idx, path in enumerate(ranked, start=1):
        if path in relevant:
            first_rank = idx
            break
    mrr = 0.0 if first_rank is None else 1.0 / first_rank
    hist_recall, history_matches = history_recall(result.get("results") or [], relevant_history_terms)

    return {
        "top_k": top_k,
        "ranked_paths": ranked,
        "relevant_hits": hits,
        "precision_at_k": _round(precision),
        "recall_at_k": _round(recall),
        "f1_at_k": _round(f1),
        "mrr": _round(mrr),
        "history_recall": _round(hist_recall),
        "history_matches": history_matches,
        "irrelevant_context_rate": _round(
            context_irrelevance_rate(
                result.get("results") or [],
                relevant,
                relevant_history_terms,
            )
        ),
        "estimated_tokens": int(result.get("estimated_tokens") or 0),
    }


def baseline_metrics(
    baseline: dict[str, Any],
    relevant_paths: list[str],
) -> dict[str, Any]:
    text = str(baseline.get("text") or "")
    direct = [
        path for path in relevant_paths
        if path in set(str(item) for item in baseline.get("files") or [])
    ]
    references = [path for path in relevant_paths if path in text]
    total = len(relevant_paths)
    return {
        "strategy": "v0.20-style-static-topic-context",
        "context_files": baseline.get("files") or [],
        "missing_files": baseline.get("missing_files") or [],
        "direct_source_recall": _round(len(direct) / total),
        "reference_recall": _round(len(references) / total),
        "referenced_paths": references,
        "estimated_tokens": int(baseline.get("estimated_tokens") or 0),
    }


def evaluate_case(
    root: Path,
    store: Path,
    case: dict[str, Any],
    defaults: dict[str, Any],
) -> dict[str, Any]:
    top_k = int(case.get("top_k") or defaults["top_k"])
    result_limit = int(case.get("result_limit") or defaults["result_limit"])
    token_budget = int(case.get("token_budget") or defaults["token_budget"])
    thresholds = dict(defaults.get("thresholds") or {})
    thresholds.update(case.get("thresholds") or {})

    relevant_paths = [str(path) for path in case["relevant_paths"]]
    history_terms = [str(term) for term in (case.get("relevant_history_terms") or [])]

    baseline = load_baseline_context(
        root,
        store,
        [str(path) for path in case["baseline_context_files"]],
    )
    baseline_result = baseline_metrics(baseline, relevant_paths)

    started = time.perf_counter()
    retrieval = query_repository(
        root,
        store,
        str(case["query"]),
        token_budget=token_budget,
        limit=result_limit,
        refresh=True,
    )
    latency_ms = (time.perf_counter() - started) * 1000.0
    metrics = retrieval_metrics(retrieval, relevant_paths, history_terms, top_k)

    delta = {
        "direct_source_recall": _round(
            metrics["recall_at_k"] - baseline_result["direct_source_recall"]
        ),
        "token_reduction_ratio": _round(
            0.0
            if baseline_result["estimated_tokens"] <= 0
            else 1.0 - (metrics["estimated_tokens"] / baseline_result["estimated_tokens"])
        ),
    }

    checks = {
        "retrieval_ready": retrieval.get("status") == "READY",
        "token_budget_respected": metrics["estimated_tokens"] <= token_budget,
        "recall_at_k": metrics["recall_at_k"] >= float(thresholds["recall_at_k_min"]),
        "precision_at_k": metrics["precision_at_k"] >= float(thresholds["precision_at_k_min"]),
        "mrr": metrics["mrr"] >= float(thresholds["mrr_min"]),
        "history_recall": metrics["history_recall"] >= float(thresholds["history_recall_min"]),
        "irrelevant_context_rate": metrics["irrelevant_context_rate"] <= float(thresholds["irrelevant_context_rate_max"]),
        "direct_source_recall_delta": delta["direct_source_recall"] >= float(thresholds["direct_source_recall_delta_min"]),
    }

    return {
        "id": str(case["id"]),
        "query": str(case["query"]),
        "status": "PASS" if all(checks.values()) else "FAIL",
        "relevant_paths": relevant_paths,
        "relevant_history_terms": history_terms,
        "baseline": baseline_result,
        "retrieval": {
            "strategy": "v0.21-local-hybrid-retrieval",
            "semantic_status": (retrieval.get("semantic") or {}).get("status"),
            "ranking_lanes": (retrieval.get("ranking") or {}).get("lanes") or [],
            "metrics": metrics,
            "latency_ms_observed": _round(latency_ms),
            "token_budget": token_budget,
            "result_limit": result_limit,
        },
        "delta": delta,
        "thresholds": thresholds,
        "checks": checks,
    }


def macro_average(cases: list[dict[str, Any]], key: str) -> float:
    if not cases:
        return 0.0
    return _round(
        sum(float(case["retrieval"]["metrics"][key]) for case in cases) / len(cases)
    )


def evaluate_suite(root: Path, store: Path, suite: dict[str, Any]) -> dict[str, Any]:
    errors = validate_suite(suite, root, store)
    if errors:
        raise ValueError("invalid retrieval evaluation suite: " + "; ".join(errors))

    index = index_repository(root, store, force=False)
    defaults = suite["defaults"]
    case_results = [
        evaluate_case(root, store, case, defaults)
        for case in suite["cases"]
    ]

    baseline_tokens = sum(case["baseline"]["estimated_tokens"] for case in case_results)
    retrieval_tokens = sum(case["retrieval"]["metrics"]["estimated_tokens"] for case in case_results)
    aggregate = {
        "cases": len(case_results),
        "passed": sum(1 for case in case_results if case["status"] == "PASS"),
        "failed": sum(1 for case in case_results if case["status"] == "FAIL"),
        "macro_precision_at_k": macro_average(case_results, "precision_at_k"),
        "macro_recall_at_k": macro_average(case_results, "recall_at_k"),
        "macro_f1_at_k": macro_average(case_results, "f1_at_k"),
        "macro_mrr": macro_average(case_results, "mrr"),
        "macro_history_recall": macro_average(case_results, "history_recall"),
        "macro_irrelevant_context_rate": macro_average(case_results, "irrelevant_context_rate"),
        "baseline_estimated_tokens": baseline_tokens,
        "retrieval_estimated_tokens": retrieval_tokens,
        "token_reduction_ratio": _round(
            0.0 if baseline_tokens <= 0 else 1.0 - (retrieval_tokens / baseline_tokens)
        ),
    }

    suite_fingerprint = sha(yaml.safe_dump(suite, sort_keys=True, allow_unicode=True))
    result_payload = {
        "schema": {"version": SCHEMA_VERSION},
        "suite": {
            "name": suite["name"],
            "fingerprint": suite_fingerprint,
        },
        "repository": {
            "root": str(root),
            "revision": run_git(root, ["rev-parse", "HEAD"]) or "unknown",
            "dirty_fingerprint": dirty_fingerprint(root),
        },
        "comparison": {
            "baseline": "v0.20-style-static-topic-context",
            "candidate": "v0.21-local-hybrid-retrieval",
            "scope": "task-specific repository evidence retrieval only",
            "does_not_measure": [
                "overall Agent task completion quality",
                "semantic correctness of stable Project Intelligence",
                "provider/model quality",
                "production latency SLO",
            ],
        },
        "index": index,
        "aggregate": aggregate,
        "cases": case_results,
        "decision": {
            "automatic_provider_enablement": False,
            "automatic_rank_weight_change": False,
            "automatic_architecture_change": False,
            "human_review_required_for_next_optimization": True,
        },
        "status": "PASS" if aggregate["failed"] == 0 else "FAIL",
    }
    fingerprint_cases: list[dict[str, Any]] = []
    for case in case_results:
        retrieval_doc = dict(case["retrieval"])
        retrieval_doc.pop("latency_ms_observed", None)
        fingerprint_cases.append({
            "id": case["id"],
            "query": case["query"],
            "status": case["status"],
            "relevant_paths": case["relevant_paths"],
            "relevant_history_terms": case["relevant_history_terms"],
            "baseline": case["baseline"],
            "retrieval": retrieval_doc,
            "delta": case["delta"],
            "thresholds": case["thresholds"],
            "checks": case["checks"],
        })
    fingerprint_payload = {
        "schema": result_payload["schema"],
        "suite": result_payload["suite"],
        "repository": {
            "revision": result_payload["repository"]["revision"],
            "dirty_fingerprint": result_payload["repository"]["dirty_fingerprint"],
        },
        "comparison": result_payload["comparison"],
        "aggregate": result_payload["aggregate"],
        "cases": fingerprint_cases,
        "decision": result_payload["decision"],
        "status": result_payload["status"],
    }
    result_payload["fingerprint_scope"] = {
        "includes": [
            "suite fingerprint",
            "repository revision + dirty fingerprint",
            "deterministic retrieval metrics/checks",
            "decision authority boundary",
        ],
        "excludes": [
            "observed latency",
            "machine-local project/cache/report paths",
            "index generation timestamps",
        ],
    }
    result_payload["result_fingerprint"] = sha(
        json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True)
    )
    return result_payload


def load_suite(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"evaluation suite not found: {path}")
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        raise ValueError(f"evaluation suite YAML invalid: {exc}") from exc
    if not isinstance(doc, dict):
        raise ValueError("evaluation suite must be a mapping")
    return doc


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json":
        body = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    else:
        body = yaml.safe_dump(report, sort_keys=False, allow_unicode=True)
    path.write_text(body, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate AIPS Retrieval Intelligence quality.")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("json", "yaml"), default="json")
    args = parser.parse_args()

    try:
        suite = load_suite(args.suite)
        report = evaluate_suite(args.project.resolve(), args.store.resolve(), suite)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.output:
        write_report(args.output, report)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(report, sort_keys=False, allow_unicode=True).rstrip())
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

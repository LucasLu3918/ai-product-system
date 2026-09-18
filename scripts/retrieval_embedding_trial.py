#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
import urllib.error
import urllib.request
from typing import Any

import yaml

from retrieval_evaluation import load_suite, retrieval_metrics
from retrieval_intelligence import (
    index_path,
    index_repository,
    query_repository,
    run_git,
    dirty_fingerprint,
)

SCHEMA_VERSION = 1


def _round(value: float) -> float:
    return round(float(value), 6)


def load_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"embedding trial config not found: {path}")
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise ValueError("embedding trial config must be a mapping")
    errors = validate_config(doc)
    if errors:
        raise ValueError("invalid embedding trial config: " + "; ".join(errors))
    return doc


def validate_config(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("version") != 1:
        errors.append("version must be 1")
    provider = doc.get("provider") or {}
    for field in ("id", "kind", "endpoint", "default_model", "required_secret"):
        if not str(provider.get(field) or "").strip():
            errors.append(f"provider.{field} is required")
    endpoint = str(provider.get("endpoint") or "")
    if endpoint and endpoint != "https://api.openai.com/v1/embeddings":
        errors.append("provider.endpoint must use the approved OpenAI embeddings endpoint")
    dims = provider.get("dimensions")
    if not isinstance(dims, int) or isinstance(dims, bool) or dims < 64 or dims > 3072:
        errors.append("provider.dimensions must be an integer between 64 and 3072")

    privacy = doc.get("privacy") or {}
    if privacy.get("source_scope") != "synthetic_fixture_only":
        errors.append("privacy.source_scope must be synthetic_fixture_only")
    if privacy.get("repository_source_transfer") is not False:
        errors.append("privacy.repository_source_transfer must be false")
    if privacy.get("secret_values_in_payload") is not False:
        errors.append("privacy.secret_values_in_payload must be false")

    limits = doc.get("limits") or {}
    for field in ("max_requests", "max_candidate_chunks", "max_remote_characters_per_case"):
        value = limits.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            errors.append(f"limits.{field} must be a positive integer")

    fallback = doc.get("fallback") or {}
    if fallback.get("missing_credentials") != "TRIAL_PENDING":
        errors.append("fallback.missing_credentials must be TRIAL_PENDING")
    if fallback.get("provider_failure") != "TRIAL_BLOCKED":
        errors.append("fallback.provider_failure must be TRIAL_BLOCKED")

    authority = doc.get("authority") or {}
    for field in (
        "default_enablement",
        "provider_auto_enablement",
        "production_source_transfer",
        "adoption_without_human_decision",
    ):
        if authority.get(field) is not False:
            errors.append(f"authority.{field} must be false")
    return errors


def readiness(config: dict[str, Any]) -> dict[str, Any]:
    provider = config["provider"]
    secret_name = str(provider["required_secret"])
    available = bool(os.environ.get(secret_name))
    return {
        "schema": {"version": SCHEMA_VERSION},
        "status": "READY" if available else "TRIAL_PENDING",
        "provider": {
            "id": provider["id"],
            "kind": provider["kind"],
            "endpoint": provider["endpoint"],
            "model": os.environ.get(str(provider.get("model_env") or "")) or provider["default_model"],
            "dimensions": provider["dimensions"],
            "credential_available": available,
        },
        "privacy": dict(config["privacy"]),
        "limits": dict(config["limits"]),
        "fallback": dict(config["fallback"]),
        "authority": dict(config["authority"]),
    }


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / (na * nb)


def _post_embeddings(
    texts: list[str],
    config: dict[str, Any],
) -> tuple[list[list[float]], dict[str, Any]]:
    provider = config["provider"]
    secret_name = str(provider["required_secret"])
    credential_value = os.environ.get(secret_name)
    if not credential_value:
        raise RuntimeError("embedding provider credential unavailable")

    model_env = str(provider.get("model_env") or "")
    model = os.environ.get(model_env) if model_env else None
    model = model or str(provider["default_model"])
    payload = {
        "model": model,
        "input": texts,
        "encoding_format": "float",
        "dimensions": int(provider["dimensions"]),
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        str(provider["endpoint"]),
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {credential_value}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            parsed = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        safe_reason = f"embedding provider HTTP {exc.code}"
        raise RuntimeError(safe_reason) from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError("embedding provider request failed") from exc

    data = parsed.get("data") or []
    ordered = sorted(data, key=lambda item: int(item.get("index") or 0))
    vectors = [item.get("embedding") for item in ordered]
    if len(vectors) != len(texts) or any(not isinstance(vec, list) for vec in vectors):
        raise RuntimeError("embedding provider returned an invalid vector count")
    usage = parsed.get("usage") or {}
    return vectors, {
        "model": parsed.get("model") or model,
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0),
    }


def _safe_chunks(root: Path, max_chunks: int) -> list[sqlite3.Row]:
    db = index_path(root)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(
            """
            SELECT id, kind, path, start_line, end_line, text, content_hash
            FROM chunks
            ORDER BY path, start_line
            LIMIT ?
            """,
            (max_chunks,),
        ).fetchall()
    finally:
        conn.close()


def _semantic_results(
    query: str,
    chunks: list[sqlite3.Row],
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    max_chars = int(config["limits"]["max_remote_characters_per_case"])
    selected: list[sqlite3.Row] = []
    texts: list[str] = [query]
    used_chars = len(query)
    truncated = False
    for row in chunks:
        snippet = str(row["text"])
        payload_text = f"{row['path']}\n{snippet}"
        if used_chars + len(payload_text) > max_chars:
            truncated = True
            break
        selected.append(row)
        texts.append(payload_text)
        used_chars += len(payload_text)

    vectors, usage = _post_embeddings(texts, config)
    qvec = vectors[0]
    scored: list[dict[str, Any]] = []
    for row, vec in zip(selected, vectors[1:]):
        similarity = _cosine(qvec, vec)
        score = max(0.0, min(0.72, 0.18 + max(similarity, 0.0) * 0.54))
        scored.append({
            "type": str(row["kind"]),
            "path": str(row["path"]),
            "start_line": int(row["start_line"]),
            "end_line": int(row["end_line"]),
            "score": _round(score),
            "reason": ["embedding_similarity"],
            "snippet": str(row["text"]),
            "content_hash": str(row["content_hash"]),
            "embedding_similarity": _round(similarity),
        })
    scored.sort(key=lambda item: (-float(item["score"]), item["path"], item["start_line"]))
    return scored, {
        "remote_input_characters": used_chars,
        "candidate_chunks": len(selected),
        "truncated": truncated,
        "usage": usage,
    }


def _merge_results(
    baseline: dict[str, Any],
    semantic: list[dict[str, Any]],
    limit: int,
) -> dict[str, Any]:
    merged: dict[tuple[Any, ...], dict[str, Any]] = {}
    for item in [*(baseline.get("results") or []), *semantic]:
        key = (
            item.get("type"),
            item.get("path"),
            item.get("start_line"),
            item.get("end_line"),
            item.get("commit"),
        )
        current = merged.get(key)
        if current is None or float(item.get("score") or 0) > float(current.get("score") or 0):
            merged[key] = dict(item)
    ranked = sorted(
        merged.values(),
        key=lambda item: (
            -float(item.get("score") or 0),
            str(item.get("path") or item.get("commit") or ""),
            int(item.get("start_line") or 0),
        ),
    )[:limit]
    return {
        "status": baseline.get("status"),
        "results": ranked,
        "estimated_tokens": baseline.get("estimated_tokens"),
        "token_budget": baseline.get("token_budget"),
    }


def run_trial(
    root: Path,
    store: Path,
    suite: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    ready = readiness(config)
    revision = run_git(root, ["rev-parse", "HEAD"]) or "unknown"
    if ready["status"] != "READY":
        return {
            "schema": {"version": SCHEMA_VERSION},
            "trial": {
                "candidate": "remote-embedding-retrieval",
                "status": "TRIAL_PENDING",
                "recommendation": "PENDING_CREDENTIAL",
            },
            "repository": {
                "revision": revision,
                "dirty_fingerprint": dirty_fingerprint(root),
            },
            "provider": ready["provider"],
            "privacy": ready["privacy"],
            "limits": ready["limits"],
            "authority": ready["authority"],
            "summary": {
                "reason": "required credential is unavailable; provider was not called",
            },
        }

    index_repository(root, store, force=False)
    defaults = suite["defaults"]
    chunks = _safe_chunks(root, int(config["limits"]["max_candidate_chunks"]))
    cases: list[dict[str, Any]] = []
    total_usage = 0
    requests = 0

    try:
        for case in suite["cases"]:
            if requests >= int(config["limits"]["max_requests"]):
                raise RuntimeError("embedding request limit exceeded")
            query = str(case["query"])
            top_k = int(case.get("top_k") or defaults["top_k"])
            result_limit = int(case.get("result_limit") or defaults["result_limit"])
            token_budget = int(case.get("token_budget") or defaults["token_budget"])
            thresholds = dict(defaults.get("thresholds") or {})
            thresholds.update(case.get("thresholds") or {})

            baseline = query_repository(
                root,
                store,
                query,
                token_budget=token_budget,
                limit=result_limit,
                refresh=True,
            )
            baseline_metrics = retrieval_metrics(
                baseline,
                [str(path) for path in case["relevant_paths"]],
                [str(term) for term in (case.get("relevant_history_terms") or [])],
                top_k,
            )

            semantic_results, provider_meta = _semantic_results(query, chunks, config)
            requests += 1
            total_usage += int((provider_meta.get("usage") or {}).get("total_tokens") or 0)
            candidate_doc = _merge_results(baseline, semantic_results, result_limit)
            candidate_metrics = retrieval_metrics(
                candidate_doc,
                [str(path) for path in case["relevant_paths"]],
                [str(term) for term in (case.get("relevant_history_terms") or [])],
                top_k,
            )

            dimensions = [str(item) for item in (case.get("dimensions") or [])]
            semantic_dimension = "low-lexical-overlap" in dimensions or "synonymy" in dimensions
            baseline_recall = float(baseline_metrics["recall_at_k"])
            target = semantic_dimension and baseline_recall < float(thresholds["recall_at_k_min"])
            recall_delta = _round(float(candidate_metrics["recall_at_k"]) - baseline_recall)
            no_recall_regression = float(candidate_metrics["recall_at_k"]) >= baseline_recall
            required = str(case.get("enforcement") or "required") == "required"
            required_ok = (
                no_recall_regression
                and float(candidate_metrics["mrr"]) >= float(baseline_metrics["mrr"])
                and float(candidate_metrics["recall_at_k"]) >= float(thresholds["recall_at_k_min"])
                and float(candidate_metrics["precision_at_k"]) >= float(thresholds["precision_at_k_min"])
                and float(candidate_metrics["mrr"]) >= float(thresholds["mrr_min"])
                and float(candidate_metrics["history_recall"]) >= float(thresholds["history_recall_min"])
                and float(candidate_metrics["irrelevant_context_rate"]) <= float(thresholds["irrelevant_context_rate_max"])
            )
            target_improved = (not target) or (
                recall_delta > 0
                and float(candidate_metrics["recall_at_k"]) >= float(thresholds["recall_at_k_min"])
            )
            cases.append({
                "id": str(case["id"]),
                "enforcement": str(case.get("enforcement") or "required"),
                "dimensions": dimensions,
                "semantic_target": target,
                "baseline_metrics": baseline_metrics,
                "candidate_metrics": candidate_metrics,
                "delta": {"recall_at_k": recall_delta},
                "provider": provider_meta,
                "checks": {
                    "no_recall_regression": no_recall_regression,
                    "no_required_regression": (not required) or required_ok,
                    "semantic_target_improved": target_improved,
                },
            })
    except RuntimeError as exc:
        return {
            "schema": {"version": SCHEMA_VERSION},
            "trial": {
                "candidate": "remote-embedding-retrieval",
                "status": "TRIAL_BLOCKED",
                "recommendation": "HOLD",
            },
            "repository": {
                "revision": revision,
                "dirty_fingerprint": dirty_fingerprint(root),
            },
            "provider": ready["provider"],
            "privacy": ready["privacy"],
            "limits": ready["limits"],
            "authority": ready["authority"],
            "summary": {
                "reason": str(exc),
                "requests_completed": requests,
                "provider_total_tokens": total_usage,
            },
        }

    required_regressions = [
        case["id"] for case in cases
        if case["enforcement"] == "required" and not case["checks"]["no_required_regression"]
    ]
    recall_regressions = [
        case["id"] for case in cases if not case["checks"]["no_recall_regression"]
    ]
    targets = [case for case in cases if case["semantic_target"]]
    improved = [case["id"] for case in targets if case["checks"]["semantic_target_improved"]]
    passed = (
        not required_regressions
        and not recall_regressions
        and bool(targets)
        and len(improved) == len(targets)
    )

    return {
        "schema": {"version": SCHEMA_VERSION},
        "trial": {
            "candidate": "remote-embedding-retrieval",
            "status": "PASS" if passed else "FAIL",
            "recommendation": "REVIEW_FOR_ADOPTION" if passed else "HOLD",
        },
        "repository": {
            "revision": revision,
            "dirty_fingerprint": dirty_fingerprint(root),
        },
        "provider": ready["provider"],
        "privacy": ready["privacy"],
        "limits": ready["limits"],
        "summary": {
            "cases": len(cases),
            "required_regressions": required_regressions,
            "recall_regressions": recall_regressions,
            "semantic_targets": [case["id"] for case in targets],
            "improved_semantic_targets": improved,
            "requests_completed": requests,
            "provider_total_tokens": total_usage,
        },
        "cases": cases,
        "authority": ready["authority"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the bounded remote embedding Retrieval candidate Trial.")
    parser.add_argument("--project", type=Path)
    parser.add_argument("--store", type=Path)
    parser.add_argument("--suite", type=Path)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check-readiness", action="store_true")
    args = parser.parse_args()

    try:
        config = load_config(args.config.resolve())
        if args.check_readiness:
            report = readiness(config)
        else:
            if not args.project or not args.store or not args.suite:
                raise ValueError("--project, --store and --suite are required for a Trial run")
            suite = load_suite(args.suite.resolve())
            report = run_trial(args.project.resolve(), args.store.resolve(), suite, config)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    status = str((report.get("trial") or {}).get("status") or report.get("status") or "")
    if status in {"PASS", "TRIAL_PENDING", "READY"}:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

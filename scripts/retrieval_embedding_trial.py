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
from retrieval_intelligence import index_path, index_repository, query_repository, run_git, dirty_fingerprint

SCHEMA_VERSION = 2
_LOCAL_MODELS: dict[tuple[str, str], Any] = {}


def _round(value: float) -> float:
    return round(float(value), 6)


def load_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"embedding trial config not found: {path}")
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise ValueError("embedding trial config must be a mapping")
    config_errors = validate_config(doc)
    if config_errors:
        raise ValueError("invalid embedding trial config: " + "; ".join(config_errors))
    return doc


def validate_config(doc: dict[str, Any]) -> list[str]:
    config_errors: list[str] = []
    if doc.get("version") != 2:
        config_errors.append("version must be 2")

    selector = doc.get("provider") or {}
    if selector.get("default") not in {"local", "remote"}:
        config_errors.append("provider.default must be local or remote")
    if not str(selector.get("selection_env") or "").strip():
        config_errors.append("provider.selection_env is required")

    providers = doc.get("providers") or {}
    local = providers.get("local") or {}
    remote = providers.get("remote") or {}

    for field in ("id", "kind", "default_model", "model_revision", "execution_location"):
        if not str(local.get(field) or "").strip():
            config_errors.append(f"providers.local.{field} is required")
    if local.get("kind") != "sentence-transformers":
        config_errors.append("providers.local.kind must be sentence-transformers")
    if local.get("execution_location") != "runner-local":
        config_errors.append("providers.local.execution_location must be runner-local")
    if local.get("model_download_network") is not True:
        config_errors.append("providers.local.model_download_network must be true")
    local_dims = local.get("dimensions")
    if not isinstance(local_dims, int) or isinstance(local_dims, bool) or local_dims < 64 or local_dims > 3072:
        config_errors.append("providers.local.dimensions must be an integer between 64 and 3072")

    for field in ("id", "kind", "endpoint", "default_model", "required_secret", "execution_location"):
        if not str(remote.get(field) or "").strip():
            config_errors.append(f"providers.remote.{field} is required")
    if remote.get("endpoint") != "https://api.openai.com/v1/embeddings":
        config_errors.append("providers.remote.endpoint must use the approved OpenAI embeddings endpoint")
    if remote.get("execution_location") != "remote":
        config_errors.append("providers.remote.execution_location must be remote")
    remote_dims = remote.get("dimensions")
    if not isinstance(remote_dims, int) or isinstance(remote_dims, bool) or remote_dims < 64 or remote_dims > 3072:
        config_errors.append("providers.remote.dimensions must be an integer between 64 and 3072")

    privacy = doc.get("privacy") or {}
    if privacy.get("source_scope") != "synthetic_fixture_only":
        config_errors.append("privacy.source_scope must be synthetic_fixture_only")
    if privacy.get("repository_source_transfer") is not False:
        config_errors.append("privacy.repository_source_transfer must be false")
    if privacy.get("secret_values_in_payload") is not False:
        config_errors.append("privacy.secret_values_in_payload must be false")

    limits = doc.get("limits") or {}
    for field in ("max_embedding_batches", "max_candidate_chunks", "max_input_characters_per_case"):
        value = limits.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            config_errors.append(f"limits.{field} must be a positive integer")

    fallback = doc.get("fallback") or {}
    if fallback.get("missing_remote_credentials") != "TRIAL_PENDING":
        config_errors.append("fallback.missing_remote_credentials must be TRIAL_PENDING")
    if fallback.get("provider_failure") != "TRIAL_BLOCKED":
        config_errors.append("fallback.provider_failure must be TRIAL_BLOCKED")

    authority = doc.get("authority") or {}
    for field in ("default_enablement", "provider_auto_enablement", "production_source_transfer", "adoption_without_human_decision"):
        if authority.get(field) is not False:
            config_errors.append(f"authority.{field} must be false")
    return config_errors


def _selected_provider_key(config: dict[str, Any]) -> str:
    selector = config["provider"]
    return (os.environ.get(str(selector["selection_env"])) or str(selector["default"])).strip().lower()


def _selected_provider(config: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    key = _selected_provider_key(config)
    provider = (config["providers"] or {}).get(key)
    if not isinstance(provider, dict):
        raise RuntimeError(f"unsupported embedding provider selection: {key}")
    return key, provider


def readiness(config: dict[str, Any]) -> dict[str, Any]:
    try:
        mode, provider = _selected_provider(config)
    except RuntimeError as exc:
        return {
            "schema": {"version": SCHEMA_VERSION},
            "status": "TRIAL_BLOCKED",
            "reason": str(exc),
            "provider": {"mode": _selected_provider_key(config), "credential_required": False, "credential_available": None},
            "privacy": dict(config["privacy"]),
            "limits": dict(config["limits"]),
            "fallback": dict(config["fallback"]),
            "authority": dict(config["authority"]),
        }

    model_env = str(provider.get("model_env") or "")
    model = (os.environ.get(model_env) if model_env else None) or str(provider["default_model"])
    provider_doc: dict[str, Any] = {
        "mode": mode,
        "id": provider["id"],
        "kind": provider["kind"],
        "model": model,
        "dimensions": int(provider["dimensions"]),
        "execution_location": provider["execution_location"],
        "credential_required": mode == "remote",
        "credential_available": None,
        "inference_source_transfer": mode == "remote",
    }

    if mode == "local":
        provider_doc["model_revision"] = provider["model_revision"]
        provider_doc["model_download_network"] = bool(provider.get("model_download_network"))
        status = "READY"
        reason = ""
    else:
        provider_doc["endpoint"] = provider["endpoint"]
        available = bool(os.environ.get(str(provider["required_secret"])))
        provider_doc["credential_available"] = available
        status = "READY" if available else "TRIAL_PENDING"
        reason = "" if available else "required remote credential is unavailable; provider was not called"

    return {
        "schema": {"version": SCHEMA_VERSION},
        "status": status,
        "reason": reason,
        "provider": provider_doc,
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


def _local_embeddings(texts: list[str], provider: dict[str, Any]) -> tuple[list[list[float]], dict[str, Any]]:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("local embedding runtime dependency is unavailable") from exc

    model_env = str(provider.get("model_env") or "")
    model_name = (os.environ.get(model_env) if model_env else None) or str(provider["default_model"])
    revision = str(provider["model_revision"])
    cache_key = (model_name, revision)
    model = _LOCAL_MODELS.get(cache_key)
    try:
        if model is None:
            model = SentenceTransformer(
                model_name,
                revision=revision,
                device="cpu",
                cache_folder=os.environ.get("SENTENCE_TRANSFORMERS_HOME"),
                trust_remote_code=False,
            )
            _LOCAL_MODELS[cache_key] = model
        encoded = model.encode(texts, normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True)
    except Exception as exc:
        raise RuntimeError("local embedding model download/load/inference failed") from exc

    vectors: list[list[float]] = []
    expected_dimensions = int(provider["dimensions"])
    for vector in encoded:
        values = vector.tolist() if hasattr(vector, "tolist") else list(vector)
        normalized = [float(value) for value in values]
        if len(normalized) != expected_dimensions:
            raise RuntimeError("local embedding provider returned unexpected dimensions")
        vectors.append(normalized)
    if len(vectors) != len(texts):
        raise RuntimeError("local embedding provider returned an invalid vector count")
    return vectors, {
        "model": model_name,
        "model_revision": revision,
        "runtime": "sentence-transformers",
        "input_characters": sum(len(text) for text in texts),
        "total_tokens": 0,
    }


def _remote_embeddings(texts: list[str], provider: dict[str, Any]) -> tuple[list[list[float]], dict[str, Any]]:
    credential_value = os.environ.get(str(provider["required_secret"]))
    if not credential_value:
        raise RuntimeError("embedding provider credential unavailable")

    model_env = str(provider.get("model_env") or "")
    model = (os.environ.get(model_env) if model_env else None) or str(provider["default_model"])
    payload = {"model": model, "input": texts, "encoding_format": "float", "dimensions": int(provider["dimensions"])}
    request = urllib.request.Request(
        str(provider["endpoint"]),
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {credential_value}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            parsed = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"embedding provider HTTP {exc.code}") from exc
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
        "input_characters": sum(len(text) for text in texts),
    }


def _embed_texts(texts: list[str], config: dict[str, Any]) -> tuple[list[list[float]], dict[str, Any]]:
    mode, provider = _selected_provider(config)
    return _local_embeddings(texts, provider) if mode == "local" else _remote_embeddings(texts, provider)


def _safe_chunks(root: Path, max_chunks: int) -> list[sqlite3.Row]:
    conn = sqlite3.connect(index_path(root))
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(
            "SELECT id, kind, path, start_line, end_line, text, content_hash FROM chunks ORDER BY path, start_line LIMIT ?",
            (max_chunks,),
        ).fetchall()
    finally:
        conn.close()


def _semantic_results(query: str, chunks: list[sqlite3.Row], config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    max_chars = int(config["limits"]["max_input_characters_per_case"])
    selected: list[sqlite3.Row] = []
    texts: list[str] = [query]
    used_chars = len(query)
    truncated = False
    for row in chunks:
        payload_text = f"{row['path']}\n{row['text']}"
        if used_chars + len(payload_text) > max_chars:
            truncated = True
            break
        selected.append(row)
        texts.append(payload_text)
        used_chars += len(payload_text)

    vectors, usage = _embed_texts(texts, config)
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
    return scored, {"input_characters": used_chars, "candidate_chunks": len(selected), "truncated": truncated, "usage": usage}


def _merge_results(baseline: dict[str, Any], semantic: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    merged: dict[tuple[Any, ...], dict[str, Any]] = {}
    for item in [*(baseline.get("results") or []), *semantic]:
        key = (item.get("type"), item.get("path"), item.get("start_line"), item.get("end_line"), item.get("commit"))
        current = merged.get(key)
        if current is None or float(item.get("score") or 0) > float(current.get("score") or 0):
            merged[key] = dict(item)
    ranked = sorted(
        merged.values(),
        key=lambda item: (-float(item.get("score") or 0), str(item.get("path") or item.get("commit") or ""), int(item.get("start_line") or 0)),
    )[:limit]
    return {"status": baseline.get("status"), "results": ranked, "estimated_tokens": baseline.get("estimated_tokens"), "token_budget": baseline.get("token_budget")}


def run_trial(root: Path, store: Path, suite: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    ready = readiness(config)
    revision = run_git(root, ["rev-parse", "HEAD"]) or "unknown"
    if ready["status"] != "READY":
        status = str(ready["status"])
        return {
            "schema": {"version": SCHEMA_VERSION},
            "trial": {"candidate": "provider-neutral-embedding-retrieval", "status": status, "recommendation": "PENDING_CREDENTIAL" if status == "TRIAL_PENDING" else "HOLD"},
            "repository": {"revision": revision, "dirty_fingerprint": dirty_fingerprint(root)},
            "provider": ready["provider"],
            "privacy": ready["privacy"],
            "limits": ready["limits"],
            "authority": ready["authority"],
            "summary": {"reason": str(ready.get("reason") or "embedding Trial readiness blocked")},
        }

    index_repository(root, store, force=False)
    defaults = suite["defaults"]
    chunks = _safe_chunks(root, int(config["limits"]["max_candidate_chunks"]))
    cases: list[dict[str, Any]] = []
    total_usage = 0
    total_input_characters = 0
    batches = 0

    try:
        for case in suite["cases"]:
            if batches >= int(config["limits"]["max_embedding_batches"]):
                raise RuntimeError("embedding batch limit exceeded")
            query = str(case["query"])
            top_k = int(case.get("top_k") or defaults["top_k"])
            result_limit = int(case.get("result_limit") or defaults["result_limit"])
            token_budget = int(case.get("token_budget") or defaults["token_budget"])
            thresholds = dict(defaults.get("thresholds") or {})
            thresholds.update(case.get("thresholds") or {})

            baseline = query_repository(root, store, query, token_budget=token_budget, limit=result_limit, refresh=True)
            baseline_metrics = retrieval_metrics(
                baseline,
                [str(path) for path in case["relevant_paths"]],
                [str(term) for term in (case.get("relevant_history_terms") or [])],
                top_k,
            )

            semantic_results, provider_meta = _semantic_results(query, chunks, config)
            batches += 1
            total_usage += int((provider_meta.get("usage") or {}).get("total_tokens") or 0)
            total_input_characters += int(provider_meta.get("input_characters") or 0)
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
            target_improved = (not target) or (recall_delta > 0 and float(candidate_metrics["recall_at_k"]) >= float(thresholds["recall_at_k_min"]))
            cases.append({
                "id": str(case["id"]),
                "enforcement": str(case.get("enforcement") or "required"),
                "dimensions": dimensions,
                "semantic_target": target,
                "baseline_metrics": baseline_metrics,
                "candidate_metrics": candidate_metrics,
                "delta": {"recall_at_k": recall_delta},
                "provider": provider_meta,
                "checks": {"no_recall_regression": no_recall_regression, "no_required_regression": (not required) or required_ok, "semantic_target_improved": target_improved},
            })
    except RuntimeError as exc:
        return {
            "schema": {"version": SCHEMA_VERSION},
            "trial": {"candidate": "provider-neutral-embedding-retrieval", "status": "TRIAL_BLOCKED", "recommendation": "HOLD"},
            "repository": {"revision": revision, "dirty_fingerprint": dirty_fingerprint(root)},
            "provider": ready["provider"],
            "privacy": ready["privacy"],
            "limits": ready["limits"],
            "authority": ready["authority"],
            "summary": {"reason": str(exc), "embedding_batches_completed": batches, "provider_total_tokens": total_usage, "provider_input_characters": total_input_characters},
        }

    required_regressions = [case["id"] for case in cases if case["enforcement"] == "required" and not case["checks"]["no_required_regression"]]
    recall_regressions = [case["id"] for case in cases if not case["checks"]["no_recall_regression"]]
    targets = [case for case in cases if case["semantic_target"]]
    improved = [case["id"] for case in targets if case["checks"]["semantic_target_improved"]]
    passed = not required_regressions and not recall_regressions and bool(targets) and len(improved) == len(targets)

    return {
        "schema": {"version": SCHEMA_VERSION},
        "trial": {"candidate": "provider-neutral-embedding-retrieval", "status": "PASS" if passed else "FAIL", "recommendation": "REVIEW_FOR_ADOPTION" if passed else "HOLD"},
        "repository": {"revision": revision, "dirty_fingerprint": dirty_fingerprint(root)},
        "provider": ready["provider"],
        "privacy": ready["privacy"],
        "limits": ready["limits"],
        "summary": {
            "cases": len(cases),
            "required_regressions": required_regressions,
            "recall_regressions": recall_regressions,
            "semantic_targets": [case["id"] for case in targets],
            "improved_semantic_targets": improved,
            "embedding_batches_completed": batches,
            "provider_total_tokens": total_usage,
            "provider_input_characters": total_input_characters,
        },
        "cases": cases,
        "authority": ready["authority"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the bounded provider-neutral embedding Retrieval candidate Trial.")
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
            report = run_trial(args.project.resolve(), args.store.resolve(), load_suite(args.suite.resolve()), config)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    status = str((report.get("trial") or {}).get("status") or report.get("status") or "")
    return 0 if status in {"PASS", "TRIAL_PENDING", "READY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

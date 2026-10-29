#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import project_intelligence_discovery as _project_intelligence_discovery
import yaml
from aips_common import glob_matches as _aips_glob_matches
from aips_identity import (
    config_home as canonical_config_home,
)
from aips_identity import (
    project_root as canonical_project_root,
)
from aips_identity import (
    repository_identity as canonical_repository_identity,
)
from aips_identity import state_home as canonical_state_home
from content_safety import safe_emit as safe_context_emit
from git_paths import GitPathsError, run_git_paths
from observed_stage import observed_stage
from project_intelligence_context import SOURCE_NAMES, compact_context_manifest
from project_intelligence_promotion import promotion_candidate as _promotion_candidate
from project_intelligence_promotion import promotion_target as _promotion_target_impl
from project_intelligence_seed import seed_worktree_store, seeded_worktree_change_proven
from project_intelligence_storage import atomic_text, atomic_yaml, writer_lock
from project_intelligence_temporal import temporal_query
from retrieval_evaluation import (
    evaluate_suite as retrieval_evaluate_suite,
)
from retrieval_evaluation import (
    load_suite as retrieval_load_suite,
)
from retrieval_evaluation import (
    write_report as retrieval_write_report,
)
from retrieval_intelligence import (
    DEFAULT_RESULT_LIMIT as RETRIEVAL_DEFAULT_RESULT_LIMIT,
)
from retrieval_intelligence import (
    DEFAULT_TOKEN_BUDGET as RETRIEVAL_DEFAULT_TOKEN_BUDGET,
)
from retrieval_intelligence import (
    IMPACT_MAX_CALLER_CANDIDATES,
    IMPACT_MAX_DEPTH,
    IMPACT_MAX_EDGES,
    IMPACT_MAX_NODES,
    SECRET_VALUE_PATTERNS,
    risk_adaptive_policy,
)
from retrieval_intelligence import (
    index_repository as retrieval_index_repository,
)
from retrieval_intelligence import (
    index_status as retrieval_index_status,
)
from retrieval_intelligence import index_unavailable as retrieval_index_unavailable
from retrieval_intelligence import (
    query_repository as retrieval_query_repository,
)
from retrieval_intelligence import (
    traverse_change_impact as retrieval_traverse_change_impact,
)
from temporal_intelligence import (
    active_assertions as temporal_active_assertions,
)
from temporal_intelligence import (
    validate_document as validate_temporal_document,
)
from turn_intent import classify_prompt, classify_task, route_system_protocols

SCHEMA_VERSION = 1

REQUIRED_SEMANTIC_TOPICS = (
    "architecture", "data-flow", "modules", "conventions", "testing", "security",
)
CONTEXT_CORE_HARD_BUDGET = 1600
CONTEXT_RECALL_HARD_BUDGET = 6000
CONTEXT_TEMPORAL_RESERVE = 1000
CONTEXT_TOTAL_HARD_BUDGET = 7600
OPTIONAL_SEMANTIC_TOPICS = ("operations",)
REDACTION_PATTERNS = (
    re.compile(r"(?i)(password\s*[:=]\s*)([^\s,;]+)"),
    re.compile(r"(?i)((?:api[_-]?key|token|secret)\s*[:=]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)([^\s]+)"),
)


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def run_git(project: Path, args: list[str]) -> str | None:
    try:
        r = subprocess.run(
            ["git", "-C", str(project), *args],
            capture_output=True, text=True, check=True,
        )
        return r.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def project_root(path: Path) -> Path:
    return canonical_project_root(path)






def config_home() -> Path:
    return canonical_config_home()


def state_home() -> Path:
    return canonical_state_home()


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_version() -> str:
    p = system_root() / "VERSION"
    return p.read_text(encoding="utf-8").strip() if p.exists() else "unknown"


def system_commit() -> str:
    return run_git(system_root(), ["rev-parse", "HEAD"]) or "unknown"


def repository_identity(root: Path) -> dict[str, str]:
    return canonical_repository_identity(root)


def external_store(root: Path) -> Path:
    ident = repository_identity(root)
    canonical = config_home() / "projects" / ident["workspace_id"] / "intelligence"
    legacy_id = ident.get("legacy_project_intelligence_id")
    if legacy_id and legacy_id != ident["workspace_id"] and not canonical.exists():
        legacy = config_home() / "projects" / legacy_id / "intelligence"
        if legacy.exists():
            canonical.parent.mkdir(parents=True, exist_ok=True)
            os.replace(legacy, canonical)
            try:
                legacy.parent.rmdir()
            except OSError:
                pass
    return canonical


def local_store(root: Path) -> Path:
    return root / ".ai" / "intelligence"


def intelligence_store(root: Path, create: bool = False) -> tuple[Path, str, str]:
    ident = repository_identity(root)
    # Project Intelligence is user-state data. Legacy .ai/intelligence is
    # imported explicitly, but never remains the active write target.
    store = external_store(root)
    mode = "EPHEMERAL"
    if create:
        (store / "topics").mkdir(parents=True, exist_ok=True)
        (store / "reviews").mkdir(parents=True, exist_ok=True)
    return store, mode, ident["workspace_id"]


def load_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or default










def scoped_sources(root: Path, registry: dict[str, Any], runtime: str, target_path: str | None) -> tuple[list[dict[str, Any]], str, int]:
    """Keep applicable instructions; leave official documents as on-demand pointers."""
    root = root.resolve()
    target = Path(target_path) if target_path else root
    if not target.is_absolute():
        target = root / target
    target = target.resolve()
    try:
        relative = target.relative_to(root)
    except ValueError as exc:
        raise ValueError("target path must remain inside the project") from exc
    directory = relative if target.is_dir() or relative == Path(".") else relative.parent
    selected: list[dict[str, Any]] = []
    excluded = 0
    for source in registry.get("sources") or []:
        if source.get("authority") != "project_instruction":
            selected.append(source)
            continue
        scope = str(source.get("scope") or ".").strip("/") or "."
        in_scope = scope == "." or directory == Path(scope) or Path(scope) in directory.parents
        runtimes = source.get("auto_loaded_by") or []
        runtime_matches = not runtimes or runtime in runtimes
        if in_scope and runtime_matches:
            selected.append(source)
        else:
            excluded += 1
    return selected, directory.as_posix(), excluded






def layered_context(root: Path, store: Path, intel: dict[str, Any], retrieval: dict[str, Any], selected: list[str], freshness_result: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic, non-canonical project capsule and report layer budgets."""
    architecture = intel.get("architecture") or {}
    state = intel.get("state") or {}
    registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []})
    overrides = load_yaml(store / "PROJECT_OVERRIDES.yaml", {})
    temporal = load_yaml(store / "TEMPORAL_ASSERTIONS.yaml", {"schema": {"version": 1}, "assertions": []})
    temporal_snapshot = temporal_active_assertions(root, temporal)
    temporal_active = temporal_snapshot.get("assertions", [])
    sources = [str(item.get("path")) for item in (registry.get("sources") or []) if item.get("path")]
    summary_source = str(architecture.get("summary") or "").strip()
    summary_safe = safe_context_emit(sink="runtime_log", payload=summary_source).get("safe_payload")
    summary = str(summary_safe or "").strip()[:6400]
    approved_override_facts: list[dict[str, str]] = []
    for collection in ("approved_inferences", "additional_rules", "exceptions"):
        for item in overrides.get(collection) or []:
            if not isinstance(item, dict) or str(item.get("status", "APPROVED")).upper() not in {"APPROVED", "ACTIVE"}:
                continue
            safe_override = safe_context_emit(sink="runtime_log", payload={key: str(item[key]) for key in ("id", "scope", "rule", "reason") if item.get(key)}).get("safe_payload") or {}
            approved_override_facts.append({key: str(value)[:240] for key, value in safe_override.items()})
    temporal_summary = [
        safe_item
        for item in temporal_active[:40]
        for safe_item in [safe_context_emit(sink="runtime_log", payload={key: str(item[key]) for key in ("id", "subject", "predicate", "object", "quality", "source") if item.get(key)}).get("safe_payload") or {}]
    ]
    temporal_summary = [{key: str(value)[:120] for key, value in item.items()} for item in temporal_summary]
    temporal_budget_tokens = CONTEXT_TEMPORAL_RESERVE
    bounded_temporal: list[dict[str, str]] = []
    temporal_truncated = len(temporal_active) > len(temporal_summary)
    for item in temporal_summary:
        candidate = [*bounded_temporal, item]
        if math.ceil(len(json.dumps(candidate, ensure_ascii=False)) / 4) > temporal_budget_tokens:
            temporal_truncated = True
            break
        bounded_temporal.append(item)
    temporal_summary = bounded_temporal
    capsule = {
        "canonical": False,
        "derived": True,
        "summary": summary,
        "summary_truncated": len(str(architecture.get("summary") or "").strip()) > 6400,
        "summary_source": "PROJECT_INTELLIGENCE.yaml#/architecture (rebuild from canonical source)",
        "override_source": str(store / "PROJECT_OVERRIDES.yaml"),
        "readiness": state.get("readiness", "PARTIAL"),
        "freshness": freshness_result.get("status", "UNKNOWN"),
        "source_pointers": sources[:12],
        "source_pointers_truncated": len(sources) > 12,
        "active_temporal_assertion_ids": [str(item.get("id"))[:120] for item in temporal_active if item.get("id")][:40],
        "temporal_assertion_ids_truncated": len([item for item in temporal_active if item.get("id")]) > 40,
        "approved_overrides": approved_override_facts[:24],
        "approved_overrides_truncated": len(approved_override_facts) > 24,
        "source_digest": sha(json.dumps({"architecture": architecture, "sources": sources, "temporal": temporal_active, "overrides": overrides}, sort_keys=True, ensure_ascii=False)),
        "estimated_tokens": 0,
        "target_tokens": CONTEXT_CORE_HARD_BUDGET,
    }
    capsule["estimated_tokens"] = math.ceil(len(json.dumps({key: value for key, value in capsule.items() if key != "estimated_tokens"}, ensure_ascii=False)) / 4)
    while capsule["estimated_tokens"] > capsule["target_tokens"] and (capsule["summary"] or capsule["approved_overrides"] or capsule["source_pointers"] or len(capsule["active_temporal_assertion_ids"]) > 40):
        if capsule["summary"]:
            capsule["summary_truncated"] = True
            capsule["summary"] = capsule["summary"][: int(len(capsule["summary"]) * 0.8)]
        elif capsule["approved_overrides"]:
            capsule["approved_overrides_truncated"] = True
            capsule["approved_overrides"].pop()
        elif capsule["source_pointers"]:
            capsule["source_pointers_truncated"] = True
            capsule["source_pointers"].pop()
        else:
            capsule["temporal_assertion_ids_truncated"] = True
            capsule["active_temporal_assertion_ids"].pop()
        capsule["estimated_tokens"] = math.ceil(len(json.dumps({key: value for key, value in capsule.items() if key != "estimated_tokens"}, ensure_ascii=False)) / 4)
    stale_topics = set()
    affected = set(freshness_result.get("affected_topics") or [])
    known_topic_paths = {
        str(store / item.get("path")): name
        for name, item in (intel.get("topics") or {}).items()
        if isinstance(item, dict) and item.get("path")
    }
    selected_topics = {known_topic_paths[path] for path in selected if path in known_topic_paths}
    selected_paths_mapped = bool(selected) and len(selected_topics) == len(selected)
    for topic_path in selected:
        if topic_path not in [str(store / item.get("path")) for item in (intel.get("topics") or {}).values() if isinstance(item, dict) and item.get("path")]:
            continue
        name = Path(topic_path).stem
        if name in affected or "unknown" in affected:
            stale_topics.add(name)
    retrieval_tokens = int(retrieval.get("estimated_tokens") or 0)
    temporal_ids = [str(item.get("id"))[:120] for item in temporal_active if item.get("id")][:40]
    recall_metadata = {
        "topic_pointers": selected[:20],
        "temporal_assertions": temporal_summary,
        "temporal_assertion_ids": temporal_ids,
        "temporal_source": str(store / "TEMPORAL_ASSERTIONS.yaml"),
    }
    recall_metadata_tokens = math.ceil(len(json.dumps(recall_metadata, ensure_ascii=False)) / 4)
    store_freshness = freshness_result.get("status", "UNKNOWN")
    reasons = freshness_result.get("reasons") or []
    topic_only_reasons = bool(reasons) and all(
        reason.startswith(("watched_committed_path_changed:", "dirty_watched_path:"))
        for reason in reasons
    )
    affected_are_known_topics = bool(affected) and affected.issubset(set((intel.get("topics") or {}).keys()))
    irrelevant_proven = (
        store_freshness == "STALE"
        and selected_paths_mapped
        and topic_only_reasons
        and affected_are_known_topics
        and not (selected_topics & affected)
    )
    if store_freshness == "UNKNOWN":
        task_freshness = "UNKNOWN"
    elif store_freshness == "STALE" and not irrelevant_proven:
        task_freshness = "STALE"
    else:
        task_freshness = "CURRENT"
    return {
        "core": capsule,
        "recall": {"topic_pointers": selected[:20], "topic_pointers_truncated": len(selected) > 20, "retrieval_status": retrieval.get("status"), "estimated_tokens": retrieval_tokens + recall_metadata_tokens, "retrieval_tokens": retrieval_tokens, "metadata_tokens": recall_metadata_tokens, "soft_budget_tokens": 4500, "hard_budget_tokens": CONTEXT_RECALL_HARD_BUDGET, "temporal_budget_tokens": temporal_budget_tokens, "temporal_assertions": temporal_summary, "temporal_assertion_ids": temporal_ids, "temporal_source": str(store / "TEMPORAL_ASSERTIONS.yaml"), "truncated": bool(retrieval.get("truncated") or temporal_truncated or len(selected) > 20)},
        "archive": {"on_demand_only": True, "source_pointers": sources[:30]},
        "task_freshness": {"status": task_freshness, "affected_selected_topics": sorted(stale_topics), "selected_topics": sorted(selected_topics), "store_freshness": store_freshness, "irrelevance_proven": store_freshness == "CURRENT" or irrelevant_proven},
        "telemetry": {"core_tokens": capsule["estimated_tokens"], "recall_tokens": retrieval_tokens + recall_metadata_tokens, "total_estimated_tokens": capsule["estimated_tokens"] + retrieval_tokens + recall_metadata_tokens, "hard_budget_tokens": CONTEXT_TOTAL_HARD_BUDGET, "core_truncated": capsule["summary_truncated"], "recall_truncated": bool(retrieval.get("truncated") or temporal_truncated or len(selected) > 20)},
    }


def context_audit(root: Path) -> dict[str, Any]:
    store, mode, pid = intelligence_store(root)
    intel = load_yaml(store / "PROJECT_INTELLIGENCE.yaml", {})
    registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []})
    overrides = load_yaml(store / "PROJECT_OVERRIDES.yaml", {})
    temporal = load_yaml(store / "TEMPORAL_ASSERTIONS.yaml", {"schema": {"version": 1}, "assertions": []})
    issues: list[dict[str, str]] = []
    source_paths = {str(item.get("path")) for item in (registry.get("sources") or []) if item.get("path")}
    for source in (registry.get("sources") or []):
        path = str(source.get("path", ""))
        if path and not (root / path).exists():
            issues.append({"kind": "orphan_source_pointer", "path": path})
        if path and (".env" in Path(path).name.lower() or Path(path).suffix.lower() in {".pem", ".key"}):
            issues.append({"kind": "secret_like_source", "path": path})
        if path and (root / path).is_file() and not is_secret_filename(Path(path).name):
            try:
                source_text = (root / path).read_text(encoding="utf-8", errors="replace")[:1_000_000]
                if any(pattern.search(source_text) for pattern in SECRET_VALUE_PATTERNS):
                    issues.append({"kind": "secret_like_value", "path": path})
            except OSError:
                issues.append({"kind": "unreadable_source", "path": path})
        expected_hash = source.get("hash") or source.get("sha256") or source.get("content_hash")
        if path and expected_hash and (root / path).is_file():
            actual_hash = hashlib.sha256((root / path).read_bytes()).hexdigest()
            expected_hash = str(expected_hash).removeprefix("sha256:")
            if actual_hash != expected_hash:
                issues.append({"kind": "stale_source_hash", "path": path})
    paths = [str(item.get("path")) for item in (registry.get("sources") or []) if item.get("path")]
    for path in sorted({p for p in paths if paths.count(p) > 1}):
        issues.append({"kind": "duplicate_source_pointer", "path": path})
    for topic in (intel.get("topics") or {}).values():
        p = str(topic.get("path", "")) if isinstance(topic, dict) else ""
        if p and not (store / p).exists():
            issues.append({"kind": "missing_topic", "path": p})
        if p and (store / p).is_file():
            topic_text = (store / p).read_text(encoding="utf-8", errors="replace")[:1_000_000]
            if any(pattern.search(topic_text) for pattern in SECRET_VALUE_PATTERNS):
                issues.append({"kind": "secret_like_value", "path": p})
    assertions = [item for item in (temporal.get("assertions") or []) if isinstance(item, dict)]
    assertion_ids = {str(item.get("id")) for item in assertions if item.get("id")}
    temporal_errors = validate_temporal_document(temporal)
    if temporal_errors:
        issues.append({"kind": "invalid_temporal_ledger", "path": "TEMPORAL_ASSERTIONS.yaml"})
    for item in assertions:
        provenance = item.get("provenance") or {}
        source = str(provenance.get("source") or "")
        expected = str(provenance.get("source_hash") or "").removeprefix("sha256:")
        if not source or not expected:
            issues.append({"kind": "missing_temporal_provenance", "path": str(item.get("id", "unknown"))})
        elif (root / source).is_file() and file_hash(root / source) != expected:
            issues.append({"kind": "stale_temporal_source_hash", "path": str(item.get("id", "unknown"))})
    override_entries = [item for key in ("approved_inferences", "additional_rules", "exceptions", "excluded_inferences") for item in (overrides.get(key) or []) if isinstance(item, dict)]
    for item in override_entries:
        temporal_ref = item.get("temporal_assertion_id")
        if temporal_ref and str(temporal_ref) not in assertion_ids:
            issues.append({"kind": "missing_temporal_reference", "path": str(item.get("id", "unknown"))})
        if not item.get("provenance") and not item.get("evidence") and not item.get("approval_id"):
            issues.append({"kind": "missing_override_provenance", "path": str(item.get("id", "unknown"))})
    current_temporal = temporal_active_assertions(root, temporal) if not temporal_errors else {"assertions": [], "excluded": [], "conflicts": []}
    for item in current_temporal.get("excluded", []):
        if item.get("reason"):
            issues.append({"kind": "expired_or_inactive_temporal_fact", "path": str(item.get("id", "unknown"))})
    for conflict in current_temporal.get("conflicts", []):
        issues.append({"kind": "temporal_conflict", "path": str(conflict.get("subject", "unknown"))})
    conflicts = active_authority_conflicts(store, intel, registry, None)
    if conflicts:
        issues.extend({"kind": "authority_conflict", "path": str(item.get("id") or item.get("scope") or "unknown")} for item in conflicts)
    status = "REBUILD_REQUIRED" if any(item["kind"] in {"orphan_source_pointer", "missing_topic", "missing_temporal_reference", "secret_like_source", "secret_like_value", "stale_source_hash", "missing_temporal_provenance", "stale_temporal_source_hash", "missing_override_provenance", "invalid_temporal_ledger"} for item in issues) else ("WARN" if issues else "PASS")
    return {"version": 1, "project_id": pid, "mode": mode, "status": status, "read_only": True, "issues": issues, "metrics": {"registered_sources": len(source_paths), "topics": len(intel.get("topics") or {}), "temporal_assertions": len(assertion_ids), "authority_conflicts": len(conflicts)}, "canonical_facts_modified": False}


def initial_intelligence(root: Path, pid: str, ident: dict[str, str], old_knowledge: Path) -> dict[str, Any]:
    head = run_git(root, ["rev-parse", "HEAD"])
    branch = run_git(root, ["branch", "--show-current"])
    dirty_paths = git_dirty_paths(root)
    return {
        "schema": {"version": SCHEMA_VERSION},
        "generated_by": {"aips_version": system_version(), "aips_commit": system_commit()},
        "project": {
            "id": pid,
            "root": str(root),
            "repository_id": ident["repository_id"],
            "workspace_id": ident["workspace_id"],
            "repository_identity": ident["repository_id"],
            "worktree_identity": ident["worktree_id"],
            "branch": branch,
        },
        "state": {"readiness": "PARTIAL", "review": "UNREVIEWED", "freshness": "CURRENT"},
        "verified": {
            "git_head": head,
            "dirty_paths": dirty_paths[:500],
            "dirty_path_count": len(dirty_paths),
            "dirty_paths_truncated": len(dirty_paths) > 500,
            "verified_at": utc_now(),
        },
        "architecture": {"summary": None, "confidence": None, "source": None},
        "coverage": {
            "required_topics": list(REQUIRED_SEMANTIC_TOPICS),
            "optional_topics": list(OPTIONAL_SEMANTIC_TOPICS),
            "complete_topics": [],
            "not_applicable": {},
        },
        "topics": {},
        "canonical_artifacts": {},
        "migration": {
            "from_project_knowledge": old_knowledge.exists(),
            "sources": [rel(root, old_knowledge)] if old_knowledge.exists() else [],
        },
        "unknowns": [
            "Architecture/data-flow semantic conclusions require Agent enrichment from repository evidence.",
            "Impact Graph relationships require semantic enrichment.",
        ],
        "conflicts": [],
    }


def seed_observation(result: dict[str, Any], attempt: dict[str, Any] | None) -> dict[str, Any]:
    """Attach the fallback diagnostic when a seed was refused or failed; never a path."""
    if attempt and attempt.get("status") in ("REFUSED", "FAILED"):
        result["observations"] = [f"intelligence_seed_fallback:{attempt.get('reason_code')}"]
    return result


def seeded_bootstrap(root: Path, attempt: dict[str, Any]) -> dict[str, Any]:
    store, mode, pid = intelligence_store(root)
    intel = load_yaml(store / "PROJECT_INTELLIGENCE.yaml", {})
    freshness_result = freshness(root)
    review = render_review(root)
    return {
        "project_id": pid,
        "mode": mode,
        "store": str(store),
        "status": "SEEDED",
        "seeded_from": {
            "project_id": attempt["source_project_id"],
            "git_head": attempt["source_git_head"],
            "selection": attempt["selection"],
        },
        "copied_artifact_count": attempt["copied_artifact_count"],
        "excluded_artifact_count": attempt["excluded_artifact_count"],
        "readiness": (intel.get("state") or {}).get("readiness"),
        "freshness": freshness_result["status"],
        "reasons": freshness_result.get("reasons", []),
        "review_html": str(review),
        "next": (
            "Intelligence was seeded and is current for this worktree; no refresh is required."
            if freshness_result["status"] == "CURRENT"
            else "Intelligence was seeded; refresh only the affected topics listed in freshness reasons."
        ),
    }


def bootstrap(root: Path) -> dict[str, Any]:
    legacy = local_store(root) / "PROJECT_INTELLIGENCE.yaml"
    external = external_store(root) / "PROJECT_INTELLIGENCE.yaml"
    if legacy.is_file() and not external.exists():
        migrate_attached(root)
    seed_attempt: dict[str, Any] | None = None
    probe, probe_mode, _probe_pid = intelligence_store(root)
    if probe_mode == "EPHEMERAL" and not (probe / "PROJECT_INTELLIGENCE.yaml").exists():
        seed_attempt = seed_worktree_store(root, probe, schema_version=SCHEMA_VERSION)
        if seed_attempt["status"] == "SEEDED":
            return seeded_bootstrap(root, seed_attempt)
    store, mode, pid = intelligence_store(root, create=True)
    with writer_lock(store):
        if (store / "PROJECT_INTELLIGENCE.yaml").exists():
            return seed_observation({
                "project_id": pid, "mode": mode, "store": str(store),
                "status": "PRESERVED_EXISTING",
                "next": "Use status and refresh-plan; enrich only affected topics before finalize.",
            }, seed_attempt)
        files = safe_walk(root)
        inv = inventory(root, files)
        sources = discover_sources(root, files)
        ident = repository_identity(root)
        old_knowledge = root / ".ai" / "knowledge" / "KNOWLEDGE_INDEX.yaml"
        intel = initial_intelligence(root, pid, ident, old_knowledge)
        registry = {
            "version": 1,
            "sources": sources,
            "runtime_visibility": {
                "codex": [s["path"] for s in sources if "codex" in s["auto_loaded_by"]],
                "claude-code": [s["path"] for s in sources if "claude-code" in s["auto_loaded_by"]],
                "gemini-cli": [s["path"] for s in sources if "gemini-cli" in s["auto_loaded_by"]],
            },
            "deduplication": {"storage": "pointer_over_copy", "runtime_context": "runtime_aware"},
        }
        overrides_path = store / "PROJECT_OVERRIDES.yaml"
        if not overrides_path.exists():
            atomic_yaml(overrides_path, {
                "version": 1,
                "approved_inferences": [],
                "additional_rules": [],
                "exceptions": [],
                "excluded_inferences": [],
                "promotion_approvals": [],
                "conflicts": [],
            })
        atomic_yaml(store / "PROJECT_INTELLIGENCE.yaml", intel)
        atomic_yaml(store / "SOURCE_REGISTRY.yaml", registry)
        atomic_yaml(store / "IMPACT_GRAPH.yaml", seed_impact_graph(inv))
        atomic_yaml(store / "TEMPORAL_ASSERTIONS.yaml", {
            "schema": {"version": 1},
            "assertions": [],
            "semantics": {
                "primary_time_axis": "git_revision_ancestry",
                "valid_time": "project_revision_interval",
                "observed_time": "aips_observation_metadata",
                "unknown_history_policy": "never_infer",
            },
        })
        atomic_yaml(store / "DISCOVERY.yaml", {
            "version": 1,
            "generated_at": utc_now(),
            "read_only": True,
            "secret_values_persisted": False,
            "repository_identity_hash": ident["repository_id"],
            "repository_identity_source_hash": ident["repository_source_hash"],
            "inventory": inv,
        })
    review = render_review(root)
    return seed_observation({
        "project_id": pid,
        "mode": mode,
        "store": str(store),
        "readiness": "PARTIAL",
        "review": "UNREVIEWED",
        "review_html": str(review),
        "next": "Agent semantic enrichment + aips intelligence finalize",
    }, seed_attempt)


def git_dirty_paths(root: Path) -> list[str]:
    """Return complete staged, unstaged and untracked path sets."""
    if run_git(root, ["rev-parse", "--show-toplevel"]) is None:
        return []
    result: set[str] = set()
    for args in (
        ["diff", "--name-only", "-z", "--"],
        ["diff", "--cached", "--name-only", "-z", "--"],
        ["ls-files", "--others", "--exclude-standard", "-z", "--"],
    ):
        result.update(run_git_paths(root, args))
    return sorted(result)


def changed_paths_between(root: Path, old_head: str, new_head: str) -> list[str] | None:
    try:
        return run_git_paths(root, ["diff", "--name-only", "-z", f"{old_head}..{new_head}", "--"])
    except GitPathsError:
        return None


def topic_watch_map(intel: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for name, topic in (intel.get("topics") or {}).items():
        if not isinstance(topic, dict):
            continue
        result[name] = [str(x) for x in topic.get("watch", []) or []]
    return result


def path_matches(path: str, pattern: str) -> bool:
    return _aips_glob_matches(path, pattern, globstar_as_star=True)


def relevant_change(path: str, source_paths: set[str], watches: dict[str, list[str]]) -> tuple[bool, list[str]]:
    affected: list[str] = []
    if path in source_paths:
        affected.append("source-registry")
    for topic, patterns in watches.items():
        if any(path_matches(path, p) for p in patterns):
            affected.append(topic)
    return bool(affected), affected


def freshness(root: Path) -> dict[str, Any]:
    store, mode, pid = intelligence_store(root)
    ip = store / "PROJECT_INTELLIGENCE.yaml"
    if not ip.exists():
        return {
            "status": "MISSING", "mode": mode, "project_id": pid,
            "reasons": ["Project Intelligence not initialized"],
            "affected_topics": [],
        }

    intel = load_yaml(ip, {})
    registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []})
    reasons: list[str] = []
    observations: list[str] = []
    affected_topics: set[str] = set()

    if (intel.get("schema") or {}).get("version") != SCHEMA_VERSION:
        reasons.append("intelligence_schema_changed")
        affected_topics.add("schema")

    ident = repository_identity(root)
    stored_project = intel.get("project") or {}
    if stored_project.get("worktree_identity") and stored_project.get("worktree_identity") != ident["worktree_id"]:
        if seeded_worktree_change_proven(intel, ident, stored_project["worktree_identity"]):
            observations.append("worktree_identity_seeded_from_same_repository")
        else:
            reasons.append("worktree_identity_changed")
            affected_topics.add("project-identity")

    current_branch = run_git(root, ["branch", "--show-current"])
    old_branch = stored_project.get("branch")
    if old_branch != current_branch:
        observations.append(f"branch_changed:{old_branch}->{current_branch}")

    source_paths = {str(s.get("path")) for s in registry.get("sources") or [] if s.get("path")}
    watches = topic_watch_map(intel)

    # Authoritative source hashes are always watched.
    for source in registry.get("sources") or []:
        path_value = str(source.get("path", ""))
        path = root / path_value
        if not path.exists():
            reasons.append(f"source_removed:{path_value}")
            affected_topics.add("source-registry")
            continue
        old_hash = source.get("hash")
        if old_hash and file_hash(path) != old_hash:
            reasons.append(f"source_changed:{path_value}")
            affected_topics.add("source-registry")

    current_head = run_git(root, ["rev-parse", "HEAD"])
    old_head = (intel.get("verified") or {}).get("git_head")
    if old_head and current_head and old_head != current_head:
        diff_paths = changed_paths_between(root, old_head, current_head)
        if diff_paths is None:
            reasons.append("revision_diff_unavailable")
            affected_topics.add("unknown")
        else:
            relevant_count = 0
            for path in diff_paths:
                matched, topics = relevant_change(path, source_paths, watches)
                if matched:
                    relevant_count += 1
                    affected_topics.update(topics)
                    reasons.append(f"watched_committed_path_changed:{path}")
            if relevant_count == 0:
                observations.append(f"git_head_changed_unrelated:{old_head[:8]}->{current_head[:8]}")

    try:
        dirty_paths = git_dirty_paths(root)
    except GitPathsError as exc:
        reasons.append(str(exc))
        affected_topics.add("unknown")
        return {
            "status": "UNKNOWN", "mode": mode, "project_id": pid,
            "reasons": sorted(set(reasons)),
            "observations": sorted(set(observations)),
            "affected_topics": sorted(affected_topics),
            "dirty_paths": [],
            "dirty_path_scan": {"total_count": None, "examined_count": 0, "truncated": True},
            "dirty_paths_display_truncated": False,
        }
    for path in dirty_paths:
        matched, topics = relevant_change(path, source_paths, watches)
        if matched:
            affected_topics.update(topics)
            reasons.append(f"dirty_watched_path:{path}")

    status = "STALE" if reasons else "CURRENT"
    return {
        "status": status,
        "mode": mode,
        "project_id": pid,
        "reasons": sorted(set(reasons)),
        "observations": sorted(set(observations)),
        "affected_topics": sorted(affected_topics),
        "dirty_paths": dirty_paths[:500],
        "dirty_path_scan": {
            "total_count": len(dirty_paths),
            "examined_count": len(dirty_paths),
            "truncated": False,
        },
        "dirty_paths_display_truncated": len(dirty_paths) > 500,
    }


def adapter_capability(runtime: str) -> str:
    state = config_home() / "harness" / "adapters" / f"{runtime}.yaml"
    if state.exists():
        doc = load_yaml(state, {})
        capability = doc.get("capability")
        if capability:
            return str(capability)
    return {
        "codex": "CONTEXT_ALWAYS",
        "claude-code": "CONTEXT_ALWAYS",
        "gemini-cli": "TURN_NATIVE",
    }.get(runtime, "MANUAL")


def adapter_enforcement(runtime: str) -> str:
    state = Path.home() / ".config" / "aips" / "harness" / "adapters" / f"{runtime}.yaml"
    if state.exists():
        doc = load_yaml(state, {})
        value = doc.get("governance_enforcement")
        if value:
            return str(value)
    return {"codex": "ADVISORY", "claude-code": "ADVISORY", "gemini-cli": "ADVISORY"}.get(runtime, "UNSUPPORTED")


def _canonical_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def active_authority_conflicts(
    store: Path,
    intel: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
    runtime: str | None = None,
) -> list[dict[str, Any]]:
    intel = intel or {}
    registry = registry or load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []})
    aliases: dict[str, dict[str, Any]] = {}
    for source in registry.get("sources") or []:
        if not isinstance(source, dict):
            continue
        if source.get("id"):
            aliases[str(source["id"])] = source
        if source.get("path"):
            aliases[str(source["path"])] = source

    overrides = load_yaml(store / "PROJECT_OVERRIDES.yaml", {"conflicts": []})
    result: list[dict[str, Any]] = []
    for origin, items in (("project_overrides", overrides.get("conflicts") or []), ("project_intelligence", intel.get("conflicts") or [])):
        for item in items:
            if not isinstance(item, dict):
                continue
            if str(item.get("status", "OPEN")).upper() in {"RESOLVED", "DISMISSED"}:
                continue
            runtimes = [str(value) for value in (item.get("runtimes") or [])]
            if runtime and runtimes and runtime not in runtimes:
                continue
            entry = dict(item)
            entry.setdefault("origin", origin)
            if "sources" in entry:
                resolved_sources: list[dict[str, Any]] = []
                for source_ref in entry.get("sources") or []:
                    ref = str(source_ref)
                    source = aliases.get(ref)
                    if source is None:
                        resolved_sources.append({"ref": ref, "registered": False})
                    else:
                        resolved_sources.append({
                            "ref": ref,
                            "registered": True,
                            "id": source.get("id"),
                            "path": source.get("path"),
                            "authority": source.get("authority"),
                            "scope": source.get("scope"),
                            "runtime_native": bool(runtime and runtime in (source.get("auto_loaded_by") or [])),
                        })
                entry["sources"] = resolved_sources
            result.append(entry)
    return result


def reconcile_overrides(root: Path) -> dict[str, Any]:
    store, mode, pid = intelligence_store(root)
    intel_path = store / "PROJECT_INTELLIGENCE.yaml"
    overrides_path = store / "PROJECT_OVERRIDES.yaml"
    discovery_path = store / "DISCOVERY.yaml"
    if not intel_path.exists() or not overrides_path.exists() or not discovery_path.exists():
        raise RuntimeError("Project Intelligence, PROJECT_OVERRIDES and DISCOVERY must exist before reconciliation")

    with writer_lock(store):
        overrides = load_yaml(overrides_path, {})
        discovery = load_yaml(discovery_path, {})
        discovered: dict[str, dict[str, Any]] = {}
        for item in discovery.get("inferences") or []:
            if not isinstance(item, dict) or not item.get("id") or "value" not in item:
                continue
            discovered[str(item["id"])] = item

        generated: list[dict[str, Any]] = []
        preserved_assertions = 0
        categories = ("approved_inferences", "additional_rules", "exceptions", "excluded_inferences")
        for category in categories:
            for assertion in overrides.get(category) or []:
                if not isinstance(assertion, dict) or not assertion.get("id") or "value" not in assertion:
                    continue
                preserved_assertions += 1
                assertion_id = str(assertion["id"])
                candidate = discovered.get(assertion_id)
                if not candidate or _canonical_value(candidate.get("value")) == _canonical_value(assertion.get("value")):
                    continue
                conflict_seed = _canonical_value({
                    "category": category,
                    "assertion_id": assertion_id,
                    "approved_value": assertion.get("value"),
                    "discovered_value": candidate.get("value"),
                })
                generated.append({
                    "id": f"conflict-{sha(conflict_seed)[:12]}",
                    "type": "override_discovery_contradiction",
                    "status": "OPEN",
                    "override_category": category,
                    "assertion_id": assertion_id,
                    "approved_value": assertion.get("value"),
                    "discovered_value": candidate.get("value"),
                    "evidence": candidate.get("evidence") or [],
                    "source": "deterministic_override_reconciliation",
                })

        existing = [item for item in (overrides.get("conflicts") or []) if isinstance(item, dict)]
        existing_ids = {str(item.get("id")) for item in existing if item.get("id")}
        new_conflicts = 0
        for conflict in generated:
            if conflict["id"] not in existing_ids:
                existing.append(conflict)
                existing_ids.add(conflict["id"])
                new_conflicts += 1
        overrides["conflicts"] = existing
        atomic_yaml(overrides_path, overrides)

    active = [item for item in existing if str(item.get("status", "OPEN")).upper() not in {"RESOLVED", "DISMISSED"}]
    return {
        "project_id": pid,
        "mode": mode,
        "preserved_assertions": preserved_assertions,
        "discovered_inferences": len(discovered),
        "new_conflicts": new_conflicts,
        "active_conflicts": len(active),
        "conflicts": active,
    }



def promotion_plan(root: Path, topic_name: str) -> dict[str, Any]:
    store, mode, pid = intelligence_store(root)
    intel_path = store / "PROJECT_INTELLIGENCE.yaml"
    if not intel_path.exists():
        raise RuntimeError("Project Intelligence is not initialized")
    intel = load_yaml(intel_path, {})
    candidate, _ = _promotion_candidate(store, intel, topic_name)
    return {"project_id": pid, "mode": mode, **candidate}


def _promotion_target(root: Path, target: str) -> Path:
    return _promotion_target_impl(root, target, SOURCE_NAMES, DOC_EXT)


def promotion_apply(root: Path, topic_name: str, target: str, approval_id: str) -> dict[str, Any]:
    store, mode, pid = intelligence_store(root)
    intel_path = store / "PROJECT_INTELLIGENCE.yaml"
    registry_path = store / "SOURCE_REGISTRY.yaml"
    overrides_path = store / "PROJECT_OVERRIDES.yaml"
    for required in (intel_path, registry_path, overrides_path):
        if not required.exists():
            raise RuntimeError(f"Required Project Intelligence artifact missing: {required.name}")

    target_path = _promotion_target(root, target)
    target_rel = target_path.relative_to(root.resolve()).as_posix()
    if target_path.exists():
        raise RuntimeError(f"Promotion target already exists; automatic overwrite is not allowed: {target_rel}")

    with writer_lock(store):
        intel = load_yaml(intel_path, {})
        registry = load_yaml(registry_path, {"version": 1, "sources": []})
        overrides = load_yaml(overrides_path, {})
        candidate, derived_path = _promotion_candidate(store, intel, topic_name)
        if candidate["status"] != "RECOMMENDED":
            raise RuntimeError(f"Project Intelligence topic is not ready for promotion: {topic_name}")

        approval = None
        for item in overrides.get("promotion_approvals") or []:
            if not isinstance(item, dict) or str(item.get("id")) != approval_id:
                continue
            if (
                str(item.get("status", "")).upper() == "APPROVED"
                and str(item.get("topic")) == topic_name
                and str(item.get("target")) == target_rel
                and str(item.get("approved_by", "")).strip()
                and str(item.get("approved_at", "")).strip()
            ):
                approval = item
                break
        if approval is None:
            raise RuntimeError("Matching APPROVED promotion approval is required before authoritative mutation")

        content = derived_path.read_text(encoding="utf-8")
        source_id = f"src-{sha(target_rel)[:10]}"
        authority = "project_instruction" if target_path.name in SOURCE_NAMES else "official_document"
        auto: list[str] = []
        if target_path.name.startswith("AGENTS"):
            auto.append("codex")
        if target_path.name == "CLAUDE.md":
            auto.append("claude-code")
        if target_path.name == "GEMINI.md":
            auto.append("gemini-cli")

        existing_sources = [item for item in (registry.get("sources") or []) if isinstance(item, dict)]
        if any(str(item.get("path")) == target_rel for item in existing_sources):
            raise RuntimeError(f"SOURCE_REGISTRY already contains promotion target: {target_rel}")
        new_source = {
            "id": source_id,
            "path": target_rel,
            "authority": authority,
            "scope": str(Path(target_rel).parent.as_posix()),
            "hash": sha(content),
            "auto_loaded_by": auto,
            "content_duplicated": False,
            "promoted_from": topic_name,
            "approval_id": approval_id,
        }

        topic = (intel.get("topics") or {}).get(topic_name)
        original_topic = dict(topic)
        original_registry = list(existing_sources)
        original_approval = dict(approval)
        derived_content = content
        target_created = False
        derived_removed = False
        try:
            atomic_text(target_path, content)
            target_created = True
            # Verify bytes before registering authoritative source.
            new_source["hash"] = file_hash(target_path)
            registry["sources"] = sorted([*existing_sources, new_source], key=lambda item: str(item.get("path", "")))

            topic.pop("path", None)
            topic["authoritative_pointer"] = {"source_id": source_id, "path": target_rel}
            topic["content_duplicated"] = False
            topic["promotion"] = {
                "status": "PROMOTED",
                "approval_id": approval_id,
                "approved_by": approval.get("approved_by"),
                "approved_at": approval.get("approved_at"),
                "promoted_at": utc_now(),
            }
            approval["status"] = "APPLIED"
            approval["applied_at"] = utc_now()
            approval["source_id"] = source_id

            atomic_yaml(registry_path, registry)
            atomic_yaml(intel_path, intel)
            atomic_yaml(overrides_path, overrides)
            derived_path.unlink()
            derived_removed = True
        except Exception:
            if target_created:
                with contextlib.suppress(FileNotFoundError):
                    target_path.unlink()
            if derived_removed and not derived_path.exists():
                atomic_text(derived_path, derived_content)
            (intel.get("topics") or {})[topic_name] = original_topic
            registry["sources"] = original_registry
            approval.clear()
            approval.update(original_approval)
            atomic_yaml(registry_path, registry)
            atomic_yaml(intel_path, intel)
            atomic_yaml(overrides_path, overrides)
            raise

    return {
        "project_id": pid,
        "mode": mode,
        "topic": topic_name,
        "status": "PROMOTED",
        "approval_id": approval_id,
        "authoritative_source": target_rel,
        "source_id": source_id,
        "derived_content_removed": True,
        "content_duplicated": False,
    }

def resolve_component_context(store: Path, intel: dict[str, Any], component: str | None) -> tuple[dict[str, Any], list[str]]:
    components = intel.get("components") or {}
    relationships = intel.get("shared_relationships") or {}
    public: dict[str, Any] = {
        "requested": component,
        "resolved": False,
        "system_summary": safe_context_emit(
            sink="runtime_log",
            payload=str((intel.get("architecture") or {}).get("summary") or ""),
        ).get("safe_payload"),
        "target": None,
        "shared_relationships": [],
        "excluded_components": [],
    }
    if not component:
        return public, []
    target = components.get(component)
    if not isinstance(target, dict):
        raise TypeError(f"Unknown Project Intelligence component: {component}")

    loaded_paths: list[str] = []
    target_topics: list[str] = []
    for value in target.get("topics") or []:
        topic_path = store / str(value)
        if not topic_path.is_file():
            raise RuntimeError(f"Component topic is missing: {value}")
        absolute = str(topic_path)
        target_topics.append(absolute)
        loaded_paths.append(absolute)

    shared: list[dict[str, Any]] = []
    for relationship_id in target.get("shared_relationships") or []:
        relationship = relationships.get(str(relationship_id))
        if not isinstance(relationship, dict):
            raise TypeError(f"Unknown shared relationship for component {component}: {relationship_id}")
        relationship_path = relationship.get("path")
        if not relationship_path:
            raise RuntimeError(f"Shared relationship has no path: {relationship_id}")
        absolute_path = store / str(relationship_path)
        if not absolute_path.is_file():
            raise RuntimeError(f"Shared relationship topic is missing: {relationship_path}")
        absolute = str(absolute_path)
        loaded_paths.append(absolute)
        shared.append({
            "id": str(relationship_id),
            "path": absolute,
            "components": [str(value) for value in (relationship.get("components") or [])],
        })

    public.update({
        "resolved": True,
        "target": {
            "id": component,
            "root": target.get("root"),
            "topics": target_topics,
        },
        "shared_relationships": shared,
        "excluded_components": sorted(str(key) for key in components if str(key) != component),
    })
    return public, list(dict.fromkeys(loaded_paths))


def retrieval_failure_code(exc: BaseException) -> str:
    return str(retrieval_index_unavailable(exc).get("reason_code"))


def retrieval_failure_remediation(exc: BaseException) -> str:
    return str(retrieval_index_unavailable(exc).get("remediation"))


def retrieval_needed_for_task(prompt: str, mutation: bool, desired_topics: list[str]) -> bool:
    """Return whether this turn needs Retrieval Intelligence evidence.

    Retrieval is needed only for a non-empty prompt that is a likely mutation
    or that selected task-relevant Intelligence topics. Chat, planning and
    general read turns without topic signals report index status only.
    """
    return bool(prompt.strip()) and (mutation or bool(desired_topics))


def task_refresh_requirement(fr: dict[str, Any], readiness: str, selected: list[str],
                             task_freshness: dict[str, Any]) -> dict[str, Any]:
    """Resolve whether this turn must refresh Intelligence topics.

    Non-READY stale Intelligence keeps the store-wide targeted refresh. READY
    stale Intelligence is advisory: refresh is required only when the
    task-relevant topics are affected or their irrelevance cannot be proven.
    """
    affected = list(fr.get("affected_topics") or [])
    if fr.get("status") != "STALE":
        return {"refresh_required": False, "targeted_refresh": [], "advisory": False,
                "reason": "freshness_not_stale"}
    if readiness != "READY":
        return {"refresh_required": True, "targeted_refresh": affected, "advisory": False,
                "reason": "stale_not_ready"}
    if not selected:
        return {"refresh_required": False, "targeted_refresh": [], "advisory": True,
                "reason": "no_task_relevant_topics"}
    if task_freshness.get("status") == "CURRENT":
        return {"refresh_required": False, "targeted_refresh": [], "advisory": True,
                "reason": "task_topics_not_affected"}
    touched = list(task_freshness.get("affected_selected_topics") or [])
    return {"refresh_required": True, "targeted_refresh": touched or affected, "advisory": True,
            "reason": "task_topics_affected" if touched else "task_relevance_unproven"}


def context_manifest(root: Path, runtime: str, prompt: str, explain: bool = False, component: str | None = None,
                     target_path: str | None = None, intent: str = "auto") -> dict[str, Any]:
    store, mode, pid = intelligence_store(root)
    task_classification = classify_task(prompt, intent)
    category, mutation, desired_topics = classify_prompt(prompt, intent)
    mutation = mutation or task_classification.get("effect") == "external_action"
    system_protocol_routes = route_system_protocols(prompt, mutation, str(system_root()))
    fr = freshness(root)
    intel = load_yaml(store / "PROJECT_INTELLIGENCE.yaml", {}) if (store / "PROJECT_INTELLIGENCE.yaml").exists() else {}
    registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []}) if store.exists() else {"sources": []}
    applicable, target_scope, excluded_sources = scoped_sources(root, registry, runtime, target_path)
    scoped_registry = {**registry, "sources": applicable}
    state = intel.get("state") or {}
    authority_conflicts = active_authority_conflicts(store, intel, scoped_registry, runtime) if store.exists() else []

    available = intel.get("topics") or {}
    selected: list[str] = []
    for name in desired_topics:
        topic = available.get(name)
        if isinstance(topic, dict) and topic.get("path"):
            selected.append(str(store / topic["path"]))
    component_resolution, component_paths = resolve_component_context(store, intel, component)
    selected = list(dict.fromkeys([*selected, *component_paths]))
    recall_preview = layered_context(root, store, intel, {"status": "NOT_QUERIED", "estimated_tokens": 0}, selected, fr)["recall"]
    retrieval_budget = CONTEXT_RECALL_HARD_BUDGET - int(recall_preview.get("estimated_tokens") or 0)
    retrieval_budget = max(0, min(RETRIEVAL_DEFAULT_TOKEN_BUDGET, retrieval_budget))

    retrieval: dict[str, Any] = {
        "status": "INDEX_MISSING",
        "results": [],
        "token_budget": retrieval_budget,
        "estimated_tokens": 0,
    }
    retrieval_state = {"status": "MISSING"}
    if store.exists() and (store / "PROJECT_INTELLIGENCE.yaml").exists():
        try:
            retrieval_state = retrieval_index_status(root, store)
            if retrieval_budget < 256 and prompt:
                retrieval = {
                    "status": "SKIPPED_BUDGET",
                    "reason_code": "RECALL_METADATA_EXHAUSTS_BUDGET",
                    "results": [],
                    "token_budget": retrieval_budget,
                    "estimated_tokens": 0,
                    "truncated": True,
                }
            elif prompt and retrieval_state.get("status") in {"CURRENT", "STALE"}:
                retrieval = retrieval_query_repository(
                    root,
                    store,
                    prompt,
                    token_budget=retrieval_budget,
                    limit=RETRIEVAL_DEFAULT_RESULT_LIMIT,
                    refresh=True,
                )
                sanitized_results: list[dict[str, Any]] = []
                sanitized_count = 0
                for item in retrieval.get("results") or []:
                    if not isinstance(item, dict):
                        continue
                    safety = safe_context_emit(sink="runtime_log", payload=item)
                    safe_item = safety.get("safe_payload")
                    if not isinstance(safe_item, dict):
                        safe_item = {key: value for key, value in item.items() if key != "snippet"}
                        if "snippet" in item:
                            safe_item["snippet"] = "[OMITTED_BY_CONTENT_SAFETY]"
                    if safety.get("decision") in {"REDACT", "REVIEW"}:
                        sanitized_count += 1
                    sanitized_results.append(safe_item)
                retrieval["results"] = sanitized_results
                retrieval["sanitized_results"] = sanitized_count
            else:
                retrieval = {
                    "status": "INDEX_MISSING" if retrieval_state.get("status") == "MISSING" else str(retrieval_state.get("status")),
                    "index": retrieval_state,
                    "results": [],
                    "token_budget": retrieval_budget,
                    "estimated_tokens": 0,
                }
        except (GitPathsError, OSError, RuntimeError, TypeError, ValueError, KeyError, yaml.YAMLError) as exc:
            diagnostic = retrieval_index_unavailable(exc, token_budget=retrieval_budget)
            retrieval = {
                "status": "UNAVAILABLE",
                "reason_code": diagnostic.get("reason_code"),
                "remediation": diagnostic.get("remediation"),
                "index": retrieval_state,
                "results": [],
                "token_budget": retrieval_budget,
                "estimated_tokens": 0,
            }
    layers = layered_context(root, store, intel, retrieval, selected, fr)

    project_native: list[str] = []
    runtime_visible: list[str] = []
    for src in applicable:
        p = str(src.get("path", ""))
        if not p:
            continue
        if runtime in (src.get("auto_loaded_by") or []):
            runtime_visible.append(str(root / p))
        else:
            project_native.append(str(root / p))

    initialize = fr["status"] == "MISSING"
    readiness = state.get("readiness", "PARTIAL") if not initialize else "PARTIAL"
    refresh_plan_for_task = task_refresh_requirement(fr, readiness, selected, layers.get("task_freshness") or {})
    refresh = refresh_plan_for_task["targeted_refresh"]
    retrieval_needed = retrieval_needed_for_task(prompt, mutation, desired_topics)
    task_effect = str(task_classification.get("effect") or "chat_only")
    task_level = "L0" if task_effect == "chat_only" else "L3" if task_effect == "external_action" else "L2"
    if task_effect == "filesystem_write" and task_classification.get("domain") == "creative" and task_classification.get("intent") == "create":
        task_level = "L2" if run_git(root, ["rev-parse", "--show-toplevel"]) else "L1"

    fail_closed_reasons: list[str] = []
    if mutation:
        if system_protocol_routes.get("status") != "READY":
            fail_closed_reasons.append("system_protocol_routes_unavailable")
        if initialize:
            fail_closed_reasons.append("intelligence_missing")
        # READY Intelligence remains useful as advisory context for a confined
        # local L2 write. Keep freshness and targeted refresh facts visible,
        # but do not let staleness alone deny that write.
        if fr["status"] == "STALE" and readiness != "READY":
            fail_closed_reasons.append("intelligence_stale")
        if fr["status"] == "UNKNOWN":
            fail_closed_reasons.append("intelligence_freshness_unknown")
        if readiness != "READY":
            fail_closed_reasons.append(f"intelligence_readiness_{readiness.lower()}")
        if authority_conflicts:
            fail_closed_reasons.append("unresolved_authority_conflict")

    manifest = {
        "version": 1,
        "runtime": {
            "id": runtime,
            "capability": adapter_capability(runtime),
            "governance_enforcement": adapter_enforcement(runtime),
        },
        "project": {
            "id": pid, "root": str(root), "mode": mode,
            "intelligence_store": str(store),
        },
        "task": {
            "prompt_hash": sha(prompt),
            "category": category,
            "mutation_likely": mutation,
            "classification": {**{key: task_classification[key] for key in ("domain", "intent", "effect", "creative_medium")}, "readiness_level": task_level},
        },
        "context": {
            "always": [
                str(system_root() / "harness" / "BOOTSTRAP.md"),
                str(system_root() / "SYSTEM_CORE.md"),
            ],
            "system_protocol_routes": system_protocol_routes,
            "runtime_native": runtime_visible[:30],
            "project_native": project_native[:30],
            "source_scope": {"target_path": target_scope, "excluded_instruction_sources": excluded_sources},
            "intelligence_topics": selected,
            "optional_evidence": [str(store / "DISCOVERY.yaml")] if (store / "DISCOVERY.yaml").exists() else [],
            "retrieval": retrieval,
            "authority_conflicts": authority_conflicts,
            "layers": layers,
        },
        "instruction_resolution": {
            "precedence": [
                "runtime_native_scoped",
                "project_authoritative_scoped",
                "derived_project_intelligence",
            ],
            "authoritative_sources_preserved": True,
            "derived_intelligence_governing": False,
            "conflicts": authority_conflicts,
            "requires_resolution": bool(authority_conflicts),
        },
        "component_resolution": component_resolution,
        "intelligence": {
            "readiness": readiness,
            "review": state.get("review", "UNREVIEWED"),
            "freshness": fr["status"],
        },
        "freshness": {
            "status": fr["status"],
            "reasons": fr.get("reasons", []),
            "observations": fr.get("observations", []),
            "affected_topics": fr.get("affected_topics", []),
            "dirty_path_scan": fr.get("dirty_path_scan"),
            "dirty_paths_display_truncated": fr.get("dirty_paths_display_truncated"),
        },
        "requirements": {
            "initialize_intelligence": initialize,
            "semantic_enrichment_required": readiness != "READY",
            "retrieval_needed": retrieval_needed,
            "retrieval_index_status": str(retrieval_state.get("status") or "MISSING"),
            "retrieval_index_required": bool(
                retrieval_needed
                and (store / "PROJECT_INTELLIGENCE.yaml").exists()
                and retrieval_state.get("status") == "MISSING"
            ),
            "refresh_required": refresh_plan_for_task["refresh_required"],
            "refresh_reason": refresh_plan_for_task["reason"],
            "freshness_advisory": refresh_plan_for_task["advisory"],
            "targeted_refresh": refresh,
            "change_impact_required": mutation,
        },
        "resolution": {
            "explained": explain,
            "decisions": ([
                {"subject": "task.category", "selected": category, "reasons": ["prompt_classification"]},
                {"subject": "system_protocol_routes", "selected": system_protocol_routes, "reasons": ["canonical_task_specific_protocols"]},
                {"subject": "change_impact", "selected": mutation, "reasons": ["existing_project_mutation"] if mutation else ["read_only_or_non_mutating"]},
                {"subject": "intelligence_topics", "selected": selected, "reasons": ["task_relevant_topics_only"]},
                {
                    "subject": "retrieval_intelligence",
                    "selected": {
                        "status": retrieval.get("status"),
                        "result_count": len(retrieval.get("results") or []),
                        "estimated_tokens": retrieval.get("estimated_tokens", 0),
                    },
                    "reasons": ["just_in_time_repository_evidence"],
                },
                {"subject": "governance_enforcement", "selected": adapter_enforcement(runtime), "reasons": ["installed_adapter_state_or_safe_fallback"]},
            ] if explain else []),
        },
        "fail_policy": {
            "mode": "closed" if fail_closed_reasons else "soft",
            "reasons": fail_closed_reasons,
        },
    }
    manifest["context"]["layers"]["telemetry"]["full_manifest_characters"] = len(json.dumps(manifest, ensure_ascii=False))
    return manifest


def topic_is_complete(store: Path, name: str, topic: Any) -> bool:
    if not isinstance(topic, dict):
        return False
    if topic.get("not_applicable") is True and topic.get("reason"):
        return True
    path_value = topic.get("path")
    if not path_value:
        return False
    p = store / str(path_value)
    if not p.is_file() or p.stat().st_size < 40:
        return False
    if topic.get("type") not in {"FACT", "INTERPRETATION", "OBSERVED_CONVENTION"}:
        return False
    if topic.get("type") != "FACT" and topic.get("confidence") not in {"low", "medium", "high"}:
        return False
    return bool(topic.get("evidence"))


def finalize(root: Path) -> dict[str, Any]:
    store, mode, pid = intelligence_store(root)
    ip = store / "PROJECT_INTELLIGENCE.yaml"
    if not ip.exists():
        raise RuntimeError("Project Intelligence is not initialized")
    with writer_lock(store):
        intel = load_yaml(ip, {})
        complete: list[str] = []
        missing: list[str] = []
        topics = intel.get("topics") or {}
        for name in REQUIRED_SEMANTIC_TOPICS:
            topic = topics.get(name)
            if topic_is_complete(store, name, topic):
                complete.append(name)
            else:
                missing.append(name)

        graph = load_yaml(store / "IMPACT_GRAPH.yaml", {})
        graph_has_structure = isinstance(graph.get("nodes"), dict) and isinstance(graph.get("edges"), list)
        if not graph_has_structure:
            missing.append("impact-graph")

        state = intel.setdefault("state", {})
        coverage = intel.setdefault("coverage", {})
        coverage["required_topics"] = list(REQUIRED_SEMANTIC_TOPICS)
        coverage["complete_topics"] = complete
        readiness = "READY" if not missing else "PARTIAL"
        state["readiness"] = readiness
        state["freshness"] = "CURRENT"
        intel["generated_by"] = {"aips_version": system_version(), "aips_commit": system_commit()}
        ident = repository_identity(root)
        project = intel.setdefault("project", {})
        project["worktree_identity"] = ident["worktree_id"]
        project["branch"] = run_git(root, ["branch", "--show-current"])
        dirty_paths = git_dirty_paths(root)
        intel["verified"] = {
            "git_head": run_git(root, ["rev-parse", "HEAD"]),
            "dirty_paths": dirty_paths[:500],
            "dirty_path_count": len(dirty_paths),
            "dirty_paths_truncated": len(dirty_paths) > 500,
            "verified_at": utc_now(),
        }
        atomic_yaml(ip, intel)
        # Finalization records semantic work; it cannot silently approve stale sources.
        current_freshness = freshness(root)
        state["freshness"] = current_freshness["status"]
        atomic_yaml(ip, intel)
    review = render_review(root)
    return {
        "project_id": pid,
        "mode": mode,
        "readiness": readiness,
        "missing": missing,
        "freshness": current_freshness["status"],
        "reasons": current_freshness.get("reasons", []),
        "review_html": str(review),
    }


def refresh_plan(root: Path) -> dict[str, Any]:
    """Describe exact source changes without mutating or approving Intelligence."""
    store, mode, pid = intelligence_store(root)
    registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []})
    changes = []
    for source in registry.get("sources") or []:
        relative = str(source.get("path") or "")
        path = root / relative
        if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            continue
        if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink() or not path.is_file():
            changes.append({"path": relative, "status": "UNAVAILABLE"})
            continue
        digest = file_hash(path)
        if digest != source.get("hash"):
            changes.append({"path": relative, "status": "CHANGED", "current_hash": digest})
    report = freshness(root)
    return {
        "project_id": pid, "mode": mode, "status": report["status"],
        "affected_topics": report.get("affected_topics", []),
        "reasons": report.get("reasons", []), "source_changes": changes,
        "steps": [
            "Review changed sources and enrich affected semantic topics.",
            "Update only reviewed SOURCE_REGISTRY hashes; retain review status and partial graph coverage.",
            "Run finalize, then status; resolve any remaining stale reasons.",
            "Refresh the retrieval index without --force using a writable cache including SQLite sidecars.",
        ],
        "read_only": True,
    }


def refresh(root: Path) -> dict[str, Any]:
    """Refresh revision metadata only when the committed tree is unchanged."""
    store, mode, pid = intelligence_store(root)
    ip = store / "PROJECT_INTELLIGENCE.yaml"
    if not ip.exists():
        raise RuntimeError("Project Intelligence is not initialized")
    dirty_paths = git_dirty_paths(root)
    if dirty_paths:
        return {
            "project_id": pid,
            "mode": mode,
            "status": "BLOCKED",
            "reason": "working_tree_dirty",
            "dirty_paths": dirty_paths[:500],
        }
    with writer_lock(store):
        intel = load_yaml(ip, {})
        old_head = str((intel.get("verified") or {}).get("git_head") or "")
        current_head = run_git(root, ["rev-parse", "HEAD"])
        if not old_head:
            raise RuntimeError("Project Intelligence has no verified git_head")
        try:
            old_tree = run_git(root, ["rev-parse", f"{old_head}^{{tree}}"])
            current_tree = run_git(root, ["rev-parse", "HEAD^{tree}"])
        except RuntimeError:
            return {"project_id": pid, "mode": mode, "status": "BLOCKED", "reason": "verified_revision_unavailable"}
        if old_tree != current_tree:
            report = freshness(root)
            return {
                "project_id": pid,
                "mode": mode,
                "status": "SEMANTIC_REFRESH_REQUIRED",
                "affected_topics": report.get("affected_topics") or [],
                "reasons": report.get("reasons") or [],
                "next": "aips intelligence refresh-plan --project <project>",
            }
        ident = repository_identity(root)
        intel.setdefault("project", {})["worktree_identity"] = ident["worktree_id"]
        intel["project"]["branch"] = run_git(root, ["branch", "--show-current"])
        intel.setdefault("state", {})["freshness"] = "CURRENT"
        intel["verified"] = {
            "git_head": current_head,
            "dirty_paths": [],
            "dirty_path_count": 0,
            "dirty_paths_truncated": False,
            "verified_at": utc_now(),
        }
        atomic_yaml(ip, intel)
        intel["state"]["freshness"] = freshness(root)["status"]
        atomic_yaml(ip, intel)
    review = render_review(root)
    return {
        "project_id": pid,
        "mode": mode,
        "status": "REFRESHED_EQUIVALENT_TREE",
        "old_head": old_head,
        "current_head": current_head,
        "review_html": str(review),
    }


def impact_path(root: Path, change_id: str) -> Path:
    _store, _mode, workspace_id = intelligence_store(root, create=True)
    return state_home() / "projects" / workspace_id / "changes" / f"{change_id}.yaml"


def impact_init(root: Path, prompt: str, change_id: str | None, *, reset: bool = False) -> dict[str, Any]:
    store, mode, _pid = intelligence_store(root, create=True)
    graph_path = store / "IMPACT_GRAPH.yaml"
    change_id = change_id or f"change-{sha(prompt)[:12]}"
    path = impact_path(root, change_id)
    doc = {
        "version": 1,
        "change": {"id": change_id, "target": [], "summary": prompt or None},
        "inputs": [], "outputs": [], "data": [], "events": [], "consumers": [],
        "security_boundaries": [], "invariants": [],
        "compatibility": {"api_breaking": None, "migration_required": None, "reasons": []},
        "tests": [], "observability": [], "documentation": [],
        "impact_graph": str(graph_path),
        "unknowns": ["Agent must resolve semantic impact before mutation."],
        "scope_review": {"status": "PENDING", "approval_reference": None, "approved_at": None},
        "reconciliation": {
            "status": "PENDING", "base_revision": None, "head_revision": None,
            "diff_digest": None, "impact_graph_reviewed": False, "evidence": [],
        },
        "status": "DRAFT",
    }
    backup: Path | None = None
    with writer_lock(store):
        if path.exists():
            if not reset:
                existing = load_yaml(path, {})
                raise ValueError(
                    f"Change Impact record already exists: {path} "
                    f"(status: {existing.get('status', 'UNKNOWN')}); use a new --change-id or --reset"
                )
            stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%S%fZ")
            backup = path.with_name(f"{path.stem}.backup-{stamp}.yaml")
            with path.open("rb") as source, backup.open("xb") as target:
                shutil.copyfileobj(source, target)
        atomic_yaml(path, doc)
    result = {"change_id": change_id, "path": str(path), "mode": mode, "status": "DRAFT"}
    if backup is not None:
        result["backup_path"] = str(backup)
    return result


def impact_traverse(
    root: Path,
    artifact_path: Path | None,
    seeds: list[dict[str, Any]],
    risk_class: str,
    directions: list[str] | None,
    max_depth: int | None,
    max_nodes: int,
    max_edges: int,
    changed_paths: list[str],
    graph_seed_ids: list[str] | None = None,
) -> dict[str, Any]:
    store, _mode, _pid = intelligence_store(root)
    result = retrieval_traverse_change_impact(
        root,
        store,
        seeds,
        risk_class,
        directions=directions,
        max_depth=max_depth,
        max_nodes=max_nodes,
        max_edges=max_edges,
        changed_paths=changed_paths,
    )
    graph = load_yaml(store / "IMPACT_GRAPH.yaml", {})
    graph_result = traverse_architecture_impact_graph(
        graph,
        seeds,
        graph_seed_ids or [],
        result.get("directions") or [],
        int(result.get("max_depth") or 0),
        max(1, max_nodes - int(result.get("visited_nodes") or 0)),
        max(1, max_edges - int(result.get("visited_edges") or 0)),
        changed_paths,
    )
    result["architecture_graph"] = graph_result
    result["nodes"].extend(graph_result.get("nodes") or [])
    result["paths"].extend(graph_result.get("paths") or [])
    result["evidence"].extend(graph_result.get("evidence") or [])
    result["unresolved"].extend(graph_result.get("unresolved") or [])
    result["resolution"]["exact"].extend(graph_result.get("resolution", {}).get("exact") or [])
    result["resolution"]["unresolved"].extend(graph_result.get("resolution", {}).get("unresolved") or [])
    for direction, depth in (graph_result.get("reached_depth") or {}).items():
        result.setdefault("reached_depth", {})[direction] = max(
            int(result.get("reached_depth", {}).get(direction, 0)), int(depth)
        )
    result["visited_nodes"] += int(graph_result.get("visited_nodes") or 0)
    result["visited_edges"] += int(graph_result.get("visited_edges") or 0)
    result["truncated"] = bool(result.get("truncated") or graph_result.get("truncated"))
    if result["truncated"]:
        result["status"] = "TRUNCATED"
    elif graph_result.get("status") != "COMPLETE" and result.get("status") == "COMPLETE":
        result["status"] = "BOUNDED_WITH_UNKNOWNS"
    if result.get("status") == "COMPLETE" and not result.get("stop_reason"):
        result["stop_reason"] = "frontier_exhausted"
    if artifact_path is not None:
        doc = load_yaml(artifact_path, {})
        if not isinstance(doc, dict):
            result["artifact_error"] = "change impact artifact must be a YAML mapping"
            return result
        if str(doc.get("status", "DRAFT")).upper() not in {"DRAFT", "IMPLEMENTATION_APPROVED"}:
            result["artifact_error"] = "traversal can only update a DRAFT or IMPLEMENTATION_APPROVED artifact"
            return result
        change = doc.setdefault("change", {})
        change["risk_class"] = risk_class
        doc["traversal"] = result
        atomic_yaml(artifact_path, doc)
        result["artifact_path"] = str(artifact_path)
    return result


from project_intelligence_impact_graph import (
    generate_relation_candidates as _generate_relation_candidates,
)
from project_intelligence_impact_graph import (
    traverse_architecture_impact_graph,
)

CODE_EXT = _project_intelligence_discovery.CODE_EXT
DOC_EXT = _project_intelligence_discovery.DOC_EXT
MANIFEST_NAMES = _project_intelligence_discovery.MANIFEST_NAMES
SECRET_NAMES = _project_intelligence_discovery.SECRET_NAMES
discover_sources = _project_intelligence_discovery.discover_sources
file_hash = _project_intelligence_discovery.file_hash
inventory = _project_intelligence_discovery.inventory
is_secret_filename = _project_intelligence_discovery.is_secret_filename
rel = _project_intelligence_discovery.rel
safe_walk = _project_intelligence_discovery.safe_walk
seed_impact_graph = _project_intelligence_discovery.seed_impact_graph
sha = _project_intelligence_discovery.sha

# Keep the legacy facade bound to the same implementation objects.


def impact_candidates(
    root: Path,
    seed_paths: list[str],
    *,
    max_files: int = 8000,
    max_candidates: int = 300,
    max_depth: int = 1,
) -> dict[str, Any]:
    """Expose bounded source candidates without changing canonical graph state."""
    return _generate_relation_candidates(
        root, seed_paths, max_files=max_files, max_candidates=max_candidates, max_depth=max_depth,
    )


def _validate_directional_traversal_evidence(
    doc: dict[str, Any], traversal: dict[str, Any], policy: dict[str, Any],
) -> tuple[list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    reports = traversal.get("reports")
    required_directions = {"callers", "consumers"}
    directions = traversal.get("directions")
    if traversal.get("policy_version") != 2 or traversal.get("policy") != "risk-adaptive-bounded":
        errors.append("directional traversal evidence has an unsupported policy version")
    if traversal.get("mode") != "directional_reviewed_scope":
        errors.append("directional traversal evidence has an unsupported mode")
    scope_id = traversal.get("scope_id")
    if not isinstance(scope_id, str) or not scope_id.strip():
        errors.append("directional traversal requires an exact scope_id")
    if (
        not isinstance(directions, list)
        or any(not isinstance(direction, str) for direction in directions)
        or set(directions) != required_directions
        or len(directions) != len(required_directions)
    ):
        errors.append("high-risk directional traversal must declare callers and consumers exactly once")
    if not isinstance(reports, dict) or set(reports) != required_directions:
        errors.append("directional traversal requires exactly one report for callers and consumers")
        reports = reports if isinstance(reports, dict) else {}

    expected_unknowns: dict[tuple[str, str], tuple[str, str]] = {}
    expected_nodes: dict[tuple[str, str], tuple[str, dict[str, Any]]] = {}
    report_nodes: list[dict[str, Any]] = []
    common_seeds_digest: str | None = None
    for direction in sorted(required_directions):
        report = reports.get(direction)
        label = f"traversal reports.{direction}"
        if not isinstance(report, dict):
            errors.append(f"{label} must be a traversal mapping")
            continue
        if report.get("policy_version") != 1 or report.get("policy") != "risk-adaptive-bounded":
            errors.append(f"{label} has an unsupported source report policy")
        if report.get("risk_class") != (doc.get("change") or {}).get("risk_class"):
            errors.append(f"{label} risk_class does not match the approved change")
        seeds_digest = _impact_evidence_digest(report.get("seeds"))
        if not isinstance(report.get("seeds"), list) or not report.get("seeds"):
            errors.append(f"{label} requires non-empty exact seed evidence")
        elif common_seeds_digest is None:
            common_seeds_digest = seeds_digest
        elif seeds_digest != common_seeds_digest:
            errors.append("directional traversal reports must use the same exact seeds")
        report_directions = report.get("directions")
        if report_directions != [direction]:
            errors.append(f"{label} must contain only its named traversal direction")
        if report.get("truncated") is not False:
            errors.append("truncated directional traversal cannot establish scoped evidence")
        if report.get("status") not in {"COMPLETE", "BOUNDED_WITH_UNKNOWNS"}:
            errors.append(f"{label} is incomplete")
        unresolved = report.get("unresolved")
        if not isinstance(unresolved, list):
            errors.append(f"{label} unresolved must be a list")
            unresolved = []
        expected_status = "BOUNDED_WITH_UNKNOWNS" if unresolved else "COMPLETE"
        if report.get("status") != expected_status:
            errors.append(f"{label} status does not match its unresolved findings")
        try:
            required_depth = int((report.get("required_depth") or {}).get(direction, -1))
        except (TypeError, ValueError, AttributeError):
            required_depth = -1
        try:
            reached_depth = int((report.get("reached_depth") or {}).get(direction, -1))
        except (TypeError, ValueError, AttributeError):
            reached_depth = -1
        try:
            max_depth = int(report.get("max_depth", -1))
        except (TypeError, ValueError):
            max_depth = -1
        minimum_depth = int(policy.get("required_depth", 0))
        if required_depth < minimum_depth or reached_depth < minimum_depth:
            errors.append(f"{label} does not reach the risk policy minimum depth")
        limits = report.get("limits") or {}
        counters = {
            "nodes": ("visited_nodes", IMPACT_MAX_NODES),
            "edges": ("visited_edges", IMPACT_MAX_EDGES),
            "depth": ("max_depth", IMPACT_MAX_DEPTH),
            "caller_candidates": ("caller_candidates_scanned", IMPACT_MAX_CALLER_CANDIDATES),
        }
        for limit_name, (counter_name, absolute_cap) in counters.items():
            try:
                limit_value = int(limits.get(limit_name, -1))
                counter_value = int(report.get(counter_name, -1))
            except (TypeError, ValueError, AttributeError):
                limit_value = counter_value = -1
            if limit_value < 0 or limit_value > absolute_cap or counter_value < 0 or counter_value > limit_value:
                limit_label = {
                    "nodes": "node", "edges": "edge", "depth": "depth",
                    "caller_candidates": "caller candidate",
                }[limit_name]
                errors.append(f"{label} {counter_name} exceeds the approved {limit_label} limit")
        try:
            depth_limit = int(limits.get("depth", -1))
        except (TypeError, ValueError, AttributeError):
            depth_limit = -1
        graph = report.get("architecture_graph") or {}
        if not isinstance(graph, dict):
            graph = {}
        if max_depth < reached_depth or depth_limit < 0 or max_depth > depth_limit:
            errors.append(f"{label} reached depth exceeds its recorded depth budget")
        scope_ids = graph.get("coverage_scope_ids")
        if graph.get("status") != "COMPLETE" or not isinstance(scope_ids, list) or scope_id not in scope_ids:
            errors.append(f"{label} lacks complete evidence for the exact scope_id")
        report_digest = _impact_evidence_digest(report)
        if not report_digest:
            errors.append(f"{label} cannot be fingerprinted")
        for unresolved_item in unresolved:
            fingerprint = _impact_evidence_digest(unresolved_item)
            if fingerprint:
                key = (direction, fingerprint)
                if key in expected_unknowns:
                    errors.append(f"{label} contains a duplicate unresolved fingerprint")
                expected_unknowns[key] = (str(report_digest or ""), "")
        if isinstance(report.get("nodes"), list):
            for node in report["nodes"]:
                if not isinstance(node, dict) or node.get("kind") == "seed":
                    continue
                node_digest = _impact_evidence_digest(node)
                if not node_digest:
                    errors.append(f"{label} contains a node that cannot be fingerprinted")
                    continue
                key = (direction, node_digest)
                if key in expected_nodes:
                    errors.append(f"{label} contains a duplicate affected-node fingerprint")
                else:
                    expected_nodes[key] = (str(report_digest or ""), node)

    reviewed: set[tuple[str, str]] = set()
    for index, unknown in enumerate(doc.get("unknowns") or []):
        if not isinstance(unknown, dict) or "traversal_review" not in unknown:
            continue
        review = unknown.get("traversal_review") or {}
        if not isinstance(review, dict):
            errors.append(f"unknowns[{index}] traversal_review must be a mapping")
            continue
        direction = review.get("direction")
        fingerprint = review.get("unresolved_sha256")
        key = (str(direction), str(fingerprint))
        expected = expected_unknowns.get(key)
        if expected is None:
            errors.append(f"unknowns[{index}] traversal review does not match an exact unresolved record")
            continue
        if key in reviewed:
            errors.append(f"unknowns[{index}] duplicates a reviewed unresolved disposition")
            continue
        reviewed.add(key)
        if review.get("report_sha256") != expected[0]:
            errors.append(f"unknowns[{index}] traversal report SHA-256 is stale")
        if review.get("disposition") != "reviewed_safe" or str(unknown.get("disposition") or "").upper() != "ACCEPTED_LIMITATION":
            errors.append(f"unknowns[{index}] must use a human-approved reviewed_safe ACCEPTED_LIMITATION")
        human_review = unknown.get("review") or {}
        if not isinstance(human_review, dict):
            human_review = {}
        if str(human_review.get("status") or "").upper() != "APPROVED" or str(human_review.get("reviewer") or "").lower() != "human":
            errors.append(f"unknowns[{index}] traversal disposition requires explicit Human approval")
    if reviewed != set(expected_unknowns):
        errors.append("unresolved relationship lacks exactly one reviewed disposition")

    node_reviews = traversal.get("node_reviews")
    if not isinstance(node_reviews, list):
        errors.append("directional traversal node_reviews must be a list")
        node_reviews = []
    reviewed_nodes: set[tuple[str, str]] = set()
    for index, node_review in enumerate(node_reviews):
        label = f"traversal.node_reviews[{index}]"
        if not isinstance(node_review, dict):
            errors.append(f"{label} must be a mapping")
            continue
        key = (str(node_review.get("direction")), str(node_review.get("node_sha256")))
        expected_node = expected_nodes.get(key)
        if expected_node is None:
            errors.append(f"{label} does not match an exact affected node")
            continue
        if key in reviewed_nodes:
            errors.append(f"{label} duplicates an affected-node review")
            continue
        reviewed_nodes.add(key)
        report_digest, node = expected_node
        if node_review.get("report_sha256") != report_digest:
            errors.append(f"{label} source report SHA-256 is stale")
        disposition = node_review.get("disposition")
        if disposition not in {"reviewed_safe", "requires_change", "unknown"}:
            errors.append(f"{label} has no valid final disposition")
            continue
        report_nodes.append(dict(node, _impact_direction=key[0], _impact_review_disposition=disposition))
    if reviewed_nodes != set(expected_nodes):
        errors.append("affected traversal node lacks exactly one scoped review")
    return errors, report_nodes


def validate_traversal_evidence(doc: dict[str, Any], changed_files: list[str] | None = None) -> list[str]:
    errors: list[str] = []
    change = doc.get("change") or {}
    risk_class = change.get("risk_class")
    traversal = doc.get("traversal")
    if not risk_class:
        if traversal:
            errors.append("traversal evidence requires change.risk_class")
        return errors
    policy = risk_adaptive_policy(str(risk_class))
    if policy.get("status"):
        errors.append(f"unsupported change.risk_class: {risk_class}")
        return errors
    requires_traversal = int(policy["required_depth"]) > 0
    if not isinstance(traversal, dict):
        if requires_traversal:
            errors.append("risk-classified change requires traversal evidence")
        return errors
    if traversal.get("mode") == "directional_reviewed_scope":
        directional_errors, traversal_nodes = _validate_directional_traversal_evidence(doc, traversal, policy)
        errors.extend(directional_errors)
        declared_paths = {str(path) for path in change.get("target_paths") or []}
        actual_paths = {str(path) for path in (changed_files or [])}
        for node in traversal_nodes:
            path = str(node.get("path") or "")
            disposition = node.get("_impact_review_disposition")
            if disposition == "requires_change" and path and path not in declared_paths:
                errors.append(f"required affected path is outside approved target_paths: {path}")
            if changed_files is not None:
                expected = "affected_and_changed" if path in actual_paths else "affected_but_unchanged"
                if node.get("impact_status") != expected:
                    errors.append(f"affected node status does not match the actual diff: {path or node.get('symbol', 'unknown')}")
            if disposition == "unknown":
                errors.append(f"directional traversal affected node remains unresolved: {path or node.get('symbol', 'unknown')}")
        return errors
    if traversal.get("policy_version") != 1 or traversal.get("policy") != "risk-adaptive-bounded":
        errors.append("traversal evidence has an unsupported policy version")
    recorded_depths = traversal.get("required_depth")
    if not isinstance(recorded_depths, dict):
        recorded_depths = {}
        errors.append("traversal required_depth must be a mapping")
    try:
        caller_depth = int(recorded_depths.get("callers", -1))
    except (TypeError, ValueError):
        caller_depth = -1
    try:
        consumer_depth = int(recorded_depths.get("consumers", 0))
    except (TypeError, ValueError):
        consumer_depth = -1
    if caller_depth < int(policy["required_depth"]):
        errors.append("traversal caller depth is below the risk policy minimum")
    if "consumers" in (traversal.get("directions") or []) and consumer_depth < int(policy["required_depth"]):
        errors.append("traversal consumer depth is below the risk policy minimum")
    if traversal.get("truncated") is True:
        errors.append("truncated traversal cannot establish impact completeness")
    if traversal.get("status") not in {"COMPLETE", "BOUNDED_WITH_UNKNOWNS"}:
        errors.append("traversal status is incomplete")
    # Keep readiness aligned with the adaptive policy table: every class that
    # requires a multi-hop traversal is treated as high risk here.
    policy = risk_adaptive_policy(str(risk_class))
    high_risk = int(policy.get("required_depth", 0)) >= 2
    unresolved = traversal.get("unresolved") or []
    if high_risk and (traversal.get("status") != "COMPLETE" or unresolved):
        errors.append("high-risk change has unresolved traversal relationships")
    declared_paths = {str(path) for path in change.get("target_paths") or []}
    actual_paths = {str(path) for path in (changed_files or [])}
    for node in traversal.get("nodes") or []:
        if not isinstance(node, dict) or node.get("kind") == "seed":
            continue
        path = str(node.get("path") or "")
        disposition = node.get("disposition")
        if disposition not in {"reviewed_safe", "requires_change", "unknown"}:
            errors.append(
                "affected node lacks a final disposition: "
                f"{path or node.get('symbol', 'unknown')}; after reviewing its callers/consumers, "
                "set disposition to reviewed_safe, requires_change or unknown, then rerun "
                "`aips intelligence impact-validate`"
            )
            continue
        if disposition == "requires_change" and path and path not in declared_paths:
            errors.append(f"required affected path is outside approved target_paths: {path}")
        impact_status = node.get("impact_status")
        if changed_files is not None:
            expected = "affected_and_changed" if path in actual_paths else "affected_but_unchanged"
            if impact_status != expected:
                errors.append(f"affected node status does not match the actual diff: {path or node.get('symbol', 'unknown')}")
        if disposition == "unknown" and high_risk:
            errors.append(
                f"high-risk affected node remains unresolved: {path or node.get('symbol', 'unknown')}; "
                "inspect the relationship and either expand target_paths for required changes, "
                "record reviewed_safe with evidence, or resolve the traversal unknown before validation"
            )
    return errors


IMPACT_UNKNOWN_DISPOSITIONS = {"OPEN", "RESOLVED", "MITIGATED", "ACCEPTED_LIMITATION"}


def _impact_evidence_digest(value: Any) -> str | None:
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError):
        return None
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _validate_impact_unknown_evidence(evidence: Any, doc: dict[str, Any], root: Path | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(evidence, list) or not evidence:
        return ["closed unknown disposition requires a non-empty evidence list"]
    for index, item in enumerate(evidence):
        label = f"evidence[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be a mapping")
            continue
        kind = item.get("kind")
        if kind == "repository_file":
            raw_path = item.get("path")
            digest = item.get("sha256")
            if not isinstance(raw_path, str) or not raw_path or Path(raw_path).is_absolute() or ".." in Path(raw_path).parts:
                errors.append(f"{label} must use an in-root repository-relative file path")
                continue
            if not isinstance(digest, str) or not re.fullmatch(r"(?:sha256:)?[0-9a-fA-F]{64}", digest):
                errors.append(f"{label} requires a SHA-256 digest")
                continue
            if root is None:
                errors.append(f"{label} cannot be verified without a project root")
                continue
            try:
                project = project_root(root).resolve(strict=True)
                evidence_path = (project / raw_path).resolve(strict=True)
                evidence_path.relative_to(project)
                if not evidence_path.is_file():
                    raise OSError("not a regular file")
                actual = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            except (OSError, RuntimeError, ValueError):
                errors.append(f"{label} path is missing, unreadable, or outside the project root")
                continue
            if digest.removeprefix("sha256:").lower() != actual:
                errors.append(f"{label} SHA-256 does not match the current file")
        elif kind == "traversal":
            traversal = doc.get("traversal")
            digest = item.get("sha256")
            if not isinstance(traversal, dict) or not isinstance(digest, str):
                errors.append(f"{label} requires a recorded traversal and its SHA-256 digest")
                continue
            actual = _impact_evidence_digest(traversal)
            if not actual or digest.removeprefix("sha256:").lower() != actual.removeprefix("sha256:"):
                errors.append(f"{label} SHA-256 does not match the recorded traversal")
                continue
            if traversal.get("status") != "COMPLETE" or traversal.get("truncated") is True or traversal.get("unresolved"):
                errors.append(f"{label} traversal must be complete, non-truncated, and unresolved-free")
                continue
            scope_id = item.get("scope_id")
            graph = traversal.get("architecture_graph") or {}
            if scope_id:
                if graph.get("status") != "COMPLETE":
                    errors.append(f"{label} scoped traversal graph must be complete")
                if not isinstance(scope_id, str) or scope_id not in (graph.get("coverage_scope_ids") or []):
                    errors.append(f"{label} scope_id is not present in the recorded traversal")
            else:
                coverage = graph.get("coverage") or {}
                dimensions = ("api", "data", "events", "consumers")
                if graph.get("status") != "COMPLETE" or any(
                    str(coverage.get(key) or "unknown").lower() not in {"complete", "covered", "full", "ready"}
                    for key in dimensions
                ):
                    errors.append(f"{label} requires complete repository-wide graph coverage or an explicit scope_id")
        else:
            errors.append(f"{label} has an unsupported evidence kind")
    return errors


def validate_impact_unknown_dispositions(doc: dict[str, Any], root: Path | None = None) -> list[str]:
    """Fail closed unless every discovered unknown has an explicit reviewed disposition."""
    unknowns = doc.get("unknowns")
    if not isinstance(unknowns, list):
        return ["unknowns must be a list"]
    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(unknowns):
        label = f"unknowns[{index}]"
        if isinstance(item, str):
            errors.append(f"legacy string unknown remains unresolved at {label}")
            continue
        if not isinstance(item, dict):
            errors.append(f"{label} must be a legacy string or structured mapping")
            continue
        disposition = str(item.get("disposition") or "").upper()
        if disposition not in IMPACT_UNKNOWN_DISPOSITIONS:
            errors.append(f"{label} has an unsupported disposition")
            continue
        if not isinstance(item.get("id"), str) or not item["id"].strip():
            errors.append(f"{label} requires a non-empty id")
        elif item["id"] in seen_ids:
            errors.append(f"{label} duplicates an existing unknown id")
        else:
            seen_ids.add(item["id"])
        if not isinstance(item.get("description"), str) or not item["description"].strip():
            errors.append(f"{label} requires a non-empty description")
        if disposition == "OPEN":
            errors.append(f"{label} remains open")
            continue
        if not isinstance(item.get("resolution"), str) or not item["resolution"].strip():
            errors.append(f"{label} requires a substantive resolution")
        errors.extend(f"{label}: {error}" for error in _validate_impact_unknown_evidence(item.get("evidence"), doc, root))
        review = item.get("review")
        if not isinstance(review, dict) or str(review.get("status") or "").upper() != "APPROVED":
            errors.append(f"{label} requires explicit Human review with APPROVED status")
        else:
            if str(review.get("reviewer") or "").lower() != "human":
                errors.append(f"{label} review must identify reviewer as human")
            if not isinstance(review.get("approval_reference"), str) or not review["approval_reference"].strip():
                errors.append(f"{label} review requires an approval_reference")
            if not isinstance(review.get("reviewed_at"), str) or not review["reviewed_at"].strip():
                errors.append(f"{label} review requires reviewed_at")
            else:
                try:
                    reviewed_at = dt.datetime.fromisoformat(review["reviewed_at"])
                    if reviewed_at.tzinfo is None:
                        raise ValueError("timezone is required")
                except ValueError:
                    errors.append(f"{label} review reviewed_at must be an ISO-8601 timestamp with timezone")
    return errors


def validate_impact_document(doc: dict[str, Any], root: Path | None = None) -> dict[str, Any]:
    status = str(doc.get("status", "DRAFT")).upper()
    errors: list[str] = []
    if status not in {"DRAFT", "IMPLEMENTATION_APPROVED", "READY", "BLOCKED"}:
        errors.append(f"unsupported status: {status}")
    if status in {"IMPLEMENTATION_APPROVED", "READY"}:
        scope = doc.get("scope_review") or {}
        if scope.get("status") != "APPROVED" or not scope.get("approval_reference") or not scope.get("approved_at"):
            errors.append("implementation requires approved scope with reference and timestamp")
        errors.extend(validate_impact_unknown_dispositions(doc, root))
        traversal = doc.get("traversal") or {}
        if (doc.get("change") or {}).get("risk_class") or traversal.get("mode") == "directional_reviewed_scope":
            recorded_paths = (doc.get("reconciliation") or {}).get("changed_files") if status == "READY" else None
            errors.extend(validate_traversal_evidence(doc, recorded_paths))
    if status == "READY":
        reconcile = doc.get("reconciliation") or {}
        required = ("base_revision", "head_revision", "diff_digest")
        missing = [key for key in required if not reconcile.get(key)]
        if reconcile.get("status") != "RECONCILED" or missing:
            errors.append("READY requires reconciled status and base/head/diff digest" + (f" (missing: {', '.join(missing)})" if missing else ""))
        if reconcile.get("impact_graph_reviewed") is not True or not reconcile.get("evidence"):
            errors.append("READY requires Impact Graph review and reconciliation evidence")
        change = doc.get("change") or {}
        declared_paths = change.get("target_paths") or []
        recorded_paths = reconcile.get("changed_files") or []
        if not declared_paths:
            errors.append("READY requires exact declared change.target_paths")
        if not recorded_paths:
            errors.append("READY requires reconciliation.changed_files from the reviewed diff")
        if root is None:
            errors.append("READY requires a project path for Git-bound reconciliation")
        else:
            errors.extend(validate_impact_git_reconciliation(root, reconcile, declared_paths, recorded_paths))
    return {"valid": not errors, "status": status, "errors": errors}


def validate_impact_git_reconciliation(root: Path, reconcile: dict[str, Any], declared_paths: list[Any], recorded_paths: list[Any]) -> list[str]:
    errors: list[str] = []
    root = project_root(root)
    base = str(reconcile.get("base_revision") or "")
    head = str(reconcile.get("head_revision") or "")
    for label, revision in (("base", base), ("head", head)):
        if not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", revision):
            errors.append(f"{label}_revision must be a full Git commit SHA")
            continue
        resolved = run_git(root, ["rev-parse", "--verify", f"{revision}^{{commit}}"])
        if not resolved or resolved.lower() != revision.lower():
            errors.append(f"{label}_revision does not resolve to the exact commit")

    current_head = run_git(root, ["rev-parse", "HEAD"])
    if current_head and head and current_head.lower() != head.lower():
        errors.append("head_revision does not match the checked-out HEAD")
    if base and head and not any("revision" in error and "full Git" in error or "does not resolve" in error for error in errors):
        ancestor = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", base, head], capture_output=True, check=False)
        if ancestor.returncode != 0:
            errors.append("base_revision must be an ancestor of head_revision")
    try:
        dirty = git_dirty_paths(root)
        if dirty:
            errors.append("working tree must be clean so READY describes the exact committed diff")
    except GitPathsError as exc:
        errors.append(f"working-tree state is unverifiable: {exc}")

    if base and head and not any("revision" in error and ("full Git" in error or "resolve" in error or "ancestor" in error) for error in errors):
        diff = subprocess.run(["git", "-C", str(root), "diff", "--binary", "--no-ext-diff", base, head, "--"], capture_output=True, check=False)
        names = subprocess.run(["git", "-C", str(root), "diff", "--name-only", "-z", base, head, "--"], capture_output=True, check=False)
        if diff.returncode or names.returncode:
            errors.append("actual Git diff could not be read")
        else:
            actual_digest = "sha256:" + hashlib.sha256(diff.stdout).hexdigest()
            supplied_digest = str(reconcile.get("diff_digest") or "")
            if supplied_digest.removeprefix("sha256:").lower() != actual_digest.removeprefix("sha256:"):
                errors.append("diff_digest does not match the actual binary Git diff")
            actual_paths = sorted(path.decode("utf-8", errors="surrogateescape") for path in names.stdout.split(b"\0") if path)
            declared = sorted({str(path) for path in declared_paths})
            recorded = sorted({str(path) for path in recorded_paths})
            if recorded != actual_paths:
                errors.append("reconciliation.changed_files does not match the actual changed-file set")
            if not set(actual_paths).issubset(set(declared)):
                errors.append("actual changed files exceed declared change.target_paths")
    return errors


def impact_validate(path: Path, root: Path | None = None) -> dict[str, Any]:
    doc = load_yaml(path, {})
    result = validate_impact_document(doc, root)
    result["path"] = str(path)
    return result


def validated_copytree(src: Path, dst: Path) -> None:
    if not (src / "PROJECT_INTELLIGENCE.yaml").is_file():
        raise RuntimeError(f"Source Intelligence is invalid: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    temp = dst.parent / f".{dst.name}.tmp-{os.getpid()}"
    backup = dst.parent / f".{dst.name}.backup-{os.getpid()}"
    shutil.rmtree(temp, ignore_errors=True)
    shutil.copytree(src, temp)
    if not (temp / "PROJECT_INTELLIGENCE.yaml").is_file():
        shutil.rmtree(temp, ignore_errors=True)
        raise RuntimeError("Copied Intelligence failed validation")
    try:
        if dst.exists():
            os.replace(dst, backup)
        os.replace(temp, dst)
        shutil.rmtree(backup, ignore_errors=True)
    except Exception:
        if backup.exists() and not dst.exists():
            os.replace(backup, dst)
        shutil.rmtree(temp, ignore_errors=True)
        raise


def migrate_attached(root: Path) -> dict[str, Any]:
    """Copy legacy project-local Intelligence to user state without deleting it."""
    src = local_store(root)
    dst = external_store(root)
    if not (src / "PROJECT_INTELLIGENCE.yaml").is_file():
        return {"status": "NO_LEGACY_INTELLIGENCE", "destination": str(dst)}
    if (dst / "PROJECT_INTELLIGENCE.yaml").is_file():
        return {"status": "EXTERNAL_ALREADY_PRESENT", "source_preserved": str(src), "destination": str(dst)}
    validated_copytree(src, dst)
    return {"status": "COPIED_TO_EXTERNAL", "source_preserved": str(src), "destination": str(dst)}


def sync_external(root: Path) -> dict[str, Any]:
    src = local_store(root)
    if not src.exists():
        return {"status": "NO_LOCAL_INTELLIGENCE"}
    dst = external_store(root)
    validated_copytree(src, dst)
    return {"status": "SYNCED", "source": str(src), "destination": str(dst)}


def redact_text(value: str) -> str:
    result = value
    for pattern in REDACTION_PATTERNS:
        result = pattern.sub(lambda m: m.group(1) + "[REDACTED]", result)
    return result


def render_review(root: Path) -> Path:
    store, mode, _pid = intelligence_store(root, create=True)
    intel = load_yaml(store / "PROJECT_INTELLIGENCE.yaml", {})
    registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []})
    graph = load_yaml(store / "IMPACT_GRAPH.yaml", {"nodes": {}, "edges": []})
    overrides = load_yaml(store / "PROJECT_OVERRIDES.yaml", {})
    discovery = load_yaml(store / "DISCOVERY.yaml", {})
    fr = freshness(root)
    topics_dir = store / "topics"

    def esc(v: Any) -> str:
        return html.escape(redact_text("" if v is None else str(v)))

    topic_html: list[str] = []
    if topics_dir.exists():
        for p in sorted(topics_dir.glob("*.md")):
            content = redact_text(p.read_text(encoding="utf-8", errors="replace"))
            topic_html.append(f"<section><h3>{esc(p.name)}</h3><pre>{html.escape(content)}</pre></section>")

    source_rows = "".join(
        f"<tr><td>{esc(s.get('path'))}</td><td>{esc(s.get('authority'))}</td>"
        f"<td>{esc(', '.join(s.get('auto_loaded_by') or []))}</td>"
        f"<td>{esc(s.get('content_duplicated'))}</td></tr>"
        for s in registry.get("sources") or []
    )
    inv = discovery.get("inventory") or {}
    state = intel.get("state") or {}

    doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Project Intelligence Review</title>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;max-width:1180px;margin:40px auto;padding:0 24px;color:#202124;line-height:1.55;background:#fafafa}}
h1,h2,h3{{line-height:1.2}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}
.card,section{{border:1px solid #ddd;border-radius:12px;padding:16px;margin:12px 0;background:#fff}}
table{{border-collapse:collapse;width:100%;background:#fff}} th,td{{border-bottom:1px solid #ddd;text-align:left;padding:8px;vertical-align:top}}
code,pre{{font-family:ui-monospace,monospace;background:#f6f7f8}} pre{{white-space:pre-wrap;padding:12px;border-radius:8px;overflow-wrap:anywhere}}
.note{{background:#fff8dd;border-left:4px solid #d6a700;padding:12px}}
</style></head><body>
<h1>Project Intelligence Review</h1>
<p>Generated deterministically by AIPS. Review view only — ask the Agent to update canonical Intelligence or PROJECT_OVERRIDES.yaml.</p>
<div class="grid">
<div class="card"><b>Project</b><br>{esc((intel.get('project') or {}).get('root'))}</div>
<div class="card"><b>Mode</b><br>{esc(mode)}</div>
<div class="card"><b>Readiness</b><br>{esc(state.get('readiness'))}</div>
<div class="card"><b>Review</b><br>{esc(state.get('review'))}</div>
<div class="card"><b>Freshness</b><br>{esc(fr.get('status'))}</div>
<div class="card"><b>AIPS</b><br>{esc((intel.get('generated_by') or {}).get('aips_version'))}</div>
</div>
<h2>Freshness</h2><section><pre>{esc(yaml.safe_dump(fr, sort_keys=False, allow_unicode=True))}</pre></section>
<h2>Architecture</h2><section><p>{esc((intel.get('architecture') or {}).get('summary') or 'Pending semantic enrichment')}</p></section>
<h2>Discovery inventory</h2><section><pre>{esc(yaml.safe_dump(inv, sort_keys=False, allow_unicode=True))}</pre></section>
<h2>Authoritative / native sources</h2>
<table><thead><tr><th>Path</th><th>Authority</th><th>Auto loaded by</th><th>Duplicated?</th></tr></thead><tbody>{source_rows}</tbody></table>
<h2>Impact graph</h2><section><p>Nodes: {len(graph.get('nodes') or {})} · Edges: {len(graph.get('edges') or [])}</p>
<pre>{esc(yaml.safe_dump(graph, sort_keys=False, allow_unicode=True))}</pre></section>
<h2>User overrides / exceptions</h2><section><pre>{esc(yaml.safe_dump(overrides, sort_keys=False, allow_unicode=True))}</pre></section>
<h2>Intelligence topics</h2>{''.join(topic_html) or '<section>Pending semantic enrichment.</section>'}
<h2>Unknowns / conflicts</h2>
<section><pre>{esc(yaml.safe_dump({'unknowns': intel.get('unknowns') or [], 'conflicts': intel.get('conflicts') or []}, sort_keys=False, allow_unicode=True))}</pre></section>
<div class="note">Secrets and sensitive payload values must never be copied into Project Intelligence or this generated review.</div>
</body></html>"""
    out = store / "reviews" / "PROJECT_INTELLIGENCE_REVIEW.html"
    atomic_text(out, doc)
    return out


def status(root: Path) -> dict[str, Any]:
    store, mode, pid = intelligence_store(root)
    intel = load_yaml(store / "PROJECT_INTELLIGENCE.yaml", {})
    return {
        "project_id": pid,
        "mode": mode,
        "store": str(store),
        "exists": bool(intel),
        "state": intel.get("state") if intel else None,
        "freshness": freshness(root),
        "review_html": str(store / "reviews" / "PROJECT_INTELLIGENCE_REVIEW.html"),
    }


# Garbage collection for orphaned external Project Intelligence stores.
# Only <config_home>/projects/<workspace>/intelligence directories are
# considered. A store is an orphan only when its recorded project root is an
# absolute path and nothing exists at that path. Dry-run is the default;
# removal requires apply=True (aips intelligence gc --yes).
GC_STORE_NAME = "intelligence"
GC_MANIFEST_NAME = "PROJECT_INTELLIGENCE.yaml"


def _gc_recorded_root(store: Path) -> tuple[str | None, str | None]:
    manifest = store / GC_MANIFEST_NAME
    if manifest.is_symlink() or not manifest.is_file():
        return None, "manifest_missing"
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return None, "manifest_unreadable"
    project = data.get("project") if isinstance(data, dict) else None
    root = project.get("root") if isinstance(project, dict) else None
    if not isinstance(root, str) or not root.strip():
        return None, "project_root_unrecorded"
    if not os.path.isabs(root):
        return None, "project_root_not_absolute"
    return root, None


def _gc_path_present(path: str) -> bool | None:
    """Return True when anything (even a broken symlink) exists, None if unverifiable."""
    try:
        os.lstat(path)
    except FileNotFoundError:
        return False
    except NotADirectoryError:
        return False
    except OSError:
        return None
    return True


def _gc_confined(base: Path, entry: Path, store: Path) -> bool:
    try:
        resolved_entry = entry.resolve(strict=True)
        resolved_store = store.resolve(strict=True)
    except OSError:
        return False
    return resolved_entry.parent == base and resolved_store.parent == resolved_entry


def gc_external_stores(projects_dir: Path, *, apply: bool = False) -> dict[str, Any]:
    """Classify external stores and remove orphans only when ``apply`` is True."""
    result: dict[str, Any] = {
        "mode": "APPLY" if apply else "DRY_RUN",
        "projects_dir": str(projects_dir),
        "orphaned": [],
        "kept": [],
        "skipped": [],
        "removed": [],
        "errors": [],
    }
    if projects_dir.is_symlink():
        result["status"] = "REFUSED"
        result["reason"] = "projects_dir_is_symlink"
        return result
    if not projects_dir.is_dir():
        result["status"] = "NO_STORES"
        return result
    base = projects_dir.resolve(strict=True)
    for entry in sorted(base.iterdir(), key=lambda item: item.name):
        store = entry / GC_STORE_NAME
        record = {"workspace_id": entry.name, "store": str(store)}
        if entry.is_symlink():
            result["skipped"].append({**record, "reason": "workspace_is_symlink"})
            continue
        if not entry.is_dir():
            continue
        if store.is_symlink():
            result["skipped"].append({**record, "reason": "store_is_symlink"})
            continue
        if not store.is_dir():
            continue
        if not _gc_confined(base, entry, store):
            result["skipped"].append({**record, "reason": "store_outside_projects_dir"})
            continue
        root, problem = _gc_recorded_root(store)
        if root is None:
            result["skipped"].append({**record, "reason": problem})
            continue
        record["project_root"] = root
        present = _gc_path_present(root)
        if present is None:
            result["skipped"].append({**record, "reason": "project_root_unverifiable"})
            continue
        if present:
            result["kept"].append({**record, "reason": "project_root_exists"})
            continue
        result["orphaned"].append({**record, "reason": "project_root_missing"})
        if not apply:
            continue
        # Re-check immediately before deletion; never delete a store whose
        # project path reappeared or whose confinement changed.
        if _gc_path_present(root) is not False or not _gc_confined(base, entry, store) or store.is_symlink():
            result["skipped"].append({**record, "reason": "changed_before_removal"})
            continue
        try:
            shutil.rmtree(store)
        except OSError as exc:
            result["errors"].append({**record, "reason": type(exc).__name__})
            continue
        result["removed"].append(record)
        try:
            entry.rmdir()
        except OSError:
            pass  # Other workspace data (runs, changes) is preserved.
    result["status"] = "APPLIED" if apply else "DRY_RUN"
    if not apply and result["orphaned"]:
        result["next"] = "Review the orphaned stores, then run: aips intelligence gc --yes"
    return result


def output(data: Any, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip())


def main() -> int:
    parser = argparse.ArgumentParser(description="AIPS Project Intelligence deterministic helper")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("bootstrap", "status", "render", "finalize", "refresh", "refresh-plan", "migrate-attached", "sync-external", "reconcile-overrides"):
        p = sub.add_parser(name)
        p.add_argument("--project", default=os.getcwd())
        p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    p = sub.add_parser("context")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--runtime", default="unknown")
    p.add_argument("--prompt", default="")
    p.add_argument("--component")
    p.add_argument("--target-path", help="File or directory whose scoped project instructions apply")
    p.add_argument("--intent", choices=("auto", "read", "write"), default="auto")
    p.add_argument("--full", action="store_true", help="Include complete Turn Context diagnostics")
    p.add_argument("--compact", action="store_true", help="Emit the bounded compact manifest in the selected output format")
    p.add_argument("--observe-run-id", help="Record this Context operation in an existing AIPS run")
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")
    p.add_argument("--explain", action="store_true")

    p = sub.add_parser("promotion-plan")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--topic", required=True)
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    p = sub.add_parser("promotion-apply")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--topic", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--approval-id", required=True)
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    p = sub.add_parser("impact-init")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--prompt", default="")
    p.add_argument("--change-id")
    p.add_argument("--reset", action="store_true", help="Back up and replace an existing Change Impact record")
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    p = sub.add_parser("impact-traverse")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--artifact")
    p.add_argument("--seed", action="append", required=True)
    p.add_argument("--seed-path", action="append", default=[])
    p.add_argument("--seed-line", action="append", type=int, default=[])
    p.add_argument("--graph-seed", action="append", default=[], help="Exact node ID from the canonical IMPACT_GRAPH.yaml")
    p.add_argument("--risk-class", required=True)
    p.add_argument("--direction", action="append", choices=["callers", "consumers"])
    p.add_argument("--max-depth", type=int)
    p.add_argument("--max-nodes", type=int, default=150)
    p.add_argument("--max-edges", type=int, default=300)
    p.add_argument("--changed-path", action="append", default=[])
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    p = sub.add_parser("impact-candidates")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--seed-path", action="append", required=True)
    p.add_argument("--max-files", type=int, default=8000)
    p.add_argument("--max-candidates", type=int, default=300)
    p.add_argument("--max-depth", type=int, choices=(1, 2, 3), default=1)
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    p = sub.add_parser("context-audit")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    p = sub.add_parser("impact-validate")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--path", required=True)
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    p = sub.add_parser("temporal")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--mode", choices=["current", "as-of", "between", "why"], default="current")
    p.add_argument("--revision")
    p.add_argument("--base")
    p.add_argument("--head")
    p.add_argument("--assertion")
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    p = sub.add_parser("index")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--force", action="store_true")
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    p = sub.add_parser("retrieve")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--prompt", required=True)
    p.add_argument("--token-budget", type=int, default=RETRIEVAL_DEFAULT_TOKEN_BUDGET)
    p.add_argument("--limit", type=int, default=RETRIEVAL_DEFAULT_RESULT_LIMIT)
    p.add_argument("--no-refresh", action="store_true")
    p.add_argument("--no-structural", action="store_true")
    p.add_argument("--observe-run-id", help="Record this Retrieval operation in an existing AIPS run")
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    p = sub.add_parser("gc", help="List (default) or remove external stores whose project path no longer exists")
    p.add_argument("--yes", action="store_true", help="Remove the listed orphaned stores; default is a dry run")
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    p = sub.add_parser("evaluate")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--suite", required=True)
    p.add_argument("--output")
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    args = parser.parse_args()
    if args.command == "gc":
        try:
            result = gc_external_stores(config_home() / "projects", apply=args.yes)
        except OSError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        output(result, args.format)
        return 1 if result.get("errors") or result.get("status") == "REFUSED" else 0
    root = project_root(Path(args.project))
    try:
        if args.command == "bootstrap":
            result = bootstrap(root)
        elif args.command == "status":
            result = status(root)
        elif args.command == "render":
            result = {"review": str(render_review(root))}
        elif args.command == "finalize":
            result = finalize(root)
        elif args.command == "refresh":
            result = refresh(root)
        elif args.command == "refresh-plan":
            result = refresh_plan(root)
        elif args.command == "context":
            with observed_stage(root, args.observe_run_id, "intelligence.context") as observation:
                result = context_manifest(root, args.runtime, args.prompt, args.explain, args.component,
                                          args.target_path or args.project, args.intent)
            result["observation"] = observation
            if args.compact or (args.format == "yaml" and not args.full):
                result = compact_context_manifest(result)
        elif args.command == "promotion-plan":
            result = promotion_plan(root, args.topic)
        elif args.command == "promotion-apply":
            result = promotion_apply(root, args.topic, args.target, args.approval_id)
        elif args.command == "impact-init":
            result = impact_init(root, args.prompt, args.change_id, reset=args.reset)
        elif args.command == "impact-traverse":
            if len(args.seed_path) > len(args.seed) or len(args.seed_line) > len(args.seed):
                raise ValueError("--seed-path and --seed-line entries must align with --seed entries")
            seeds = []
            for index, symbol in enumerate(args.seed):
                seed = {"symbol": symbol}
                if index < len(args.seed_path):
                    seed["path"] = args.seed_path[index]
                if index < len(args.seed_line):
                    seed["line"] = args.seed_line[index]
                seeds.append(seed)
            result = impact_traverse(
                root,
                Path(args.artifact) if args.artifact else None,
                seeds,
                args.risk_class,
                args.direction,
                args.max_depth,
                args.max_nodes,
                args.max_edges,
                args.changed_path,
                args.graph_seed,
            )
        elif args.command == "impact-candidates":
            result = impact_candidates(
                root,
                args.seed_path,
                max_files=args.max_files,
                max_candidates=args.max_candidates,
                max_depth=args.max_depth,
            )
        elif args.command == "impact-validate":
            result = impact_validate(Path(args.path), root)
        elif args.command == "context-audit":
            result = context_audit(root)
        elif args.command == "temporal":
            store, _, _ = intelligence_store(root, create=True)
            result = temporal_query(root, store, args.mode, args.revision, args.base, args.head, args.assertion)
        elif args.command == "index":
            store, _, _ = intelligence_store(root, create=True)
            if not (store / "PROJECT_INTELLIGENCE.yaml").exists():
                raise RuntimeError("Project Intelligence must be initialized before Retrieval Intelligence indexing")
            result = retrieval_index_repository(root, store, force=args.force)
        elif args.command == "retrieve":
            store, _, _ = intelligence_store(root)
            if not (store / "PROJECT_INTELLIGENCE.yaml").exists():
                raise RuntimeError("Project Intelligence must be initialized before Retrieval Intelligence query")
            with observed_stage(root, args.observe_run_id, "intelligence.retrieve") as observation:
                result = retrieval_query_repository(
                    root,
                    store,
                    args.prompt,
                    token_budget=max(256, args.token_budget),
                    limit=max(1, min(50, args.limit)),
                    refresh=not args.no_refresh,
                    structural=False if args.no_structural else None,
                )
            result["observation"] = observation
        elif args.command == "evaluate":
            store, _, _ = intelligence_store(root)
            if not (store / "PROJECT_INTELLIGENCE.yaml").exists():
                raise RuntimeError("Project Intelligence must be initialized before Retrieval Intelligence evaluation")
            suite_path = Path(args.suite).resolve()
            result = retrieval_evaluate_suite(root, store, retrieval_load_suite(suite_path))
            if args.output:
                retrieval_write_report(Path(args.output).resolve(), result)
        elif args.command == "migrate-attached":
            result = migrate_attached(root)
        elif args.command == "sync-external":
            result = sync_external(root)
        elif args.command == "reconcile-overrides":
            result = reconcile_overrides(root)
        else:
            raise RuntimeError("unsupported command")
    except (RuntimeError, OSError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    output(result, args.format)
    if args.command == "evaluate" and result.get("status") == "FAIL":
        return 1
    if args.command == "impact-validate" and not result.get("valid"):
        return 1
    if args.command in {"index", "retrieve", "impact-traverse"} and result.get("status") in {"INDEX_UNAVAILABLE", "INCOMPLETE"}:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

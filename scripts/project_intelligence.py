#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
from fnmatch import fnmatch
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Iterator

import yaml

from git_paths import GitPathsError, run_git_paths
from aips_identity import (
    config_home as canonical_config_home,
    project_root as canonical_project_root,
    repository_identity as canonical_repository_identity,
)
from retrieval_intelligence import (
    DEFAULT_RESULT_LIMIT as RETRIEVAL_DEFAULT_RESULT_LIMIT,
    DEFAULT_TOKEN_BUDGET as RETRIEVAL_DEFAULT_TOKEN_BUDGET,
    index_repository as retrieval_index_repository,
    index_status as retrieval_index_status,
    query_repository as retrieval_query_repository,
)
from retrieval_evaluation import (
    evaluate_suite as retrieval_evaluate_suite,
    load_suite as retrieval_load_suite,
    write_report as retrieval_write_report,
)

SCHEMA_VERSION = 1

SECRET_NAMES = {
    ".env", ".env.local", ".env.production", ".env.development",
    "id_rsa", "id_ed25519", "credentials.json", "service-account.json",
}
SOURCE_NAMES = {"AGENTS.md", "AGENTS.override.md", "CLAUDE.md", "GEMINI.md"}
MANIFEST_NAMES = {
    "go.mod", "go.work", "package.json", "pnpm-workspace.yaml", "yarn.lock",
    "Cargo.toml", "pyproject.toml", "requirements.txt", "pom.xml", "build.gradle",
    "build.gradle.kts", "composer.json", "Gemfile", "Dockerfile",
    "docker-compose.yml", "docker-compose.yaml", "Makefile",
}
DOC_EXT = {".md", ".yaml", ".yml", ".json", ".toml"}
CODE_EXT = {
    ".go", ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".kts",
    ".cs", ".php", ".rb", ".rs", ".swift", ".vue", ".svelte", ".sql",
}
REQUIRED_SEMANTIC_TOPICS = (
    "architecture", "data-flow", "modules", "conventions", "testing", "security",
)
OPTIONAL_SEMANTIC_TOPICS = ("operations",)
MUTATION_WORDS = {
    "modify", "change", "fix", "implement", "add", "remove", "refactor", "update",
    "create", "delete", "rename", "修改", "調整", "實作", "新增", "刪除", "重構", "修正", "更新",
}
VISUAL_WORDS = {"css", "ui", "ux", "button", "tag", "layout", "visual", "style", "樣式", "風格", "按鈕", "版面"}
DATA_WORDS = {"database", "schema", "sql", "migration", "table", "db", "資料庫", "欄位", "遷移"}
API_WORDS = {"api", "endpoint", "request", "response", "handler", "route", "接口", "介面", "請求", "回應"}
SECURITY_WORDS = {"auth", "authorization", "security", "permission", "token", "權限", "驗證", "資安"}
TEST_WORDS = {"test", "spec", "coverage", "測試"}

REDACTION_PATTERNS = (
    re.compile(r"(?i)(password\s*[:=]\s*)([^\s,;]+)"),
    re.compile(r"(?i)((?:api[_-]?key|token|secret)\s*[:=]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)([^\s]+)"),
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def run_git(project: Path, args: list[str]) -> str | None:
    try:
        r = subprocess.run(
            ["git", "-C", str(project), *args],
            capture_output=True, text=True, check=True,
        )
        return r.stdout.strip()
    except Exception:
        return None


def project_root(path: Path) -> Path:
    return canonical_project_root(path)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def config_home() -> Path:
    return canonical_config_home()


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
    if (root / ".ai").is_dir():
        store = local_store(root)
        mode = "ATTACHED"
    else:
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


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_name, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temp_name)


def atomic_yaml(path: Path, data: Any) -> None:
    atomic_text(path, yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


@contextlib.contextmanager
def writer_lock(store: Path) -> Iterator[None]:
    store.mkdir(parents=True, exist_ok=True)
    lock = store / ".writer.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise RuntimeError(f"Project Intelligence writer lock is active: {lock}")
    try:
        os.write(fd, f"pid={os.getpid()}\ncreated_at={utc_now()}\n".encode())
        os.close(fd)
        yield
    finally:
        with contextlib.suppress(FileNotFoundError):
            lock.unlink()


def rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return str(path)


def is_secret_filename(name: str) -> bool:
    low = name.lower()
    return low in SECRET_NAMES or low.startswith(".env.") or low.endswith(".pem") or low.endswith(".key")


def safe_walk(root: Path, max_files: int = 8000) -> list[Path]:
    ignored = {
        ".git", ".ai", ".venv", "venv", "node_modules", "vendor", "dist", "build",
        "coverage", ".next", ".cache", "target", "__pycache__",
    }
    result: list[Path] = []
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in ignored and not d.startswith(".ai.detached-"))
        for name in sorted(files):
            if is_secret_filename(name):
                continue
            p = Path(base) / name
            result.append(p)
            if len(result) >= max_files:
                return result
    return result


def discover_sources(root: Path, files: list[Path]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for p in files:
        rp = rel(root, p)
        name = p.name
        if name not in SOURCE_NAMES and not (
            (rp.startswith("docs/") or rp.startswith("doc/")) and p.suffix.lower() in DOC_EXT
        ):
            continue
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size > 2_000_000:
            continue
        authority = "project_instruction" if name in SOURCE_NAMES else "official_document"
        auto: list[str] = []
        if name.startswith("AGENTS"):
            auto.append("codex")
        if name == "CLAUDE.md":
            auto.append("claude-code")
        if name == "GEMINI.md":
            auto.append("gemini-cli")
        sources.append({
            "id": f"src-{sha(rp)[:10]}",
            "path": rp,
            "authority": authority,
            "scope": str(Path(rp).parent.as_posix()),
            "hash": file_hash(p),
            "auto_loaded_by": auto,
            "content_duplicated": False,
        })
    return sorted(sources, key=lambda x: x["path"])


def inventory(root: Path, files: list[Path]) -> dict[str, Any]:
    ext_counts: dict[str, int] = {}
    manifests: list[str] = []
    entry_candidates: list[str] = []
    api_candidates: list[str] = []
    data_candidates: list[str] = []
    event_candidates: list[str] = []
    test_candidates: list[str] = []
    top_dirs: dict[str, int] = {}
    for p in files:
        rp = rel(root, p)
        parts = Path(rp).parts
        if parts:
            top_dirs[parts[0]] = top_dirs.get(parts[0], 0) + 1
        ext = p.suffix.lower()
        if ext in CODE_EXT:
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
        if p.name in MANIFEST_NAMES:
            manifests.append(rp)
        low = rp.lower()
        if p.name.lower() in {"main.go", "main.py", "app.py", "server.py", "index.ts", "index.js", "program.cs"}:
            entry_candidates.append(rp)
        if any(k in low for k in ("openapi", "swagger", "/api/", "/routes/", "/handlers/", "/controller")):
            api_candidates.append(rp)
        if any(k in low for k in ("migration", "schema", "/repository/", "/repositories/", "/database/", "/db/")):
            data_candidates.append(rp)
        if any(k in low for k in ("event", "kafka", "queue", "consumer", "producer", "worker")):
            event_candidates.append(rp)
        if any(k in low for k in ("/test", "/tests/", "_test.", ".spec.", ".test.")):
            test_candidates.append(rp)
    return {
        "scanned_file_count": len(files),
        "top_level": dict(sorted(top_dirs.items(), key=lambda kv: (-kv[1], kv[0]))[:40]),
        "code_extensions": dict(sorted(ext_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "manifests": sorted(manifests)[:200],
        "entry_candidates": sorted(entry_candidates)[:200],
        "api_candidates": sorted(api_candidates)[:300],
        "data_candidates": sorted(data_candidates)[:300],
        "event_candidates": sorted(event_candidates)[:300],
        "test_candidates": sorted(test_candidates)[:300],
    }


def seed_impact_graph(inv: dict[str, Any]) -> dict[str, Any]:
    nodes: dict[str, Any] = {}
    for kind, key in (
        ("api_source", "api_candidates"),
        ("data_source", "data_candidates"),
        ("event_source", "event_candidates"),
    ):
        for path in inv.get(key, [])[:100]:
            nid = f"{kind}-{sha(path)[:12]}"
            nodes[nid] = {"type": kind, "source": path}
    return {
        "version": 1,
        "nodes": nodes,
        "edges": [],
        "coverage": {"api": "partial", "data": "partial", "events": "partial", "consumers": "unknown"},
        "unknowns": ["Semantic relationships require Agent enrichment from repository evidence."],
    }


def classify_prompt(prompt: str) -> tuple[str, bool, list[str]]:
    low = prompt.lower()
    mutation = any(w in low for w in MUTATION_WORDS)
    topics = ["architecture", "conventions", "modules"] if mutation else []
    if any(w in low for w in VISUAL_WORDS):
        return "visual", mutation, ["conventions", "modules"]
    if any(w in low for w in DATA_WORDS):
        return "data", mutation, ["architecture", "data-flow", "modules"]
    if any(w in low for w in SECURITY_WORDS):
        return "security", mutation, ["architecture", "security", "modules"]
    if any(w in low for w in TEST_WORDS):
        return "testing", mutation, ["testing", "modules", "conventions"]
    if any(w in low for w in API_WORDS):
        return "api", mutation, ["architecture", "data-flow", "modules", "conventions"]
    return ("mutation" if mutation else "general"), mutation, topics


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


def bootstrap(root: Path) -> dict[str, Any]:
    store, mode, pid = intelligence_store(root, create=True)
    with writer_lock(store):
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
    return {
        "project_id": pid,
        "mode": mode,
        "store": str(store),
        "readiness": "PARTIAL",
        "review": "UNREVIEWED",
        "review_html": str(review),
        "next": "Agent semantic enrichment + aips intelligence finalize",
    }


def git_dirty_paths(root: Path) -> list[str]:
    """Return complete staged, unstaged and untracked path sets."""
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
    return fnmatch(path, pattern) or fnmatch(path, pattern.replace("**/", "*"))


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



def _promotion_candidate(store: Path, intel: dict[str, Any], topic_name: str) -> tuple[dict[str, Any], Path]:
    topic = (intel.get("topics") or {}).get(topic_name)
    if not isinstance(topic, dict):
        raise RuntimeError(f"Unknown Project Intelligence topic: {topic_name}")
    path_value = topic.get("path")
    if not path_value:
        raise RuntimeError(f"Project Intelligence topic has no derived content path: {topic_name}")
    derived_path = store / str(path_value)
    if not derived_path.is_file():
        raise RuntimeError(f"Project Intelligence topic content is missing: {path_value}")
    promotion = topic.get("promotion") or {}
    confirmations = [str(value) for value in (promotion.get("confirmations") or []) if str(value).strip()]
    confirmations = list(dict.fromkeys(confirmations))
    eligible = (
        len(confirmations) >= 2
        and topic.get("type") in {"FACT", "INTERPRETATION", "OBSERVED_CONVENTION"}
        and bool(topic.get("evidence"))
    )
    return {
        "topic": topic_name,
        "status": "RECOMMENDED" if eligible else "NOT_READY",
        "approval_required": True,
        "mutation_performed": False,
        "confirmations": confirmations,
        "confirmation_count": len(confirmations),
        "reason": "repeated_confirmed_derived_invariant" if eligible else "insufficient_confirmation_or_evidence",
        "allowed_targets": ["AGENTS.md", "AGENTS.override.md", "docs/<official-project-rule>.md"],
    }, derived_path


def promotion_plan(root: Path, topic_name: str) -> dict[str, Any]:
    store, mode, pid = intelligence_store(root)
    intel_path = store / "PROJECT_INTELLIGENCE.yaml"
    if not intel_path.exists():
        raise RuntimeError("Project Intelligence is not initialized")
    intel = load_yaml(intel_path, {})
    candidate, _ = _promotion_candidate(store, intel, topic_name)
    return {"project_id": pid, "mode": mode, **candidate}


def _promotion_target(root: Path, target: str) -> Path:
    raw = Path(target)
    if raw.is_absolute():
        raise RuntimeError("Promotion target must be project-relative")
    resolved = (root / raw).resolve()
    try:
        relative = resolved.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise RuntimeError("Promotion target escapes project root") from exc
    allowed = raw.name in SOURCE_NAMES or (relative.startswith("docs/") and raw.suffix.lower() in DOC_EXT)
    if not allowed:
        raise RuntimeError("Promotion target must be AGENTS*/runtime instruction source or an official docs/* document")
    return resolved


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
        "system_summary": (intel.get("architecture") or {}).get("summary"),
        "target": None,
        "shared_relationships": [],
        "excluded_components": [],
    }
    if not component:
        return public, []
    target = components.get(component)
    if not isinstance(target, dict):
        raise RuntimeError(f"Unknown Project Intelligence component: {component}")

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
            raise RuntimeError(f"Unknown shared relationship for component {component}: {relationship_id}")
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


def context_manifest(root: Path, runtime: str, prompt: str, explain: bool = False, component: str | None = None) -> dict[str, Any]:
    store, mode, pid = intelligence_store(root)
    category, mutation, desired_topics = classify_prompt(prompt)
    fr = freshness(root)
    intel = load_yaml(store / "PROJECT_INTELLIGENCE.yaml", {}) if (store / "PROJECT_INTELLIGENCE.yaml").exists() else {}
    registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []}) if store.exists() else {"sources": []}
    state = intel.get("state") or {}
    authority_conflicts = active_authority_conflicts(store, intel, registry, runtime) if store.exists() else []

    retrieval: dict[str, Any] = {
        "status": "INDEX_MISSING",
        "results": [],
        "token_budget": RETRIEVAL_DEFAULT_TOKEN_BUDGET,
        "estimated_tokens": 0,
    }
    retrieval_state = {"status": "MISSING"}
    if store.exists() and (store / "PROJECT_INTELLIGENCE.yaml").exists():
        try:
            retrieval_state = retrieval_index_status(root, store)
            if prompt and retrieval_state.get("status") in {"CURRENT", "STALE"}:
                retrieval = retrieval_query_repository(
                    root,
                    store,
                    prompt,
                    token_budget=RETRIEVAL_DEFAULT_TOKEN_BUDGET,
                    limit=RETRIEVAL_DEFAULT_RESULT_LIMIT,
                    refresh=True,
                )
            else:
                retrieval = {
                    "status": "INDEX_MISSING" if retrieval_state.get("status") == "MISSING" else str(retrieval_state.get("status")),
                    "index": retrieval_state,
                    "results": [],
                    "token_budget": RETRIEVAL_DEFAULT_TOKEN_BUDGET,
                    "estimated_tokens": 0,
                }
        except Exception as exc:
            retrieval = {
                "status": "UNAVAILABLE",
                "reason": str(exc),
                "index": retrieval_state,
                "results": [],
                "token_budget": RETRIEVAL_DEFAULT_TOKEN_BUDGET,
                "estimated_tokens": 0,
            }

    available = intel.get("topics") or {}
    selected: list[str] = []
    for name in desired_topics:
        topic = available.get(name)
        if isinstance(topic, dict) and topic.get("path"):
            selected.append(str(store / topic["path"]))

    component_resolution, component_paths = resolve_component_context(store, intel, component)
    selected = list(dict.fromkeys([*selected, *component_paths]))

    project_native: list[str] = []
    runtime_visible: list[str] = []
    for src in registry.get("sources") or []:
        p = str(src.get("path", ""))
        if not p:
            continue
        if runtime in (src.get("auto_loaded_by") or []):
            runtime_visible.append(str(root / p))
        else:
            project_native.append(str(root / p))

    initialize = fr["status"] == "MISSING"
    readiness = state.get("readiness", "PARTIAL") if not initialize else "PARTIAL"
    refresh = fr.get("affected_topics", []) if fr["status"] == "STALE" else []

    fail_closed_reasons: list[str] = []
    if mutation:
        if initialize:
            fail_closed_reasons.append("intelligence_missing")
        if fr["status"] == "STALE":
            fail_closed_reasons.append("intelligence_stale")
        if fr["status"] == "UNKNOWN":
            fail_closed_reasons.append("intelligence_freshness_unknown")
        if readiness != "READY":
            fail_closed_reasons.append(f"intelligence_readiness_{readiness.lower()}")
        if authority_conflicts:
            fail_closed_reasons.append("unresolved_authority_conflict")

    return {
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
        },
        "context": {
            "always": [
                str(system_root() / "harness" / "BOOTSTRAP.md"),
                str(system_root() / "SYSTEM.md"),
            ],
            "runtime_native": runtime_visible[:30],
            "project_native": project_native[:30],
            "intelligence_topics": selected,
            "optional_evidence": [str(store / "DISCOVERY.yaml")] if (store / "DISCOVERY.yaml").exists() else [],
            "retrieval": retrieval,
            "authority_conflicts": authority_conflicts,
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
            "retrieval_index_required": bool(
                (store / "PROJECT_INTELLIGENCE.yaml").exists()
                and retrieval_state.get("status") == "MISSING"
            ),
            "targeted_refresh": refresh,
            "change_impact_required": mutation,
        },
        "resolution": {
            "explained": explain,
            "decisions": ([
                {"subject": "task.category", "selected": category, "reasons": ["prompt_classification"]},
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
    if not topic.get("evidence"):
        return False
    return True


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
    review = render_review(root)
    return {
        "project_id": pid,
        "mode": mode,
        "readiness": readiness,
        "missing": missing,
        "review_html": str(review),
    }


def impact_path(root: Path, change_id: str) -> Path:
    store, mode, pid = intelligence_store(root, create=True)
    if mode == "ATTACHED":
        return root / ".ai" / "runs" / change_id / "CHANGE_IMPACT.yaml"
    return store.parent / "changes" / f"{change_id}.yaml"


def impact_init(root: Path, prompt: str, change_id: str | None) -> dict[str, Any]:
    store, mode, pid = intelligence_store(root, create=True)
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
        "status": "DRAFT",
    }
    atomic_yaml(path, doc)
    return {"change_id": change_id, "path": str(path), "mode": mode, "status": "DRAFT"}


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
    if not (root / ".ai").is_dir():
        raise RuntimeError("Project must be attached before migrating Intelligence")
    src = external_store(root)
    dst = local_store(root)
    if not src.exists():
        return {"status": "NO_EXTERNAL_CACHE", "destination": str(dst)}
    if dst.exists() and (dst / "PROJECT_INTELLIGENCE.yaml").exists():
        return {"status": "LOCAL_ALREADY_PRESENT", "source_preserved": str(src), "destination": str(dst)}
    validated_copytree(src, dst)
    shutil.rmtree(src)
    return {"status": "MIGRATED", "source_removed": str(src), "destination": str(dst)}


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
    store, mode, pid = intelligence_store(root, create=True)
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


def output(data: Any, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip())


def main() -> int:
    parser = argparse.ArgumentParser(description="AIPS Project Intelligence deterministic helper")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("bootstrap", "status", "render", "finalize", "migrate-attached", "sync-external", "reconcile-overrides"):
        p = sub.add_parser(name)
        p.add_argument("--project", default=os.getcwd())
        p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    p = sub.add_parser("context")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--runtime", default="unknown")
    p.add_argument("--prompt", default="")
    p.add_argument("--component")
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
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    p = sub.add_parser("evaluate")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--suite", required=True)
    p.add_argument("--output")
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    args = parser.parse_args()
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
        elif args.command == "context":
            result = context_manifest(root, args.runtime, args.prompt, args.explain, args.component)
        elif args.command == "promotion-plan":
            result = promotion_plan(root, args.topic)
        elif args.command == "promotion-apply":
            result = promotion_apply(root, args.topic, args.target, args.approval_id)
        elif args.command == "impact-init":
            result = impact_init(root, args.prompt, args.change_id)
        elif args.command == "index":
            store, _, _ = intelligence_store(root, create=True)
            if not (store / "PROJECT_INTELLIGENCE.yaml").exists():
                raise RuntimeError("Project Intelligence must be initialized before Retrieval Intelligence indexing")
            result = retrieval_index_repository(root, store, force=args.force)
        elif args.command == "retrieve":
            store, _, _ = intelligence_store(root)
            if not (store / "PROJECT_INTELLIGENCE.yaml").exists():
                raise RuntimeError("Project Intelligence must be initialized before Retrieval Intelligence query")
            result = retrieval_query_repository(
                root,
                store,
                args.prompt,
                token_budget=max(256, args.token_budget),
                limit=max(1, min(50, args.limit)),
                refresh=not args.no_refresh,
                structural=False if args.no_structural else None,
            )
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
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    output(result, args.format)
    if args.command == "evaluate" and result.get("status") == "FAIL":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

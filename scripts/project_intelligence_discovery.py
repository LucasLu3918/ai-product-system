"""Bounded source discovery and initial inventory for Project Intelligence."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

from project_intelligence_context import SOURCE_NAMES

SECRET_NAMES = {
    ".env", ".env.local", ".env.production", ".env.development",
    "id_rsa", "id_ed25519", "credentials.json", "service-account.json",
}

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

def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()

def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (OSError, RuntimeError, ValueError):
        return str(path)

def is_secret_filename(name: str) -> bool:
    low = name.lower()
    return low in SECRET_NAMES or low.startswith(".env.") or low.endswith((".pem", ".key"))

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
            rp.startswith(("docs/", "doc/")) and p.suffix.lower() in DOC_EXT
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
    ci_candidates: list[str] = []
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
        if rp.startswith(".github/workflows/") and p.suffix in {".yml", ".yaml"}:
            ci_candidates.append(rp)
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
        "ci_candidates": sorted(ci_candidates)[:100],
    }

def seed_impact_graph(inv: dict[str, Any]) -> dict[str, Any]:
    nodes: dict[str, Any] = {}
    for kind, key in (
        ("api_source", "api_candidates"),
        ("data_source", "data_candidates"),
        ("event_source", "event_candidates"),
        ("ci_workflow", "ci_candidates"),
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

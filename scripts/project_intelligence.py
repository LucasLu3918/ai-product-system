#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Iterator

import yaml

SCHEMA_VERSION = 1
SECRET_NAMES = {
    ".env", ".env.local", ".env.production", ".env.development",
    "id_rsa", "id_ed25519", "credentials.json", "service-account.json",
}
SOURCE_NAMES = {"AGENTS.md", "AGENTS.override.md", "CLAUDE.md", "GEMINI.md"}
MANIFEST_NAMES = {
    "go.mod", "go.work", "package.json", "pnpm-workspace.yaml", "yarn.lock",
    "Cargo.toml", "pyproject.toml", "requirements.txt", "pom.xml", "build.gradle",
    "build.gradle.kts", "composer.json", "Gemfile", "Dockerfile", "docker-compose.yml",
    "docker-compose.yaml", "Makefile",
}
DOC_EXT = {".md", ".yaml", ".yml", ".json", ".toml"}
CODE_EXT = {
    ".go", ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".kts",
    ".cs", ".php", ".rb", ".rs", ".swift", ".vue", ".svelte", ".sql",
}
MUTATION_WORDS = {
    "modify", "change", "fix", "implement", "add", "remove", "refactor", "update",
    "create", "delete", "rename", "修改", "調整", "實作", "新增", "刪除", "重構", "修正", "更新",
}
VISUAL_WORDS = {"css", "ui", "ux", "button", "tag", "layout", "visual", "style", "樣式", "風格", "按鈕", "版面"}
DATA_WORDS = {"database", "schema", "sql", "migration", "table", "db", "資料庫", "欄位", "遷移"}
API_WORDS = {"api", "endpoint", "request", "response", "handler", "route", "接口", "介面", "請求", "回應"}
SECURITY_WORDS = {"auth", "authorization", "security", "permission", "token", "權限", "驗證", "資安"}
TEST_WORDS = {"test", "spec", "coverage", "測試"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def run_git(project: Path, args: list[str]) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(project), *args], capture_output=True, text=True, check=True)
        return r.stdout.strip()
    except Exception:
        return None


def project_root(path: Path) -> Path:
    path = path.expanduser().resolve()
    root = run_git(path, ["rev-parse", "--show-toplevel"])
    return Path(root).resolve() if root else path


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def repository_identity(root: Path) -> tuple[str, str, str]:
    remote = run_git(root, ["config", "--get", "remote.origin.url"]) or ""
    common = run_git(root, ["rev-parse", "--git-common-dir"]) or ""
    git_dir = run_git(root, ["rev-parse", "--git-dir"]) or ""
    repo_raw = remote or f"{root}|{common}"
    worktree_raw = f"{root}|{git_dir}"
    return sha(repo_raw)[:20], repo_raw, sha(worktree_raw)[:20]


def config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "aips"


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_version() -> str:
    p = system_root() / "VERSION"
    return p.read_text(encoding="utf-8").strip() if p.exists() else "unknown"


def system_commit() -> str:
    return run_git(system_root(), ["rev-parse", "HEAD"]) or "unknown"


def intelligence_store(root: Path, create: bool = False) -> tuple[Path, str, str]:
    pid, _, _ = repository_identity(root)
    if (root / ".ai").is_dir():
        store = root / ".ai" / "intelligence"
        mode = "ATTACHED"
    else:
        store = config_home() / "projects" / pid / "intelligence"
        mode = "EPHEMERAL"
    if create:
        (store / "topics").mkdir(parents=True, exist_ok=True)
        (store / "reviews").mkdir(parents=True, exist_ok=True)
    return store, mode, pid


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
        os.write(fd, f"pid={os.getpid()}\ncreated_at={now()}\n".encode())
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


def safe_walk(root: Path, max_files: int = 8000) -> list[Path]:
    ignored = {
        ".git", ".ai", ".venv", "venv", "node_modules", "vendor", "dist", "build",
        "coverage", ".next", ".cache", "target", "__pycache__",
    }
    result: list[Path] = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ignored and not d.startswith(".ai.detached-")]
        for name in files:
            if name in SECRET_NAMES or name.startswith(".env."):
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
        if p.stat().st_size > 2_000_000:
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


def bootstrap(root: Path) -> dict[str, Any]:
    store, mode, pid = intelligence_store(root, create=True)
    with writer_lock(store):
        files = safe_walk(root)
        inv = inventory(root, files)
        sources = discover_sources(root, files)
        repo_id, repo_raw, worktree_id = repository_identity(root)
        head = run_git(root, ["rev-parse", "HEAD"])
        branch = run_git(root, ["branch", "--show-current"])
        dirty = (run_git(root, ["status", "--porcelain"]) or "").splitlines()
        dirty_paths = [line[3:] if len(line) > 3 else line for line in dirty][:500]

        old_knowledge = root / ".ai" / "knowledge" / "KNOWLEDGE_INDEX.yaml"
        intel = {
            "schema": {"version": SCHEMA_VERSION},
            "generated_by": {"aips_version": system_version(), "aips_commit": system_commit()},
            "project": {
                "id": pid,
                "root": str(root),
                "repository_identity": repo_id,
                "worktree_identity": worktree_id,
                "branch": branch,
            },
            "state": {"readiness": "PARTIAL", "review": "UNREVIEWED", "freshness": "CURRENT"},
            "verified": {"git_head": head, "dirty_paths": dirty_paths, "verified_at": now()},
            "architecture": {
                "summary": None,
                "confidence": None,
                "source": None,
            },
            "topics": {},
            "canonical_artifacts": {},
            "migration": {
                "from_project_knowledge": old_knowledge.exists(),
                "sources": [rel(root, old_knowledge)] if old_knowledge.exists() else [],
            },
            "unknowns": [
                "Architecture/data-flow semantic conclusions require Agent review of discovery evidence.",
                "Impact graph relationships require semantic enrichment.",
            ],
            "conflicts": [],
        }
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
                "version": 1, "approved_inferences": [], "additional_rules": [],
                "exceptions": [], "excluded_inferences": [], "conflicts": [],
            })
        atomic_yaml(store / "PROJECT_INTELLIGENCE.yaml", intel)
        atomic_yaml(store / "SOURCE_REGISTRY.yaml", registry)
        atomic_yaml(store / "IMPACT_GRAPH.yaml", seed_impact_graph(inv))
        atomic_yaml(store / "DISCOVERY.yaml", {
            "version": 1,
            "generated_at": now(),
            "read_only": True,
            "secret_values_persisted": False,
            "repository_identity_hash": repo_id,
            "repository_identity_source_hash": sha(repo_raw),
            "inventory": inv,
        })
    render_review(root)
    return {"project_id": pid, "mode": mode, "store": str(store), "readiness": "PARTIAL", "review": "UNREVIEWED"}


def freshness(root: Path) -> dict[str, Any]:
    store, mode, pid = intelligence_store(root)
    ip = store / "PROJECT_INTELLIGENCE.yaml"
    if not ip.exists():
        return {"status": "MISSING", "mode": mode, "project_id": pid, "reasons": ["Project Intelligence not initialized"]}
    intel = load_yaml(ip, {})
    reg = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []})
    reasons: list[str] = []
    if (intel.get("schema") or {}).get("version") != SCHEMA_VERSION:
        reasons.append("intelligence_schema_changed")
    head = run_git(root, ["rev-parse", "HEAD"])
    old_head = (intel.get("verified") or {}).get("git_head")
    if old_head and head and old_head != head:
        reasons.append("git_head_changed")
    for source in reg.get("sources") or []:
        path = root / str(source.get("path", ""))
        if not path.exists():
            reasons.append(f"source_removed:{source.get('path')}")
            continue
        old_hash = source.get("hash")
        if old_hash and file_hash(path) != old_hash:
            reasons.append(f"source_changed:{source.get('path')}")
    dirty = (run_git(root, ["status", "--porcelain"]) or "").splitlines()
    dirty_paths = [line[3:] if len(line) > 3 else line for line in dirty]
    topics = intel.get("topics") or {}
    watched: set[str] = set()
    for topic in topics.values():
        for item in (topic or {}).get("watch", []) or []:
            watched.add(str(item))
    for p in dirty_paths:
        if any(simple_glob_match(p, pattern) for pattern in watched):
            reasons.append(f"dirty_watched_path:{p}")
    return {
        "status": "STALE" if reasons else "CURRENT",
        "mode": mode,
        "project_id": pid,
        "reasons": sorted(set(reasons)),
        "dirty_paths": dirty_paths[:500],
    }


def simple_glob_match(path: str, pattern: str) -> bool:
    from fnmatch import fnmatch
    return fnmatch(path, pattern) or fnmatch(path, pattern.replace("**/", "*"))


def context_manifest(root: Path, runtime: str, prompt: str) -> dict[str, Any]:
    store, mode, pid = intelligence_store(root)
    category, mutation, desired_topics = classify_prompt(prompt)
    fr = freshness(root)
    intel = load_yaml(store / "PROJECT_INTELLIGENCE.yaml", {}) if (store / "PROJECT_INTELLIGENCE.yaml").exists() else {}
    registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []}) if store.exists() else {"sources": []}
    available = intel.get("topics") or {}
    selected = []
    for name in desired_topics:
        topic = available.get(name)
        if topic and topic.get("path"):
            selected.append(str(store / topic["path"]))
    project_native = []
    for src in registry.get("sources") or []:
        if runtime not in (src.get("auto_loaded_by") or []):
            project_native.append(str(root / src["path"]))
    initialize = fr["status"] == "MISSING"
    fail_mode = "closed" if mutation and (initialize or fr["status"] == "STALE") else "soft"
    return {
        "version": 1,
        "runtime": {"id": runtime, "capability": runtime_capability(runtime)},
        "project": {"id": pid, "root": str(root), "mode": mode, "intelligence_store": str(store)},
        "task": {"prompt_hash": sha(prompt), "category": category, "mutation_likely": mutation},
        "context": {
            "always": [str(system_root() / "harness" / "BOOTSTRAP.md"), str(system_root() / "SYSTEM.md")],
            "runtime_native": [],
            "project_native": project_native[:30],
            "intelligence_topics": selected,
            "optional_evidence": [str(store / "DISCOVERY.yaml")] if store.exists() else [],
        },
        "freshness": {"status": fr["status"], "reasons": fr.get("reasons", [])},
        "requirements": {
            "initialize_intelligence": initialize,
            "targeted_refresh": fr.get("reasons", []) if fr["status"] == "STALE" else [],
            "change_impact_required": mutation,
        },
        "fail_policy": {"mode": fail_mode},
    }


def runtime_capability(runtime: str) -> str:
    return {
        "gemini-cli": "TURN_NATIVE",
        "claude-code": "TURN_NATIVE",
        "codex": "CONTEXT_ALWAYS",
    }.get(runtime, "MANUAL")


def render_review(root: Path) -> Path:
    store, mode, pid = intelligence_store(root, create=True)
    intel = load_yaml(store / "PROJECT_INTELLIGENCE.yaml", {})
    registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []})
    graph = load_yaml(store / "IMPACT_GRAPH.yaml", {"nodes": {}, "edges": []})
    overrides = load_yaml(store / "PROJECT_OVERRIDES.yaml", {})
    discovery = load_yaml(store / "DISCOVERY.yaml", {})
    topics_dir = store / "topics"

    def esc(v: Any) -> str:
        return html.escape("" if v is None else str(v))

    topic_html = []
    if topics_dir.exists():
        for p in sorted(topics_dir.glob("*.md")):
            content = p.read_text(encoding="utf-8", errors="replace")
            topic_html.append(f"<section><h3>{esc(p.name)}</h3><pre>{esc(content)}</pre></section>")

    source_rows = "".join(
        f"<tr><td>{esc(s.get('path'))}</td><td>{esc(s.get('authority'))}</td><td>{esc(', '.join(s.get('auto_loaded_by') or []))}</td><td>{esc(s.get('content_duplicated'))}</td></tr>"
        for s in registry.get("sources") or []
    )
    inv = discovery.get("inventory") or {}
    doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Project Intelligence Review</title>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;max-width:1180px;margin:40px auto;padding:0 24px;color:#202124;line-height:1.55}}
h1,h2,h3{{line-height:1.2}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}
.card,section{{border:1px solid #ddd;border-radius:12px;padding:16px;margin:12px 0;background:#fff}}
table{{border-collapse:collapse;width:100%}} th,td{{border-bottom:1px solid #ddd;text-align:left;padding:8px;vertical-align:top}}
code,pre{{font-family:ui-monospace,monospace;background:#f6f7f8}} pre{{white-space:pre-wrap;padding:12px;border-radius:8px;overflow-wrap:anywhere}}
.badge{{display:inline-block;padding:3px 8px;border:1px solid #bbb;border-radius:999px;margin-right:6px}}
.note{{background:#fff8dd;border-left:4px solid #d6a700;padding:12px}}
</style></head><body>
<h1>Project Intelligence Review</h1>
<p>Generated deterministically by AIPS. Review view only — edit canonical YAML/Markdown or ask the Agent to update PROJECT_OVERRIDES.yaml.</p>
<div class="grid">
<div class="card"><b>Project</b><br>{esc((intel.get('project') or {}).get('root'))}</div>
<div class="card"><b>Mode</b><br>{esc(mode)}</div>
<div class="card"><b>Readiness</b><br>{esc((intel.get('state') or {}).get('readiness'))}</div>
<div class="card"><b>Review</b><br>{esc((intel.get('state') or {}).get('review'))}</div>
<div class="card"><b>Freshness</b><br>{esc((intel.get('state') or {}).get('freshness'))}</div>
<div class="card"><b>AIPS</b><br>{esc((intel.get('generated_by') or {}).get('aips_version'))}</div>
</div>
<h2>Architecture</h2>
<section><p>{esc((intel.get('architecture') or {}).get('summary') or 'Pending semantic enrichment')}</p></section>
<h2>Discovery inventory</h2>
<section><pre>{esc(yaml.safe_dump(inv, sort_keys=False, allow_unicode=True))}</pre></section>
<h2>Authoritative / native sources</h2>
<table><thead><tr><th>Path</th><th>Authority</th><th>Auto loaded by</th><th>Duplicated?</th></tr></thead><tbody>{source_rows}</tbody></table>
<h2>Impact graph</h2>
<section><p>Nodes: {len(graph.get('nodes') or {})} · Edges: {len(graph.get('edges') or [])}</p>
<pre>{esc(yaml.safe_dump(graph, sort_keys=False, allow_unicode=True))}</pre></section>
<h2>User overrides / exceptions</h2>
<section><pre>{esc(yaml.safe_dump(overrides, sort_keys=False, allow_unicode=True))}</pre></section>
<h2>Intelligence topics</h2>
{''.join(topic_html) or '<section>Pending semantic enrichment.</section>'}
<h2>Unknowns / conflicts</h2>
<section><pre>{esc(yaml.safe_dump({'unknowns': intel.get('unknowns') or [], 'conflicts': intel.get('conflicts') or []}, sort_keys=False, allow_unicode=True))}</pre></section>
<div class="note">Secrets and sensitive payload values must never be copied into Project Intelligence or this review.</div>
</body></html>"""
    out = store / "reviews" / "PROJECT_INTELLIGENCE_REVIEW.html"
    atomic_text(out, doc)
    return out


def output(data: Any, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip())


def main() -> int:
    parser = argparse.ArgumentParser(description="AIPS Project Intelligence deterministic helper")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("bootstrap", "status", "render"):
        p = sub.add_parser(name)
        p.add_argument("--project", default=os.getcwd())
        p.add_argument("--format", choices=["yaml", "json"], default="yaml")
    p = sub.add_parser("context")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--runtime", default="unknown")
    p.add_argument("--prompt", default="")
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    args = parser.parse_args()
    root = project_root(Path(args.project))
    try:
        if args.command == "bootstrap":
            result = bootstrap(root)
        elif args.command == "status":
            store, mode, pid = intelligence_store(root)
            result = {"project_id": pid, "mode": mode, "store": str(store), "freshness": freshness(root)}
        elif args.command == "render":
            result = {"review": str(render_review(root))}
        elif args.command == "context":
            result = context_manifest(root, args.runtime, args.prompt)
        else:
            raise RuntimeError("unsupported command")
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    output(result, args.format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import subprocess
from typing import Any, Iterable

import yaml

from aips_identity import config_home as canonical_config_home
from aips_identity import repository_identity as canonical_repository_identity

SCHEMA_VERSION = 1
DEFAULT_TOKEN_BUDGET = 6000
DEFAULT_RESULT_LIMIT = 12
MAX_FILE_BYTES = 1_000_000
MAX_HISTORY = 200
MAX_HISTORY_DIFF_CHARS = 1600
STRUCTURAL_MAX_BRIDGES = 120
STRUCTURAL_MAX_IDENTIFIERS_PER_BRIDGE = 200
STRUCTURAL_MAX_TARGET_DEFINITIONS = 200
STRUCTURAL_MAX_TEST_CHUNKS = 500
CHUNK_LINES = 100
CHUNK_OVERLAP = 20

INDEXABLE_EXTENSIONS = {
    ".go", ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".kts",
    ".cs", ".php", ".rb", ".rs", ".swift", ".vue", ".svelte", ".sql",
    ".md", ".yaml", ".yml", ".json", ".toml",
}
INDEXABLE_NAMES = {
    "Dockerfile", "Makefile", "go.mod", "go.work", "package.json",
    "requirements.txt", "composer.json", "Gemfile",
}
EXCLUDED_PARTS = {
    ".git", ".ai", ".venv", "venv", "node_modules", "vendor", "dist", "build",
    "coverage", ".next", ".cache", "target", "__pycache__",
}
SECRET_NAMES = {
    ".env", ".env.local", ".env.production", ".env.development",
    "id_rsa", "id_ed25519", "credentials.json", "service-account.json",
}
SECRET_VALUE_PATTERNS = (
    re.compile(r"(?i)(password\s*[:=]\s*)([^\s,;]+)"),
    re.compile(r"(?i)((?:api[_-]?key|token|secret)\s*[:=]\s*)([^\s,;]+)"),
    re.compile(r"""(?i)(["']?(?:password|api[_-]?key|token|secret)["']?\s*[:=]\s*["']?)([^"'\s,;}]+)"""),
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)([^\s]+)"),
)
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{1,}|[\u4e00-\u9fff]{2,}")
IDENTIFIER_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
SYMBOL_PATTERNS = {
    ".py": [
        ("class", re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)")),
        ("function", re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)")),
    ],
    ".go": [
        ("type", re.compile(r"^\s*type\s+([A-Za-z_][A-Za-z0-9_]*)\s+")),
        ("function", re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\s*\(")),
    ],
    ".js": [("symbol", re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(?:function|class)\s+([A-Za-z_$][A-Za-z0-9_$]*)"))],
    ".jsx": [("symbol", re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(?:function|class)\s+([A-Za-z_$][A-Za-z0-9_$]*)"))],
    ".ts": [("symbol", re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(?:function|class|interface|type)\s+([A-Za-z_$][A-Za-z0-9_$]*)"))],
    ".tsx": [("symbol", re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(?:function|class|interface|type)\s+([A-Za-z_$][A-Za-z0-9_$]*)"))],
    ".java": [("symbol", re.compile(r"^\s*(?:public|protected|private)?\s*(?:final\s+)?(?:class|interface|enum)\s+([A-Za-z_][A-Za-z0-9_]*)"))],
    ".cs": [("symbol", re.compile(r"^\s*(?:public|internal|protected|private)?\s*(?:sealed\s+|static\s+)?(?:class|interface|record|enum)\s+([A-Za-z_][A-Za-z0-9_]*)"))],
    ".php": [("symbol", re.compile(r"^\s*(?:final\s+|abstract\s+)?(?:class|interface|trait|function)\s+([A-Za-z_][A-Za-z0-9_]*)"))],
    ".rs": [("symbol", re.compile(r"^\s*(?:pub\s+)?(?:fn|struct|enum|trait)\s+([A-Za-z_][A-Za-z0-9_]*)"))],
}
GENERIC_SYMBOL_PATTERN = re.compile(
    r"^\s*(?:export\s+)?(?:public\s+|private\s+|protected\s+|internal\s+)?"
    r"(?:async\s+|static\s+|final\s+)?(?:class|interface|struct|enum|trait|func|function|def)\s+"
    r"([A-Za-z_][A-Za-z0-9_$]*)"
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def run_git(root: Path, args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def repository_identity(root: Path) -> dict[str, str]:
    return canonical_repository_identity(root)


def cache_root() -> Path:
    base = Path(os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache"))
    return base / "aips" / "projects"


def index_path(root: Path) -> Path:
    ident = repository_identity(root)
    return cache_root() / ident["workspace_id"] / "retrieval" / "index.sqlite"


def metadata_path(store: Path) -> Path:
    return store / "RETRIEVAL_INDEX.yaml"


def redact_text(value: str) -> str:
    result = value
    for pattern in SECRET_VALUE_PATTERNS:
        result = pattern.sub(lambda m: m.group(1) + "[REDACTED]", result)
    return result


def is_secret_path(rel_path: str) -> bool:
    path = Path(rel_path)
    low_name = path.name.lower()
    if low_name in SECRET_NAMES or low_name.startswith(".env."):
        return True
    if low_name.endswith((".pem", ".key", ".p12", ".pfx")):
        return True
    lowered_parts = {part.lower() for part in path.parts}
    if {"secrets", ".secrets"} & lowered_parts:
        return True
    return False


def is_indexable(rel_path: str) -> bool:
    path = Path(rel_path)
    if any(part in EXCLUDED_PARTS or part.startswith(".ai.detached-") for part in path.parts):
        return False
    if is_secret_path(rel_path):
        return False
    return path.name in INDEXABLE_NAMES or path.suffix.lower() in INDEXABLE_EXTENSIONS


def tracked_and_untracked_files(root: Path) -> list[str]:
    raw = run_git(root, ["ls-files", "--cached", "--others", "--exclude-standard"]) or ""
    result: list[str] = []
    for value in raw.splitlines():
        value = value.strip()
        if not value or not is_indexable(value):
            continue
        path = root / value
        try:
            if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        result.append(value)
    return sorted(set(result))


def dirty_paths(root: Path) -> list[str]:
    result: set[str] = set()
    for args in (
        ["diff", "--name-only"],
        ["diff", "--cached", "--name-only"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        raw = run_git(root, args) or ""
        result.update(line.strip() for line in raw.splitlines() if line.strip())
    return sorted(result)


def dirty_fingerprint(root: Path) -> str:
    pieces: list[str] = []
    for rel_path in dirty_paths(root):
        path = root / rel_path
        if path.is_file() and is_indexable(rel_path) and not is_secret_path(rel_path):
            try:
                pieces.append(rel_path + ":" + hashlib.sha256(path.read_bytes()).hexdigest())
            except OSError:
                pieces.append(rel_path + ":unreadable")
        else:
            pieces.append(rel_path + ":nonindexed")
    return sha("\n".join(pieces))


def read_text_file(path: Path) -> str | None:
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in raw[:8192]:
        return None
    try:
        return redact_text(raw.decode("utf-8", errors="replace"))
    except Exception:
        return None


def extract_symbols(rel_path: str, text: str) -> list[tuple[str, str, int]]:
    ext = Path(rel_path).suffix.lower()
    patterns = SYMBOL_PATTERNS.get(ext, [])
    symbols: list[tuple[str, str, int]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        found = False
        for kind, pattern in patterns:
            match = pattern.match(line)
            if match:
                symbols.append((match.group(1), kind, line_no))
                found = True
                break
        if not found:
            match = GENERIC_SYMBOL_PATTERN.match(line)
            if match:
                symbols.append((match.group(1), "symbol", line_no))
    return symbols


def chunks_for(rel_path: str, text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    if not lines:
        return []
    chunks: list[dict[str, Any]] = []
    step = max(1, CHUNK_LINES - CHUNK_OVERLAP)
    for start in range(0, len(lines), step):
        end = min(len(lines), start + CHUNK_LINES)
        body = "\n".join(lines[start:end]).strip()
        if not body:
            continue
        chunks.append({
            "path": rel_path,
            "start_line": start + 1,
            "end_line": end,
            "text": body,
            "content_hash": sha(body),
            "kind": "test" if is_test_path(rel_path) else ("doc" if Path(rel_path).suffix.lower() in {".md", ".yaml", ".yml"} else "code"),
        })
        if end >= len(lines):
            break
    return chunks


def is_test_path(path: str) -> bool:
    low = path.lower()
    name = Path(low).name
    return (
        "/test/" in f"/{low}/"
        or "/tests/" in f"/{low}/"
        or "__tests__" in low
        or name.startswith("test_")
        or "_test." in name
        or ".test." in name
        or ".spec." in name
    )


def open_db(path: Path) -> tuple[sqlite3.Connection, bool]:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            content_hash TEXT NOT NULL,
            size INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            start_line INTEGER NOT NULL,
            end_line INTEGER NOT NULL,
            text TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            kind TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(path);
        CREATE TABLE IF NOT EXISTS symbols (
            name TEXT NOT NULL,
            kind TEXT NOT NULL,
            path TEXT NOT NULL,
            line INTEGER NOT NULL,
            chunk_id INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
        CREATE INDEX IF NOT EXISTS idx_symbols_path ON symbols(path);
        CREATE TABLE IF NOT EXISTS commits (
            sha TEXT PRIMARY KEY,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            paths TEXT NOT NULL,
            authored_at TEXT
        );
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
    fts_available = True
    try:
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(path, text)")
    except sqlite3.OperationalError:
        fts_available = False
    return conn, fts_available


def metadata_get(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row else None


def metadata_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO metadata(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def changed_paths_between(root: Path, old_head: str | None, new_head: str | None) -> set[str] | None:
    if not old_head or not new_head or old_head == new_head:
        return set()
    raw = run_git(root, ["diff", "--name-only", f"{old_head}..{new_head}"])
    if raw is None:
        return None
    return {line.strip() for line in raw.splitlines() if line.strip()}


def replace_file_index(conn: sqlite3.Connection, root: Path, rel_path: str, fts_available: bool) -> bool:
    conn.execute("DELETE FROM symbols WHERE path = ?", (rel_path,))
    chunk_ids = [row["id"] for row in conn.execute("SELECT id FROM chunks WHERE path = ?", (rel_path,)).fetchall()]
    if fts_available:
        for chunk_id in chunk_ids:
            conn.execute("DELETE FROM chunks_fts WHERE rowid = ?", (chunk_id,))
    conn.execute("DELETE FROM chunks WHERE path = ?", (rel_path,))
    conn.execute("DELETE FROM files WHERE path = ?", (rel_path,))

    path = root / rel_path
    if not path.is_file() or not is_indexable(rel_path) or is_secret_path(rel_path):
        return False
    try:
        size = path.stat().st_size
    except OSError:
        return False
    if size > MAX_FILE_BYTES:
        return False
    text = read_text_file(path)
    if text is None:
        return False
    file_hash = sha(text)
    conn.execute("INSERT INTO files(path, content_hash, size) VALUES (?, ?, ?)", (rel_path, file_hash, size))

    chunk_records = chunks_for(rel_path, text)
    for chunk in chunk_records:
        cur = conn.execute(
            "INSERT INTO chunks(path, start_line, end_line, text, content_hash, kind) VALUES (?, ?, ?, ?, ?, ?)",
            (
                chunk["path"], chunk["start_line"], chunk["end_line"], chunk["text"],
                chunk["content_hash"], chunk["kind"],
            ),
        )
        chunk_id = int(cur.lastrowid)
        if fts_available:
            conn.execute(
                "INSERT INTO chunks_fts(rowid, path, text) VALUES (?, ?, ?)",
                (chunk_id, rel_path, chunk["text"]),
            )

    chunk_rows = conn.execute(
        "SELECT id, start_line, end_line FROM chunks WHERE path = ? ORDER BY start_line",
        (rel_path,),
    ).fetchall()
    for name, kind, line in extract_symbols(rel_path, text):
        chunk_id = None
        for row in chunk_rows:
            if int(row["start_line"]) <= line <= int(row["end_line"]):
                chunk_id = int(row["id"])
                break
        conn.execute(
            "INSERT INTO symbols(name, kind, path, line, chunk_id) VALUES (?, ?, ?, ?, ?)",
            (name, kind, rel_path, line, chunk_id),
        )
    return True


def refresh_commits(conn: sqlite3.Connection, root: Path) -> None:
    raw = run_git(
        root,
        [
            "log", f"-n{MAX_HISTORY}",
            "--date=iso-strict",
            "--pretty=format:%x1e%H%x1f%aI%x1f%s%x1f%b",
            "--name-only",
        ],
    ) or ""
    conn.execute("DELETE FROM commits")
    for record in raw.split("\x1e"):
        record = record.strip()
        if not record:
            continue
        lines = record.splitlines()
        header = lines[0].split("\x1f", 3)
        if len(header) < 4:
            continue
        commit_sha, authored_at, subject, body = header
        paths = [line.strip() for line in lines[1:] if line.strip() and not is_secret_path(line.strip())]
        conn.execute(
            "INSERT OR REPLACE INTO commits(sha, subject, body, paths, authored_at) VALUES (?, ?, ?, ?, ?)",
            (commit_sha, redact_text(subject), redact_text(body), "\n".join(paths), authored_at),
        )


def count_table(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"])


def write_metadata_file(store: Path, doc: dict[str, Any]) -> None:
    path = metadata_path(store)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temp.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    os.replace(temp, path)


def index_repository(root: Path, store: Path, force: bool = False) -> dict[str, Any]:
    root = root.resolve()
    db_path = index_path(root)
    conn, fts_available = open_db(db_path)
    try:
        old_schema = metadata_get(conn, "schema_version")
        old_head = metadata_get(conn, "git_head")
        new_head = run_git(root, ["rev-parse", "HEAD"]) or "unknown"

        full = force or old_schema != str(SCHEMA_VERSION) or old_head is None
        changed: set[str] = set()
        if full:
            changed = set(tracked_and_untracked_files(root))
            old_files = {row["path"] for row in conn.execute("SELECT path FROM files").fetchall()}
            changed.update(old_files)
        else:
            committed = changed_paths_between(root, old_head, new_head)
            if committed is None:
                full = True
                changed = set(tracked_and_untracked_files(root))
                changed.update(row["path"] for row in conn.execute("SELECT path FROM files").fetchall())
            else:
                changed.update(committed)
                changed.update(dirty_paths(root))

        indexed = 0
        removed = 0
        for rel_path in sorted(changed):
            existed = conn.execute("SELECT 1 FROM files WHERE path = ?", (rel_path,)).fetchone() is not None
            kept = replace_file_index(conn, root, rel_path, fts_available)
            if kept:
                indexed += 1
            elif existed:
                removed += 1

        if full and not changed:
            for rel_path in tracked_and_untracked_files(root):
                if replace_file_index(conn, root, rel_path, fts_available):
                    indexed += 1

        if full or old_head != new_head:
            refresh_commits(conn, root)

        metadata_set(conn, "schema_version", str(SCHEMA_VERSION))
        metadata_set(conn, "git_head", new_head)
        metadata_set(conn, "dirty_fingerprint", dirty_fingerprint(root))
        metadata_set(conn, "generated_at", utc_now())
        metadata_set(conn, "fts_available", "true" if fts_available else "false")
        conn.commit()

        doc = {
            "schema": {"version": SCHEMA_VERSION},
            "generated_at": metadata_get(conn, "generated_at"),
            "repository": {
                "head": new_head,
                "dirty_fingerprint": metadata_get(conn, "dirty_fingerprint"),
                "workspace_id": repository_identity(root)["workspace_id"],
            },
            "cache": {
                "kind": "rebuildable",
                "database": str(db_path),
                "canonical": False,
            },
            "providers": {
                "lexical": "sqlite-fts5" if fts_available else "sqlite-like-fallback",
                "symbols": "language-aware-regex",
                "graph": "project-intelligence-impact-graph",
                "history": "git",
                "semantic": {
                    "status": "NOT_CONFIGURED",
                    "provider": None,
                    "model": None,
                    "required": False,
                },
            },
            "coverage": {
                "files": count_table(conn, "files"),
                "chunks": count_table(conn, "chunks"),
                "symbols": count_table(conn, "symbols"),
                "commits": count_table(conn, "commits"),
            },
        }
        write_metadata_file(store, doc)
        return {
            "status": "READY",
            "full_rebuild": full,
            "changed_paths": sorted(changed),
            "indexed_paths": indexed,
            "removed_paths": removed,
            "index": str(db_path),
            "metadata": str(metadata_path(store)),
            "coverage": doc["coverage"],
            "providers": doc["providers"],
        }
    finally:
        conn.close()


def index_status(root: Path, store: Path) -> dict[str, Any]:
    path = metadata_path(store)
    db_path = index_path(root)
    if not path.is_file() or not db_path.is_file():
        return {"status": "MISSING", "index": str(db_path), "metadata": str(path)}
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {"status": "INVALID", "index": str(db_path), "metadata": str(path)}
    repo = doc.get("repository") or {}
    head = run_git(root, ["rev-parse", "HEAD"]) or "unknown"
    dirty = dirty_fingerprint(root)
    reasons: list[str] = []
    if str((doc.get("schema") or {}).get("version")) != str(SCHEMA_VERSION):
        reasons.append("retrieval_schema_changed")
    if repo.get("head") != head:
        reasons.append("git_head_changed")
    if repo.get("dirty_fingerprint") != dirty:
        reasons.append("dirty_workspace_changed")
    return {
        "status": "STALE" if reasons else "CURRENT",
        "reasons": reasons,
        "index": str(db_path),
        "metadata": str(path),
        "providers": doc.get("providers") or {},
        "coverage": doc.get("coverage") or {},
    }


def query_terms(query: str) -> list[str]:
    result: list[str] = []
    for token in TOKEN_RE.findall(query):
        low = token.lower()
        if low not in result:
            result.append(low)
    return result[:20]


def fts_expression(terms: list[str]) -> str:
    safe = [re.sub(r"[^A-Za-z0-9_\u4e00-\u9fff]", "", term) for term in terms]
    safe = [term for term in safe if term]
    return " OR ".join(f'"{term}"' for term in safe)


def load_graph_boosts(store: Path, terms: list[str]) -> set[str]:
    graph_path = store / "IMPACT_GRAPH.yaml"
    if not graph_path.is_file():
        return set()
    try:
        graph = yaml.safe_load(graph_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return set()
    boosts: set[str] = set()
    for node_id, node in (graph.get("nodes") or {}).items():
        if not isinstance(node, dict):
            continue
        source = str(node.get("source") or node.get("path") or "")
        haystack = f"{node_id} {source} {node.get('type', '')}".lower()
        if any(term in haystack for term in terms):
            if source:
                boosts.add(source)
    return boosts


def symbol_boosts(conn: sqlite3.Connection, terms: list[str]) -> dict[int, tuple[float, list[str]]]:
    boosts: dict[int, tuple[float, list[str]]] = {}
    for row in conn.execute("SELECT name, kind, path, line, chunk_id FROM symbols").fetchall():
        chunk_id = row["chunk_id"]
        if chunk_id is None:
            continue
        name = str(row["name"]).lower()
        matched = [term for term in terms if term == name or term in name]
        if not matched:
            continue
        exact = any(term == name for term in terms)
        # Exact symbol definitions should outrank generic lexical overlap.
        value = 0.95 if exact else 0.35
        old_value, old_reasons = boosts.get(int(chunk_id), (0.0, []))
        boosts[int(chunk_id)] = (
            max(old_value, value),
            list(dict.fromkeys([*old_reasons, f"symbol:{row['name']}"])),
        )
    return boosts


def companion_test_key(path: str) -> str:
    name = Path(path).name.lower()
    name = re.sub(
        r"(?:\.test|\.spec)?\.(?:py|go|js|jsx|ts|tsx|java|kt|kts|cs|php|rb|rs|swift|vue|svelte)$",
        "",
        name,
    )
    name = re.sub(r"^(?:test[_-])", "", name)
    name = re.sub(r"(?:[_-]test)$", "", name)
    return re.sub(r"[^a-z0-9]+", "", name)


def exact_symbol_companion_keys(
    conn: sqlite3.Connection,
    symbol_map: dict[int, tuple[float, list[str]]],
) -> dict[str, str]:
    result: dict[str, str] = {}
    for chunk_id, (boost, _) in symbol_map.items():
        if boost < 0.9:
            continue
        row = conn.execute("SELECT path FROM chunks WHERE id = ?", (chunk_id,)).fetchone()
        if not row:
            continue
        path = str(row["path"])
        if is_test_path(path):
            continue
        key = companion_test_key(path)
        if key:
            result[key] = path
    return result


def structural_relation_boosts(
    conn: sqlite3.Connection,
    symbol_map: dict[int, tuple[float, list[str]]],
    terms: list[str],
    fts_available: bool,
) -> tuple[dict[int, tuple[float, list[str]]], dict[str, Any]]:
    """Build a bounded, index-backed exact-identifier two-hop relation graph.

    This remains a trial lane. It seeds only from exact query symbols, uses the
    lexical index (or a bounded LIKE fallback) to discover bridge chunks, then
    resolves identifiers in those bridges through the indexed symbol table.
    """
    seed_rows: list[sqlite3.Row] = []
    exact_terms = set(terms)
    for chunk_id, (boost, _) in symbol_map.items():
        if boost < 0.9:
            continue
        for row in conn.execute(
            "SELECT name, path, chunk_id FROM symbols WHERE chunk_id = ?",
            (chunk_id,),
        ).fetchall():
            if str(row["name"]).lower() in exact_terms:
                seed_rows.append(row)

    stats: dict[str, Any] = {
        "seed_symbols": 0,
        "bridge_chunks": 0,
        "target_definitions": 0,
        "test_chunks_scanned": 0,
        "truncated": False,
        "limits": {
            "bridges": STRUCTURAL_MAX_BRIDGES,
            "identifiers_per_bridge": STRUCTURAL_MAX_IDENTIFIERS_PER_BRIDGE,
            "target_definitions": STRUCTURAL_MAX_TARGET_DEFINITIONS,
            "test_chunks": STRUCTURAL_MAX_TEST_CHUNKS,
        },
    }
    if not seed_rows:
        return {}, stats

    seed_names = {str(row["name"]) for row in seed_rows}
    seed_paths = {str(row["path"]) for row in seed_rows}
    stats["seed_symbols"] = len(seed_names)

    boosts: dict[int, tuple[float, list[str]]] = {}
    structural_paths: dict[str, str] = {}

    def add_boost(chunk_id: int, value: float, reason: str) -> None:
        old_value, old_reasons = boosts.get(chunk_id, (0.0, []))
        boosts[chunk_id] = (
            max(old_value, value),
            list(dict.fromkeys([*old_reasons, reason])),
        )

    bridges: dict[int, sqlite3.Row] = {}
    for seed_name in sorted(seed_names):
        remaining = STRUCTURAL_MAX_BRIDGES - len(bridges)
        if remaining <= 0:
            stats["truncated"] = True
            break

        rows: list[sqlite3.Row] = []
        if fts_available:
            try:
                rows = conn.execute(
                    """
                    SELECT c.id, c.path, c.text
                    FROM chunks_fts
                    JOIN chunks c ON c.id = chunks_fts.rowid
                    WHERE chunks_fts MATCH ?
                    LIMIT ?
                    """,
                    (f'"{seed_name}"', remaining + 1),
                ).fetchall()
            except sqlite3.OperationalError:
                rows = []

        if not rows:
            rows = conn.execute(
                "SELECT id, path, text FROM chunks WHERE instr(text, ?) > 0 LIMIT ?",
                (seed_name, remaining + 1),
            ).fetchall()

        for row in rows:
            if len(bridges) >= STRUCTURAL_MAX_BRIDGES:
                stats["truncated"] = True
                break
            source_path = str(row["path"])
            if source_path in seed_paths:
                continue
            tokens = set(IDENTIFIER_RE.findall(str(row["text"])))
            if seed_name not in tokens:
                continue
            bridges[int(row["id"])] = row

    stats["bridge_chunks"] = len(bridges)
    target_ids: set[int] = set()

    for bridge_id, chunk in sorted(bridges.items()):
        source_path = str(chunk["path"])
        tokens = sorted(set(IDENTIFIER_RE.findall(str(chunk["text"]))))
        if len(tokens) > STRUCTURAL_MAX_IDENTIFIERS_PER_BRIDGE:
            tokens = tokens[:STRUCTURAL_MAX_IDENTIFIERS_PER_BRIDGE]
            stats["truncated"] = True

        matched_seeds = sorted(seed_names & set(tokens))
        if not matched_seeds:
            continue

        add_boost(
            bridge_id,
            0.62,
            "structural_reference_to_seed:" + ",".join(matched_seeds),
        )
        structural_paths[source_path] = "bridge"

        if not tokens:
            continue
        placeholders = ",".join("?" for _ in tokens)
        target_rows = conn.execute(
            f"SELECT name, path, chunk_id FROM symbols "
            f"WHERE chunk_id IS NOT NULL AND name IN ({placeholders})",
            tuple(tokens),
        ).fetchall()

        by_name: dict[str, list[sqlite3.Row]] = {}
        for target in target_rows:
            by_name.setdefault(str(target["name"]), []).append(target)

        for token in tokens:
            targets = by_name.get(token) or []
            if not targets or len(targets) > 4:
                continue
            for target in targets:
                target_path = str(target["path"])
                target_chunk = target["chunk_id"]
                if target_chunk is None:
                    continue
                target_id = int(target_chunk)
                if target_path == source_path or target_path in seed_paths:
                    continue
                if target_id not in target_ids and len(target_ids) >= STRUCTURAL_MAX_TARGET_DEFINITIONS:
                    stats["truncated"] = True
                    continue
                target_ids.add(target_id)
                add_boost(
                    target_id,
                    0.58,
                    f"structural_two_hop:{matched_seeds[0]}->{source_path}->{token}",
                )
                if not is_test_path(target_path):
                    structural_paths[target_path] = "target"

    stats["target_definitions"] = len(target_ids)

    companion_keys = {
        companion_test_key(path): path
        for path in structural_paths
        if not is_test_path(path) and companion_test_key(path)
    }
    if companion_keys:
        test_rows = conn.execute(
            "SELECT id, path FROM chunks WHERE kind = 'test' LIMIT ?",
            (STRUCTURAL_MAX_TEST_CHUNKS + 1,),
        ).fetchall()
        if len(test_rows) > STRUCTURAL_MAX_TEST_CHUNKS:
            stats["truncated"] = True
            test_rows = test_rows[:STRUCTURAL_MAX_TEST_CHUNKS]
        stats["test_chunks_scanned"] = len(test_rows)
        for chunk in test_rows:
            path = str(chunk["path"])
            key = companion_test_key(path)
            if key in companion_keys:
                add_boost(
                    int(chunk["id"]),
                    0.52,
                    f"structural_companion_test:{companion_keys[key]}",
                )

    return boosts, stats


def lexical_candidates(conn: sqlite3.Connection, fts_available: bool, terms: list[str], limit: int = 80) -> list[sqlite3.Row]:
    if not terms:
        return []
    if fts_available:
        expression = fts_expression(terms)
        if not expression:
            return []
        try:
            return conn.execute(
                """
                SELECT c.*, bm25(chunks_fts) AS lexical_rank
                FROM chunks_fts
                JOIN chunks c ON c.id = chunks_fts.rowid
                WHERE chunks_fts MATCH ?
                ORDER BY lexical_rank
                LIMIT ?
                """,
                (expression, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            pass

    clauses = " OR ".join("lower(text) LIKE ?" for _ in terms)
    values = [f"%{term}%" for term in terms]
    return conn.execute(
        f"SELECT *, 1.0 AS lexical_rank FROM chunks WHERE {clauses} LIMIT ?",
        (*values, limit),
    ).fetchall()


def lexical_score(rank: Any) -> float:
    try:
        value = abs(float(rank))
    except Exception:
        return 0.2
    return max(0.05, min(0.75, 1.0 / (1.0 + value)))


def history_candidates(conn: sqlite3.Connection, root: Path, terms: list[str], limit: int = 3) -> list[dict[str, Any]]:
    ranked: list[tuple[int, int, int, sqlite3.Row]] = []
    for row in conn.execute("SELECT sha, subject, body, paths, authored_at FROM commits").fetchall():
        message = f"{row['subject']} {row['body']}".lower()
        path_text = str(row["paths"]).lower()
        message_overlap = sum(1 for term in terms if term in message)
        path_overlap = sum(1 for term in terms if term in path_text)
        if message_overlap or path_overlap:
            # Commit-message intent is stronger evidence than a broad commit merely
            # touching a path whose name happens to overlap the query.
            rank_value = message_overlap * 10 + min(path_overlap, 3)
            ranked.append((rank_value, message_overlap, path_overlap, row))
    best_message_overlap = max((item[1] for item in ranked), default=0)
    if best_message_overlap:
        # When commit intent is visible in the message, suppress weak path-only
        # history and low-signal message matches from broad initialization commits.
        message_floor = max(1, math.ceil(best_message_overlap / 2))
        ranked = [item for item in ranked if item[1] >= message_floor]
    ranked.sort(key=lambda item: (-item[0], str(item[3]["authored_at"])), reverse=False)

    results: list[dict[str, Any]] = []
    for _, message_overlap, path_overlap, row in ranked[:limit]:
        safe_paths = [
            path for path in str(row["paths"]).splitlines()
            if path and is_indexable(path) and not is_secret_path(path)
        ]
        if safe_paths:
            diff = run_git(root, ["show", "--format=", "--unified=6", str(row["sha"]), "--", *safe_paths]) or ""
        else:
            diff = ""
        snippet = redact_text(diff)[:MAX_HISTORY_DIFF_CHARS]
        reasons: list[str] = []
        if message_overlap:
            reasons.append("git_history_message_overlap")
        if path_overlap:
            reasons.append("git_history_path_overlap")
        score = min(
            0.60,
            0.16 + message_overlap * 0.10 + min(path_overlap, 3) * 0.025,
        )
        evidence_text = f"{row['subject']}\n{snippet}"
        results.append({
            "type": "history",
            "commit": row["sha"],
            "subject": row["subject"],
            "authored_at": row["authored_at"],
            "paths": safe_paths[:20],
            "score": round(score, 4),
            "reason": reasons,
            "snippet": snippet,
            "content_hash": sha(evidence_text),
        })
    return results


def token_estimate(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def query_repository(
    root: Path,
    store: Path,
    query: str,
    *,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
    limit: int = DEFAULT_RESULT_LIMIT,
    refresh: bool = True,
    structural: bool = False,
) -> dict[str, Any]:
    status_before = index_status(root, store)
    index_update = None
    if status_before["status"] == "MISSING":
        return {
            "status": "INDEX_MISSING",
            "query": query,
            "index": status_before,
            "semantic": {"status": "NOT_CONFIGURED", "provider": None, "required": False},
            "results": [],
            "token_budget": token_budget,
            "estimated_tokens": 0,
        }
    if status_before["status"] in {"STALE", "INVALID"} and refresh:
        index_update = index_repository(root, store, force=status_before["status"] == "INVALID")

    status_now = index_status(root, store)
    if status_now["status"] not in {"CURRENT"}:
        return {
            "status": "INDEX_STALE",
            "query": query,
            "index": status_now,
            "semantic": ((status_now.get("providers") or {}).get("semantic") or {"status": "NOT_CONFIGURED"}),
            "results": [],
            "token_budget": token_budget,
            "estimated_tokens": 0,
        }

    terms = query_terms(query)
    db_path = index_path(root)
    conn, fts_available = open_db(db_path)
    try:
        symbol_map = symbol_boosts(conn, terms)
        exact_companion_keys = exact_symbol_companion_keys(conn, symbol_map)
        structural_map: dict[int, tuple[float, list[str]]] = {}
        structural_stats: dict[str, Any] = {
            "seed_symbols": 0,
            "bridge_chunks": 0,
            "target_definitions": 0,
            "test_chunks_scanned": 0,
            "truncated": False,
        }
        if structural:
            structural_map, structural_stats = structural_relation_boosts(
                conn, symbol_map, terms, fts_available
            )
        graph_paths = load_graph_boosts(store, terms)
        candidates = lexical_candidates(conn, fts_available, terms)

        scored: list[dict[str, Any]] = []
        seen_chunks: set[int] = set()
        for row in candidates:
            chunk_id = int(row["id"])
            score = lexical_score(row["lexical_rank"])
            reasons = ["lexical"]
            if chunk_id in symbol_map:
                boost, symbol_reasons = symbol_map[chunk_id]
                score += boost
                reasons.extend(symbol_reasons)
            if chunk_id in structural_map:
                boost, structural_reasons = structural_map[chunk_id]
                score += boost
                reasons.extend(structural_reasons)
            if str(row["path"]) in graph_paths:
                score += 0.25
                reasons.append("impact_graph")
            if is_test_path(str(row["path"])):
                score += 0.08
                reasons.append("test_evidence")
                test_key = companion_test_key(str(row["path"]))
                if test_key in exact_companion_keys:
                    score += 0.70
                    reasons.append(f"companion_test:{exact_companion_keys[test_key]}")
            scored.append({
                "type": str(row["kind"]),
                "path": str(row["path"]),
                "start_line": int(row["start_line"]),
                "end_line": int(row["end_line"]),
                "score": round(min(score, 1.5), 4),
                "reason": list(dict.fromkeys(reasons)),
                "snippet": str(row["text"]),
                "content_hash": str(row["content_hash"]),
                "_chunk_id": chunk_id,
            })
            seen_chunks.add(chunk_id)

        for chunk_id, (boost, symbol_reasons) in symbol_map.items():
            if chunk_id in seen_chunks:
                continue
            row = conn.execute("SELECT * FROM chunks WHERE id = ?", (chunk_id,)).fetchone()
            if not row:
                continue
            structural_boost, structural_reasons = structural_map.get(chunk_id, (0.0, []))
            scored.append({
                "type": str(row["kind"]),
                "path": str(row["path"]),
                "start_line": int(row["start_line"]),
                "end_line": int(row["end_line"]),
                "score": round(min(boost + structural_boost, 1.5), 4),
                "reason": list(dict.fromkeys([*symbol_reasons, *structural_reasons])),
                "snippet": str(row["text"]),
                "content_hash": str(row["content_hash"]),
                "_chunk_id": chunk_id,
            })
            seen_chunks.add(chunk_id)

        for chunk_id, (boost, structural_reasons) in structural_map.items():
            if chunk_id in seen_chunks:
                continue
            row = conn.execute("SELECT * FROM chunks WHERE id = ?", (chunk_id,)).fetchone()
            if not row:
                continue
            scored.append({
                "type": str(row["kind"]),
                "path": str(row["path"]),
                "start_line": int(row["start_line"]),
                "end_line": int(row["end_line"]),
                "score": round(boost, 4),
                "reason": list(dict.fromkeys(structural_reasons)),
                "snippet": str(row["text"]),
                "content_hash": str(row["content_hash"]),
                "_chunk_id": chunk_id,
            })
            seen_chunks.add(chunk_id)

        scored.sort(key=lambda item: (-float(item["score"]), item["path"], item["start_line"]))
        history = history_candidates(conn, root, terms)

        combined = [*scored[: max(limit * 3, 20)], *history]
        combined.sort(key=lambda item: (-float(item["score"]), str(item.get("path") or item.get("commit") or "")))

        selected: list[dict[str, Any]] = []
        consumed = 0
        path_counts: dict[str, int] = {}
        for item in combined:
            if len(selected) >= limit:
                break
            key = str(item.get("path") or f"commit:{item.get('commit')}")
            if item.get("type") != "history" and path_counts.get(key, 0) >= 2:
                continue
            estimate = token_estimate(str(item.get("snippet") or ""))
            if selected and consumed + estimate > token_budget:
                continue
            if not selected and estimate > token_budget:
                snippet = str(item.get("snippet") or "")[: max(200, token_budget * 4)]
                item = dict(item)
                item["snippet"] = snippet
                estimate = token_estimate(snippet)
            public = {k: v for k, v in item.items() if not k.startswith("_")}
            public["estimated_tokens"] = estimate
            public["revision"] = {
                "git_head": run_git(root, ["rev-parse", "HEAD"]) or "unknown",
                "dirty_fingerprint": dirty_fingerprint(root),
            }
            selected.append(public)
            consumed += estimate
            path_counts[key] = path_counts.get(key, 0) + 1

        semantic = ((status_now.get("providers") or {}).get("semantic") or {
            "status": "NOT_CONFIGURED", "provider": None, "required": False,
        })
        return {
            "status": "READY",
            "query": query,
            "terms": terms,
            "index": status_now,
            "index_update": index_update,
            "semantic": semantic,
            "structural": {
                "status": "TRIAL_ENABLED" if structural else "DISABLED",
                "mode": "exact-identifier-two-hop",
                "external_dependency": False,
                "default_enabled": False,
                "telemetry": structural_stats,
            },
            "ranking": {
                "lanes": [
                    "lexical",
                    "symbol",
                    "companion_test",
                    *(["structural_reference_graph"] if structural else []),
                    "impact_graph",
                    "test_evidence",
                    "git_history",
                ],
                "semantic_lane_active": semantic.get("status") == "READY",
                "structural_lane_active": structural,
            },
            "token_budget": token_budget,
            "estimated_tokens": consumed,
            "result_limit": limit,
            "results": selected,
        }
    finally:
        conn.close()


def compact_pointer(result: dict[str, Any]) -> str:
    if result.get("type") == "history":
        return f"commit:{result.get('commit')} {result.get('subject')}"
    return f"{result.get('path')}:{result.get('start_line')}-{result.get('end_line')}"

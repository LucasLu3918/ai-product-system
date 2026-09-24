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

from git_paths import GitPathsError, run_git_nul_output, run_git_paths
from aips_identity import config_home as canonical_config_home
from aips_identity import repository_identity as canonical_repository_identity
from temporal_intelligence import load_temporal, temporal_digest, validate_document as validate_temporal_document

SCHEMA_VERSION = 4
DEFAULT_TOKEN_BUDGET = 6000
DEFAULT_RESULT_LIMIT = 12
MAX_FILE_BYTES = 1_000_000
MAX_HISTORY = 200
MAX_HISTORY_DIFF_CHARS = 1600
STRUCTURAL_MAX_BRIDGES = 120
STRUCTURAL_MAX_IDENTIFIERS_PER_BRIDGE = 200
STRUCTURAL_MAX_TARGET_DEFINITIONS = 200
STRUCTURAL_MAX_TEST_CHUNKS = 500
IMPACT_MAX_DEPTH = 4
IMPACT_MAX_NODES = 100
IMPACT_MAX_EDGES = 250
IMPACT_MAX_RELATIONS_PER_FILE = 5000
SEMANTIC_ALIAS_LIMIT = 32
SEMANTIC_ALIAS_PATH = Path(__file__).resolve().parents[1] / "templates/intelligence/SEMANTIC_ALIASES.yaml"
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
    ".vue": [("symbol", re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(?:function|class)\s+([A-Za-z_$][A-Za-z0-9_$]*)"))],
    ".svelte": [("symbol", re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(?:function|class)\s+([A-Za-z_$][A-Za-z0-9_$]*)"))],
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
    paths = run_git_paths(root, ["ls-files", "--cached", "--others", "--exclude-standard", "-z", "--"])
    result: list[str] = []
    for value in paths:
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
        ["diff", "--name-only", "-z", "--"],
        ["diff", "--cached", "--name-only", "-z", "--"],
        ["ls-files", "--others", "--exclude-standard", "-z", "--"],
    ):
        result.update(run_git_paths(root, args))
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
        CREATE TABLE IF NOT EXISTS relations (
            source_name TEXT NOT NULL,
            source_path TEXT NOT NULL,
            source_definition_line INTEGER NOT NULL,
            target_name TEXT NOT NULL,
            source_line INTEGER NOT NULL,
            relation TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            PRIMARY KEY(source_path, source_line, target_name, relation)
        );
        CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_name, relation);
        CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_name, source_path);
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
        CREATE TABLE IF NOT EXISTS temporal_assertions (
            id TEXT PRIMARY KEY,
            subject TEXT NOT NULL,
            predicate TEXT NOT NULL,
            object TEXT NOT NULL,
            from_revision TEXT,
            to_revision_exclusive TEXT,
            history_quality TEXT NOT NULL,
            payload TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_temporal_subject_predicate
            ON temporal_assertions(subject, predicate);
        CREATE TABLE IF NOT EXISTS temporal_supersession (
            assertion_id TEXT NOT NULL,
            supersedes_id TEXT NOT NULL,
            PRIMARY KEY(assertion_id, supersedes_id)
        );
        CREATE TABLE IF NOT EXISTS revision_ancestry_cache (
            ancestor TEXT NOT NULL,
            descendant TEXT NOT NULL,
            is_ancestor INTEGER NOT NULL,
            PRIMARY KEY(ancestor, descendant)
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
    try:
        return set(run_git_paths(root, ["diff", "--name-only", "-z", f"{old_head}..{new_head}", "--"]))
    except GitPathsError:
        return None


def replace_file_index(conn: sqlite3.Connection, root: Path, rel_path: str, fts_available: bool) -> bool:
    conn.execute("DELETE FROM symbols WHERE path = ?", (rel_path,))
    conn.execute("DELETE FROM relations WHERE source_path = ?", (rel_path,))
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
    for relation in extract_code_relations(rel_path, text):
        conn.execute(
            """INSERT OR REPLACE INTO relations(
                source_name, source_path, source_definition_line, target_name,
                source_line, relation, content_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                relation["source_name"], rel_path, relation["source_definition_line"],
                relation["target_name"], relation["source_line"], relation["relation"],
                file_hash,
            ),
        )
    return True


_CALL_KEYWORDS = {
    "if", "for", "while", "switch", "catch", "with", "function", "class",
    "def", "async", "return", "new", "typeof", "sizeof", "nameof", "select",
    "where", "when", "lock", "using", "import", "require", "assert", "print",
}
_CALL_PATTERN = re.compile(r"(?<![\w$])([A-Za-z_$][A-Za-z0-9_$]*)\s*\(")
_REFERENCE_PATTERN = re.compile(r"(?<![\w$])([A-Za-z_$][A-Za-z0-9_$]*)(?![\w$])")


def code_without_comments_or_strings(text: str) -> str:
    """Mask comments and quoted strings while preserving line and column offsets."""
    out = list(text)
    i = 0
    state = "code"
    quote = ""
    while i < len(text):
        char = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if state == "line":
            if char == "\n":
                state = "code"
            else:
                out[i] = " "
            i += 1
            continue
        if state == "block":
            if char == "*" and nxt == "/":
                out[i] = out[i + 1] = " "
                i += 2
                state = "code"
                continue
            if char != "\n":
                out[i] = " "
            i += 1
            continue
        if state == "string":
            if char == "\\":
                if char != "\n":
                    out[i] = " "
                if i + 1 < len(text):
                    if text[i + 1] != "\n":
                        out[i + 1] = " "
                    i += 2
                    continue
            if text.startswith(quote, i):
                for offset in range(len(quote)):
                    if text[i + offset] != "\n":
                        out[i + offset] = " "
                i += len(quote)
                state = "code"
                continue
            if char != "\n":
                out[i] = " "
            i += 1
            continue

        if char == "/" and nxt == "/":
            out[i] = out[i + 1] = " "
            i += 2
            state = "line"
            continue
        if char == "/" and nxt == "*":
            out[i] = out[i + 1] = " "
            i += 2
            state = "block"
            continue
        if char == "#" or (char == "-" and nxt == "-"):
            out[i] = " "
            if nxt == "-":
                out[i + 1] = " "
                i += 2
            else:
                i += 1
            state = "line"
            continue
        if char in "'\"`":
            quote = char * 3 if text.startswith(char * 3, i) else char
            for offset in range(len(quote)):
                if text[i + offset] != "\n":
                    out[i + offset] = " "
            i += len(quote)
            state = "string"
            continue
        i += 1
    return "".join(out)


def extract_code_relations(rel_path: str, text: str) -> list[dict[str, Any]]:
    """Extract bounded lexical call/reference candidates, never compiler semantics."""
    ext = Path(rel_path).suffix.lower()
    if ext not in SYMBOL_PATTERNS or is_secret_path(rel_path):
        return []
    definitions = extract_symbols(rel_path, text)
    masked = code_without_comments_or_strings(text)
    rows: list[dict[str, Any]] = []
    lines = masked.splitlines()
    for line_no, line in enumerate(lines, start=1):
        owner_name = "@file"
        owner_line = 0
        for name, _kind, definition_line in definitions:
            if definition_line > line_no:
                break
            owner_name, owner_line = name, definition_line
        if owner_name != "@file" and any(
            definition_line == line_no and name == owner_name
            for name, _kind, definition_line in definitions
        ):
            continue
        call_names = {
            match.group(1) for match in _CALL_PATTERN.finditer(line)
            if match.group(1).lower() not in _CALL_KEYWORDS
        }
        names = set(_REFERENCE_PATTERN.findall(line))
        for name in sorted(names):
            if name.lower() in _CALL_KEYWORDS:
                continue
            relation = "calls" if name in call_names else "references"
            rows.append({
                "source_name": owner_name,
                "source_definition_line": owner_line,
                "target_name": name,
                "source_line": line_no,
                "relation": relation,
            })
            if len(rows) >= IMPACT_MAX_RELATIONS_PER_FILE:
                return rows
    return rows


def risk_adaptive_policy(risk_class: str) -> dict[str, Any]:
    key = re.sub(r"[^a-z0-9]+", "_", str(risk_class).lower()).strip("_")
    policies: dict[str, dict[str, Any]] = {
        "docs_style_test": {"required_depth": 0, "max_depth": 0, "directions": [], "history_required": False},
        "private_leaf": {"required_depth": 1, "max_depth": IMPACT_MAX_DEPTH, "directions": ["callers"], "history_required": False},
        "function_signature": {"required_depth": 2, "max_depth": IMPACT_MAX_DEPTH, "directions": ["callers"], "history_required": True},
        "return_shape": {"required_depth": 2, "max_depth": IMPACT_MAX_DEPTH, "directions": ["callers", "consumers"], "history_required": True},
        "shared_dto": {"required_depth": 2, "max_depth": IMPACT_MAX_DEPTH, "directions": ["callers", "consumers"], "history_required": True},
        "api_contract": {"required_depth": 2, "max_depth": IMPACT_MAX_DEPTH, "directions": ["callers", "consumers"], "history_required": True},
        "db_schema": {"required_depth": 2, "max_depth": IMPACT_MAX_DEPTH, "directions": ["callers", "consumers"], "history_required": True},
        "event_schema": {"required_depth": 2, "max_depth": IMPACT_MAX_DEPTH, "directions": ["callers", "consumers"], "history_required": True},
        "shared_library": {"required_depth": 2, "max_depth": IMPACT_MAX_DEPTH, "directions": ["callers", "consumers"], "history_required": True},
        "security_boundary": {"required_depth": 2, "max_depth": IMPACT_MAX_DEPTH, "directions": ["callers", "consumers"], "history_required": True},
        "payment": {"required_depth": 2, "max_depth": IMPACT_MAX_DEPTH, "directions": ["callers", "consumers"], "history_required": True},
    }
    return {"risk_class": key, **policies[key]} if key in policies else {
        "risk_class": key, "status": "UNKNOWN_RISK_CLASS", "required_depth": None,
        "max_depth": IMPACT_MAX_DEPTH, "directions": ["callers", "consumers"],
        "history_required": True,
    }


def traverse_change_impact(
    root: Path,
    store: Path,
    seeds: list[dict[str, Any]],
    risk_class: str,
    directions: list[str] | None = None,
    max_depth: int | None = None,
    max_nodes: int = IMPACT_MAX_NODES,
    max_edges: int = IMPACT_MAX_EDGES,
    changed_paths: list[str] | None = None,
) -> dict[str, Any]:
    """Return bounded, lexical caller/consumer candidates with explicit uncertainty."""
    policy = risk_adaptive_policy(risk_class)
    requested_directions = list(dict.fromkeys(directions or policy["directions"]))
    depth_limit = policy["max_depth"] if max_depth is None else max_depth
    depth_limit = min(max(0, int(depth_limit)), IMPACT_MAX_DEPTH)
    max_nodes = min(max(1, int(max_nodes)), IMPACT_MAX_NODES)
    max_edges = min(max(1, int(max_edges)), IMPACT_MAX_EDGES)
    report: dict[str, Any] = {
        "policy_version": 1,
        "policy": "risk-adaptive-bounded",
        "risk_class": policy["risk_class"],
        "status": "INCOMPLETE",
        "seeds": seeds,
        "directions": requested_directions,
        "required_depth": {"callers": policy["required_depth"]},
        "reached_depth": {direction: 0 for direction in requested_directions},
        "max_depth": depth_limit,
        "limits": {"nodes": max_nodes, "edges": max_edges, "depth": depth_limit},
        "visited_nodes": 0,
        "visited_edges": 0,
        "truncated": False,
        "stop_reason": None,
        "nodes": [],
        "paths": [],
        "unresolved": [],
        "history_evidence": [],
        "evidence": [],
        "resolution": {"exact": [], "inferred": [], "unresolved": []},
    }
    if policy.get("status"):
        report["status"] = "INCOMPLETE"
        report["stop_reason"] = "unknown_risk_class"
        report["unresolved"].append({"kind": "risk_class", "value": policy["risk_class"]})
        report["resolution"]["unresolved"].append(policy["risk_class"])
        return report
    if any(direction not in {"callers", "consumers"} for direction in requested_directions):
        report["stop_reason"] = "invalid_direction"
        report["unresolved"].append({"kind": "direction", "values": requested_directions})
        return report
    if depth_limit < int(policy["required_depth"]):
        report["stop_reason"] = "depth_below_required_minimum"
        report["truncated"] = True
        return report

    status = index_status(root, store)
    if status.get("status") != "CURRENT":
        report["status"] = "INCOMPLETE"
        report["stop_reason"] = "retrieval_index_" + str(status.get("status", "unavailable")).lower()
        report["index_status"] = status.get("status")
        report["unresolved"].append({"kind": "retrieval_index", "status": status.get("status")})
        report["resolution"]["unresolved"].append("retrieval_index")
        return report

    db_path = index_path(root)
    try:
        conn, _fts_available = open_db(db_path)
    except (OSError, sqlite3.Error) as exc:
        report["stop_reason"] = "retrieval_index_unavailable"
        report["unresolved"].append({"kind": "retrieval_index", "status": "INDEX_UNAVAILABLE"})
        report["resolution"]["unresolved"].append("retrieval_index")
        return report

    visited: dict[tuple[str, str, int], dict[str, Any]] = {}
    frontier: list[dict[str, Any]] = []
    edge_rows: list[dict[str, Any]] = []
    changed_set = set(changed_paths or [])
    try:
        for seed in seeds:
            name = str(seed.get("symbol") or seed.get("name") or "").strip()
            if not name:
                report["unresolved"].append({"kind": "seed", "reason": "empty_symbol"})
                continue
            seed_path = seed.get("path")
            seed_line = seed.get("line")
            if seed_path and not seed_line:
                definitions = conn.execute(
                    "SELECT line FROM symbols WHERE name = ? AND path = ? ORDER BY line LIMIT 2",
                    (name, str(seed_path)),
                ).fetchall()
                if len(definitions) == 1:
                    seed_line = int(definitions[0]["line"])
                elif len(definitions) > 1:
                    report["unresolved"].append({"kind": "ambiguous_seed_definition", "symbol": name, "path": str(seed_path), "candidate_count": len(definitions)})
            node = {"symbol": name, "path": seed_path, "line": seed_line, "depth": 0, "kind": "seed"}
            key = (name, str(node["path"] or ""), int(node["line"] or 0))
            visited[key] = node
            frontier.append(node)

        if not frontier:
            report["stop_reason"] = "no_valid_seeds"
            return report

        for seed in seeds:
            name = str(seed.get("symbol") or seed.get("name") or "").strip()
            if not name:
                continue
            for chunk in conn.execute(
                "SELECT path, start_line, text FROM chunks WHERE instr(text, ?) > 0 LIMIT 20",
                (name,),
            ).fetchall():
                snippet = str(chunk["text"])
                if re.search(r"(?is)(resolve|dispatch|emit|subscribe|register|route|inject|handler)\s*[^\n]{0,100}[\"']" + re.escape(name) + r"[\"']", snippet):
                    unknown = {"kind": "dynamic_relationship", "symbol": name, "path": str(chunk["path"]), "line": int(chunk["start_line"]), "resolution": "unresolved"}
                    report["unresolved"].append(unknown)
                    report["resolution"]["unresolved"].append(name)

        for direction in requested_directions:
            direction_frontier = list(frontier)
            while direction_frontier:
                current = direction_frontier.pop(0)
                depth = int(current["depth"])
                if depth >= depth_limit:
                    if direction == "callers":
                        more = conn.execute(
                            "SELECT source_name, source_path, source_definition_line FROM relations "
                            "WHERE target_name = ? AND relation = 'calls' LIMIT ?",
                            (current["symbol"], max_nodes + 1),
                        ).fetchall()
                        unseen = any(
                            (str(row["source_name"]), str(row["source_path"]), int(row["source_definition_line"])) not in visited
                            for row in more
                        )
                    else:
                        more = conn.execute(
                            "SELECT target_name, source_path, source_definition_line FROM relations "
                            "WHERE source_name = ? AND source_path = ? LIMIT ?",
                            (current["symbol"], str(current.get("path") or ""), max_nodes + 1),
                        ).fetchall()
                        unseen = any(
                            conn.execute("SELECT 1 FROM symbols WHERE name = ? LIMIT 1", (str(row["target_name"]),)).fetchone()
                            for row in more
                        )
                    if unseen or len(more) > max_nodes:
                        report["truncated"] = True
                        report["stop_reason"] = "max_depth"
                    continue
                if direction == "callers":
                    rows = conn.execute(
                        "SELECT source_name, source_path, source_definition_line, target_name, source_line, relation "
                        "FROM relations WHERE target_name = ? AND relation = 'calls' "
                        "ORDER BY source_path, source_line LIMIT ?",
                        (current["symbol"], max_edges - len(edge_rows) + 1),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT source_name, source_path, source_definition_line, target_name, source_line, relation "
                        "FROM relations WHERE source_name = ? AND source_path = ? "
                        "ORDER BY source_line LIMIT ?",
                        (current["symbol"], str(current.get("path") or ""), max_edges - len(edge_rows) + 1),
                    ).fetchall()
                if len(rows) > max_edges - len(edge_rows):
                    report["truncated"] = True
                    report["stop_reason"] = "max_edges"
                    rows = rows[: max(0, max_edges - len(edge_rows))]
                definitions = conn.execute(
                    "SELECT path, line FROM symbols WHERE name = ? ORDER BY path, line LIMIT 9",
                    (current["symbol"],),
                ).fetchall()
                target_matches = [row for row in definitions if str(row["path"]) == str(current.get("path")) and (not current.get("line") or int(row["line"]) == int(current["line"]))]
                if direction == "callers" and current.get("path") and definitions and not target_matches:
                    continue
                if direction == "callers" and len(definitions) > 1 and not current.get("path"):
                    report["unresolved"].append({"kind": "ambiguous_seed_definition", "symbol": current["symbol"], "candidate_count": len(definitions)})
                    report["resolution"]["unresolved"].append(current["symbol"])
                for row in rows:
                    if len(edge_rows) >= max_edges:
                        report["truncated"] = True
                        report["stop_reason"] = "max_edges"
                        break
                    source_name = str(row["source_name"])
                    source_path = str(row["source_path"])
                    source_definition_line = int(row["source_definition_line"])
                    source_line = int(row["source_line"])
                    if direction == "callers":
                        next_name, next_path, next_line = source_name, source_path, source_definition_line
                        from_ref = {"symbol": source_name, "path": source_path, "line": source_definition_line or None}
                        to_ref = {"symbol": current["symbol"], "path": current.get("path"), "line": current.get("line")}
                    else:
                        next_name = str(row["target_name"])
                        target_definitions = conn.execute(
                            "SELECT path, line FROM symbols WHERE name = ? ORDER BY path, line LIMIT 9",
                            (next_name,),
                        ).fetchall()
                        if not target_definitions:
                            report["unresolved"].append({"kind": "unresolved_consumer_target", "symbol": next_name, "path": source_path, "line": source_line})
                            report["resolution"]["unresolved"].append(next_name)
                            continue
                        if len(target_definitions) > 1:
                            report["unresolved"].append({"kind": "ambiguous_consumer_target", "symbol": next_name, "candidate_count": len(target_definitions), "path": source_path, "line": source_line})
                            report["resolution"]["unresolved"].append(next_name)
                        next_path, next_line = str(target_definitions[0]["path"]), int(target_definitions[0]["line"])
                        from_ref = {"symbol": source_name, "path": source_path, "line": source_definition_line or None}
                        to_ref = {"symbol": next_name, "path": next_path, "line": next_line}
                    node = {"symbol": next_name, "path": next_path, "line": next_line or None, "depth": depth + 1, "kind": "file_scope" if next_name == "@file" else ("caller" if direction == "callers" else "consumer")}
                    key = (next_name, next_path, next_line)
                    edge = {
                        "from": from_ref,
                        "to": to_ref,
                        "relation": str(row["relation"]),
                        "direction": direction,
                        "source_path": source_path,
                        "source_line": source_line,
                        "resolution": "inferred",
                    }
                    if direction == "callers" and definitions and len(definitions) > 1:
                        edge["resolution"] = "ambiguous"
                        report["unresolved"].append({"kind": "ambiguous_target", "symbol": current["symbol"], "path": current.get("path"), "candidate_count": len(definitions), "evidence": {"path": source_path, "line": source_line}})
                        report["resolution"]["unresolved"].append(current["symbol"])
                    edge_rows.append(edge)
                    if edge["resolution"] == "inferred":
                        report["resolution"]["inferred"].append({"symbol": current["symbol"], "path": source_path, "line": source_line})
                    if key not in visited:
                        if len(visited) >= max_nodes:
                            report["truncated"] = True
                            report["stop_reason"] = "max_nodes"
                            continue
                        visited[key] = node
                        direction_frontier.append(node)
                    report["reached_depth"][direction] = max(report["reached_depth"][direction], depth + 1)
                    if len(edge_rows) >= max_edges or len(visited) >= max_nodes:
                        break
                if report["truncated"] and report["stop_reason"] in {"max_edges", "max_nodes"}:
                    direction_frontier.clear()
                    break

        nodes = list(visited.values())
        for node in nodes:
            path = str(node.get("path") or "")
            if node.get("kind") == "seed":
                continue
            node["impact_status"] = "affected_and_changed" if path in changed_set else ("affected_but_unchanged" if changed_set else "affected_candidate")
            node["disposition"] = "pending_review"
            if path:
                path_obj = root / path
                if path_obj.is_file() and not is_secret_path(path):
                    try:
                        file_text = path_obj.read_text(encoding="utf-8", errors="replace")
                        map_lines = [n for n, line in enumerate(file_text.splitlines(), start=1) if re.search(r"\.\s*map\s*\(", line)]
                        if map_lines:
                            node["consumer_hints"] = [{"kind": "map_call", "lines": map_lines[:10]}]
                    except OSError:
                        pass
        report["nodes"] = sorted(nodes, key=lambda item: (int(item["depth"]), str(item.get("path") or ""), str(item["symbol"])))
        report["visited_nodes"] = len(visited)
        report["visited_edges"] = len(edge_rows)
        report["paths"] = edge_rows
        report["evidence"] = [{"path": edge["source_path"], "line": edge["source_line"], "relation": edge["relation"], "resolution": edge["resolution"]} for edge in edge_rows]

        seeds_names = [str(seed.get("symbol") or seed.get("name") or "") for seed in seeds]
        if policy["history_required"] or report["unresolved"]:
            terms = sorted({name.lower() for name in seeds_names if name})
            history = history_candidates(conn, root, terms, limit=5) if terms else []
            report["history_evidence"] = [
                {"commit": row["commit"], "subject": redact_text(str(row["subject"])), "authored_at": row["authored_at"], "paths": row["paths"], "reason": row["reason"]}
                for row in history
            ]

        # COMPLETE describes exhaustion of the bounded indexed candidate graph, not compiler-grade repository semantics.
        report["status"] = "TRUNCATED" if report["truncated"] else ("BOUNDED_WITH_UNKNOWNS" if report["unresolved"] else "COMPLETE")
        if report["stop_reason"] is None:
            report["stop_reason"] = "frontier_exhausted"
        return report
    finally:
        conn.close()


def refresh_commits(conn: sqlite3.Connection, root: Path) -> None:
    raw = run_git_nul_output(
        root,
        [
            "log", "-z", f"-n{MAX_HISTORY}",
            "--date=iso-strict",
            "--pretty=format:%x1e%H%x1f%aI%x1f%s%x1f%b%x00",
            "--name-only",
        ],
    )
    records = []
    for record in raw.split(b"\x1e"):
        if not record:
            continue
        fields = record.split(b"\0")
        header = fields[0].split(b"\x1f", 3)
        if len(header) != 4:
            raise GitPathsError("git_history_invalid_header")
        commit_sha, authored_at, subject, body = [part.decode("utf-8", errors="replace") for part in header]
        paths = []
        for part in fields[1:]:
            if not part:
                continue
            # Git emits one separator newline before the first path.
            if not paths and part.startswith(b"\n"):
                part = part[1:]
            path = os.fsdecode(part)
            if path and not is_secret_path(path):
                paths.append(path)
        records.append((commit_sha, redact_text(subject), redact_text(body), json.dumps(paths, ensure_ascii=True), authored_at))
    conn.execute("DELETE FROM commits")
    for commit_sha, subject, body, paths, authored_at in records:
        conn.execute(
            "INSERT OR REPLACE INTO commits(sha, subject, body, paths, authored_at) VALUES (?, ?, ?, ?, ?)",
            (commit_sha, subject, body, paths, authored_at),
        )


def refresh_temporal(conn: sqlite3.Connection, store: Path) -> dict[str, Any]:
    """Project canonical temporal YAML into rebuildable query tables."""
    doc = load_temporal(store)
    errors = validate_temporal_document(doc)
    if errors:
        raise ValueError("invalid temporal assertions: " + "; ".join(errors))
    conn.execute("DELETE FROM temporal_supersession")
    conn.execute("DELETE FROM temporal_assertions")
    count = 0
    links = 0
    for assertion in doc.get("assertions") or []:
        validity = assertion.get("validity") or {}
        assertion_id = str(assertion.get("id"))
        conn.execute(
            """INSERT INTO temporal_assertions
               (id, subject, predicate, object, from_revision, to_revision_exclusive, history_quality, payload)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                assertion_id,
                str(assertion.get("subject")),
                str(assertion.get("predicate")),
                str(assertion.get("object")),
                None if str(validity.get("from_revision")).upper() == "UNKNOWN" else validity.get("from_revision"),
                None if str(validity.get("to_revision_exclusive")).upper() in {"NONE", "NULL", "UNKNOWN"} else validity.get("to_revision_exclusive"),
                str(assertion.get("history_quality") or "UNKNOWN").upper(),
                json.dumps(assertion, ensure_ascii=False, sort_keys=True),
            ),
        )
        count += 1
        supersedes = assertion.get("supersedes") or []
        if isinstance(supersedes, str):
            supersedes = [supersedes]
        for target in supersedes:
            conn.execute(
                "INSERT INTO temporal_supersession(assertion_id, supersedes_id) VALUES (?, ?)",
                (assertion_id, str(target)),
            )
            links += 1
    digest = temporal_digest(doc)
    metadata_set(conn, "temporal_digest", digest)
    return {"assertions": count, "supersession_links": links, "digest": digest}


def count_table(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"])


def write_metadata_file(store: Path, doc: dict[str, Any]) -> None:
    path = metadata_path(store)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temp.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    os.replace(temp, path)


def index_unavailable(exc: BaseException, *, token_budget: int = 0, query: str | None = None) -> dict[str, Any]:
    message = str(exc).lower()
    if "unable to open database file" in message or "database or disk is full" in message:
        code = "SQLITE_OPEN_FAILED"
    elif isinstance(exc, PermissionError) or "permission denied" in message or "operation not permitted" in message:
        code = "RETRIEVAL_CACHE_ACCESS_DENIED"
    elif "database disk image is malformed" in message or "not a database" in message:
        code = "SQLITE_DATABASE_INVALID"
    else:
        code = "RETRIEVAL_INDEX_UNAVAILABLE"
    remediation = (
        "Rebuild the disposable index with aips intelligence index --project <project> --force."
        if code == "SQLITE_DATABASE_INVALID"
        else "Check that the configured AIPS cache directory is accessible and writable, then rebuild with aips intelligence index --project <project> --force."
    )
    result: dict[str, Any] = {
        "status": "INDEX_UNAVAILABLE",
        "reason_code": code,
        "remediation": remediation,
        "results": [],
        "token_budget": token_budget,
        "estimated_tokens": 0,
    }
    if query is not None:
        result["query"] = query
    return result


def index_repository(root: Path, store: Path, force: bool = False) -> dict[str, Any]:
    root = root.resolve()
    db_path = index_path(root)
    try:
        conn, fts_available = open_db(db_path)
    except (OSError, sqlite3.Error) as exc:
        return index_unavailable(exc)
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

        temporal = refresh_temporal(conn, store)

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
                "temporal": {
                    "status": "READY",
                    "provider": "revision-aware-yaml",
                    "canonical": "TEMPORAL_ASSERTIONS.yaml",
                },
                "structural": {
                    "status": "READY",
                    "provider": "builtin-exact-identifier-two-hop",
                    "external_dependency": False,
                    "default_enabled": True,
                },
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
                "temporal_assertions": count_table(conn, "temporal_assertions"),
                "temporal_supersession_links": count_table(conn, "temporal_supersession"),
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
            "temporal": temporal,
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
    try:
        dirty = dirty_fingerprint(root)
    except GitPathsError as exc:
        return {
            "status": "UNKNOWN", "reasons": [str(exc)],
            "index": str(db_path), "metadata": str(path),
            "providers": doc.get("providers") or {},
            "coverage": doc.get("coverage") or {},
        }
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


def semantic_alias_expansion(terms: list[str]) -> tuple[list[str], dict[str, Any]]:
    telemetry: dict[str, Any] = {
        "provider": "builtin-curated-software-aliases",
        "matched_groups": [],
        "matched_group_terms": {},
        "expanded_terms": [],
        "truncated": False,
        "limit": SEMANTIC_ALIAS_LIMIT,
    }
    if not SEMANTIC_ALIAS_PATH.is_file():
        telemetry["status"] = "UNAVAILABLE"
        return [], telemetry
    try:
        doc = yaml.safe_load(SEMANTIC_ALIAS_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        telemetry["status"] = "INVALID"
        return [], telemetry

    source_terms = set(terms)
    expanded: list[str] = []
    for group in doc.get("groups") or []:
        if not isinstance(group, dict):
            continue
        group_terms = [
            str(item).lower()
            for item in (group.get("terms") or [])
            if str(item).strip()
        ]
        if not source_terms.intersection(group_terms):
            continue
        group_id = str(group.get("id") or "unnamed")
        telemetry["matched_groups"].append(group_id)
        telemetry["matched_group_terms"][group_id] = group_terms
        for term in group_terms:
            if term in source_terms or term in expanded:
                continue
            if len(expanded) >= SEMANTIC_ALIAS_LIMIT:
                telemetry["truncated"] = True
                break
            expanded.append(term)
        if telemetry["truncated"]:
            break
    telemetry["expanded_terms"] = expanded
    telemetry["status"] = "READY"
    return expanded, telemetry


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


def semantic_alias_boosts(
    conn: sqlite3.Connection,
    fts_available: bool,
    alias_terms: list[str],
    matched_group_terms: dict[str, list[str]],
    limit: int = 80,
) -> dict[int, tuple[float, list[str]]]:
    if not alias_terms or not matched_group_terms:
        return {}
    boosts: dict[int, tuple[float, list[str]]] = {}
    for row in lexical_candidates(conn, fts_available, alias_terms, limit=limit):
        text = str(row["text"]).lower()
        matched_groups: list[str] = []
        matched_terms: list[str] = []
        for group_id, group_terms in matched_group_terms.items():
            hits = [term for term in group_terms if term in text]
            if not hits:
                continue
            matched_groups.append(group_id)
            matched_terms.extend(hits[:2])
        if not matched_groups:
            continue

        # Cross-group coherence is the signal. A single broad alias such as
        # "session" or "token" must not outrank a chunk that jointly expresses
        # credential lifecycle + invalidation + rotation intent.
        group_count = len(matched_groups)
        if group_count >= 3:
            value = 0.78
        elif group_count == 2:
            value = 0.58
        else:
            value = 0.06
        boosts[int(row["id"])] = (
            value,
            [
                *[f"semantic_alias_group:{group}" for group in matched_groups[:4]],
                *[f"semantic_alias:{term}" for term in list(dict.fromkeys(matched_terms))[:4]],
            ],
        )
    return boosts


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
        paths = json.loads(str(row["paths"]))
        path_text = " ".join(paths).lower()
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
        safe_paths = [path for path in json.loads(str(row["paths"])) if path and is_indexable(path) and not is_secret_path(path)]
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
    structural: bool | None = None,
    semantic_aliases: bool = False,
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
        if index_update.get("status") == "INDEX_UNAVAILABLE":
            return {**index_update, "query": query, "token_budget": token_budget}

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

    structural_enabled = True if structural is None else structural
    structural_selection = "default" if structural is None else "explicit"
    terms = query_terms(query)
    alias_terms: list[str] = []
    alias_telemetry: dict[str, Any] = {
        "provider": "builtin-curated-software-aliases",
        "matched_groups": [],
        "expanded_terms": [],
        "truncated": False,
        "limit": SEMANTIC_ALIAS_LIMIT,
        "status": "DISABLED",
    }
    if semantic_aliases:
        alias_terms, alias_telemetry = semantic_alias_expansion(terms)
    db_path = index_path(root)
    try:
        conn, fts_available = open_db(db_path)
    except (OSError, sqlite3.Error) as exc:
        return index_unavailable(exc, token_budget=token_budget, query=query)
    try:
        symbol_map = symbol_boosts(conn, terms)
        exact_companion_keys = exact_symbol_companion_keys(conn, symbol_map)
        alias_map = semantic_alias_boosts(
            conn,
            fts_available,
            alias_terms,
            dict(alias_telemetry.get("matched_group_terms") or {}),
        ) if semantic_aliases else {}
        structural_map: dict[int, tuple[float, list[str]]] = {}
        structural_stats: dict[str, Any] = {
            "seed_symbols": 0,
            "bridge_chunks": 0,
            "target_definitions": 0,
            "test_chunks_scanned": 0,
            "truncated": False,
        }
        if structural_enabled:
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
            if chunk_id in alias_map:
                boost, alias_reasons = alias_map[chunk_id]
                score += boost
                reasons.extend(alias_reasons)
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

        for chunk_id, (boost, alias_reasons) in alias_map.items():
            if chunk_id in seen_chunks:
                continue
            row = conn.execute("SELECT * FROM chunks WHERE id = ?", (chunk_id,)).fetchone()
            if not row:
                continue
            reasons = list(alias_reasons)
            score = boost
            if is_test_path(str(row["path"])):
                score += 0.08
                reasons.append("test_evidence")
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

        scored.sort(key=lambda item: (-float(item["score"]), item["path"], item["start_line"]))
        history_terms = [*terms, *alias_terms] if semantic_aliases else terms
        history = history_candidates(conn, root, history_terms)

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
            "semantic_alias": {
                "status": "TRIAL_ENABLED" if semantic_aliases else "DISABLED",
                "provider": "builtin-curated-software-aliases",
                "external_dependency": False,
                "default_enabled": False,
                "telemetry": alias_telemetry,
            },
            "structural": {
                "status": "READY" if structural_enabled else "DISABLED",
                "mode": "exact-identifier-two-hop",
                "external_dependency": False,
                "default_enabled": True,
                "enabled": structural_enabled,
                "selection": structural_selection,
                "telemetry": structural_stats,
            },
            "ranking": {
                "lanes": [
                    "lexical",
                    "symbol",
                    "companion_test",
                    *(["structural_reference_graph"] if structural_enabled else []),
                    *(["semantic_alias_expansion"] if semantic_aliases else []),
                    "impact_graph",
                    "test_evidence",
                    "git_history",
                ],
                "semantic_lane_active": semantic.get("status") == "READY",
                "structural_lane_active": structural_enabled,
                "semantic_alias_lane_active": semantic_aliases,
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

"""SQLite persistence helpers for the disposable Retrieval Intelligence index."""
from __future__ import annotations

import shutil
import sqlite3
import tempfile
from pathlib import Path


def open_db(path: Path) -> tuple[sqlite3.Connection, bool]:
    """Open the writable retrieval cache and create its existing schema."""
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


def open_read_db(
    path: Path,
) -> tuple[sqlite3.Connection, bool, tempfile.TemporaryDirectory[str] | None]:
    """Read an existing index without running schema or journal writes."""
    snapshot: tempfile.TemporaryDirectory[str] | None = None
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        fts_available = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='chunks_fts'"
        ).fetchone() is not None
        return conn, fts_available, None
    except sqlite3.OperationalError:
        # SQLite may connect successfully but fail on its first read when a
        # sandbox denies WAL shared memory. Never snapshot a live WAL alone.
        if conn is not None:
            conn.close()
        if path.with_name(path.name + "-wal").exists():
            raise
    before = path.stat()
    snapshot = tempfile.TemporaryDirectory(prefix="aips-retrieval-read-")
    conn = None
    try:
        copied = Path(snapshot.name) / "index.sqlite"
        shutil.copyfile(path, copied)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or path.with_name(path.name + "-wal").exists():
            raise sqlite3.OperationalError("retrieval index changed during read-only snapshot")
        conn = sqlite3.connect(copied.as_uri() + "?mode=ro", uri=True)
        if conn.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise sqlite3.DatabaseError("retrieval index snapshot failed integrity check")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        fts_available = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='chunks_fts'"
        ).fetchone() is not None
        return conn, fts_available, snapshot
    except BaseException:
        if conn is not None:
            conn.close()
        snapshot.cleanup()
        raise


def metadata_get(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row else None


def metadata_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO metadata(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )

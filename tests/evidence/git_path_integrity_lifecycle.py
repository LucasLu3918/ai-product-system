#!/usr/bin/env python3
"""Exercise Git filename transport and complete Intelligence freshness checks."""

from __future__ import annotations

import os
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import sqlite3

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import git_paths  # noqa: E402
import project_intelligence as intelligence  # noqa: E402
import retrieval_intelligence as retrieval  # noqa: E402


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def make_repo(root: Path) -> None:
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.name", "AIPS Evidence")
    git(root, "config", "user.email", "aips@example.invalid")
    (root / "base.py").write_text("base = True\n", encoding="utf-8")
    git(root, "add", "--", "base.py")
    git(root, "commit", "-qm", "base")


def filename_cases(base: Path) -> None:
    root = base / "names"
    make_repo(root)
    names = ["說明.py", "with space.py", 'quote"name.py', "-leading.py"]
    if os.name != "nt":
        names += ["tab\tname.py", "line\nname.py"]
    for index, name in enumerate(names):
        (root / name).write_text(f"value = {index}\n", encoding="utf-8")
    git(root, "add", "--", *names[:-1])
    for quote in ("true", "false"):
        git(root, "config", "core.quotePath", quote)
        assert set(names) <= set(retrieval.tracked_and_untracked_files(root))
        assert set(names) <= set(retrieval.dirty_paths(root))
        assert set(names) <= set(intelligence.git_dirty_paths(root))

    old_head = git(root, "rev-parse", "HEAD")
    git(root, "commit", "-qm", "special filenames")
    new_head = git(root, "rev-parse", "HEAD")
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE commits (sha TEXT PRIMARY KEY, subject TEXT, body TEXT, paths TEXT, authored_at TEXT)")
    retrieval.refresh_commits(conn, root)
    indexed = json.loads(conn.execute("SELECT paths FROM commits WHERE sha = ?", (new_head,)).fetchone()["paths"])
    assert set(names[:-1]) <= set(indexed), indexed
    conn.close()
    for quote in ("true", "false"):
        git(root, "config", "core.quotePath", quote)
        assert set(names[:-1]) <= set(intelligence.changed_paths_between(root, old_head, new_head) or [])
        assert set(names[:-1]) <= (retrieval.changed_paths_between(root, old_head, new_head) or set())

    git(root, "mv", "--", "說明.py", "重新命名.py")
    (root / "with space.py").unlink()
    git(root, "add", "-u")
    for quote in ("true", "false"):
        git(root, "config", "core.quotePath", quote)
        assert {"重新命名.py", "with space.py"} <= set(intelligence.git_dirty_paths(root))
        assert {"重新命名.py", "with space.py"} <= set(retrieval.dirty_paths(root))
    git(root, "commit", "-qm", "rename and remove")
    renamed_head = git(root, "rev-parse", "HEAD")
    assert {"重新命名.py", "with space.py"} <= set(intelligence.changed_paths_between(root, new_head, renamed_head) or [])


def freshness_cases(base: Path) -> None:
    root = base / "freshness"
    make_repo(root)
    store = base / "intelligence"
    store.mkdir()
    (store / "PROJECT_INTELLIGENCE.yaml").write_text(yaml.safe_dump({
        "schema": {"version": intelligence.SCHEMA_VERSION},
        "project": {"branch": git(root, "branch", "--show-current")},
        "verified": {"git_head": git(root, "rev-parse", "HEAD")},
        "topics": {"architecture": {"watch": ["zzz.py"]}},
    }), encoding="utf-8")
    original_store = intelligence.intelligence_store
    intelligence.intelligence_store = lambda _root: (store, "EPHEMERAL", "fixture")
    try:
        for i in range(1000):
            (root / f"a{i:04d}.txt").write_text("unrelated\n", encoding="utf-8")
        (root / "zzz.py").write_text("watched = True\n", encoding="utf-8")
        state = intelligence.freshness(root)
        assert state["status"] == "STALE", state
        assert "dirty_watched_path:zzz.py" in state["reasons"]
        assert state["dirty_path_scan"] == {
            "total_count": 1001, "examined_count": 1001, "truncated": False,
        }
        assert state["dirty_paths_display_truncated"] is True
        assert "zzz.py" not in state["dirty_paths"]  # Display truncation does not affect the decision.

        original_limit = git_paths.MAX_GIT_PATH_OUTPUT_BYTES
        git_paths.MAX_GIT_PATH_OUTPUT_BYTES = 20
        try:
            unknown = intelligence.freshness(root)
            assert unknown["status"] == "UNKNOWN", unknown
            assert "git_paths_output_limit" in unknown["reasons"]
            assert unknown["dirty_path_scan"]["truncated"] is True
            context = intelligence.context_manifest(root, "codex", "modify zzz.py")
            assert context["fail_policy"]["mode"] == "closed"
            assert "intelligence_freshness_unknown" in context["fail_policy"]["reasons"]

            original_index_path = retrieval.index_path
            db_path = base / "index.sqlite"
            db_path.touch()
            (store / "RETRIEVAL_INDEX.yaml").write_text(yaml.safe_dump({
                "schema": {"version": retrieval.SCHEMA_VERSION},
                "repository": {"head": git(root, "rev-parse", "HEAD")},
            }), encoding="utf-8")
            retrieval.index_path = lambda _root: db_path
            try:
                assert retrieval.index_status(root, store)["status"] == "UNKNOWN"
            finally:
                retrieval.index_path = original_index_path
        finally:
            git_paths.MAX_GIT_PATH_OUTPUT_BYTES = original_limit
    finally:
        intelligence.intelligence_store = original_store


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        filename_cases(base)
        freshness_cases(base)
    print("git_path_integrity_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

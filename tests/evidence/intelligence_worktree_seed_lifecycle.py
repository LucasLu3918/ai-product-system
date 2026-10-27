#!/usr/bin/env python3
"""Lifecycle evidence for copy-on-write Project Intelligence seeding across worktrees.

Runs the real project_intelligence CLI against temporary git repositories and a
temporary XDG_CONFIG_HOME. Covers: a new worktree before and after seeding,
watched-path staleness, source-store removal, gc on seeded stores, and the
symlink fallback. Nothing outside the temporary directory is written.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PI = ROOT / "scripts" / "project_intelligence.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def pi_json(command: list[str], env: dict[str, str]) -> dict:
    result = subprocess.run(
        [sys.executable, str(PI), *command, "--format", "json"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    require(
        result.returncode == 0,
        f"project_intelligence {command[0]} failed: {result.stdout} {result.stderr}",
    )
    return json.loads(result.stdout)


def init_repo(path: Path) -> None:
    path.mkdir(parents=True)
    git(path, "init", "-q")
    git(path, "branch", "-m", "main")
    git(path, "config", "user.email", "aips" + chr(64) + "example.invalid")
    git(path, "config", "user.name", "AIPS Evidence")
    (path / "src").mkdir()
    (path / "src" / "app.py").write_text("print('a')\n", encoding="utf-8")
    (path / "README.md").write_text("# demo\n", encoding="utf-8")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "initial")


def mark_ready(env: dict[str, str], project: Path) -> Path:
    store = Path(pi_json(["status", "--project", str(project)], env)["store"])
    manifest = store / "PROJECT_INTELLIGENCE.yaml"
    intel = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    intel["state"]["readiness"] = "READY"
    intel["topics"] = {"modules": {"watch": ["src/**"]}}
    manifest.write_text(
        yaml.safe_dump(intel, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return store


def seed_and_staleness(base: Path, env: dict[str, str]) -> Path:
    main = base / "main"
    init_repo(main)
    pi_json(["bootstrap", "--project", str(main)], env)
    source_store = mark_ready(env, main)

    wt = base / "wt-feature"
    git(main, "worktree", "add", "-q", str(wt), "-b", "feature")

    before = pi_json(["status", "--project", str(wt)], env)
    require(
        before["freshness"]["status"] == "MISSING",
        f"new worktree must start MISSING before seeding: {before}",
    )

    seeded = pi_json(["bootstrap", "--project", str(wt)], env)
    require(
        seeded.get("status") == "SEEDED",
        f"new worktree must be seeded from the primary store: {seeded}",
    )
    require(
        seeded["seeded_from"]["selection"] == "primary_worktree",
        f"primary must be selected: {seeded}",
    )
    require(
        str(main) not in json.dumps(seeded),
        "user-facing output must not contain another worktree's absolute path",
    )

    after = pi_json(["status", "--project", str(wt)], env)
    require(
        after["freshness"]["status"] == "CURRENT",
        f"seeded worktree must be CURRENT: {after}",
    )
    require(
        "worktree_identity_seeded_from_same_repository"
        in after["freshness"]["observations"],
        f"seeding must turn the identity change into an observation: {after}",
    )
    require(
        "worktree_identity_changed" not in after["freshness"]["reasons"],
        "identity change must not be a reason",
    )

    (wt / "docs").mkdir()
    (wt / "docs" / "notes.md").write_text("unrelated\n", encoding="utf-8")
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", "docs")
    unrelated = pi_json(["status", "--project", str(wt)], env)
    require(
        unrelated["freshness"]["status"] == "CURRENT",
        f"unrelated commit must not make the store STALE: {unrelated}",
    )

    (wt / "src" / "app.py").write_text("print('b')\n", encoding="utf-8")
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", "app")
    stale = pi_json(["status", "--project", str(wt)], env)
    require(
        stale["freshness"]["status"] == "STALE"
        and stale["freshness"]["affected_topics"] == ["modules"],
        f"watched change must make only the affected topic STALE: {stale}",
    )

    require(
        yaml.safe_load(
            (source_store / "PROJECT_INTELLIGENCE.yaml").read_text(encoding="utf-8")
        )["project"]["root"]
        == str(main),
        "the source store must keep its own recorded root",
    )
    return main


def gc_keeps_seeded_store_after_source_removal(
    base: Path, env: dict[str, str], main: Path
) -> None:
    main_store = Path(pi_json(["status", "--project", str(main)], env)["store"])
    shutil.rmtree(
        main_store.parent
    )  # the primary store is gone; seeded copies must not depend on it

    wt = base / "wt-feature"
    fr = pi_json(["status", "--project", str(wt)], env)["freshness"]
    require(
        fr["status"] == "STALE",
        "the seeded store stays usable after the source store is removed (watched change still pending)",
    )

    dry = pi_json(["gc"], env)
    orphan_stores = [item["store"] for item in dry["orphaned"]]
    require(
        str(Path(pi_json(["status", "--project", str(wt)], env)["store"]))
        not in orphan_stores,
        f"gc must keep a seeded store whose own worktree exists: {dry}",
    )


def gc_removes_seeded_store_when_its_worktree_is_removed(
    base: Path, env: dict[str, str], main: Path
) -> None:
    wt = base / "wt-feature"
    wt_store = Path(pi_json(["status", "--project", str(wt)], env)["store"])
    git(main, "worktree", "remove", "--force", str(wt))
    dry = pi_json(["gc"], env)
    require(
        [item["store"] for item in dry["orphaned"]] == [str(wt_store)],
        f"gc dry run must list only the seeded store whose worktree was removed: {dry}",
    )
    require(wt_store.is_dir(), "gc dry run must not delete anything")
    applied = pi_json(["gc", "--yes"], env)
    require(
        [item["store"] for item in applied["removed"]] == [str(wt_store)]
        and not wt_store.exists(),
        f"gc --yes must remove only that seeded store: {applied}",
    )


def symlink_fallback_is_observed(base: Path, env: dict[str, str]) -> None:
    repo = base / "fallback-main"
    init_repo(repo)
    pi_json(["bootstrap", "--project", str(repo)], env)
    store = mark_ready(env, repo)
    outside = base / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    os.symlink(outside, store / "NOTES.md")

    wt = base / "fallback-wt"
    git(repo, "worktree", "add", "-q", str(wt), "-b", "fallback")
    result = pi_json(["bootstrap", "--project", str(wt)], env)
    require(
        result.get("observations")
        == ["intelligence_seed_fallback:source_contains_symlink"],
        f"a refused seed must fall back with a diagnostic observation: {result}",
    )
    require(
        "readiness" in result and result.get("status") != "SEEDED",
        "fallback must use normal initialization",
    )
    wt_store = Path(result["store"])
    require(
        not (wt_store / "NOTES.md").exists(),
        "a refused seed must not copy the symlinked artifact",
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp).resolve()
        config = base / "config"
        config.mkdir()
        env = dict(os.environ)
        env["XDG_CONFIG_HOME"] = str(config)
        primary = seed_and_staleness(base, env)
        gc_keeps_seeded_store_after_source_removal(base, env, primary)
        gc_removes_seeded_store_when_its_worktree_is_removed(base, env, primary)
        symlink_fallback_is_observed(base, env)
    print("intelligence_worktree_seed_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

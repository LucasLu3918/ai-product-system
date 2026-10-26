"""Copy-on-write seeding of external Project Intelligence stores across worktrees.

A worktree without an external store is seeded from the READY store of another
worktree that git itself lists as part of the same repository. The copy is an
independent store: the source is only read, and every later write goes to the
new worktree's store. Seeding copies allowlisted Intelligence artifacts, records
provenance and never re-analyzes the repository. A refusal or error leaves no
partial store behind and is reported with a reason code, never with a path.
"""

from __future__ import annotations

import datetime as dt
import os
import secrets
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml
from aips_identity import config_home, repository_identity
from project_intelligence_storage import atomic_yaml

SEED_MANIFEST = "PROJECT_INTELLIGENCE.yaml"
SEED_TOP_LEVEL_FILES = (
    SEED_MANIFEST,
    "SOURCE_REGISTRY.yaml",
    "PROJECT_OVERRIDES.yaml",
    "IMPACT_GRAPH.yaml",
    "TEMPORAL_ASSERTIONS.yaml",
    "DISCOVERY.yaml",
)
SEED_TOPIC_DIR = "topics"
SEED_TOPIC_SUFFIXES = (".md", ".yaml")
SEED_STAGING_PREFIX = ".intelligence-seed-"
SEED_FAILURES = (
    OSError,
    ValueError,
    TypeError,
    KeyError,
    AttributeError,
    RuntimeError,
    yaml.YAMLError,
    shutil.Error,
)


class SeedRefused(Exception):
    """A safety check refused the seed; the message is a stable reason code."""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


def _now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def _git(path: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip()


def _common_dir(path: Path) -> str | None:
    raw = _git(path, "rev-parse", "--git-common-dir")
    if not raw:
        return None
    candidate = Path(raw)
    return str((candidate if candidate.is_absolute() else path / candidate).resolve())


def _listed_worktrees(root: Path) -> list[Path]:
    """Worktree paths in git's order; the first entry is the primary worktree."""
    output = _git(root, "worktree", "list", "--porcelain") or ""
    return [
        Path(line[len("worktree ") :])
        for line in output.splitlines()
        if line.startswith("worktree ")
    ]


def _load_manifest(path: Path) -> dict[str, Any] | None:
    if path.is_symlink() or not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return None
    return data if isinstance(data, dict) else None


def _confined_store(store: Path, projects: Path) -> bool:
    """True when the store sits directly under the real projects directory without symlinks."""
    if store.name != "intelligence" or store.is_symlink() or store.parent.is_symlink():
        return False
    try:
        return store.resolve(strict=True).parent.parent == projects.resolve(strict=True)
    except OSError:
        return False


def _source_candidates(
    root: Path, ident: dict[str, str], schema_version: int, projects: Path
) -> list[dict[str, Any]]:
    """Same-repository READY stores of other worktrees, best candidate first.

    Same-repository proof: git lists the worktree and reports the same common git
    directory, the AIPS repository identity matches, and the candidate store is the
    canonical store of that worktree whose recorded root is that worktree.
    Order: primary worktree first, then most recent verified_at, then workspace id.
    """
    common = _common_dir(root)
    if common is None:
        return []
    found: list[dict[str, Any]] = []
    for index, worktree in enumerate(_listed_worktrees(root)):
        if not worktree.is_dir() or worktree.resolve() == root.resolve():
            continue
        if _common_dir(worktree) != common:
            continue
        if (worktree / ".ai").exists() or (worktree / ".ai").is_symlink():
            continue
        candidate_ident = repository_identity(worktree)
        if candidate_ident["repository_id"] != ident["repository_id"]:
            continue
        store = projects / candidate_ident["workspace_id"] / "intelligence"
        if not store.is_dir() or not _confined_store(store, projects):
            continue
        intel = _load_manifest(store / SEED_MANIFEST)
        if (
            intel is None
            or (intel.get("schema") or {}).get("version") != schema_version
        ):
            continue
        if (intel.get("state") or {}).get("readiness") != "READY":
            continue
        project = intel.get("project") or {}
        if project.get("repository_id") != ident["repository_id"]:
            continue
        recorded = project.get("root")
        if not isinstance(recorded, str) or not os.path.isabs(recorded):
            continue
        if Path(recorded).resolve() != worktree.resolve():
            continue
        found.append(
            {
                "primary": index == 0,
                "workspace_id": candidate_ident["workspace_id"],
                "store": store,
                "intel": intel,
            }
        )
    found.sort(key=lambda item: item["workspace_id"])
    found.sort(
        key=lambda item: str(
            (item["intel"].get("verified") or {}).get("verified_at") or ""
        ),
        reverse=True,
    )
    found.sort(key=lambda item: not item["primary"])
    return found


def _collect_artifacts(source: Path) -> tuple[list[tuple[str, Path]], int]:
    """Allowlisted artifacts to copy, plus the count of excluded entries.

    Any symlink in the source store refuses the seed, so nothing is ever read
    through a link. Retrieval metadata, reviews, lock files, ad hoc notes and
    anything unrecognized are excluded.
    """
    for dirpath, dirnames, filenames in os.walk(source, followlinks=False):
        for name in (*dirnames, *filenames):
            if os.path.islink(os.path.join(dirpath, name)):
                raise SeedRefused("source_contains_symlink")
    artifacts: list[tuple[str, Path]] = []
    excluded = 0
    names = {entry.name for entry in source.iterdir()}
    if SEED_MANIFEST not in names:
        raise SeedRefused("source_manifest_missing")
    for entry in sorted(source.iterdir(), key=lambda item: item.name):
        if entry.name in SEED_TOP_LEVEL_FILES and entry.is_file():
            artifacts.append((entry.name, entry))
        elif entry.name == SEED_TOPIC_DIR and entry.is_dir():
            for topic in sorted(entry.iterdir(), key=lambda item: item.name):
                if topic.is_file() and topic.name.endswith(SEED_TOPIC_SUFFIXES):
                    artifacts.append((f"{SEED_TOPIC_DIR}/{topic.name}", topic))
                else:
                    excluded += 1
        else:
            excluded += 1
    return artifacts, excluded


def _only_empty_directories(path: Path) -> bool:
    for dirpath, dirnames, filenames in os.walk(path, followlinks=False):
        if filenames:
            return False
        if any(os.path.islink(os.path.join(dirpath, name)) for name in dirnames):
            return False
    return True


def _remove_empty_directories(path: Path) -> None:
    for dirpath, _dirnames, _filenames in os.walk(
        path, topdown=False, followlinks=False
    ):
        os.rmdir(dirpath)


def _seed(root: Path, store: Path, schema_version: int) -> dict[str, Any]:
    if store.is_symlink() or store.parent.is_symlink():
        raise SeedRefused("target_store_is_symlink")
    if store.exists() and (not store.is_dir() or not _only_empty_directories(store)):
        raise SeedRefused("target_store_not_empty")
    projects = config_home() / "projects"
    ident = repository_identity(root)
    candidates = _source_candidates(root, ident, schema_version, projects)
    if not candidates:
        return {"status": "NO_SOURCE", "reason_code": "no_ready_same_repository_store"}
    source = candidates[0]
    artifacts, excluded = _collect_artifacts(source["store"])
    source_intel = source["intel"]
    source_project = source_intel.get("project") or {}
    source_head = (source_intel.get("verified") or {}).get("git_head")
    selection = "primary_worktree" if source["primary"] else "most_recent_ready_store"

    staging: Path | None = None
    store.parent.mkdir(parents=True, exist_ok=True)
    try:
        staging = store.parent / f"{SEED_STAGING_PREFIX}{secrets.token_hex(8)}"
        staging.mkdir()
        for rel, src in artifacts:
            dst = staging / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
        manifest_path = staging / SEED_MANIFEST
        intel = _load_manifest(manifest_path)
        if intel is None or not isinstance(intel.get("project"), dict):
            raise SeedRefused("source_manifest_unusable")
        # Only the recorded root changes so GC and reviews point at this worktree.
        # worktree_identity keeps the source value; provenance proves the difference.
        intel["project"]["root"] = str(root)
        intel["provenance"] = {
            "seeded_from": {
                "project_id": source["workspace_id"],
                "git_head": source_head,
                "worktree_identity": source_project.get("worktree_identity"),
                "selection": selection,
            },
            "seeded_into": {
                "project_id": ident["workspace_id"],
                "worktree_identity": ident["worktree_id"],
                "repository_id": ident["repository_id"],
            },
            "seeded_at": _now(),
            "copied_artifact_count": len(artifacts),
            "excluded_artifact_count": excluded,
        }
        atomic_yaml(manifest_path, intel)
        if store.exists():
            _remove_empty_directories(store)
        os.rename(staging, store)
        staging = None
    finally:
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)
    return {
        "status": "SEEDED",
        "source_project_id": source["workspace_id"],
        "source_git_head": source_head,
        "selection": selection,
        "copied_artifact_count": len(artifacts),
        "excluded_artifact_count": excluded,
    }


def seed_worktree_store(
    root: Path, store: Path, *, schema_version: int
) -> dict[str, Any]:
    """Seed the absent external store of ``root``; never raises.

    Returns status SEEDED, NO_SOURCE, REFUSED or FAILED. Only REFUSED and FAILED
    carry a diagnostic reason_code for the caller's observation.
    """
    try:
        return _seed(root, store, schema_version)
    except SeedRefused as exc:
        return {"status": "REFUSED", "reason_code": exc.reason_code}
    except (
        SEED_FAILURES
    ) as exc:  # fail-safe: any I/O or parse error falls back to normal initialization
        return {
            "status": "FAILED",
            "reason_code": "seed_error",
            "error_type": type(exc).__name__,
        }


def seeded_worktree_change_proven(
    intel: dict[str, Any], ident: dict[str, str], stored_worktree_id: str
) -> bool:
    """True when a worktree_identity mismatch is explained by seeding into this worktree."""
    provenance = intel.get("provenance") or {}
    source = provenance.get("seeded_from") or {}
    target = provenance.get("seeded_into") or {}
    return bool(
        source.get("worktree_identity")
        and source.get("worktree_identity") == stored_worktree_id
        and target.get("worktree_identity") == ident["worktree_id"]
        and target.get("project_id") == ident["workspace_id"]
        and target.get("repository_id") == ident["repository_id"]
    )

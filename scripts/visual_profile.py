#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path
import subprocess
from typing import Any

import yaml


def run_git(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=project,
        capture_output=True,
        text=True,
    )


def git_output(project: Path, *args: str) -> str:
    result = run_git(project, *args)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "git command failed")
    return result.stdout.strip()


def load_profile(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("visual profile must be a YAML mapping")
    return data


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def path_matches(path: str, patterns: list[str]) -> bool:
    normalized = normalize_path(path)
    for raw in patterns:
        pattern = normalize_path(str(raw))
        if not pattern:
            continue
        if fnmatch.fnmatch(normalized, pattern):
            return True
        if pattern.endswith("/**") and normalized.startswith(pattern[:-3].rstrip("/") + "/"):
            return True
    return False


def committed_changes(project: Path, base: str, head: str) -> list[str]:
    if base == head:
        return []
    output = git_output(project, "diff", "--name-only", f"{base}..{head}")
    return sorted({normalize_path(line) for line in output.splitlines() if line.strip()})


def dirty_changes(project: Path) -> list[str]:
    result = run_git(project, "status", "--porcelain", "--untracked-files=all")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "git status failed")
    output = result.stdout
    paths: set[str] = set()
    for line in output.splitlines():
        if len(line) < 4:
            continue
        value = line[3:].strip()
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        if value:
            paths.add(normalize_path(value))
    return sorted(paths)


def commit_exists(project: Path, commit: str) -> bool:
    result = run_git(project, "cat-file", "-e", f"{commit}^{{commit}}")
    return result.returncode == 0


def evaluate(project: Path, profile_path: Path) -> dict[str, Any]:
    inside = run_git(project, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip().lower() != "true":
        return {
            "status": "BLOCKED",
            "decision": "FULL_DISCOVERY",
            "profile_loaded": False,
            "full_rescan_required": True,
            "targeted_refresh": False,
            "reasons": ["project_is_not_git_repository"],
        }
    if not profile_path.exists():
        return {
            "status": "MISSING",
            "decision": "FULL_DISCOVERY",
            "profile_loaded": False,
            "full_rescan_required": True,
            "targeted_refresh": False,
            "profile": str(profile_path),
            "reasons": ["visual_profile_missing"],
        }

    profile = load_profile(profile_path)
    current = git_output(project, "rev-parse", "HEAD")
    base = str(profile.get("last_verified_commit") or "").strip()
    watch = profile.get("watch") or {}
    patterns = [str(item) for item in (watch.get("paths") or []) if str(item).strip()]
    direction = profile.get("direction") or {}

    common = {
        "profile": str(profile_path),
        "profile_loaded": True,
        "last_verified_commit": base or None,
        "current_commit": current,
        "watch_paths": patterns,
        "direction_archetype": direction.get("archetype"),
        "direction_status": direction.get("status"),
    }

    if str(profile.get("status") or "").upper() == "STALE":
        return {
            **common,
            "status": "STALE",
            "decision": "FULL_DISCOVERY",
            "full_rescan_required": True,
            "targeted_refresh": False,
            "changed_paths": [],
            "affected_watched_paths": [],
            "reasons": ["profile_explicitly_stale"],
        }

    if not base:
        return {
            **common,
            "status": "UNKNOWN",
            "decision": "FULL_DISCOVERY",
            "full_rescan_required": True,
            "targeted_refresh": False,
            "changed_paths": [],
            "affected_watched_paths": [],
            "reasons": ["last_verified_commit_missing"],
        }

    if not commit_exists(project, base):
        return {
            **common,
            "status": "UNKNOWN",
            "decision": "FULL_DISCOVERY",
            "full_rescan_required": True,
            "targeted_refresh": False,
            "changed_paths": [],
            "affected_watched_paths": [],
            "reasons": ["last_verified_commit_unavailable"],
        }

    ancestor = run_git(project, "merge-base", "--is-ancestor", base, current)
    if ancestor.returncode != 0:
        return {
            **common,
            "status": "UNKNOWN",
            "decision": "FULL_DISCOVERY",
            "full_rescan_required": True,
            "targeted_refresh": False,
            "changed_paths": [],
            "affected_watched_paths": [],
            "reasons": ["last_verified_commit_not_ancestor"],
        }

    if not patterns:
        return {
            **common,
            "status": "UNKNOWN",
            "decision": "FULL_DISCOVERY",
            "full_rescan_required": True,
            "targeted_refresh": False,
            "changed_paths": [],
            "affected_watched_paths": [],
            "reasons": ["watch_paths_missing"],
        }

    changed = sorted(set(committed_changes(project, base, current) + dirty_changes(project)))
    affected = [path for path in changed if path_matches(path, patterns)]

    if affected:
        return {
            **common,
            "status": "STALE",
            "decision": "TARGETED_REFRESH",
            "full_rescan_required": False,
            "targeted_refresh": True,
            "changed_paths": changed,
            "affected_watched_paths": affected,
            "reasons": [f"watched_visual_source_changed:{path}" for path in affected],
        }

    return {
        **common,
        "status": "CURRENT",
        "decision": "REUSE",
        "full_rescan_required": False,
        "targeted_refresh": False,
        "changed_paths": changed,
        "affected_watched_paths": [],
        "reasons": ["watched_visual_sources_unchanged"],
    }


def emit(data: dict[str, Any], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Project Visual Profile freshness before visual rescans")
    sub = parser.add_subparsers(dest="command", required=True)
    status = sub.add_parser("status")
    status.add_argument("--project", default=".")
    status.add_argument("--profile", default="docs/design/PROJECT_VISUAL_PROFILE.yaml")
    status.add_argument("--format", choices=["yaml", "json"], default="yaml")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    profile = Path(args.profile)
    if not profile.is_absolute():
        profile = project / profile

    try:
        data = evaluate(project, profile)
        emit(data, args.format)
        return 2 if data.get("status") == "BLOCKED" else 0
    except (OSError, ValueError, RuntimeError, yaml.YAMLError) as exc:
        print("ERROR: " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

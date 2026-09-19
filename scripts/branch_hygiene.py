#!/usr/bin/env python3
"""Deterministic read-only branch lifecycle classifier for AIPS."""

from __future__ import annotations

import argparse
import fnmatch
import subprocess
from pathlib import Path
from typing import Any

import yaml


class BranchHygieneError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict) or data.get("version") != 1:
        raise BranchHygieneError("branch lifecycle config must be version 1 mapping")
    return data


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(["git", *args], text=True, capture_output=True)
    if check and proc.returncode != 0:
        raise BranchHygieneError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc


def integrated(branch: str, target: str) -> bool:
    ancestor = git("merge-base", "--is-ancestor", branch, target, check=False)
    if ancestor.returncode == 0:
        return True

    cherry = git("cherry", target, branch, check=False)
    if cherry.returncode == 0:
        rows = [line.strip() for line in cherry.stdout.splitlines() if line.strip()]
        if not rows or all(row.startswith("-") for row in rows):
            return True

    # Multi-commit branches are often squash-merged, so their individual patch IDs
    # do not necessarily appear in the target. A clean synthetic merge whose tree is
    # identical to the target proves that the branch contributes no remaining net
    # change without relying on GitHub PR metadata.
    merge_tree = git("merge-tree", "--write-tree", target, branch, check=False)
    if merge_tree.returncode != 0:
        return False
    merged_tree = next(
        (line.strip() for line in merge_tree.stdout.splitlines() if line.strip()),
        "",
    )
    target_tree = git("rev-parse", f"{target}^{{tree}}", check=False)
    return (
        target_tree.returncode == 0
        and bool(merged_tree)
        and merged_tree == target_tree.stdout.strip()
    )


def classify(name: str, config: dict[str, Any]) -> str:
    persistent = set(config.get("persistent_exact") or [])
    if name in persistent:
        return "PERSISTENT"
    for pattern in config.get("persistent_patterns") or []:
        if fnmatch.fnmatch(name, pattern):
            return "PERSISTENT"
    for pattern in config.get("ephemeral_patterns") or []:
        if fnmatch.fnmatch(name, pattern):
            return "EPHEMERAL"
    return "UNCLASSIFIED"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/branch-lifecycle.yaml"))
    parser.add_argument("--target")
    args = parser.parse_args()

    try:
        config = load_yaml(args.config)
        target = args.target or str(config.get("default_branch") or "main")
        refs = git("for-each-ref", "--format=%(refname:short)", "refs/heads").stdout.splitlines()
        branches = sorted({ref.strip() for ref in refs if ref.strip() and ref.strip() != target})
        report = []
        for name in branches:
            lifecycle = classify(name, config)
            is_integrated = integrated(name, target)
            report.append({
                "branch": name,
                "lifecycle": lifecycle,
                "integrated_into_target": is_integrated,
                "deletion_candidate": lifecycle == "EPHEMERAL" and is_integrated,
            })
        payload = {
            "version": 1,
            "target": target,
            "policy": "report_only",
            "branches": report,
            "authority": {
                "branch_deletion_authorized": False,
                "human_authority_preserved": True,
            },
        }
    except (OSError, yaml.YAMLError, BranchHygieneError) as exc:
        print(f"BRANCH HYGIENE BLOCKED: {exc}")
        return 2
    print(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

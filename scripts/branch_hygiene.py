#!/usr/bin/env python3
"""Deterministic branch lifecycle reporting and exact-manifest cleanup for AIPS."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml


class BranchHygieneError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict) or data.get("version") != 1:
        raise BranchHygieneError(f"{path} must be a version 1 mapping")
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

    merge_tree = git("merge-tree", "--write-tree", target, branch, check=False)
    if merge_tree.returncode != 0:
        return False
    merged_tree = next((line.strip() for line in merge_tree.stdout.splitlines() if line.strip()), "")
    target_tree = git("rev-parse", f"{target}^{{tree}}", check=False)
    return target_tree.returncode == 0 and bool(merged_tree) and merged_tree == target_tree.stdout.strip()


def classify(name: str, config: dict[str, Any]) -> str:
    if name in set(config.get("persistent_exact") or []):
        return "PERSISTENT"
    if any(fnmatch.fnmatch(name, pattern) for pattern in config.get("persistent_patterns") or []):
        return "PERSISTENT"
    if any(fnmatch.fnmatch(name, pattern) for pattern in config.get("ephemeral_patterns") or []):
        return "EPHEMERAL"
    return "UNCLASSIFIED"


def branch_refs(target: str, remote: str | None) -> tuple[str, list[tuple[str, str]]]:
    if remote:
        scope = f"refs/remotes/{remote}"
        raw = git("for-each-ref", "--format=%(refname:short)", scope).stdout.splitlines()
        prefix = f"{remote}/"
        rows: list[tuple[str, str]] = []
        for ref in raw:
            ref = ref.strip()
            if not ref or ref == f"{remote}/HEAD" or not ref.startswith(prefix):
                continue
            name = ref[len(prefix):]
            if name != target:
                rows.append((name, ref))
        target_ref = f"{remote}/{target}"
        if git("rev-parse", "--verify", target_ref, check=False).returncode != 0:
            raise BranchHygieneError(f"remote target ref not found: {target_ref}")
        return target_ref, sorted(set(rows))

    raw = git("for-each-ref", "--format=%(refname:short)", "refs/heads").stdout.splitlines()
    rows = sorted({(ref.strip(), ref.strip()) for ref in raw if ref.strip() and ref.strip() != target})
    return target, rows


def build_report(config: dict[str, Any], target: str, remote: str | None) -> dict[str, Any]:
    target_ref, refs = branch_refs(target, remote)
    rows = []
    for name, ref in refs:
        lifecycle = classify(name, config)
        is_integrated = integrated(ref, target_ref)
        rows.append({
            "branch": name,
            "lifecycle": lifecycle,
            "integrated_into_target": is_integrated,
            "deletion_candidate": lifecycle == "EPHEMERAL" and is_integrated,
        })
    return {
        "version": 1,
        "target": target,
        "ref_scope": f"remote:{remote}" if remote else "local",
        "policy": "report_only",
        "branches": rows,
        "authority": {
            "branch_deletion_authorized": False,
            "human_authority_preserved": True,
        },
    }


def github_pr_integrated(row: dict[str, Any], *, repository: str, target: str) -> bool:
    pr_number = row.get("merged_pr")
    expected = str(row.get("expected_sha") or "")
    branch = str(row.get("branch") or "")
    if not isinstance(pr_number, int) or pr_number < 1:
        return False
    env = dict(os.environ)
    proc = subprocess.run(
        ["gh", "api", f"repos/{repository}/pulls/{pr_number}"],
        text=True,
        capture_output=True,
        env=env,
    )
    if proc.returncode != 0:
        raise BranchHygieneError(
            proc.stderr.strip() or f"failed to verify merged PR #{pr_number} for {branch}"
        )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise BranchHygieneError(f"invalid GitHub PR evidence for #{pr_number}: {exc}") from exc
    return bool(
        payload.get("merged_at")
        and (payload.get("head") or {}).get("sha") == expected
        and (payload.get("head") or {}).get("ref") == branch
        and (payload.get("base") or {}).get("ref") == target
    )


def validate_cleanup_manifest(doc: dict[str, Any]) -> None:
    if doc.get("version") != 1:
        raise BranchHygieneError("cleanup manifest version must be 1")
    if not re.fullmatch(r"[0-9a-f]{40}", str(doc.get("baseline_main_sha") or "")):
        raise BranchHygieneError("cleanup manifest baseline_main_sha must be a full commit SHA")
    auth = doc.get("authorization") or {}
    if auth.get("type") != "explicit_user_request" or auth.get("scope") != "exact_manifest_only":
        raise BranchHygieneError("cleanup manifest requires explicit exact-list Human authorization")
    if auth.get("one_time") is not True:
        raise BranchHygieneError("cleanup manifest must be one_time=true")
    rows = doc.get("branches")
    if not isinstance(rows, list) or not rows:
        raise BranchHygieneError("cleanup manifest branches must be a non-empty list")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise BranchHygieneError("cleanup manifest branch entries must be mappings")
        name = str(row.get("branch") or "")
        sha = str(row.get("expected_sha") or "")
        if not name or name in seen:
            raise BranchHygieneError("cleanup manifest branch names must be unique and non-empty")
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise BranchHygieneError(f"{name}: expected_sha must be a full commit SHA")
        if not isinstance(row.get("merged_pr"), int) or row["merged_pr"] < 1:
            raise BranchHygieneError(f"{name}: merged_pr must be a positive integer")
        seen.add(name)


def apply_cleanup(
    config: dict[str, Any],
    manifest: dict[str, Any],
    *,
    target: str,
    remote: str,
    github_repository: str | None = None,
) -> dict[str, Any]:
    validate_cleanup_manifest(manifest)
    target_ref, refs = branch_refs(target, remote)
    ref_map = dict(refs)
    preflight: list[dict[str, Any]] = []
    blockers: list[str] = []

    for row in manifest["branches"]:
        name = row["branch"]
        expected = row["expected_sha"]
        ref = ref_map.get(name)
        if ref is None:
            preflight.append({"branch": name, "expected_sha": expected, "status": "ALREADY_ABSENT"})
            continue
        if name == target or classify(name, config) != "EPHEMERAL":
            blockers.append(f"{name}: branch is not an EPHEMERAL cleanup target")
            continue
        current = git("rev-parse", ref).stdout.strip()
        if current != expected:
            blockers.append(f"{name}: ref moved from approved SHA {expected} to {current}")
            continue
        local_integrated = integrated(ref, target_ref)
        pr_integrated = False
        if not local_integrated and github_repository:
            pr_integrated = github_pr_integrated(row, repository=github_repository, target=target)
        if not (local_integrated or pr_integrated):
            blockers.append(
                f"{name}: no integration proof; local Git integration failed and exact merged-PR evidence was unavailable or mismatched"
            )
            continue
        preflight.append({
            "branch": name,
            "expected_sha": expected,
            "status": "READY",
            "integration_proof": "LOCAL_GIT" if local_integrated else "GITHUB_MERGED_PR_EXACT_HEAD",
        })

    if blockers:
        raise BranchHygieneError("cleanup preflight blocked: " + "; ".join(blockers))

    results: list[dict[str, Any]] = []
    for row in preflight:
        if row["status"] == "ALREADY_ABSENT":
            results.append(row)
            continue
        name = row["branch"]
        proc = git("push", remote, "--delete", name, check=False)
        if proc.returncode != 0:
            raise BranchHygieneError(proc.stderr.strip() or f"failed to delete {name}")
        results.append({**row, "status": "DELETED"})

    return {
        "version": 1,
        "cleanup_id": manifest.get("cleanup_id"),
        "target": target,
        "remote": remote,
        "baseline_main_sha": manifest.get("baseline_main_sha"),
        "results": results,
        "summary": {
            "requested": len(results),
            "deleted": sum(row["status"] == "DELETED" for row in results),
            "already_absent": sum(row["status"] == "ALREADY_ABSENT" for row in results),
        },
        "authority": {
            "branch_deletion_authorized": True,
            "authorization_scope": "exact_manifest_only",
            "human_authority_preserved": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/branch-lifecycle.yaml"))
    parser.add_argument("--target")
    parser.add_argument("--remote", help="Classify refs/remotes/<remote>; required for approved cleanup.")
    parser.add_argument("--apply-cleanup", type=Path, help="Apply one exact Human-authorized cleanup manifest.")
    parser.add_argument(
        "--github-repository",
        help="Optional owner/repo used to verify exact merged-PR evidence when local squash integration is no longer reproducible.",
    )
    args = parser.parse_args()

    try:
        config = load_yaml(args.config)
        target = args.target or str(config.get("default_branch") or "main")
        if args.apply_cleanup:
            if not args.remote:
                raise BranchHygieneError("--apply-cleanup requires --remote")
            manifest = load_yaml(args.apply_cleanup)
            payload = apply_cleanup(
                config,
                manifest,
                target=target,
                remote=args.remote,
                github_repository=args.github_repository,
            )
        else:
            payload = build_report(config, target, args.remote)
    except (OSError, yaml.YAMLError, BranchHygieneError) as exc:
        print(f"BRANCH HYGIENE BLOCKED: {exc}")
        return 2
    print(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Deterministic branch lifecycle reporting and exact-manifest cleanup for AIPS."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
from datetime import UTC, datetime
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
    proc = subprocess.run(["git", *args], text=True, capture_output=True, check=False)
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


def _pull_request_state(branch: str, target: str, sha: str, pull_requests: list[dict[str, Any]]) -> tuple[int | None, str, str | None]:
    rows = [
        row for row in pull_requests
        if row.get("headRefName") == branch and row.get("baseRefName") == target
    ]
    exact = [row for row in rows if row.get("headRefOid") == sha]
    candidates = exact or rows
    if not candidates:
        return None, "NO_MATCHING_PR", None
    row = max(candidates, key=lambda item: str(item.get("mergedAt") or item.get("closedAt") or ""))
    if row.get("mergedAt"):
        return int(row["number"]), "MERGED" if row.get("headRefOid") == sha else "MERGED_HEAD_MOVED", row.get("mergedAt")
    if row.get("state") == "OPEN":
        return int(row["number"]), "OPEN", None
    if row.get("closedAt") or row.get("state") == "CLOSED":
        return int(row["number"]), "CLOSED_UNMERGED", None
    return int(row["number"]), "UNKNOWN", None


def build_report(
    config: dict[str, Any], target: str, remote: str | None,
    pull_requests: list[dict[str, Any]] | None = None, generated_at: str | None = None,
) -> dict[str, Any]:
    target_ref, refs = branch_refs(target, remote)
    prs = pull_requests or []
    try:
        now = datetime.fromisoformat(generated_at or datetime.now(UTC).isoformat())
    except ValueError as exc:
        raise BranchHygieneError("generated_at must be a valid ISO-8601 timestamp") from exc
    rows = []
    for name, ref in refs:
        lifecycle = classify(name, config)
        is_integrated = integrated(ref, target_ref)
        sha = git("rev-parse", ref).stdout.strip()
        committed_at = datetime.fromisoformat(git("show", "-s", "--format=%cI", ref).stdout.strip())
        age_days = max(0, (now - committed_at).days)
        merged_pr, merged_status, merged_at = _pull_request_state(name, target, sha, prs)
        action = "REVIEW_FOR_CLEANUP" if lifecycle == "EPHEMERAL" and is_integrated else "PRESERVE"
        rows.append({
            "branch": name,
            "lifecycle": lifecycle,
            "current_sha": sha,
            "merged_pr": merged_pr,
            "merged_status": merged_status,
            "merged_at": merged_at,
            "age_days": age_days,
            "integrated_into_target": is_integrated,
            "recommended_action": action,
            "recommendation_reason": "ephemeral_and_integrated" if action == "REVIEW_FOR_CLEANUP" else "persistent_unclassified_or_not_integrated",
        })
    main_sha = git("rev-parse", target_ref).stdout.strip()
    proposal_rows = [
        {
            "branch": row["branch"],
            "expected_sha": row["current_sha"],
            "merged_pr": row["merged_pr"],
            "merged_at": row["merged_at"],
            "age_days": row["age_days"],
            "integrated_into_main": row["integrated_into_target"],
            "classification": row["lifecycle"],
            "reason": row["recommendation_reason"],
        }
        for row in rows
        if row["recommended_action"] == "REVIEW_FOR_CLEANUP"
        and row["merged_status"] == "MERGED"
        and row["merged_at"]
    ]
    proposal = {
        "version": 1,
        "status": "PROPOSED",
        "target": target,
        "generated_against_main_sha": main_sha,
        "branches": proposal_rows,
        "authorization": {
            "authorized": False,
            "requires_explicit_human_approval": True,
            "scope": "proposal_only",
        },
    }
    proposal["proposal_fingerprint"] = "sha256:" + hashlib.sha256(
        json.dumps(proposal, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "version": 2,
        "target": target,
        "ref_scope": f"remote:{remote}" if remote else "local",
        "policy": "report_only",
        "generated_at": now.isoformat(),
        "generated_against_main_sha": main_sha,
        "cleanup_proposal": proposal,
        "branches": rows,
        "authority": {
            "branch_deletion_authorized": False,
            "human_authority_preserved": True,
        },
    }


def validate_proposal(
    proposal: dict[str, Any], *, current_main_sha: str | None = None,
    current_branch_shas: dict[str, str] | None = None,
) -> None:
    if proposal.get("version") != 1 or proposal.get("status") != "PROPOSED":
        raise BranchHygieneError("cleanup proposal must be version 1 PROPOSED")
    authorization = proposal.get("authorization") or {}
    if authorization.get("authorized") is not False or authorization.get("scope") != "proposal_only":
        raise BranchHygieneError("cleanup proposal must remain unauthorized and proposal-only")
    baseline = str(proposal.get("generated_against_main_sha") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", baseline):
        raise BranchHygieneError("proposal generated_against_main_sha must be a full SHA")
    if current_main_sha is not None and current_main_sha != baseline:
        raise BranchHygieneError("cleanup proposal is stale: target main moved")
    supplied = str(proposal.get("proposal_fingerprint") or "")
    payload = {key: value for key, value in proposal.items() if key != "proposal_fingerprint"}
    expected = "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if supplied != expected:
        raise BranchHygieneError("cleanup proposal fingerprint mismatch")
    seen: set[str] = set()
    for row in proposal.get("branches") or []:
        branch = str(row.get("branch") or "")
        sha = str(row.get("expected_sha") or "")
        if not branch or branch in seen or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise BranchHygieneError("proposal branch entries must be unique and bind full SHAs")
        if not row.get("integrated_into_main") or not row.get("merged_at") or not row.get("merged_pr"):
            raise BranchHygieneError(f"{branch}: proposal requires exact integration and merged PR evidence")
        if current_branch_shas is not None and current_branch_shas.get(branch) != sha:
            raise BranchHygieneError(f"{branch}: cleanup proposal is stale: branch SHA moved")
        seen.add(branch)


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
        check=False,
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
    current_baseline = git("rev-parse", target_ref).stdout.strip()
    ref_map = dict(refs)
    preflight: list[dict[str, Any]] = []
    blockers: list[str] = []

    if manifest["baseline_main_sha"] != current_baseline:
        blockers.append(
            "manifest baseline is stale: "
            f"approved {manifest['baseline_main_sha']}, current {target} is {current_baseline}"
        )

    for row in manifest["branches"]:
        name = row["branch"]
        expected = row["expected_sha"]
        ref = ref_map.get(name)
        if ref is None:
            blockers.append(f"{name}: branch is absent; manifest is consumed, replayed, or partially applied")
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
        name = row["branch"]
        proc = git("push", remote, "--delete", name, check=False)
        if proc.returncode != 0:
            deleted = [result["branch"] for result in results]
            raise BranchHygieneError(
                "cleanup stopped at a deletion failure; verify remote refs and create a newly reviewed "
                "manifest before retrying; branches deleted before failure: "
                f"{deleted or 'none'}; {proc.stderr.strip() or f'failed to delete {name}'}"
            )
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
    parser.add_argument("--pull-requests", type=Path, help="Read-only JSON from `gh pr list` for the branch proposal report.")
    parser.add_argument("--generated-at", help="Fixed ISO-8601 report time for deterministic replay.")
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
            prs = json.loads(args.pull_requests.read_text(encoding="utf-8")) if args.pull_requests else []
            if not isinstance(prs, list) or any(not isinstance(row, dict) for row in prs):
                raise BranchHygieneError("pull request report input must be a JSON list of mappings")
            payload = build_report(config, target, args.remote, prs, args.generated_at)
    except (OSError, yaml.YAMLError, BranchHygieneError) as exc:
        print(f"BRANCH HYGIENE BLOCKED: {exc}")
        return 2
    print(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

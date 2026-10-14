"""Shared safe publication diagnostic categories and read-only GitHub observations."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


def remote_failure(stderr: str = "", returncode: int | None = None) -> str:
    """Map host failures to stable categories without returning provider text."""
    text = stderr.lower()
    if "http 429" in text or "rate limit" in text or "secondary rate" in text:
        return "RATE_LIMITED"
    if any(marker in text for marker in ("http 500", "http 502", "http 503", "http 504", "server error")):
        return "GITHUB_SERVER_ERROR"
    if "http 403" in text or "forbidden" in text or "resource not accessible" in text:
        return "PERMISSION"
    if returncode == 4 or "http 401" in text or "authentication" in text or "not logged" in text:
        return "AUTHENTICATION"
    if "timed out" in text or "timeout" in text or "could not resolve" in text:
        return "NETWORK"
    if "http 404" in text or "not found" in text:
        return "MISSING"
    return "API_UNAVAILABLE"


def classify_required_checks(payload: Any = None, *, returncode: int = 0,
                              stderr: str = "",
                              required_policy: list[str] | None = None) -> dict[str, Any]:
    """Classify required checks without treating an empty CLI result as pending.

    Only independently observed branch protection/ruleset evidence can establish
    UNCONFIGURED. Missing policy visibility is never proof of no required checks.
    """
    if returncode == 1 and "no required checks reported" in stderr.casefold():
        if required_policy is None:
            return {"status": "UNAVAILABLE", "reason_code": "REQUIRED_CHECKS_POLICY_UNVERIFIED",
                    "checks": []}
        if not required_policy:
            return {"status": "UNCONFIGURED", "reason_code": "REQUIRED_CHECKS_UNCONFIGURED",
                    "checks": []}
        return {"status": "MISSING", "reason_code": "REQUIRED_CHECKS_MISSING",
                "checks": sorted(required_policy)}
    if returncode not in {0, 8}:
        reason = remote_failure(stderr, returncode)
        return {"status": "UNAVAILABLE", "reason_code": "REQUIRED_CHECKS_" + reason,
                "checks": []}
    if not isinstance(payload, list):
        return {"status": "UNAVAILABLE", "reason_code": "REQUIRED_CHECKS_INVALID", "checks": []}
    if not payload:
        if required_policy is None:
            return {"status": "UNAVAILABLE", "reason_code": "REQUIRED_CHECKS_POLICY_UNVERIFIED",
                    "checks": []}
        if required_policy:
            return {"status": "MISSING", "reason_code": "REQUIRED_CHECKS_MISSING",
                    "checks": sorted(required_policy)}
        return {"status": "UNCONFIGURED", "reason_code": "REQUIRED_CHECKS_UNCONFIGURED",
                "checks": []}
    buckets = [item.get("bucket") if isinstance(item, dict) else None for item in payload]
    names = [item.get("name") for item in payload if isinstance(item, dict)]
    if any(not isinstance(item, dict) or item.get("bucket") not in
           {"pass", "skipping", "fail", "pending", "cancel"} or
           not isinstance(item.get("name"), str) or not item["name"] for item in payload):
        return {"status": "UNAVAILABLE", "reason_code": "REQUIRED_CHECKS_INVALID", "checks": []}
    if "fail" in buckets:
        status, code = "FAIL", "REQUIRED_CHECKS_FAILING"
    elif "pending" in buckets:
        status, code = "PENDING", "REQUIRED_CHECKS_PENDING"
    elif "cancel" in buckets:
        status, code = "CANCELLED", "REQUIRED_CHECKS_CANCELLED"
    elif "skipping" in buckets:
        # Skipping is not a successful Required Check for publication authority.
        status, code = "MISSING", "REQUIRED_CHECKS_MISSING"
    else:
        status, code = "PASS", None
    if returncode == 8 and status == "PASS":
        return {"status": "UNAVAILABLE", "reason_code": "REQUIRED_CHECKS_INVALID", "checks": []}
    result = {"status": status, "reason_code": code, "checks": sorted(names)}
    if "skipping" in buckets:
        result.update(provider_status="SKIPPING", github_required_check_outcome="SUCCESSFUL")
    return result


def required_checks_policy(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Resolve Required Checks from the same complete, read-only policy snapshot."""
    sources = snapshot.get("sources") if isinstance(snapshot.get("sources"), dict) else {}
    required: set[str] = set()
    protection = snapshot.get("branch_protection") or {}
    if isinstance(protection, dict):
        required.update(item for item in protection.get("required_checks", [])
                        if isinstance(item, str) and item)
    rule_collections = []
    effective = snapshot.get("effective_rules")
    if isinstance(effective, list):
        rule_collections.append(effective)
    rulesets = snapshot.get("rulesets")
    if isinstance(rulesets, list):
        rule_collections.extend(item.get("rules", []) for item in rulesets if isinstance(item, dict))
    for rules in rule_collections:
        for rule in rules if isinstance(rules, list) else []:
            if not isinstance(rule, dict) or rule.get("type") != "required_status_checks":
                continue
            parameters = rule.get("parameters") if isinstance(rule.get("parameters"), dict) else {}
            for check in parameters.get("required_status_checks", []):
                if isinstance(check, dict) and isinstance(check.get("context"), str) and check["context"]:
                    required.add(check["context"])
    if snapshot.get("source_complete") is not True:
        errors = [source.get("error_class") for source in sources.values()
                  if isinstance(source, dict) and source.get("error_class")]
        if "PERMISSION" in errors:
            return {"status": "UNKNOWN_PERMISSION", "reason_code": "REQUIRED_CHECKS_POLICY_PERMISSION",
                    "category": "PERMISSION", "retryable": False, "checks": sorted(required),
                    "sources": sources}
        transient = next((name for name in ("NETWORK", "RATE_LIMITED", "GITHUB_SERVER_ERROR")
                          if name in errors), None)
        if transient:
            return {"status": "UNAVAILABLE", "reason_code": "REQUIRED_CHECKS_POLICY_" + transient,
                    "category": transient, "retryable": True, "checks": sorted(required),
                    "sources": sources}
        return {"status": "UNAVAILABLE", "reason_code": "REQUIRED_CHECKS_POLICY_UNVERIFIED",
                "category": "UNAVAILABLE", "retryable": False, "checks": sorted(required),
                "sources": sources}
    if not required:
        return {"status": "UNCONFIGURED", "reason_code": "REQUIRED_CHECKS_UNCONFIGURED",
                "category": "POLICY", "retryable": False, "checks": [], "sources": sources}
    return {"status": "CONFIGURED", "reason_code": None, "category": "POLICY",
            "retryable": False, "checks": sorted(required), "sources": sources}


def doctor(root: Path, *, pr_number: int | None = None, branch: str | None = None,
           worktree_details: bool = False) -> dict[str, Any]:
    """Read-only repository, auth, policy, PR and required-check diagnosis."""
    import publication_authority as authority
    from repository_governance_snapshot import build_snapshot, repository_slug

    result: dict[str, Any] = {"version": 2, "status": "BLOCKED", "authorized": False,
                              "read_only": True, "api_write_performed": False, "repository": None,
                              "authentication": "UNKNOWN", "merge_methods": [],
                              "required_checks": {"status": "UNKNOWN", "checks": []},
                              "pr": None, "blockers": [], "diagnostics": [], "next_steps": [], "phases": []}
    def finish() -> dict[str, Any]:
        result["next_steps"] = [item["next_step"] for item in result["diagnostics"]
                                if isinstance(item, dict) and isinstance(item.get("next_step"), str)]
        return result
    try:
        root = root.expanduser().resolve(strict=True)
        if Path(authority.git(root, "rev-parse", "--show-toplevel")).resolve() != root:
            raise authority.PublicationError("repository root required", "CWD_MISMATCH")
        try:
            result["candidate_sha"] = authority.git(root, "rev-parse", "HEAD^{commit}")
        except authority.PublicationError:
            result["candidate_sha"] = None
        dirty = authority.worktree_dirty_details(root)
        result["worktree"] = {"branch": authority.git(root, "branch", "--show-current") or None,
                              "status": dirty["status"]}
        if worktree_details:
            result["worktree_details"] = dirty
        result["phases"].append({"phase": "worktree_validation", "status": dirty["status"],
                                 "blocking": dirty["status"] == "DIRTY"})
        if dirty["status"] == "DIRTY":
            result["blockers"].append("worktree_dirty")
            item = authority.PublicationError("publication requires a clean worktree", "WORKTREE_DIRTY",
                context={"worktree": root, "candidate_sha": result.get("candidate_sha")},
                phase="worktree_validation").diagnostic()
            if not worktree_details:
                item.pop("worktree_details", None)
            result["diagnostics"].append(item)
        remote = authority.git(root, "remote", "get-url", "origin")
        repo = repository_slug(remote)
        if not repo or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise authority.PublicationError("GitHub origin required", "REMOTE_OBSERVATION_FAILED")
        result["repository"] = repo
        result["phases"].append({"phase": "repository_identity", "status": "PASS", "repository": repo})
        gh = shutil.which("gh")
        if not gh:
            result["blockers"].append("gh_unavailable")
            result["diagnostics"].append({"reason_code": "GH_UNAVAILABLE", "phase": "authentication",
                "category": "LOCAL_TOOL", "detail": "GitHub CLI is unavailable.",
                "next_step": "Install or expose GitHub CLI, then rerun `aips publish doctor`."})
            return finish()
        auth_check = subprocess.run([gh, "auth", "status", "--hostname", "github.com"], cwd=root,
                                    capture_output=True, text=True, timeout=15, check=False)
        result["authentication"] = "AVAILABLE" if auth_check.returncode == 0 else "UNAVAILABLE"
        result["phases"].append({"phase": "authentication", "status": result["authentication"]})
        if auth_check.returncode:
            result["blockers"].append("github_auth_unavailable")
            result["diagnostics"].append({"reason_code": "GITHUB_AUTH_UNAVAILABLE", "phase": "authentication",
                "category": remote_failure(auth_check.stderr, auth_check.returncode),
                "detail": "GitHub authentication could not be confirmed.",
                "next_step": "Run `gh auth status` locally and resolve access without sharing credentials."})
            return finish()
        api = subprocess.run([gh, "api", "repos/" + repo], cwd=root, capture_output=True,
                             text=True, timeout=20, check=False)
        try:
            metadata = json.loads(api.stdout) if api.returncode == 0 else None
        except json.JSONDecodeError:
            metadata = None
        if not isinstance(metadata, dict):
            reason = remote_failure(api.stderr, api.returncode)
            result["blockers"].append("repository_metadata_unavailable")
            result["diagnostics"].append({"reason_code": "REPOSITORY_METADATA_" + reason,
                "phase": "repository", "category": reason,
                "detail": "Repository settings could not be read.",
                "next_step": "Check repository access and GitHub API availability, then rerun the doctor."})
            return finish()
        result["merge_methods"] = sorted(name for name, key in
            (("merge", "allow_merge_commit"), ("squash", "allow_squash_merge"),
             ("rebase", "allow_rebase_merge")) if metadata.get(key) is True)
        candidate_branch = result["worktree"].get("branch")
        policy_branch = branch or authority._remote_default_branch(root, remote)
        result["candidate_branch"] = candidate_branch
        result["policy_branch"] = policy_branch
        from repository_governance_snapshot import query_github_api
        def read_api(endpoint: str) -> dict[str, Any]:
            try:
                return query_github_api(root, endpoint)
            except subprocess.TimeoutExpired:
                return {"returncode": 1, "http_status": None, "payload": None,
                        "endpoint": endpoint, "error_class": "NETWORK", "error_message": None}
        snapshot = build_snapshot(repo, policy_branch, read_api)
        policy = snapshot.get("branch_protection") or {}
        policy_observation = required_checks_policy(snapshot)
        required = policy_observation["checks"] if policy_observation["status"] in {"CONFIGURED", "UNCONFIGURED"} else None
        ruleset_required = sorted(set(required or []) - set(policy.get("required_checks") or [])) if required else []
        result["governance"] = snapshot
        result["phases"].append({"phase": "protection_policy_evidence",
                                 "status": snapshot.get("protection_state", "UNKNOWN"),
                                 "evidence_level": snapshot.get("evidence_level"),
                                 "blocking": not snapshot.get("source_complete")})
        result["policy"] = {"status": "AVAILABLE" if snapshot.get("source_complete") else "UNAVAILABLE",
                             "branch": policy_branch, "required_checks": required or [],
                             "ruleset_required_checks": ruleset_required,
                             "required_check_state": policy_observation["status"],
                             "required_check_reason_code": policy_observation["reason_code"],
                             "source_complete": snapshot.get("source_complete") is True,
                             "api_write_performed": False}
        if policy_observation["status"] in {"UNKNOWN_PERMISSION", "UNAVAILABLE"}:
            result["blockers"].append("protection_evidence_unavailable")
            item = authority.PublicationError("branch protection evidence unavailable",
                policy_observation["reason_code"], phase="protection_policy_evidence").diagnostic()
            item["category"] = policy_observation["category"]
            item["retryable"] = policy_observation["retryable"]
            item["recovery_mode"] = "SAFE_OBSERVATION" if policy_observation["retryable"] else "MANUAL_REVIEW"
            item["api_sources"] = {name: {key: source.get(key) for key in
                ("status", "endpoint", "http_status", "error_class")}
                for name, source in policy_observation["sources"].items() if isinstance(source, dict)}
            result["diagnostics"].append(item)
        elif policy_observation["status"] == "UNCONFIGURED":
            result["blockers"].append("required_checks_unconfigured")
            result["diagnostics"].append({"reason_code": "REQUIRED_CHECKS_UNCONFIGURED", "phase": "policy",
                "category": "POLICY", "detail": "No branch-protection Required Checks were observed.",
                "next_step": "Ask a repository administrator to review Required Checks configuration."})
        if not result["merge_methods"]:
            result["blockers"].append("merge_methods_unavailable")
        if pr_number is None:
            current_branch = authority.git(root, "branch", "--show-current")
            base_branch = authority._remote_default_branch(root, remote)
            from publication_planning import _prs
            candidates = _prs(root, repo, current_branch, base_branch) if current_branch else []
            open_prs = [item for item in candidates if item.get("state") == "OPEN"]
            if len(open_prs) == 1:
                pr_number = open_prs[0]["number"]
            elif len(open_prs) > 1:
                result["blockers"].append("pr_state_ambiguous")
                result["diagnostics"].append({"reason_code": "PR_STATE_AMBIGUOUS", "phase": "pr",
                    "category": "AMBIGUOUS", "detail": "Multiple open PRs match this branch and base.",
                    "next_step": "Inspect the matching PRs and rerun the doctor with an explicit `--pr`."})
        if pr_number is not None:
            view = subprocess.run([gh, "pr", "view", str(pr_number), "--repo", repo, "--json",
                "number,state,isDraft,headRefOid,headRefName,baseRefName,baseRefOid,mergeable"], cwd=root,
                capture_output=True, text=True, timeout=20, check=False)
            try:
                pr = json.loads(view.stdout) if view.returncode == 0 else None
            except json.JSONDecodeError:
                pr = None
            if (not isinstance(pr, dict) or type(pr.get("number")) is not int or
                    pr.get("state") not in {"OPEN", "CLOSED", "MERGED"} or
                    type(pr.get("isDraft")) is not bool or
                    not isinstance(pr.get("headRefName"), str) or not isinstance(pr.get("baseRefName"), str) or
                    not re.fullmatch(r"[0-9a-f]{40,64}", str(pr.get("headRefOid"))) or
                    not re.fullmatch(r"[0-9a-f]{40,64}", str(pr.get("baseRefOid")))):
                result["blockers"].append("pr_observation_unavailable")
                result["pr"] = {"status": "UNAVAILABLE"}
            else:
                pr_blockers = []
                head_branch = pr.get("headRefName")
                base_branch = pr.get("baseRefName")
                try:
                    authority._ref(root, "refs/heads/" + str(head_branch))
                    authority._ref(root, "refs/heads/" + str(base_branch))
                    live_head = authority._tip(root, remote, "refs/heads/" + str(head_branch))
                    live_base = authority._tip(root, remote, "refs/heads/" + str(base_branch))
                except authority.PublicationError:
                    live_head = live_base = None
                if live_head is None or live_base is None:
                    pr_blockers.append(("PR_STATE_AMBIGUOUS", "PR branch tips could not be confirmed."))
                else:
                    if live_head != pr["headRefOid"]:
                        pr_blockers.append(("PR_HEAD_STALE", "The PR head differs from its current remote branch."))
                    if live_base != pr.get("baseRefOid"):
                        pr_blockers.append(("PR_BASE_STALE", "The PR base differs from the current remote target."))
                if pr.get("state") != "OPEN":
                    pr_blockers.append(("PR_STATE_AMBIGUOUS", "The selected PR is not open."))
                if pr.get("isDraft") is True:
                    pr_blockers.append(("PR_STATE_AMBIGUOUS", "The selected PR is still a draft."))
                if pr.get("mergeable") != "MERGEABLE":
                    pr_blockers.append(("PR_STATE_AMBIGUOUS", "GitHub has not confirmed that the selected PR is mergeable."))
                checks_proc = subprocess.run([gh, "pr", "checks", str(pr_number), "--repo", repo,
                    "--required", "--json", "bucket,name"], cwd=root, capture_output=True,
                    text=True, timeout=30, check=False)
                try:
                    check_payload = json.loads(checks_proc.stdout) if checks_proc.returncode in {0, 8} else None
                except json.JSONDecodeError:
                    check_payload = None
                checks = classify_required_checks(check_payload, returncode=checks_proc.returncode,
                                                  stderr=checks_proc.stderr, required_policy=required)
                if any(code in {"PR_HEAD_STALE", "PR_BASE_STALE"} for code, _ in pr_blockers):
                    checks = {**checks, "status": "STALE", "reason_code": "CANDIDATE_CHANGED"}
                result["required_checks"] = checks
                result["phases"].append({"phase": "required_checks", "status": checks["status"],
                                         "blocking": checks["status"] != "PASS"})
                result["phases"].append({"phase": "pr_state_observation",
                                         "status": "OBSERVED" if not pr_blockers else "BLOCKED",
                                         "blocking": bool(pr_blockers)})
                result["pr"] = {"status": pr.get("state"), "freshness": "STALE" if any(
                    code in {"PR_HEAD_STALE", "PR_BASE_STALE"} for code, _ in pr_blockers) else "CURRENT",
                    "number": pr["number"],
                    "draft": pr.get("isDraft"), "head_sha": pr["headRefOid"],
                    "head_branch": pr.get("headRefName"), "base_branch": pr.get("baseRefName"),
                    "base_sha": pr.get("baseRefOid"), "mergeable": pr.get("mergeable")}
                for code, detail in pr_blockers:
                    result["blockers"].append(code.lower())
                    result["diagnostics"].append({"reason_code": code, "phase": "pr",
                        "category": "STALE" if "STALE" in code else "BLOCKED", "detail": detail,
                        "next_step": "Refresh PR and branch observations, resolve the reported state, then rerun the doctor."})
                if checks["status"] != "PASS":
                    result["blockers"].append("required_checks_" + checks["status"].lower())
                    result["diagnostics"].append({"reason_code": checks["reason_code"] or "REQUIRED_CHECKS_BLOCKED",
                        "phase": "checks", "category": checks["status"],
                        "detail": "Required Checks are not confirmed passing.",
                        "next_step": "Resolve the reported check state and rerun `aips publish doctor`."})
        result["status"] = "READY" if not result["blockers"] else "BLOCKED"
        return finish()
    except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired):
        result["blockers"].append("repository_observation_unavailable")
        result["diagnostics"].append({"reason_code": "REMOTE_OBSERVATION_FAILED", "phase": "repository",
            "category": "API_UNAVAILABLE", "detail": "Required repository evidence is unavailable.",
            "next_step": "Check local repository configuration and GitHub access, then rerun the doctor."})
        return finish()

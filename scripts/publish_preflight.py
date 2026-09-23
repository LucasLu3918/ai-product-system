#!/usr/bin/env python3
"""Resolve and validate the same exact publication candidate locally and in CI."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

try:
    from browser_runtime import discover_browser, probe_browser
except ModuleNotFoundError:  # imported as a repository module by lifecycle evidence
    from scripts.browser_runtime import discover_browser, probe_browser

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_MATRIX = ROOT / ".aips/review/CORE_CHANGE_TEST_MATRIX.yaml"


class PreflightError(RuntimeError):
    pass


def git(*args: str, check: bool = True) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and proc.returncode:
        raise PreflightError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout.strip()


def resolve_commit(ref: str) -> str:
    return git("rev-parse", f"{ref}^{{commit}}")


def git_success(*args: str) -> bool:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True).returncode == 0


def changed_files(base: str, head: str) -> list[str]:
    out = git("diff", "--name-only", f"{base}...{head}")
    return sorted(item for item in out.splitlines() if item)


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    import hashlib

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def matches(paths: list[str], patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for path in paths for pattern in patterns)


def resolve_change_class(explicit: str, labels: str) -> tuple[str, str | None]:
    label_set = {item.strip() for item in labels.split(",") if item.strip()}
    label_class = "core" if "aips:core-change" in label_set else "large" if "aips:large-change" in label_set else "standard"
    if explicit == "auto":
        return label_class, None
    warning = None if explicit == label_class or not labels else f"explicit {explicit} differs from labels ({label_class})"
    return explicit, warning


def matrix_required(profile: dict[str, Any], files: list[str], change_class: str) -> bool:
    if change_class in (profile.get("matrix_required_change_classes") or []):
        return True
    return matches(files, [str(item) for item in profile.get("matrix_required_paths") or []])


def documentation_impact(files: list[str]) -> dict[str, Any]:
    sync = yaml.safe_load((ROOT / "config/documentation-sync.yaml").read_text(encoding="utf-8")) or {}
    placement = yaml.safe_load((ROOT / "config/documentation-placement.yaml").read_text(encoding="utf-8")) or {}
    closure = set(files)
    triggered: dict[str, dict[str, Any]] = {}
    placement_hits = []
    for rule in placement.get("placement_rules") or []:
        patterns = [str(item) for item in rule.get("triggers") or []]
        if not matches(files, patterns):
            continue
        placements = rule.get("placements") or {}
        placement_hits.append({"id": rule.get("id"), "placements": placements})
        closure.update(str(path) for path in placements)
    changed = True
    while changed:
        changed = False
        current = sorted(closure)
        technology = sync.get("technology_guide") or {}
        if matches(current, [str(item) for item in technology.get("triggers") or []]):
            target = str(technology.get("path") or "")
            if target and target not in closure:
                closure.add(target)
                changed = True
        for rule in sync.get("rules") or []:
            patterns = [str(item) for item in rule.get("triggers") or []]
            if not matches(current, patterns):
                continue
            required = [str(item) for item in (rule.get("human_docs") or []) + (rule.get("agent_docs") or [])]
            triggered.setdefault(str(rule.get("id")), {"required": required})
            before = len(closure)
            closure.update(required)
            changed = changed or len(closure) != before
    required = sorted(closure - set(files))
    return {
        "changed_files": files,
        "triggered_rules": triggered,
        "required_additions": required,
        "complete": not required,
        "placement_rules": placement_hits,
    }


def environment_status() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        probe.close()
        localhost = "READY"
    except OSError as exc:
        localhost = "BLOCKED"
        blockers.append(f"localhost_bind:{exc.__class__.__name__}")
    selection = discover_browser()
    browser_probe = probe_browser(selection.get("path"), provider=str(selection["provider"]))
    if browser_probe["status"] != "READY":
        blockers.append(f"browser:{browser_probe['status']}")
    return {
        "status": "READY" if not blockers else "ENVIRONMENT_BLOCKED",
        "localhost": localhost,
        "browser": browser_probe,
        "blockers": blockers,
    }


def remote_policy(branch: str, offline: bool) -> dict[str, Any]:
    if offline:
        return {"status": "NOT_CHECKED", "reason": "offline"}
    gh = shutil.which("gh")
    remote = git("remote", "get-url", "origin", check=False)
    if not gh or "github.com" not in remote:
        return {"status": "UNAVAILABLE", "reason": "GitHub CLI or GitHub origin unavailable"}
    path = remote.removeprefix("git@github.com:").removeprefix("https://github.com/").removesuffix(".git")
    proc = subprocess.run([gh, "api", f"repos/{path}/branches/{branch}/protection"], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode == 0:
        return {"status": "PROTECTED", "publication_route": "pull_request"}
    if "Branch not protected" in proc.stderr or "404" in proc.stderr:
        return {"status": "UNPROTECTED", "publication_route": "direct_or_pull_request"}
    return {"status": "UNAVAILABLE", "reason": proc.stderr.strip() or "protection query failed"}


def build_plan(args: argparse.Namespace) -> dict[str, Any]:
    base = resolve_commit(args.base)
    head = resolve_commit(args.head)
    files = changed_files(base, head)
    profile = yaml.safe_load(Path(args.profile).read_text(encoding="utf-8")) or {}
    change_class, warning = resolve_change_class(args.change_class, args.labels)
    required = matrix_required(profile, files, change_class)
    matrix = Path(args.matrix).resolve() if args.matrix else CANONICAL_MATRIX
    matrix_ok = matrix.is_file() and matrix == CANONICAL_MATRIX.resolve()
    blockers: list[str] = []
    if required and not matrix_ok:
        blockers.append("canonical Core Change Test Matrix is required")
    docs = documentation_impact(files)
    if not docs["complete"]:
        blockers.append("documentation impact is incomplete")
    if git("status", "--porcelain"):
        blockers.append("working tree is dirty; commit the exact candidate before publication preflight")
    if resolve_commit("HEAD") != head:
        blockers.append("current checkout does not match the exact candidate head")
    if args.base_tip and resolve_commit(args.base_tip) != base:
        blockers.append("candidate base is stale relative to base-tip")
    matrix_binding: dict[str, Any] = {}
    if required and matrix_ok:
        matrix_binding = yaml.safe_load(matrix.read_text(encoding="utf-8")) or {}
        binding = matrix_binding.get("candidate") or {}
        actual_hash = canonical_hash(files)
        if binding.get("base_sha") != base:
            blockers.append("Core Change Test Matrix base_sha does not match candidate")
        if binding.get("changed_files_hash") != actual_hash:
            blockers.append("Core Change Test Matrix changed_files_hash does not match candidate")
    return {
        "version": 1,
        "candidate": {"base": base, "head": head, "changed_files": files},
        "change_class": change_class,
        "change_class_warning": warning,
        "matrix": {
            "required": required,
            "path": str(matrix),
            "canonical": matrix_ok,
            "changed_files_hash": canonical_hash(files),
        },
        "documentation": docs,
        "environment": environment_status(),
        "remote": remote_policy(args.branch, args.offline),
        "blockers": blockers,
        "status": "READY" if not blockers else "BLOCKED",
    }


def post_merge(args: argparse.Namespace) -> dict[str, Any]:
    remote_ref = f"{args.remote}/{args.branch}"
    if args.fetch:
        proc = subprocess.run(["git", "fetch", args.remote, args.branch], cwd=ROOT, capture_output=True, text=True)
        if proc.returncode:
            raise PreflightError(proc.stderr.strip() or "git fetch failed")
    remote_sha = resolve_commit(remote_ref)
    local_sha = resolve_commit("HEAD")
    current_branch = git("branch", "--show-current")
    local_tree = git("rev-parse", "HEAD^{tree}")
    remote_tree = git("rev-parse", f"{remote_ref}^{{tree}}")
    clean = not bool(git("status", "--porcelain"))
    result: dict[str, Any] = {
        "version": 1,
        "branch": current_branch,
        "target_branch": args.branch,
        "local_sha": local_sha,
        "remote_sha": remote_sha,
        "tree_equivalent": local_tree == remote_tree,
        "clean": clean,
        "action": "NONE",
        "status": "CURRENT" if local_sha == remote_sha else "RECONCILIATION_REQUIRED",
    }
    if not args.apply or local_sha == remote_sha:
        return result
    if current_branch != args.branch:
        result["status"] = "BLOCKED"
        result["reason"] = f"checkout {args.branch} before applying reconciliation"
        return result
    if not clean:
        result["status"] = "BLOCKED"
        result["reason"] = "working tree is dirty"
        return result
    if local_tree != remote_tree:
        result["status"] = "BLOCKED"
        result["reason"] = "local and remote trees differ; automatic reset is unsafe"
        return result
    backup = args.backup_branch or f"aips/pre-reconcile-{local_sha[:12]}"
    if git_success("show-ref", "--verify", "--quiet", f"refs/heads/{backup}"):
        result["status"] = "BLOCKED"
        result["reason"] = f"backup branch already exists: {backup}"
        return result
    subprocess.run(["git", "branch", backup, local_sha], cwd=ROOT, check=True)
    subprocess.run(["git", "reset", "--hard", remote_ref], cwd=ROOT, check=True)
    result.update({"status": "RECONCILED", "action": "RESET_EQUIVALENT_TREE", "backup_branch": backup})
    if args.refresh_intelligence:
        refresh_result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/project_intelligence.py"), "refresh", "--project", str(ROOT), "--format", "json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if refresh_result.returncode:
            result["intelligence_refresh"] = {"status": "FAILED", "error": refresh_result.stderr.strip() or refresh_result.stdout.strip()}
        else:
            result["intelligence_refresh"] = json.loads(refresh_result.stdout)
    return result


def emit(value: dict[str, Any], fmt: str) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2) if fmt == "json" else yaml.safe_dump(value, sort_keys=False, allow_unicode=True).rstrip())


def run_candidate(args: argparse.Namespace) -> int:
    plan = build_plan(args)
    if plan["environment"]["status"] != "READY":
        plan["blockers"].extend(f"environment:{item}" for item in plan["environment"]["blockers"])
        plan["status"] = "ENVIRONMENT_BLOCKED"
    if plan["status"] != "READY":
        emit(plan, args.format)
        return 2 if plan["status"] == "ENVIRONMENT_BLOCKED" else 1
    env = dict(os.environ)
    env["AIPS_DOCS_DIFF_BASE"] = plan["candidate"]["base"]
    fast = subprocess.run(
        [sys.executable, str(ROOT / "scripts/repository_preflight.py"), "--base", plan["candidate"]["base"], "--head", plan["candidate"]["head"]],
        cwd=ROOT,
        env=env,
    )
    if fast.returncode:
        return fast.returncode
    command = [
        sys.executable,
        str(ROOT / "scripts/integration_gate.py"),
        "--profile", args.profile,
        "--base", plan["candidate"]["base"],
        "--head", plan["candidate"]["head"],
        "--change-class", plan["change_class"],
        "--output", args.output,
    ]
    if args.base_tip:
        command.extend(["--base-tip", args.base_tip])
    if plan["matrix"]["required"] or Path(plan["matrix"]["path"]).is_file():
        command.extend(["--matrix", plan["matrix"]["path"]])
    return subprocess.run(command, cwd=ROOT, env=env).returncode


def common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--base-tip")
    parser.add_argument("--profile", default=str(ROOT / "config/integration-gate.yaml"))
    parser.add_argument("--change-class", choices=("auto", "standard", "large", "core"), default="auto")
    parser.add_argument("--labels", default="")
    parser.add_argument("--matrix")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")


def main() -> int:
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command", required=True)
    plan = subs.add_parser("plan")
    common(plan)
    run = subs.add_parser("run")
    common(run)
    run.add_argument("--output", required=True)
    docs = subs.add_parser("docs-impact")
    docs.add_argument("--base", required=True)
    docs.add_argument("--head", default="HEAD")
    docs.add_argument("--format", choices=("yaml", "json"), default="yaml")
    env = subs.add_parser("environment")
    env.add_argument("--format", choices=("yaml", "json"), default="yaml")
    post = subs.add_parser("post-merge")
    post.add_argument("--remote", default="origin")
    post.add_argument("--branch", default="main")
    post.add_argument("--fetch", action="store_true")
    post.add_argument("--apply", action="store_true")
    post.add_argument("--backup-branch")
    post.add_argument("--refresh-intelligence", action="store_true")
    post.add_argument("--format", choices=("yaml", "json"), default="yaml")
    args = parser.parse_args()
    try:
        if args.command == "docs-impact":
            emit(documentation_impact(changed_files(resolve_commit(args.base), resolve_commit(args.head))), args.format)
            return 0
        if args.command == "environment":
            result = environment_status()
            emit(result, args.format)
            return 0 if result["status"] == "READY" else 2
        if args.command == "post-merge":
            result = post_merge(args)
            emit(result, args.format)
            return 0 if result["status"] in {"CURRENT", "RECONCILED"} else 1
        if args.command == "plan":
            result = build_plan(args)
            emit(result, args.format)
            return 0 if result["status"] == "READY" else 1
        return run_candidate(args)
    except (OSError, ValueError, PreflightError) as exc:
        print(f"PUBLISH PREFLIGHT ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

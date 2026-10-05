"""Post-merge reconciliation behind the publication preflight facade."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


class PreflightError(RuntimeError):
    """A publication preflight input or repository invariant is invalid."""


def sync_installed(
    root: Path, args: argparse.Namespace, expected: str
) -> dict[str, Any]:
    configured = os.environ.get("AIPS_INSTALLED_SYSTEM_DIR")
    if not configured:
        return {"status": "BLOCKED", "reason_code": "INSTALLATION_NOT_REGISTERED"}
    installed = Path(configured).resolve()

    def read(path: Path, *parts: str) -> str:
        return subprocess.run(
            ["git", *parts], cwd=path, capture_output=True, text=True, check=True
        ).stdout.strip()

    try:
        if Path(read(installed, "rev-parse", "--show-toplevel")).resolve() != installed:
            raise ValueError("installation is not a Git root")
        if read(installed, "remote", "get-url", args.remote) != read(
            root, "remote", "get-url", args.remote
        ):
            return {"status": "BLOCKED", "reason_code": "INSTALLATION_REMOTE_MISMATCH"}
        if read(installed, "branch", "--show-current") != args.branch or read(
            installed, "status", "--porcelain"
        ):
            return {"status": "BLOCKED", "reason_code": "INSTALLATION_NOT_CLEAN_MAIN"}
        if args.fetch:
            read(installed, "fetch", args.remote, args.branch)
        if (
            read(installed, "rev-parse", f"{args.remote}/{args.branch}^{{commit}}")
            != expected
        ):
            return {"status": "BLOCKED", "reason_code": "INSTALLATION_REMOTE_STALE"}
        head = read(installed, "rev-parse", "HEAD")
        if subprocess.run(
            ["git", "merge-base", "--is-ancestor", head, expected],
            cwd=installed,
            capture_output=True,
            check=False,
        ).returncode:
            return {"status": "BLOCKED", "reason_code": "INSTALLATION_DIVERGED"}
        if head != expected and args.apply:
            read(installed, "merge", "--ff-only", f"{args.remote}/{args.branch}")
        actual = read(installed, "rev-parse", "HEAD")
        return {
            "status": "CURRENT" if actual == expected else "RECONCILIATION_REQUIRED",
            "head_sha": actual,
            "expected_sha": expected,
            "action": "FAST_FORWARD" if args.apply and head != actual else "NONE",
        }
    except (OSError, subprocess.CalledProcessError, ValueError):
        return {
            "status": "BLOCKED",
            "reason_code": "INSTALLATION_SYNC_FAILED",
            "next_step": "Inspect the registered installation and its Git access; no raw Git diagnostics are emitted.",
        }


def post_merge(
    args: argparse.Namespace,
    *,
    root_default: Path = ROOT,
    installed_sync=sync_installed,
) -> dict[str, Any]:
    root = (getattr(args, "project_root", None) or root_default).resolve()
    if not (root / "scripts/publish_preflight.py").is_file():
        raise PreflightError(f"not an AIPS repository: {root}")

    def git_at(*parts: str, check: bool = True) -> str:
        proc = subprocess.run(
            ["git", *parts], cwd=root, capture_output=True, text=True, check=check
        )
        if check and proc.returncode:
            raise PreflightError(proc.stderr.strip() or f"git {' '.join(parts)} failed")
        return proc.stdout.strip()

    def git_success_at(*parts: str) -> bool:
        return (
            subprocess.run(
                ["git", *parts], cwd=root, capture_output=True, check=False
            ).returncode
            == 0
        )

    if Path(git_at("rev-parse", "--show-toplevel")).resolve() != root:
        raise PreflightError(f"project root is not the Git top level: {root}")
    remote_ref = f"{args.remote}/{args.branch}"
    if args.fetch:
        proc = subprocess.run(
            ["git", "fetch", args.remote, args.branch],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode:
            raise PreflightError(proc.stderr.strip() or "git fetch failed")
    remote_sha = git_at("rev-parse", f"{remote_ref}^{{commit}}")
    local_sha = git_at("rev-parse", "HEAD^{commit}")
    current_branch = git_at("branch", "--show-current")
    local_tree = git_at("rev-parse", "HEAD^{tree}")
    remote_tree = git_at("rev-parse", f"{remote_ref}^{{tree}}")
    clean = not bool(git_at("status", "--porcelain"))
    fast_forward_possible = git_success_at(
        "merge-base", "--is-ancestor", local_sha, remote_sha
    )
    result: dict[str, Any] = {
        "version": 1,
        "branch": current_branch,
        "target_branch": args.branch,
        "local_sha": local_sha,
        "remote_sha": remote_sha,
        "tree_equivalent": local_tree == remote_tree,
        "fast_forward_possible": fast_forward_possible,
        "clean": clean,
        "action": "NONE",
        "status": "CURRENT" if local_sha == remote_sha else "RECONCILIATION_REQUIRED",
    }

    def finish() -> dict[str, Any]:
        if getattr(args, "sync_installed", False):
            if (
                result["status"] not in {"CURRENT", "RECONCILED"}
                or current_branch != args.branch
                or not clean
            ):
                result.update(
                    status="BLOCKED",
                    reason="reconcile a clean target branch before syncing the installation",
                )
            else:
                result["installation"] = installed_sync(root, args, remote_sha)
                if result["installation"]["status"] != "CURRENT":
                    result["status"] = result["installation"]["status"]
        return result

    if not args.apply or local_sha == remote_sha:
        return finish()
    if current_branch != args.branch:
        result["status"] = "BLOCKED"
        result["reason"] = f"checkout {args.branch} before applying reconciliation"
        return result
    if not clean:
        result["status"] = "BLOCKED"
        result["reason"] = "working tree is dirty"
        return result
    if not fast_forward_possible and local_tree != remote_tree:
        result["status"] = "BLOCKED"
        result["reason"] = (
            "local and remote histories diverged and trees differ; automatic reconciliation is unsafe"
        )
        return result
    backup = args.backup_branch or f"aips/pre-reconcile-{local_sha[:12]}"
    if git_success_at("show-ref", "--verify", "--quiet", f"refs/heads/{backup}"):
        result["status"] = "BLOCKED"
        result["reason"] = f"backup branch already exists: {backup}"
        return result
    subprocess.run(["git", "branch", backup, local_sha], cwd=root, check=True)
    if fast_forward_possible:
        subprocess.run(
            ["git", "merge", "--ff-only", remote_ref],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        result.update(
            {"status": "RECONCILED", "action": "FAST_FORWARD", "backup_branch": backup}
        )
    elif local_tree == remote_tree:
        subprocess.run(["git", "reset", "--hard", remote_ref], cwd=root, check=True)
        result.update(
            {
                "status": "RECONCILED",
                "action": "RESET_EQUIVALENT_TREE",
                "backup_branch": backup,
            }
        )
    if args.refresh_intelligence:
        refresh_result = subprocess.run(
            [
                sys.executable,
                str(root / "scripts/project_intelligence.py"),
                "refresh",
                "--project",
                str(root),
                "--format",
                "json",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if refresh_result.returncode:
            result["intelligence_refresh"] = {
                "status": "FAILED",
                "error": refresh_result.stderr.strip() or refresh_result.stdout.strip(),
            }
        else:
            result["intelligence_refresh"] = json.loads(refresh_result.stdout)
    return finish()

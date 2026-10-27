#!/usr/bin/env python3
"""Resolve and validate the same exact publication candidate locally and in CI."""

from __future__ import annotations

import argparse
import errno
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import documentation_placement
import repository_preflight
from aips_common import canonical_hash as _aips_canonical_hash
from dependency_impact import pure_dependency_update
from integration_gate import load_yaml as load_matrix_yaml
from integration_gate import matrix_readiness_issues
from publish_post_merge import PreflightError
from publish_post_merge import post_merge as _post_merge
from publish_post_merge import sync_installed as _sync_installed
from publish_preflight_policy import (
    documentation_impact,
    matrix_required,
    pr_creation_plan,
    resolve_change_class,
)
from runtime_cache import cache_environment
from runtime_context import collect_runtime_context

try:
    from content_safety import safe_emit
except ModuleNotFoundError:  # imported as a repository module
    from scripts.content_safety import safe_emit

try:
    from browser_runtime import discover_browser, probe_browser
except ModuleNotFoundError:  # imported as a repository module by lifecycle evidence
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.browser_runtime import discover_browser, probe_browser

CANONICAL_MATRIX = ROOT / ".aips/review/CORE_CHANGE_TEST_MATRIX.yaml"
GIT_PUBLICATION_POLICY = ROOT / "config/git-publication.yaml"
TRAILER_LINE_RE = re.compile(r"[A-Za-z][A-Za-z0-9-]*: \S.*", re.ASCII)
TRAILER_KEY_RE = re.compile(r"[A-Za-z][A-Za-z0-9-]*", re.ASCII)
BOT_SLUG_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?", re.ASCII)
PROFILE_TRAILER_LINE_RE = re.compile(r"([A-Za-z][A-Za-z0-9-]*): ([^<>\r\n]+) <([^<>\r\n]+)>", re.ASCII)
IDENTITY_METADATA_PLACEHOLDER ="git-identity-metadata"


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


def worktree_changed_files(base: str) -> list[str]:
    tracked = git("diff", "--name-only", base, "--")
    untracked = git("ls-files", "--others", "--exclude-standard")
    return sorted({item for item in (*tracked.splitlines(), *untracked.splitlines()) if item})


def canonical_hash(value: Any) -> str:
    return _aips_canonical_hash(value)


def environment_status() -> dict[str, Any]:
    blockers: list[str] = []
    diagnostics: list[dict[str, str]] = []
    from github_workflow_validation import validate_workflows

    workflow_errors = validate_workflows(ROOT)
    if workflow_errors:
        blockers.append("workflow_semantics:invalid")
        diagnostics.append({"check": "workflow_semantics", "status": "BLOCKED", "detail": "; ".join(workflow_errors), "next_step": "Correct reusable workflow structure and permissions before the full Gate."})
    python_version = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
    plan_path = os.environ.get("AIPS_CI_VALIDATION_PLAN")
    plan = None
    if plan_path:
        try:
            plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
            if not isinstance(plan, dict) or plan.get("version") != 1:
                plan = None
        except (OSError, ValueError, TypeError):
            plan = None
    needs_browser = plan is None or plan.get("needs_browser") is True
    needs_openapi = plan is None or plan.get("needs_openapi") is True
    needs_node = plan is None or plan.get("needs_node") is True
    from hashlib import sha256

    from ci_validation_plan import validation_capabilities
    from runtime_context import BASE_VALIDATION_MODULES

    capabilities = validation_capabilities(plan)
    needs_browser, needs_openapi, needs_node = (capabilities[name] for name in ("browser", "openapi", "node"))
    required_modules = list(BASE_VALIDATION_MODULES)
    if needs_browser:
        required_modules.append("playwright")
    if needs_openapi:
        required_modules.append("openapi_spec_validator")
    missing_modules = []
    for module in required_modules:
        check = subprocess.run(
            [sys.executable, "-c", f"import {module}"], capture_output=True, text=True
        )
        if check.returncode:
            missing_modules.append(module)
    if missing_modules:
        blockers.append("python_modules:" + ",".join(missing_modules))
        diagnostics.append({
            "check": "python_modules",
            "status": "BLOCKED",
            "detail": ",".join(missing_modules),
            "next_step": "Run `python3.12 bin/prepare-local-validation` to install the pinned Gate dependencies, then rerun `aips publish environment`.",
        })
    dependency_check = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True, check=False)
    if dependency_check.returncode:
        blockers.append("python_dependencies:inconsistent")
        diagnostics.append({"check": "pip_check", "status": "BLOCKED", "detail": "selected executor has inconsistent dependencies", "next_step": "Rebuild the pinned validation environment, then rerun the environment probe."})
    if python_version.returncode:
        blockers.append("python_runtime:unavailable")
        diagnostics.append({
            "check": "python_runtime",
            "status": "BLOCKED",
            "detail": "selected Python executable could not report its version",
            "next_step": "Select the repository validation environment with `aips publish --project-root <repo> environment`.",
        })
    _, docs_errors = repository_preflight.docs_build_prerequisites(ROOT) if needs_node else (None, [])
    for message in docs_errors:
        check = "node_runtime" if "Node.js" in message else "vitepress"
        blockers.append(check)
        diagnostics.append({
            "check": check,
            "status": "BLOCKED",
            "detail": message.split(";", 1)[0],
            "next_step": message,
        })
    # Telemetry lifecycle always requires loopback, independently of browser selection.
    try:
        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        probe.close()
        localhost = "READY"
    except OSError as exc:
        localhost = "BLOCKED"
        blocker = f"localhost_bind:{exc.__class__.__name__}"
        blockers.append(blocker)
        diagnostics.append({
            "check": "localhost_bind",
            "status": "BLOCKED",
            "detail": exc.__class__.__name__,
            "next_step": "Run in an environment that permits loopback socket binding; rerun `aips publish environment` to verify.",
        })
    selection = discover_browser() if needs_browser else {"provider": "not_required"}
    browser_probe = probe_browser(selection.get("path"), provider=str(selection.get("provider") or "not_required")) if needs_browser else {"status": "NOT_REQUIRED", "provider": "not_required"}
    if needs_browser and browser_probe["status"] != "READY":
        blockers.append(f"browser:{browser_probe['status']}")
        if browser_probe["status"] == "BROWSER_NOT_FOUND":
            next_step = "Install Playwright Chromium with `python -m playwright install chromium`, or configure a supported Chrome/Chromium binary."
        elif browser_probe["status"] == "BROWSER_PROBE_DEPENDENCY_MISSING":
            next_step = "Install project validation dependencies, then rerun `aips publish environment`."
        else:
            next_step = "Inspect the browser probe stderr and retry with the managed Playwright browser; classify launch permission failures as environment blockers."
        stderr = str(browser_probe.get("stderr") or "")
        if any(token in stderr for token in ("PermissionError", "EPERM", "EACCES")):
            detail = "browser launch is blocked by process permissions"
            next_step = "Run in an environment that permits the managed browser to launch, then rerun `aips publish environment`."
        else:
            detail = "browser launch probe failed; inspect locally with `aips publish environment`"
        diagnostics.append({
            "check": "browser_probe",
            "status": str(browser_probe["status"]),
            "detail": detail,
            "next_step": next_step,
        })
    return {
        "status": "READY" if not blockers else "ENVIRONMENT_BLOCKED",
        "runtime_context": collect_runtime_context(ROOT, ROOT),
        "runtime": {"project_root": str(ROOT), "commit": git("rev-parse", "HEAD", check=False), "python": sys.executable},
        "cache_diagnostics": cache_diagnostics(),
        "python": {"executable": Path(sys.executable).name, "version": python_version.stdout.strip() or python_version.stderr.strip()},
        "python_modules": {"status": "READY" if not missing_modules else "BLOCKED", "missing": missing_modules},
        "toolchain": {
            "selected_capabilities": capabilities,
            "required_modules": required_modules,
            "pip_check": "PASS" if dependency_check.returncode == 0 else "FAIL",
            "requirements_sha256": {name: "sha256:" + sha256((ROOT / name).read_bytes()).hexdigest() for name in
                                    ("requirements.txt", "requirements-validation.txt", "requirements-visual.txt", "requirements-openapi.txt", "constraints/tested.txt") if (ROOT / name).is_file()},
        },
        "localhost": localhost,
        "browser": {
            "status": browser_probe["status"],
            "provider": browser_probe.get("provider"),
            "version": browser_probe.get("version"),
            "path_configured": bool(browser_probe.get("path")),
        },
        "blockers": blockers,
        "diagnostics": diagnostics,
    }


def cache_diagnostics() -> list[dict[str, str]]:
    """Probe cache parents separately from Gate prerequisites, without installing anything."""
    results = []
    for name, root in (
        ("retrieval", Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")),
        ("intelligence", Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")),
    ):
        parent = root
        while not parent.exists() and parent != parent.parent:
            parent = parent.parent
        try:
            with tempfile.TemporaryFile(dir=parent):
                pass
            status = "PARENT_WRITABLE"
        except OSError:
            status = "WRITE_BLOCKED"
        results.append({
            "check": name, "status": status,
            "next_step": "Use a writable XDG_CACHE_HOME/XDG_CONFIG_HOME for this runtime; existing SQLite files and sidecars may have separate permissions. Keep network and filesystem diagnosis separate.",
        })
    return results


def preview_candidate(args: argparse.Namespace) -> dict[str, Any]:
    base = resolve_commit(args.base)
    head = resolve_commit(args.head)
    files = worktree_changed_files(base)
    change_class, warning = resolve_change_class(args.change_class, args.labels)
    profile = yaml.safe_load(Path(args.profile).read_text(encoding="utf-8")) or {}
    required = matrix_required(profile, files, change_class)
    matrix_path = Path(args.matrix).resolve() if args.matrix else CANONICAL_MATRIX.resolve()
    if required and matrix_path == CANONICAL_MATRIX.resolve():
        files = sorted(set(files) | {str(CANONICAL_MATRIX.relative_to(ROOT))})
    docs = documentation_impact(files, ROOT, pure_dependency_update(base, None, ROOT))
    placement_errors = documentation_placement.audit_worktree(base)
    matrix_hash = canonical_hash(files)
    binding: dict[str, Any] = {"required": required, "path": str(matrix_path), "changed_files_hash": matrix_hash}
    if required and matrix_path.is_file():
        matrix = load_matrix_yaml(matrix_path)
        candidate = matrix.get("candidate") or {}
        issues = matrix_readiness_issues(matrix, base_sha=base, changed_files_hash=matrix_hash)
        binding.update({
            "base_matches": candidate.get("base_sha") == base,
            "hash_matches": candidate.get("changed_files_hash") == matrix_hash,
            "bound_base": candidate.get("base_sha"),
            "bound_hash": candidate.get("changed_files_hash"),
            "readiness": "READY" if not issues else "BLOCKED",
            "issues": issues,
        })
    else:
        binding["base_matches"] = not required
        binding["hash_matches"] = not required
        binding["readiness"] = "BLOCKED" if required else "NOT_REQUIRED"
        binding["issues"] = ["missing"] if required else []
    pending = list(docs["required_additions"])
    if required and any(issue in {"base_sha", "changed_files_hash", "missing"} for issue in binding["issues"]):
        binding["next_step"] = (
            f"Run `aips publish matrix-sync --base {base}`, then review the matrix scope and "
            "evidence before marking it READY."
        )
    matrix_messages = {
        "missing": "canonical Core Change Test Matrix is missing",
        "status": "Core Change Test Matrix status is not executable; review scope and mark it READY",
        "blockers": "Core Change Test Matrix contains blockers; resolve them before Gate",
        "actual_diff_reconciled": "Core Change Test Matrix actual diff is not reconciled",
        "base_sha": "Core Change Test Matrix base binding needs synchronization",
        "changed_files_hash": "Core Change Test Matrix changed-files binding needs synchronization",
    }
    pending.extend(matrix_messages[issue] for issue in binding["issues"])
    pending.extend(f"Documentation placement: {item}" for item in placement_errors)
    safety = preview_content_safety(base, files)
    identity = configured_identity_plan()
    pending.extend(safety["blockers"])
    pending.extend(identity["blockers"])
    return {
        "version": 1,
        "status": "READY_FOR_GATE" if not pending else "NEEDS_WORK",
        "preview": True,
        "candidate": {"base": base, "head": head, "working_tree_included": True, "changed_files": files},
        "change_class": change_class,
        "change_class_warning": warning,
        "documentation": docs,
        "documentation_placement": {"status": "PASS" if not placement_errors else "BLOCKED", "errors": placement_errors},
        "matrix": binding,
        "pr_creation": pr_creation_plan(change_class),
        "content_safety": safety,
        "git_identity": identity,
        "pending": pending,
        "note": "Preview includes committed, staged, unstaged and untracked paths; final Integration Gate still requires a clean committed candidate.",
    }


def preview_content_safety(base: str, files: list[str]) -> dict[str, Any]:
    tracked_diff = git("diff", "--no-ext-diff", "--unified=0", base, "--")
    tracked_additions = [
        line[1:]
        for line in tracked_diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    untracked: dict[str, str] = {}
    unscannable: list[str] = []
    m4a_blockers: list[str] = []
    font_blockers: list[str] = []
    raster_blockers: list[str] = []
    for relative in files:
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            continue
        if path.suffix.lower() == ".avif":
            from media_metadata import MediaInspectionError, extract_metadata
            if path.stat().st_size > 8 * 1024 * 1024:
                raster_blockers.append(f"AVIF exceeds 8 MiB publication limit: {relative}")
                continue
            try:
                untracked[relative] = extract_metadata(path.read_bytes(), ".avif")
            except (MediaInspectionError, OSError):
                raster_blockers.append(f"STAGED_MEDIA_INVALID: {relative}")
            continue
        if path.suffix.lower() == ".m4a":
            from m4a_inspection import M4AInspectionError, inspect_m4a, metadata_text
            size = path.stat().st_size
            if size > 8 * 1024 * 1024:
                m4a_blockers.append(f"M4A exceeds 8 MiB publication limit: {relative}; use Git LFS or external asset storage.")
                continue
            try:
                inspected = inspect_m4a(path.read_bytes())
            except (M4AInspectionError, OSError):
                m4a_blockers.append(f"invalid or spoofed M4A file: {relative}")
                continue
            # The source-artifact sink scans selected metadata, not binary audio.
            untracked[relative] = metadata_text(inspected.metadata)
            continue
        if path.suffix.lower() in {".ttf", ".otf", ".woff", ".woff2"}:
            from media_metadata import MediaInspectionError, extract_metadata
            if path.stat().st_size > 8 * 1024 * 1024:
                font_blockers.append(f"STAGED_FONT_RESOURCE_LIMIT: {relative}")
                continue
            try:
                untracked[relative] = extract_metadata(path.read_bytes(), path.suffix.lower())
            except (MediaInspectionError, OSError) as exc:
                reason = str(exc) if str(exc).startswith("STAGED_FONT_") else "STAGED_FONT_INVALID"
                font_blockers.append(f"{reason}: {relative}")
            continue
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "--", relative], cwd=ROOT, capture_output=True, text=True)
        if tracked.returncode == 0:
            continue
        if path.stat().st_size > 1_000_000:
            unscannable.append(relative)
            continue
        try:
            untracked[relative] = path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError):
            unscannable.append(relative)
    check = safe_emit(sink="source_artifact", payload={"tracked_additions": tracked_additions, "untracked_files": untracked})
    blockers = list(m4a_blockers) + font_blockers + raster_blockers
    if check["decision"] == "BLOCK":
        blockers.append("early content-safety check blocked the working-tree candidate")
    if unscannable:
        blockers.append("early content-safety check could not scan one or more candidate files")
    return {
        "status": "BLOCKED" if blockers else "PASS",
        "findings": [{"type": item["type"], "detector": item["detector"], "location": item["location"]} for item in check["findings"]],
        "unscannable_count": len(unscannable),
        "blockers": blockers,
    }


def configured_identity_plan() -> dict[str, Any]:
    policy = yaml.safe_load((ROOT / "config/git-publication.yaml").read_text(encoding="utf-8")) or {}
    patterns = [re.compile(str(item), re.IGNORECASE) for item in (policy.get("identity") or {}).get("allowed_email_patterns") or []]
    email = git("config", "--get", "user.email", check=False).strip()
    valid = bool(email) and any(pattern.fullmatch(email) for pattern in patterns)
    return {
        "status": "PASS" if valid else "BLOCKED",
        "configured": bool(email),
        "findings": [] if valid else [{"reason": "git_email_not_approved" if email else "git_email_not_configured"}],
        "blockers": [] if valid else ["configured Git author email is not approved by publication policy"],
    }


def sync_matrix_binding(base_ref: str, head_ref: str, matrix_path: Path) -> dict[str, Any]:
    base = resolve_commit(base_ref)
    head = resolve_commit(head_ref)
    matrix_path = matrix_path.resolve()
    if matrix_path != CANONICAL_MATRIX.resolve():
        raise PreflightError("matrix sync only writes the canonical Core Change Test Matrix")
    files = sorted(set(worktree_changed_files(base)) | {str(CANONICAL_MATRIX.relative_to(ROOT))})
    digest = canonical_hash(files)
    original_text = matrix_path.read_text(encoding="utf-8")
    text = original_text
    data = yaml.safe_load(text) or {}
    if not isinstance(data.get("candidate"), dict):
        raise PreflightError("canonical Core Change Test Matrix requires a candidate mapping")
    replacements = {"base_sha": base, "changed_files_hash": digest}
    for key, value in replacements.items():
        pattern = rf"(?m)^(  {re.escape(key)}:\s*).+$"
        text, count = re.subn(pattern, lambda match: match.group(1) + value, text, count=1)
        if count != 1:
            raise PreflightError(f"canonical Core Change Test Matrix must contain exactly one top-level candidate.{key}")
    changed = text != original_text
    if changed:
        text, _ = re.subn(r"(?m)^actual_diff_reconciled:\s*(?:true|false)\s*$", "actual_diff_reconciled: false", text, count=1)
        text, _ = re.subn(r"(?m)^status:\s*(?:READY|APPROVED|PASS)\s*$", "status: DRAFT", text, count=1)
        blockers = data.get("blockers") or []
        if not isinstance(blockers, list):
            raise PreflightError("Core Change Test Matrix blockers must be a list")
        reminder = "candidate binding refreshed; review scope and evidence before marking READY"
        if reminder not in blockers:
            empty = re.compile(r"(?m)^blockers:\s*\[\s*\]\s*$")
            populated = re.compile(r"(?m)^blockers:\n((?:[ \t]*-[^\n]*\n)+)")
            if empty.search(text):
                text = empty.sub(f"blockers:\n  - {reminder}", text, count=1)
            elif populated.search(text):
                text = populated.sub(
                    lambda match: match.group(0) + re.match(r"[ \t]*", match.group(1)).group(0) + f"- {reminder}\n",
                    text, count=1,
                )
            else:
                raise PreflightError("matrix binding changed; unable to safely add a review blocker")
    if changed:
        matrix_path.write_text(text, encoding="utf-8")
    return {
        "status": "BOUND_NEEDS_REVIEW" if changed else "UNCHANGED",
        "base_sha": base,
        "head_sha": head,
        "changed_files": files,
        "changed_files_hash": digest,
        "requires_review": changed,
        "path": str(matrix_path),
    }


def remote_policy(branch: str, offline: bool) -> dict[str, Any]:
    if offline:
        return {"status": "NOT_CHECKED", "reason": "offline"}
    gh = shutil.which("gh")
    remote = git("remote", "get-url", "origin", check=False)
    if not gh or "github.com" not in remote:
        return {"status": "UNAVAILABLE", "reason": "GitHub CLI or GitHub origin unavailable", "next_step": "Install gh and configure a GitHub origin before publication."}
    gh_env = cache_environment()
    auth = subprocess.run([gh, "auth", "status", "-h", "github.com"], cwd=ROOT, capture_output=True, text=True, env=gh_env)
    if auth.returncode:
        diagnostic = (auth.stderr + "\n" + auth.stdout).lower()
        if any(marker in diagnostic for marker in (
            "no such host", "could not resolve", "network is unreachable",
            "temporary failure in name resolution", "connection timed out",
            "connect: operation not permitted", "failed to connect",
        )):
            return {"status": "NETWORK_UNAVAILABLE", "reason": "GitHub connectivity is unavailable", "next_step": "Check network or sandbox access to api.github.com, then rerun `gh auth status -h github.com`."}
        if os.environ.get("XDG_CONFIG_HOME") and not os.environ.get("GH_CONFIG_DIR"):
            return {
                "status": "AUTH_CONFIGURATION_UNVERIFIED",
                "reason": "GitHub CLI authentication was checked using XDG_CONFIG_HOME/gh",
                "next_step": "Verify that this is the intended GitHub configuration directory. When isolating AIPS configuration, preserve the original gh directory with GH_CONFIG_DIR, then rerun `gh auth status -h github.com`. Do not copy credentials or repeat login solely because configuration was isolated.",
            }
        return {"status": "AUTH_REQUIRED", "reason": "GitHub CLI authentication is unavailable in the selected configuration", "next_step": "Verify GH_CONFIG_DIR/XDG_CONFIG_HOME selects the intended gh configuration, then run `gh auth status -h github.com`; login only if authentication is actually missing."}
    path = remote.removeprefix("git@github.com:").removeprefix("https://github.com/").removesuffix(".git")
    repository = subprocess.run([gh, "api", f"repos/{path}"], cwd=ROOT, capture_output=True, text=True, env=gh_env)
    if repository.returncode:
        diagnostic = (repository.stderr + "\n" + repository.stdout).lower()
        if any(marker in diagnostic for marker in (
            "no such host", "could not resolve", "network is unreachable",
            "temporary failure in name resolution", "connection timed out",
            "connect: operation not permitted", "failed to connect",
        )):
            return {"status": "NETWORK_UNAVAILABLE", "reason": "GitHub connectivity is unavailable", "next_step": "Check network or sandbox access to api.github.com, then rerun `gh auth status -h github.com`."}
        if any(marker in diagnostic for marker in ("http 401", "http 403", "bad credentials", "resource not accessible")):
            return {"status": "AUTH_REQUIRED", "reason": "GitHub API access to the repository is unavailable", "next_step": "Verify repository access with `gh auth status -h github.com` and ensure the token can read repository metadata."}
        return {"status": "UNAVAILABLE", "reason": "repository metadata query failed", "next_step": "Check GitHub CLI repository access and rerun publication plan."}
    try:
        repository_data = json.loads(repository.stdout)
    except json.JSONDecodeError:
        return {"status": "UNAVAILABLE", "reason": "repository metadata response was invalid", "next_step": "Retry the GitHub repository metadata query before publication."}
    merge_methods = [
        name for key, name in (
            ("allow_merge_commit", "merge_commit"),
            ("allow_squash_merge", "squash"),
            ("allow_rebase_merge", "rebase"),
        ) if repository_data.get(key) is True
    ]
    proc = subprocess.run([gh, "api", f"repos/{path}/branches/{branch}/protection"], cwd=ROOT, capture_output=True, text=True, env=gh_env)
    if proc.returncode == 0:
        return {"status": "PROTECTED", "publication_route": "pull_request", "merge_methods": merge_methods}
    if "Branch not protected" in proc.stderr or "404" in proc.stderr:
        return {"status": "UNPROTECTED", "publication_route": "direct_or_pull_request", "merge_methods": merge_methods}
    diagnostic = (proc.stderr + "\n" + proc.stdout).lower()
    if any(marker in diagnostic for marker in (
        "no such host", "could not resolve", "network is unreachable",
        "temporary failure in name resolution", "connection timed out",
        "connect: operation not permitted", "failed to connect",
    )):
        return {"status": "NETWORK_UNAVAILABLE", "reason": "GitHub connectivity is unavailable", "next_step": "Check network or sandbox access to api.github.com, then rerun publication plan."}
    if any(marker in diagnostic for marker in ("http 401", "http 403", "bad credentials", "resource not accessible")):
        return {"status": "AUTH_REQUIRED", "reason": "GitHub branch policy could not be read", "next_step": "Verify repository access with `gh auth status -h github.com` and ensure the token can read branch settings."}
    return {"status": "UNAVAILABLE", "reason": "branch protection query failed", "next_step": "Check GitHub CLI repository access and rerun publication plan."}


class GitIdentityPolicyError(ValueError):
    """The Git identity policy is malformed; publication checks fail closed."""


def _string_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise GitIdentityPolicyError(f"{field} must be a list of non-empty strings")
    return value


def _profile_values() -> dict[str, bool]:
    """Effective AIPS profile switches; any problem yields the strict defaults (all off)."""
    try:
        from aips_profile import load_profile

        return dict(load_profile().values)
    except Exception:  # noqa: BLE001 - an unavailable profile must never relax the policy.
        return {}


def git_identity_policy(profile_values: dict[str, bool] | None = None) -> dict[str, Any]:
    """Load the Git identity policy; any malformed entry raises GitIdentityPolicyError (callers fail closed).

    ``profile_values`` are the effective AIPS profile switches (default: read from the profile file).
    """
    try:
        policy = yaml.safe_load(GIT_PUBLICATION_POLICY.read_text(encoding="utf-8")) or {}
        identity = policy.get("identity") or {}
        if not isinstance(identity, dict):
            raise GitIdentityPolicyError("identity must be a mapping")
        human = [re.compile(item, re.IGNORECASE) for item in _string_list(identity.get("allowed_email_patterns"), "allowed_email_patterns")]
        bots = [re.compile(item, re.ASCII) for item in _string_list(identity.get("allowed_bot_author_patterns"), "allowed_bot_author_patterns")]
        trailers: list[dict[str, Any]] = []
        raw_trailers = identity.get("trailer_identities") or []
        if not isinstance(raw_trailers, list):
            raise GitIdentityPolicyError("trailer_identities must be a list")
        for entry in raw_trailers:
            if not isinstance(entry, dict) or set(entry) != {"key", "name", "email_pattern", "requires_author_slug"}:
                raise GitIdentityPolicyError("trailer identity requires exactly key, name, email_pattern and requires_author_slug")
            key, name, pattern, slug = (entry[field] for field in ("key", "name", "email_pattern", "requires_author_slug"))
            if not all(isinstance(item, str) and item.isascii() for item in (key, name, pattern, slug)):
                raise GitIdentityPolicyError("trailer identity fields must be ASCII strings")
            if not TRAILER_KEY_RE.fullmatch(key) or not BOT_SLUG_RE.fullmatch(slug):
                raise GitIdentityPolicyError("trailer identity key or author slug is malformed")
            if not name.strip() or name != name.strip() or any(char in name for char in "<>\r\n"):
                raise GitIdentityPolicyError("trailer identity name is malformed")
            trailers.append({"prefix": f"{key}: {name} <", "email": re.compile(pattern, re.ASCII), "slug": slug})
        raw_profile = identity.get("profile_trailer_identities") or {}
        if not isinstance(raw_profile, dict):
            raise GitIdentityPolicyError("profile_trailer_identities must be a mapping")
        enabled = profile_values if profile_values is not None else _profile_values()
        for switch, entry in raw_profile.items():
            if not isinstance(entry, dict) or set(entry) != {"key", "name_pattern", "email_pattern"}:
                raise GitIdentityPolicyError("profile trailer identity requires exactly key, name_pattern and email_pattern")
            key, name_pattern, pattern = (entry[field] for field in ("key", "name_pattern", "email_pattern"))
            if not isinstance(switch, str) or not all(isinstance(item, str) and item.isascii() for item in (key, name_pattern, pattern)):
                raise GitIdentityPolicyError("profile trailer identity fields must be ASCII strings")
            if not TRAILER_KEY_RE.fullmatch(key):
                raise GitIdentityPolicyError("profile trailer identity key is malformed")
            compiled_name, compiled_email = re.compile(name_pattern, re.ASCII), re.compile(pattern, re.ASCII)
            if enabled.get(switch) is True:
                trailers.append({"key": key, "name": compiled_name, "email": compiled_email, "slug": None})
    except (OSError, re.error, yaml.YAMLError, AttributeError) as exc:
        raise GitIdentityPolicyError(type(exc).__name__) from exc
    if not human:
        raise GitIdentityPolicyError("allowed_email_patterns must not be empty")
    return {"human": human, "bots": bots, "trailers": trailers}


def is_bot_author(email: str, policy: dict[str, Any], slug: str | None = None) -> bool:
    if not email.isascii() or not any(pattern.fullmatch(email) for pattern in policy["bots"]):
        return False
    if slug is None:
        return True
    return re.fullmatch(r"[0-9]+\+" + re.escape(slug) + r"\[bot\]", email.split("\x40", 1)[0], re.ASCII) is not None


def mask_trailer_identities(message: str, author_email: str, policy: dict[str, Any]) -> str:
    """Replace exact approved trailer identities in the final trailer block with a placeholder.

    Every other line, including any other address, is returned unchanged for the PII scan.
    """
    blocks = message.rstrip("\n").split("\n\n")
    if len(blocks) < 2 or not policy["trailers"]:
        return message
    lines = blocks[-1].split("\n")
    if not all(TRAILER_LINE_RE.fullmatch(line) for line in lines):
        return message
    masked: list[str] = []
    for line in lines:
        for identity in policy["trailers"]:
            if identity["slug"] is None:
                # Profile-gated identity: exact key, name and address; the commit author is not constrained.
                match = PROFILE_TRAILER_LINE_RE.fullmatch(line)
                if (match and match.group(1) == identity["key"] and identity["name"].fullmatch(match.group(2))
                        and identity["email"].fullmatch(match.group(3))):
                    line = f"{match.group(1)}: {match.group(2)} <{IDENTITY_METADATA_PLACEHOLDER}>"
                    break
                continue
            prefix = identity["prefix"]
            if (
                line.startswith(prefix)
                and line.endswith(">")
                and identity["email"].fullmatch(line[len(prefix):-1])
                and is_bot_author(author_email, policy, identity["slug"])
            ):
                line = prefix + IDENTITY_METADATA_PLACEHOLDER + ">"
                break
        masked.append(line)
    blocks[-1] = "\n".join(masked)
    return "\n\n".join(blocks)


def candidate_commit_messages(base: str, head: str) -> str:
    try:
        policy: dict[str, Any] | None = git_identity_policy()
    except ValueError:
        policy = None  # Fail closed: scan raw messages; commit_identity_plan reports the invalid policy.
    messages: list[str] = []
    for commit in reversed(git("rev-list", "--reverse", f"{base}..{head}").splitlines()):
        message = git("log", "-1", "--format=%B", commit)
        if policy is not None:
            message = mask_trailer_identities(message, git("show", "-s", "--format=%ae", commit), policy)
        messages.append(message)
    return "\n\n".join(messages)


def content_safety_plan(args: argparse.Namespace, base: str, head: str) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(sink: str, payload: Any, label: str, context: dict[str, Any] | None = None) -> None:
        result = safe_emit(sink=sink, payload=payload, context=context)
        checks.append({"label": label, "sink": sink, "decision": result["decision"], "findings": result["findings"]})

    messages = candidate_commit_messages(base, head)
    check("git_commit", messages, "commit_messages")
    diff = git("diff", "--no-ext-diff", "--unified=0", base, head)
    from content_safety import git_diff_payload_with_added_lines

    diff_payload, added_lines = git_diff_payload_with_added_lines(diff)
    check("source_artifact", diff_payload, "candidate_diff", {
        "source_path": "<candidate-diff>",
        "injection_changed_lines": sorted(added_lines),
    })
    if args.commit_message:
        check("git_commit", args.commit_message, "explicit_commit_message")
    if args.body:
        check("github_pr", args.body, "explicit_body")
    if args.body_file:
        body_path = Path(args.body_file).expanduser().resolve()
        if not body_path.is_file():
            checks.append({"label": "body_file", "sink": "github_pr", "decision": "BLOCK", "findings": [], "reason": "body file does not exist"})
        else:
            check("github_pr", body_path.read_text(encoding="utf-8"), "body_file")
    blockers = [f"content safety blocked {item['label']}" for item in checks if item["decision"] == "BLOCK"]
    return {"status": "BLOCKED" if blockers else "PASS", "checks": checks, "blockers": blockers}


def commit_identity_plan(base: str, head: str) -> dict[str, Any]:
    try:
        policy = git_identity_policy()
    except ValueError:
        return {
            "status": "BLOCKED",
            "findings": [{"reason": "identity_policy_invalid"}],
            "blockers": ["Git identity policy in config/git-publication.yaml is invalid"],
        }
    invalid: list[dict[str, str]] = []
    commits = git("rev-list", "--reverse", f"{base}..{head}").splitlines()
    for commit in commits:
        fields = git("show", "-s", "--format=%ae%x00%ce", commit).split("\0")
        for field, email in zip(("author", "committer"), fields):
            approved = bool(email) and (
                any(pattern.fullmatch(email) for pattern in policy["human"])
                or (field == "author" and is_bot_author(email, policy))
            )
            if not approved:
                invalid.append({"commit": commit[:12], "field": field, "reason": "email_not_approved"})
    blockers = ["candidate contains an author/committer identity outside the approved GitHub noreply formats"] if invalid else []
    return {"status": "BLOCKED" if blockers else "PASS", "findings": invalid, "blockers": blockers}


def secret_scan_plan(base: str, head: str) -> dict[str, Any]:
    command = [
        sys.executable,
        str(ROOT / "scripts/check_secret_leakage.py"),
        "--root", str(ROOT),
        "--policy", str(ROOT / "config/secret-scan.yaml"),
        "--publication-candidate",
        "--base", base,
        "--head", head,
        "--json",
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "status": "BLOCKED",
            "findings": [],
            "blockers": ["mandatory candidate secret scan did not return a valid redacted report"],
        }
    if result.returncode != 0 or report.get("status") != "PASS":
        status = "BLOCKED" if report.get("status") == "BLOCKED" or result.returncode == 2 else "FAIL"
        return {**report, "status": status}
    return report


def build_plan(args: argparse.Namespace, environment: dict[str, Any] | None = None) -> dict[str, Any]:
    base = resolve_commit(args.base)
    head = resolve_commit(args.head)
    files = changed_files(base, head)
    profile = yaml.safe_load(Path(args.profile).read_text(encoding="utf-8")) or {}
    change_class, warning = resolve_change_class(args.change_class, args.labels)
    required = matrix_required(profile, files, change_class)
    matrix = Path(args.matrix).resolve() if args.matrix else CANONICAL_MATRIX
    matrix_ok = matrix.is_file() and matrix == CANONICAL_MATRIX.resolve()
    blockers: list[str] = []
    try:
        git_root = Path(git("rev-parse", "--show-toplevel")).resolve()
    except PreflightError:
        git_root = None
    if git_root != ROOT.resolve():
        blockers.append("publish preflight source root does not match the Git checkout root")
    if required and not matrix_ok:
        blockers.append("canonical Core Change Test Matrix is required")
    docs = documentation_impact(files, ROOT, pure_dependency_update(base, head, ROOT))
    if not docs["complete"]:
        blockers.append("documentation impact is incomplete")
    if git("status", "--porcelain"):
        blockers.append("working tree is dirty; commit the exact candidate before publication preflight")
    if resolve_commit("HEAD") != head:
        blockers.append("current checkout does not match the exact candidate head")
    if args.base_tip and resolve_commit(args.base_tip) != base:
        blockers.append("candidate base is stale relative to base-tip")
    safety = content_safety_plan(args, base, head)
    blockers.extend(safety["blockers"])
    secret_scan = secret_scan_plan(base, head)
    if secret_scan["status"] != "PASS":
        blockers.extend(secret_scan.get("blockers") or ["mandatory candidate secret scan failed"])
    identities = commit_identity_plan(base, head)
    blockers.extend(identities["blockers"])
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
        "repository": {
            "root": str(ROOT.resolve()),
            "git_root": str(git_root) if git_root else None,
            "root_matches": git_root == ROOT.resolve(),
        },
        "candidate": {"base": base, "head": head, "changed_files": files},
        "change_class": change_class,
        "change_class_warning": warning,
        "pr_creation": pr_creation_plan(change_class),
        "matrix": {
            "required": required,
            "path": str(matrix),
            "canonical": matrix_ok,
            "changed_files_hash": canonical_hash(files),
        },
        "documentation": docs,
        "environment": environment if environment is not None else environment_status(),
        "remote": remote_policy(args.branch, args.offline),
        "content_safety": safety,
        "secret_scan": secret_scan,
        "git_identity": identities,
        "blockers": blockers,
        "status": "READY" if not blockers else "BLOCKED",
    }


def summarize_checks(payload: dict[str, Any], required: list[str]) -> dict[str, Any]:
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    cancelled = 0
    superseded = []
    for check in payload.get("statusCheckRollup") or []:
        if check.get("conclusion") == "CANCELLED":
            cancelled += 1
        key = (str(check.get("workflowName") or ""), str(check.get("name") or check.get("context") or ""))
        stamp = str(check.get("startedAt") or check.get("createdAt") or "")
        previous_stamp = str(latest.get(key, {}).get("startedAt") or latest.get(key, {}).get("createdAt") or "")
        tied_unsuccessful = stamp == previous_stamp and check.get("conclusion") not in {"SUCCESS", "NEUTRAL"}
        if key not in latest or stamp > previous_stamp or tied_unsuccessful:
            if key in latest:
                superseded.append({"name": key[1], "status": "SUPERSEDED", "conclusion": latest[key].get("conclusion")})
            latest[key] = check
        else:
            superseded.append({"name": key[1], "status": "SUPERSEDED", "conclusion": check.get("conclusion")})
    failures, pending, incomplete, skipped, passed = [], [], [], [], []
    required_pass = set()
    for (_, name), check in sorted(latest.items()):
        conclusion = check.get("conclusion") or check.get("state")
        if conclusion in {"FAILURE", "ERROR", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE"}:
            failures.append(name)
        elif conclusion in {"SUCCESS", "NEUTRAL"}:
            passed.append(name)
            if conclusion == "SUCCESS":
                required_pass.add(name)
        elif conclusion == "SKIPPED":
            skipped.append(name)
        elif conclusion == "CANCELLED":
            incomplete.append(name)
        else:
            pending.append(name)
    missing = sorted(set(required) - required_pass)
    status = "FAIL" if failures else "PENDING" if pending else "INCOMPLETE" if missing or incomplete else "PASS"
    return {"status": status, "head_sha": payload.get("headRefOid"), "failures": failures,
            "pending": pending, "incomplete": incomplete, "skipped": skipped, "passed": passed,
            "required_not_passed": missing, "cancelled_run_checks": cancelled,
            "superseded_checks": superseded,
            "merge_authority": False}


def check_status(args: argparse.Namespace) -> dict[str, Any]:
    gh = shutil.which("gh")
    if not gh:
        return {"status": "BLOCKED", "reason_code": "GH_UNAVAILABLE"}
    proc = subprocess.run([gh, "pr", "view", str(args.pr), "--json", "headRefOid,statusCheckRollup"],
                          cwd=ROOT, capture_output=True, text=True, env=cache_environment())
    if proc.returncode:
        return {"status": "BLOCKED", "reason_code": "CHECKS_UNAVAILABLE", "next_step": "Verify GitHub connectivity and repository access; raw diagnostics are withheld."}
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"status": "BLOCKED", "reason_code": "INVALID_CHECK_RESPONSE"}
    if not isinstance(payload, dict):
        return {"status": "BLOCKED", "reason_code": "INVALID_CHECK_RESPONSE"}
    if args.head and payload.get("headRefOid") != args.head:
        return {"status": "BLOCKED", "reason_code": "CANDIDATE_CHANGED"}
    return summarize_checks(payload, args.required_check or ["repository"])


def sync_installed(root: Path, args: argparse.Namespace, expected: str) -> dict[str, Any]:
    return _sync_installed(root, args, expected)


def post_merge(args: argparse.Namespace) -> dict[str, Any]:
    return _post_merge(args, root_default=ROOT, installed_sync=sync_installed)


def emit(value: dict[str, Any], fmt: str) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2) if fmt == "json" else yaml.safe_dump(value, sort_keys=False, allow_unicode=True).rstrip())


def cli_exception_result(exc: Exception) -> dict[str, Any]:
    """Return a redacted, non-authorizing JSON diagnosis for CLI-boundary failures."""
    if isinstance(exc, PermissionError):
        error_class = "PermissionError"
    elif isinstance(exc, FileNotFoundError):
        error_class = "FileNotFoundError"
    elif isinstance(exc, OSError):
        error_class = "OSError"
    elif isinstance(exc, ValueError):
        error_class = "ValueError"
    else:
        error_class = "PreflightError"
    error_code = None
    if isinstance(exc, OSError):
        error_code = errno.errorcode.get(exc.errno, "UNKNOWN_OS_ERROR")
        safe_os_message = os.strerror(exc.errno) if exc.errno is not None else "unknown OS error"
        if exc.errno in {errno.EACCES, errno.EPERM}:
            reason_code = "LOCAL_PERMISSION_DENIED"
            category = "PERMISSION"
            next_step = "Check access to the selected worktree and body file, then rerun the read-only command."
            next_step_zh = "檢查工作樹與 body 檔案的存取權限，再重新執行唯讀診斷。"
        elif exc.errno == errno.ENOENT:
            reason_code = "LOCAL_FILE_NOT_FOUND"
            category = "INVALID_ARGUMENT"
            next_step = "Check that the selected worktree and body file exist, then rerun the read-only command."
            next_step_zh = "確認工作樹與 body 檔案存在，再重新執行唯讀診斷。"
        elif exc.errno in {errno.ENOSPC, getattr(errno, "EDQUOT", -1)}:
            reason_code = "LOCAL_STORAGE_UNAVAILABLE"
            category = "INTERNAL"
            next_step = "Free local storage or resolve the quota limit, then rerun the read-only command."
            next_step_zh = "釋出本機空間或排除配額限制，再重新執行唯讀診斷。"
        else:
            reason_code = "LOCAL_OS_ERROR"
            category = "INTERNAL"
            next_step = "Check local worktree and file access, then rerun the read-only command."
            next_step_zh = "檢查工作樹與檔案存取狀態，再重新執行唯讀診斷。"
        detail = f"Local operation failed: {safe_os_message} ({error_code})."
        detail_zh = f"本機操作失敗：{error_code}。"
    elif isinstance(exc, ValueError):
        reason_code = "INVALID_PUBLICATION_INPUT"
        category = "INVALID_ARGUMENT"
        detail = "A publication input or local state value was invalid."
        detail_zh = "發佈輸入或本機狀態值無效。"
        next_step = "Review the worktree and supplied title, body file, or literal native command, then retry."
        next_step_zh = "檢查工作樹、標題、body 檔案或原生指令內容後重試。"
    else:
        reason_code = "PREFLIGHT_VALIDATION_ERROR"
        category = "INTERNAL"
        detail = "The local publication preflight rejected the request. Raw exception details are withheld."
        detail_zh = "本機發佈前置驗證拒絕此要求；原始例外內容已遮蔽。"
        next_step = "Review the worktree and supplied input, then rerun prepare or diagnose without a shell pipeline."
        next_step_zh = "檢查工作樹與輸入內容，並以獨立指令重新執行 prepare 或 diagnose。"
    diagnostic: dict[str, Any] = {
        "version": 1,
        "reason_code": reason_code,
        "detail": detail,
        "phase": "cli_error",
        "category": category,
        "source": "AIPS_PUBLICATION",
        "blocking_rule": "LOCAL_PREFLIGHT",
        "blocking_rule_id": reason_code,
        "error_class": error_class,
        "retryable": False,
        "redacted": True,
        "detail_zh": detail_zh,
        "next_step": next_step,
        "next_step_zh": next_step_zh,
    }
    if error_code:
        diagnostic["error_code"] = error_code
    return {
        "version": 2,
        "status": "BLOCKED",
        "authorized": False,
        "executed": False,
        "api_write_performed": False,
        "diagnostics": [diagnostic],
        "recovery": {
            "state": "REPAIR_REQUIRED",
            "next_step": "REVIEW_LOCAL_INPUT",
            "requires_human": False,
            "retry_read_only": False,
            "executed": False,
            "authorized": False,
            "instruction": "Resolve the local error and re-run a read-only diagnosis; this report never authorizes publication.",
        },
    }


def run_candidate(args: argparse.Namespace) -> int:
    environment = environment_status()
    if environment["status"] != "READY":
        emit({
            "version": 1,
            "repository": {"root": str(ROOT.resolve()), "git_root": git("rev-parse", "--show-toplevel", check=False)},
            "status": "ENVIRONMENT_BLOCKED",
            "environment": environment,
            "blockers": [f"environment:{item}" for item in environment["blockers"]],
        }, args.format)
        return 2
    plan = build_plan(args, environment=environment)
    if plan["status"] != "READY":
        emit(plan, args.format)
        return 2 if plan["status"] == "ENVIRONMENT_BLOCKED" else 1
    env = dict(os.environ)
    # Nested helpers invoke bare `python3`; keep them on this Gate interpreter.
    env["PATH"] = os.pathsep.join((str(Path(sys.executable).parent), env.get("PATH", "")))
    env["AIPS_DOCS_DIFF_BASE"] = plan["candidate"]["base"]
    fast = subprocess.run(
        [sys.executable, str(ROOT / "scripts/repository_preflight.py"), "--base", plan["candidate"]["base"], "--head", plan["candidate"]["head"], "--docs-build"],
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
    if args.review_evidence:
        command.extend(["--review-evidence", args.review_evidence])
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
    parser.add_argument("--review-evidence")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--commit-message")
    parser.add_argument("--body")
    parser.add_argument("--body-file")
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")


def main() -> int:
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command", required=True)
    doctor = subs.add_parser("doctor", help="Read-only phase-separated GitHub policy and worktree diagnostics")
    doctor.add_argument("--project-root", "--worktree", dest="worktree", type=Path, default=Path.cwd())
    doctor.add_argument("--branch", help="Branch to inspect; defaults to the remote default branch")
    doctor.add_argument("--pr", type=int, help="Optional PR number for read-only state inspection")
    doctor.add_argument("--worktree-details", action="store_true", help="Include staged/modified/deleted/untracked repository-relative paths")
    doctor.add_argument("--format", choices=("yaml", "json"), default="yaml")
    prepare = subs.add_parser("prepare", help="Read-only native publication command and resume plan")
    prepare.add_argument("--worktree", required=True, type=Path)
    prepare.add_argument("--title", required=True)
    prepare.add_argument("--body-file", required=True, type=Path)
    prepare.add_argument("--runtime", choices=("codex", "claude-code", "gemini-cli", "opencode"), default="codex")
    prepare.add_argument("--expected-fingerprint")
    prepare.add_argument("--host-denied", action="store_true")
    prepare.add_argument("--host-denial-class", choices=("unknown", "merge-without-review",
                         "read-only-diagnostic"), default="unknown")
    prepare.add_argument("--merge-intent", action="store_true", help="Task intent only; never a grant or host permission")
    prepare.add_argument("--auto-merge", action="store_true", help="Request GitHub auto-merge after verified required checks; native authorization still applies")
    prepare.add_argument("--format", choices=("yaml", "json"), default="yaml")
    diagnose = subs.add_parser("diagnose", help="Diagnose a literal native command without executing it")
    diagnose.add_argument("--worktree", type=Path, default=Path.cwd())
    diagnose_target = diagnose.add_mutually_exclusive_group(required=True)
    diagnose_target.add_argument("--command", dest="native_command")
    diagnose_target.add_argument("--diagnostic-id", help="Read one safe event from the configured governance audit ledger")
    diagnose.add_argument("--format", choices=("yaml", "json"), default="yaml")
    plan = subs.add_parser("plan")
    common(plan)
    preview = subs.add_parser("preview")
    common(preview)
    run = subs.add_parser("run")
    common(run)
    run.add_argument("--output", required=True)
    docs = subs.add_parser("docs-impact")
    docs.add_argument("--base", required=True)
    docs.add_argument("--head", default="HEAD")
    docs.add_argument("--require-complete", action="store_true")
    docs.add_argument("--planned-path", action="append", default=[], help="Prospective repository-relative path for pre-implementation closure review; grants no mutation authority")
    docs.add_argument("--summary-file", help="Append bounded diagnostics to a GitHub Step Summary")
    docs.add_argument("--format", choices=("yaml", "json"), default="yaml")
    matrix_sync = subs.add_parser("matrix-sync")
    matrix_sync.add_argument("--base", required=True)
    matrix_sync.add_argument("--head", default="HEAD")
    matrix_sync.add_argument("--matrix", type=Path, default=CANONICAL_MATRIX)
    matrix_sync.add_argument("--format", choices=("yaml", "json"), default="yaml")
    env = subs.add_parser("environment")
    env.add_argument("--format", choices=("yaml", "json"), default="yaml")
    post = subs.add_parser("post-merge")
    post.add_argument("--project-root", type=Path)
    post.add_argument("--remote", default="origin")
    post.add_argument("--branch", default="main")
    post.add_argument("--fetch", action="store_true")
    post.add_argument("--apply", action="store_true")
    post.add_argument("--backup-branch")
    post.add_argument("--refresh-intelligence", action="store_true")
    post.add_argument("--sync-installed", action="store_true", help="Also verify or fast-forward the registered installed AIPS checkout; never reset it")
    post.add_argument("--format", choices=("yaml", "json"), default="yaml")
    checks = subs.add_parser("checks", help="Summarize latest PR check results; this does not grant merge authority")
    checks.add_argument("--pr", required=True, type=int)
    checks.add_argument("--head")
    checks.add_argument("--required-check", action="append")
    checks.add_argument("--format", choices=("yaml", "json"), default="yaml")
    ship = subs.add_parser("ship", allow_abbrev=False, help="Personal publication: one scan, exact push, then PR create")
    ship.add_argument("--title", required=True)
    ship.add_argument("--body-file", required=True, type=Path)
    ship.add_argument("--base", required=True, help="Remote default branch the PR targets")
    ship.add_argument("--head", help="Current candidate branch; defaults to the checked-out branch")
    ship.add_argument("--format", choices=("yaml", "json"), default="yaml")
    args = parser.parse_args()
    try:
        if args.command == "doctor":
            from publication_diagnostics import doctor as publication_doctor
            result = publication_doctor(args.worktree, pr_number=args.pr, branch=args.branch,
                                        worktree_details=args.worktree_details)
            from publication_diagnostics import record_diagnostic
            for item in result.get('diagnostics', []):
                if isinstance(item, dict) and item.get('diagnostic_id'):
                    item['trace_status'] = record_diagnostic(item, 'codex')
            emit(result, args.format)
            return 0 if result["status"] == "READY" else 1
        if args.command in {"prepare", "diagnose"}:
            import publication_planning
            if args.command == "prepare":
                result = publication_planning.prepare(args.worktree, title=args.title, body_file=args.body_file,
                    runtime=args.runtime, expected_fingerprint=args.expected_fingerprint,
                    host_denied=args.host_denied, merge_intent=args.merge_intent or args.auto_merge,
                    auto_merge=args.auto_merge, host_denial_class=args.host_denial_class)
            elif args.diagnostic_id:
                from publication_diagnostics import lookup_diagnostic
                result = lookup_diagnostic(args.diagnostic_id)
            else:
                result = publication_planning.diagnose(args.worktree, args.native_command)
            if not getattr(args, 'diagnostic_id', None):
                from publication_diagnostics import record_diagnostic
                binding = result.get('candidate') if isinstance(result.get('candidate'), dict) else None
                for item in result.get('diagnostics', []):
                    if isinstance(item, dict) and item.get('diagnostic_id'):
                        item['trace_status'] = record_diagnostic(item, getattr(args, 'runtime', 'codex'), binding)
            result["recovery"] = publication_planning.recovery_guidance(result)
            emit(result, args.format)
            return 1 if result["status"] == "BLOCKED" else 0
        if args.command == "ship":
            import publication_ship
            result = publication_ship.run(Path.cwd(), {"title": args.title, "body_file": str(args.body_file),
                                                       "base": args.base, "head": args.head})
            emit(result, args.format)
            return 0 if result["status"] == "COMPLETE" else 1
        if args.command == "docs-impact":
            for planned in args.planned_path:
                if Path(planned).is_absolute() or ".." in Path(planned).parts or not planned or "\0" in planned:
                    raise PreflightError("planned documentation scope must contain safe repository-relative paths")
            base, head = resolve_commit(args.base), resolve_commit(args.head)
            files = sorted(set(changed_files(base, head)) | set(args.planned_path))
            scope = pure_dependency_update(base, head, ROOT, planned_paths=args.planned_path)
            impact = documentation_impact(files, ROOT, scope)
            impact["prospective_paths"] = args.planned_path
            emit(impact, args.format)
            if args.summary_file:
                with Path(args.summary_file).open("a", encoding="utf-8") as summary:
                    exemption = impact.get("dependency_update_exemption") or {}
                    summary.write("Documentation impact: " + ("PASS" if impact["complete"] else "FAIL")
                                  + (" (pure dependency update exemption)" if exemption.get("applied") else "") + "\n")
                    # Package/action names are regex-constrained to [A-Za-z0-9._/-].
                    summary.writelines(
                        f"- Dependency: {item['name']} {item['current_version']} -> {item['target_version']}"
                        f" ({item['classification']}/{item['risk']})\n"
                        for item in (exemption.get("items") or [])[:40] if exemption.get("applied")
                    )
                    # Repository-controlled paths are rendered as plain text.
                    summary.writelines(
                        "- Required: " + str(path).replace("\n", " ").replace("\r", " ") + "\n"
                        for path in impact["required_additions"][:40]
                    )
                    if len(impact["required_additions"]) > 40:
                        summary.write("- Additional paths omitted; inspect the full precheck report.\n")
            return 0 if impact["complete"] or not args.require_complete else 1
        if args.command == "checks":
            result = check_status(args)
            emit(result, args.format)
            return 0 if result["status"] == "PASS" else 1
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
        if args.command == "preview":
            result = preview_candidate(args)
            emit(result, args.format)
            return 0
        if args.command == "matrix-sync":
            result = sync_matrix_binding(args.base, args.head, args.matrix)
            emit(result, args.format)
            return 0
        return run_candidate(args)
    except (OSError, ValueError, PreflightError) as exc:
        if args.command in {"prepare", "diagnose"} and args.format == "json":
            emit(cli_exception_result(exc), "json")
        else:
            print(f"PUBLISH PREFLIGHT ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

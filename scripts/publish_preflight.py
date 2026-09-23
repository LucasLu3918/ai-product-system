#!/usr/bin/env python3
"""Resolve and validate the same exact publication candidate locally and in CI."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

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


def worktree_changed_files(base: str) -> list[str]:
    tracked = git("diff", "--name-only", base, "--")
    untracked = git("ls-files", "--others", "--exclude-standard")
    return sorted({item for item in (*tracked.splitlines(), *untracked.splitlines()) if item})


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
    required_by: dict[str, set[str]] = {}
    placement_hits = []
    for rule in placement.get("placement_rules") or []:
        patterns = [str(item) for item in rule.get("triggers") or []]
        if not matches(files, patterns):
            continue
        placements = rule.get("placements") or {}
        placement_hits.append({"id": rule.get("id"), "placements": placements})
        for path in placements:
            target = str(path)
            required_by.setdefault(target, set()).add(f"placement:{rule.get('id')}")
            closure.add(target)
    changed = True
    while changed:
        changed = False
        current = sorted(closure)
        technology = sync.get("technology_guide") or {}
        if matches(current, [str(item) for item in technology.get("triggers") or []]):
            target = str(technology.get("path") or "")
            if target:
                required_by.setdefault(target, set()).add("technology-guide")
                if target not in closure:
                    closure.add(target)
                    changed = True
        for rule in sync.get("rules") or []:
            patterns = [str(item) for item in rule.get("triggers") or []]
            if not matches(current, patterns):
                continue
            required = [str(item) for item in (rule.get("human_docs") or []) + (rule.get("agent_docs") or [])]
            triggered.setdefault(str(rule.get("id")), {"required": required})
            for path in required:
                required_by.setdefault(path, set()).add(f"sync:{rule.get('id')}")
            before = len(closure)
            closure.update(required)
            changed = changed or len(closure) != before
    required = sorted(closure - set(files))
    return {
        "changed_files": files,
        "triggered_rules": triggered,
        "required_additions": required,
        "required_by": {path: sorted(required_by.get(path, set())) for path in required},
        "complete": not required,
        "placement_rules": placement_hits,
    }


def environment_status() -> dict[str, Any]:
    blockers: list[str] = []
    diagnostics: list[dict[str, str]] = []
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
    selection = discover_browser()
    browser_probe = probe_browser(selection.get("path"), provider=str(selection["provider"]))
    if browser_probe["status"] != "READY":
        blockers.append(f"browser:{browser_probe['status']}")
        if browser_probe["status"] == "BROWSER_NOT_FOUND":
            next_step = "Install Playwright Chromium with `python -m playwright install chromium`, or configure a supported Chrome/Chromium binary."
        elif browser_probe["status"] == "BROWSER_PROBE_DEPENDENCY_MISSING":
            next_step = "Install project validation dependencies, then rerun `aips publish environment`."
        else:
            next_step = "Inspect the browser probe stderr and retry with the managed Playwright browser; classify launch permission failures as environment blockers."
        diagnostics.append({
            "check": "browser_probe",
            "status": str(browser_probe["status"]),
            "detail": str(browser_probe.get("stderr") or browser_probe.get("path") or "browser unavailable"),
            "next_step": next_step,
        })
    return {
        "status": "READY" if not blockers else "ENVIRONMENT_BLOCKED",
        "localhost": localhost,
        "browser": browser_probe,
        "blockers": blockers,
        "diagnostics": diagnostics,
    }


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
    docs = documentation_impact(files)
    matrix_hash = canonical_hash(files)
    binding: dict[str, Any] = {"required": required, "path": str(matrix_path), "changed_files_hash": matrix_hash}
    if required and matrix_path.is_file():
        matrix = yaml.safe_load(matrix_path.read_text(encoding="utf-8")) or {}
        candidate = matrix.get("candidate") or {}
        binding.update({
            "base_matches": candidate.get("base_sha") == base,
            "hash_matches": candidate.get("changed_files_hash") == matrix_hash,
            "bound_base": candidate.get("base_sha"),
            "bound_hash": candidate.get("changed_files_hash"),
        })
    else:
        binding["base_matches"] = not required
        binding["hash_matches"] = not required
    pending = list(docs["required_additions"])
    if required and not matrix_path.is_file():
        pending.append("canonical Core Change Test Matrix is missing")
    if required and (not binding.get("base_matches") or not binding.get("hash_matches")):
        pending.append("Core Change Test Matrix binding needs synchronization")
    return {
        "version": 1,
        "status": "READY_FOR_GATE" if not pending else "NEEDS_WORK",
        "preview": True,
        "candidate": {"base": base, "head": head, "working_tree_included": True, "changed_files": files},
        "change_class": change_class,
        "change_class_warning": warning,
        "documentation": docs,
        "matrix": binding,
        "pending": pending,
        "note": "Preview includes committed, staged, unstaged and untracked paths; final Integration Gate still requires a clean committed candidate.",
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
                text = populated.sub(lambda match: match.group(0) + f"  - {reminder}\n", text, count=1)
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
        return {"status": "UNAVAILABLE", "reason": "GitHub CLI or GitHub origin unavailable"}
    path = remote.removeprefix("git@github.com:").removeprefix("https://github.com/").removesuffix(".git")
    proc = subprocess.run([gh, "api", f"repos/{path}/branches/{branch}/protection"], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode == 0:
        return {"status": "PROTECTED", "publication_route": "pull_request"}
    if "Branch not protected" in proc.stderr or "404" in proc.stderr:
        return {"status": "UNPROTECTED", "publication_route": "direct_or_pull_request"}
    return {"status": "UNAVAILABLE", "reason": proc.stderr.strip() or "protection query failed"}


def content_safety_plan(args: argparse.Namespace, base: str, head: str) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(sink: str, payload: Any, label: str) -> None:
        result = safe_emit(sink=sink, payload=payload)
        checks.append({"label": label, "sink": sink, "decision": result["decision"], "findings": result["findings"]})

    check("git_commit", git("log", "-1", "--format=%B", head), "commit_message")
    diff = git("diff", "--no-ext-diff", "--unified=0", base, head)
    check("source_artifact", diff, "candidate_diff")
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
    safety = content_safety_plan(args, base, head)
    blockers.extend(safety["blockers"])
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
        "content_safety": safety,
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
    parser.add_argument("--commit-message")
    parser.add_argument("--body")
    parser.add_argument("--body-file")
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")


def main() -> int:
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command", required=True)
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
    docs.add_argument("--format", choices=("yaml", "json"), default="yaml")
    matrix_sync = subs.add_parser("matrix-sync")
    matrix_sync.add_argument("--base", required=True)
    matrix_sync.add_argument("--head", default="HEAD")
    matrix_sync.add_argument("--matrix", type=Path, default=CANONICAL_MATRIX)
    matrix_sync.add_argument("--format", choices=("yaml", "json"), default="yaml")
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
        print(f"PUBLISH PREFLIGHT ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

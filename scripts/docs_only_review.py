"""Opt-in, read-only docs-only classification derived from the actual Git worktree."""
from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

DOC_EXTENSIONS = {".md", ".markdown", ".rst"}
ROOT_DOCS = {"README.md", "CHANGELOG.md"}
REQUIRED_CHECKS = ["git_diff_check", "markdown_path_check", "secret_scan", "approval_and_reconciliation"]
MAX_IGNORED_PATHS = 200


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=10, check=False)
    if result.returncode:
        raise OSError("Git status is unavailable")
    return result.stdout


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _path_safety(root: Path, relative: str) -> str | None:
    candidate = root / relative
    try:
        resolved = candidate.resolve(strict=False)
    except OSError:
        return "PATH_CANONICALIZATION_FAILED"
    if not _inside(resolved, root):
        return "PATH_OUTSIDE_REPOSITORY"
    cursor = root
    try:
        for component in PurePosixPath(relative).parts:
            if component in {"", ".", ".."}:
                return "PATH_TRAVERSAL"
            cursor = cursor / component
            try:
                info = cursor.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(info.st_mode) and not _inside(cursor.resolve(strict=False), root):
                return "PATH_OUTSIDE_REPOSITORY"
    except OSError:
        return "PATH_CANONICALIZATION_FAILED"
    return None


def _is_document_path(relative: str) -> bool:
    posix = PurePosixPath(relative)
    if relative in ROOT_DOCS:
        return True
    if not relative.startswith("docs/") or posix.suffix.lower() not in DOC_EXTENSIONS:
        return False
    return not relative.startswith(("docs/qa/", "docs/history/"))


def _parse_status(data: bytes) -> tuple[list[str], list[str] | None]:
    fields = data.split(b"\0")
    changed: list[str] = []
    for raw in fields:
        if not raw:
            continue
        status = raw[:2]
        if b"R" in status or b"C" in status:
            return [], None
        path = os.fsdecode(raw[3:])
        changed.append(path)
    return sorted(set(changed)), changed


def review(project: Path | str, *, opt_in: bool = False) -> dict[str, Any]:
    """Classify only a user-requested Git diff; never makes approval or test-scope claims."""
    if not opt_in:
        return {"version": 1, "status": "OPT_IN_REQUIRED", "classification": "NOT_EVALUATED",
                "docs_only": False, "reason_code": "OPT_IN_REQUIRED", "required_checks": REQUIRED_CHECKS}
    requested = Path(project).expanduser().resolve(strict=True)
    if not requested.is_dir():
        return {"version": 1, "status": "NOT_DOCS_ONLY", "classification": "NOT_DOCS_ONLY",
                "docs_only": False, "reason_code": "PROJECT_NOT_DIRECTORY", "required_checks": REQUIRED_CHECKS}
    try:
        root = Path(os.fsdecode(_git(requested, "rev-parse", "--show-toplevel")).strip()).resolve(strict=True)
        status = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
        changed, raw_changed = _parse_status(status)
        ignored = sorted(os.fsdecode(item) for item in _git(
            root, "ls-files", "--others", "--ignored", "--exclude-standard", "-z").split(b"\0") if item)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return {"version": 1, "status": "NOT_DOCS_ONLY", "classification": "NOT_DOCS_ONLY",
                "docs_only": False, "reason_code": "GIT_STATE_UNAVAILABLE", "required_checks": REQUIRED_CHECKS}
    if raw_changed is None:
        return {"version": 1, "status": "NOT_DOCS_ONLY", "classification": "NOT_DOCS_ONLY",
                "docs_only": False, "reason_code": "RENAME_OR_COPY_REQUIRES_FULL_REVIEW", "required_checks": REQUIRED_CHECKS}
    if not changed:
        return {"version": 1, "status": "NO_CHANGES", "classification": "NOT_DOCS_ONLY", "docs_only": False,
                "reason_code": "NO_CHANGES", "changed_files": [], "ignored_paths": ignored[:MAX_IGNORED_PATHS],
                "ignored_paths_truncated": len(ignored) > MAX_IGNORED_PATHS, "required_checks": REQUIRED_CHECKS}
    rejected: list[str] = []
    reason = None
    for relative in changed:
        path_reason = _path_safety(root, relative)
        if path_reason:
            rejected.append(relative)
            reason = path_reason
        elif not _is_document_path(relative):
            rejected.append(relative)
            reason = "NON_DOCUMENT_OR_PROTECTED_PATH"
    if rejected:
        return {"version": 1, "status": "NOT_DOCS_ONLY", "classification": "NOT_DOCS_ONLY", "docs_only": False,
                "reason_code": reason or "NON_DOCUMENT_OR_PROTECTED_PATH", "changed_files": changed,
                "rejected_paths": sorted(rejected), "ignored_paths": ignored[:MAX_IGNORED_PATHS],
                "ignored_paths_truncated": len(ignored) > MAX_IGNORED_PATHS, "required_checks": REQUIRED_CHECKS}
    return {"version": 1, "status": "DOCS_ONLY_REVIEW_ONLY", "classification": "DOCS_ONLY", "docs_only": True,
            "derived_from": "git_status_and_canonical_paths", "changed_files": changed,
            "ignored_paths": ignored[:MAX_IGNORED_PATHS], "ignored_paths_truncated": len(ignored) > MAX_IGNORED_PATHS,
            "required_checks": REQUIRED_CHECKS}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify the actual worktree as docs-only; this never grants approval or skips checks")
    parser.add_argument("review", choices=("review",))
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--opt-in", action="store_true", help="explicitly request a read-only docs-only classification")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    result = review(args.project, opt_in=args.opt_in)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(f"Docs-only classification: {result['classification']} ({result['reason_code'] if 'reason_code' in result else result['status']})")
        if result.get("changed_files"):
            print("Changed documentation paths were derived from Git status; required checks remain: " + ", ".join(result['required_checks']))
    return 0 if result.get("docs_only") else 2


if __name__ == "__main__":
    raise SystemExit(main())

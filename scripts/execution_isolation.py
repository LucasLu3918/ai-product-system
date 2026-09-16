#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

import yaml

from aips_identity import (
    config_home,
    project_root as canonical_project_root,
    repository_identity,
)

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_git(root: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def project_root(path: Path) -> Path:
    root = canonical_project_root(path)
    result = run_git(root, "rev-parse", "--show-toplevel")
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError("project is not a Git repository")
    return Path(result.stdout.strip()).resolve()


def state_dir(root: Path) -> Path:
    return config_home() / "isolation" / repository_identity(root)["repository_id"]


def worktree_dir(root: Path) -> Path:
    return config_home() / "worktrees" / repository_identity(root)["repository_id"]


def atomic_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def validate_id(value: str, label: str) -> str:
    if not ID_RE.fullmatch(value):
        raise ValueError(f"{label} must match {ID_RE.pattern}")
    return value


def worktree_supported(root: Path) -> bool:
    result = run_git(root, "worktree", "list", "--porcelain")
    return result.returncode == 0


def _record_repository_id(record: dict[str, Any]) -> str | None:
    explicit = record.get("repository_id")
    if explicit:
        return str(explicit)
    raw_root = record.get("project_root")
    if not raw_root:
        return None
    candidate = Path(str(raw_root))
    if not candidate.exists():
        return None
    try:
        return repository_identity(project_root(candidate))["repository_id"]
    except Exception:
        return None


def _record_paths(root: Path) -> list[Path]:
    repo_id = repository_identity(root)["repository_id"]
    base = config_home() / "isolation"
    if not base.exists():
        return []
    result: list[Path] = []
    for path in sorted(base.glob("*/*.yaml")):
        doc = load_yaml(path)
        if doc.get("ownership") != "aips":
            continue
        if _record_repository_id(doc) == repo_id:
            result.append(path)
    return result


def records(root: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for path in _record_paths(root):
        doc = load_yaml(path)
        doc["_record_path"] = str(path)
        result.append(doc)
    return result


def active_records(root: Path) -> list[dict[str, Any]]:
    return [doc for doc in records(root) if doc.get("status") == "ACTIVE"]


def resolve_mode(args: argparse.Namespace) -> dict[str, Any]:
    root = project_root(Path(args.project))
    ident = repository_identity(root)
    base = {
        "project_root": str(root),
        "repository_id": ident["repository_id"],
        "workspace_id": ident["workspace_id"],
    }
    if args.mode == "shared":
        return {
            **base,
            "mode": "shared",
            "status": "AVAILABLE",
            "isolated": False,
            "reason": "shared uses the existing project workspace and does not provide an isolation boundary",
        }
    if args.mode == "worktree":
        available = worktree_supported(root)
        return {
            **base,
            "mode": "worktree",
            "status": "AVAILABLE" if available else "UNSUPPORTED",
            "isolated": available,
            "reason": "git worktree is available" if available else "git worktree is unavailable for this repository/runtime",
        }
    return {
        **base,
        "mode": "sandbox",
        "status": "UNSUPPORTED",
        "isolated": False,
        "reason": "no verified sandbox provider is registered; AIPS core does not emulate sandbox isolation with a temporary directory",
        "requires_provider": True,
    }


def create_worktree(args: argparse.Namespace) -> dict[str, Any]:
    root = project_root(Path(args.project))
    isolation_id = validate_id(args.id, "id")
    boundary = validate_id(args.boundary, "boundary")
    ident = repository_identity(root)
    if not worktree_supported(root):
        raise RuntimeError("git worktree is unavailable")

    for record in active_records(root):
        if record.get("boundary_id") == boundary:
            raise RuntimeError(
                f"single-writer boundary is already owned by active isolation {record.get('id')}"
            )
    if any(record.get("id") == isolation_id for record in records(root)):
        raise RuntimeError(f"isolation record already exists: {isolation_id}")

    record_path = state_dir(root) / f"{isolation_id}.yaml"
    target = worktree_dir(root) / isolation_id
    if target.exists():
        raise RuntimeError(f"managed worktree path already exists: {target}")

    branch = f"aips/isolation/{isolation_id}"
    branch_check = run_git(root, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}")
    if branch_check.returncode == 0:
        raise RuntimeError(f"managed branch already exists: {branch}")

    base_ref = args.ref or "HEAD"
    target.parent.mkdir(parents=True, exist_ok=True)
    created = run_git(root, "worktree", "add", "-b", branch, str(target), base_ref)
    if created.returncode != 0:
        raise RuntimeError((created.stderr or created.stdout).strip() or "git worktree add failed")

    target_ident = repository_identity(target)
    base_revision = run_git(target, "rev-parse", "HEAD")
    record = {
        "version": 2,
        "id": isolation_id,
        "mode": "worktree",
        "status": "ACTIVE",
        "ownership": "aips",
        "project_root": str(root),
        "repository_id": ident["repository_id"],
        "base_workspace_id": ident["workspace_id"],
        "workspace_id": target_ident["workspace_id"],
        "project_id": target_ident["workspace_id"],
        "boundary_id": boundary,
        "path": str(target),
        "branch": branch,
        "base_ref": base_ref,
        "base_revision": base_revision.stdout.strip() if base_revision.returncode == 0 else None,
        "created_at": now(),
        "updated_at": now(),
    }
    atomic_yaml(record_path, record)
    return {
        "status": "ACTIVE",
        "mode": "worktree",
        "id": isolation_id,
        "repository_id": ident["repository_id"],
        "workspace_id": target_ident["workspace_id"],
        "boundary_id": boundary,
        "path": str(target),
        "branch": branch,
        "record": str(record_path),
    }


def create_isolation(args: argparse.Namespace) -> dict[str, Any]:
    if args.mode == "sandbox":
        root = project_root(Path(args.project))
        ident = repository_identity(root)
        return {
            "status": "BLOCKED",
            "mode": "sandbox",
            "project_root": str(root),
            "repository_id": ident["repository_id"],
            "workspace_id": ident["workspace_id"],
            "reason": "no verified sandbox provider is registered",
            "requires_provider": True,
        }
    return create_worktree(args)


def record_for(root: Path, isolation_id: str) -> tuple[Path, dict[str, Any]]:
    isolation_id = validate_id(isolation_id, "id")
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in _record_paths(root):
        doc = load_yaml(path)
        if doc.get("id") == isolation_id:
            matches.append((path, doc))
    if not matches:
        raise RuntimeError(f"isolation record not found: {isolation_id}")
    if len(matches) > 1:
        raise RuntimeError(f"multiple AIPS isolation records found for id: {isolation_id}")
    return matches[0]


def status_isolation(args: argparse.Namespace) -> dict[str, Any]:
    root = project_root(Path(args.project))
    path, record = record_for(root, args.id)
    if record.get("ownership") != "aips":
        raise RuntimeError("isolation record is not AIPS-owned")
    target = Path(str(record.get("path", "")))
    exists = target.is_dir()
    clean: bool | None = None
    revision: str | None = None
    current_workspace_id: str | None = None
    if exists:
        stat = run_git(target, "status", "--porcelain")
        clean = stat.returncode == 0 and not stat.stdout.strip()
        rev = run_git(target, "rev-parse", "HEAD")
        revision = rev.stdout.strip() if rev.returncode == 0 else None
        try:
            current_workspace_id = repository_identity(target)["workspace_id"]
        except Exception:
            current_workspace_id = None
    return {
        "status": record.get("status"),
        "mode": record.get("mode"),
        "id": record.get("id"),
        "repository_id": repository_identity(root)["repository_id"],
        "workspace_id": record.get("workspace_id") or current_workspace_id,
        "boundary_id": record.get("boundary_id"),
        "path": str(target),
        "branch": record.get("branch"),
        "exists": exists,
        "clean": clean,
        "revision": revision,
        "record": str(path),
    }


def _registered_worktrees(root: Path) -> set[Path]:
    result = run_git(root, "worktree", "list", "--porcelain")
    if result.returncode != 0:
        return set()
    paths: set[Path] = set()
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            paths.add(Path(line.split(" ", 1)[1]).resolve())
    return paths


def remove_isolation(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    root = project_root(Path(args.project))
    path, record = record_for(root, args.id)
    if record.get("ownership") != "aips" or record.get("mode") != "worktree":
        raise RuntimeError("only AIPS-owned worktree isolation may be removed")
    if _record_repository_id(record) != repository_identity(root)["repository_id"]:
        raise RuntimeError("isolation record does not belong to this repository")

    target = Path(str(record.get("path", ""))).resolve()
    global_managed_root = (config_home() / "worktrees").resolve()
    try:
        target.relative_to(global_managed_root)
    except ValueError as exc:
        raise RuntimeError("refusing to remove worktree outside AIPS-managed roots") from exc

    if target.exists():
        if target not in _registered_worktrees(root):
            raise RuntimeError("managed path is not a registered Git worktree")
        stat = run_git(target, "status", "--porcelain")
        if stat.returncode != 0:
            raise RuntimeError("cannot verify worktree cleanliness")
        if stat.stdout.strip():
            return ({
                "status": "BLOCKED",
                "mode": "worktree",
                "id": record.get("id"),
                "path": str(target),
                "reason": "worktree has uncommitted changes; cleanup preserved it",
            }, 2)
        removed = run_git(root, "worktree", "remove", str(target))
        if removed.returncode != 0:
            raise RuntimeError((removed.stderr or removed.stdout).strip() or "git worktree remove failed")

    record["version"] = max(int(record.get("version") or 1), 2)
    record["repository_id"] = repository_identity(root)["repository_id"]
    record["status"] = "REMOVED"
    record["removed_at"] = now()
    record["updated_at"] = now()
    atomic_yaml(path, record)
    return ({
        "status": "REMOVED",
        "mode": "worktree",
        "id": record.get("id"),
        "path": str(target),
        "branch": record.get("branch"),
        "branch_preserved": True,
        "record": str(path),
    }, 0)


def output(data: dict[str, Any], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip())


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project", default=os.getcwd())
    parser.add_argument("--format", choices=["yaml", "json"], default="yaml")


def main() -> int:
    parser = argparse.ArgumentParser(description="AIPS execution isolation helper")
    sub = parser.add_subparsers(dest="command", required=True)

    resolve = sub.add_parser("resolve")
    add_common(resolve)
    resolve.add_argument("--mode", choices=["shared", "worktree", "sandbox"], required=True)

    create = sub.add_parser("create")
    add_common(create)
    create.add_argument("--mode", choices=["worktree", "sandbox"], default="worktree")
    create.add_argument("--id", required=True)
    create.add_argument("--boundary", required=True)
    create.add_argument("--ref")

    status = sub.add_parser("status")
    add_common(status)
    status.add_argument("--id", required=True)

    remove = sub.add_parser("remove")
    add_common(remove)
    remove.add_argument("--id", required=True)

    args = parser.parse_args()
    exit_code = 0
    try:
        if args.command == "resolve":
            data = resolve_mode(args)
        elif args.command == "create":
            data = create_isolation(args)
            if data.get("status") == "BLOCKED":
                exit_code = 2
        elif args.command == "status":
            data = status_isolation(args)
        else:
            data, exit_code = remove_isolation(args)
    except (RuntimeError, OSError, ValueError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    output(data, args.format)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

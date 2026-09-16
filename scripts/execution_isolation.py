#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

import yaml

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
    path = path.resolve()
    result = run_git(path, "rev-parse", "--show-toplevel")
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError("project is not a Git repository")
    return Path(result.stdout.strip()).resolve()


def project_id(root: Path) -> str:
    return hashlib.sha256(str(root).encode()).hexdigest()[:20]


def config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))).resolve() / "aips"


def state_dir(root: Path) -> Path:
    return config_home() / "isolation" / project_id(root)


def worktree_dir(root: Path) -> Path:
    return config_home() / "worktrees" / project_id(root)


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


def resolve_mode(args: argparse.Namespace) -> dict[str, Any]:
    root = project_root(Path(args.project))
    if args.mode == "shared":
        return {
            "mode": "shared",
            "status": "AVAILABLE",
            "isolated": False,
            "project_root": str(root),
            "reason": "shared uses the existing project workspace and does not provide an isolation boundary",
        }
    if args.mode == "worktree":
        available = worktree_supported(root)
        return {
            "mode": "worktree",
            "status": "AVAILABLE" if available else "UNSUPPORTED",
            "isolated": available,
            "project_root": str(root),
            "reason": "git worktree is available" if available else "git worktree is unavailable for this repository/runtime",
        }
    return {
        "mode": "sandbox",
        "status": "UNSUPPORTED",
        "isolated": False,
        "project_root": str(root),
        "reason": "no verified sandbox provider is registered; AIPS core does not emulate sandbox isolation with a temporary directory",
        "requires_provider": True,
    }


def active_records(root: Path) -> list[dict[str, Any]]:
    directory = state_dir(root)
    if not directory.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.yaml")):
        doc = load_yaml(path)
        if doc.get("status") == "ACTIVE" and doc.get("ownership") == "aips":
            doc["_record_path"] = str(path)
            records.append(doc)
    return records


def create_worktree(args: argparse.Namespace) -> dict[str, Any]:
    root = project_root(Path(args.project))
    isolation_id = validate_id(args.id, "id")
    boundary = validate_id(args.boundary, "boundary")
    if not worktree_supported(root):
        raise RuntimeError("git worktree is unavailable")

    for record in active_records(root):
        if record.get("boundary_id") == boundary:
            raise RuntimeError(
                f"single-writer boundary is already owned by active isolation {record.get('id')}"
            )

    record_path = state_dir(root) / f"{isolation_id}.yaml"
    if record_path.exists():
        raise RuntimeError(f"isolation record already exists: {isolation_id}")

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

    base_revision = run_git(target, "rev-parse", "HEAD")
    record = {
        "version": 1,
        "id": isolation_id,
        "mode": "worktree",
        "status": "ACTIVE",
        "ownership": "aips",
        "project_root": str(root),
        "project_id": project_id(root),
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
        "boundary_id": boundary,
        "path": str(target),
        "branch": branch,
        "record": str(record_path),
    }


def create_isolation(args: argparse.Namespace) -> dict[str, Any]:
    if args.mode == "sandbox":
        root = project_root(Path(args.project))
        return {
            "status": "BLOCKED",
            "mode": "sandbox",
            "project_root": str(root),
            "reason": "no verified sandbox provider is registered",
            "requires_provider": True,
        }
    return create_worktree(args)


def record_for(root: Path, isolation_id: str) -> tuple[Path, dict[str, Any]]:
    isolation_id = validate_id(isolation_id, "id")
    path = state_dir(root) / f"{isolation_id}.yaml"
    if not path.exists():
        raise RuntimeError(f"isolation record not found: {isolation_id}")
    return path, load_yaml(path)


def status_isolation(args: argparse.Namespace) -> dict[str, Any]:
    root = project_root(Path(args.project))
    path, record = record_for(root, args.id)
    if record.get("ownership") != "aips":
        raise RuntimeError("isolation record is not AIPS-owned")
    target = Path(str(record.get("path", "")))
    exists = target.is_dir()
    clean: bool | None = None
    revision: str | None = None
    if exists:
        stat = run_git(target, "status", "--porcelain")
        clean = stat.returncode == 0 and not stat.stdout.strip()
        rev = run_git(target, "rev-parse", "HEAD")
        revision = rev.stdout.strip() if rev.returncode == 0 else None
    return {
        "status": record.get("status"),
        "mode": record.get("mode"),
        "id": record.get("id"),
        "boundary_id": record.get("boundary_id"),
        "path": str(target),
        "branch": record.get("branch"),
        "exists": exists,
        "clean": clean,
        "revision": revision,
        "record": str(path),
    }


def remove_isolation(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    root = project_root(Path(args.project))
    path, record = record_for(root, args.id)
    if record.get("ownership") != "aips" or record.get("mode") != "worktree":
        raise RuntimeError("only AIPS-owned worktree isolation may be removed")

    target = Path(str(record.get("path", ""))).resolve()
    managed_root = worktree_dir(root).resolve()
    try:
        target.relative_to(managed_root)
    except ValueError as exc:
        raise RuntimeError("refusing to remove worktree outside AIPS-managed root") from exc

    if target.exists():
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

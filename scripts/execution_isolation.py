#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time
from typing import Any

import yaml

from aips_identity import (
    config_home,
    project_root as canonical_project_root,
    repository_identity,
)

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
ENV_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DEFAULT_PORT_START = 31000
DEFAULT_PORT_END = 31999
DEFAULT_MAX_ATTEMPTS = 128
LOCK_TIMEOUT_SECONDS = 5.0
LOCK_STALE_SECONDS = 30.0


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


def runtime_dir(root: Path) -> Path:
    return config_home() / "runtime" / repository_identity(root)["repository_id"]


def port_registry_path(root: Path) -> Path:
    return runtime_dir(root) / "ports.yaml"


def port_lock_path(root: Path) -> Path:
    return runtime_dir(root) / ".ports.lock"


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


def validate_env(value: str) -> str:
    if not ENV_RE.fullmatch(value):
        raise ValueError(f"environment variable must match {ENV_RE.pattern}")
    return value


def validate_port(value: int, label: str) -> int:
    if value < 1024 or value > 65535:
        raise ValueError(f"{label} must be between 1024 and 65535")
    return value


def validate_port_range(start: int, end: int) -> tuple[int, int]:
    validate_port(start, "port-start")
    validate_port(end, "port-end")
    if start > end:
        raise ValueError("port-start must be <= port-end")
    return start, end


class RuntimeRegistryLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.acquired = False

    def __enter__(self) -> RuntimeRegistryLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
        while True:
            try:
                os.mkdir(self.path)
                self.acquired = True
                return self
            except FileExistsError:
                try:
                    age = time.time() - self.path.stat().st_mtime
                    if age >= LOCK_STALE_SECONDS:
                        self.path.rmdir()
                        continue
                except (FileNotFoundError, OSError):
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError("runtime port registry lock timeout")
                time.sleep(0.05)

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self.acquired:
            try:
                self.path.rmdir()
            except FileNotFoundError:
                pass
            self.acquired = False


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
        "version": 3,
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
        "runtime": {
            "environment_id": isolation_id,
            "ports": {},
            "environment": {"AIPS_ISOLATION_ID": isolation_id},
        },
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
        "runtime": record["runtime"],
    }


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


def _load_port_registry(root: Path) -> dict[str, Any]:
    path = port_registry_path(root)
    if not path.exists():
        return {"version": 1, "leases": []}
    doc = load_yaml(path)
    if doc.get("version") != 1 or not isinstance(doc.get("leases"), list):
        raise RuntimeError("invalid runtime port registry")
    return doc


def _write_port_registry(root: Path, leases: list[dict[str, Any]]) -> None:
    ordered = sorted(
        leases,
        key=lambda item: (
            int(item.get("port") or 0),
            str(item.get("isolation_id") or ""),
            str(item.get("resource_id") or ""),
        ),
    )
    atomic_yaml(port_registry_path(root), {"version": 1, "leases": ordered})


def _env_key(resource_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "_", resource_id).upper()


def _runtime_environment(isolation_id: str, leases: list[dict[str, Any]]) -> dict[str, str]:
    env: dict[str, str] = {"AIPS_ISOLATION_ID": isolation_id}
    ordered = sorted(leases, key=lambda item: str(item["resource_id"]))
    for lease in ordered:
        resource_id = str(lease["resource_id"])
        value = str(lease["port"])
        env[f"AIPS_PORT_{_env_key(resource_id)}"] = value
        for name in lease.get("expose_as") or []:
            env[str(name)] = value
    if len(ordered) == 1:
        env["AIPS_PORT"] = str(ordered[0]["port"])
    return env


def _runtime_snapshot(isolation_id: str, leases: list[dict[str, Any]]) -> dict[str, Any]:
    mine = sorted(
        [item for item in leases if item.get("isolation_id") == isolation_id],
        key=lambda item: str(item["resource_id"]),
    )
    ports = {
        str(item["resource_id"]): {
            "protocol": "tcp",
            "port": int(item["port"]),
            "status": "LEASED",
            "preferred": item.get("preferred"),
            "expose_as": list(item.get("expose_as") or []),
        }
        for item in mine
    }
    return {
        "environment_id": isolation_id,
        "ports": ports,
        "environment": _runtime_environment(isolation_id, mine),
    }


def _sync_runtime_record(root: Path, isolation_id: str, leases: list[dict[str, Any]]) -> None:
    path, record = record_for(root, isolation_id)
    record["version"] = max(int(record.get("version") or 1), 3)
    record["runtime"] = _runtime_snapshot(isolation_id, leases)
    record["updated_at"] = now()
    atomic_yaml(path, record)


def _port_available(port: int) -> bool:
    probes: list[tuple[int, tuple[Any, ...]]] = [
        (socket.AF_INET, ("0.0.0.0", port)),
    ]
    if socket.has_ipv6:
        probes.append((socket.AF_INET6, ("::", port, 0, 0)))
    for family, address in probes:
        sock = socket.socket(family, socket.SOCK_STREAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
            sock.bind(address)
        except OSError:
            return False
        finally:
            sock.close()
    return True


def _candidate_ports(
    repository_id: str,
    isolation_id: str,
    resource_id: str,
    start: int,
    end: int,
    preferred: int | None,
) -> list[int]:
    result: list[int] = []
    if preferred is not None:
        result.append(preferred)
    span = end - start + 1
    seed = int(
        hashlib.sha256(f"{repository_id}:{isolation_id}:{resource_id}".encode("utf-8")).hexdigest(),
        16,
    ) % span
    for offset in range(span):
        candidate = start + ((seed + offset) % span)
        if candidate not in result:
            result.append(candidate)
    return result


def _assert_active_record(root: Path, isolation_id: str) -> dict[str, Any]:
    _, record = record_for(root, isolation_id)
    if record.get("ownership") != "aips" or record.get("status") != "ACTIVE":
        raise RuntimeError("runtime resources require an ACTIVE AIPS-owned isolation")
    return record


def _lease_port(
    root: Path,
    isolation_id: str,
    resource_id: str,
    *,
    preferred: int | None,
    expose_as: list[str],
    port_start: int,
    port_end: int,
    max_attempts: int,
    reallocate: bool,
) -> dict[str, Any]:
    isolation_id = validate_id(isolation_id, "id")
    resource_id = validate_id(resource_id, "port")
    expose = sorted({validate_env(item) for item in expose_as})
    validate_port_range(port_start, port_end)
    if preferred is not None:
        validate_port(preferred, "preferred")
    if max_attempts < 1:
        raise ValueError("max-attempts must be >= 1")
    _assert_active_record(root, isolation_id)
    repo_id = repository_identity(root)["repository_id"]

    with RuntimeRegistryLock(port_lock_path(root)):
        registry = _load_port_registry(root)
        leases = list(registry["leases"])
        existing = next(
            (
                item
                for item in leases
                if item.get("isolation_id") == isolation_id and item.get("resource_id") == resource_id
            ),
            None,
        )
        if existing is not None and not reallocate:
            existing["expose_as"] = sorted(set(existing.get("expose_as") or []) | set(expose))
            _write_port_registry(root, leases)
            _sync_runtime_record(root, isolation_id, leases)
            return {
                "status": "LEASED",
                "id": isolation_id,
                "resource_id": resource_id,
                "port": int(existing["port"]),
                "protocol": "tcp",
                "reused": True,
                "runtime": _runtime_snapshot(isolation_id, leases),
            }

        excluded: set[int] = set()
        if existing is not None:
            excluded.add(int(existing["port"]))
            leases.remove(existing)
        used = {int(item["port"]) for item in leases}
        selected: int | None = None
        attempts = 0
        for candidate in _candidate_ports(repo_id, isolation_id, resource_id, port_start, port_end, preferred):
            if candidate in excluded or candidate in used:
                continue
            attempts += 1
            if attempts > max_attempts:
                break
            if not _port_available(candidate):
                continue
            selected = candidate
            break
        if selected is None:
            raise RuntimeError("no available TCP port found within bounded allocation attempts")

        lease = {
            "port": selected,
            "protocol": "tcp",
            "repository_id": repo_id,
            "isolation_id": isolation_id,
            "resource_id": resource_id,
            "preferred": preferred,
            "expose_as": expose,
            "allocated_at": now(),
        }
        leases.append(lease)
        _write_port_registry(root, leases)
        _sync_runtime_record(root, isolation_id, leases)
        return {
            "status": "LEASED",
            "id": isolation_id,
            "resource_id": resource_id,
            "port": selected,
            "protocol": "tcp",
            "reused": False,
            "reallocated_from": int(existing["port"]) if existing is not None else None,
            "attempts": attempts,
            "runtime": _runtime_snapshot(isolation_id, leases),
        }


def runtime_lease(args: argparse.Namespace, *, reallocate: bool = False) -> dict[str, Any]:
    root = project_root(Path(args.project))
    return _lease_port(
        root,
        args.id,
        args.port,
        preferred=args.preferred,
        expose_as=list(args.expose or []),
        port_start=args.port_start,
        port_end=args.port_end,
        max_attempts=args.max_attempts,
        reallocate=reallocate,
    )


def _release_leases(root: Path, isolation_id: str, resource_id: str | None = None) -> dict[str, Any]:
    isolation_id = validate_id(isolation_id, "id")
    if resource_id is not None:
        resource_id = validate_id(resource_id, "port")
    with RuntimeRegistryLock(port_lock_path(root)):
        registry = _load_port_registry(root)
        before = list(registry["leases"])
        released = [
            item
            for item in before
            if item.get("isolation_id") == isolation_id
            and (resource_id is None or item.get("resource_id") == resource_id)
        ]
        remaining = [item for item in before if item not in released]
        _write_port_registry(root, remaining)
        try:
            _sync_runtime_record(root, isolation_id, remaining)
        except RuntimeError:
            pass
        return {
            "status": "RELEASED",
            "id": isolation_id,
            "resource_id": resource_id,
            "released": [
                {"resource_id": item.get("resource_id"), "port": int(item["port"])}
                for item in released
            ],
            "runtime": _runtime_snapshot(isolation_id, remaining),
        }


def runtime_release(args: argparse.Namespace) -> dict[str, Any]:
    root = project_root(Path(args.project))
    record_for(root, args.id)
    return _release_leases(root, args.id, args.port)


def runtime_reconcile(args: argparse.Namespace) -> dict[str, Any]:
    root = project_root(Path(args.project))
    with RuntimeRegistryLock(port_lock_path(root)):
        registry = _load_port_registry(root)
        active_ids = {str(item["id"]) for item in active_records(root)}
        stale = [
            item
            for item in registry["leases"]
            if str(item.get("isolation_id") or "") not in active_ids
        ]
        remaining = [item for item in registry["leases"] if item not in stale]
        _write_port_registry(root, remaining)
        for isolation_id in active_ids:
            try:
                _sync_runtime_record(root, isolation_id, remaining)
            except RuntimeError:
                pass
        return {
            "status": "RECONCILED",
            "released": [
                {
                    "isolation_id": item.get("isolation_id"),
                    "resource_id": item.get("resource_id"),
                    "port": int(item["port"]),
                }
                for item in stale
            ],
            "active_lease_count": len(remaining),
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
    data = create_worktree(args)
    if args.port:
        lease = _lease_port(
            project_root(Path(args.project)),
            args.id,
            args.port,
            preferred=args.preferred,
            expose_as=list(args.expose or []),
            port_start=args.port_start,
            port_end=args.port_end,
            max_attempts=args.max_attempts,
            reallocate=False,
        )
        data["runtime"] = lease["runtime"]
    return data


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
    registry = _load_port_registry(root)
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
        "runtime": _runtime_snapshot(str(record.get("id")), list(registry["leases"])),
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
                "runtime_preserved": True,
            }, 2)
        removed = run_git(root, "worktree", "remove", str(target))
        if removed.returncode != 0:
            raise RuntimeError((removed.stderr or removed.stdout).strip() or "git worktree remove failed")

    record["version"] = max(int(record.get("version") or 1), 3)
    record["repository_id"] = repository_identity(root)["repository_id"]
    record["status"] = "REMOVED"
    record["removed_at"] = now()
    record["updated_at"] = now()
    atomic_yaml(path, record)
    runtime = _release_leases(root, str(record.get("id")))
    return ({
        "status": "REMOVED",
        "mode": "worktree",
        "id": record.get("id"),
        "path": str(target),
        "branch": record.get("branch"),
        "branch_preserved": True,
        "runtime": runtime["runtime"],
        "released_runtime": runtime["released"],
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


def add_port_options(parser: argparse.ArgumentParser, *, require_port: bool) -> None:
    parser.add_argument("--port", required=require_port)
    parser.add_argument("--preferred", type=int)
    parser.add_argument("--expose", action="append", default=[])
    parser.add_argument("--port-start", type=int, default=DEFAULT_PORT_START)
    parser.add_argument("--port-end", type=int, default=DEFAULT_PORT_END)
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)


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
    add_port_options(create, require_port=False)

    status = sub.add_parser("status")
    add_common(status)
    status.add_argument("--id", required=True)

    remove = sub.add_parser("remove")
    add_common(remove)
    remove.add_argument("--id", required=True)

    lease = sub.add_parser("runtime-lease")
    add_common(lease)
    lease.add_argument("--id", required=True)
    add_port_options(lease, require_port=True)

    reallocate = sub.add_parser("runtime-reallocate")
    add_common(reallocate)
    reallocate.add_argument("--id", required=True)
    add_port_options(reallocate, require_port=True)

    release = sub.add_parser("runtime-release")
    add_common(release)
    release.add_argument("--id", required=True)
    release.add_argument("--port")

    reconcile = sub.add_parser("runtime-reconcile")
    add_common(reconcile)

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
        elif args.command == "remove":
            data, exit_code = remove_isolation(args)
        elif args.command == "runtime-lease":
            data = runtime_lease(args)
        elif args.command == "runtime-reallocate":
            data = runtime_lease(args, reallocate=True)
        elif args.command == "runtime-release":
            data = runtime_release(args)
        else:
            data = runtime_reconcile(args)
    except (RuntimeError, OSError, ValueError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    output(data, args.format)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

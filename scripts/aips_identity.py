#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any

import yaml


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def git_output(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return result.stdout.strip()
    except Exception:
        return None


def git_bytes(root: Path, *args: str) -> bytes | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            check=True,
            timeout=30,
        )
        return result.stdout
    except Exception:
        return None


def project_root(path: Path) -> Path:
    path = path.expanduser().resolve()
    root = git_output(path, "rev-parse", "--show-toplevel")
    return Path(root).resolve() if root else path


def config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))).expanduser().resolve() / "aips"


def _resolved_git_path(root: Path, raw: str | None) -> str:
    if not raw:
        return ""
    path = Path(raw)
    return str(path.resolve() if path.is_absolute() else (root / path).resolve())


def legacy_path_id(root: Path) -> str:
    return sha(str(root.resolve()))[:20]


def repository_identity(root: Path) -> dict[str, str]:
    root = project_root(root)
    remote = git_output(root, "config", "--get", "remote.origin.url") or ""
    common_raw = git_output(root, "rev-parse", "--git-common-dir") or ""
    git_dir_raw = git_output(root, "rev-parse", "--git-dir") or ""

    common_resolved = _resolved_git_path(root, common_raw)
    if remote:
        repository_source = "remote:" + remote
        # Preserve the v0.9+ Project Intelligence repository-id algorithm for remote-backed repos.
        repository_id = sha(remote)[:20]
        legacy_pi_repository_id = repository_id
    elif common_resolved:
        repository_source = "git-common:" + common_resolved
        repository_id = sha(repository_source)[:20]
        legacy_pi_repository_id = sha(f"{root}|{common_raw}")[:20]
    else:
        repository_source = "path:" + str(root)
        repository_id = sha(repository_source)[:20]
        legacy_pi_repository_id = sha(f"{root}|")[:20]

    # Preserve the prior Project Intelligence worktree-id shape when possible.
    worktree_source = f"{root}|{git_dir_raw}"
    worktree_id = sha(worktree_source)[:16]
    workspace_id = f"{repository_id}-{worktree_id}"
    legacy_pi_project_id = f"{legacy_pi_repository_id}-{worktree_id}"

    return {
        "repository_id": repository_id,
        "repository_source_hash": sha(repository_source),
        "worktree_id": worktree_id,
        "workspace_id": workspace_id,
        "project_id": workspace_id,
        "legacy_path_id": legacy_path_id(root),
        "legacy_project_intelligence_id": legacy_pi_project_id,
        "root": str(root),
    }


def _hash_file(path: Path, hasher: Any) -> None:
    try:
        if path.is_symlink():
            hasher.update(("symlink:" + os.readlink(path)).encode("utf-8", errors="replace"))
            return
        if not path.is_file():
            hasher.update(b"non-regular")
            return
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                hasher.update(chunk)
    except OSError as exc:
        hasher.update(("unreadable:" + type(exc).__name__).encode())


def dirty_fingerprint(root: Path) -> tuple[str | None, bool | None]:
    root = project_root(root)
    status = git_bytes(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if status is None:
        return None, None

    hasher = hashlib.sha256()
    hasher.update(b"status\0")
    hasher.update(status)

    diff = git_bytes(root, "diff", "--binary", "--no-ext-diff", "HEAD")
    if diff is not None:
        hasher.update(b"diff\0")
        hasher.update(diff)

    untracked = git_bytes(root, "ls-files", "--others", "--exclude-standard", "-z") or b""
    paths = [p for p in untracked.decode("utf-8", errors="surrogateescape").split("\0") if p]
    hasher.update(f"untracked-count:{len(paths)}".encode())
    for rel in sorted(paths):
        hasher.update(rel.encode("utf-8", errors="surrogateescape"))
        hasher.update(b"\0")
        _hash_file(root / rel, hasher)
        hasher.update(b"\0")

    return "sha256:" + hasher.hexdigest(), len(status) == 0


def workspace_snapshot(root: Path) -> dict[str, Any]:
    root = project_root(root)
    ident = repository_identity(root)
    revision = git_output(root, "rev-parse", "HEAD")
    branch = git_output(root, "branch", "--show-current") or None
    dirty, clean = dirty_fingerprint(root)
    if revision is None or dirty is None:
        fingerprint = None
    else:
        payload = {
            "repository_id": ident["repository_id"],
            "workspace_id": ident["workspace_id"],
            "revision": revision,
            "branch": branch,
            "dirty_fingerprint": dirty,
        }
        fingerprint = "sha256:" + hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    return {
        "root": str(root),
        "repository_id": ident["repository_id"],
        "workspace_id": ident["workspace_id"],
        "project_id": ident["workspace_id"],
        "revision": revision,
        "branch": branch,
        "dirty_fingerprint": dirty,
        "fingerprint": fingerprint,
        "clean": clean,
    }


def output(data: dict[str, Any], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip())


def main() -> int:
    parser = argparse.ArgumentParser(description="AIPS canonical project/workspace identity")
    parser.add_argument("command", choices=["show"])
    parser.add_argument("--project", default=os.getcwd())
    parser.add_argument("--format", choices=["yaml", "json"], default="yaml")
    args = parser.parse_args()
    root = project_root(Path(args.project))
    data = {
        "identity": repository_identity(root),
        "workspace": workspace_snapshot(root),
    }
    output(data, args.format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

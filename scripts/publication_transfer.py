#!/usr/bin/env python3
"""Check a GitHub API publication candidate before any remote ref is updated.

This tool never writes to GitHub. The caller creates blobs and a tree, records the
returned identities, and must verify them here before creating a commit or ref.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit


class TransferError(RuntimeError):
    pass


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)
    if result.returncode:
        raise TransferError(
            result.stderr.decode("utf-8", errors="replace").strip()
            or f"git {args[0]} failed"
        )
    return result.stdout


def github_repository(url: str) -> str | None:
    scp_prefix = "git" + chr(64) + "github.com:"
    if url.startswith(scp_prefix):
        path = url.removeprefix(scp_prefix)
    else:
        parsed = urlsplit(url)
        if parsed.scheme not in {"https", "ssh"} or parsed.hostname != "github.com":
            return None
        if (
            parsed.username not in {None, "git"}
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            return None
        path = parsed.path.lstrip("/")
    path = path.removesuffix(".git")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", path):
        return None
    return path.lower()


def commit(root: Path, ref: str) -> str:
    return git(root, "rev-parse", f"{ref}^{{commit}}").decode("ascii").strip()


def manifest(root: Path, base: str, head: str, repository: str, remote: str) -> dict:
    expected = github_repository(f"https://github.com/{repository}")
    if expected != repository.lower():
        raise TransferError("expected repository must be owner/name")
    actual = github_repository(
        git(root, "remote", "get-url", remote).decode("utf-8").strip()
    )
    if actual != expected:
        raise TransferError(
            f"remote {remote} does not match expected GitHub repository {expected}"
        )
    base_sha, head_sha = commit(root, base), commit(root, head)
    if git(root, "status", "--porcelain"):
        raise TransferError("working tree is dirty; commit the exact candidate first")
    if commit(root, "HEAD") != head_sha:
        raise TransferError("checked-out HEAD differs from the candidate head")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", base_sha, head_sha],
        cwd=root,
        check=False,
    ).returncode:
        raise TransferError("candidate base is not an ancestor of head")
    count = int(git(root, "rev-list", "--count", f"{base_sha}..{head_sha}").strip())
    if count != 1:
        raise TransferError(
            "GitHub API publication requires exactly one clean candidate commit"
        )
    tree_sha = git(root, "rev-parse", f"{head_sha}^{{tree}}").decode("ascii").strip()
    changed = [
        item.decode("utf-8")
        for item in git(
            root, "diff", "--name-only", "-z", "--no-renames", base_sha, head_sha
        ).split(b"\0")
        if item
    ]
    tree: dict[str, dict] = {}
    for record in git(root, "ls-tree", "-r", "-z", head_sha).split(b"\0"):
        if not record:
            continue
        meta, raw_path = record.split(b"\t", 1)
        mode, kind, sha = meta.decode("ascii").split()
        tree[raw_path.decode("utf-8")] = {"mode": mode, "type": kind, "sha": sha}
    entries = [
        {"path": path, **tree[path]} if path in tree else {"path": path, "sha": None}
        for path in sorted(changed)
    ]
    if not entries:
        raise TransferError("candidate has no changed paths")
    return {
        "version": 1,
        "repository": expected,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "tree_sha": tree_sha,
        "entries": entries,
    }


def unique_json(path: Path) -> dict:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict:
        value = {}
        for key, item in pairs:
            if key in value:
                raise TransferError(f"duplicate receipt key: {key}")
            value[key] = item
        return value

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TransferError(f"cannot read UTF-8 JSON receipt: {exc}") from exc
    if not isinstance(value, dict):
        raise TransferError("receipt must be a JSON object")
    return value


def verify(candidate: dict, receipt: dict) -> dict:
    receipt_repository = receipt.get("repository")
    if (
        not isinstance(receipt_repository, str)
        or receipt_repository.lower() != candidate["repository"]
    ):
        raise TransferError("receipt repository differs from expected destination")
    if receipt.get("base_sha") != candidate["base_sha"]:
        raise TransferError("remote base moved or differs from the local candidate")
    expected = {
        entry["path"]: entry["sha"]
        for entry in candidate["entries"]
        if entry["sha"] is not None
    }
    blobs = receipt.get("blobs")
    if not isinstance(blobs, dict) or blobs != expected:
        raise TransferError("remote blob identities differ from the local candidate")
    if receipt.get("tree_sha") != candidate["tree_sha"]:
        raise TransferError("remote tree differs from the exact local candidate tree")
    return {
        "status": "READY_TO_PUBLISH",
        "repository": candidate["repository"],
        "base_sha": candidate["base_sha"],
        "head_sha": candidate["head_sha"],
        "tree_sha": candidate["tree_sha"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "verify"))
    parser.add_argument(
        "--project-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument(
        "--repository", required=True, help="Expected GitHub owner/name"
    )
    parser.add_argument("--remote", default="origin")
    parser.add_argument(
        "--receipt",
        type=Path,
        help="JSON returned blob/tree identities; required for verify",
    )
    args = parser.parse_args()
    try:
        candidate = manifest(
            args.project_root.resolve(),
            args.base,
            args.head,
            args.repository,
            args.remote,
        )
        if args.action == "prepare":
            result = {"status": "PREPARED", **candidate}
        else:
            if args.receipt is None:
                raise TransferError("--receipt is required for verify")
            result = verify(candidate, unique_json(args.receipt))
    except (OSError, UnicodeError, ValueError, TransferError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

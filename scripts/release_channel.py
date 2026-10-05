#!/usr/bin/env python3
"""Resolve and verify exact SemVer release tags for AIPS stable installs."""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
from typing import Any

VERSION_RE = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")


class ReleaseChannelError(ValueError):
    pass


def parse_remote_tags(output: str) -> list[dict[str, Any]]:
    direct: dict[str, str] = {}
    peeled: dict[str, str] = {}
    for line in output.splitlines():
        fields = line.split("\t", 1)
        if len(fields) != 2:
            continue
        sha, ref = fields
        if not SHA_RE.fullmatch(sha):
            continue
        match = re.fullmatch(r"refs/tags/(v(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))(\^\{\})?", ref)
        if not match:
            continue
        (peeled if match.group(2) else direct)[match.group(1)] = sha
    rows = []
    for tag, tag_sha in direct.items():
        commit = peeled.get(tag, tag_sha)
        version = VERSION_RE.fullmatch(tag)
        assert version is not None
        rows.append({"tag": tag, "version": tuple(int(part) for part in version.groups()), "tag_sha": tag_sha, "commit_sha": commit})
    return sorted(rows, key=lambda item: item["version"])


def latest_release(remote: str, *, git_run=subprocess.run) -> dict[str, Any] | None:
    result = git_run(
        ["git", "ls-remote", "--tags", remote, "refs/tags/v*"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ReleaseChannelError("could not inspect remote version tags")
    rows = parse_remote_tags(result.stdout)
    return rows[-1] if rows else None


def verify_tag(repository: Path, tag: str, expected_sha: str) -> dict[str, str]:
    if not VERSION_RE.fullmatch(tag) or not SHA_RE.fullmatch(expected_sha):
        raise ReleaseChannelError("stable channel requires a full vX.Y.Z tag and commit SHA")
    try:
        commit = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", f"refs/tags/{tag}^{{commit}}"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        version = subprocess.run(
            ["git", "-C", str(repository), "show", f"{tag}:VERSION"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseChannelError("release tag is unavailable in the installed checkout") from exc
    if commit != expected_sha:
        raise ReleaseChannelError("release tag target differs from the advertised remote commit")
    if tag != f"v{version}":
        raise ReleaseChannelError("release tag and VERSION file do not match")
    return {"tag": tag, "version": version, "commit_sha": commit}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    resolve = sub.add_parser("resolve")
    resolve.add_argument("--remote", required=True)
    check = sub.add_parser("verify")
    check.add_argument("--repository", type=Path, required=True)
    check.add_argument("--tag", required=True)
    check.add_argument("--expected-sha", required=True)
    args = parser.parse_args()
    try:
        if args.command == "resolve":
            result = latest_release(args.remote)
            if result is None:
                print("NO_STABLE_RELEASE")
                return 3
            print(f"{result['tag']}\t{result['commit_sha']}")
            return 0
        result = verify_tag(args.repository, args.tag, args.expected_sha)
        print(f"VERIFIED {result['tag']} {result['commit_sha']}")
        return 0
    except (OSError, ReleaseChannelError) as exc:
        print(f"RELEASE_CHANNEL_BLOCKED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Capture read-only GitHub ruleset and branch-protection evidence."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aips_common import canonical_digest as _aips_canonical_digest

ROOT = Path(__file__).resolve().parents[1]


def canonical_digest(value: Any) -> str:
    return _aips_canonical_digest(value)


def repository_slug(remote: str) -> str | None:
    match = re.search(r"(?:github\.com[:/])([^/]+/[^/.]+?)(?:\.git)?$", remote.strip())
    return match.group(1) if match else None


def _required_checks(protection: dict[str, Any]) -> list[str]:
    checks = protection.get("required_status_checks") or {}
    contexts = {str(item) for item in checks.get("contexts") or []}
    contexts.update({str(item.get("context")) for item in checks.get("checks") or [] if item.get("context")})
    return sorted(contexts)


def build_snapshot(
    repository: str,
    branch: str,
    read_api: Callable[[str], tuple[int, str]],
    *,
    captured_at: str | None = None,
) -> dict[str, Any]:
    """Read both GitHub surfaces and retain UNKNOWN when either is incomplete."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("repository must be an owner/name slug")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", branch):
        raise ValueError("branch must be a simple branch name")

    sources: dict[str, dict[str, Any]] = {}
    payloads: dict[str, Any] = {}
    endpoints = {
        "rulesets": f"repos/{repository}/rulesets?includes_parents=true&per_page=100",
        "branch_protection": f"repos/{repository}/branches/{branch}/protection",
    }
    for name, endpoint in endpoints.items():
        status, output = read_api(endpoint)
        try:
            payload = json.loads(output) if status == 0 else None
        except json.JSONDecodeError:
            payload = None
        if name == "rulesets" and isinstance(payload, list) and all(isinstance(page, list) for page in payload):
            payload = [ruleset for page in payload for ruleset in page]
        readable = status == 0 and (isinstance(payload, list) if name == "rulesets" else isinstance(payload, dict))
        sources[name] = {"status": "READABLE" if readable else "UNKNOWN", "exit_code": status if status else 0}
        if readable:
            payloads[name] = payload

    rulesets = payloads.get("rulesets")
    protection = payloads.get("branch_protection")
    complete = rulesets is not None and protection is not None
    bypass_actor_map = {
        json.dumps(actor, sort_keys=True, ensure_ascii=False): actor
        for ruleset in (rulesets or []) if isinstance(ruleset, dict)
        for actor in (ruleset.get("bypass_actors") or []) if isinstance(actor, dict)
    }
    normalized_protection = dict(protection or {})
    if protection:
        normalized_protection["required_checks"] = _required_checks(protection)
    snapshot = {
        "version": 1,
        "repository": repository,
        "branch": branch,
        "captured_at": captured_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_status": "COMPLETE" if complete else "UNKNOWN",
        "sources": sources,
        "branch_protection": normalized_protection,
        "rulesets": rulesets or [],
        "bypass_actors": [bypass_actor_map[key] for key in sorted(bypass_actor_map)],
        "source_complete": complete,
        "activation_authorized": False,
        "api_write_performed": False,
    }
    digest_content = {key: value for key, value in snapshot.items() if key != "captured_at"}
    snapshot["snapshot_digest"] = canonical_digest(digest_content)
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", help="GitHub owner/name; inferred from origin when omitted")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--output", type=Path, help="Write the snapshot JSON to this path")
    args = parser.parse_args()
    repository = args.repository
    if not repository:
        remote = subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT, capture_output=True, text=True, check=False)
        repository = repository_slug(remote.stdout) if remote.returncode == 0 else None
    if not repository:
        parser.error("cannot infer GitHub owner/name; pass --repository")

    def read_api(endpoint: str) -> tuple[int, str]:
        argv = ["gh", "api", endpoint]
        if "/rulesets?" in endpoint:
            argv[2:2] = ["--paginate", "--slurp"]
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, check=False)
        return result.returncode, result.stdout

    snapshot = build_snapshot(repository, args.branch, read_api)
    rendered = json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if snapshot["source_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

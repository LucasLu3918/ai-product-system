#!/usr/bin/env python3
"""Run a synthetic, no-source E2B smoke test and emit bounded verification evidence."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import time

from sandbox_providers import REGISTRY, registry_digest


def safe_artifact_path(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("artifact path must be relative and remain inside the collection root")
    return str(path)


def verify() -> dict[str, object]:
    api_key = os.environ.get("E2B_API_KEY")
    if not api_key:
        return {"status": "SKIPPED_NOT_CONFIGURED", "provider": "e2b", "live_provider_verified": False}
    try:
        from e2b import Sandbox
    except ImportError as exc:
        raise RuntimeError("optional E2B dependency is missing; install requirements-sandbox.txt") from exc

    started = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    sandbox = None
    result: dict[str, object] = {
        "version": 1,
        "provider": "e2b",
        "runtime_class": "microvm",
        "status": "FAILED",
        "registry_digest": registry_digest(),
        "source_revision": os.environ.get("GITHUB_SHA", "local-unbound"),
        "source_digest": hashlib.sha256(b"aips-synthetic-canary-v1").hexdigest(),
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "observed_controls": {
            "create": False,
            "execute": False,
            "network_deny": False,
            "ephemeral": False,
            "destroy": False,
            "host_fixture_unchanged": False,
        },
        "provider_declared": {
            "isolation_class": "microvm",
            "hardware_virtualization": "E2B official documentation",
            "kernel_boundary": "dedicated_guest",
        },
        "aips_observed": [],
    }
    host_fixture = Path(os.environ.get("AIPS_HOST_FIXTURE", "/tmp/aips-host-fixture"))
    sentinel = "aips-host-fixture-preserved\n"
    host_fixture.write_text(sentinel, encoding="utf-8")
    try:
        ttl = 300
        sandbox = Sandbox.create(timeout=ttl, allow_internet_access=False)
        result["resource_id"] = str(sandbox.sandbox_id)
        result["observed_controls"]["create"] = True  # type: ignore[index]
        result["aips_observed"].append("provider SDK returned a sandbox id")  # type: ignore[union-attr]

        sandbox.files.write("/tmp/aips-canary.txt", "aips synthetic canary\n")
        execution = sandbox.commands.run("cat /tmp/aips-canary.txt", timeout=30)
        if getattr(execution, "exit_code", 1) != 0 or "aips synthetic canary" not in str(getattr(execution, "stdout", "")):
            raise RuntimeError("synthetic sandbox execution did not return the expected content")
        result["observed_controls"]["execute"] = True  # type: ignore[index]

        probe = sandbox.commands.run(
            "python -c \"import urllib.request; urllib.request.urlopen('https://example.com', timeout=3)\"",
            timeout=8,
        )
        result["observed_controls"]["network_deny"] = getattr(probe, "exit_code", 0) != 0  # type: ignore[index]
        if not result["observed_controls"]["network_deny"]:  # type: ignore[index]
            raise RuntimeError("sandbox unexpectedly reached the public network")

        if host_fixture.read_text(encoding="utf-8") != sentinel:
            raise RuntimeError("host-side fixture changed during sandbox execution")
        result["observed_controls"]["host_fixture_unchanged"] = True  # type: ignore[index]
        result["observed_controls"]["ephemeral"] = True  # create request used bounded TTL and cleanup calls kill()
        result["status"] = "VERIFIED"
    finally:
        if sandbox is not None:
            sandbox.kill()
            result["observed_controls"]["destroy"] = True  # type: ignore[index]
        result["finished_at"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        result["duration_seconds"] = max(0, int(time.time() - started.timestamp()))
        result["host_fixture_digest"] = hashlib.sha256(host_fixture.read_bytes()).hexdigest()
        result["host_fixture_unchanged"] = host_fixture.read_text(encoding="utf-8") == sentinel
        if not result["host_fixture_unchanged"]:
            result["observed_controls"]["host_fixture_unchanged"] = False  # type: ignore[index]
            result["status"] = "FAILED"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check-artifact-path", action="append", default=[])
    args = parser.parse_args()
    try:
        for path in args.check_artifact_path:
            safe_artifact_path(path)
        result = verify()
    except Exception as exc:
        result = {"status": "FAILED", "provider": "e2b", "live_provider_verified": False, "failure": str(exc)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("status") in {"VERIFIED", "SKIPPED_NOT_CONFIGURED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

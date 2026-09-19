from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/resource_authorization.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=ROOT, text=True, capture_output=True)


with tempfile.TemporaryDirectory(prefix="aips-resource-auth-") as tmp:
    root = Path(tmp)
    profile = {
        "version": 1,
        "default_effect": "DENY",
        "subject": {"id": "agent-1", "role": "backend-engineer"},
        "grants": [
            {
                "id": "source",
                "kind": "repository_path",
                "selector": "src/**",
                "operations": ["read", "search", "update"],
                "constraints": {"change_boundary_required": True, "network_allowed": False},
            }
        ],
        "authority": {
            "human_approval_granted": False,
            "merge_authorized": False,
            "release_authorized": False,
            "protected_operation_authorized": False,
        },
    }
    path = root / "profile.yaml"
    path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")

    assert run("validate", "--profile", str(path)).returncode == 0
    read = run("check", "--profile", str(path), "--resource-id", "source", "--operation", "read")
    assert read.returncode == 0 and "status: ALLOW" in read.stdout
    missing_boundary = run("check", "--profile", str(path), "--resource-id", "source", "--operation", "update")
    assert missing_boundary.returncode == 1 and "change_boundary_required" in missing_boundary.stdout
    update = run("check", "--profile", str(path), "--resource-id", "source", "--operation", "update", "--change-boundary", "orders")
    assert update.returncode == 0 and "status: ALLOW" in update.stdout
    undeclared = run("check", "--profile", str(path), "--resource-id", "prod", "--operation", "execute")
    assert undeclared.returncode == 1 and "resource_not_granted" in undeclared.stdout

    forbidden = dict(profile)
    forbidden["grants"] = [dict(profile["grants"][0], operations=["read", "publish"])]
    bad_path = root / "bad.yaml"
    bad_path.write_text(yaml.safe_dump(forbidden, sort_keys=False), encoding="utf-8")
    bad = run("validate", "--profile", str(bad_path))
    assert bad.returncode == 2 and "BLOCKED" in bad.stdout

    authority = dict(profile)
    authority["authority"] = dict(profile["authority"], merge_authorized=True)
    authority_path = root / "authority.yaml"
    authority_path.write_text(yaml.safe_dump(authority, sort_keys=False), encoding="utf-8")
    assert run("validate", "--profile", str(authority_path)).returncode == 2

print("resource authorization lifecycle: PASS")

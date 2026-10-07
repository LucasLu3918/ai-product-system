"""Pin Plan21 public contracts before the hardening and consolidation phases."""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_secret_leakage  # noqa: E402
import deterministic_scheduler  # noqa: E402
import documentation_placement  # noqa: E402
import integration_gate  # noqa: E402
import project_intelligence  # noqa: E402
import repository_health  # noqa: E402
import repository_health_conformance  # noqa: E402
import resource_authorization  # noqa: E402
import review_evidence  # noqa: E402
import review_packet  # noqa: E402
import run_projection  # noqa: E402
import visual_profile  # noqa: E402


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    fixture = yaml.safe_load((ROOT / "tests/fixtures/plan21-contract-golden-vectors.yaml").read_text(encoding="utf-8"))
    raw_helpers = (
        resource_authorization.canonical_hash,
        integration_gate.canonical_hash,
        deterministic_scheduler.canonical_hash,
        check_secret_leakage.canonical_hash,
    )
    prefixed_helpers = (
        review_evidence.canonical_hash,
        run_projection.canonical_hash,
        repository_health.canonical_hash,
        review_packet.canonical_hash,
    )
    for vector in fixture["canonical_hashes"]["raw"]:
        for helper in raw_helpers:
            assert helper(vector["value"]) == vector["digest"], f"raw digest drift: {helper.__module__}.{helper.__name__}"
    for vector in fixture["canonical_hashes"]["prefixed"]:
        for helper in prefixed_helpers:
            assert helper(vector["value"]) == vector["digest"], f"prefixed digest drift: {helper.__module__}.{helper.__name__}"

    inside = ROOT / "scripts" / "resource_authorization.py"
    assert repository_health.relative_path(ROOT, inside) == "scripts/resource_authorization.py"
    assert repository_health_conformance.relative_path(ROOT, inside) == "scripts/resource_authorization.py"
    outside = ROOT.parent / "outside.py"
    expected_outside = str(outside.resolve())
    assert repository_health.relative_path(ROOT, outside) == expected_outside
    assert repository_health_conformance.relative_path(ROOT, outside) == expected_outside

    path_helpers = {
        "check_secret_leakage.glob_matches": check_secret_leakage.glob_matches,
        "project_intelligence.path_matches": project_intelligence.path_matches,
        "documentation_placement.matches_any": documentation_placement.matches_any,
        "visual_profile.path_matches": visual_profile.path_matches,
    }
    for case in fixture["path_matching"]:
        helper = path_helpers[case["helper"]]
        patterns = case.get("patterns", [case.get("pattern")])
        assert helper(case["path"], patterns if case["helper"].endswith("matches_any") or case["helper"].endswith("visual_profile.path_matches") else patterns[0]) is case["expected"], case

    for case in fixture["cli"]:
        proc = subprocess.run(
            [str(ROOT / "bin/aips"), *case["argv"]], cwd=ROOT, capture_output=True, check=False,
        )
        assert proc.returncode == case["exit_code"], f"CLI {case['argv']}: exit {proc.returncode}"
        if case["argv"] == ["version"]:
            assert re.fullmatch(case["stdout_pattern"], proc.stdout.decode("utf-8")), "version output shape drift"
        else:
            assert sha256(proc.stdout) == case["stdout_sha256"], f"CLI {case['argv']}: stdout drift"
        if case["stderr_sha256"] != "ignored-dynamic-startup-diagnostics":
            assert sha256(proc.stderr) == case["stderr_sha256"], f"CLI {case['argv']}: stderr drift"

    print("Plan21 contract baseline evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

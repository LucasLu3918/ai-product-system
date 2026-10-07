"""Golden contracts keep shared helper extraction behavior compatible."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_secret_leakage
import deterministic_scheduler
import documentation_placement
import evolution_effectiveness
import evolution_preanalysis
import governance_guard
import implementation_enforcement
import integration_gate
import maintenance_reliability
import openapi_generator_adapter
import project_intelligence
import publish_preflight
import repository_governance_snapshot
import repository_health
import repository_health_conformance
import resource_authorization
import review_evidence
import review_packet
import run_projection
import runtime_policy
import visual_profile


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    fixture = yaml.safe_load((ROOT / "tests/fixtures/plan21-contract-golden-vectors.yaml").read_text(encoding="utf-8"))
    raw_wrappers = [
        check_secret_leakage.canonical_hash,
        deterministic_scheduler.canonical_hash,
        integration_gate.canonical_hash,
        publish_preflight.canonical_hash,
        resource_authorization.canonical_hash,
    ]
    prefixed_wrappers = [
        evolution_effectiveness.canonical_digest,
        evolution_preanalysis.canonical_digest,
        implementation_enforcement.canonical_digest,
        maintenance_reliability.canonical_digest,
        openapi_generator_adapter.canonical_digest,
        repository_governance_snapshot.canonical_digest,
        repository_health.canonical_hash,
        review_evidence.canonical_hash,
        review_packet.canonical_hash,
        run_projection.canonical_hash,
    ]
    for item in fixture["canonical_hashes"]["raw"]:
        for wrapper in raw_wrappers:
            require(wrapper(item["value"]) == item["digest"], f"raw hash changed: {wrapper.__module__}.{wrapper.__name__}/{item['name']}")
    for item in fixture["canonical_hashes"]["prefixed"]:
        for wrapper in prefixed_wrappers:
            require(wrapper(item["value"]) == item["digest"], f"prefixed hash changed: {wrapper.__module__}.{wrapper.__name__}/{item['name']}")

    for item in fixture["path_matching"]:
        helper = {
            "check_secret_leakage.glob_matches": check_secret_leakage.glob_matches,
            "project_intelligence.path_matches": project_intelligence.path_matches,
            "documentation_placement.matches_any": documentation_placement.matches_any,
            "visual_profile.path_matches": visual_profile.path_matches,
        }[item["helper"]]
        actual = helper(item["path"], item.get("patterns", item.get("pattern")))
        require(actual is item["expected"], f"path match changed: {item['helper']} {item['path']}")

    root = ROOT / "scripts"
    target = root / "aips_common" / "canonical.py"
    relative = "aips_common/canonical.py"
    require(repository_health.relative_path(root, target) == relative, "repository health relative path changed")
    require(repository_health_conformance.relative_path(root, target) == relative, "conformance relative path changed")
    outside = root.parent / "outside-path-fixture.txt"
    outside_relative = str(outside.resolve())
    require(repository_health.relative_path(root, outside) == outside_relative, "repository health outside path changed")
    require(repository_health_conformance.relative_path(root, outside) == outside_relative, "conformance outside path changed")

    domain = fixture["canonical_hashes"]["domain_specific"]
    require(governance_guard.fingerprint(domain[0]["value"]) == domain[0]["digest"], "governance fingerprint domain contract changed")
    require(runtime_policy.action_digest(domain[1]["value"]) == domain[1]["digest"], "runtime action digest domain contract changed")
    print("shared_primitives_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import yaml

EVENT_ORDER = [
    "planning_complete",
    "local_verified",
    "release_candidate_created",
    "staging_verified",
    "release_readiness_ready",
    "promotion_approved",
    "production_deployed",
    "production_verified",
    "recovery_triggered",
    "recovery_completed",
]


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("evidence must be a mapping")
    return data


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve(root: Path, raw: Any) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    path = Path(raw)
    return path if path.is_absolute() else root / path


def validate(path: Path) -> dict[str, Any]:
    doc = load_yaml(path)
    root = path.parent
    errors: list[str] = []

    if doc.get("version") != 1:
        errors.append("version must be 1")
    if doc.get("mode") != "representative_isolated_lifecycle":
        errors.append("mode must be representative_isolated_lifecycle")
    if doc.get("status") != "PASS":
        errors.append("status must be PASS")
    if doc.get("external_production_claimed") is not False:
        errors.append("external_production_claimed must be false for this evidence mode")

    product = doc.get("product") or {}
    product_path = resolve(root, product.get("product_yaml"))
    if product_path is None or not product_path.is_file():
        errors.append("product.product_yaml must reference an existing PRODUCT.yaml")
    if product.get("delivery_state") != "PRODUCTION_VERIFIED":
        errors.append("product.delivery_state must be PRODUCTION_VERIFIED")

    candidate = doc.get("release_candidate") or {}
    artifact = resolve(root, candidate.get("artifact"))
    expected_hash = str(candidate.get("sha256") or "")
    if artifact is None or not artifact.is_file():
        errors.append("release_candidate.artifact must exist")
    elif not expected_hash or sha256(artifact) != expected_hash:
        errors.append("release_candidate artifact hash mismatch")
    if not str(candidate.get("source_revision") or "").strip():
        errors.append("release_candidate.source_revision is required")

    environments = doc.get("environments") or {}
    for name in ("local", "staging", "production"):
        env = environments.get(name) or {}
        if env.get("status") != "PASS":
            errors.append(f"environments.{name}.status must be PASS")
        if env.get("isolated") is not True:
            errors.append(f"environments.{name}.isolated must be true")
        if env.get("candidate_sha256") != expected_hash:
            errors.append(f"environments.{name}.candidate_sha256 must match the exact release candidate")
        evidence = resolve(root, env.get("evidence"))
        if evidence is None or not evidence.is_file() or evidence.stat().st_size == 0:
            errors.append(f"environments.{name}.evidence must be a non-empty file")

    gates = doc.get("gates") or {}
    if (gates.get("local_complete") or {}).get("status") != "PASS":
        errors.append("LOCAL_COMPLETE gate must PASS")
    readiness = gates.get("release_readiness") or {}
    if readiness.get("status") != "READY":
        errors.append("Release Readiness gate must be READY")
    readiness_path = resolve(root, readiness.get("evidence"))
    if readiness_path is None or not readiness_path.is_file():
        errors.append("Release Readiness evidence must exist")
    approval = gates.get("promotion_approval") or {}
    if approval.get("status") != "APPROVED":
        errors.append("explicit product-level promotion approval is required")
    if approval.get("candidate_sha256") != expected_hash:
        errors.append("promotion approval must bind the exact release candidate")
    if approval.get("target_environment") != "production":
        errors.append("promotion approval target_environment must be production")

    post = doc.get("post_deploy") or {}
    if post.get("health") != "PASS" or post.get("smoke") != "PASS":
        errors.append("post-deploy health and smoke must PASS")
    if post.get("structured_logs_observed") is not True:
        errors.append("post-deploy structured logs must be observed")

    recovery = doc.get("recovery") or {}
    if recovery.get("exercised") is not True:
        errors.append("recovery path must be exercised")
    if recovery.get("trigger") != "production_health_failure":
        errors.append("recovery trigger must prove a production health failure path")
    if recovery.get("restored_candidate_sha256") != expected_hash:
        errors.append("recovery must restore the verified candidate")
    if recovery.get("restored_health") != "PASS":
        errors.append("recovery must restore healthy service")
    recovery_evidence = resolve(root, recovery.get("evidence"))
    if recovery_evidence is None or not recovery_evidence.is_file() or recovery_evidence.stat().st_size == 0:
        errors.append("recovery evidence must exist")

    events = doc.get("events") or []
    names = [item.get("name") for item in events if isinstance(item, dict)]
    positions: dict[str, int] = {}
    for required in EVENT_ORDER:
        if required not in names:
            errors.append(f"missing lifecycle event: {required}")
        else:
            positions[required] = names.index(required)
    if len(positions) == len(EVENT_ORDER):
        ordered = [positions[name] for name in EVENT_ORDER]
        if ordered != sorted(ordered):
            errors.append("lifecycle events are out of order; production must follow readiness and approval")

    if "production_deployed" in positions and "promotion_approved" in positions:
        if positions["production_deployed"] <= positions["promotion_approved"]:
            errors.append("production deployment occurred before explicit promotion approval")

    status = "PASS" if not errors else "FAIL"
    return {
        "status": status,
        "errors": errors,
        "candidate_sha256": expected_hash or None,
        "lifecycle_complete": status == "PASS",
        "external_production_inferred": False,
        "production_gate_inferred_from_readiness_alone": False,
        "path": str(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AIPS end-to-end product delivery evidence")
    parser.add_argument("path")
    parser.add_argument("--format", choices=["json", "yaml"], default="yaml")
    args = parser.parse_args()
    try:
        result = validate(Path(args.path).resolve())
    except (OSError, ValueError, yaml.YAMLError) as exc:
        result = {"status": "FAIL", "errors": [str(exc)], "external_production_inferred": False}
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(result, sort_keys=False, allow_unicode=True).rstrip())
    return 0 if result.get("status") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

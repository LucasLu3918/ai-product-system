#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import re
from typing import Any

import yaml

from governance_audit import (
    BUNDLE_ANCHOR,
    BUNDLE_MANIFEST,
    canonical_json,
    file_sha256,
    load_json_mapping,
    sha256_text,
    verify_bundle,
)

CATALOG_TYPE = "aips-governance-audit-catalog"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SAFE_SUBJECT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$")


def load_yaml_mapping(path: Path, label: str) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"{label} is not valid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    return value


def parse_iso_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be YYYY-MM-DD") from exc


def optional_days(value: Any, field: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer or null")
    return value


def load_policy(path: Path) -> dict[str, Any]:
    policy = load_yaml_mapping(path, "retention policy")
    if policy.get("version") != 1:
        raise ValueError("retention policy version must be 1")
    policy_id = str(policy.get("policy_id") or "")
    if not SAFE_ID.fullmatch(policy_id):
        raise ValueError("retention policy_id is invalid")
    if policy.get("mode") != "advisory_only":
        raise ValueError("retention policy mode must be advisory_only")
    authority = policy.get("authority") or {}
    if authority.get("automatic_delete") is not False or authority.get("deletion_authorized") is not False:
        raise ValueError("retention policy must not authorize automatic deletion")
    requirements = policy.get("requirements") or {}
    for field in ("external_anchor_from_sal", "checkpoint_from_sal"):
        value = requirements.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > 4:
            raise ValueError(f"{field} must be an integer from 0 to 4")
    if requirements.get("preserve_minimal_digest") is not True:
        raise ValueError("preserve_minimal_digest must be true")
    levels = policy.get("levels") or {}
    for sal in range(5):
        item = levels.get(str(sal))
        if not isinstance(item, dict):
            raise ValueError(f"retention policy missing SAL {sal}")
        optional_days(item.get("full_bundle_days"), f"SAL {sal} full_bundle_days")
        optional_days(item.get("minimal_record_days"), f"SAL {sal} minimal_record_days")
        optional_days(item.get("checkpoint_public_key_days"), f"SAL {sal} checkpoint_public_key_days")
    return policy


def load_descriptor(path: Path) -> dict[str, Any]:
    raw = load_yaml_mapping(path, "catalog entry")
    if raw.get("version") != 1:
        raise ValueError(f"catalog entry version must be 1: {path}")
    bundle_id = str(raw.get("bundle_id") or "")
    if not SAFE_ID.fullmatch(bundle_id):
        raise ValueError(f"invalid bundle_id: {bundle_id!r}")
    subject = raw.get("subject") or {}
    subject_type = str(subject.get("type") or "")
    subject_id = str(subject.get("id") or "")
    if not SAFE_ID.fullmatch(subject_type):
        raise ValueError(f"invalid subject.type for {bundle_id}")
    if not SAFE_SUBJECT.fullmatch(subject_id):
        raise ValueError(f"invalid subject.id for {bundle_id}")
    sal = raw.get("sal")
    if not isinstance(sal, int) or isinstance(sal, bool) or sal < 0 or sal > 4:
        raise ValueError(f"sal must be 0-4 for {bundle_id}")
    retained_on = str(raw.get("retained_on") or "")
    parse_iso_date(retained_on, f"{bundle_id}.retained_on")
    bundle_path = Path(str(raw.get("bundle_path") or "")).expanduser().resolve()
    if not bundle_path.is_dir():
        raise ValueError(f"bundle_path missing for {bundle_id}: {bundle_path}")
    anchor_raw = raw.get("anchor_path")
    anchor_path = None
    if anchor_raw:
        anchor_path = Path(str(anchor_raw)).expanduser().resolve()
        if not anchor_path.is_file():
            raise ValueError(f"anchor_path missing for {bundle_id}: {anchor_path}")
    legal_hold = raw.get("legal_hold", False)
    if not isinstance(legal_hold, bool):
        raise ValueError(f"legal_hold must be boolean for {bundle_id}")
    return {
        "bundle_id": bundle_id,
        "subject": {"type": subject_type, "id": subject_id},
        "sal": sal,
        "retained_on": retained_on,
        "legal_hold": legal_hold,
        "bundle_path": bundle_path,
        "anchor_path": anchor_path,
    }


def build_entry(descriptor: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    bundle_id = descriptor["bundle_id"]
    sal = descriptor["sal"]
    bundle = descriptor["bundle_path"]
    external_anchor = descriptor["anchor_path"]
    requirements = policy["requirements"]
    if sal >= requirements["external_anchor_from_sal"] and external_anchor is None:
        raise ValueError(f"{bundle_id} SAL {sal} requires an external anchor")

    verification = verify_bundle(bundle, anchor_path=external_anchor)
    if verification.get("status") != "PASS":
        raise ValueError(f"{bundle_id} bundle verification failed: {'; '.join(verification.get('errors') or [])}")

    manifest = load_json_mapping(bundle / BUNDLE_MANIFEST, BUNDLE_MANIFEST)
    anchor_path = external_anchor or (bundle / BUNDLE_ANCHOR)
    anchor = load_json_mapping(anchor_path, "anchor")
    ledger_meta = manifest.get("ledger") or {}
    checkpoint_summary = ledger_meta.get("checkpoints") or {}
    checkpoint_events = int(checkpoint_summary.get("checkpoint_events") or 0)
    if sal >= requirements["checkpoint_from_sal"] and checkpoint_events < 1:
        raise ValueError(f"{bundle_id} SAL {sal} requires at least one signed checkpoint")

    public_keys = []
    for item in manifest.get("public_keys") or []:
        if not isinstance(item, dict):
            raise ValueError(f"{bundle_id} contains an invalid public-key entry")
        key_id = str(item.get("key_id") or "")
        fingerprint = str(item.get("public_key_fingerprint") or "")
        digest = str(item.get("sha256") or "")
        if not SAFE_ID.fullmatch(key_id) or not fingerprint.startswith("sha256:") or not digest.startswith("sha256:"):
            raise ValueError(f"{bundle_id} contains invalid checkpoint key metadata")
        public_keys.append({
            "key_id": key_id,
            "public_key_fingerprint": fingerprint,
            "sha256": digest,
        })

    evidence = []
    for item in manifest.get("evidence") or []:
        if not isinstance(item, dict):
            raise ValueError(f"{bundle_id} contains an invalid evidence entry")
        evidence.append({
            "name": str(item.get("name") or ""),
            "sha256": str(item.get("sha256") or ""),
            "bytes": item.get("bytes"),
        })

    return {
        "bundle_id": bundle_id,
        "subject": descriptor["subject"],
        "sal": sal,
        "retained_on": descriptor["retained_on"],
        "legal_hold": descriptor["legal_hold"],
        "repository_revision": manifest.get("repository_revision"),
        "events": ledger_meta.get("events"),
        "chain_head": ledger_meta.get("chain_head"),
        "manifest_sha256": verification.get("manifest_sha256"),
        "anchor_sha256": file_sha256(anchor_path),
        "anchor_source": "external" if external_anchor is not None else "bundle",
        "checkpoint_events": checkpoint_events,
        "checkpoint_keys": sorted(public_keys, key=lambda item: item["key_id"]),
        "evidence": sorted(evidence, key=lambda item: item["name"]),
        "verification": "PASS",
    }


def key_registry(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for entry in entries:
        for key in entry.get("checkpoint_keys") or []:
            key_id = key["key_id"]
            fingerprint = key["public_key_fingerprint"]
            current = registry.get(key_id)
            if current is not None and current["public_key_fingerprint"] != fingerprint:
                raise ValueError(f"checkpoint key id fingerprint changed: {key_id}")
            if current is None:
                current = {
                    "key_id": key_id,
                    "public_key_fingerprint": fingerprint,
                    "first_retained_on": entry["retained_on"],
                    "last_retained_on": entry["retained_on"],
                    "bundle_ids": [],
                }
                registry[key_id] = current
            current["first_retained_on"] = min(current["first_retained_on"], entry["retained_on"])
            current["last_retained_on"] = max(current["last_retained_on"], entry["retained_on"])
            current["bundle_ids"].append(entry["bundle_id"])
    for item in registry.values():
        item["bundle_ids"] = sorted(set(item["bundle_ids"]))
    return sorted(registry.values(), key=lambda item: (item["first_retained_on"], item["key_id"]))


def catalog_payload(entries: list[dict[str, Any]], policy_path: Path, policy: dict[str, Any]) -> dict[str, Any]:
    ordered = sorted(entries, key=lambda item: (item["retained_on"], item["bundle_id"]))
    return {
        "version": 1,
        "catalog_type": CATALOG_TYPE,
        "policy": {
            "policy_id": policy["policy_id"],
            "sha256": file_sha256(policy_path),
        },
        "entries": ordered,
        "checkpoint_key_registry": key_registry(ordered),
        "authority": {
            "evidence_only": True,
            "automatic_delete": False,
            "deletion_authorized": False,
            "approval_authorized": False,
            "merge_authorized": False,
            "release_authorized": False,
            "production_authorized": False,
        },
    }


def build_catalog(policy_path: Path, descriptors: list[Path], output: Path) -> dict[str, Any]:
    if output.exists():
        raise ValueError(f"catalog output already exists: {output}")
    if not descriptors:
        raise ValueError("at least one catalog entry is required")
    policy = load_policy(policy_path)
    entries = [build_entry(load_descriptor(path), policy) for path in descriptors]
    bundle_ids = [item["bundle_id"] for item in entries]
    if len(bundle_ids) != len(set(bundle_ids)):
        raise ValueError("duplicate bundle_id in catalog entries")
    payload = catalog_payload(entries, policy_path, policy)
    catalog = dict(payload)
    catalog["catalog_fingerprint"] = sha256_text(canonical_json(payload))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(canonical_json(catalog) + "\n", encoding="utf-8")
    return {
        "status": "CATALOG_CREATED",
        "catalog": str(output),
        "entries": len(entries),
        "checkpoint_keys": len(payload["checkpoint_key_registry"]),
        "catalog_fingerprint": catalog["catalog_fingerprint"],
        "deletion_authorized": False,
    }


def verify_catalog(catalog_path: Path, policy_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    catalog = load_json_mapping(catalog_path, "catalog")
    policy = load_policy(policy_path)
    if catalog.get("version") != 1 or catalog.get("catalog_type") != CATALOG_TYPE:
        errors.append("unsupported audit catalog")
    fingerprint = str(catalog.get("catalog_fingerprint") or "")
    payload = {k: v for k, v in catalog.items() if k != "catalog_fingerprint"}
    expected_fingerprint = sha256_text(canonical_json(payload))
    if fingerprint != expected_fingerprint:
        errors.append("catalog fingerprint mismatch")
    policy_meta = catalog.get("policy") or {}
    if policy_meta.get("policy_id") != policy["policy_id"]:
        errors.append("catalog policy_id mismatch")
    if policy_meta.get("sha256") != file_sha256(policy_path):
        errors.append("catalog policy sha256 mismatch")
    authority = catalog.get("authority") or {}
    if authority.get("automatic_delete") is not False or authority.get("deletion_authorized") is not False:
        errors.append("catalog must not authorize deletion")
    entries = catalog.get("entries") or []
    if not isinstance(entries, list):
        errors.append("catalog entries must be a list")
        entries = []
    ids = [str(item.get("bundle_id") or "") for item in entries if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        errors.append("catalog contains duplicate bundle_id")
    try:
        expected_registry = key_registry([item for item in entries if isinstance(item, dict)])
        if catalog.get("checkpoint_key_registry") != expected_registry:
            errors.append("checkpoint key registry mismatch")
    except ValueError as exc:
        errors.append(str(exc))
    return {
        "status": "PASS" if not errors else "FAIL",
        "entries": len(entries),
        "catalog_fingerprint": fingerprint,
        "errors": errors,
    }


def find_catalog(catalog_path: Path, policy_path: Path, args: argparse.Namespace) -> dict[str, Any]:
    verified = verify_catalog(catalog_path, policy_path)
    if verified["status"] != "PASS":
        return verified
    catalog = load_json_mapping(catalog_path, "catalog")
    matches = []
    for entry in catalog.get("entries") or []:
        if args.bundle_id and entry.get("bundle_id") != args.bundle_id:
            continue
        if args.subject_id and (entry.get("subject") or {}).get("id") != args.subject_id:
            continue
        if args.repository_revision and entry.get("repository_revision") != args.repository_revision.lower():
            continue
        if args.chain_head and entry.get("chain_head") != args.chain_head:
            continue
        if args.key_id and args.key_id not in {item.get("key_id") for item in entry.get("checkpoint_keys") or []}:
            continue
        matches.append(entry)
    return {
        "status": "PASS",
        "matches": matches,
        "count": len(matches),
        "catalog_fingerprint": catalog.get("catalog_fingerprint"),
    }


def minimal_record(entry: dict[str, Any]) -> dict[str, Any]:
    value = {
        "bundle_id": entry["bundle_id"],
        "subject": entry["subject"],
        "sal": entry["sal"],
        "repository_revision": entry["repository_revision"],
        "events": entry["events"],
        "chain_head": entry["chain_head"],
        "manifest_sha256": entry["manifest_sha256"],
        "anchor_sha256": entry["anchor_sha256"],
        "checkpoint_keys": entry.get("checkpoint_keys") or [],
        "evidence": entry.get("evidence") or [],
    }
    value["record_fingerprint"] = sha256_text(canonical_json(value))
    return value


def retention_plan(catalog_path: Path, policy_path: Path, as_of: date) -> dict[str, Any]:
    verified = verify_catalog(catalog_path, policy_path)
    if verified["status"] != "PASS":
        return verified
    catalog = load_json_mapping(catalog_path, "catalog")
    policy = load_policy(policy_path)
    actions = []
    for entry in catalog.get("entries") or []:
        retained = parse_iso_date(entry["retained_on"], f"{entry['bundle_id']}.retained_on")
        if as_of < retained:
            raise ValueError(f"as-of date precedes retained_on for {entry['bundle_id']}")
        age_days = (as_of - retained).days
        level = policy["levels"][str(entry["sal"])]
        full_days = optional_days(level.get("full_bundle_days"), "full_bundle_days")
        minimal_days = optional_days(level.get("minimal_record_days"), "minimal_record_days")
        key_days = optional_days(level.get("checkpoint_public_key_days"), "checkpoint_public_key_days")

        if entry.get("legal_hold") is True:
            state = "HOLD_FULL"
            review_on = None
        elif full_days is None:
            state = "KEEP_FULL"
            review_on = None
        elif age_days < full_days:
            state = "KEEP_FULL"
            review_on = (retained + timedelta(days=full_days)).isoformat()
        else:
            state = "REVIEW_DUE"
            review_on = (retained + timedelta(days=full_days)).isoformat()

        actions.append({
            "bundle_id": entry["bundle_id"],
            "subject": entry["subject"],
            "sal": entry["sal"],
            "age_days": age_days,
            "state": state,
            "review_on": review_on,
            "legal_hold": entry.get("legal_hold") is True,
            "minimal_record": minimal_record(entry),
            "minimal_record_review_due": minimal_days is not None and age_days >= minimal_days,
            "checkpoint_public_key_review_due": key_days is not None and age_days >= key_days,
            "proposed_action": "HUMAN_REVIEW_FOR_COMPACTION" if state == "REVIEW_DUE" else "NONE",
            "automatic_delete": False,
            "deletion_authorized": False,
        })
    return {
        "status": "PASS",
        "as_of": as_of.isoformat(),
        "policy_id": policy["policy_id"],
        "catalog_fingerprint": catalog.get("catalog_fingerprint"),
        "actions": actions,
        "automatic_delete": False,
        "deletion_authorized": False,
    }


def emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="AIPS Governance Audit retention and verification policy helper")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("catalog-build")
    build.add_argument("--policy", required=True)
    build.add_argument("--output", required=True)
    build.add_argument("--entry", action="append", default=[], required=True)

    verify = sub.add_parser("catalog-verify")
    verify.add_argument("--policy", required=True)
    verify.add_argument("--catalog", required=True)

    find = sub.add_parser("catalog-find")
    find.add_argument("--policy", required=True)
    find.add_argument("--catalog", required=True)
    find.add_argument("--bundle-id")
    find.add_argument("--subject-id")
    find.add_argument("--repository-revision")
    find.add_argument("--chain-head")
    find.add_argument("--key-id")

    plan = sub.add_parser("retention-plan")
    plan.add_argument("--policy", required=True)
    plan.add_argument("--catalog", required=True)
    plan.add_argument("--as-of", required=True)

    args = parser.parse_args()
    try:
        policy_path = Path(args.policy).expanduser().resolve()
        if args.command == "catalog-build":
            result = build_catalog(
                policy_path,
                [Path(item).expanduser().resolve() for item in args.entry],
                Path(args.output).expanduser().resolve(),
            )
        elif args.command == "catalog-verify":
            result = verify_catalog(Path(args.catalog).expanduser().resolve(), policy_path)
        elif args.command == "catalog-find":
            result = find_catalog(Path(args.catalog).expanduser().resolve(), policy_path, args)
        else:
            result = retention_plan(
                Path(args.catalog).expanduser().resolve(),
                policy_path,
                parse_iso_date(args.as_of, "as-of"),
            )
        emit(result)
        return 0 if result.get("status") in {"PASS", "CATALOG_CREATED"} else 2
    except (OSError, ValueError, TypeError, json.JSONDecodeError, yaml.YAMLError) as exc:
        emit({"status": "FAIL", "errors": [str(exc)]})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

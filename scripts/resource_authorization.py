#!/usr/bin/env python3
"""Deterministic pre-execution resource authorization evidence for AIPS."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

KINDS = {"repository_path", "workspace", "runtime_tool", "connector", "external_service"}
OPERATIONS = {"read", "search", "create", "update", "execute"}
MUTATING = {"create", "update", "execute"}


class AuthorizationError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise AuthorizationError("profile must be a mapping")
    return data


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_profile(profile: dict[str, Any]) -> None:
    if profile.get("version") != 1:
        raise AuthorizationError("version must be 1")
    if profile.get("default_effect") != "DENY":
        raise AuthorizationError("default_effect must be DENY")

    subject = profile.get("subject")
    if not isinstance(subject, dict) or not isinstance(subject.get("id"), str) or not subject["id"].strip():
        raise AuthorizationError("subject.id is required")

    grants = profile.get("grants")
    if not isinstance(grants, list):
        raise AuthorizationError("grants must be a list")

    seen: set[str] = set()
    for grant in grants:
        if not isinstance(grant, dict):
            raise AuthorizationError("each grant must be a mapping")
        grant_id = grant.get("id")
        if not isinstance(grant_id, str) or not grant_id.strip():
            raise AuthorizationError("each grant requires id")
        if grant_id in seen:
            raise AuthorizationError(f"duplicate grant id: {grant_id}")
        seen.add(grant_id)

        if grant.get("kind") not in KINDS:
            raise AuthorizationError(f"grant {grant_id}: unsupported kind")
        selector = grant.get("selector")
        if not isinstance(selector, str) or not selector.strip():
            raise AuthorizationError(f"grant {grant_id}: selector is required")
        ops = grant.get("operations")
        if not isinstance(ops, list) or not ops:
            raise AuthorizationError(f"grant {grant_id}: operations must be non-empty")
        if len(set(ops)) != len(ops) or any(op not in OPERATIONS for op in ops):
            raise AuthorizationError(f"grant {grant_id}: unsupported or duplicate operation")

        constraints = grant.get("constraints") or {}
        if not isinstance(constraints, dict):
            raise AuthorizationError(f"grant {grant_id}: constraints must be a mapping")
        for key in ("change_boundary_required", "network_allowed"):
            if key in constraints and not isinstance(constraints[key], bool):
                raise AuthorizationError(f"grant {grant_id}: {key} must be boolean")
        secret_ref = constraints.get("credential_reference")
        if secret_ref is not None and (not isinstance(secret_ref, str) or not secret_ref.strip()):
            raise AuthorizationError(f"grant {grant_id}: credential_reference must be a non-empty reference")
        for forbidden in ("credential", "token", "password", "secret_value", "api_key"):
            if forbidden in constraints:
                raise AuthorizationError(f"grant {grant_id}: secret values are forbidden; use credential_reference")

    authority = profile.get("authority") or {}
    if not isinstance(authority, dict):
        raise AuthorizationError("authority must be a mapping")
    for key in ("human_approval_granted", "merge_authorized", "release_authorized", "protected_operation_authorized"):
        if authority.get(key, False) is not False:
            raise AuthorizationError(f"authority.{key} must remain false")


def render(value: dict[str, Any], fmt: str) -> str:
    if fmt == "json":
        return json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True)


def decision(profile: dict[str, Any], resource_id: str, operation: str, change_boundary: str | None) -> dict[str, Any]:
    grant = next((g for g in profile["grants"] if g["id"] == resource_id), None)
    allowed = False
    reason = "resource_not_granted"
    if grant is not None:
        if operation not in grant["operations"]:
            reason = "operation_not_granted"
        elif operation in MUTATING and (grant.get("constraints") or {}).get("change_boundary_required", False) and not change_boundary:
            reason = "change_boundary_required"
        else:
            allowed = True
            reason = "explicit_grant"

    return {
        "version": 1,
        "status": "ALLOW" if allowed else "DENY",
        "reason": reason,
        "subject": profile["subject"]["id"],
        "resource_id": resource_id,
        "operation": operation,
        "change_boundary": change_boundary,
        "profile_fingerprint": canonical_hash(profile),
        "enforcement": {
            "mode": "PRE_EXECUTION_EVIDENCE",
            "runtime_enforced": False,
            "default_effect": "DENY",
        },
        "authority": {
            "human_approval_granted": False,
            "merge_authorized": False,
            "release_authorized": False,
            "protected_operation_authorized": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--profile", required=True, type=Path)

    p_check = sub.add_parser("check")
    p_check.add_argument("--profile", required=True, type=Path)
    p_check.add_argument("--resource-id", required=True)
    p_check.add_argument("--operation", required=True, choices=sorted(OPERATIONS))
    p_check.add_argument("--change-boundary")

    args = parser.parse_args()
    try:
        profile = load_yaml(args.profile)
        validate_profile(profile)
        if args.command == "validate":
            out = {
                "version": 1,
                "status": "PASS",
                "profile_fingerprint": canonical_hash(profile),
                "default_effect": "DENY",
                "grant_count": len(profile["grants"]),
                "authority": {
                    "human_approval_granted": False,
                    "merge_authorized": False,
                    "release_authorized": False,
                    "protected_operation_authorized": False,
                },
            }
            print(render(out, args.format), end="")
            return 0

        out = decision(profile, args.resource_id, args.operation, args.change_boundary)
        print(render(out, args.format), end="")
        return 0 if out["status"] == "ALLOW" else 1
    except (OSError, yaml.YAMLError, AuthorizationError) as exc:
        print(f"RESOURCE AUTHORIZATION BLOCKED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Deterministic pre-execution resource authorization evidence for AIPS."""

from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path
from typing import Any
import uuid

import yaml
from aips_common import canonical_hash as _aips_canonical_hash

KINDS = {"repository_path", "workspace", "runtime_tool", "connector", "external_service"}
OPERATIONS = {"read", "search", "create", "update", "execute"}
MUTATING = {"create", "update", "execute"}
RECOVERY_ZH = {
    "explicit_grant": "不需額外處理，可依其他適用檢查繼續。",
    "resource_not_granted": "請確認 Resource ID 是否列在 Profile 的 grants 中。",
    "grant_kind_mismatch": "確認 Resource kind 與核准 Grant 相同。",
    "selector_mismatch": "確認資源路徑或目的地主機符合核准 selector。",
    "operation_not_granted": "請求的操作未授權；取得核准後再重試。",
    "change_boundary_required": "提供符合專案核准範圍的 Change Boundary。",
    "network_not_allowed": "此 Grant 禁止網路使用；改用已核准的本機資源。",
    "redirect_not_allowed": "檢查目的地回應；Redirect 預設不允許。",
    "destination_constraint_mismatch": "核對目的地、Port、Method 與 Path 限制。",
}


class AuthorizationError(ValueError):
    def __init__(self, reason_code: str, message: str):
        super().__init__(message)
        self.reason_code = reason_code


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise AuthorizationError("resource_profile_missing", "Resource Authorization profile does not exist.") from exc
    except PermissionError as exc:
        raise AuthorizationError("resource_profile_unreadable", "Resource Authorization profile cannot be read.") from exc
    except OSError as exc:
        raise AuthorizationError("resource_profile_unreadable", "Resource Authorization profile cannot be read.") from exc
    try:
        data = yaml.safe_load(raw.decode("utf-8")) or {}
    except (UnicodeError, yaml.YAMLError) as exc:
        raise AuthorizationError("resource_profile_format_invalid", "Resource Authorization profile is not valid UTF-8 YAML.") from exc
    if not isinstance(data, dict):
        raise AuthorizationError("resource_profile_schema_invalid", "Resource Authorization profile must be a mapping.")
    return data


def canonical_hash(value: Any) -> str:
    return _aips_canonical_hash(value)


def validate_profile(profile: dict[str, Any]) -> None:
    if profile.get("version") != 1:
        raise AuthorizationError("resource_profile_schema_invalid", "version must be 1")
    if profile.get("default_effect") != "DENY":
        raise AuthorizationError("resource_profile_schema_invalid", "default_effect must be DENY")

    subject = profile.get("subject")
    if not isinstance(subject, dict) or not isinstance(subject.get("id"), str) or not subject["id"].strip():
        raise AuthorizationError("resource_profile_schema_invalid", "subject.id is required")

    grants = profile.get("grants")
    if not isinstance(grants, list):
        raise AuthorizationError("resource_profile_schema_invalid", "grants must be a list")

    seen: set[str] = set()
    for grant in grants:
        if not isinstance(grant, dict):
            raise AuthorizationError("resource_profile_schema_invalid", "each grant must be a mapping")
        grant_id = grant.get("id")
        if not isinstance(grant_id, str) or not grant_id.strip():
            raise AuthorizationError("resource_profile_schema_invalid", "each grant requires id")
        if grant_id in seen:
            raise AuthorizationError("resource_profile_schema_invalid", "duplicate grant id")
        seen.add(grant_id)

        if grant.get("kind") not in KINDS:
            raise AuthorizationError("resource_profile_schema_invalid", "grant kind is unsupported")
        selector = grant.get("selector")
        if not isinstance(selector, str) or not selector.strip():
            raise AuthorizationError("resource_profile_schema_invalid", "grant selector is required")
        ops = grant.get("operations")
        if not isinstance(ops, list) or not ops:
            raise AuthorizationError("resource_profile_schema_invalid", "grant operations must be non-empty")
        if len(set(ops)) != len(ops) or any(op not in OPERATIONS for op in ops):
            raise AuthorizationError("resource_profile_schema_invalid", "grant operations are unsupported or duplicated")

        constraints = grant.get("constraints") or {}
        if not isinstance(constraints, dict):
            raise AuthorizationError("resource_profile_schema_invalid", "grant constraints must be a mapping")
        for key in ("change_boundary_required", "network_allowed", "redirects_allowed"):
            if key in constraints and not isinstance(constraints[key], bool):
                raise AuthorizationError("resource_profile_schema_invalid", f"{key} must be boolean")
        for key in ("allowed_destinations", "allowed_paths", "allowed_methods"):
            values = constraints.get(key)
            if values is not None and (not isinstance(values, list) or not values or any(not isinstance(value, str) or not value.strip() for value in values)):
                raise AuthorizationError("resource_profile_schema_invalid", f"{key} must be a non-empty string list")
        ports = constraints.get("allowed_ports")
        if ports is not None and (not isinstance(ports, list) or not ports or any(not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535 for port in ports)):
            raise AuthorizationError("resource_profile_schema_invalid", "allowed_ports must contain valid TCP port numbers")
        secret_ref = constraints.get("credential_reference")
        if secret_ref is not None and (not isinstance(secret_ref, str) or not secret_ref.strip()):
            raise AuthorizationError("resource_profile_schema_invalid", "credential_reference must be a non-empty reference")
        for forbidden in ("credential", "token", "password", "secret_value", "api_key"):
            if forbidden in constraints:
                raise AuthorizationError("resource_profile_schema_invalid", "secret values are forbidden; use credential_reference")

    authority = profile.get("authority") or {}
    if not isinstance(authority, dict):
        raise AuthorizationError("resource_profile_schema_invalid", "authority must be a mapping")
    for key in ("human_approval_granted", "merge_authorized", "release_authorized", "protected_operation_authorized"):
        if authority.get(key, False) is not False:
            raise AuthorizationError("resource_profile_schema_invalid", f"authority.{key} must remain false")


def render(value: dict[str, Any], fmt: str) -> str:
    if fmt == "json":
        return json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True)


def decision(profile: dict[str, Any], resource_id: str, operation: str, change_boundary: str | None, *,
             resource_kind: str | None = None, selector: str | None = None, destination: str | None = None,
             network_used: bool = False, port: int | None = None, method: str | None = None,
             path: str | None = None, redirected: bool = False) -> dict[str, Any]:
    grant = next((g for g in profile["grants"] if g["id"] == resource_id), None)
    allowed = False
    reason = "resource_not_granted"
    if grant is not None:
        constraints = grant.get("constraints") or {}
        target_selector = selector or (destination if resource_kind == "external_service" else resource_id)
        if resource_kind is not None and resource_kind != grant.get("kind"):
            reason = "grant_kind_mismatch"
        elif not isinstance(target_selector, str) or not fnmatch.fnmatchcase(target_selector, grant["selector"]):
            reason = "selector_mismatch"
        elif operation not in grant["operations"]:
            reason = "operation_not_granted"
        elif operation in MUTATING and constraints.get("change_boundary_required", False) and not change_boundary:
            reason = "change_boundary_required"
        elif network_used and constraints.get("network_allowed") is not True:
            reason = "network_not_allowed"
        elif redirected and constraints.get("redirects_allowed", False) is not True:
            reason = "redirect_not_allowed"
        elif constraints.get("allowed_destinations") is not None and (not isinstance(destination, str) or destination.casefold() not in {item.casefold() for item in constraints["allowed_destinations"]}):
            reason = "destination_constraint_mismatch"
        elif constraints.get("allowed_ports") is not None and (port is None or port not in constraints["allowed_ports"]):
            reason = "destination_constraint_mismatch"
        elif constraints.get("allowed_methods") is not None and (not isinstance(method, str) or method.upper() not in {item.upper() for item in constraints["allowed_methods"]}):
            reason = "destination_constraint_mismatch"
        elif constraints.get("allowed_paths") is not None and (not isinstance(path, str) or not any(fnmatch.fnmatchcase(path, item) for item in constraints["allowed_paths"])):
            reason = "destination_constraint_mismatch"
        else:
            allowed = True
            reason = "explicit_grant"

    return {
        "version": 1,
        "status": "ALLOW" if allowed else "DENY",
        "reason": reason,
        "reason_code": reason,
        "phase": "authorization.grant_match",
        "source": "resource_authorization",
        "retryable": False,
        "trace_id": str(uuid.uuid4()),
        "recovery": {"action": RECOVERY_ZH.get(reason, "檢查 Resource Authorization Grant 後再重試。"),
                     "code": "NONE_REQUIRED" if allowed else "REVIEW_APPROVED_GRANT"},
        "subject": profile["subject"]["id"],
        "resource_id": resource_id,
        "operation": operation,
        "change_boundary": change_boundary,
        "resource_kind": resource_kind,
        "selector": selector,
        "destination": destination,
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
    p_check.add_argument("--kind", required=True, choices=sorted(KINDS))
    p_check.add_argument("--selector", required=True)
    p_check.add_argument("--operation", required=True, choices=sorted(OPERATIONS))
    p_check.add_argument("--change-boundary")
    p_check.add_argument("--destination")
    p_check.add_argument("--network-used", action="store_true")
    p_check.add_argument("--port", type=int)
    p_check.add_argument("--method")
    p_check.add_argument("--path")
    p_check.add_argument("--redirected", action="store_true")

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

        out = decision(profile, args.resource_id, args.operation, args.change_boundary,
                       resource_kind=getattr(args, "kind", None), selector=getattr(args, "selector", None),
                       destination=getattr(args, "destination", None), network_used=getattr(args, "network_used", False),
                       port=getattr(args, "port", None), method=getattr(args, "method", None),
                       path=getattr(args, "path", None), redirected=getattr(args, "redirected", False))
        print(render(out, args.format), end="")
        return 0 if out["status"] == "ALLOW" else 1
    except AuthorizationError as exc:
        print(json.dumps({"status": "BLOCKED", "phase": "profile_validation", "reason_code": exc.reason_code,
                          "source": "resource_authorization", "retryable": False,
                          "trace_id": str(uuid.uuid4()), "recovery": {"action": "CHECK_PROFILE_AND_RETRY"}}, ensure_ascii=False))
        return 2
    except (OSError, yaml.YAMLError):
        print(json.dumps({"status": "BLOCKED", "phase": "profile_validation", "reason_code": "resource_profile_invalid",
                          "source": "resource_authorization", "retryable": False,
                          "trace_id": str(uuid.uuid4()), "recovery": {"action": "CHECK_PROFILE_AND_RETRY"}}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

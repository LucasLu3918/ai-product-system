#!/usr/bin/env python3
"""Deterministic, provider-neutral AIPS runtime action policy evaluator."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from content_safety import safe_emit
from resource_authorization import AuthorizationError, decision as authorization_decision, load_yaml as load_authorization_profile, validate_profile as validate_authorization_profile
from semantic_guard import validate_signal
from sandbox_providers import resolve_egress

DECISIONS = {"ALLOW", "DENY", "REQUIRE_APPROVAL", "BLOCKED"}
ENFORCEMENT = {"ADVISORY": 0, "TOOL_GUARDED": 1, "ENFORCED": 2}
DATA_CLASSES = {"public", "internal", "confidential", "restricted"}
DATA_CLASS_PRIORITY = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}
SECRET_KEYS = {"api_key", "credential", "password", "secret", "secret_value", "token"}


class PolicyError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _contains_secret_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in SECRET_KEYS and item not in (None, ""):
                return True
            if _contains_secret_key(item):
                return True
    elif isinstance(value, list):
        return any(_contains_secret_key(item) for item in value)
    return False


def validate_action(action: dict[str, Any]) -> None:
    if action.get("version") != 1:
        raise PolicyError("version must be 1")
    for section in ("actor", "action", "resource", "destination", "context", "data", "authorization", "requirements"):
        if not isinstance(action.get(section), dict):
            raise PolicyError(f"{section} must be a mapping")
    for section, key in (("actor", "task_id"), ("actor", "runtime"), ("action", "tool"),
                         ("action", "operation"), ("resource", "kind"), ("resource", "id")):
        value = (action.get(section) or {}).get(key)
        if not isinstance(value, str) or not value.strip():
            raise PolicyError(f"{section}.{key} is required")
    destination = action["destination"]
    if destination.get("trust") not in {"internal", "approved_external", "external", "unknown"}:
        raise PolicyError("destination.trust is invalid")
    host = destination.get("host")
    if host is not None and (not isinstance(host, str) or not host.strip() or "/" in host):
        raise PolicyError("destination.host must be a hostname or null")
    sal = action["context"].get("effective_sal")
    if sal is not None and (not isinstance(sal, int) or isinstance(sal, bool) or sal < 0 or sal > 4):
        raise PolicyError("context.effective_sal must be an integer from 0 to 4 or null")
    classes = action["data"].get("classes")
    assets = action["data"].get("protected_assets")
    if not isinstance(classes, list) or any(item not in DATA_CLASSES for item in classes):
        raise PolicyError("data.classes must be a list of supported classes")
    if not isinstance(assets, list) or any(not isinstance(item, str) or not item for item in assets):
        raise PolicyError("data.protected_assets must be a list of non-empty strings")
    if _contains_secret_key(action):
        raise PolicyError("secret values are forbidden; use credential_reference")
    if "credential_reference" in action and action["credential_reference"] is not None and not isinstance(action["credential_reference"], str):
        raise PolicyError("credential_reference must be a string reference or null")
    minimum = action["requirements"].get("minimum_enforcement", "ADVISORY")
    if minimum not in ENFORCEMENT:
        raise PolicyError("requirements.minimum_enforcement is invalid")
    provider = action["requirements"].get("sandbox_provider_id")
    if provider is not None and (not isinstance(provider, str) or not provider.strip()):
        raise PolicyError("requirements.sandbox_provider_id must be a string or null")


def action_digest(action: dict[str, Any], *, project_root: Path | None = None) -> str:
    project_root = project_root or ROOT
    profile_fingerprint = None
    profile_path = ((action.get("authorization") or {}).get("resource_profile"))
    if isinstance(profile_path, str) and profile_path:
        try:
            profile_file = (project_root / profile_path).resolve()
            if profile_file.is_relative_to(project_root.resolve()):
                profile = load_authorization_profile(profile_file)
                validate_authorization_profile(profile)
                profile_fingerprint = hashlib.sha256(canonical_json(profile).encode("utf-8")).hexdigest()
        except (OSError, yaml.YAMLError, AuthorizationError):
            pass
    material = {key: action.get(key) for key in (
        "version", "actor", "action", "resource", "destination", "context", "data",
        "credential_reference", "requirements",
    )}
    material["authorization"] = {"resource_profile_fingerprint": profile_fingerprint}
    return "sha256:" + hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()


def policy_digest(policy: dict[str, Any], policy_bytes: bytes | None = None) -> str:
    return "sha256:" + hashlib.sha256(policy_bytes or canonical_json(policy).encode("utf-8")).hexdigest()


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("version") != 1:
        raise PolicyError("policy version must be 1")
    if policy.get("default_effect") != "DENY":
        raise PolicyError("default_effect must be DENY")
    rules = policy.get("rules")
    if not isinstance(rules, list):
        raise PolicyError("rules must be a list")
    seen: set[str] = set()
    for rule in rules:
        if not isinstance(rule, dict):
            raise PolicyError("each policy rule must be a mapping")
        if not isinstance(rule.get("id"), str) or not rule["id"].strip() or rule["id"] in seen:
            raise PolicyError("each policy rule requires a unique id")
        seen.add(rule["id"])
        if rule.get("effect") not in DECISIONS - {"ALLOW", "BLOCKED"} | {"ALLOW"}:
            raise PolicyError(f"rule {rule['id']}: unsupported effect")
        if not isinstance(rule.get("priority", 0), int):
            raise PolicyError(f"rule {rule['id']}: priority must be an integer")
        if not isinstance(rule.get("when") or {}, dict):
            raise PolicyError(f"rule {rule['id']}: when must be a mapping")


def _matches(action: dict[str, Any], condition: dict[str, Any], contains_secret: bool) -> bool:
    trust = action["destination"].get("trust")
    if "destination_trust" in condition and trust not in condition["destination_trust"]:
        return False
    minimum_sal = condition.get("effective_sal_gte")
    if minimum_sal is not None:
        sal = action["context"].get("effective_sal")
        if sal is None or sal < minimum_sal:
            return False
    maximum_sal = condition.get("effective_sal_lte")
    if maximum_sal is not None:
        sal = action["context"].get("effective_sal")
        if sal is None or sal > maximum_sal:
            return False
    classes = set(action["data"].get("classes") or [])
    if "data_class_any" in condition and not classes.intersection(condition["data_class_any"]):
        return False
    assets = set(action["data"].get("protected_assets") or [])
    if "protected_asset_any" in condition and not assets.intersection(condition["protected_asset_any"]):
        return False
    if condition.get("contains_secret") is True and not contains_secret:
        return False
    return True


def _approval_valid(path: Path | None, digest: str, policy_fingerprint: str, action: dict[str, Any]) -> tuple[bool, str]:
    if path is None or not path.is_file():
        return False, "runtime approval record unavailable"
    try:
        record = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return False, "runtime approval record invalid"
    approval = record.get("approval") or {}
    scope = record.get("scope") or {}
    try:
        from governance_guard import verify_record
        valid_binding, binding_reason, _ = verify_record(path, "external_data_egress", ROOT, check_actual=False)
        if not valid_binding:
            return False, "runtime Approval Record binding is stale: " + binding_reason
    except Exception:
        return False, "runtime Approval Record binding could not be verified"
    if approval.get("status") != "APPROVED" or approval.get("type") not in {"runtime_action", "runtime_policy"}:
        return False, "runtime action approval is not APPROVED"
    if "external_data_egress" not in (scope.get("operations") or []):
        return False, "approval operation is outside runtime action scope"
    if scope.get("action_digest") != digest:
        return False, "approval action digest is stale"
    if scope.get("policy_digest") != policy_fingerprint:
        return False, "approval policy digest is stale"
    if scope.get("destination") != action["destination"].get("host"):
        return False, "approval destination is stale"
    if scope.get("change_boundary") != action["context"].get("change_boundary"):
        return False, "approval Change Boundary is stale"
    if sorted(scope.get("data_classes") or []) != sorted(action["data"].get("classes") or []):
        return False, "approval data classification is stale"
    if sorted(scope.get("protected_assets") or []) != sorted(action["data"].get("protected_assets") or []):
        return False, "approval protected assets are stale"
    expires = approval.get("expires_at") or scope.get("expires_at")
    if not isinstance(expires, str):
        return False, "runtime action approval expiry is required"
    try:
        expiry = datetime.fromisoformat(expires.replace("Z", "+00:00"))
    except ValueError:
        return False, "runtime action approval expiry is invalid"
    if expiry.tzinfo is None or expiry <= datetime.now(timezone.utc):
        return False, "runtime action approval is expired"
    return True, "scope-bound runtime approval valid"


def evaluate(action: dict[str, Any], policy: dict[str, Any], *, runtime_capability: str,
             policy_bytes: bytes | None = None, approval_path: Path | None = None,
             semantic_signal: dict[str, Any] | None = None, project_root: Path | None = None,
             sandbox_evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    validate_action(action)
    validate_policy(policy)
    if runtime_capability not in ENFORCEMENT:
        return {"version": 1, "decision": "BLOCKED", "reason": "runtime enforcement capability unknown",
                "action_digest": action_digest(action)}
    project_root = project_root or ROOT
    digest = action_digest(action, project_root=project_root)
    current_policy_digest = policy_digest(policy, policy_bytes)
    profile_path = ((action.get("authorization") or {}).get("resource_profile"))
    if not isinstance(profile_path, str) or not profile_path.strip():
        return {"version": 1, "decision": "BLOCKED", "reason": "Resource Authorization profile unavailable", "action_digest": digest}
    try:
        profile_file = (project_root / profile_path).resolve()
        if not profile_file.is_relative_to(project_root.resolve()):
            raise PolicyError("Resource Authorization profile must remain inside the project")
        profile = load_authorization_profile(profile_file)
        validate_authorization_profile(profile)
        auth_operation = "execute" if action["action"]["operation"] == "external_data_egress" else action["action"]["operation"]
        auth = authorization_decision(profile, action["resource"]["id"], auth_operation, action["context"].get("change_boundary"))
    except (OSError, yaml.YAMLError, AuthorizationError, PolicyError) as exc:
        return {"version": 1, "decision": "BLOCKED", "reason": "Resource Authorization failed: " + str(exc), "action_digest": digest}
    if auth["status"] != "ALLOW":
        return {"version": 1, "decision": "DENY", "reason": "Resource Authorization denied action", "action_digest": digest}
    serialized = canonical_json(action.get("action", {}).get("arguments"))
    content = safe_emit(sink="source_artifact", payload={"arguments": serialized})
    contains_secret = content.get("decision") in {"BLOCK", "REDACT"}
    host = action["destination"].get("host")
    allowlist = {str(item).lower() for item in policy.get("external_destination_allowlist", [])}
    trust = action["destination"].get("trust")
    if trust in {"external", "approved_external"} and (not host or host.lower() not in allowlist):
        return {"version": 1, "decision": "DENY", "reason": "external destination is not allowlisted",
                "action_digest": digest, "policy_digest": current_policy_digest}
    if trust in {"external", "approved_external"} and action["context"].get("effective_sal") is None:
        return {"version": 1, "decision": "BLOCKED", "reason": "effective SAL is unknown for external action",
                "action_digest": digest}
    matches = [r for r in policy["rules"] if _matches(action, r.get("when") or {}, contains_secret)]
    matches.sort(key=lambda r: (-r.get("priority", 0), r["id"]))
    if any(r["effect"] == "DENY" for r in matches):
        decision, reason = "DENY", "policy deny-overrides"
        rule_ids = [r["id"] for r in matches if r["effect"] == "DENY"]
    else:
        requiring = [r for r in matches if r["effect"] == "REQUIRE_APPROVAL"]
        rule_ids = [r["id"] for r in matches]
        allowing = [r for r in matches if r["effect"] == "ALLOW"]
        decision, reason = ("REQUIRE_APPROVAL", "policy requires scoped human approval") if requiring else (("ALLOW", "explicit policy allow") if allowing else ("DENY", "no allow policy matched"))
    minima = [action["requirements"].get("minimum_enforcement", "ADVISORY")]
    minima.extend((r.get("requirements") or {}).get("minimum_enforcement", "ADVISORY") for r in matches)
    minimum = max(minima, key=lambda item: ENFORCEMENT[item])
    if ENFORCEMENT[runtime_capability] < ENFORCEMENT[minimum]:
        decision, reason = "BLOCKED", "required runtime enforcement capability unavailable"
    if decision == "REQUIRE_APPROVAL":
        requires_sandbox = any((r.get("requirements") or {}).get("sandbox_network_enforced") for r in matches if r["effect"] == "REQUIRE_APPROVAL")
        provider_id = action["requirements"].get("sandbox_provider_id")
        sandbox_result = sandbox_evidence or resolve_egress(project_root or ROOT, host=host,
                                                               data_class=max(action["data"].get("classes") or ["public"], key=lambda x: DATA_CLASS_PRIORITY[x]))
        provider_verified = bool(sandbox_result.get("status") == "AVAILABLE"
                                  and sandbox_result.get("host") == host
                                  and sandbox_result.get("data_class") in action["data"].get("classes", [])
                                  and (not provider_id or sandbox_result.get("provider") == provider_id))
        if requires_sandbox and not provider_verified:
            decision, reason = "BLOCKED", "required sandbox network enforcement unavailable: " + str(sandbox_result.get("reason", "verification missing"))
        else:
            valid, approval_reason = _approval_valid(approval_path, digest, current_policy_digest, action)
            if valid:
                decision, reason = "ALLOW", approval_reason
            elif approval_path is not None and approval_path.is_file():
                decision, reason = "BLOCKED", "APPROVAL_STALE: " + approval_reason
            else:
                reason += ": " + approval_reason
    if decision == "ALLOW" and semantic_signal is not None:
        try:
            validated_signal = validate_signal(semantic_signal, expected_action_digest=digest)
            semantic_decision = validated_signal["decision"]
        except ValueError:
            decision, reason = "BLOCKED", "optional semantic guard returned an invalid or mismatched result"
            semantic_decision = None
        if semantic_decision in {"DENY", "ESCALATE"}:
            decision = "DENY" if semantic_decision == "DENY" else "REQUIRE_APPROVAL"
            reason = "optional semantic guard tightened deterministic result"
        elif semantic_decision is not None and semantic_decision != "ALLOW":
            decision, reason = "BLOCKED", "optional semantic guard returned an invalid result"
    return {"version": 1, "decision": decision, "reason": reason, "action_digest": digest,
            "policy_digest": current_policy_digest, "matched_rules": rule_ids, "runtime_capability": runtime_capability,
            "audit": {"event_type": "RUNTIME_ACTION_" + decision, "action_digest": digest,
                      "policy_digest": current_policy_digest, "destination_host": host, "rule_ids": rule_ids,
                      "resource_authorization_fingerprint": auth.get("profile_fingerprint")}}


def classify_url(value: str) -> tuple[str | None, str]:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None, "unknown"
    return parsed.hostname.lower(), "external"


def action_from_hook(payload: dict[str, Any], runtime: str) -> dict[str, Any] | None:
    explicit = payload.get("aips_runtime_action")
    if isinstance(explicit, dict):
        return explicit
    tool_input = payload.get("tool_input") or {}
    tool_name = str(payload.get("tool_name") or "unknown")
    command = str(tool_input.get("command") or "")
    # Only classify direct, visible HTTP(S) CLI URLs. Scripts, child processes,
    # SDK calls and arbitrary shell syntax require OS/sandbox network enforcement.
    match = re.search(r"https?://[^\s'\"<>]+", command)
    if not match or not re.search(r"(?:^|[;&|\s])(curl|wget)(?:\s|$)", command):
        return None
    host, trust = classify_url(match.group(0).rstrip(",);]"))
    return {"version": 1, "actor": {"task_id": str(payload.get("session_id") or "runtime-hook"), "runtime": runtime},
            "action": {"tool": tool_name, "operation": "external_data_egress", "arguments": {"command": "[redacted]"}},
            "resource": {"kind": "external_service", "id": host or "unresolved-host"},
            "destination": {"host": host, "trust": trust},
            "context": {"effective_sal": None, "change_boundary": None},
            "data": {"classes": [], "protected_assets": []},
            "authorization": {"resource_profile": os.environ.get("AIPS_RESOURCE_AUTHORIZATION_PROFILE")},
            "requirements": {"minimum_enforcement": "TOOL_GUARDED", "sandbox_provider_id": None}}


def load_policy(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    doc = yaml.safe_load(raw) or {}
    if not isinstance(doc, dict):
        raise PolicyError("runtime policy must be a mapping")
    return doc, raw


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    sub = parser.add_subparsers(dest="command", required=True)
    ep = sub.add_parser("evaluate")
    ep.add_argument("--action", required=True, type=Path)
    ep.add_argument("--policy", type=Path, default=ROOT / "config/runtime-policy.yaml")
    ep.add_argument("--runtime-capability", default="ADVISORY", choices=sorted(ENFORCEMENT))
    ep.add_argument("--approval", type=Path)
    ep.add_argument("--project-root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        policy, raw = load_policy(args.policy)
        action = yaml.safe_load(args.action.read_text(encoding="utf-8")) or {}
        decision = evaluate(action, policy, runtime_capability=args.runtime_capability,
                            policy_bytes=raw, approval_path=args.approval, project_root=args.project_root)
        rendered = json.dumps(decision, indent=2, ensure_ascii=False) if args.format == "json" else yaml.safe_dump(decision, sort_keys=False, allow_unicode=True)
        print(rendered, end="")
        return 0 if decision["decision"] == "ALLOW" else 1
    except (OSError, yaml.YAMLError, PolicyError) as exc:
        print(yaml.safe_dump({"version": 1, "decision": "BLOCKED", "reason": str(exc)}, sort_keys=False), end="")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

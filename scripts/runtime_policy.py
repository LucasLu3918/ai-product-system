#!/usr/bin/env python3
"""Deterministic, provider-neutral AIPS runtime action policy evaluator."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import shlex
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from content_safety import safe_emit
from creative_errors import RECOVERY, redact
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
    port = destination.get("port")
    if port is not None and (not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535):
        raise PolicyError("destination.port must be a valid TCP port or null")
    for key in ("method", "path"):
        value = destination.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip() or len(value) > 2048 or "\r" in value or "\n" in value):
            raise PolicyError(f"destination.{key} must be a bounded non-empty string or null")
    if not isinstance(destination.get("redirected", False), bool):
        raise PolicyError("destination.redirected must be boolean")
    selector = action["resource"].get("selector")
    if selector is not None and (not isinstance(selector, str) or not selector.strip() or len(selector) > 2048):
        raise PolicyError("resource.selector must be a bounded non-empty string or null")
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


def _result(decision: str, reason: str, *, reason_code: str, phase: str = "runtime_policy",
            source: str = "runtime_policy", retryable: bool = False,
            recovery_action: str = "CHECK_RUNTIME_POLICY_AND_RETRY", **fields: Any) -> dict[str, Any]:
    return {"version": 1, "decision": decision, "status": decision, "phase": phase,
            "reason_code": reason_code, "source": source, "retryable": retryable,
            "trace_id": str(uuid.uuid4()), "recovery": {"action": RECOVERY.get(reason_code, "檢查已核准的 Runtime Policy 範圍後重新評估。"),
                                                        "code": recovery_action},
            "reason": redact(reason), **fields}


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("version") != 1:
        raise PolicyError("policy version must be 1")
    if policy.get("default_effect") != "DENY":
        raise PolicyError("default_effect must be DENY")
    rules = policy.get("rules")
    if not isinstance(rules, list):
        raise PolicyError("rules must be a list")
    seen: set[str] = set()
    condition_keys = {
        "destination_trust", "destination_host", "destination_port",
        "destination_method", "destination_path", "effective_sal_gte",
        "effective_sal_lte", "data_class_any", "protected_asset_any",
        "contains_secret",
    }
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
        condition = rule.get("when") or {}
        if not isinstance(condition, dict):
            raise PolicyError(f"rule {rule['id']}: when must be a mapping")
        unknown = set(condition) - condition_keys
        if unknown:
            raise PolicyError(f"rule {rule['id']}: unsupported condition key(s): {', '.join(sorted(unknown))}")
        for key in ("destination_host", "destination_path"):
            value = condition.get(key)
            if value is not None and (not isinstance(value, str) or not value.strip() or len(value) > 2048
                                      or "\r" in value or "\n" in value):
                raise PolicyError(f"rule {rule['id']}: {key} must be a bounded non-empty string")
        if condition.get("destination_host") is not None and "/" in condition["destination_host"]:
            raise PolicyError(f"rule {rule['id']}: destination_host must be a hostname or IP address")
        port = condition.get("destination_port")
        if port is not None and (not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535):
            raise PolicyError(f"rule {rule['id']}: destination_port must be an integer from 1 to 65535")
        method = condition.get("destination_method")
        if method is not None and (not isinstance(method, str) or not re.fullmatch(r"[A-Z]+", method)):
            raise PolicyError(f"rule {rule['id']}: destination_method must be an uppercase HTTP method")
        trust = condition.get("destination_trust")
        if trust is not None and (not isinstance(trust, list)
                                  or any(item not in {"internal", "approved_external", "external", "unknown"}
                                         for item in trust)):
            raise PolicyError(f"rule {rule['id']}: destination_trust must be a list of supported trust levels")
        for key in ("effective_sal_gte", "effective_sal_lte"):
            value = condition.get(key)
            if value is not None and (not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 4):
                raise PolicyError(f"rule {rule['id']}: {key} must be an integer from 0 to 4")
        for key in ("data_class_any", "protected_asset_any"):
            value = condition.get(key)
            if value is not None and (not isinstance(value, list)
                                      or any(not isinstance(item, str) or not item for item in value)):
                raise PolicyError(f"rule {rule['id']}: {key} must be a list of non-empty strings")
        if "data_class_any" in condition and any(item not in DATA_CLASSES for item in condition["data_class_any"]):
            raise PolicyError(f"rule {rule['id']}: data_class_any contains an unsupported data class")
        if "contains_secret" in condition and not isinstance(condition["contains_secret"], bool):
            raise PolicyError(f"rule {rule['id']}: contains_secret must be boolean")


def _matches(action: dict[str, Any], condition: dict[str, Any], contains_secret: bool) -> bool:
    destination = action["destination"]
    trust = destination.get("trust")
    if "destination_trust" in condition and trust not in condition["destination_trust"]:
        return False
    exact_destination = {
        "destination_host": (destination.get("host") or "").lower(),
        "destination_port": destination.get("port"),
        "destination_method": (destination.get("method") or "").upper(),
        "destination_path": destination.get("path"),
    }
    for key, observed in exact_destination.items():
        if key in condition:
            expected = condition[key]
            if key == "destination_host":
                expected = expected.lower()
            if observed != expected:
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
        return _result("BLOCKED", "runtime enforcement capability unknown", reason_code="runtime_capability_unknown",
                       phase="runtime_policy.enforcement", recovery_action="VERIFY_RUNTIME_CAPABILITY",
                       action_digest=action_digest(action))
    project_root = project_root or ROOT
    digest = action_digest(action, project_root=project_root)
    current_policy_digest = policy_digest(policy, policy_bytes)
    profile_path = ((action.get("authorization") or {}).get("resource_profile"))
    if not isinstance(profile_path, str) or not profile_path.strip():
        return _result("BLOCKED", "Resource Authorization profile was not provided by the runtime configuration.",
                       reason_code="resource_profile_not_provided", phase="authorization.profile_resolution",
                       source="resource_authorization", recovery_action="CONFIGURE_TRUSTED_PROFILE",
                       action_digest=digest)
    try:
        profile_file = (project_root / profile_path).resolve(strict=True)
        if not profile_file.is_relative_to(project_root.resolve()):
            return _result("BLOCKED", "Resource Authorization profile must remain inside the project.",
                           reason_code="resource_profile_outside_project", phase="authorization.profile_resolution",
                           source="resource_authorization", recovery_action="USE_PROJECT_PROFILE",
                           action_digest=digest)
        profile = load_authorization_profile(profile_file)
        validate_authorization_profile(profile)
        auth_operation = "execute" if action["action"]["operation"] == "external_data_egress" else action["action"]["operation"]
        destination = action["destination"]
        resource = action["resource"]
        auth = authorization_decision(
            profile, resource["id"], auth_operation, action["context"].get("change_boundary"),
            resource_kind=resource["kind"], selector=resource.get("selector"), destination=destination.get("host"),
            network_used=(action["action"]["operation"] == "external_data_egress"),
            port=destination.get("port"), method=destination.get("method"), path=destination.get("path"),
            redirected=destination.get("redirected", False),
        )
    except FileNotFoundError:
        return _result("BLOCKED", "Resource Authorization profile does not exist.", reason_code="resource_profile_missing",
                       phase="authorization.profile_resolution", source="resource_authorization",
                       recovery_action="CHECK_PROFILE_PATH", action_digest=digest)
    except PermissionError:
        return _result("BLOCKED", "Resource Authorization profile cannot be read.", reason_code="resource_profile_unreadable",
                       phase="authorization.profile_resolution", source="resource_authorization",
                       recovery_action="CHECK_PROFILE_PERMISSIONS", action_digest=digest)
    except AuthorizationError as exc:
        return _result("BLOCKED", str(exc), reason_code=exc.reason_code,
                       phase="authorization.profile_validation", source="resource_authorization",
                       recovery_action="CHECK_PROFILE_AND_RETRY", action_digest=digest)
    except (OSError, yaml.YAMLError, PolicyError):
        return _result("BLOCKED", "Resource Authorization profile could not be safely loaded.",
                       reason_code="resource_profile_unreadable", phase="authorization.profile_resolution",
                       source="resource_authorization", recovery_action="CHECK_PROFILE_PATH_AND_PERMISSIONS",
                       action_digest=digest)
    if auth["status"] != "ALLOW":
        return _result("DENY", "Resource Authorization denied action: " + auth["reason"],
                       reason_code=auth["reason"], phase="authorization.grant_match",
                       source="resource_authorization", recovery_action="REVIEW_APPROVED_GRANT",
                       action_digest=digest, authorization=auth)
    serialized = canonical_json(action.get("action", {}).get("arguments"))
    content = safe_emit(sink="source_artifact", payload={"arguments": serialized})
    contains_secret = content.get("decision") in {"BLOCK", "REDACT"}
    host = action["destination"].get("host")
    allowlist = {str(item).lower() for item in policy.get("external_destination_allowlist", [])}
    trust = action["destination"].get("trust")
    if trust in {"external", "approved_external"} and (not host or host.lower() not in allowlist):
        return _result("DENY", "external destination is not allowlisted", reason_code="destination_not_allowlisted",
                       phase="runtime_policy.destination", recovery_action="USE_ALLOWLISTED_DESTINATION",
                       action_digest=digest, policy_digest=current_policy_digest)
    if trust in {"external", "approved_external"} and action["context"].get("effective_sal") is None:
        return _result("BLOCKED", "effective SAL is unknown for external action", reason_code="effective_sal_unknown",
                       phase="runtime_policy.classification", recovery_action="CLASSIFY_ACTION_RISK",
                       action_digest=digest)
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
    reason_codes = {"ALLOW": "policy_allow", "DENY": "policy_denied", "REQUIRE_APPROVAL": "approval_required", "BLOCKED": "runtime_policy_blocked"}
    recovery = {"ALLOW": "NONE_REQUIRED", "DENY": "REVIEW_POLICY_AND_SCOPE", "REQUIRE_APPROVAL": "REQUEST_SCOPED_HUMAN_APPROVAL", "BLOCKED": "CHECK_RUNTIME_CAPABILITY_AND_EVIDENCE"}
    return _result(decision, reason, reason_code=reason_codes[decision], phase="runtime_policy.decision",
                   source="runtime_policy", recovery_action=recovery[decision], retryable=False,
                   action_digest=digest, policy_digest=current_policy_digest, matched_rules=rule_ids,
                   runtime_capability=runtime_capability,
                   audit={"event_type": "RUNTIME_ACTION_" + decision, "action_digest": digest,
                          "policy_digest": current_policy_digest, "destination_host": host, "rule_ids": rule_ids,
                          "resource_authorization_fingerprint": auth.get("profile_fingerprint")})


def classify_url(value: str) -> tuple[str | None, str]:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None, "unknown"
    host = parsed.hostname.lower()
    try:
        if ipaddress.ip_address(host).is_loopback:
            return host, "internal"
    except ValueError:
        pass
    return host, "external"


def action_from_hook(payload: dict[str, Any], runtime: str) -> dict[str, Any] | None:
    explicit = payload.get("aips_runtime_action")
    tool_input = payload.get("tool_input") or {}
    tool_name = str(payload.get("tool_name") or "unknown")
    command = str(tool_input.get("command") or "")
    # Only classify visible curl/wget URLs. Complex shell, scripts, child
    # processes and SDK calls cannot borrow a model-supplied Runtime Action.
    match = re.search(r"https?://[^\s'\"<>]+", command)
    if not match or not re.search(r"(?:^|[;&|\s])(curl|wget)(?:\s|$)", command):
        return None
    raw_url = match.group(0).rstrip(",);]")
    host, trust = classify_url(raw_url)
    try:
        parsed_command = shlex.split(command)
    except ValueError:
        parsed_command = []
    direct = bool(parsed_command and Path(parsed_command[0]).name in {"curl", "wget"})
    method = "GET"
    if direct and parsed_command[0].endswith("curl"):
        for index, token in enumerate(parsed_command[:-1]):
            if token in {"-X", "--request"}:
                method = parsed_command[index + 1].upper()
                break
        if "-I" in parsed_command or "--head" in parsed_command:
            method = "HEAD"
    observed = urlparse(raw_url)
    observed_host = host if direct else None
    observed_id = host if direct and host else "unresolved-host"
    # A top-level action is accepted only when its claimed tool/operation and
    # resource host bind to the actual direct command. Its authority metadata is
    # still rebuilt from the host event and trusted environment.
    explicit_action = explicit.get("action") if isinstance(explicit, dict) else {}
    explicit_resource = explicit.get("resource") if isinstance(explicit, dict) else {}
    explicit_destination = explicit.get("destination") if isinstance(explicit, dict) else {}
    explicit_action = explicit_action if isinstance(explicit_action, dict) else {}
    explicit_resource = explicit_resource if isinstance(explicit_resource, dict) else {}
    explicit_destination = explicit_destination if isinstance(explicit_destination, dict) else {}
    bound = (isinstance(explicit, dict)
             and explicit_action.get("tool") == tool_name
             and explicit_action.get("operation") == "external_data_egress"
             and explicit_resource.get("kind") == "external_service"
             and explicit_resource.get("id") == observed_id
             and explicit_destination.get("host") == observed_host)
    context = explicit.get("context") if bound else {}
    data = explicit.get("data") if bound else {}
    requirements = explicit.get("requirements") if bound else {}
    return {"version": 1, "actor": {"task_id": str(payload.get("session_id") or "runtime-hook"), "runtime": runtime},
            "action": {"tool": tool_name, "operation": "external_data_egress", "arguments": {"command": "[redacted]"}},
            "resource": {"kind": "external_service", "id": observed_id, "selector": observed_host},
            "destination": {"host": observed_host, "trust": trust if direct else "unknown",
                            "port": observed.port or (443 if observed.scheme == "https" else 80),
                            "method": method if direct else None, "path": observed.path or "/" if direct else None},
            "context": {"effective_sal": context.get("effective_sal") if isinstance(context, dict) else None,
                        "change_boundary": context.get("change_boundary") if isinstance(context, dict) else None},
            "data": {"classes": data.get("classes", []) if isinstance(data, dict) else [],
                     "protected_assets": data.get("protected_assets", []) if isinstance(data, dict) else []},
            "authorization": {"resource_profile": os.environ.get("AIPS_RESOURCE_AUTHORIZATION_PROFILE")},
            "requirements": {"minimum_enforcement": (requirements.get("minimum_enforcement", "TOOL_GUARDED")
                                                         if isinstance(requirements, dict) else "TOOL_GUARDED"),
                             "sandbox_provider_id": requirements.get("sandbox_provider_id") if isinstance(requirements, dict) else None}}


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
    except (OSError, yaml.YAMLError, PolicyError):
        result = _result("BLOCKED", "Runtime Policy input could not be safely loaded.",
                         reason_code="runtime_policy_input_invalid", phase="runtime_policy.input",
                         recovery_action="CHECK_POLICY_AND_ACTION_FILES")
        print(yaml.safe_dump(result, sort_keys=False, allow_unicode=True), end="")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

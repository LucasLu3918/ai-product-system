#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import runtime_policy as policy
from governance_guard import fingerprint


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def base_action() -> dict:
    return {
        "version": 1,
        "actor": {"task_id": "runtime-policy-test", "runtime": "claude-code"},
        "action": {"tool": "http_request", "operation": "external_data_egress", "arguments": {"body": "synthetic public fixture"}},
        "resource": {"kind": "external_service", "id": "analytics-provider"},
        "destination": {"host": "analytics.example.com", "trust": "approved_external"},
        "context": {"effective_sal": 1, "change_boundary": "runtime-policy-test"},
        "data": {"classes": ["public"], "protected_assets": []},
        "authorization": {"resource_profile": "tests/fixtures/runtime_policy/resource-authorization.yaml"},
        "requirements": {"minimum_enforcement": "TOOL_GUARDED", "sandbox_provider_id": None},
    }


def base_config() -> dict:
    doc = yaml.safe_load((ROOT / "config/runtime-policy.yaml").read_text())
    doc["external_destination_allowlist"] = ["analytics.example.com"]
    return doc


def main() -> int:
    action = base_action()
    cfg = base_config()
    result = policy.evaluate(action, cfg, runtime_capability="TOOL_GUARDED")
    require(result["decision"] == "ALLOW", f"low-risk allow failed: {result}")

    changed = copy.deepcopy(action)
    changed["action"]["arguments"]["body"] += " changed"
    require(policy.action_digest(changed) != policy.action_digest(action), "arguments are missing from action digest")

    high_risk = copy.deepcopy(action)
    high_risk["context"]["effective_sal"] = 4
    high_risk["data"] = {"classes": ["restricted"], "protected_assets": ["financial_state"]}
    high_risk["requirements"]["sandbox_provider_id"] = "verified-test-sandbox"
    blocked = policy.evaluate(high_risk, cfg, runtime_capability="TOOL_GUARDED")
    require(blocked["decision"] == "BLOCKED", f"unverified sandbox must block: {blocked}")

    approval_scope = {
        "operations": ["external_data_egress"],
        "action_digest": policy.action_digest(high_risk),
        "policy_digest": policy.policy_digest(cfg),
        "destination": high_risk["destination"]["host"],
        "change_boundary": high_risk["context"]["change_boundary"],
        "data_classes": high_risk["data"]["classes"],
        "protected_assets": high_risk["data"]["protected_assets"],
    }
    approval_scope["fingerprint"] = fingerprint(approval_scope)
    record = {"approval": {"id": "synthetic-approval", "type": "runtime_action", "status": "APPROVED",
                           "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()},
              "scope": approval_scope}
    with tempfile.TemporaryDirectory() as tmp:
        approval_path = Path(tmp) / "approval.yaml"
        approval_path.write_text(yaml.safe_dump(record, sort_keys=False))
        approved = policy.evaluate(high_risk, cfg, runtime_capability="TOOL_GUARDED",
                                   approval_path=approval_path,
                                   sandbox_evidence={"status": "AVAILABLE", "provider": "verified-test-sandbox",
                                                     "host": "analytics.example.com", "data_class": "restricted"})
        require(approved["decision"] == "ALLOW", f"valid scoped approval should allow in verified sandbox test: {approved}")
        changed_scope = copy.deepcopy(high_risk)
        changed_scope["destination"]["host"] = "other.example.com"
        cfg["external_destination_allowlist"].append("other.example.com")
        stale = policy.evaluate(changed_scope, cfg, runtime_capability="TOOL_GUARDED",
                                approval_path=approval_path,
                                sandbox_evidence={"status": "AVAILABLE", "provider": "verified-test-sandbox",
                                                  "host": "other.example.com", "data_class": "restricted"})
        require(stale["decision"] == "BLOCKED" and "APPROVAL_STALE" in stale["reason"], f"destination drift must block: {stale}")
        policy_drift = policy.evaluate(high_risk, cfg, runtime_capability="TOOL_GUARDED",
                                       approval_path=approval_path,
                                       sandbox_evidence={"status": "AVAILABLE", "provider": "verified-test-sandbox",
                                                         "host": "analytics.example.com", "data_class": "restricted"})
        require(policy_drift["decision"] == "BLOCKED" and "policy digest is stale" in policy_drift["reason"],
                f"policy drift must invalidate approval: {policy_drift}")
        cfg = base_config()
        approval_scope["policy_digest"] = policy.policy_digest(cfg)
        approval_scope["fingerprint"] = fingerprint({k: v for k, v in approval_scope.items() if k != "fingerprint"})
        record["scope"] = copy.deepcopy(approval_scope)
        expired_record = copy.deepcopy(record)
        expired_record["approval"]["expires_at"] = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        approval_path.write_text(yaml.safe_dump(expired_record, sort_keys=False))
        expired = policy.evaluate(high_risk, cfg, runtime_capability="TOOL_GUARDED",
                                  approval_path=approval_path,
                                  sandbox_evidence={"status": "AVAILABLE", "provider": "verified-test-sandbox",
                                                    "host": "analytics.example.com", "data_class": "restricted"})
        require(expired["decision"] == "BLOCKED" and "expired" in expired["reason"], f"expired approval must block: {expired}")

    conflicting = copy.deepcopy(cfg)
    conflicting["rules"].append({"id": "synthetic-hard-deny", "priority": 2000,
                                  "when": {"destination_trust": ["approved_external"]}, "effect": "DENY"})
    denied = policy.evaluate(action, conflicting, runtime_capability="TOOL_GUARDED")
    require(denied["decision"] == "DENY", f"deny must override allow: {denied}")
    signal = lambda decision: {"decision": decision, "provider": "synthetic-semantic-guard", "action_digest": policy.action_digest(action)}
    semantic_deny = policy.evaluate(action, cfg, runtime_capability="TOOL_GUARDED", semantic_signal=signal("DENY"))
    require(semantic_deny["decision"] == "DENY", f"semantic DENY did not tighten: {semantic_deny}")
    semantic_escalate = policy.evaluate(action, cfg, runtime_capability="TOOL_GUARDED", semantic_signal=signal("ESCALATE"))
    require(semantic_escalate["decision"] == "REQUIRE_APPROVAL", f"semantic escalation did not tighten: {semantic_escalate}")
    semantic_invalid = policy.evaluate(action, cfg, runtime_capability="TOOL_GUARDED", semantic_signal=signal("TIMEOUT"))
    require(semantic_invalid["decision"] == "BLOCKED", f"invalid semantic signal must block: {semantic_invalid}")

    credential_action = copy.deepcopy(action)
    credential_action["action"]["arguments"] = {"api_key": "synthetic-secret-value"}
    try:
        policy.evaluate(credential_action, cfg, runtime_capability="TOOL_GUARDED")
    except policy.PolicyError:
        pass
    else:
        raise AssertionError("literal secret field must be rejected before policy evaluation")
    print("runtime_policy deterministic contract evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

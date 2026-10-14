#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from repository_governance_snapshot import build_snapshot, repository_slug


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    require(repository_slug("git@" + "github.com:owner/repository.git") == "owner/repository", "SSH origin parsing")
    require(repository_slug("https://github.com/owner/repository.git") == "owner/repository", "HTTPS origin parsing")
    payloads = {
        "repos/owner/repo/branches/main": {"name": "main", "protected": True},
        "repos/owner/repo/rules/branches/main": [{"type": "pull_request", "source_type": "Repository"}],
        "repos/owner/repo/rulesets?includes_parents=true&per_page=100": [{
            "id": 7,
            "name": "main rules",
            "bypass_actors": [{"actor_id": 12, "actor_type": "Team", "bypass_mode": "always"}],
        }],
        "repos/owner/repo/branches/main/protection": {
            "required_status_checks": {"contexts": ["repository"], "checks": [{"context": "lint"}]},
        },
    }
    calls: list[str] = []

    def complete_reader(endpoint: str) -> tuple[int, str]:
        calls.append(endpoint)
        return 0, json.dumps(payloads[endpoint])

    complete = build_snapshot("owner/repo", "main", complete_reader, captured_at="2026-10-07T00:00:00Z")
    require(complete["source_complete"] is True, "verified branch and effective rules should produce a complete snapshot")
    require(complete["branch_protection"]["required_checks"] == ["lint", "repository"], "required checks normalize and sort")
    require(complete["branch_protection"]["required_status_checks"] == payloads["repos/owner/repo/branches/main/protection"]["required_status_checks"], "full branch protection response remains available")
    require(len(complete["bypass_actors"]) == 1, "ruleset bypass actors are retained")
    require(complete["bypass_actors"][0]["actor_type"] == "Team", "bypass actors remain structured evidence")
    require(complete["activation_authorized"] is False and complete["api_write_performed"] is False, "snapshot has no write authority")
    require(len(calls) == 4, "only branch and read-only policy endpoints are queried")
    require(complete["protection_state"] == "PROTECTED", "effective rules determine active policy state")
    require(complete["evidence_level"] == "EFFECTIVE_RULES_CONFIRMED", "effective evidence has an explicit level")
    paged_payload = {
        "branch": json.dumps(payloads["repos/owner/repo/branches/main"]),
        "effective_rules": json.dumps(payloads["repos/owner/repo/rules/branches/main"]),
        "rulesets": json.dumps([[payloads["repos/owner/repo/rulesets?includes_parents=true&per_page=100"][0]], []]),
        "branch_protection": json.dumps(payloads["repos/owner/repo/branches/main/protection"]),
    }
    paged = build_snapshot(
        "owner/repo",
        "main",
        lambda endpoint: (0, paged_payload["rulesets"] if "rulesets" in endpoint else json.dumps(payloads[endpoint])),
        captured_at="2026-10-08T00:00:00Z",
    )
    require(paged["rulesets"] == complete["rulesets"], "paginated ruleset pages must be flattened")
    require(paged["snapshot_digest"] == complete["snapshot_digest"], "same governance evidence must keep a stable digest across capture times")

    def denied_reader(endpoint: str) -> tuple[int, str]:
        if "/rules/branches/" in endpoint:
            return 1, ""
        return 0, json.dumps(payloads[endpoint])

    incomplete = build_snapshot("owner/repo", "main", denied_reader, captured_at="2026-10-07T00:00:00Z")
    require(incomplete["source_complete"] is False, "permission failure must not claim completeness")
    require(incomplete["source_status"] == "UNKNOWN", "incomplete source is UNKNOWN")
    require(incomplete["sources"]["effective_rules"]["status"] == "UNKNOWN", "unreadable effective rules remain explicit")
    require(incomplete["snapshot_digest"].startswith("sha256:"), "snapshot is fingerprinted")

    no_classic = {
        "repos/owner/repo/branches/main": {"returncode": 0, "http_status": 200, "payload": {"name": "main", "protected": False}},
        "repos/owner/repo/rules/branches/main": {"returncode": 0, "http_status": 200, "payload": []},
        "repos/owner/repo/rulesets?includes_parents=true&per_page=100": {"returncode": 1, "http_status": 403, "payload": None, "error_class": "PERMISSION_OR_AUTHENTICATION", "error_message": "Resource not accessible by integration"},
        "repos/owner/repo/branches/main/protection": {"returncode": 1, "http_status": 404, "payload": None, "error_class": "NOT_FOUND", "error_message": "Branch not protected"},
    }
    explicit_none = build_snapshot("owner/repo", "main", no_classic.__getitem__)
    require(explicit_none["protection_state"] == "UNPROTECTED", "effective empty rules plus verified branch is explicit no-active-rules evidence")
    require(explicit_none["source_complete"] is True, "optional detailed ruleset access does not hide complete effective evidence")
    require(explicit_none["sources"]["branch_protection"]["status"] == "NOT_CONFIGURED", "classic protection 404 is distinguished")
    require(explicit_none["sources"]["rulesets"]["http_status"] == 403, "real HTTP denial is retained")

    classic_protected = dict(no_classic)
    classic_protected["repos/owner/repo/rulesets?includes_parents=true&per_page=100"] = {
        "returncode": 0, "http_status": 200, "payload": []}
    classic_protected["repos/owner/repo/branches/main/protection"] = {
        "returncode": 0, "http_status": 200,
        "payload": {"required_status_checks": {"contexts": ["repository"]}}}
    classic_protected["repos/owner/repo/branches/main"] = {
        "returncode": 0, "http_status": 200, "payload": {"name": "main", "protected": True}}
    classic = build_snapshot("owner/repo", "main", classic_protected.__getitem__)
    require(classic["protection_state"] == "PROTECTED",
            "affirmative classic branch protection cannot be mislabeled unprotected when effective rules are empty")
    require(classic["classic_protection_configured"] is True,
            "classic protection evidence has an explicit additive field")

    classic_permission = dict(classic_protected)
    classic_permission["repos/owner/repo/branches/main/protection"] = {
        "returncode": 1, "http_status": 403, "payload": None,
        "error_class": "PERMISSION", "error_message": "private detail"}
    unknown_classic = build_snapshot("owner/repo", "main", classic_permission.__getitem__)
    require(unknown_classic["source_complete"] is False,
            "a protected branch with unreadable classic policy remains incomplete")
    require(unknown_classic["sources"]["branch_protection"]["status"] == "UNKNOWN_PERMISSION",
            "classic protection permission failure has a distinct policy state")

    inconsistent_protection = dict(no_classic)
    inconsistent_protection["repos/owner/repo/branches/main"] = {
        "returncode": 0, "http_status": 200, "payload": {"name": "main", "protected": True}}
    inconsistent = build_snapshot("owner/repo", "main", inconsistent_protection.__getitem__)
    require(inconsistent["source_complete"] is False,
            "aggregate protected state with no readable policy evidence remains incomplete")

    inaccessible = dict(no_classic)
    inaccessible["repos/owner/repo/rules/branches/main"] = {"returncode": 1, "http_status": 403, "payload": None, "error_class": "PERMISSION_OR_AUTHENTICATION", "error_message": "Resource not accessible by integration"}
    unknown = build_snapshot("owner/repo", "main", inaccessible.__getitem__)
    require(unknown["protection_state"] == "UNKNOWN", "inaccessible effective rules never imply unprotected")
    require(unknown["sources"]["effective_rules"]["http_status"] == 403, "effective rules HTTP status is preserved")

    missing_branch = dict(no_classic)
    missing_branch["repos/owner/repo/branches/main"] = {"returncode": 1, "http_status": 404, "payload": None, "error_class": "NOT_FOUND", "error_message": "Branch not found"}
    missing = build_snapshot("owner/repo", "main", missing_branch.__getitem__)
    require(missing["protection_state"] == "UNKNOWN", "branch 404 is not interpreted as unprotected")

    token_like = "gh" + "p_" + "123456789012345678901234567890"
    raw = f'HTTP/2 403\r\ncontent-type: application/json\r\n\r\n{{"message":"Resource not accessible by integration token {token_like}"}}'
    parsed = __import__("repository_governance_snapshot").parse_gh_response("repos/owner/repo/rulesets", 1, raw)
    require(parsed["http_status"] == 403, "HTTP response status is parsed")
    require("ghp_" not in parsed["error_message"], "token-like text is redacted from safe API messages")
    print("REPOSITORY GOVERNANCE SNAPSHOT LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
    require(complete["source_complete"] is True, "both readable endpoints should produce a complete snapshot")
    require(complete["branch_protection"]["required_checks"] == ["lint", "repository"], "required checks normalize and sort")
    require(complete["branch_protection"]["required_status_checks"] == payloads[calls[1]]["required_status_checks"], "full branch protection response remains available")
    require(len(complete["bypass_actors"]) == 1, "ruleset bypass actors are retained")
    require(complete["bypass_actors"][0]["actor_type"] == "Team", "bypass actors remain structured evidence")
    require(complete["activation_authorized"] is False and complete["api_write_performed"] is False, "snapshot has no write authority")
    require(len(calls) == 2, "only the two read-only endpoints are queried")
    paged_payload = {
        "rulesets": json.dumps([[payloads[calls[0]][0]], []]),
        "branch_protection": json.dumps(payloads[calls[1]]),
    }
    paged = build_snapshot(
        "owner/repo",
        "main",
        lambda endpoint: (0, paged_payload["rulesets"] if "rulesets" in endpoint else paged_payload["branch_protection"]),
        captured_at="2026-10-08T00:00:00Z",
    )
    require(paged["rulesets"] == complete["rulesets"], "paginated ruleset pages must be flattened")
    require(paged["snapshot_digest"] == complete["snapshot_digest"], "same governance evidence must keep a stable digest across capture times")

    def denied_reader(endpoint: str) -> tuple[int, str]:
        if "rulesets" in endpoint:
            return 1, ""
        return 0, json.dumps(payloads[endpoint])

    incomplete = build_snapshot("owner/repo", "main", denied_reader, captured_at="2026-10-07T00:00:00Z")
    require(incomplete["source_complete"] is False, "permission failure must not claim completeness")
    require(incomplete["source_status"] == "UNKNOWN", "incomplete source is UNKNOWN")
    require(incomplete["sources"]["rulesets"]["status"] == "UNKNOWN", "unreadable surface remains explicit")
    require(incomplete["snapshot_digest"].startswith("sha256:"), "snapshot is fingerprinted")
    print("REPOSITORY GOVERNANCE SNAPSHOT LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

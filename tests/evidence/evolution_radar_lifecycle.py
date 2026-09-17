#!/usr/bin/env python3
from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import evolution_radar as radar  # noqa: E402
import evolution_radar_rollup as rollup  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    config = yaml.safe_load((ROOT / "config/evolution-sources.yaml").read_text(encoding="utf-8")) or {}
    require(not radar.validate_config(config), "real Evolution Radar source config must validate")
    require(len([s for s in config["sources"] if s.get("enabled", True)]) >= 5, "at least five sources required")
    require(config["policy"]["max_items_per_source"] == 5, "source item bound must remain five")

    original_collect = radar.collect_source

    def fake_collect(source, max_items, timeout):
        require(max_items == 5, "collector must pass the configured bounded item count")
        require(timeout > 0, "collector must use a finite positive timeout")
        source_id = source["id"]
        if source_id in {config["sources"][0]["id"], config["sources"][1]["id"]}:
            return [{
                "fingerprint": radar.signal_fingerprint("Shared signal", "https://example.test/shared?utm_source=x"),
                "title": "Shared signal",
                "canonical_url": "https://example.test/shared",
                "source_id": source_id,
                "published_at": "2026-09-01",
            }]
        return [{
            "fingerprint": radar.signal_fingerprint(f"Signal {source_id}", f"https://example.test/{source_id}"),
            "title": f"Signal {source_id}",
            "canonical_url": f"https://example.test/{source_id}",
            "source_id": source_id,
            "published_at": "2026-09-02",
        }]

    radar.collect_source = fake_collect
    try:
        weekly = radar.build_evidence(config, mode="weekly", timeout=1.0)
    finally:
        radar.collect_source = original_collect

    require(not radar.validate_evidence(weekly), "weekly evidence must validate")
    require(weekly["summary"]["signal_count"] == 5, "five bounded source items expected")
    require(weekly["summary"]["deduplicated_count"] == 4, "cross-source duplicate must collapse")
    require(any(s["recurrence_count"] == 2 for s in weekly["signals"]), "duplicate recurrence must be recorded")
    require(all(r["state"] == "ANALYSIS_PENDING" for r in weekly["recommendations"]), "no analyzer must not infer suitability")
    require(weekly["summary"]["actionable_count"] == 0, "no analyzer must not fabricate actionable recommendations")
    require(weekly["summary"]["zero_recommendations_valid"] is True, "zero recommendations must remain valid")
    require(weekly["authority"] == {
        "code_change_authorized": False,
        "branch_or_pr_authorized": False,
        "merge_authorized": False,
        "release_authorized": False,
        "human_decision_required": True,
    }, "research authority boundary must be fail-closed")

    body1 = rollup.issue_markdown(weekly)
    require(rollup.EVIDENCE_START in body1 and rollup.EVIDENCE_END in body1, "Issue must carry machine-readable evidence markers")
    parsed = rollup.extract_evidence(body1)
    require(parsed is not None and not radar.validate_evidence(parsed), "Issue evidence must round-trip")

    weekly2 = copy.deepcopy(weekly)
    weekly2["run"]["generated_at"] = "2026-09-08T01:00:00Z"
    body2 = rollup.issue_markdown(weekly2)
    old_weekly = copy.deepcopy(weekly)
    old_weekly["run"]["generated_at"] = "2026-08-25T01:00:00Z"
    old_body = rollup.issue_markdown(old_weekly)
    issues = [
        {"title": "Evolution Radar [weekly] 2026-09-01", "created_at": "2026-09-01T01:05:00Z", "body": body1},
        {"title": "Evolution Radar [weekly] 2026-09-08", "created_at": "2026-09-08T01:05:00Z", "body": body2},
        {"title": "Evolution Radar [weekly] 2026-08-25", "created_at": "2026-08-25T01:05:00Z", "body": old_body},
        {"title": "Unrelated issue", "created_at": "2026-09-09T01:05:00Z", "body": body1},
        {"title": "Evolution Radar [weekly] malformed", "created_at": "2026-09-15T01:05:00Z", "body": "no evidence"},
    ]
    require(rollup.flatten_issue_pages(issues) == issues, "single-page issue arrays must remain supported")
    paged = rollup.flatten_issue_pages([issues[:2], issues[2:]])
    require(paged == issues, "paginated gh api --slurp pages must flatten without losing evidence")
    try:
        rollup.flatten_issue_pages([[issues[0]], ["invalid"]])
    except ValueError:
        pass
    else:
        raise AssertionError("invalid paginated issue payload must fail closed")

    monthly = rollup.monthly_rollup(paged, config, period="2026-09")
    require(monthly["run"]["period"] == "2026-09", "monthly evidence must record the reviewed calendar period")
    require(monthly["run"]["weekly_evidence_count"] == 2, "monthly rollup must consume only weekly evidence from the requested calendar period")
    require(monthly["summary"]["signal_count"] == 8, "out-of-period weekly evidence must be excluded")
    require(monthly["summary"]["deduplicated_count"] == 4, "monthly rollup must deduplicate recurring signals")
    require(all(s["recurrence_count"] >= 2 for s in monthly["signals"]), "monthly rollup must accumulate recurrence")
    require(all(r["state"] == "ANALYSIS_PENDING" for r in monthly["recommendations"]), "monthly rollup must preserve analyzer truthfulness")
    require(not radar.validate_evidence(monthly), "monthly evidence must validate")

    try:
        rollup.monthly_rollup(issues, config, period="2026/09")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid monthly period format must fail closed")

    bad_config = copy.deepcopy(config)
    bad_config["sources"] = bad_config["sources"][:4]
    require(radar.validate_config(bad_config), "fewer than five configured sources must fail")

    bad_authority = copy.deepcopy(weekly)
    bad_authority["authority"]["branch_or_pr_authorized"] = True
    require(radar.validate_evidence(bad_authority), "research must fail if it claims implementation publication authority")

    bad_adopt = copy.deepcopy(weekly)
    bad_adopt["recommendations"][0]["state"] = "ADOPT"
    require(radar.validate_evidence(bad_adopt), "unavailable analyzer must not emit ADOPT")

    bad_duplicate = copy.deepcopy(weekly)
    bad_duplicate["signals"].append(copy.deepcopy(bad_duplicate["signals"][0]))
    require(radar.validate_evidence(bad_duplicate), "duplicate fingerprints must fail evidence validation")

    workflow = (ROOT / ".github/workflows/evolution-radar.yml").read_text(encoding="utf-8")
    for required in (
        'cron: "0 1 * * 1"',
        'cron: "30 1 1 * *"',
        "contents: read",
        "issues: write",
        "gh issue create",
        "monthly-rollup",
        "--period",
        "gh api --paginate --slurp",
    ):
        require(required in workflow, f"workflow missing contract: {required}")
    for forbidden in ("contents: write", "pull-requests: write", "git push", "gh pr create", "gh pr merge", "releases: write"):
        require(forbidden not in workflow, f"workflow must not gain implementation authority: {forbidden}")

    with tempfile.TemporaryDirectory() as tmp:
        evidence = Path(tmp) / "evidence.yaml"
        issue_body = Path(tmp) / "issue.md"
        evidence.write_text(yaml.safe_dump(weekly, sort_keys=False), encoding="utf-8")
        require(not radar.validate_evidence(yaml.safe_load(evidence.read_text(encoding="utf-8"))), "serialized evidence must validate")
        issue_body.write_text(rollup.issue_markdown(weekly), encoding="utf-8")
        require(issue_body.stat().st_size > 0, "Human review artifact must be non-empty")

    print("EVOLUTION RADAR LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

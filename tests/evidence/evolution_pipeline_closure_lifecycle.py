#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import evolution_radar_rollup as rollup  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def weekly_doc(day: str, *, signal_count: int = 0, state: str = "ANALYSIS_PENDING") -> dict:
    config = yaml.safe_load((ROOT / "config/evolution-sources.yaml").read_text(encoding="utf-8")) or {}
    configured = [str(source["id"]) for source in config.get("sources") or [] if source.get("enabled", True)]
    signals = [
        {
            "fingerprint": f"sha256:{index:064x}",
            "title": f"Signal {index}",
            "canonical_url": f"https://example.test/{index}",
            "source_id": configured[0],
            "published_at": None,
            "retrieved_at": f"2026-09-{day}T01:00:00Z",
            "summary": "",
            "recurrence_count": 1,
            "duplicate_of": None,
        }
        for index in range(1, signal_count + 1)
    ]
    return {
        "version": 1,
        "run": {
            "mode": "weekly",
            "generated_at": f"2026-09-{day}T01:00:00Z",
            "repository_revision": "a" * 40,
            "analyzer": {"status": "available" if state != "ANALYSIS_PENDING" else "unavailable", "provider": "fixture", "model": "fixture"},
        },
        "sources": {"configured": configured, "attempted": configured, "failures": []},
        "signals": signals,
        "recommendations": [
            {"signal_fingerprint": item["fingerprint"], "state": state}
            for item in signals
        ],
        "summary": {
            "signal_count": signal_count,
            "deduplicated_count": signal_count,
            "recommendation_count": signal_count,
            "actionable_count": 0,
            "zero_recommendations_valid": True,
        },
        "authority": {
            "code_change_authorized": False,
            "branch_or_pr_authorized": False,
            "merge_authorized": False,
            "release_authorized": False,
            "human_decision_required": True,
        },
    }


def issue(title: str, doc: dict) -> dict:
    body = rollup.issue_markdown(doc)
    return {"title": title, "created_at": doc["run"].get("generated_at"), "body": body}


def main() -> int:
    config = yaml.safe_load((ROOT / "config/evolution-sources.yaml").read_text(encoding="utf-8")) or {}
    weekly_issues = [
        issue(f"Evolution Radar [weekly] 2026-09-{day}", weekly_doc(day))
        for day in ("07", "14", "21", "28")
    ]
    complete_empty = rollup.monthly_rollup(weekly_issues, config, period="2026-09")
    require(complete_empty["run"]["pipeline_health"]["status"] == "COMPLETE", "all four scheduled cohorts must be complete")
    require(complete_empty["run"]["content_value"]["status"] == "SOURCE_YIELD_LOW", "complete zero-source yield must remain distinct from missing inputs")

    partial = rollup.monthly_rollup(weekly_issues[:-1], config, period="2026-09")
    require(partial["run"]["pipeline_health"]["status"] == "INCOMPLETE_INPUT", "a missing scheduled bundle must be incomplete")
    require("2026-09-28" in partial["run"]["pipeline_health"]["missing_dates"], "the exact missing weekly date must be reported")
    require(partial["run"]["content_value"]["status"] == "INCOMPLETE_INPUT", "content cannot be declared healthy for an incomplete cohort")

    healthy_issues = [
        issue(f"Evolution Radar [weekly] 2026-09-{day}", weekly_doc(day, signal_count=2, state="HOLD"))
        for day in ("07", "14", "21", "28")
    ]
    healthy = rollup.monthly_rollup(healthy_issues, config, period="2026-09")
    require(healthy["run"]["content_value"]["status"] == "HEALTHY_NO_ACTIONABLE_SIGNAL", "complete semantic review with no actionable candidate is a healthy result")

    monthly_issues = []
    for month in ("2026-07", "2026-08", "2026-09"):
        doc = rollup.monthly_rollup([], config, period=month)
        doc["run"]["pipeline_health"] = {"status": "COMPLETE"}
        doc["summary"]["zero_recommendations_valid"] = True
        monthly_issues.append(issue(f"Evolution Radar [monthly] {month}", doc))
    quarterly = rollup.quarterly_rollup(monthly_issues, config, period="2026-Q3")
    require(quarterly["run"]["pipeline_health"]["status"] == "COMPLETE", "three complete monthly bundles must close the quarter")
    quarterly_missing = rollup.quarterly_rollup(monthly_issues[:-1], config, period="2026-Q3")
    require(quarterly_missing["run"]["pipeline_health"]["status"] == "INCOMPLETE_INPUT", "a quarter with a missing month must not report a healthy zero")
    require(quarterly_missing["run"]["pipeline_health"]["missing_months"] == ["2026-09"], "quarter report must identify the missing month")

    print("EVOLUTION PIPELINE CLOSURE LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

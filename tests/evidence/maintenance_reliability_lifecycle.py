#!/usr/bin/env python3
"""Exercise bounded monthly maintenance reliability collection and metrics."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from maintenance_reliability import build_report, collect_data, load_mapping, validate_report


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def iso(seconds: int) -> tuple[str, str]:
    end = datetime(2026, 8, 20, 12, tzinfo=timezone.utc)
    start = end - timedelta(seconds=seconds)
    return start.isoformat().replace("+00:00", "Z"), end.isoformat().replace("+00:00", "Z")


def run(run_id: int, event: str, conclusion: str, sha: str, seconds: int = 60, *, branch: str = "feature/x", step: str = "") -> dict:
    started, completed = iso(seconds)
    return {
        "id": run_id,
        "event": event,
        "branch": branch,
        "head_sha": sha,
        "conclusion": conclusion,
        "created_at": completed,
        "started_at": started,
        "completed_at": completed,
        "attempt": 1,
        "pull_requests": [],
        "failed_jobs": ["deterministic integration gate"] if step else [],
        "failed_steps": [step] if step else [],
        "failure_details_available": True,
    }


def complete_data(config: dict) -> dict:
    pr_a, pr_b, pr_c = "a" * 40, "b" * 40, "c" * 40
    runs = [
        run(1, "pull_request", "success", "1" * 40, 100),
        run(2, "pull_request", "failure", "2" * 40, 300, step="Install dependencies"),
        run(3, "pull_request", "timed_out", "3" * 40, 500, step="SQLite cache lifecycle"),
        run(4, "pull_request", "cancelled", "4" * 40, 40),
        run(5, "push", "success", pr_a, 120, branch="main"),
        run(6, "push", "failure", pr_b, 150, branch="main", step="Repository validation"),
        run(7, "push", "success", pr_c, 110, branch="main"),
    ]
    prs = [
        {"number": 11, "merged_at": "2026-08-10T00:00:00Z", "merge_sha": pr_a, "labels": [], "changed_file_count": 2, "files": ["scripts/a.py", "docs/a.md"], "files_complete": True},
        {"number": 12, "merged_at": "2026-08-11T00:00:00Z", "merge_sha": pr_b, "labels": ["Hotfix"], "changed_file_count": 3, "files": ["scripts/a.py", "tests/a.py", "docs/b.md"], "files_complete": True},
        {"number": 13, "merged_at": "2026-08-12T00:00:00Z", "merge_sha": pr_c, "labels": [], "changed_file_count": 1, "files": ["README.md"], "files_complete": True},
    ]
    return {
        "version": 1,
        "repository": "owner/repo",
        "period": "2026-08",
        "validation_runs": runs,
        "merged_pull_requests": prs,
        "collection": {
            "validation_runs_total": len(runs),
            "validation_runs_fetched": len(runs),
            "validation_runs_complete": True,
            "merged_pull_requests_total": len(prs),
            "merged_pull_requests_fetched": len(prs),
            "merged_pull_requests_complete": True,
            "changed_file_lists_complete": True,
            "failure_details_complete": True,
            "collection_errors": [],
        },
    }


def test_metrics_and_unknowns(config: dict) -> None:
    data = complete_data(config)
    report = build_report(data, config, repository_revision="a" * 40, generated_at="2026-09-03T04:15:00Z")
    metrics = report["metrics"]
    validation = metrics["validation"]
    require(validation["attempt_count"] == 3, "cancelled run must be excluded from eligible validation attempts")
    require(validation["passed_count"] == 1 and validation["failed_count"] == 2, "completed PR outcomes must be counted")
    require(validation["cancelled_count"] == 1, "cancelled/superseded attempts must be separately reported")
    require(validation["pass_rate_basis_points"] == 3333, "pass rate must use integer basis points")
    require(validation["duration_seconds"] == {"median": 300, "p95": 500}, "nearest-rank durations must be deterministic")
    require(validation["failure_categories"] == {"cache": 1, "environment": 1, "runtime": 0, "ci": 0, "validation": 0, "unknown": 0}, "failure categories must follow configured keyword priority")
    changes = metrics["merged_changes"]
    require(changes["labeled_hotfix_count"] == 1, "hotfixes must use explicit normalized labels")
    require(changes["files_per_change"] == {"median": 2, "p95": 3}, "file-count distribution must use nearest-rank percentiles")
    require(changes["repeated_surfaces"] == [{"path": "scripts/a.py", "merged_pr_count": 2}], "repeated changed surfaces must count across PRs")
    require(metrics["escaped_regressions"]["count"] == 1, "only exact failing merge-SHA push runs count as escaped regressions")
    require(validate_report(report, config) == [], "complete report should validate")

    partial = deepcopy(data)
    partial["collection"]["validation_runs_complete"] = False
    partial["collection"]["merged_pull_requests_complete"] = False
    partial["collection"]["changed_file_lists_complete"] = False
    partial_report = build_report(partial, config, repository_revision="a" * 40, generated_at="2026-09-03T04:15:00Z")
    require(partial_report["metrics"]["validation"]["pass_rate_basis_points"] is None, "truncated run history must not publish a pass rate")
    require(partial_report["metrics"]["merged_changes"]["labeled_hotfix_count"] is None, "truncated PR history must not claim a hotfix count")
    require(partial_report["metrics"]["escaped_regressions"]["count"] is None, "incomplete SHA linkage must remain UNKNOWN")
    require("REVIEW_INCOMPLETE_VALIDATION_RUN_HISTORY" in partial_report["review_flags"], "incomplete history must request review")

    malformed = deepcopy(data)
    malformed["validation_runs"][0]["started_at"] = ""
    malformed["merged_pull_requests"][0]["changed_file_count"] = None
    malformed_report = build_report(malformed, config, repository_revision="a" * 40, generated_at="2026-09-03T04:15:00Z")
    require(malformed_report["metrics"]["validation"]["duration_seconds"] == {"median": None, "p95": None}, "incomplete duration samples must not publish partial percentiles")
    require(malformed_report["metrics"]["merged_changes"]["files_per_change"] == {"median": None, "p95": None}, "incomplete changed-file counts must not publish partial percentiles")
    require("REVIEW_INCOMPLETE_RUNTIME_DURATION_DATA" in malformed_report["review_flags"], "missing run timestamps must request review")
    require("REVIEW_INCOMPLETE_CHANGED_FILE_COUNT_DATA" in malformed_report["review_flags"], "missing changed-file counts must request review")


def test_collector_handles_api_shapes(config: dict) -> None:
    start, completed = iso(120)
    calls: list[tuple[str, dict | None]] = []

    def api(endpoint: str, params: dict | None = None):
        calls.append((endpoint, params))
        if endpoint.endswith("/actions/workflows/validate.yml/runs"):
            return {"total_count": 1, "workflow_runs": [{
                "id": 99, "event": "pull_request", "head_branch": "feature/x", "head_sha": "d" * 40,
                "conclusion": "failure", "created_at": completed, "updated_at": completed,
                "run_started_at": start, "run_attempt": 1,
                "pull_requests": [{"number": 50, "head": {"sha": "d" * 40}, "base": {"ref": "main"}}],
            }]}
        if endpoint.endswith("/actions/runs/99/jobs"):
            return {"total_count": 1, "jobs": [{"name": "lint", "conclusion": "failure", "steps": [{"name": "setup python", "conclusion": "failure"}]}]}
        if endpoint == "/search/issues":
            return {"total_count": 1, "items": [{"number": 50}]}
        if endpoint.endswith("/pulls/50"):
            return {"merged_at": "2026-08-20T12:00:00Z", "merge_commit_sha": "e" * 40, "changed_files": 2, "labels": [{"name": "hotfix"}]}
        if endpoint.endswith("/pulls/50/files"):
            return [{"filename": "scripts/a.py"}, {"filename": "tests/a.py"}]
        raise AssertionError(f"unexpected API request: {endpoint}")

    data = collect_data(repo="owner/repo", period="2026-08", config=config, api_get=api)
    require(data["collection"]["validation_runs_complete"], "complete run page should be recorded")
    require(data["collection"]["changed_file_lists_complete"], "array-shaped PR files response should be read")
    require(data["merged_pull_requests"][0]["files"] == ["scripts/a.py", "tests/a.py"], "PR file paths should be sorted and retained")
    require(data["validation_runs"][0]["failed_steps"] == ["setup python"], "failure detail should retain only step names")
    require(any(endpoint == "/search/issues" for endpoint, _ in calls), "collector should use bounded merged PR search")


def main() -> int:
    config = load_mapping(ROOT / "config/maintenance-reliability.yaml")
    test_metrics_and_unknowns(config)
    test_collector_handles_api_shapes(config)
    print("Maintenance Reliability lifecycle: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

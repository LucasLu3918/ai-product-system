#!/usr/bin/env python3
"""Build deterministic, bounded monthly repository maintenance reliability evidence."""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import yaml
from aips_common import canonical_digest as _aips_canonical_digest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/maintenance-reliability.yaml"


def canonical_digest(value: Any) -> str:
    return _aips_canonical_digest(value)


def load_mapping(path: str | Path) -> dict[str, Any]:
    value = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a mapping")
    return value


def valid_period(value: str) -> bool:
    if not re.fullmatch(r"\d{4}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value + "-01")
    except ValueError:
        return False
    return True


def period_dates(period: str) -> tuple[str, str]:
    if not valid_period(period):
        raise ValueError("period must be a valid YYYY-MM calendar month")
    start = date.fromisoformat(period + "-01")
    year = start.year + (1 if start.month == 12 else 0)
    month = 1 if start.month == 12 else start.month + 1
    next_month = date(year, month, 1)
    return start.isoformat(), (next_month - timedelta(days=1)).isoformat()


def validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if config.get("version") != 1:
        errors.append("maintenance reliability config version must be 1")
    collection = config.get("collection") or {}
    for name in ("page_size", "max_pages", "max_failure_details", "max_files_per_pull_request"):
        value = collection.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            errors.append(f"collection.{name} must be a positive integer")
    if collection.get("page_size") != 100:
        errors.append("collection.page_size must be 100 (GitHub API maximum)")
    thresholds = config.get("review_thresholds") or {}
    for name in ("minimum_validation_attempts", "minimum_merged_changes"):
        value = thresholds.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"review_thresholds.{name} must be a non-negative integer")
    categories = config.get("failure_categories") or {}
    expected = {"cache", "environment", "runtime", "ci", "validation", "unknown"}
    if set(categories) != expected:
        errors.append("failure_categories must define cache, environment, runtime, ci, validation and unknown")
    for category, patterns in categories.items():
        if not isinstance(patterns, list) or not patterns or not all(isinstance(x, str) and x for x in patterns):
            errors.append(f"failure_categories.{category} must be a non-empty string list")
    authority = config.get("authority") or {}
    for name in ("automatic_remediation", "automatic_code_change", "branch_or_pr_authorized", "merge_authorized", "release_authorized"):
        if authority.get(name) is not False:
            errors.append(f"authority.{name} must be false")
    if authority.get("human_review_required") is not True:
        errors.append("authority.human_review_required must be true")
    return errors


def gh_api(endpoint: str, params: dict[str, str | int] | None = None) -> Any:
    command = ["gh", "api", endpoint]
    for key, value in (params or {}).items():
        command.extend(["-F" if isinstance(value, int) else "-f", f"{key}={value}"])
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        # GitHub CLI output can contain repository metadata. Do not persist or echo it.
        raise RuntimeError(f"GitHub API request failed ({result.returncode}) for {endpoint.split('?')[0]}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"GitHub API returned invalid JSON for {endpoint.split('?')[0]}") from exc


def _fetch_pages(
    endpoint: str,
    params: dict[str, str | int],
    *,
    key: str,
    page_size: int,
    max_pages: int,
    api_get: Callable[[str, dict[str, str | int] | None], Any],
) -> tuple[list[dict[str, Any]], int, bool]:
    first = api_get(endpoint, {**params, "per_page": page_size, "page": 1})
    if not isinstance(first, dict) or not isinstance(first.get(key), list):
        raise RuntimeError(f"GitHub API response did not contain {key}")
    total = first.get("total_count")
    if not isinstance(total, int):
        total = len(first[key])
    items = [item for item in first[key] if isinstance(item, dict)]
    pages_needed = max(1, math.ceil(total / page_size))
    pages_to_fetch = min(pages_needed, max_pages)
    for page in range(2, pages_to_fetch + 1):
        payload = api_get(endpoint, {**params, "per_page": page_size, "page": page})
        rows = payload.get(key) if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise RuntimeError(f"GitHub API page did not contain {key}")
        items.extend(item for item in rows if isinstance(item, dict))
    return items, total, len(items) >= total


def _fetch_file_pages(
    endpoint: str,
    expected_count: int,
    *,
    page_size: int,
    max_pages: int,
    api_get: Callable[[str, dict[str, str | int] | None], Any],
) -> tuple[list[dict[str, Any]], int, bool]:
    if expected_count == 0:
        return [], 0, True
    rows: list[dict[str, Any]] = []
    pages_needed = min(max_pages, math.ceil(expected_count / page_size))
    for page in range(1, pages_needed + 1):
        payload = api_get(endpoint, {"per_page": page_size, "page": page})
        if not isinstance(payload, list):
            raise RuntimeError("GitHub pull request files response was not an array")
        rows.extend(item for item in payload if isinstance(item, dict))
        if len(payload) < page_size:
            break
    return rows, expected_count, len(rows) >= expected_count


def _run_row(run: dict[str, Any], failed_jobs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    links: list[dict[str, Any]] = []
    for item in run.get("pull_requests") or []:
        if not isinstance(item, dict):
            continue
        head = item.get("head") or {}
        base = item.get("base") or {}
        links.append({"number": item.get("number"), "head_sha": head.get("sha"), "base_ref": base.get("ref")})
    failed_step_names: list[str] = []
    failed_job_names: list[str] = []
    for job in failed_jobs or []:
        if not isinstance(job, dict):
            continue
        if job.get("conclusion") == "failure":
            failed_job_names.append(str(job.get("name") or ""))
        for step in job.get("steps") or []:
            if isinstance(step, dict) and step.get("conclusion") == "failure":
                failed_step_names.append(str(step.get("name") or ""))
    return {
        "id": run.get("id"),
        "event": str(run.get("event") or ""),
        "branch": str(run.get("head_branch") or ""),
        "head_sha": str(run.get("head_sha") or ""),
        "conclusion": str(run.get("conclusion") or ""),
        "created_at": str(run.get("created_at") or ""),
        "started_at": str(run.get("run_started_at") or ""),
        "completed_at": str(run.get("updated_at") or ""),
        "attempt": run.get("run_attempt"),
        "pull_requests": links,
        "failed_jobs": sorted(set(x for x in failed_job_names if x)),
        "failed_steps": sorted(set(x for x in failed_step_names if x)),
        "failure_details_available": failed_jobs is not None,
    }


def collect_data(
    *,
    repo: str,
    period: str,
    config: dict[str, Any],
    api_get: Callable[[str, dict[str, str | int] | None], Any] = gh_api,
) -> dict[str, Any]:
    errors = validate_config(config)
    if errors:
        raise ValueError("invalid maintenance reliability config: " + "; ".join(errors))
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("repo must be owner/name")
    start, end = period_dates(period)
    collection = config["collection"]
    page_size = int(collection["page_size"])
    max_pages = int(collection["max_pages"])
    created = f"{start}T00:00:00Z..{end}T23:59:59Z"
    run_rows, run_total, runs_complete = _fetch_pages(
        f"/repos/{repo}/actions/workflows/{collection['validation_workflow']}/runs",
        {"created": created}, key="workflow_runs", page_size=page_size, max_pages=max_pages, api_get=api_get,
    )
    run_rows.sort(key=lambda x: (str(x.get("created_at") or ""), int(x.get("id") or 0)))
    failure_candidates = [row for row in run_rows if row.get("conclusion") in {"failure", "timed_out", "startup_failure"}]
    max_failure_details = int(collection["max_failure_details"])
    failed_detail_complete = len(failure_candidates) <= max_failure_details
    run_data: list[dict[str, Any]] = []
    failure_detail_errors = False
    failure_index = 0
    for index, run in enumerate(run_rows):
        details: list[dict[str, Any]] | None = None
        if run.get("conclusion") in {"failure", "timed_out", "startup_failure"}:
            if failure_index < max_failure_details:
                try:
                    payload = api_get(f"/repos/{repo}/actions/runs/{run.get('id')}/jobs", {"per_page": 100, "page": 1})
                    details = payload.get("jobs") if isinstance(payload, dict) and isinstance(payload.get("jobs"), list) else None
                    if details is None:
                        failure_detail_errors = True
                    elif isinstance(payload.get("total_count"), int) and payload["total_count"] > len(details):
                        failure_detail_errors = True
                except RuntimeError:
                    failure_detail_errors = True
            else:
                details = None
            failure_index += 1
        run_data.append(_run_row(run, details))

    query = f"repo:{repo} is:pr is:merged merged:{start}..{end}"
    pr_rows, pr_total, prs_complete = _fetch_pages(
        "/search/issues", {"q": query}, key="items", page_size=page_size, max_pages=max_pages, api_get=api_get,
    )
    prs_complete = prs_complete and pr_total <= int(collection.get("max_pull_requests", 500))
    pr_rows = pr_rows[: int(collection.get("max_pull_requests", 500))]
    max_file_pages = max(1, math.ceil(int(collection["max_files_per_pull_request"]) / page_size))
    pr_data: list[dict[str, Any]] = []
    pr_details_complete = True
    files_complete = True
    for issue in pr_rows:
        number = int(issue.get("number") or 0)
        try:
            detail = api_get(f"/repos/{repo}/pulls/{number}", None)
        except RuntimeError:
            pr_details_complete = False
            continue
        try:
            file_rows, file_total, file_rows_complete = _fetch_file_pages(
                f"/repos/{repo}/pulls/{number}/files", int(detail.get("changed_files") or 0), page_size=page_size,
                max_pages=max_file_pages, api_get=api_get,
            )
        except RuntimeError:
            file_rows, file_total, file_rows_complete = [], int(detail.get("changed_files") or 0), False
        if file_total > int(collection["max_files_per_pull_request"]):
            file_rows_complete = False
            files_complete = False
        files_complete = files_complete and file_rows_complete
        labels = [str((item or {}).get("name") or "") for item in (detail.get("labels") or []) if isinstance(item, dict)]
        pr_data.append({
            "number": number,
            "merged_at": str(detail.get("merged_at") or ""),
            "merge_sha": str(detail.get("merge_commit_sha") or ""),
            "labels": sorted(set(x for x in labels if x)),
            "changed_file_count": detail.get("changed_files"),
            "files": sorted(set(str(row.get("filename") or "") for row in file_rows if isinstance(row, dict) and row.get("filename"))),
            "files_complete": file_rows_complete,
        })
    return {
        "version": 1,
        "repository": repo,
        "period": period,
        "validation_runs": run_data,
        "merged_pull_requests": sorted(pr_data, key=lambda x: (x["merged_at"], x["number"])),
        "collection": {
            "validation_runs_total": run_total,
            "validation_runs_fetched": len(run_data),
            "validation_runs_complete": runs_complete,
            "merged_pull_requests_total": pr_total,
            "merged_pull_requests_fetched": len(pr_data),
            "merged_pull_requests_complete": prs_complete and pr_details_complete,
            "changed_file_lists_complete": files_complete,
            "failure_details_complete": failed_detail_complete and not failure_detail_errors and all(
                row["failure_details_available"] for row in run_data if row["conclusion"] in {"failure", "timed_out", "startup_failure"}
            ),
            "collection_errors": [] if pr_details_complete else ["one_or_more_pull_request_details_unavailable"],
        },
    }


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else None


def _nearest_rank(values: list[int]) -> dict[str, int | None]:
    if not values:
        return {"median": None, "p95": None}
    ordered = sorted(values)
    median = (ordered[(len(ordered) - 1) // 2] + ordered[len(ordered) // 2]) // 2
    p95 = ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]
    return {"median": median, "p95": p95}


def _duration(run: dict[str, Any]) -> int | None:
    start = _parse_time(run.get("started_at"))
    end = _parse_time(run.get("completed_at"))
    if start is None or end is None or end < start:
        return None
    return int((end - start).total_seconds())


def _normalized_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _failure_category(names: list[str], categories: dict[str, list[str]]) -> str:
    text = " ".join(names).casefold()
    for category in ("cache", "environment", "runtime", "ci", "validation"):
        if any(token.casefold() in text for token in categories[category]):
            return category
    return "unknown"


def build_report(
    data: dict[str, Any], config: dict[str, Any], *, repository_revision: str, generated_at: str,
) -> dict[str, Any]:
    errors = validate_config(config)
    if errors:
        raise ValueError("invalid maintenance reliability config: " + "; ".join(errors))
    period = str(data.get("period") or "")
    if not valid_period(period):
        raise ValueError("input period must be a valid YYYY-MM calendar month")
    if not re.fullmatch(r"[0-9a-f]{40}", repository_revision):
        raise ValueError("repository_revision must be a 40-character lowercase git SHA")
    if _parse_time(generated_at) is None:
        raise ValueError("generated_at must be timezone-aware ISO-8601")
    runs = [row for row in data.get("validation_runs") or [] if isinstance(row, dict)]
    prs = [row for row in data.get("merged_pull_requests") or [] if isinstance(row, dict)]
    coverage = dict(data.get("collection") or {})
    runs_complete = coverage.get("validation_runs_complete") is True
    prs_complete = coverage.get("merged_pull_requests_complete") is True
    files_complete = coverage.get("changed_file_lists_complete") is True
    details_complete = coverage.get("failure_details_complete") is True

    completed_pr_runs = [
        run for run in runs
        if run.get("event") in {"pull_request", "pull_request_target"}
        and run.get("conclusion") in {"success", "failure", "timed_out", "startup_failure"}
    ]
    passed = sum(run.get("conclusion") == "success" for run in completed_pr_runs)
    failed = len(completed_pr_runs) - passed
    cancelled = sum(run.get("conclusion") == "cancelled" for run in runs)
    skipped = sum(run.get("conclusion") == "skipped" for run in runs)
    durations = [seconds for run in completed_pr_runs if (seconds := _duration(run)) is not None]
    duration_stats = _nearest_rank(durations)
    duration_complete = runs_complete and len(durations) == len(completed_pr_runs)
    validation_rate = (passed * 10000 // len(completed_pr_runs)) if completed_pr_runs and runs_complete else None

    hotfix_labels = {_normalized_label(str(x)) for x in (config.get("hotfix_labels") or [])}
    hotfix_count = sum(
        bool({_normalized_label(str(label)) for label in (pr.get("labels") or [])} & hotfix_labels)
        for pr in prs
    ) if prs_complete else None
    file_counts = [int(pr["changed_file_count"]) for pr in prs if isinstance(pr.get("changed_file_count"), int) and pr["changed_file_count"] >= 0]
    file_counts_complete = prs_complete and len(file_counts) == len(prs)
    file_stats = _nearest_rank(file_counts) if file_counts_complete else {"median": None, "p95": None}
    surface_counts: dict[str, int] = {}
    if files_complete and prs_complete:
        for pr in prs:
            if pr.get("files_complete") is not True:
                continue
            for filename in set(str(x) for x in pr.get("files") or [] if str(x)):
                surface_counts[filename] = surface_counts.get(filename, 0) + 1
    repeated = [
        {"path": path, "merged_pr_count": count}
        for path, count in sorted(surface_counts.items(), key=lambda item: (-item[1], item[0]))
        if count > 1
    ]
    failure_categories: dict[str, int] | None = None
    if runs_complete and details_complete:
        failure_categories = {key: 0 for key in (config.get("failure_categories") or {})}
        for run in completed_pr_runs:
            if run.get("conclusion") == "success":
                continue
            names = [str(x) for x in (run.get("failed_steps") or []) + (run.get("failed_jobs") or [])]
            failure_categories[_failure_category(names, config["failure_categories"])] += 1

    main_push_runs: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        sha = str(run.get("head_sha") or "")
        if run.get("event") == "push" and run.get("branch") == str(config.get("default_branch") or "main") and sha:
            main_push_runs.setdefault(sha, []).append(run)
    matched_merges = 0
    escaped = 0
    for pr in prs:
        merge_sha = str(pr.get("merge_sha") or "")
        linked = main_push_runs.get(merge_sha) or []
        terminal = [run for run in linked if run.get("conclusion") in {"success", "failure", "timed_out", "startup_failure"}]
        if terminal:
            matched_merges += 1
            if any(run.get("conclusion") != "success" for run in terminal):
                escaped += 1
    escaped_count = escaped if runs_complete and prs_complete and matched_merges == len(prs) else None
    minimum_runs = int(config["review_thresholds"]["minimum_validation_attempts"])
    minimum_changes = int(config["review_thresholds"]["minimum_merged_changes"])
    review_flags: list[str] = []
    if not runs_complete:
        review_flags.append("REVIEW_INCOMPLETE_VALIDATION_RUN_HISTORY")
    if not prs_complete:
        review_flags.append("REVIEW_INCOMPLETE_MERGED_PR_HISTORY")
    if not files_complete:
        review_flags.append("REVIEW_INCOMPLETE_CHANGED_FILE_HISTORY")
    if runs_complete and len(completed_pr_runs) < minimum_runs:
        review_flags.append("REVIEW_SMALL_VALIDATION_SAMPLE")
    if runs_complete and not duration_complete:
        review_flags.append("REVIEW_INCOMPLETE_RUNTIME_DURATION_DATA")
    if prs_complete and len(prs) < minimum_changes:
        review_flags.append("REVIEW_SMALL_MERGED_CHANGE_SAMPLE")
    if prs_complete and not file_counts_complete:
        review_flags.append("REVIEW_INCOMPLETE_CHANGED_FILE_COUNT_DATA")
    if runs_complete and not details_complete:
        review_flags.append("REVIEW_INCOMPLETE_FAILURE_DETAILS")
    if escaped_count is None:
        review_flags.append("REVIEW_INCOMPLETE_MERGE_SHA_VALIDATION_LINKAGE")

    report = {
        "version": 1,
        "run": {"mode": "monthly_maintenance_reliability", "period": period, "generated_at": generated_at, "repository_revision": repository_revision},
        "source": {"repository": str(data.get("repository") or ""), "input_digest": canonical_digest(data), "coverage": coverage},
        "metrics": {
            "validation": {
                "attempt_count": len(completed_pr_runs) if runs_complete else None,
                "passed_count": passed if runs_complete else None,
                "failed_count": failed if runs_complete else None,
                "cancelled_count": cancelled if runs_complete else None,
                "skipped_count": skipped if runs_complete else None,
                "pass_rate_basis_points": validation_rate,
                "duration_sample_count": len(durations) if runs_complete else None,
                "duration_seconds": duration_stats if duration_complete else {"median": None, "p95": None},
                "failure_categories": failure_categories,
            },
            "merged_changes": {
                "count": len(prs) if prs_complete else None,
                "labeled_hotfix_count": hotfix_count,
                "files_per_change_sample_count": len(file_counts) if prs_complete else None,
                "files_per_change": file_stats,
                "repeated_surface_count": len(repeated) if files_complete and prs_complete else None,
                "repeated_change_path_count": sum(row["merged_pr_count"] for row in repeated) if files_complete and prs_complete else None,
                "repeated_surfaces": repeated if files_complete and prs_complete else None,
            },
            "escaped_regressions": {
                "count": escaped_count,
                "merged_changes_with_exact_main_validation": matched_merges if prs_complete else None,
                "eligible_merged_changes": len(prs) if prs_complete else None,
            },
        },
        "definitions": {
            "validation_pass_rate": "Successful completed PR validation runs divided by successful plus failed/timed-out/startup-failed PR validation runs; cancelled/superseded and skipped runs are reported separately.",
            "duration_percentile": "Nearest-rank percentile over completed eligible PR validation runs with valid timestamps; seconds are rounded down to whole seconds.",
            "failure_categories": "One heuristic category per failed PR run based on failed job/step names; this is not a root-cause diagnosis.",
            "hotfix": "Merged PR carrying an exact normalized label listed in configuration; title text is not used.",
            "repeated_surfaces": "Repository paths changed by more than one merged PR in the reporting month.",
            "escaped_regression": "A failed main push validation run whose head SHA exactly matches a merged PR's merge SHA; missing linkage yields UNKNOWN.",
            "files_per_change": "Changed-file counts reported by GitHub for merged PRs in the reporting month.",
        },
        "review_flags": sorted(set(review_flags)),
        "authority": dict(config["authority"]),
    }
    report["reliability_fingerprint"] = canonical_digest({
        "period": period, "source": report["source"], "metrics": report["metrics"],
        "definitions": report["definitions"], "review_flags": report["review_flags"], "authority": report["authority"],
    })
    return report


def validate_report(doc: dict[str, Any], config: dict[str, Any]) -> list[str]:
    errors = validate_config(config)
    if doc.get("version") != 1:
        errors.append("maintenance reliability report version must be 1")
    run = doc.get("run") or {}
    if run.get("mode") != "monthly_maintenance_reliability" or not valid_period(str(run.get("period") or "")):
        errors.append("report run mode/period is invalid")
    if not re.fullmatch(r"[0-9a-f]{40}", str(run.get("repository_revision") or "")):
        errors.append("report repository_revision must be a 40-character lowercase Git SHA")
    source = doc.get("source") or {}
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(source.get("input_digest") or "")):
        errors.append("report source.input_digest must be a SHA-256 digest")
    metrics = doc.get("metrics") or {}
    validation = metrics.get("validation") or {}
    for key in ("attempt_count", "passed_count", "failed_count", "cancelled_count", "skipped_count", "pass_rate_basis_points", "duration_sample_count"):
        value = validation.get(key)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
            errors.append(f"metrics.validation.{key} must be null or a non-negative integer")
    rate = validation.get("pass_rate_basis_points")
    if rate is not None and rate > 10000:
        errors.append("validation pass rate may not exceed 10000 basis points")
    escaped = (metrics.get("escaped_regressions") or {}).get("count")
    if escaped is not None and (not isinstance(escaped, int) or isinstance(escaped, bool) or escaped < 0):
        errors.append("escaped regression count must be null or a non-negative integer")
    authority = doc.get("authority") or {}
    for name in ("automatic_remediation", "automatic_code_change", "branch_or_pr_authorized", "merge_authorized", "release_authorized"):
        if authority.get(name) is not False:
            errors.append(f"report authority.{name} must be false")
    if authority.get("human_review_required") is not True:
        errors.append("report authority.human_review_required must be true")
    expected = canonical_digest({
        "period": str(run.get("period") or ""), "source": source, "metrics": metrics,
        "definitions": doc.get("definitions") or {}, "review_flags": doc.get("review_flags") or [], "authority": authority,
    })
    if doc.get("reliability_fingerprint") != expected:
        errors.append("reliability_fingerprint does not match report content")
    return errors


def markdown(doc: dict[str, Any]) -> str:
    metrics = doc["metrics"]
    validation = metrics["validation"]
    changes = metrics["merged_changes"]
    escaped = metrics["escaped_regressions"]
    bp = validation.get("pass_rate_basis_points")
    pass_rate = "UNKNOWN" if bp is None else f"{bp / 100:.2f}%"
    duration = validation.get("duration_seconds") or {}
    files = changes.get("files_per_change") or {}
    lines = [
        f"# Maintenance Reliability — {doc['run']['period']}", "",
        f"- Validation pass rate: **{pass_rate}** (eligible attempts: {validation.get('attempt_count')})",
        f"- Validation duration: median `{duration.get('median')}` s / p95 `{duration.get('p95')}` s (n=`{validation.get('duration_sample_count')}`)",
        f"- Merged changes: `{changes.get('count')}`; labeled hotfixes: `{changes.get('labeled_hotfix_count')}`",
        f"- Files per merged change: median `{files.get('median')}` / p95 `{files.get('p95')}` (n=`{changes.get('files_per_change_sample_count')}`)",
        f"- Repeated changed surfaces: `{changes.get('repeated_surface_count')}`; repeated path touches: `{changes.get('repeated_change_path_count')}`",
        f"- Escaped regressions: `{escaped.get('count')}`; exact merge-SHA links: `{escaped.get('merged_changes_with_exact_main_validation')}` / `{escaped.get('eligible_merged_changes')}`",
        f"- Evidence fingerprint: `{doc['reliability_fingerprint']}`",
        "", "## Failure categories", "",
    ]
    categories = validation.get("failure_categories")
    if categories is None:
        lines.append("UNKNOWN — failure evidence is incomplete.")
    else:
        lines.extend(f"- {key}: {value}" for key, value in categories.items())
    lines.extend(["", "## Data coverage", "", "```yaml", yaml.safe_dump(doc["source"]["coverage"], sort_keys=False).rstrip(), "```", ""])
    flags = doc.get("review_flags") or []
    lines.extend(["## Human review", ""])
    lines.extend([f"- {flag}" for flag in flags] if flags else ["- No deterministic review flag."])
    lines.extend(["", "Failure labels are heuristics from job/step names, not root-cause diagnoses. Missing or truncated source data remains UNKNOWN. This report authorizes no automatic remediation, code change, PR, merge or release.", ""])
    return "\n".join(lines)


def _write_yaml(path: str, value: Any) -> None:
    Path(path).write_text(yaml.safe_dump(value, sort_keys=False, allow_unicode=True), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    collect = sub.add_parser("collect")
    collect.add_argument("--repo", required=True)
    collect.add_argument("--period", required=True)
    collect.add_argument("--config", default=str(CONFIG))
    collect.add_argument("--output", required=True)
    build = sub.add_parser("build")
    build.add_argument("--input-json", required=True)
    build.add_argument("--config", default=str(CONFIG))
    build.add_argument("--repository-revision", required=True)
    build.add_argument("--generated-at", required=True)
    build.add_argument("--output", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("report")
    validate.add_argument("--config", default=str(CONFIG))
    render = sub.add_parser("markdown")
    render.add_argument("report")
    render.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        config = load_mapping(getattr(args, "config", CONFIG))
        if args.command == "collect":
            data = collect_data(repo=args.repo, period=args.period, config=config)
            Path(args.output).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return 0
        if args.command == "build":
            data = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
            report = build_report(data, config, repository_revision=args.repository_revision, generated_at=args.generated_at)
            _write_yaml(args.output, report)
            return 0
        report = load_mapping(args.report)
        if args.command == "validate":
            errors = validate_report(report, config)
            for error in errors:
                print(f"- {error}")
            if errors:
                return 1
            print("Maintenance Reliability report valid")
            return 0
        if args.command == "markdown":
            Path(args.output).write_text(markdown(report), encoding="utf-8")
            return 0
    except (OSError, ValueError, RuntimeError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(f"maintenance reliability error: {exc}")
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Create and collect bounded full-run validation observations; never skip tests."""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from performance_evidence import observed_distribution

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "scripts"))
import validation_graduation
from validation.registry import VALIDATORS

MAX_RESPONSE_BYTES = 50 * 1024 * 1024
MAX_RUNS = 5000
MAX_PAGES = 50
MAX_ZIP_MEMBERS = 20
MAX_OBSERVATION_BYTES = 2 * 1024 * 1024
API = "https://api.github.com"


class ObservationError(ValueError):
    pass


def read_mapping(path: Path) -> dict[str, Any] | None:
    if not path.is_file() or path.stat().st_size > MAX_OBSERVATION_BYTES:
        return None
    text = path.read_text(encoding="utf-8")
    value = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    return value if isinstance(value, dict) else None


def sha256(path: Path) -> str | None:
    if not path.is_file() or path.stat().st_size > MAX_RESPONSE_BYTES:
        return None
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_observation(
    event: dict[str, Any], shadow: dict[str, Any] | None,
    timing: dict[str, Any] | None, gate: dict[str, Any] | None,
    *, run_id: str, run_attempt: str, workflow: str,
) -> dict[str, Any]:
    pr_data = event.get("pull_request") or {}
    pr = event.get("number")
    head = str(pr_data.get("head", {}).get("sha") or "")
    base = str(pr_data.get("base", {}).get("sha") or "")
    expected = [spec.module for spec in VALIDATORS]
    timing_checks = timing.get("checks", []) if timing else []
    actual = sorted({
        str(item.get("name")) for item in timing_checks
        if isinstance(item, dict) and str(item.get("name", "")).startswith("validation.")
        and item.get("status") in {"PASS", "FAIL"}
    })
    failed = sorted({
        str(item.get("name")) for item in timing_checks
        if isinstance(item, dict) and str(item.get("name", "")).startswith("validation.")
        and item.get("status") == "FAIL"
    })
    gate_checks = (gate or {}).get("checks", [])
    repo_check: dict[str, Any] = next((item for item in gate_checks if item.get("id") == "repository-validation"), {})
    gate_status = str(repo_check.get("status", "UNAVAILABLE"))
    full = bool(
        shadow and timing and gate and gate_status in {"PASS", "FAIL"}
        and timing.get("status") in {"PASS", "FAIL"}
        and sorted(actual) == sorted(expected)
    )
    paths = shadow.get("changed_paths", []) if shadow else []
    predicted_skips = sorted((shadow or {}).get("would_skip", []))
    head_valid = bool(re.fullmatch(r"[0-9a-f]{40,64}", head))
    base_valid = bool(re.fullmatch(r"[0-9a-f]{40,64}", base))
    timestamp = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    candidate_head = str((shadow or {}).get("head", ""))
    candidate_base = str((shadow or {}).get("base", ""))
    identity_matches = head_valid and base_valid and head == candidate_head and base == candidate_base
    failed_gate = gate_status == "FAIL" or bool(timing and timing.get("status") == "FAIL")
    # If the full run failed but the harness cannot attribute its failure to a
    # validator, conservatively treat every predicted skip as failed.
    if failed_gate:
        failed = sorted(set(failed) | set(predicted_skips))
    observation = {
        "schema_version": 1,
        "timestamp": timestamp,
        "workflow": workflow,
        "run_id": str(run_id),
        "run_attempt": int(run_attempt) if str(run_attempt).isdigit() else None,
        "source_digests": {
            "shadow_plan": os.environ.get("AIPS_SHADOW_DIGEST"),
            "validation_timing": os.environ.get("AIPS_TIMING_DIGEST"),
            "integration_gate": os.environ.get("AIPS_GATE_DIGEST"),
        },
        "record": {
            "pull_request": pr if isinstance(pr, int) else None,
            "workflow": workflow,
            "run_id": str(run_id),
            "run_attempt": int(run_attempt) if str(run_attempt).isdigit() else None,
            "source_digests": {
                "shadow_plan": os.environ.get("AIPS_SHADOW_DIGEST"),
                "validation_timing": os.environ.get("AIPS_TIMING_DIGEST"),
                "integration_gate": os.environ.get("AIPS_GATE_DIGEST"),
            },
            "base_sha": base,
            "head_sha": head,
            "timestamp": timestamp,
            "change_class": str((shadow or {}).get("change_class", "unknown")),
            "changed_paths": paths if isinstance(paths, list) else [],
            "would_skip": predicted_skips,
            "failed_modules": failed,
            "actual_modules_run": actual,
            "full_validation_run": bool(full and identity_matches),
            "deterministic_full_audit": validation_graduation.deterministic_full_audit(head, 10) if head_valid else False,
            "full_validation_result": "FAIL" if failed_gate else "PASS" if full and timing and timing.get("status") == "PASS" and gate_status == "PASS" else "INCOMPLETE",
            "evidence_complete": bool(shadow and timing and gate and identity_matches),
            "measurements": {
                "repository_duration_ms": (timing or {}).get("total_duration_ms") if full and identity_matches else None,
                "validators": [{"name": item["name"], "duration_ms": item.get("duration_ms")}
                               for item in timing_checks if isinstance(item, dict)
                               and item.get("name") in actual] if full and identity_matches else [],
            },
        },
    }
    return observation


def summarize_timings(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep incomplete evidence separate and avoid counting reruns as new PRs."""
    candidates: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        if record.get("evidence_complete") is not True or record.get("full_validation_run") is not True:
            continue
        key = (str(record.get("pull_request")), str(record.get("head_sha")))
        prior = candidates.get(key)
        if prior is None or str(record.get("timestamp", "")) > str(prior.get("timestamp", "")):
            candidates[key] = record
    classes = sorted({str(record.get("change_class", "unknown")) for record in candidates.values()})
    return {"status": "OBSERVED" if candidates else "UNKNOWN", "unit": "milliseconds",
            "candidate_count": len(candidates), "selective_execution_authorized": False,
            "by_change_class": {category: observed_distribution([
                (record.get("measurements") or {}).get("repository_duration_ms")
                for record in candidates.values() if record.get("change_class", "unknown") == category
            ]) for category in classes}}


def safe_observation_zip(payload: bytes) -> dict[str, Any]:
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ObservationError("artifact download exceeds size limit")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        entries = archive.infolist()
        if len(entries) > MAX_ZIP_MEMBERS:
            raise ObservationError("artifact contains too many files")
        for entry in entries:
            name = PurePosixPath(entry.filename)
            if name.is_absolute() or ".." in name.parts or entry.file_size > MAX_OBSERVATION_BYTES:
                raise ObservationError("artifact contains an unsafe or oversized path")
        matches = [entry for entry in entries if PurePosixPath(entry.filename).name == "observation.json"]
        if len(matches) != 1:
            raise ObservationError("artifact must contain exactly one observation.json")
        data = json.loads(archive.read(matches[0]))
        if not isinstance(data, dict) or not isinstance(data.get("record"), dict):
            raise ObservationError("observation schema is invalid")
        return data


def api_get(url: str, token: str) -> tuple[dict[str, Any] | list[Any], bytes | None]:
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "aips-validation-observation-collector",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read(MAX_RESPONSE_BYTES + 1)
        if len(payload) > MAX_RESPONSE_BYTES:
            raise ObservationError("GitHub API response exceeds size limit")
        if "zip" in response.headers.get("Content-Type", "") or "octet-stream" in response.headers.get("Content-Type", ""):
            return {}, payload
        value = json.loads(payload)
        if not isinstance(value, (dict, list)):
            raise ObservationError("GitHub API returned an unexpected payload")
        return value, None


def download_artifact(repo: str, artifact_id: int, token: str) -> bytes:
    """Follow GitHub's signed artifact redirect without forwarding the API token."""
    url = f"{API}/repos/{repo}/actions/artifacts/{artifact_id}/zip"
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "aips-validation-observation-collector",
    })

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, new_url):
            return None

    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
            payload = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as response:
        if response.code not in {301, 302, 303, 307, 308}:
            raise
        location = response.headers.get("Location", "")
        parsed = urllib.parse.urlsplit(location)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ObservationError("artifact redirect must use a credential-free HTTPS URL")
        # This signed storage URL grants access to one artifact; never attach GITHUB_TOKEN.
        with urllib.request.urlopen(urllib.request.Request(location, headers={"User-Agent": "aips-validation-observation-collector"}), timeout=30) as artifact:
            payload = artifact.read(MAX_RESPONSE_BYTES + 1)
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ObservationError("artifact download exceeds size limit")
    return payload


def collect_dataset(repo: str, token: str, start: date, end: date) -> dict[str, Any]:
    if not re.fullmatch(r"[^/\s]+/[^/\s]+", repo):
        raise ObservationError("repository must be owner/name")
    if end < start or (end - start).days > 89:
        raise ObservationError("collection window must be bounded to 1..90 days")
    query = urllib.parse.urlencode({"event": "pull_request", "per_page": 100, "created": f"{start.isoformat()}T00:00:00Z..{end.isoformat()}T23:59:59Z"})
    base_url = f"{API}/repos/{repo}/actions/workflows/validate.yml/runs"
    runs: list[dict[str, Any]] = []
    complete = True
    pages = 0
    total = 0
    while pages < MAX_PAGES and len(runs) < MAX_RUNS:
        pages += 1
        try:
            url = f"{base_url}?{query}&page={pages}"
            payload, _ = api_get(url, token)
        except (urllib.error.URLError, OSError, ValueError, ObservationError):
            complete = False
            break
        if not isinstance(payload, dict):
            complete = False
            break
        batch = payload.get("workflow_runs", []) if isinstance(payload, dict) else []
        if not isinstance(batch, list):
            complete = False
            break
        total = int(payload.get("total_count", len(batch)))
        runs.extend(item for item in batch if isinstance(item, dict))
        if len(runs) >= total:
            break
    if len(runs) < total or len(runs) >= MAX_RUNS or (pages >= MAX_PAGES and len(runs) < total):
        complete = False
    records: list[dict[str, Any]] = []
    artifacts_checked = 0
    for run in runs:
        prs = run.get("pull_requests") or []
        if run.get("event") != "pull_request" or not prs:
            complete = False
            continue
        if run.get("status") != "completed":
            complete = False
            continue
        pr = prs[0].get("number")
        run_id = run.get("id")
        attempt = run.get("run_attempt", 1)
        if not isinstance(pr, int) or not isinstance(run_id, int):
            complete = False
            continue
        artifacts_checked += 1
        try:
            listing, _ = api_get(f"{API}/repos/{repo}/actions/runs/{run_id}/artifacts?per_page=100", token)
            artifacts = listing.get("artifacts", []) if isinstance(listing, dict) else []
            prefix = f"validation-observation-{run_id}-{attempt}"
            item = next((artifact for artifact in artifacts if artifact.get("name") == prefix and not artifact.get("expired")), None)
            if not item or not isinstance(item.get("id"), int):
                complete = False
                continue
            archive = download_artifact(repo, item["id"], token)
            observation = safe_observation_zip(archive)
            record = observation["record"]
            if (
                record.get("pull_request") != pr
                or record.get("head_sha") != run.get("head_sha")
                or record.get("run_id") != str(run_id)
                or record.get("run_attempt") != int(attempt)
            ):
                complete = False
                continue
            records.append(record)
        except (urllib.error.URLError, OSError, ValueError, ObservationError, zipfile.BadZipFile):
            complete = False
    # Keep the newest run per PR; preserve latest-attempt identity and avoid reruns inflating cohort size.
    latest: dict[int, dict[str, Any]] = {}
    for record in records:
        pr = record["pull_request"]
        old = latest.get(pr)
        key = (str(record.get("timestamp", "")), int(record.get("run_attempt") or 0), str(record.get("head_sha", "")))
        old_key = (str(old.get("timestamp", "")), int(old.get("run_attempt") or 0), str(old.get("head_sha", ""))) if old else None
        if old is None or (old_key is not None and key > old_key):
            latest[pr] = record
    return {
        "window_start": start.isoformat(), "window_end": end.isoformat(),
        "artifact_history_complete": complete and pages < MAX_PAGES and len(runs) < MAX_RUNS,
        "collection": {"workflow_run_count": len(runs), "artifacts_checked": artifacts_checked, "pages_read": pages, "history_complete": complete},
        "records": list(latest.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    capture = sub.add_parser("capture")
    capture.add_argument("--event", type=Path, required=True)
    capture.add_argument("--shadow", type=Path)
    capture.add_argument("--timing", type=Path)
    capture.add_argument("--gate", type=Path)
    capture.add_argument("--output", type=Path, required=True)
    capture.add_argument("--run-id", required=True)
    capture.add_argument("--run-attempt", required=True)
    capture.add_argument("--workflow", default="validate")
    collect = sub.add_parser("collect")
    collect.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    collect.add_argument("--days", type=int, default=30)
    collect.add_argument("--output", type=Path, required=True)
    collect.add_argument("--report", type=Path, required=True)
    collect.add_argument("--end-date", type=date.fromisoformat, default=datetime.now(UTC).date())
    collect.add_argument("--require-ready", action="store_true", help="Return non-zero when the observation cohort is not ready for Human review")
    args = parser.parse_args()
    try:
        if args.command == "capture":
            event = read_mapping(args.event) or {}
            sources = {"shadow": args.shadow, "timing": args.timing, "gate": args.gate}
            loaded = {key: read_mapping(path) if path else None for key, path in sources.items()}
            for key, path in sources.items():
                os.environ[{"shadow": "AIPS_SHADOW_DIGEST", "timing": "AIPS_TIMING_DIGEST", "gate": "AIPS_GATE_DIGEST"}[key]] = (sha256(path) or "") if path else ""
            observation = create_observation(event, loaded["shadow"], loaded["timing"], loaded["gate"], run_id=args.run_id, run_attempt=args.run_attempt, workflow=args.workflow)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(observation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps({"evidence_complete": observation["record"]["evidence_complete"], "full_validation_result": observation["record"]["full_validation_result"]}))
            return 0
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            raise ObservationError("GITHUB_TOKEN is required for read-only artifact collection")
        if not 1 <= args.days <= 90:
            raise ObservationError("days must be between 1 and 90")
        start = args.end_date - timedelta(days=args.days - 1)
        dataset = collect_dataset(args.repo, token, start, args.end_date)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        config = yaml.safe_load((ROOT / "config/validation-graduation.yaml").read_text(encoding="utf-8")) or {}
        scope = yaml.safe_load((ROOT / "config/validation-scope.yaml").read_text(encoding="utf-8")) or {}
        report = validation_graduation.evaluate(config, scope, dataset)
        report["timing_summary"] = summarize_timings(dataset["records"])
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "unique_pull_request_count": report.get("unique_pull_request_count"), "artifact_history_complete": dataset["artifact_history_complete"], "errors": report["errors"]}, indent=2))
        status = report.get("status")
        if status == "READY_FOR_HUMAN_REVIEW":
            return 0
        if status == "NOT_READY":
            return 1 if args.require_ready else 0
        raise ObservationError(f"graduation evaluator returned an unknown status: {status!r}")
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError, ObservationError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

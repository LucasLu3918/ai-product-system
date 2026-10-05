from __future__ import annotations

import io
import sys
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import validation_observation as observation
from validation.registry import VALIDATORS


def archive(record: dict) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as item:
        import json
        item.writestr("observation.json", json.dumps({"schema_version": 1, "record": record}))
    return buffer.getvalue()


def main() -> int:
    base = "a" * 40
    head = "b" * 40
    event = {"number": 17, "pull_request": {"base": {"sha": base}, "head": {"sha": head}}}
    shadow = {"base": base, "head": head, "change_class": "standard", "changed_paths": ["scripts/a.py"], "would_skip": ["validation.extra"]}
    timing = {"status": "PASS", "checks": [{"name": spec.module, "status": "PASS"} for spec in VALIDATORS]}
    gate = {"checks": [{"id": "repository-validation", "status": "PASS"}]}
    full = observation.create_observation(event, shadow, timing, gate, run_id="10", run_attempt="1", workflow="validate")
    record = full["record"]
    assert record["full_validation_run"] is True and record["full_validation_result"] == "PASS"
    assert record["actual_modules_run"] == sorted(spec.module for spec in VALIDATORS)
    assert record["pull_request"] == 17 and record["base_sha"] == base and record["head_sha"] == head
    assert record["run_id"] == "10" and record["run_attempt"] == 1
    failed_gate = {"checks": [{"id": "repository-validation", "status": "FAIL"}]}
    failed = observation.create_observation(event, shadow, timing, failed_gate, run_id="12", run_attempt="1", workflow="validate")
    assert failed["record"]["full_validation_run"] is True
    assert failed["record"]["failed_modules"] == ["validation.extra"]
    assert failed["record"]["full_validation_result"] == "FAIL"

    missing = observation.create_observation(event, shadow, None, gate, run_id="11", run_attempt="1", workflow="validate")
    assert missing["record"]["full_validation_run"] is False
    assert missing["record"]["full_validation_result"] == "INCOMPLETE"

    runs = [
        {"id": 10, "run_attempt": 1, "event": "pull_request", "status": "completed", "head_sha": head, "pull_requests": [{"number": 17}]},
        {"id": 11, "run_attempt": 2, "event": "pull_request", "status": "completed", "head_sha": head, "pull_requests": [{"number": 17}]},
    ]
    records = []
    for run in runs:
        records.append({
            "pull_request": 17, "base_sha": base, "head_sha": head,
            "timestamp": "2026-10-05T00:00:00Z" if run["id"] == 10 else "2026-10-05T01:00:00Z",
            "run_attempt": run["run_attempt"], "run_id": str(run["id"]),
        })
    original_api = observation.api_get
    original_download = observation.download_artifact

    def fake_api(url: str, token: str):
        if "/actions/workflows/validate.yml/runs?" in url:
            return {"total_count": 2, "workflow_runs": runs}, None
        if "/actions/runs/10/artifacts" in url:
            return {"artifacts": [{"id": 110, "name": "validation-observation-10-1", "expired": False}]}, None
        if "/actions/runs/11/artifacts" in url:
            return {"artifacts": [{"id": 111, "name": "validation-observation-11-2", "expired": False}]}, None
        raise AssertionError(url)

    def fake_download(repo: str, artifact_id: int, token: str) -> bytes:
        assert repo == "owner/repo" and token == "test-token"
        return archive(records[0] if artifact_id == 110 else records[1])

    observation.api_get = fake_api
    observation.download_artifact = fake_download
    try:
        dataset = observation.collect_dataset("owner/repo", "test-token", date(2026, 10, 5), date(2026, 10, 5))
    finally:
        observation.api_get = original_api
        observation.download_artifact = original_download
    assert dataset["artifact_history_complete"] is True
    assert len(dataset["records"]) == 1 and dataset["records"][0]["run_id"] == "11"

    original_build = observation.urllib.request.build_opener
    original_urlopen = observation.urllib.request.urlopen

    class RedirectingOpener:
        def open(self, request, timeout):
            assert request.get_header("Authorization") == "Bearer test-token"
            raise observation.urllib.error.HTTPError(request.full_url, 302, "redirect", {"Location": "https://storage.example.test/signed"}, None)

    def signed_download(request, timeout):
        assert request.get_header("Authorization") is None, "API token must not follow GitHub's artifact redirect"
        return io.BytesIO(b"signed-artifact")

    observation.urllib.request.build_opener = lambda *_handlers: RedirectingOpener()
    observation.urllib.request.urlopen = signed_download
    try:
        assert observation.download_artifact("owner/repo", 7, "test-token") == b"signed-artifact"
    finally:
        observation.urllib.request.build_opener = original_build
        observation.urllib.request.urlopen = original_urlopen

    unsafe = io.BytesIO()
    with zipfile.ZipFile(unsafe, "w") as item:
        item.writestr("../observation.json", "{}")
    try:
        observation.safe_observation_zip(unsafe.getvalue())
    except observation.ObservationError:
        pass
    else:
        raise AssertionError("zip traversal path must be rejected")

    print("VALIDATION OBSERVATION LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

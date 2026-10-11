"""Prompt-free evidence for cross-profile creative benchmark coverage and failure stages."""
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import creative_quality_benchmark as benchmark


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))


def main() -> int:
    dataset = benchmark.load_dataset()
    assert len(dataset["profiles"]) == 3 and len(dataset["cases"]) == 6
    profiles = [item["id"] for item in dataset["profiles"]]
    with tempfile.TemporaryDirectory(prefix="creative-quality-benchmark-") as temporary:
        project = Path(temporary)
        image = project / "sample.png"
        image.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 2, 0, 0, 0))
            + png_chunk(b"IDAT", zlib.compress((b"\0" + b"\xff\0\0" * 8) * 8))
            + png_chunk(b"IEND", b"")
        )
        common = {"source": "observed_host", "provider": "mflux_local",
                  "model_revision": "fixture-only", "device": "fixture-only"}
        completed = {
            **common, "profile_id": profiles[0], "case_id": "identity-retention", "status": "COMPLETE",
            "output": "sample.png", "sha256": "sha256:" + hashlib.sha256(image.read_bytes()).hexdigest(),
            "elapsed_ms": 17, "visual_review": {"reviewer_type": "human", "reviewer": "fixture",
                "dimensions": {"character_identity": "PASS"}}, "user_acceptance": "NOT_RECORDED",
        }
        failures = [
            {**common, "profile_id": profiles[0], "case_id": "outfit-consistency", "status": "FAILED",
             "failure_stage": "model", "reason_code": "model_unavailable"},
            {**common, "profile_id": profiles[1], "case_id": "recovery-after-rejection", "status": "FAILED",
             "failure_stage": "check", "reason_code": "output_check_failed"},
            {**common, "profile_id": profiles[2], "case_id": "prompt-compilation", "status": "FAILED",
             "failure_stage": "compiler", "reason_code": "prompt_compile_invalid"},
        ]
        evidence = {"version": 2, "dataset_id": dataset["id"], "trials": [completed, *failures]}
        report = benchmark.summarize_trials(project, evidence)
        assert report["status"] == "RECORDED" and report["artifact_bound_samples"] == 1
        assert report["failures_by_stage"] == {"model": 1, "check": 1, "compiler": 1}
        coverage = report["dataset_coverage"]
        assert coverage["status"] == "PARTIAL" and coverage["expected_cells"] == 18 and coverage["observed_cells"] == 4
        assert coverage["profiles"][0]["complete_trials"] == 1 and coverage["profiles"][0]["failed_trials"] == 1
        assert report["visual_dimensions"]["character_identity"]["pass"] == 1
        assert report["user_acceptance_count"] == 0 and report["user_acceptance_status"] == "NOT_RECORDED"
        assert "prompt" not in report and "traceback" not in report

        evidence_path = project / "evidence.json"
        evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
        cli = subprocess.run([sys.executable, str(ROOT / "scripts/creative_quality_benchmark.py"),
                              "--project", str(project), "--evidence", str(evidence_path)],
                             cwd=ROOT, capture_output=True, text=True, timeout=15, check=False)
        assert cli.returncode == 0, cli.stdout + cli.stderr
        assert json.loads(cli.stdout)["dataset_coverage"]["observed_cells"] == 4

        malformed = {**evidence, "trials": [{**failures[0], "failure_stage": "model_and_check"}]}
        rejected = benchmark.summarize_trials(project, malformed)
        assert rejected["invalid_or_unobserved"] == 1 and rejected["failures_by_stage"] == {"model": 0, "check": 0, "compiler": 0}
        malformed = {**evidence, "trials": [{**failures[0], "traceback": "/private/user/path"}]}
        assert benchmark.summarize_trials(project, malformed)["invalid_or_unobserved"] == 1
        legacy = benchmark.summarize_trials(project, {"version": 1, "trials": []})
        assert legacy["dataset_coverage"]["status"] == "UNVERIFIED"
        assert legacy["status"] == "UNKNOWN" and legacy["user_acceptance_status"] == "NOT_RECORDED"
    print("Creative quality benchmark lifecycle PASS: three-profile matrix, case coverage, artifact-bound visual review, separate model/check/compiler failures, legacy UNKNOWN, and independent user acceptance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

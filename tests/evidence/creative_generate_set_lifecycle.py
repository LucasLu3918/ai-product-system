"""Resumable Creative generation-set orchestration evidence."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import creative_execution as creative


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="aips-generate-set-") as temporary:
        root = Path(temporary)
        for name in ("first", "second", "third"):
            bundle = {
                "version": 1, "mode": "EPHEMERAL", "operation": "generate",
                "prompt": f"Generate {name}", "output_scope": f"artifacts/{name}",
                "output_path": f"artifacts/{name}/image.png", "max_retries": 0, "timeout_seconds": 10,
                "runtime": "fixture", "runtime_version": "1",
                "model": {"id": "fixture", "revision": "sha", "license": "fixture", "license_source": "https://example.test"},
            }
            (root / f"{name}.yaml").write_text(yaml.safe_dump(bundle), encoding="utf-8")
        job_path = root / "CREATIVE_JOB_MANIFEST.yaml"
        job_path.write_text(yaml.safe_dump({
            "version": 1,
            "items": [{"id": name, "bundle": f"{name}.yaml"} for name in ("first", "second", "third")],
        }), encoding="utf-8")
        calls: list[str] = []
        failed_once = False
        # Simulate a process interruption after image + provenance publication
        # but before the batch checkpoint was recorded.
        third_bundle = root / "third.yaml"
        third = yaml.safe_load(third_bundle.read_text())
        orphan_output = root / third["output_path"]
        orphan_output.parent.mkdir(parents=True)
        orphan_output.write_bytes(b"orphaned but valid output")
        orphan_manifest = orphan_output.parent / "creative-execution-manifest.json"
        orphan_manifest.write_text(json.dumps({
            "status": "COMPLETE", "bundle_sha256": creative.digest(third_bundle),
            "output": {"path": third["output_path"], "sha256": creative.digest(orphan_output)},
        }))

        def preflight(_root: Path, _bundle: str):
            return {"status": "READY"}

        def execute(project: Path, bundle: str):
            nonlocal failed_once
            item_id = Path(bundle).stem
            calls.append(item_id)
            if item_id == "second" and not failed_once:
                failed_once = True
                raise creative.Blocked("fixture_engine_unavailable", "fixture")
            bundle_data = yaml.safe_load((project / bundle).read_text())
            output = project / bundle_data["output_path"]
            manifest = output.parent / "creative-execution-manifest.json"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"fixture image")
            output_hash = creative.digest(output)
            manifest.write_text(json.dumps({
                "status": "COMPLETE", "bundle_sha256": creative.digest(project / bundle),
                "output": {"path": bundle_data["output_path"], "sha256": output_hash},
            }), encoding="utf-8")
            return {"status": "COMPLETE", "reason_code": "execution_complete",
                    "output": bundle_data["output_path"],
                    "manifest": manifest.relative_to(project).as_posix()}

        with patch.object(creative, "is_git_workspace", return_value=False), \
             patch.object(creative, "preflight", side_effect=preflight), \
             patch.object(creative, "execute", side_effect=execute):
            try:
                creative.generate_set(root, job_path.name, max_items=2)
            except creative.Blocked as exc:
                assert exc.reason_code == "creative_output_limit_exceeded"
            else:
                raise AssertionError("job exceeded the prompt-scoped output grant")
            link = root / "linked.yaml"
            link.symlink_to(root / "first.yaml")
            symlink_job = root / "SYMLINK.yaml"
            symlink_job.write_text(yaml.safe_dump({"version": 1, "items": [{"id": "link", "bundle": "linked.yaml"}]}))
            try:
                creative.generate_set(root, symlink_job.name)
            except creative.Blocked as exc:
                assert exc.reason_code == "creative_job_manifest_invalid"
            else:
                raise AssertionError("symlinked job Bundle was accepted")
            first = creative.generate_set(root, job_path.name)
            assert first["status"] == "PARTIAL" and first["completed"] == 2 and first["failed"] == 1
            assert calls == ["first", "second"], "batch must continue after an item fails and recover orphaned outputs"
            assert first["items"][2]["status"] == "SKIPPED_COMPLETE"
            calls.clear()
            second = creative.generate_set(root, job_path.name)
            assert second["status"] == "COMPLETE" and second["completed"] == 3
            assert calls == ["second"], "resume must skip only hash-verified completed outputs"
            assert [item["status"] for item in second["items"]] == ["SKIPPED_COMPLETE", "COMPLETE", "SKIPPED_COMPLETE"]
            result = json.loads((root / "CREATIVE_JOB_MANIFEST.results.json").read_text())
            assert "fixture" not in json.dumps(result), "result must not persist prompt/provider details"

            invalid = root / "INVALID.yaml"
            invalid.write_text(yaml.safe_dump({"version": 1, "items": [{"id": "escape", "bundle": "../outside.yaml"}]}))
            try:
                creative.generate_set(root, invalid.name)
            except creative.Blocked as exc:
                assert exc.reason_code in {"path_outside_project", "creative_job_manifest_invalid"}
            else:
                raise AssertionError("path traversal was accepted")

        executable = root / "mflux-generate"
        executable.write_text("#!/bin/sh\nprintf 'mflux fixture 1\n'\n", encoding="utf-8")
        executable.chmod(0o755)
        with patch.object(creative.shutil, "which", side_effect=lambda command: str(executable) if command == "mflux-generate" else None), \
             patch.object(creative.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="mflux fixture 1.0\n", stderr="")) as probe:
            discovered = creative.discover(root)
        assert discovered["engine_probe"] == "bounded_version_only"
        assert discovered["health_summary"]["healthy_commands"] == 1
        runtime = next(item for item in discovered["runtimes"] if item["command"] == "mflux-generate")
        assert runtime["capability_status"] == "COMMAND_PRESENT"
        assert runtime["version_status"] == "PARSED"
        assert probe.call_count == 1 and discovered["generation_executed"] is False

    print("Creative generate-set PASS: per-item preflight, continue-on-failure, verified resume and version-only health probe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

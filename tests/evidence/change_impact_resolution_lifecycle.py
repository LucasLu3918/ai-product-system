from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


class ChangeImpactResolutionLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="aips-impact-resolution-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.evidence = self.root / "reviewed.md"
        self.evidence.write_text("Reviewed bounded impact evidence.\n", encoding="utf-8")
        self.artifact = self.root / "CHANGE_IMPACT.yaml"
        self.doc = {
            "version": 1,
            "status": "IMPLEMENTATION_APPROVED",
            "change": {"id": "resolution-lifecycle", "target_paths": []},
            "scope_review": {"status": "APPROVED", "approval_reference": "scope-approval", "approved_at": "2026-09-26"},
            "unknowns": [{
                "id": "bounded-graph-coverage",
                "description": "Global architecture coverage remains incomplete outside the reviewed seeds.",
                "disposition": "ACCEPTED_LIMITATION",
                "resolution": "Use the reviewed seed scope while preserving global partial coverage.",
                "evidence": [{
                    "kind": "repository_file",
                    "path": "reviewed.md",
                    "sha256": hashlib.sha256(self.evidence.read_bytes()).hexdigest(),
                }],
                "review": {
                    "status": "APPROVED",
                    "reviewer": "human",
                    "approval_reference": "human-review-1",
                    "reviewed_at": "2026-09-26T04:06:50Z",
                },
            }],
        }

    def validate_cli(self) -> subprocess.CompletedProcess[str]:
        self.artifact.write_text(yaml.safe_dump(self.doc, sort_keys=False), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/project_intelligence.py"), "impact-validate",
             "--project", str(self.root), "--path", str(self.artifact), "--format", "json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_cli_accepts_evidence_backed_human_review(self) -> None:
        proc = self.validate_cli()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn('"valid": true', proc.stdout)

    def test_cli_keeps_legacy_string_blocking(self) -> None:
        self.doc["unknowns"] = ["legacy unresolved unknown"]
        proc = self.validate_cli()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("legacy string unknown remains unresolved", proc.stdout)

    def test_cli_rejects_missing_human_review(self) -> None:
        self.doc["unknowns"][0]["review"] = {"status": "APPROVED", "reviewer": "agent"}
        proc = self.validate_cli()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("reviewer as human", proc.stdout)


if __name__ == "__main__":
    unittest.main()

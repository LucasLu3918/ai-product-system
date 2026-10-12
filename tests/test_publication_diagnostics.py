from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import publication_diagnostics as diagnostics


class PublicationDiagnosticsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        subprocess.run(["git", "init", "-b", "main"], cwd=self.root, check=True,
                       capture_output=True, text=True)
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/fixture/repo.git"],
                       cwd=self.root, check=True, capture_output=True, text=True)

    def test_doctor_reports_policy_and_checks_without_side_effects(self):
        real_run = subprocess.run
        calls = []

        def run(argv, *args, **kwargs):
            if Path(argv[0]).name != "gh":
                return real_run(argv, *args, **kwargs)
            calls.append(list(argv))
            if argv[1:3] == ["auth", "status"]:
                return subprocess.CompletedProcess(argv, 0, "", "")
            endpoint = argv[-1]
            if endpoint == "repos/fixture/repo":
                data = {"allow_squash_merge": True, "allow_merge_commit": False,
                        "allow_rebase_merge": True}
            elif endpoint.endswith("/rulesets?includes_parents=true&per_page=100"):
                data = []
            elif endpoint.endswith("/branches/main/protection"):
                data = {"required_status_checks": {"contexts": ["repository"]}}
            else:
                raise AssertionError("unexpected GitHub read")
            return subprocess.CompletedProcess(argv, 0, json.dumps(data), "")

        with patch("publication_diagnostics.subprocess.run", side_effect=run), \
                patch("publication_authority._remote_default_branch", return_value="main"), \
                patch("publication_planning._prs", return_value=[]):
            result = diagnostics.doctor(self.root)
        self.assertEqual(result["status"], "READY", result)
        self.assertFalse(result["authorized"])
        self.assertTrue(result["read_only"])
        self.assertEqual(result["merge_methods"], ["rebase", "squash"])
        self.assertEqual(result["policy"]["required_checks"], ["repository"])
        self.assertFalse(result["policy"]["api_write_performed"])
        self.assertTrue(all(call[:2] != ["gh", "api"] or " -X " not in " ".join(call) for call in calls))

    def test_incomplete_protection_visibility_stays_blocked_unknown(self):
        real_run = subprocess.run

        def run(argv, *args, **kwargs):
            if Path(argv[0]).name != "gh":
                return real_run(argv, *args, **kwargs)
            if argv[1:3] == ["auth", "status"]:
                return subprocess.CompletedProcess(argv, 0, "", "")
            if argv[-1] == "repos/fixture/repo":
                data = {"allow_squash_merge": True}
                return subprocess.CompletedProcess(argv, 0, json.dumps(data), "")
            if "rulesets?" in argv[-1]:
                return subprocess.CompletedProcess(argv, 0, "[]", "")
            return subprocess.CompletedProcess(argv, 1, "", "HTTP 403 private detail")

        with patch("publication_diagnostics.subprocess.run", side_effect=run), \
                patch("publication_authority._remote_default_branch", return_value="main"), \
                patch("publication_planning._prs", return_value=[]):
            result = diagnostics.doctor(self.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["policy"]["status"], "UNAVAILABLE")
        self.assertTrue(any(item["reason_code"] == "PROTECTION_EVIDENCE_UNAVAILABLE"
                            for item in result["diagnostics"]))
        self.assertNotIn("private detail", str(result))

    def test_aips_cli_routes_doctor_to_non_aips_git_project(self):
        project = self.root / "customer-project"
        project.mkdir()
        subprocess.run(["git", "init", "-b", "main"], cwd=project, check=True,
                       capture_output=True, text=True)
        env = dict(os.environ)
        env["AIPS_VALIDATION_PYTHON"] = sys.executable
        result = subprocess.run([str(ROOT / "bin/aips"), "publish", "doctor", "--project-root",
                                 str(project), "--format", "json"], cwd=ROOT, env=env,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertNotIn("not an AIPS repository", result.stderr)
        self.assertIn("REMOTE_OBSERVATION_FAILED", result.stdout)


if __name__ == "__main__":
    unittest.main()

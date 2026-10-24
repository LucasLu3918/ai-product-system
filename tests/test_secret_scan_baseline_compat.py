from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_secret_leakage as scanner


class SecretScanBaselineCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.policy = {
            "limits": {"max_file_bytes": 2_000_000, "max_json_file_bytes": 8_000_000},
            "allowlist": [],
            "lockfiles": {"path_patterns": [], "disabled_detectors": []},
            "generated_paths": [],
        }

    def scan(self, text: str, path: str = "sample.cs"):
        return scanner.scan_text(text, path, self.policy, strict=True)

    def test_generated_password_expression_is_not_a_literal_secret(self):
        source = (
            "var password = "
            "Convert.ToBase64String(RandomNumberGenerator.GetBytes(32))"
            ".TrimEnd('-', '+');"
        )
        self.assertEqual(self.scan(source), [])

    def test_parameterized_sql_password_expression_is_not_a_literal_secret(self):
        source = """var sql = "WITH PASSWORD='+QUOTENAME(@password,'''')+'";"""
        self.assertEqual(self.scan(source), [])

    def test_high_entropy_password_literal_remains_blocked(self):
        fixture = "Ab9Cd7Ef5Gh3Jk1Lm8Np6Qr4St2Uv0Wx"
        source = f'password = "{fixture}"'
        findings = self.scan(source)
        self.assertEqual([item["detector"] for item in findings], ["generic-secret-assignment"])

    def test_provider_token_and_private_key_detectors_remain_enabled(self):
        source = (
            "token = 'ghp_" + "A" * 40 + "'\n"
            "-----BEGIN " + "PRIVATE KEY-----"
        )
        findings = self.scan(source)
        self.assertEqual(
            [item["detector"] for item in findings],
            ["github-token", "private-key"],
        )

    def test_only_three_exact_generated_webm_paths_are_excluded(self):
        policy, _ = scanner.load_policy(ROOT / "config/secret-scan.yaml")
        expected = {
            "docs/art/candidates/pixel-movement/gate1-runtime-evidence/videos/legacy-movement-and-farming.webm",
            "docs/art/candidates/pixel-movement/gate1-runtime-evidence/videos/pixel16-movement-and-farming.webm",
            "docs/art/candidates/pixel-movement/gate1-runtime-evidence/videos/pixel32-movement-and-farming.webm",
        }
        exact_webm_exceptions = {
            path for path in policy["generated_paths"] if path.endswith(".webm")
        }
        self.assertEqual(exact_webm_exceptions, expected)
        self.assertEqual(policy["limits"]["max_file_bytes"], 2_000_000)
        for path in expected:
            self.assertTrue(scanner.generated_path(path, policy), path)
        for path in (
            "docs/art/candidates/pixel-movement/gate1-runtime-evidence/videos/other.webm",
            "docs/art/candidates/pixel-movement/gate1-runtime-evidence/videos/legacy-movement-and-farming-copy.webm",
            "docs/art/candidates/pixel-movement/gate1-mapscene-ab/legacy-movement-and-farming.webm",
        ):
            self.assertFalse(scanner.generated_path(path, policy), path)

    def test_exact_webm_paths_skip_large_payload_but_other_webm_stays_blocked(self):
        policy, _ = scanner.load_policy(ROOT / "config/secret-scan.yaml")
        exact = "docs/art/candidates/pixel-movement/gate1-runtime-evidence/videos/legacy-movement-and-farming.webm"
        other = "docs/art/candidates/pixel-movement/gate1-runtime-evidence/videos/other.webm"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            exact_path = root / exact
            exact_path.parent.mkdir(parents=True)
            exact_path.write_bytes(b"\x00" * 2_000_001)
            findings, blockers = scanner.scan_worktree(root, policy, strict=True, paths=[])
        self.assertEqual(findings, [])
        self.assertEqual(blockers, [])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            other_path = root / other
            other_path.parent.mkdir(parents=True)
            other_path.write_bytes(b"\x00" * 2_000_001)
            findings, blockers = scanner.scan_worktree(root, policy, strict=True, paths=[])
        self.assertEqual(findings, [])
        self.assertEqual(blockers, [f"candidate file exceeds scan limit: {other}"])

    def test_json_over_text_limit_is_scanned_with_json_limit(self):
        marker = "ghp_" + "A" * 40
        payload = json.dumps({"note": "x" * 2_100_000 + " " + marker})
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "metrics.json").write_text(payload, encoding="utf-8")
            findings, blockers = scanner.scan_worktree(root, self.policy, strict=True, paths=[])
        self.assertEqual(blockers, [])
        self.assertEqual([item["detector"] for item in findings], ["github-token"])

    def test_non_json_over_text_limit_remains_blocked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "metrics.txt").write_text("x" * 2_100_000, encoding="utf-8")
            findings, blockers = scanner.scan_worktree(root, self.policy, strict=True, paths=[])
        self.assertEqual(findings, [])
        self.assertEqual(blockers, ["candidate file exceeds scan limit: metrics.txt"])

    def test_json_over_json_limit_remains_blocked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "metrics.json").write_text(
                '{"note":"' + "x" * 8_000_001 + '"}', encoding="utf-8"
            )
            findings, blockers = scanner.scan_worktree(root, self.policy, strict=True, paths=[])
        self.assertEqual(findings, [])
        self.assertEqual(blockers, ["candidate file exceeds scan limit: metrics.json"])


if __name__ == "__main__":
    unittest.main()

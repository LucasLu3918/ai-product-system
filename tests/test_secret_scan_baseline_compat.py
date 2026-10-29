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

    def test_no_webm_paths_are_excluded(self):
        policy, _ = scanner.load_policy(ROOT / "config/secret-scan.yaml")
        exact_webm_exceptions = {
            path for path in policy["generated_paths"] if path.endswith(".webm")
        }
        self.assertEqual(exact_webm_exceptions, set())
        self.assertEqual(policy["limits"]["max_file_bytes"], 2_000_000)
        self.assertEqual(policy["limits"]["max_webm_file_bytes"], 33_554_432)
        for path in (
            "docs/art/candidates/pixel-movement/gate1-runtime-evidence/videos/legacy-movement-and-farming.webm",
            "docs/art/candidates/pixel-movement/gate1-runtime-evidence/videos/pixel16-movement-and-farming.webm",
            "docs/art/candidates/pixel-movement/gate1-runtime-evidence/videos/pixel32-movement-and-farming.webm",
            "docs/art/candidates/pixel-movement/gate1-runtime-evidence/videos/other.webm",
            "docs/art/candidates/pixel-movement/gate1-runtime-evidence/videos/legacy-movement-and-farming-copy.webm",
            "docs/art/candidates/pixel-movement/gate1-mapscene-ab/legacy-movement-and-farming.webm",
        ):
            self.assertFalse(scanner.generated_path(path, policy), path)

    @staticmethod
    def ebml_element(element_id: bytes, payload: bytes) -> bytes:
        if len(payload) >= 127:
            raise ValueError("test fixture supports only one-byte EBML sizes")
        return element_id + bytes([0x80 | len(payload)]) + payload

    @classmethod
    def minimal_webm(cls, title: bytes = b"safe title") -> bytes:
        header = cls.ebml_element(b"\x1a\x45\xdf\xa3", cls.ebml_element(b"\x42\x82", b"webm"))
        info = cls.ebml_element(b"\x15\x49\xa9\x66", cls.ebml_element(b"\x7b\xa9", title))
        return header + cls.ebml_element(b"\x18\x53\x80\x67", info)

    @classmethod
    def webm_with_segment_children(cls, *elements: bytes) -> bytes:
        header = cls.ebml_element(b"\x1a\x45\xdf\xa3", cls.ebml_element(b"\x42\x82", b"webm"))
        return header + cls.ebml_element(b"\x18\x53\x80\x67", b"".join(elements))

    def test_webm_metadata_is_scanned_and_secret_values_are_redacted(self):
        policy, _ = scanner.load_policy(ROOT / "config/secret-scan.yaml")
        token = "ghp_" + "A" * 40
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            media = root / "evidence.webm"
            media.write_bytes(self.minimal_webm(("token=" + token).encode()))
            findings, blockers = scanner.scan_worktree(root, policy, strict=True, paths=[])
        self.assertEqual([item["detector"] for item in findings], ["github-token"])
        self.assertEqual(findings[0]["path"], "evidence.webm")
        self.assertEqual(blockers, [])

    def test_webm_tag_string_and_unknown_sized_cluster_are_scanned(self):
        policy, _ = scanner.load_policy(ROOT / "config/secret-scan.yaml")
        token = "ghp_" + "B" * 40
        tag_string = self.ebml_element(b"\x44\x87", ("token=" + token).encode())
        simple_tag = self.ebml_element(b"\x67\xc8", tag_string)
        tag = self.ebml_element(b"\x73\x73", simple_tag)
        tags = self.ebml_element(b"\x12\x54\xc3\x67", tag)
        info = self.ebml_element(b"\x15\x49\xa9\x66", self.ebml_element(b"\x7b\xa9", b"safe"))
        # An unknown-sized Cluster ends at the following Segment-level Info element.
        cluster = b"\x1f\x43\xb6\x75\xff" + self.ebml_element(b"\xe7", b"\x00")
        payload = self.webm_with_segment_children(tags + cluster + info)
        findings: list[dict] = []
        blocker = scanner.scan_webm(payload, "nested.webm", policy, findings)
        self.assertIsNone(blocker)
        self.assertEqual([item["detector"] for item in findings], ["github-token"])

    def test_webm_invalid_utf8_metadata_fails_closed(self):
        policy, _ = scanner.load_policy(ROOT / "config/secret-scan.yaml")
        findings: list[dict] = []
        payload = self.minimal_webm(b"\xff")
        blocker = scanner.scan_webm(payload, "invalid-text.webm", policy, findings)
        self.assertIn("invalid or unsupported WebM", blocker or "")
        self.assertEqual(findings, [])

    def test_webm_nul_termination_scans_value_and_ignores_padding(self):
        policy, _ = scanner.load_policy(ROOT / "config/secret-scan.yaml")
        token = "ghp_" + "G" * 40
        findings: list[dict] = []
        blocker = scanner.scan_webm(self.minimal_webm(b"safe title\x00" + b"\xff" * 4), "padded.webm", policy, findings)
        self.assertIsNone(blocker)
        self.assertEqual(findings, [])

        blocker = scanner.scan_webm(self.minimal_webm(("token=" + token).encode() + b"\x00ignored"), "nul.webm", policy, findings)
        self.assertIsNone(blocker)
        self.assertEqual([item["detector"] for item in findings], ["github-token"])

    def test_webm_malformed_metadata_fails_closed(self):
        policy, _ = scanner.load_policy(ROOT / "config/secret-scan.yaml")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "broken.webm").write_bytes(b"\x1a\x45\xdf\xa3\xff")
            findings, blockers = scanner.scan_worktree(root, policy, strict=True, paths=[])
        self.assertEqual(findings, [])
        self.assertEqual(len(blockers), 1)
        self.assertIn("invalid or unsupported WebM", blockers[0])

    def test_webm_over_configured_limit_fails_closed(self):
        policy, _ = scanner.load_policy(ROOT / "config/secret-scan.yaml")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "large.webm").write_bytes(b"x" * (policy["limits"]["max_webm_file_bytes"] + 1))
            findings, blockers = scanner.scan_worktree(root, policy, strict=True, paths=[])
        self.assertEqual(findings, [])
        self.assertEqual(blockers, ["WebM exceeds 32 MiB publication limit: large.webm"])

    def test_policy_rejects_webm_limit_above_parser_hard_cap(self):
        policy = {
            "version": 1,
            "limits": {"max_file_bytes": 2_000_000, "max_webm_file_bytes": 33_554_433},
            "generated_paths": [],
            "lockfiles": {"path_patterns": [], "disabled_detectors": []},
            "allowlist": [],
        }
        with tempfile.TemporaryDirectory() as temporary:
            policy_path = Path(temporary) / "policy.yaml"
            policy_path.write_text(scanner.yaml.safe_dump(policy), encoding="utf-8")
            with self.assertRaises(scanner.ScanError):
                scanner.load_policy(policy_path)

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

from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_secret_leakage
import content_safety
import governance_guard
import publication_authority
import publish_preflight
from creative_image_validation import valid_raster
from media_metadata import MediaInspectionError, extract_metadata, media_diagnostic_code
from safety_diagnostics import diagnose_commit


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xffffffff)


def synchsafe(size: int) -> bytes:
    return bytes(((size >> 21) & 0x7f, (size >> 14) & 0x7f, (size >> 7) & 0x7f, size & 0x7f))


def avif_box(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload) + 8) + kind + payload


def avif_with_exif(value: bytes, *, brand: bytes = b"avif") -> bytes:
    ftyp = avif_box(b"ftyp", brand + b"\x00\x00\x00\x00" + brand + b"mif1")
    infe = avif_box(b"infe", b"\x02\x00\x00\x00" + b"\x00\x01\x00\x00Exif\x00")
    iinf = avif_box(b"iinf", b"\x00\x00\x00\x00\x00\x01" + infe)
    item = b"\x00\x00\x00\x00" + value
    iloc_entry = b"\x00\x01\x00\x01\x00\x00\x00\x01" + struct.pack(">II", 0, len(item))
    iloc = avif_box(b"iloc", b"\x01\x00\x00\x00\x44\x00\x00\x01" + iloc_entry)
    idat = avif_box(b"idat", item)
    return ftyp + avif_box(b"meta", b"\x00\x00\x00\x00" + iinf + iloc + idat) + avif_box(b"mdat", b"AV1 payload")


class SafetyDiagnosticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.run_git("init", "-b", "main")
        self.run_git("config", "user.name", "Fixture")
        self.run_git("config", "user.email", "fixture" + chr(64) + "example.test")
        (self.root / "base.txt").write_text("base\n")
        self.run_git("add", "base.txt")
        self.run_git("commit", "-m", "base")
        self.message_file = Path(self.temp.name) / "message.txt"
        self.message_file.write_text("candidate message\n")

    def run_git(self, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()

    def test_strict_marker_does_not_suppress_staged_secret_and_hook_redacts(self) -> None:
        secret = "ghp_" + "A" * 40
        staged = self.root / "credential.txt"
        staged.write_text("AIPS-SECRET-SCAN-IGNORE-FILE\ntoken=" + secret + "\n")
        self.run_git("add", "credential.txt")
        command = "git commit -m 'candidate message'"
        output = __import__("io").StringIO()
        payload = {"cwd": str(self.root), "tool_input": {"command": command}}
        with patch.dict(os.environ, {"GIT_CONFIG_COUNT": "0"}, clear=False), \
                patch("sys.stdin", __import__("io").StringIO(json.dumps(payload))), \
                patch("sys.stdout", output):
            governance_guard.hook("claude-code")
        rendered = output.getvalue()
        self.assertNotIn(secret, rendered)
        response = json.loads(rendered)
        specific = response["hookSpecificOutput"]
        self.assertEqual(specific["permissionDecision"], "deny")
        self.assertIn("diagnostic_id", specific["additionalContext"])
        self.assertIn("CONTENT_SECRET_BLOCKED", specific["additionalContext"])
        self.assertIn('"file":"credential.txt"', specific["additionalContext"])
        self.assertIn('"line":2', specific["additionalContext"])

    def test_read_only_cli_shares_blocking_scanner_and_does_not_mutate_git(self) -> None:
        secret = "sk_live_" + "B" * 32
        (self.root / "payload.txt").write_text("AIPS-SECRET-SCAN-IGNORE-LINE token=" + secret + "\n")
        self.run_git("add", "payload.txt")
        before_head = self.run_git("rev-parse", "HEAD")
        before_status = self.run_git("status", "--porcelain=v1")
        before_index = hashlib.sha256((self.root / ".git/index").read_bytes()).hexdigest()
        result = diagnose_commit(self.root, self.message_file)
        after_status = self.run_git("status", "--porcelain=v1")
        after_head = self.run_git("rev-parse", "HEAD")
        after_index = hashlib.sha256((self.root / ".git/index").read_bytes()).hexdigest()
        rendered = json.dumps(result, ensure_ascii=False)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertNotIn(secret, rendered)
        self.assertEqual(result["diagnostic"]["reason_code"], "CONTENT_SECRET_BLOCKED")
        self.assertEqual(before_head, after_head)
        self.assertEqual(before_status, after_status)
        self.assertEqual(before_index, after_index)

    def test_unknown_binary_fails_closed_with_stable_classification(self) -> None:
        (self.root / "archive.bin").write_bytes(b"\x00\xffbinary")
        self.run_git("add", "archive.bin")
        result = diagnose_commit(self.root, self.message_file)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["diagnostic"]["reason_code"], "STAGED_CONTENT_UNSUPPORTED_BINARY")
        self.assertNotIn("archive.bin", json.dumps(result))

    def test_malformed_media_message_file_and_scanner_failures_have_stable_reasons(self) -> None:
        (self.root / "broken.png").write_bytes(b"not a PNG")
        self.run_git("add", "broken.png")
        malformed = diagnose_commit(self.root, self.message_file)
        self.assertEqual(malformed["diagnostic"]["reason_code"], "STAGED_MEDIA_INVALID")

        self.run_git("reset", "--quiet", "broken.png")
        unavailable_message = diagnose_commit(self.root, Path(self.temp.name) / "missing-message.txt")
        self.assertEqual(unavailable_message["diagnostic"]["reason_code"], "MESSAGE_FILE_UNAVAILABLE")

        with patch("governance_guard.safe_emit", side_effect=RuntimeError("private scanner details")):
            scanner_failure = diagnose_commit(self.root, self.message_file)
        rendered = json.dumps(scanner_failure, ensure_ascii=False)
        self.assertEqual(scanner_failure["diagnostic"]["reason_code"], "CONTENT_SCANNER_FAILED")
        self.assertNotIn("private scanner details", rendered)

    def test_ordinary_staged_javascript_is_allowed_by_native_diagnostic(self) -> None:
        source = "const state = { run: data };\nrun.endingId = data.endingId;\n"
        (self.root / "runtime.mjs").write_text(source, encoding="utf-8")
        self.run_git("add", "runtime.mjs")
        result = diagnose_commit(self.root, self.message_file)
        self.assertEqual(result["decision"], "ALLOW", result)

    def test_unchanged_injection_context_does_not_block_unrelated_staged_line(self) -> None:
        fixture_path = ROOT / "tests/fixtures/content-safety/corpus.json"
        corpus = json.loads(fixture_path.read_text(encoding="utf-8"))
        prior_text = bytes.fromhex(corpus["malicious_hex"][0]).decode("utf-8")
        path = self.root / "runtime.mjs"
        path.write_text(prior_text + "\nconst version = 1;\n", encoding="utf-8")
        self.run_git("add", "runtime.mjs")
        self.run_git("commit", "-m", "baseline")
        path.write_text(prior_text + "\nconst version = 2;\n", encoding="utf-8")
        self.run_git("add", "runtime.mjs")
        result = diagnose_commit(self.root, self.message_file)
        self.assertEqual(result["decision"], "ALLOW", result)

    def test_full_staged_blob_keeps_secret_scan_and_diagnostic_is_actionable(self) -> None:
        marker = "synthetic-secret-canary"
        path = self.root / "payload.txt"
        path.write_text("token=" + marker + "\nversion=1\n", encoding="utf-8")
        self.run_git("add", "payload.txt")
        self.run_git("commit", "-m", "baseline")
        path.write_text("token=" + marker + "\nversion=2\n", encoding="utf-8")
        self.run_git("add", "payload.txt")

        def synthetic_secret_scan(text: str, location: str, *, strict: bool = False) -> list[dict[str, object]]:
            del location, strict
            if marker not in text:
                return []
            return [{"detector": "synthetic-secret", "fingerprint": "test-fingerprint",
                     "secret_length": len(marker), "line": 1}]

        with patch("content_safety.scan_text", side_effect=synthetic_secret_scan):
            result = diagnose_commit(self.root, self.message_file)
        diagnostic = result["diagnostic"]
        self.assertEqual(diagnostic["reason_code"], "CONTENT_SECRET_BLOCKED")
        self.assertEqual(diagnostic["findings"][0]["file"], "payload.txt")
        self.assertIn("finding_fingerprint", diagnostic["findings"][0])
        self.assertNotIn(marker, json.dumps(result))

    def test_ambiguous_signal_returns_review_reason_and_safe_fingerprint(self) -> None:
        corpus = json.loads((ROOT / "tests/fixtures/content-safety/corpus.json").read_text(encoding="utf-8"))
        source = bytes.fromhex(corpus["ambiguous_hex"]).decode("utf-8")
        (self.root / "notes.txt").write_text(source + "\n", encoding="utf-8")
        self.run_git("add", "notes.txt")
        result = diagnose_commit(self.root, self.message_file)
        diagnostic = result["diagnostic"]
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(diagnostic["reason_code"], "CONTENT_REVIEW_REQUIRED")
        self.assertEqual(diagnostic["findings"][0]["rule_id"], "injection.ambiguous.v2")
        self.assertEqual(diagnostic["findings"][0]["file"], "notes.txt")
        self.assertIn("finding_fingerprint", diagnostic["findings"][0])
        self.assertTrue(diagnostic["recovery"]["human_approval_required"])
        self.assertEqual(diagnostic["recovery"]["blocking_phase"], "content_scan")
        self.assertFalse(diagnostic["recovery"]["matched_content_included"])
        self.assertTrue(diagnostic["recovery"]["next_steps"])
        self.assertNotIn(source, json.dumps(result))

    def test_strong_injection_is_still_blocked_with_rule_identity(self) -> None:
        corpus = json.loads((ROOT / "tests/fixtures/content-safety/corpus.json").read_text(encoding="utf-8"))
        source = bytes.fromhex(corpus["malicious_hex"][0]).decode("utf-8")
        (self.root / "notes.txt").write_text(source + "\n", encoding="utf-8")
        self.run_git("add", "notes.txt")
        result = diagnose_commit(self.root, self.message_file)
        finding = result["diagnostic"]["findings"][0]
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(finding["reason_code"], "CONTENT_INJECTION_BLOCKED")
        self.assertIn(finding["rule_id"], {"injection.override.v2", "injection.exfiltration.v2"})
        self.assertTrue(finding["finding_fingerprint"].startswith("sha256:"))
        self.assertNotIn(source, json.dumps(result))

    def test_exact_exception_allows_only_approved_injection_finding(self) -> None:
        corpus = json.loads((ROOT / "tests/fixtures/content-safety/corpus.json").read_text(encoding="utf-8"))
        source = bytes.fromhex(corpus["ambiguous_hex"]).decode("utf-8")
        context = {"source_path": "notes.txt"}
        finding = next(item for item in content_safety.scan_payload(source, sink="git_commit", context=context)
                       if item.rule_id == "injection.ambiguous.v2")
        (self.root / "notes.txt").write_text(source + "\n", encoding="utf-8")
        self.run_git("add", "notes.txt")
        exception_file = Path(self.temp.name) / "exceptions.yaml"
        exception_file.write_text(
            "version: 1\nexceptions:\n"
            "  - rule_id: injection.ambiguous.v2\n"
            "    path: notes.txt\n"
            f"    finding_fingerprint: {finding.finding_fingerprint}\n"
            "    sink: git_commit\n"
            "    expires_on: '2099-01-01'\n"
            "    approved_by: reviewer\n"
            "    approval_reference: PR-123\n",
            encoding="utf-8",
        )
        with patch.object(content_safety, "DEFAULT_EXCEPTIONS", exception_file):
            result = diagnose_commit(self.root, self.message_file)
        self.assertEqual(result["decision"], "ALLOW", result)

    def test_expired_exception_returns_specific_recovery_reason(self) -> None:
        (self.root / "notes.txt").write_text("ordinary content\n", encoding="utf-8")
        self.run_git("add", "notes.txt")
        exception_file = Path(self.temp.name) / "exceptions.yaml"
        exception_file.write_text(
            "version: 1\nexceptions:\n"
            "  - rule_id: injection.ambiguous.v2\n"
            "    path: notes.txt\n"
            "    finding_fingerprint: sha256:" + "0" * 64 + "\n"
            "    sink: git_commit\n"
            "    expires_on: '2000-01-01'\n"
            "    approved_by: reviewer\n"
            "    approval_reference: PR-123\n",
            encoding="utf-8",
        )
        with patch.object(content_safety, "DEFAULT_EXCEPTIONS", exception_file):
            result = diagnose_commit(self.root, self.message_file)
        diagnostic = result["diagnostic"]
        self.assertEqual(diagnostic["reason_code"], "CONTENT_EXCEPTION_EXPIRED")
        self.assertEqual(diagnostic["phase"], "commit_message")
        self.assertIn("過期", diagnostic["next_step_zh"] + diagnostic["detail_zh"])
        self.assertNotIn("2000-01-01", json.dumps(result))

    def test_metadata_extractors_validate_format_boundaries(self) -> None:
        png_text = b"Comment\x00api_key=" + b"A" * 32
        ihdr = b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
        png = (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr)
               + png_chunk(b"tEXt", png_text) + png_chunk(b"IEND", b""))
        self.assertIn("api_key=", extract_metadata(png, ".png"))

        email = "owner" + chr(64) + "example.test"
        xmp = b"http://ns.adobe.com/xap/1.0/\x00" + email.encode()
        jpeg_segment = b"\xff\xe1" + struct.pack(">H", len(xmp) + 2) + xmp
        sof = b"\xff\xc0" + struct.pack(">H", 11) + b"\x08\x00\x01\x00\x01\x01\x01\x11\x00"
        sos = b"\xff\xda" + struct.pack(">H", 8) + b"\x01\x01\x00\x00\x3f\x00"
        self.assertIn(email, extract_metadata(b"\xff\xd8" + jpeg_segment + sof + sos + b"\x00\xff\xd9", ".jpg"))

        exif = email.encode()
        webp_chunk = b"EXIF" + struct.pack("<I", len(exif)) + exif
        if len(exif) & 1:
            webp_chunk += b"\x00"
        image = b"\x2f\x00\x00\x00\x00"
        webp_chunk += b"VP8L" + struct.pack("<I", len(image)) + image
        if len(image) & 1:
            webp_chunk += b"\x00"
        webp_body = b"WEBP" + webp_chunk
        webp = b"RIFF" + struct.pack("<I", len(webp_body)) + webp_body
        self.assertIn(email, extract_metadata(webp, ".webp"))

        frame_data = b"\x03" + email.encode()
        frame = b"TIT2" + synchsafe(len(frame_data)) + b"\x00\x00" + frame_data
        mp3_tag = b"ID3\x04\x00\x00" + synchsafe(len(frame)) + frame
        self.assertIn(email, extract_metadata(mp3_tag + b"\xff\xfb\x90\x64" + b"audio", ".mp3"))
        self.assertEqual(extract_metadata(b"\xff\xfb\x90\x64audio", ".mp3"), "")
        with self.assertRaises(MediaInspectionError):
            extract_metadata(b"not png", ".png")

    def test_avif_metadata_is_extracted_and_animation_is_rejected(self) -> None:
        email = "owner" + chr(64) + "example.test"
        payload = avif_with_exif(email.encode())
        self.assertIn(email, extract_metadata(payload, ".avif"))
        self.assertIn(email, extract_metadata(payload, ".AVIF"))
        with self.assertRaises(MediaInspectionError):
            extract_metadata(avif_with_exif(email.encode(), brand=b"avis"), ".avif")
        with self.assertRaises(MediaInspectionError):
            extract_metadata(payload + b"trailing", ".avif")
        with self.assertRaises(MediaInspectionError):
            extract_metadata(payload[:20], ".avif")
        wrong_extent = bytearray(payload)
        iloc_at = wrong_extent.index(b"iloc")
        wrong_extent[iloc_at + 14:iloc_at + 16] = b"\x00\x00"
        with self.assertRaises(MediaInspectionError):
            extract_metadata(bytes(wrong_extent), ".avif")
        with self.assertRaises(MediaInspectionError):
            extract_metadata(avif_with_exif(b"x" * (1024 * 1024 + 1)), ".avif")

    def test_avif_failures_have_stable_actionable_diagnostic_categories(self) -> None:
        cases = (
            (avif_box(b"free", b"x"), "STAGED_MEDIA_SIGNATURE_MISMATCH"),
            (avif_with_exif(b"x", brand=b"avis"), "STAGED_MEDIA_UNSUPPORTED_FEATURE"),
            (avif_with_exif(b"x" * (1024 * 1024 + 1)), "STAGED_MEDIA_RESOURCE_LIMIT"),
        )
        for payload, expected in cases:
            with self.subTest(expected=expected), self.assertRaises(MediaInspectionError) as caught:
                extract_metadata(payload, ".avif")
            self.assertEqual(media_diagnostic_code(caught.exception), expected)

        for code in {expected for _payload, expected in cases}:
            diagnostic = publication_authority.PublicationError("private parser detail", code).diagnostic()
            self.assertEqual(diagnostic["reason_code"], code)
            self.assertTrue(diagnostic["next_step_zh"])
            self.assertNotIn("private parser detail", json.dumps(diagnostic))

    def test_staged_avif_secret_is_blocked_without_echoing_value(self) -> None:
        token = "ghp_" + "C" * 40
        (self.root / "metadata.avif").write_bytes(avif_with_exif(("token=" + token).encode()))
        self.run_git("add", "metadata.avif")
        result = diagnose_commit(self.root, self.message_file)
        rendered = json.dumps(result)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["diagnostic"]["reason_code"], "CONTENT_SECRET_BLOCKED")
        self.assertNotIn(token, rendered)

    def test_avif_candidate_history_and_creative_validation_use_shared_registry(self) -> None:
        token = "ghp_" + "D" * 40
        payload = avif_with_exif(("token=" + token).encode())
        image = self.root / "metadata.avif"
        image.write_bytes(payload)
        self.assertTrue(valid_raster(image))
        base = self.run_git("rev-parse", "HEAD")
        self.run_git("add", "metadata.avif")
        self.run_git("commit", "-m", "add AVIF")
        policy, _policy_hash = check_secret_leakage.load_policy(check_secret_leakage.DEFAULT_POLICY)
        findings, blockers, _base_sha, _head_sha = check_secret_leakage.scan_candidate(self.root, base, "HEAD", policy)
        rendered = json.dumps({"findings": findings, "blockers": blockers})
        self.assertTrue(any(item["detector"] == "github-token" for item in findings))
        self.assertNotIn(token, rendered)
        self.assertFalse(valid_raster(self.root / "missing.avif"))

    def test_publication_preview_scans_avif_metadata_and_blocks_malformed_container(self) -> None:
        token = "ghp_" + "E" * 40
        image = self.root / "preview.avif"
        image.write_bytes(avif_with_exif(("token=" + token).encode()))
        base = self.run_git("rev-parse", "HEAD")
        with patch.object(publish_preflight, "ROOT", self.root):
            secret_result = publish_preflight.preview_content_safety(base, ["preview.avif"])
            self.assertEqual(secret_result["status"], "BLOCKED")
            self.assertNotIn(token, json.dumps(secret_result))
            image.write_bytes(b"not an AVIF")
            malformed_result = publish_preflight.preview_content_safety(base, ["preview.avif"])
        self.assertEqual(malformed_result["status"], "BLOCKED")
        self.assertTrue(any("STAGED_MEDIA_INVALID" in item for item in malformed_result["blockers"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)

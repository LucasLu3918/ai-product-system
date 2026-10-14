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

import governance_guard
from media_metadata import MediaInspectionError, extract_metadata
from safety_diagnostics import diagnose_commit


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xffffffff)


def synchsafe(size: int) -> bytes:
    return bytes(((size >> 21) & 0x7f, (size >> 14) & 0x7f, (size >> 7) & 0x7f, size & 0x7f))


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


if __name__ == "__main__":
    unittest.main(verbosity=2)

from __future__ import annotations

import builtins
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_secret_leakage as secret_scanner
import publish_preflight
from media_metadata import MediaInspectionError, extract_metadata
from safety_diagnostics import diagnose_commit


def make_font(is_ttf: bool, flavor: str | None = None, family: str = "AIPS Test Font") -> bytes:
    builder = FontBuilder(1000, isTTF=is_ttf)
    glyphs = [".notdef", "A"]
    builder.setupGlyphOrder(glyphs); builder.setupCharacterMap({65: "A"})
    builder.setupHorizontalMetrics({".notdef": (500, 0), "A": (600, 0)})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({"familyName": family, "styleName": "Regular", "uniqueFontIdentifier": "AIPS-Test",
                            "fullName": family, "psName": "AIPS-Test", "version": "Version 1.0"})
    builder.setupOS2(); builder.setupPost(); builder.setupMaxp()
    if is_ttf:
        outlines = {}
        for name in glyphs:
            pen = TTGlyphPen(None)
            if name == "A":
                pen.moveTo((0, 0)); pen.lineTo((300, 700)); pen.lineTo((600, 0)); pen.closePath()
            outlines[name] = pen.glyph()
        builder.setupGlyf(outlines)
    else:
        outlines = {}
        for name in glyphs:
            pen = T2CharStringPen(600, None)
            if name == "A":
                pen.moveTo((0, 0)); pen.lineTo((300, 700)); pen.lineTo((600, 0)); pen.closePath()
            outlines[name] = pen.getCharString()
        builder.setupCFF("AIPSTestFont-Regular", {}, outlines, {})
    if flavor:
        builder.font.flavor = flavor
    output = BytesIO(); builder.font.save(output)
    return output.getvalue()


class FontMetadataTests(unittest.TestCase):
    def test_all_supported_formats_extract_names(self) -> None:
        for is_ttf, flavor, suffix in ((True, None, ".ttf"), (False, None, ".otf"),
                                       (True, "woff", ".woff"), (True, "woff2", ".woff2")):
            with self.subTest(suffix=suffix):
                self.assertIn("AIPS Test Font", extract_metadata(make_font(is_ttf, flavor), suffix))

    def test_spoofed_and_corrupt_fonts_fail_with_stable_reason(self) -> None:
        with self.assertRaises(MediaInspectionError) as spoofed:
            extract_metadata(make_font(True), ".woff2")
        self.assertEqual(str(spoofed.exception), "STAGED_FONT_FORMAT_MISMATCH")
        with self.assertRaises(MediaInspectionError) as corrupt:
            extract_metadata(b"\x00\x01\x00\x00broken", ".ttf")
        self.assertEqual(str(corrupt.exception), "STAGED_FONT_INVALID")

    def test_missing_parser_dependencies_and_decompression_limit_fail_closed(self) -> None:
        ttf = make_font(True)
        woff2 = make_font(True, "woff2")
        original_import = builtins.__import__
        def without_fonttools(name, *args, **kwargs):
            if name == "fontTools.ttLib":
                raise ImportError("fixture")
            return original_import(name, *args, **kwargs)
        with (patch("builtins.__import__", side_effect=without_fonttools),
              self.assertRaises(MediaInspectionError) as missing_fonttools):
            extract_metadata(ttf, ".ttf")
        self.assertEqual(str(missing_fonttools.exception), "STAGED_FONT_INSPECTOR_UNAVAILABLE")

        original_import = builtins.__import__
        def without_brotli(name, *args, **kwargs):
            if name == "brotli":
                raise ImportError("fixture")
            return original_import(name, *args, **kwargs)
        with (patch("builtins.__import__", side_effect=without_brotli),
              self.assertRaises(MediaInspectionError) as missing_brotli):
                extract_metadata(woff2, ".woff2")
        self.assertEqual(str(missing_brotli.exception), "STAGED_FONT_BROTLI_UNAVAILABLE")

        oversized = bytearray(woff2)
        oversized[16:20] = (32 * 1024 * 1024 + 1).to_bytes(4, "big")
        with self.assertRaises(MediaInspectionError) as resource_limit:
            extract_metadata(bytes(oversized), ".woff2")
        self.assertEqual(str(resource_limit.exception), "STAGED_FONT_RESOURCE_LIMIT")

    def test_staged_sensitive_font_name_is_redacted_and_scan_is_read_only(self) -> None:
        secret = "ghp_" + "A" * 40
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"; root.mkdir()
            def git(*args: str) -> str:
                return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
            git("init", "-b", "main"); git("config", "user.name", "Fixture"); git("config", "user.email", "fixture" + chr(64) + "example.test")
            (root / "base.txt").write_text("base\n"); git("add", "base.txt"); git("commit", "-m", "base")
            (root / "private.ttf").write_bytes(make_font(True, family="Identity " + secret)); git("add", "private.ttf")
            message = Path(temp) / "message.txt"; message.write_text("candidate\n")
            head_before = git("rev-parse", "HEAD")
            index_before = hashlib.sha256((root / ".git/index").read_bytes()).hexdigest()
            result = diagnose_commit(root, message)
            rendered = json.dumps(result)
            self.assertEqual(result["decision"], "BLOCK")
            self.assertEqual(result["diagnostic"]["reason_code"], "CONTENT_SECRET_BLOCKED")
            self.assertNotIn(secret, rendered); self.assertIn("private.ttf", rendered)
            self.assertEqual(head_before, git("rev-parse", "HEAD"))
            self.assertEqual(index_before, hashlib.sha256((root / ".git/index").read_bytes()).hexdigest())
            policy, _ = secret_scanner.load_policy(secret_scanner.DEFAULT_POLICY)
            findings, blockers = secret_scanner.scan_worktree(root.resolve(), policy, strict=True, paths=["private.ttf"])
            self.assertTrue(any(item["path"] == "private.ttf" for item in findings), findings)
            self.assertEqual(blockers, [])
            with patch.object(publish_preflight, "ROOT", root):
                preview = publish_preflight.preview_content_safety(head_before, ["private.ttf"])
            self.assertEqual(preview["status"], "BLOCKED")
            self.assertNotIn(secret, json.dumps(preview))
            git("commit", "-m", "font scanner fixture")
            head_after = git("rev-parse", "HEAD")
            history_findings, history_blockers, _, _ = secret_scanner.scan_candidate(root, head_before, head_after, policy)
            self.assertTrue(any(item["path"] == "private.ttf" for item in history_findings), history_findings)
            self.assertEqual(history_blockers, [])

    def test_malformed_font_diagnostic_identifies_safe_path_format_phase_and_cause(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"; root.mkdir()
            def git(*args: str) -> str:
                return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
            git("init", "-b", "main"); git("config", "user.name", "Fixture"); git("config", "user.email", "fixture" + chr(64) + "example.test")
            (root / "base.txt").write_text("base\n"); git("add", "base.txt"); git("commit", "-m", "base")
            (root / "broken.ttf").write_bytes(b"\x00\x01\x00\x00broken"); git("add", "broken.ttf")
            message = Path(temp) / "message.txt"; message.write_text("candidate\n")
            result = diagnose_commit(root, message)
            diagnostic = result["diagnostic"]
            self.assertEqual(diagnostic["reason_code"], "STAGED_FONT_INVALID")
            self.assertEqual(diagnostic["phase"], "font_metadata")
            self.assertEqual(diagnostic["file"], "broken.ttf")
            self.assertEqual(diagnostic["format"], "TrueType")
            self.assertRegex(diagnostic["error_class"], r"^[A-Za-z][A-Za-z0-9_.]{0,79}$")
            self.assertNotIn("/private/", json.dumps(result))


if __name__ == "__main__":
    unittest.main(verbosity=2)

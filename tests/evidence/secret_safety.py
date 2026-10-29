#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SCANNER = ROOT / "scripts" / "check_secret_leakage.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def ebml_element(element_id: bytes, payload: bytes) -> bytes:
    if len(payload) >= 127:
        raise ValueError("test fixture supports only one-byte EBML sizes")
    return element_id + bytes([0x80 | len(payload)]) + payload


def webm_with_title(title: bytes) -> bytes:
    header = ebml_element(b"\x1a\x45\xdf\xa3", ebml_element(b"\x42\x82", b"webm"))
    info = ebml_element(b"\x15\x49\xa9\x66", ebml_element(b"\x7b\xa9", title))
    return header + ebml_element(b"\x18\x53\x80\x67", info)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        secret_file = root / "config.txt"
        fake_token = "ghp_" + ("A" * 40)
        secret_file.write_text("TOKEN=" + fake_token + "\n", encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(SCANNER), "--root", str(root), "--json"],
            capture_output=True,
            text=True,
        )
        require(result.returncode != 0, "high-confidence credential must be detected")
        require(fake_token not in result.stdout, "scanner stdout exposed secret value")
        require(fake_token not in result.stderr, "scanner stderr exposed secret value")

        doc = json.loads(result.stdout)
        findings = doc.get("findings") or []
        require(bool(findings), "scanner emitted no finding metadata")
        finding = findings[0]
        require(finding.get("detector") == "github-token", "unexpected detector")
        require("path" in finding, "finding path missing")
        require("line" in finding, "finding line missing")
        require("fingerprint" in finding, "finding fingerprint missing")
        require("value" not in finding, "finding must not contain secret value")

        media_token = "ghp_" + ("B" * 40)
        media = root / "evidence.webm"
        media.write_bytes(webm_with_title(("token=" + media_token).encode("utf-8")))
        media_result = subprocess.run(
            [sys.executable, str(SCANNER), "--root", str(root), "--strict", "--path", "evidence.webm", "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
        require(media_result.returncode != 0, "WebM metadata token must be detected")
        require(media_token not in media_result.stdout and media_token not in media_result.stderr,
                "WebM scan output exposed secret value")
        media_doc = json.loads(media_result.stdout)
        require(any(item.get("path") == "evidence.webm" and item.get("detector") == "github-token"
                    for item in media_doc.get("findings", [])), "WebM metadata finding was not reported")

        media.write_bytes(b"\x1a\x45\xdf\xa3\xff")
        malformed_result = subprocess.run(
            [sys.executable, str(SCANNER), "--root", str(root), "--strict", "--path", "evidence.webm", "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
        require(malformed_result.returncode != 0, "malformed WebM must fail closed")
        malformed_doc = json.loads(malformed_result.stdout)
        require(any("invalid or unsupported WebM" in item for item in malformed_doc.get("blockers", [])),
                "malformed WebM blocker was not reported")

    print("secret_safety evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

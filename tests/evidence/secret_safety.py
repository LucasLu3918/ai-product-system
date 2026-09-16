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

    print("secret_safety evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

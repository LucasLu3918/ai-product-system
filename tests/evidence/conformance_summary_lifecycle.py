#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/conformance_summary.py"


def main() -> int:
    for view, output in (
        ("current", ROOT / "docs/human/CONFORMANCE_CURRENT.md"),
        ("history", ROOT / "docs/human/CONFORMANCE_HISTORY_INDEX.md"),
    ):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), view, "--check", str(output)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
    current = (ROOT / "docs/human/CONFORMANCE_CURRENT.md").read_text(encoding="utf-8")
    assert "deterministic + lifecycle + agent_eval" in current
    assert "not a quality score" in current
    history = (ROOT / "docs/human/CONFORMANCE_HISTORY_INDEX.md").read_text(encoding="utf-8")
    assert "Historical record" in history and "Normative rule" in history
    assert "github.com/LucasLu3918/ai-product-system/blob/main/orchestration/CONFORMANCE.md#" in history
    print("CONFORMANCE SUMMARY LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

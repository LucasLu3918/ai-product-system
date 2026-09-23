#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    result = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "tests.test_temporal_intelligence", "-v"],
        cwd=ROOT,
        text=True,
    )
    if result.returncode == 0:
        print("temporal_intelligence_lifecycle evidence: PASS")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

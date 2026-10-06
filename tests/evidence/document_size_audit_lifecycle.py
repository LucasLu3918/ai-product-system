"""Verify oversized tracked documentation remains a non-blocking warning."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/document_size_audit.py"


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary) / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "docs/human").mkdir(parents=True)
    (root / "tests/evidence").mkdir(parents=True)
    (root / "docs/human/large.md").write_bytes(b"x" * 50001)
    (root / "tests/evidence/boundary.py").write_bytes(b"x" * 50000)
    (root / "outside.md").write_bytes(b"x" * 90000)
    git(root, "add", "docs/human/large.md", "tests/evidence/boundary.py", "outside.md")
    policy = root / "policy.yaml"
    policy.write_text(
        "version: 1\nhot_document_max_bytes: 50000\nscan_roots: [docs/human, tests/evidence]\n"
        "extensions: [.md, .py]\nthreshold_behavior: WARN\ngate_blocking: false\narchive_or_move: false\n",
        encoding="utf-8",
    )
    before = {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--policy", str(policy)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    report = json.loads(result.stdout)
    assert result.returncode == 0 and report["status"] == "WARN"
    assert report["gate_blocking"] is False and report["archive_or_move"] is False
    assert report["oversized_count"] == 1 and report["files_scanned"] == 2
    assert {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()} == before
print("document size audit lifecycle: PASS")

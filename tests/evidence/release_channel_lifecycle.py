#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import release_channel


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True).stdout.strip()


def main() -> int:
    import coverage

    measured = coverage.Coverage(data_file=None, branch=True, source=["release_channel"])
    measured.start()
    annotated = """aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\trefs/tags/v0.9.0\n1111111111111111111111111111111111111111\trefs/tags/v0.9.0^{}\nbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\trefs/tags/v0.10.0\ncccccccccccccccccccccccccccccccccccccccc\trefs/tags/v0.10.0^{}\ndddddddddddddddddddddddddddddddddddddddd\trefs/tags/v0.10.0-rc1\n"""
    versions = release_channel.parse_remote_tags(annotated)
    assert [item["tag"] for item in versions] == ["v0.9.0", "v0.10.0"]
    assert versions[-1]["commit_sha"] == "c" * 40
    assert release_channel.parse_remote_tags("refs without versions") == []

    with tempfile.TemporaryDirectory(prefix="aips-release-channel-") as tmp:
        repo = Path(tmp)
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "aips" + chr(64) + "example.invalid")
        git(repo, "config", "user.name", "AIPS Test")
        (repo / "VERSION").write_text("0.10.0\n", encoding="utf-8")
        git(repo, "add", "VERSION")
        git(repo, "commit", "-qm", "release fixture")
        git(repo, "tag", "v0.10.0")
        head = git(repo, "rev-parse", "HEAD")
        assert release_channel.verify_tag(repo, "v0.10.0", head)["commit_sha"] == head
        try:
            release_channel.verify_tag(repo, "v0.9.0", head)
        except release_channel.ReleaseChannelError:
            pass
        else:
            raise AssertionError("tag/version mismatch must fail closed")
    property_check = subprocess.run(
        [sys.executable, str(ROOT / "tests/evidence/release_channel_properties.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert property_check.returncode == 0, property_check.stdout + property_check.stderr
    measured.stop()
    measured.report(file=sys.stdout, include=["*/scripts/release_channel.py"])
    print("RELEASE CHANNEL LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

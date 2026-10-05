#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import release_channel


def git(root: Path, *args: str, check: bool = True) -> str:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=check).stdout.strip()


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
    with tempfile.TemporaryDirectory(prefix="aips-source-checkout-") as tmp:
        base = Path(tmp)
        source = base / "source"
        source.mkdir()
        git(source, "init", "-q", "-b", "main")
        git(source, "config", "user.email", "aips" + chr(64) + "example.invalid")
        git(source, "config", "user.name", "AIPS Test")
        (source / "VERSION").write_text("0.0.0\n", encoding="utf-8")
        (source / "bin").mkdir()
        (source / "bin/aips").write_text("#!/usr/bin/env bash\nprintf 'candidate installed\n'\n", encoding="utf-8")
        (source / "bin/aips").chmod(0o755)
        (source / "scripts").mkdir()
        (source / "scripts/release_channel.py").write_bytes((ROOT / "scripts/release_channel.py").read_bytes())
        git(source, "add", ".")
        git(source, "commit", "-qm", "source-checkout fixture")
        source_head = git(source, "rev-parse", "HEAD")
        git(source, "checkout", "--quiet", "--detach", "HEAD")
        git(source, "update-ref", "-d", "refs/heads/main")
        install_dir = base / "install"
        env = dict(__import__("os").environ)
        env.update({
            "AIPS_INSTALL_SOURCE": str(source),
            "AIPS_REPO_URL": str(source),
            "AIPS_INSTALL_DIR": str(install_dir),
            "HOME": str(base / "home"),
        })
        (base / "home").mkdir()
        result = subprocess.run(["bash", str(ROOT / "scripts/install.sh")], env=env, text=True, capture_output=True, check=False)
        assert result.returncode != 0, "stable install must fail when no verified release tag exists"
        assert "no stable AIPS release tag exists yet" in result.stderr
        assert "--channel main" in result.stderr
        assert not install_dir.exists(), "failed stable bootstrap must remove its newly cloned checkout"
        result = subprocess.run(["bash", str(ROOT / "scripts/install.sh"), "--channel", "main"], env=env, text=True, capture_output=True, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        assert git(install_dir, "rev-parse", "HEAD") == source_head
        assert git(install_dir, "remote", "get-url", "origin") == str(source)
        channel_path = Path(git(install_dir, "rev-parse", "--path-format=absolute", "--git-path", "aips-channel"))
        assert channel_path.read_text(encoding="utf-8").strip() == "main"
        git(source, "tag", "v0.0.0")
        stable_env = dict(env)
        stable_env["AIPS_INSTALL_DIR"] = str(base / "stable-install")
        stable_result = subprocess.run(["bash", str(ROOT / "scripts/install.sh")], env=stable_env, text=True, capture_output=True, check=False)
        assert stable_result.returncode == 0, stable_result.stdout + stable_result.stderr
        stable_install = Path(stable_env["AIPS_INSTALL_DIR"])
        assert git(stable_install, "rev-parse", "HEAD") == source_head
        stable_channel_path = Path(git(stable_install, "rev-parse", "--path-format=absolute", "--git-path", "aips-channel"))
        assert stable_channel_path.read_text(encoding="utf-8").strip() == "stable"
        assert git(stable_install, "symbolic-ref", "-q", "HEAD", check=False) == "", "stable installation must be detached at the verified tag"

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

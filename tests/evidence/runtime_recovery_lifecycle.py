#!/usr/bin/env python3
"""Exercise permission, download, installed-sync and linked-worktree recovery."""
from __future__ import annotations

from argparse import Namespace
import json
import os
from pathlib import Path
import subprocess
import shlex
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import runtime_cache as cache
import package_install as packages
import publish_preflight as publish


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="aips recovery ") as tmp:
        base = Path(tmp)
        fallback = base / "private cache"
        env = {"HOME": str(base / "home"), "GH_CONFIG_DIR": str(base / "gh-config")}
        with patch.object(cache, "fallback_home", return_value=fallback), patch.object(cache, "writable", return_value=False):
            assert cache.cache_home(env, for_write=False) == base / "home/.cache"
            resolved = cache.cache_environment(env)
            assert Path(resolved["XDG_CACHE_HOME"]) == fallback
            assert resolved["GH_CONFIG_DIR"] == env["GH_CONFIG_DIR"]
            assert cache.cache_home(env) == fallback
            assert fallback.stat().st_mode & 0o077 == 0
            explicit = {**env, "XDG_CACHE_HOME": str(base / "explicit inaccessible")}
            assert cache.cache_environment(explicit)["XDG_CACHE_HOME"] == explicit["XDG_CACHE_HOME"]
            fallback.rmdir()
            fallback.symlink_to(base)
            try:
                cache.cache_home(env, for_write=True)
            except PermissionError:
                pass
            else:
                raise AssertionError("a symlink must not receive cache data")
            fallback.unlink()

        python = base / "fake python"
        requirements = base / "requirements.txt"
        requirements.write_text("pinned-fixture==1\n")
        python.write_text(f'#!/bin/sh\necho "HTTP 403 https://user{chr(58)}secret{chr(64)}example.invalid/simple" >&2\nexit 1\n')
        python.chmod(0o755)
        result = packages.install(str(python), requirements)
        assert result["reason_code"] == "HTTP_FORBIDDEN" and "secret" not in json.dumps(result)
        assert packages.failure_category("ProxyError") == "PROXY_ERROR"
        assert packages.failure_category("temporary failure in name resolution") == "DNS_UNAVAILABLE"
        assert packages.failure_category("CERTIFICATE_VERIFY_FAILED") == "TLS_ERROR"
        python.write_text('#!/bin/sh\nexit 0\n')
        assert packages.install(str(python), requirements)["status"] == "PASS"

        project = base / "validation project"
        (project / "scripts").mkdir(parents=True)
        (project / ".venv/bin").mkdir(parents=True)
        complete = project / ".venv/bin/python"
        complete.write_text(f'#!/bin/sh\nexec {shlex.quote(sys.executable)} "$@"\n')
        complete.chmod(0o755)
        partial = base / "partial python"
        partial.write_text('#!/bin/sh\nif [ "$1" = -c ] && [ "$2" = "import yaml" ]; then exit 0; fi\nexit 1\n')
        partial.chmod(0o755)
        (project / "scripts/publish_preflight.py").write_text('print("complete environment selected")\n')
        isolated_env = {**os.environ, "AIPS_VALIDATION_PYTHON": str(partial)}
        isolated_env.pop("AIPS_VALIDATION_VENV", None)
        routed = subprocess.run(["bash", str(ROOT / "bin/aips"), "publish", "plan", "--project-root", str(project)],
                                env=isolated_env, capture_output=True, text=True)
        assert routed.returncode == 0 and "complete environment selected" in routed.stdout, routed.stderr
        assert f"python={complete.parent.resolve() / complete.name}" in routed.stderr, routed.stderr

        source = base / "source"
        source.mkdir()
        git(source, "init", "-q", "-b", "main")
        git(source, "config", "user.name", "AIPS Fixture")
        git(source, "config", "user.email", "aips" + chr(64) + "example.invalid")
        (source / "bin").mkdir()
        (source / "bin/aips").write_text("#!/bin/sh\nexit 0\n")
        (source / "bin/aips").chmod(0o755)
        git(source, "add", "bin/aips")
        git(source, "commit", "-qm", "fixture")
        linked = base / "linked worktree"
        git(source, "worktree", "add", "--detach", str(linked))
        assert (linked / ".git").is_file()
        target = base / "installed"
        installed = subprocess.run(["bash", str(ROOT / "scripts/install.sh"), "--source-checkout", str(linked)],
                                   env={**os.environ, "AIPS_INSTALL_DIR": str(target)}, capture_output=True, text=True)
        assert installed.returncode == 0, installed.stderr
        assert git(target, "rev-parse", "HEAD") == git(source, "rev-parse", "HEAD")
        rejected = subprocess.run(["bash", str(ROOT / "scripts/install.sh"), "--source-checkout", str(linked / "bin")],
                                  env={**os.environ, "AIPS_INSTALL_DIR": str(base / "rejected")}, capture_output=True, text=True)
        assert rejected.returncode != 0 and "top level" in rejected.stderr

        remote = base / "remote.git"
        git(base, "clone", "--bare", str(source), str(remote))
        git(source, "remote", "add", "origin", str(remote))
        (source / "state").write_text("new\n")
        git(source, "add", "state")
        git(source, "commit", "-qm", "update")
        git(source, "push", "-q", "origin", "main")
        git(target, "remote", "set-url", "origin", str(remote))
        head = git(source, "rev-parse", "HEAD")
        args = Namespace(remote="origin", branch="main", fetch=True, apply=True)
        with patch.dict(os.environ, {"AIPS_INSTALLED_SYSTEM_DIR": str(target)}):
            sync = publish.sync_installed(source, args, head)
            assert sync["status"] == "CURRENT" and sync["action"] == "FAST_FORWARD", sync
            (target / "dirty").write_text("keep\n")
            denied = publish.sync_installed(source, args, head)
            assert denied["reason_code"] == "INSTALLATION_NOT_CLEAN_MAIN"
            assert (target / "dirty").read_text() == "keep\n"
            (target / "dirty").unlink()
            git(target, "config", "user.name", "AIPS Fixture")
            git(target, "config", "user.email", "aips" + chr(64) + "example.invalid")
            (target / "local").write_text("diverged\n")
            git(target, "add", "local")
            git(target, "commit", "-qm", "local")
            divergent = git(target, "rev-parse", "HEAD")
            assert publish.sync_installed(source, args, head)["reason_code"] == "INSTALLATION_DIVERGED"
            assert git(target, "rev-parse", "HEAD") == divergent

        checks = {"headRefOid": "candidate", "statusCheckRollup": [
            {"workflowName": "validate", "name": "repository", "conclusion": "CANCELLED", "startedAt": "2026-01-01T00:00:00Z"},
            {"workflowName": "validate", "name": "repository", "conclusion": "SUCCESS", "startedAt": "2026-01-01T00:01:00Z"},
            {"workflowName": "docs", "name": "deploy", "conclusion": "SKIPPED", "startedAt": "2026-01-01T00:01:00Z"},
        ]}
        assert publish.summarize_checks(checks, ["repository"])["status"] == "PASS"
        checks["statusCheckRollup"][1]["conclusion"] = "CANCELLED"
        assert publish.summarize_checks(checks, ["repository"])["status"] == "INCOMPLETE"
        checks["statusCheckRollup"][1]["conclusion"] = "FAILURE"
        assert publish.summarize_checks(checks, ["repository"])["status"] == "FAIL"
    print("runtime_recovery_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

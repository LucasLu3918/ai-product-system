#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "scripts" / "governance_guard.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    spec = importlib.util.spec_from_file_location("aips_governance_guard", GUARD)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load governance_guard.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    cases = {
        "git push origin main": ["git_push"],
        "git -C /tmp/repo push origin main": ["git_push"],
        "/usr/bin/git --no-pager -C /tmp/repo push": ["git_push"],
        "env A=1 git push": ["git_push"],
        "sudo -u runner git push": ["git_push"],
        "bash -lc 'git push origin main'": ["git_push"],
        "git tag v1.2.3": ["git_tag"],
        "/usr/bin/git -C /tmp/repo tag v1.2.3": ["git_tag"],
        "gh pr create --title release": ["gh_pr_create"],
        "gh --repo owner/repo pr create --title release": ["gh_pr_create"],
        "/usr/bin/gh release create v1.2.3": ["gh_release_create"],
        "bash -c 'git push && gh release create v1.2.3'": ["git_push", "gh_release_create"],
        "echo ok && git -C /tmp/repo push": ["git_push"],
        "printf 'git push'": [],
        "git status": [],
        "gh pr view 1": [],
        "python -m pytest": [],
    }
    for command, expected in cases.items():
        actual = module.operations_for(command)
        require(actual == expected, f"{command!r}: expected {expected}, got {actual}")

    require(module.operation_for("git -C /tmp/repo push") == "git_push", "compatibility operation_for failed")
    print("governance_command_guard evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "scripts" / "manage_runtime_adapter.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(MANAGER), *args],
        capture_output=True,
        text=True,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "CLAUDE.md"
        source = root / "aips.md"
        snapshot = root / "owned.block"
        original = "# user rule\nkeep this exactly\n"
        target.write_text(original, encoding="utf-8")
        source.write_text("# aips rule\n", encoding="utf-8")

        installed = run(
            "install-block",
            "--target", str(target),
            "--source", str(source),
            "--snapshot", str(snapshot),
        )
        require(installed.returncode == 0, f"managed block install failed: {installed.stderr}")
        installed_text = target.read_text(encoding="utf-8")
        require(original.strip() in installed_text, "existing user instructions were not preserved")
        require("AIPS-MANAGED-BEGIN" in installed_text, "AIPS managed block missing")

        removed = run(
            "uninstall-block",
            "--target", str(target),
            "--snapshot", str(snapshot),
        )
        require(removed.returncode == 0, f"managed block uninstall failed: {removed.stderr}")
        require(target.read_text(encoding="utf-8") == original, "uninstall did not restore original user file bytes")

        installed = run(
            "install-block",
            "--target", str(target),
            "--source", str(source),
            "--snapshot", str(snapshot),
        )
        require(installed.returncode == 0, "second managed block install failed")
        edited = target.read_text(encoding="utf-8").replace("# aips rule", "# aips rule manually edited")
        target.write_text(edited, encoding="utf-8")
        conflict = run(
            "uninstall-block",
            "--target", str(target),
            "--snapshot", str(snapshot),
        )
        require(conflict.returncode != 0, "modified managed block must not be silently removed")
        conflict_doc = json.loads(conflict.stdout)
        require(conflict_doc.get("status") == "CONFLICT", "modified managed block must report CONFLICT")
        require("manually edited" in target.read_text(encoding="utf-8"), "modified managed block was not preserved")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        settings = root / "settings.json"
        user_hook = {"hooks": [{"type": "command", "command": "user-hook"}]}
        settings.write_text(
            json.dumps({"permissions": {"allow": ["Read"]}, "hooks": {"PreToolUse": [user_hook]}}),
            encoding="utf-8",
        )
        installed = run(
            "install-claude-hook",
            "--settings", str(settings),
            "--command", "AIPS_MANAGED_HOOK=1 echo prompt",
            "--guard-command", "AIPS_MANAGED_HOOK=1 echo guard",
        )
        require(installed.returncode == 0, f"Claude hook install failed: {installed.stderr}")
        doc = json.loads(settings.read_text(encoding="utf-8"))
        require(doc.get("permissions") == {"allow": ["Read"]}, "unrelated Claude settings changed")
        require(user_hook in doc.get("hooks", {}).get("PreToolUse", []), "unrelated PreToolUse hook was replaced")
        require("UserPromptSubmit" in doc.get("hooks", {}), "AIPS UserPromptSubmit hook missing")

        removed = run("uninstall-claude-hook", "--settings", str(settings))
        require(removed.returncode == 0, f"Claude hook uninstall failed: {removed.stderr}")
        doc = json.loads(settings.read_text(encoding="utf-8"))
        require(doc.get("permissions") == {"allow": ["Read"]}, "Claude settings were not preserved")
        require(doc.get("hooks", {}).get("PreToolUse") == [user_hook], "unrelated PreToolUse hook was not preserved")
        require("UserPromptSubmit" not in doc.get("hooks", {}), "AIPS UserPromptSubmit hook was not removed")

    print("adapter_composition evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

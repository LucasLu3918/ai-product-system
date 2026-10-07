from __future__ import annotations

import json
import subprocess
import sys

from .static_contracts import ROOT, errors

HOOK_SCRIPT = ROOT / "harness/adapters/codex/hooks/pre_tool_use_policy.py"
HOOK_CONFIG = ROOT / "harness/adapters/codex/hooks/hooks.json"
required = (
    ROOT / "harness/adapters/codex/hooks/README.md",
    HOOK_SCRIPT,
    HOOK_CONFIG,
    ROOT / "tests/evidence/codex_hooks_lifecycle.py",
    ROOT / "tests/scenarios/227-codex-native-hook-enforcement-probe.md",
)
for path in required:
    if not path.is_file():
        errors.append(f"Missing Codex hook probe artifact: {path.relative_to(ROOT)}")

if HOOK_CONFIG.is_file():
    try:
        config = json.loads(HOOK_CONFIG.read_text(encoding="utf-8"))
        handlers = config["hooks"]["PreToolUse"]
        if len(handlers) != 1 or handlers[0].get("matcher") != "^Bash$":
            errors.append("Codex hook probe must match only Bash")
        hook = handlers[0]["hooks"][0]
        if hook.get("timeout") != 3 or hook.get("type") != "command":
            errors.append("Codex hook probe must use the bounded three-second command handler")
        if not str(hook.get("command") or "").endswith("pre_tool_use_policy.py\""):
            errors.append("Codex hook probe command must reference the repository-local callback")
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        errors.append(f"Codex hook configuration is invalid: {exc}")

if HOOK_SCRIPT.is_file():
    result = subprocess.run(
        [sys.executable, str(ROOT / "tests/evidence/codex_hooks_lifecycle.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        errors.append("Codex hook synthetic lifecycle failed: " + result.stdout + result.stderr)

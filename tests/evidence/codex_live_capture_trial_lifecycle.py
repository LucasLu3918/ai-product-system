#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import agent_observable_event_capture as capture  # noqa: E402

MANAGER = ROOT / "scripts" / "manage_runtime_adapter.py"


def run_manager(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(MANAGER), *args], capture_output=True, text=True)


def write_config(path: Path, *, enabled: bool = True, max_events: int = 32) -> None:
    value = dict(capture.DEFAULT_CONFIG)
    value["enabled"] = enabled
    value["max_events"] = max_events
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def payload(tool_use_id: str, response: object, tool_input: object | None = None) -> dict:
    return {
        "session_id": "session-test",
        "cwd": "/tmp/project",
        "hook_event_name": "PostToolUse",
        "turn_id": "turn-test",
        "tool_name": "apply_patch",
        "tool_use_id": tool_use_id,
        "tool_input": tool_input if tool_input is not None else {"command": "*** Begin Patch\n*** End Patch"},
        "tool_response": response,
    }


with tempfile.TemporaryDirectory(prefix="aips-codex-capture-trial-") as tmp:
    root = Path(tmp)
    hooks = root / "hooks.json"
    snapshot = root / "owned-hook.json"
    original_user_group = {
        "matcher": "^Bash$",
        "hooks": [{"type": "command", "command": "user-owned-hook", "timeout": 9}],
    }
    hooks.write_text(json.dumps({"description": "user-owned", "hooks": {"PostToolUse": [original_user_group]}}, indent=2) + "\n", encoding="utf-8")

    command = "AIPS_MANAGED_HOOK=1 python3 /aips/scripts/agent_observable_event_capture.py hook --runtime codex --spool /tmp/aips-spool"
    installed = run_manager("install-codex-hook", "--settings", str(hooks), "--command", command, "--snapshot", str(snapshot))
    assert installed.returncode == 0, installed.stdout + installed.stderr

    doc = json.loads(hooks.read_text(encoding="utf-8"))
    groups = doc["hooks"]["PostToolUse"]
    assert original_user_group in groups
    aips_groups = [
        group for group in groups
        if any("AIPS_MANAGED_HOOK=1" in str(hook.get("command", "")) for hook in group.get("hooks", []))
    ]
    assert len(aips_groups) == 1
    aips_group = aips_groups[0]
    assert aips_group["matcher"] == "^(apply_patch|Edit|Write)$"
    hook = aips_group["hooks"][0]
    assert hook["type"] == "command"
    assert hook["async"] is True
    assert hook["timeout"] == 2
    assert snapshot.exists()

    reinstalled = run_manager("install-codex-hook", "--settings", str(hooks), "--command", command, "--snapshot", str(snapshot))
    assert reinstalled.returncode == 0
    doc = json.loads(hooks.read_text(encoding="utf-8"))
    assert len([
        group for group in doc["hooks"]["PostToolUse"]
        if any("AIPS_MANAGED_HOOK=1" in str(h.get("command", "")) for h in group.get("hooks", []))
    ]) == 1

    modified = json.loads(hooks.read_text(encoding="utf-8"))
    for group in modified["hooks"]["PostToolUse"]:
        if any("AIPS_MANAGED_HOOK=1" in str(h.get("command", "")) for h in group.get("hooks", [])):
            group["hooks"][0]["timeout"] = 3
    hooks.write_text(json.dumps(modified, indent=2) + "\n", encoding="utf-8")
    conflict = run_manager("uninstall-codex-hook", "--settings", str(hooks), "--snapshot", str(snapshot))
    assert conflict.returncode != 0
    assert json.loads(conflict.stdout)["status"] == "CONFLICT"
    assert snapshot.exists()

    for group in modified["hooks"]["PostToolUse"]:
        if any("AIPS_MANAGED_HOOK=1" in str(h.get("command", "")) for h in group.get("hooks", [])):
            group["hooks"][0]["timeout"] = 2
    hooks.write_text(json.dumps(modified, indent=2) + "\n", encoding="utf-8")
    removed = run_manager("uninstall-codex-hook", "--settings", str(hooks), "--snapshot", str(snapshot))
    assert removed.returncode == 0
    after = json.loads(hooks.read_text(encoding="utf-8"))
    assert after["description"] == "user-owned"
    assert after["hooks"]["PostToolUse"] == [original_user_group]
    assert not snapshot.exists()

    config = root / "capture.yaml"
    spool = root / "spool"
    write_config(config, enabled=True, max_events=8)

    success = capture.process_hook(
        payload("tool-1", {"success": True}),
        config_path=config,
        spool=spool,
        observed_at="2026-09-20T02:40:00Z",
        env={"AIPS_CHANGE_BOUNDARY": "trial"},
    )
    assert success["status"] == "ACCEPTED"
    events = sorted(spool.glob("event-*.json"))
    assert len(events) == 1
    event = json.loads(events[0].read_text(encoding="utf-8"))
    assert event["runtime"] == "codex"
    assert event["adapter_id"] == "codex-post-tool-use-v1"
    assert event["resource_id"] == "repository-patch"
    assert event["operation"] == "update"
    assert event["observed_outcome"] == "SUCCESS"
    assert event["network_used"] is False
    assert event["change_boundary"] == "trial"
    serialized = events[0].read_text(encoding="utf-8")
    for forbidden in ("tool_input", "tool_response", "*** Begin Patch", "session-test", "turn-test"):
        assert forbidden not in serialized

    failed = capture.process_hook(
        payload("tool-2", {"exit_code": 1}),
        config_path=config,
        spool=spool,
        observed_at="2026-09-20T02:40:01Z",
        env={},
    )
    assert failed["status"] == "ACCEPTED"
    outcomes = [json.loads(path.read_text(encoding="utf-8"))["observed_outcome"] for path in spool.glob("event-*.json")]
    assert "FAILED" in outcomes

    secret = capture.process_hook(
        payload("tool-secret", {"success": True}, {"command": "api_key=super-secret-value"}),
        config_path=config,
        spool=spool,
        observed_at="2026-09-20T02:40:02Z",
        env={},
    )
    assert secret["status"] == "DROPPED_SENSITIVE"

    private = capture.process_hook(
        payload("tool-private", {"success": True}, {"chain_of_thought": "private"}),
        config_path=config,
        spool=spool,
        observed_at="2026-09-20T02:40:03Z",
        env={},
    )
    assert private["status"] == "DROPPED_SENSITIVE"

    unresolved = capture.process_hook(
        payload("tool-unresolved", "opaque response"),
        config_path=config,
        spool=spool,
        observed_at="2026-09-20T02:40:04Z",
        env={},
    )
    assert unresolved["status"] == "DROPPED_UNRESOLVED_OUTCOME"

    disabled = capture.process_hook(
        payload("tool-disabled", {"success": True}),
        config_path=root / "missing.yaml",
        spool=root / "disabled-spool",
        observed_at="2026-09-20T02:40:05Z",
        env={},
    )
    assert disabled["status"] == "DISABLED"
    assert not (root / "disabled-spool").exists()

    bounded_config = root / "bounded.yaml"
    bounded_spool = root / "bounded-spool"
    write_config(bounded_config, enabled=True, max_events=4)

    def emit(index: int) -> str:
        result = capture.process_hook(
            payload(f"parallel-{index}", {"success": True}),
            config_path=bounded_config,
            spool=bounded_spool,
            observed_at=f"2026-09-20T02:41:{index:02d}Z",
            env={},
        )
        return result["status"]

    with ThreadPoolExecutor(max_workers=8) as pool:
        statuses = list(pool.map(emit, range(8)))
    assert len(list(bounded_spool.glob("event-*.json"))) <= 4
    assert "DROPPED_BUFFER_FULL" in statuses
    health = json.loads((bounded_spool / "health.json").read_text(encoding="utf-8"))
    assert health["dropped_buffer_full"] >= 1
    assert health["live_capture_verified"] is False
    assert health["raw_payload_persisted"] is False

    perf_config = root / "perf.yaml"
    perf_spool = root / "perf-spool"
    write_config(perf_config, enabled=True, max_events=64)
    durations = []
    for index in range(30):
        start = time.perf_counter()
        result = capture.process_hook(
            payload(f"perf-{index}", {"success": True}),
            config_path=perf_config,
            spool=perf_spool,
            observed_at=f"2026-09-20T02:42:{index:02d}Z",
            env={},
        )
        durations.append((time.perf_counter() - start) * 1000.0)
        assert result["status"] == "ACCEPTED"
    p95 = statistics.quantiles(durations, n=20)[18]
    assert p95 < 250.0, f"capture p95 overhead too high: {p95:.2f}ms"

print("codex live-capture implementation trial lifecycle: PASS")

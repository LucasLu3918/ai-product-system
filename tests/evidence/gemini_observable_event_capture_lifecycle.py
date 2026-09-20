#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import agent_anomaly_evaluation as anomaly  # noqa: E402
import gemini_observable_event_capture as capture  # noqa: E402
import resource_authorization as authorization  # noqa: E402

CONFIG = ROOT / "config/gemini-observable-event-capture.yaml"
FIXTURE = ROOT / "tests/fixtures/gemini_observable_event_capture/after-tool-events.yaml"
PROFILE = ROOT / "tests/fixtures/gemini_observable_event_capture/profile.yaml"
RESULT = ROOT / "references/evolution/ISSUE_79_GEMINI_LIVE_CAPTURE_TRIAL_RESULT.yaml"
SCRIPT = ROOT / "scripts/gemini_observable_event_capture.py"
HOOK = ROOT / "harness/adapters/gemini-cli/hooks/aips-observable-event-capture.sh"


config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
fixture = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
profile = yaml.safe_load(PROFILE.read_text(encoding="utf-8"))
result = yaml.safe_load(RESULT.read_text(encoding="utf-8"))

capture.validate_config(config)
authorization.validate_profile(profile)
assert capture.enabled(config, {}) is False
assert result["status"] == "PASS"
assert result["runtime_verification"]["live_runtime_execution_verified"] is False
assert result["runtime_verification"]["live_capture_verified"] is False
assert result["enabled_by_default"] is False
assert result["enforcement"]["critical_path"] is False
assert result["enforcement"]["critical_path_semantics"] == "authorization_or_result_enforcement_only"
assert result["enforcement"]["synchronous_hook"] is True
assert result["enforcement"]["latency_path"] == "synchronous"
assert result["enforcement"]["result_flow_control_authorized"] is False

captured = 0
degraded = 0
skipped = 0
with tempfile.TemporaryDirectory(prefix="aips-gemini-capture-") as tmp:
    sink = Path(tmp) / "events.jsonl"
    for case in fixture["cases"]:
        outcome = capture.process_payload(
            case["payload"],
            config,
            capture_enabled=True,
            sink_text=str(sink),
        )
        assert outcome["status"] == case["expect"], (case["id"], outcome)
        if outcome["status"] == "CAPTURED":
            captured += 1
        elif outcome["status"] == "DEGRADED":
            degraded += 1
        elif outcome["status"] == "SKIPPED_UNSUPPORTED":
            skipped += 1

    assert captured == 6
    assert degraded == 3
    assert skipped == 1

    rows = [json.loads(line) for line in sink.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 6
    persisted = sink.read_text(encoding="utf-8")
    assert "super-secret-value" not in persisted
    assert "private_reasoning" not in persisted
    assert "tool_input" not in persisted
    assert "tool_response" not in persisted
    assert "llmContent" not in persisted

    for event in rows:
        assert set(event) == {
            "event_id",
            "observed_at",
            "runtime",
            "adapter_id",
            "subject",
            "resource_id",
            "operation",
            "observed_outcome",
            "network_used",
        }
        auth = authorization.decision(
            profile,
            event["resource_id"],
            event["operation"],
            None,
        )
        assert auth["status"] == "ALLOW"
        assert anomaly.detect(event, profile) == []

    missing_sink = capture.process_payload(
        fixture["cases"][0]["payload"],
        config,
        capture_enabled=True,
        sink_text="",
    )
    assert missing_sink["status"] == "DEGRADED"

    disabled_sink = Path(tmp) / "disabled.jsonl"
    disabled = capture.process_payload(
        fixture["cases"][0]["payload"],
        config,
        capture_enabled=False,
        sink_text=str(disabled_sink),
    )
    assert disabled["status"] == "DISABLED"
    assert not disabled_sink.exists()

    disabled_hook_sink = Path(tmp) / "disabled-hook.jsonl"
    disabled_hook = subprocess.run(
        [str(HOOK)],
        cwd=ROOT,
        input=json.dumps(fixture["cases"][0]["payload"]),
        text=True,
        capture_output=True,
        env={
            **__import__("os").environ,
            "AIPS_OBSERVABLE_EVENT_CAPTURE_SINK": str(disabled_hook_sink),
        },
        timeout=2,
    )
    assert disabled_hook.returncode == 0
    assert json.loads(disabled_hook.stdout) == {"decision": "allow", "suppressOutput": True}
    assert not disabled_hook_sink.exists()

    env = {
        "AIPS_OBSERVABLE_EVENT_CAPTURE": "1",
        "AIPS_OBSERVABLE_EVENT_CAPTURE_SINK": str(Path(tmp) / "subprocess.jsonl"),
    }
    durations = []
    payload = json.dumps(fixture["cases"][0]["payload"])
    for _ in range(result["overhead"]["sample_count"]):
        started = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "hook", "--config", str(CONFIG)],
            cwd=ROOT,
            input=payload,
            text=True,
            capture_output=True,
            env={**__import__("os").environ, **env},
            timeout=2,
        )
        durations.append((time.perf_counter() - started) * 1000)
        assert proc.returncode == 0
        assert json.loads(proc.stdout) == {"decision": "allow", "suppressOutput": True}
    p95 = max(durations) if len(durations) < 20 else statistics.quantiles(durations, n=20)[18]
    assert p95 <= result["overhead"]["max_allowed_ms"], p95
    print(f"gemini observable-event capture p95_ms={p95:.3f}")

assert result["supported_case_count"] == captured
assert result["captured_supported_cases"] == captured
assert result["unexpected_event_loss"] == 0
assert result["expected_degraded_cases"] == degraded + skipped
assert result["secret_private_raw_leakage"] == 0
print("gemini observable-event capture lifecycle: PASS")

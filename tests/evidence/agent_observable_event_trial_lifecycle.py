#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "agent_observable_event_trial.py"
CONFIG = ROOT / "config" / "agent-observable-event-trial.yaml"
PROFILE = ROOT / "tests" / "fixtures" / "agent_anomaly_evaluation" / "profile.yaml"
BASELINE = ROOT / "references" / "evolution" / "ISSUE_79_AGENT_ANOMALY_TRIAL_BASELINE.yaml"
DECISION = ROOT / "references" / "evolution" / "ISSUE_79_AGENT_ANOMALY_TRIAL_DECISION.yaml"
FIXTURE = ROOT / "tests" / "fixtures" / "agent_observable_event_trial" / "raw-events.yaml"
RESULT = ROOT / "references" / "evolution" / "ISSUE_79_AGENT_OBSERVABLE_EVENT_TRIAL_RESULT.yaml"


def run(fixture: Path, *, decision: Path = DECISION, config: Path = CONFIG) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable, str(SCRIPT), "--format", "json", "run",
            "--config", str(config),
            "--profile", str(PROFILE),
            "--baseline", str(BASELINE),
            "--decision", str(decision),
            "--fixture", str(fixture),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


good = run(FIXTURE)
assert good.returncode == 0, good.stdout + good.stderr
doc = json.loads(good.stdout)
committed = yaml.safe_load(RESULT.read_text(encoding="utf-8"))
assert doc == committed
assert doc["status"] == "PASS"
assert doc["case_count"] == 12
assert doc["metrics"]["true_positive"] == 6
assert doc["metrics"]["false_positive"] == 0
assert doc["metrics"]["true_negative"] == 6
assert doc["metrics"]["false_negative"] == 0
assert doc["live_capture_verified"] is False
assert doc["raw_payload_persisted"] is False
assert doc["enforcement"]["runtime_enforced"] is False
assert doc["authority"]["human_adoption_decision_required"] is True
assert "raw_event" not in good.stdout

base = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
decision_doc = yaml.safe_load(DECISION.read_text(encoding="utf-8"))
config_doc = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))

with tempfile.TemporaryDirectory(prefix="aips-observable-event-trial-") as tmp:
    root = Path(tmp)

    private = copy.deepcopy(base)
    private["cases"][0]["raw_event"]["chain_of_thought"] = "private"
    private_path = root / "private.yaml"
    private_path.write_text(yaml.safe_dump(private, sort_keys=False), encoding="utf-8")
    assert run(private_path).returncode == 2

    secret = copy.deepcopy(base)
    secret["cases"][1]["raw_event"]["target"] = "api_key=super-secret-value"
    secret_path = root / "secret.yaml"
    secret_path.write_text(yaml.safe_dump(secret, sort_keys=False), encoding="utf-8")
    assert run(secret_path).returncode == 2

    extra = copy.deepcopy(base)
    extra["cases"][0]["raw_event"]["tool_args"] = "--dangerous"
    extra_path = root / "extra.yaml"
    extra_path.write_text(yaml.safe_dump(extra, sort_keys=False), encoding="utf-8")
    assert run(extra_path).returncode == 2

    unknown = copy.deepcopy(base)
    unknown["cases"][0]["adapter"] = "unknown-runtime-adapter"
    unknown_path = root / "unknown.yaml"
    unknown_path.write_text(yaml.safe_dump(unknown, sort_keys=False), encoding="utf-8")
    assert run(unknown_path).returncode == 2

    stale_decision = copy.deepcopy(decision_doc)
    stale_decision["decision"]["baseline_repository_revision"] = "0" * 40
    stale_path = root / "stale-decision.yaml"
    stale_path.write_text(yaml.safe_dump(stale_decision, sort_keys=False), encoding="utf-8")
    assert run(FIXTURE, decision=stale_path).returncode == 2

    live_config = copy.deepcopy(config_doc)
    live_config["live_capture_verified"] = True
    live_path = root / "live.yaml"
    live_path.write_text(yaml.safe_dump(live_config, sort_keys=False), encoding="utf-8")
    assert run(FIXTURE, config=live_path).returncode == 2

print("agent observable-event integration trial lifecycle: PASS")

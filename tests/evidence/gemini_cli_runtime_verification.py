#!/usr/bin/env python3
"""Exact-candidate real Gemini CLI runtime verification for AIPS AfterTool capture."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "gemini_cli_runtime_verification"
EXTENSION = ROOT / "harness" / "adapters" / "gemini-cli"
CONFIG = ROOT / "config" / "gemini-observable-event-capture.yaml"
EXPECTED_RESULT = ROOT / "references" / "evolution" / "ISSUE_79_GEMINI_RUNTIME_VERIFICATION_RESULT.yaml"


def run(cmd: list[str], *, cwd: Path, env: dict[str, str], input_text: str | None = None, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def closed_guard_endpoint() -> None:
    sock = socket.socket()
    sock.settimeout(0.25)
    try:
        require(sock.connect_ex(("127.0.0.1", 9)) != 0, "provider guard endpoint unexpectedly has a listener")
    finally:
        sock.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gemini", default="gemini")
    parser.add_argument("--expected-version", default="0.60.0")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    gemini = shutil.which(args.gemini)
    require(bool(gemini), "Gemini CLI executable not found")
    gemini = str(gemini)

    version = run([gemini, "--version"], cwd=ROOT, env=dict(os.environ), timeout=20)
    require(version.returncode == 0, version.stderr)
    require(args.expected_version in version.stdout.strip(), f"unexpected Gemini CLI version: {version.stdout!r}")

    closed_guard_endpoint()
    expected = yaml.safe_load(EXPECTED_RESULT.read_text(encoding="utf-8")) or {}
    require(expected.get("gemini_cli_version") == args.expected_version, "result/version binding mismatch")

    with tempfile.TemporaryDirectory(prefix="aips-gemini-real-runtime-") as tmp:
        base = Path(tmp)
        home = base / "home"
        workspace = base / "workspace"
        sink = base / "events.jsonl"
        home.mkdir()
        workspace.mkdir()
        (workspace / "read-target.txt").write_text("read-runtime-verification\n", encoding="utf-8")
        (workspace / "replace-target.txt").write_text("before\n", encoding="utf-8")

        gemini_dir = home / ".gemini"
        gemini_dir.mkdir(parents=True)
        (gemini_dir / "settings.json").write_text(
            json.dumps(
                {
                    "general": {"enableAutoUpdate": False},
                    "privacy": {"usageStatisticsEnabled": False},
                    "security": {
                        "auth": {"selectedType": "gemini-api-key"},
                        "folderTrust": {"enabled": False},
                    },
                    "hooksConfig": {"enabled": True},
                    "model": {
                        "name": "gemini-2.5-flash",
                        "skipNextSpeakerCheck": True,
                    },
                }
            ),
            encoding="utf-8",
        )

        env = dict(os.environ)
        env.update(
            {
                "HOME": str(home),
                "GEMINI_CLI_HOME": str(home),
                "GEMINI_CLI_INTEGRATION_TEST": "true",
                "GEMINI_FORCE_FILE_STORAGE": "true",
                "GEMINI_API_KEY": "aips-fake-responses-no-provider-secret",
                "GOOGLE_GEMINI_BASE_URL": "http://127.0.0.1:9",
                "NO_COLOR": "1",
                "CI": "true",
                "AIPS_OBSERVABLE_EVENT_CAPTURE": "1",
                "AIPS_OBSERVABLE_EVENT_CAPTURE_SINK": str(sink),
                "GEMINI_CWD": str(workspace),
            }
        )

        linked = run(
            [gemini, "extensions", "link", str(EXTENSION)],
            cwd=workspace,
            env=env,
            input_text="y\n",
            timeout=60,
        )
        require(linked.returncode == 0, f"extension link failed: {linked.stdout}\n{linked.stderr}")
        listed = run([gemini, "extensions", "list"], cwd=workspace, env=env, timeout=30)
        require(listed.returncode == 0, listed.stderr)
        require("aips-global-harness" in listed.stdout, f"AIPS extension not loaded: {listed.stdout}")

        disabled_sink = base / "disabled.jsonl"
        disabled_env = dict(env)
        disabled_env.pop("AIPS_OBSERVABLE_EVENT_CAPTURE", None)
        disabled_env["AIPS_OBSERVABLE_EVENT_CAPTURE_SINK"] = str(disabled_sink)
        disabled = run(
            [
                gemini,
                "--approval-mode=yolo",
                "--skip-trust",
                "--fake-responses",
                str(FIXTURES / "read.responses"),
                "-p",
                "Execute the deterministic read verification.",
            ],
            cwd=workspace,
            env=disabled_env,
            timeout=30,
        )
        require(disabled.returncode == 0, f"disabled CLI run failed: {disabled.stdout}\n{disabled.stderr}")
        require(not disabled_sink.exists(), "disabled-by-default real CLI path unexpectedly captured an event")

        durations: list[float] = []
        for name in ("read", "write", "replace"):
            started = time.perf_counter()
            proc = run(
                [
                    gemini,
                    "--approval-mode=yolo",
                    "--skip-trust",
                    "--fake-responses",
                    str(FIXTURES / f"{name}.responses"),
                    "-p",
                    f"Execute the deterministic {name} verification.",
                ],
                cwd=workspace,
                env=env,
                timeout=30,
            )
            durations.append(time.perf_counter() - started)
            require(proc.returncode == 0, f"{name} real CLI run failed: {proc.stdout}\n{proc.stderr}")

        require((workspace / "written-target.txt").read_text(encoding="utf-8") == "written-by-gemini-runtime-verification\n", "write_file did not execute in the real CLI")
        require((workspace / "replace-target.txt").read_text(encoding="utf-8") == "after\n", "replace did not execute in the real CLI")
        require(sink.exists(), "AfterTool hook did not produce the capture sink")

        rows = [json.loads(line) for line in sink.read_text(encoding="utf-8").splitlines() if line.strip()]
        require(len(rows) == 3, f"expected 3 captured events, got {len(rows)}")
        require([row["resource_id"] for row in rows] == [
            "gemini-cli-read-file",
            "gemini-cli-write-file",
            "gemini-cli-write-file",
        ], f"unexpected resource sequence: {rows}")
        require([row["operation"] for row in rows] == ["read", "update", "update"], f"unexpected operation sequence: {rows}")
        require(all(row["runtime"] == "gemini-cli" for row in rows), "runtime metadata mismatch")
        require(all(row["observed_outcome"] == "SUCCESS" for row in rows), "real tool execution did not report SUCCESS")
        require(all(row["network_used"] is False for row in rows), "bounded file-tool scope must remain network_used=false")

        persisted = sink.read_text(encoding="utf-8")
        forbidden = (
            "tool_input",
            "tool_response",
            "private_reasoning",
            "chain_of_thought",
            "aips-fake-responses-no-provider-secret",
            "written-by-gemini-runtime-verification",
            "read-runtime-verification",
        )
        require(not any(token in persisted for token in forbidden), "capture sink leaked raw/private/secret-like data")

        max_duration = max(durations)
        require(max_duration <= 30, f"real CLI verification exceeded bounded per-run time: {max_duration:.3f}s")
        report: dict[str, Any] = {
            "status": "PASS",
            "runtime": "gemini-cli",
            "gemini_cli_version": args.expected_version,
            "binary_execution_verified": True,
            "extension_loading_verified": True,
            "real_tool_execution_verified": True,
            "after_tool_hook_execution_verified": True,
            "provider_model_api_exercised": False,
            "provider_model_execution_verified": False,
            "capture_events": len(rows),
            "unexpected_event_loss": 0,
            "disabled_by_default_verified": True,
            "max_cli_run_seconds_observed": round(max_duration, 3),
            "verified_tools": ["read_file", "write_file", "replace"],
        }
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

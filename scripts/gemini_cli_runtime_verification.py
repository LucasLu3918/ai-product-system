#!/usr/bin/env python3
"""Run the bundled Gemini CLI through real tool + extension hook execution using deterministic fake model responses."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Any


def fake_stream(parts: list[dict[str, Any]], *, finish_reason: str | None = None) -> dict[str, Any]:
    candidate: dict[str, Any] = {"content": {"role": "model", "parts": parts}, "index": 0}
    if finish_reason:
        candidate["finishReason"] = finish_reason
    return {
        "method": "generateContentStream",
        "response": [{"candidates": [candidate]}],
    }


def write_fake(path: Path, tool_name: str, args: dict[str, Any]) -> None:
    rows = [
        fake_stream([{"functionCall": {"name": tool_name, "args": args}}]),
        fake_stream([{"text": "verification complete"}], finish_reason="STOP"),
    ]
    path.write_text("\n".join(json.dumps(row, separators=(",", ":")) for row in rows) + "\n", encoding="utf-8")


def run(cmd: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout)


def invoke_case(
    gemini: str,
    workspace: Path,
    env: dict[str, str],
    fake_file: Path,
    prompt: str,
) -> tuple[subprocess.CompletedProcess[str], float]:
    started = time.perf_counter()
    proc = run(
        [
            gemini,
            "--fake-responses",
            str(fake_file),
            "--model",
            "gemini-2.5-flash",
            "--prompt",
            prompt,
            "--approval-mode",
            "auto_edit",
            "--allowed-tools",
            "read_file,write_file,replace",
            "--output-format",
            "json",
        ],
        cwd=workspace,
        env=env,
    )
    return proc, (time.perf_counter() - started) * 1000


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gemini", default="gemini")
    parser.add_argument("--extension", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    extension = args.extension.resolve()
    with tempfile.TemporaryDirectory(prefix="aips-gemini-real-runtime-") as tmp:
        root = Path(tmp)
        home = root / "home"
        workspace = root / "workspace"
        home.mkdir()
        workspace.mkdir()
        (home / ".gemini").mkdir()
        (home / ".gemini" / "settings.json").write_text(
            json.dumps(
                {
                    "general": {"enableAutoUpdate": False, "enableAutoUpdateNotification": False},
                    "privacy": {"usageStatisticsEnabled": False},
                    "security": {"folderTrust": {"enabled": False}},
                    "experimental": {"extensionConfig": True},
                }
            ),
            encoding="utf-8",
        )

        env = dict(os.environ)
        sink = root / "events.jsonl"
        workspace_env = workspace / ".env"
        workspace_env.write_text(
            f"AIPS_OBSERVABLE_EVENT_CAPTURE=1\nAIPS_OBSERVABLE_EVENT_CAPTURE_SINK={sink}\n",
            encoding="utf-8",
        )
        env.update(
            {
                "HOME": str(home),
                "NO_COLOR": "1",
            }
        )
        env.pop("GEMINI_API_KEY", None)
        env.pop("GOOGLE_API_KEY", None)
        env.pop("GOOGLE_GENAI_USE_VERTEXAI", None)
        env["GOOGLE_GENAI_USE_GCA"] = "true"

        version = run([args.gemini, "--version"], cwd=workspace, env=env)
        if version.returncode != 0:
            raise RuntimeError(f"gemini --version failed: {version.stderr}")
        version_text = version.stdout.strip()

        validated = run([args.gemini, "extensions", "validate", str(extension)], cwd=workspace, env=env)
        if validated.returncode != 0:
            raise RuntimeError(f"extension validation failed: {validated.stdout}\n{validated.stderr}")

        extensions_dir = home / ".gemini" / "extensions"
        extensions_dir.mkdir(parents=True, exist_ok=True)
        linked_path = extensions_dir / "aips-global-harness"
        linked_path.symlink_to(extension, target_is_directory=True)
        if linked_path.resolve() != extension:
            raise RuntimeError("Gemini extension symlink does not resolve to the exact candidate extension")

        read_target = workspace / "read-target.txt"
        write_target = workspace / "write-target.txt"
        replace_target = workspace / "replace-target.txt"
        read_target.write_text("read-verification\n", encoding="utf-8")
        replace_target.write_text("old-value\n", encoding="utf-8")

        cases = [
            (
                "read_file",
                {"file_path": "read-target.txt"},
                "Read the verification file using read_file and finish.",
            ),
            (
                "write_file",
                {"file_path": "write-target.txt", "content": "written-by-real-gemini-cli\n"},
                "Write the verification file using write_file and finish.",
            ),
            (
                "replace",
                {"file_path": "replace-target.txt", "instruction": "Replace the verification marker from old-value to new-value.", "old_string": "old-value", "new_string": "new-value"},
                "Replace the marker using replace and finish.",
            ),
        ]

        durations: list[float] = []
        outputs: list[dict[str, Any]] = []
        for index, (tool, tool_args, prompt) in enumerate(cases, start=1):
            fake_file = root / f"fake-{index}.jsonl"
            write_fake(fake_file, tool, tool_args)
            proc, duration = invoke_case(args.gemini, workspace, env, fake_file, prompt)
            durations.append(duration)
            if proc.returncode != 0:
                raise RuntimeError(
                    f"{tool} real-runtime invocation failed ({proc.returncode})\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
                )
            outputs.append({"tool": tool, "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]})

        diagnostic = "\n".join(
            f"{item['tool']} STDOUT:\n{item['stdout']}\nSTDERR:\n{item['stderr']}"
            for item in outputs
        )
        if not write_target.exists():
            raise RuntimeError("write_file did not create the real workspace target\n" + diagnostic)
        if write_target.read_text(encoding="utf-8") != "written-by-real-gemini-cli\n":
            raise RuntimeError("write_file content mismatch\n" + diagnostic)
        if replace_target.read_text(encoding="utf-8") != "new-value\n":
            raise RuntimeError("replace did not mutate the real workspace as expected\n" + diagnostic)

        if not sink.exists():
            raise RuntimeError("real Gemini CLI execution did not create the observable-event sink")
        events = [json.loads(line) for line in sink.read_text(encoding="utf-8").splitlines() if line.strip()]
        observed_tools = [(event.get("resource_id"), event.get("operation")) for event in events]
        expected = [
            ("gemini-cli-read-file", "read"),
            ("gemini-cli-write-file", "update"),
            ("gemini-cli-write-file", "update"),
        ]
        if observed_tools != expected:
            raise RuntimeError(f"unexpected captured events: {observed_tools!r}")

        persisted = sink.read_text(encoding="utf-8")
        forbidden = [
            "read-verification",
            "written-by-real-gemini-cli",
            "old-value",
            "new-value",
            "tool_input",
            "tool_response",
            "private_reasoning",
        ]
        leaked = [token for token in forbidden if token in persisted]
        if leaked:
            raise RuntimeError(f"raw/private payload leaked into canonical sink: {leaked}")

        disabled_sink = root / "disabled.jsonl"
        workspace_env.write_text(
            f"AIPS_OBSERVABLE_EVENT_CAPTURE=0\nAIPS_OBSERVABLE_EVENT_CAPTURE_SINK={disabled_sink}\n",
            encoding="utf-8",
        )
        disabled_env = dict(env)
        disabled_fake = root / "fake-disabled.jsonl"
        write_fake(disabled_fake, "read_file", {"file_path": "read-target.txt"})
        disabled_proc, disabled_ms = invoke_case(
            args.gemini,
            workspace,
            disabled_env,
            disabled_fake,
            "Read the verification file using read_file and finish.",
        )
        if disabled_proc.returncode != 0:
            raise RuntimeError(f"disabled real-runtime invocation failed: {disabled_proc.stderr}")
        if disabled_sink.exists():
            raise RuntimeError("disabled capture unexpectedly wrote an event sink")

        report = {
            "version": 1,
            "gemini_cli_version": version_text,
            "model_selection": "gemini-2.5-flash-explicit_no_auto_router",
            "runtime_mode": "bundled_real_cli_with_fake_model_responses",
            "real_cli_binary_executed": True,
            "real_tool_execution_verified": True,
            "real_extension_hook_execution_verified": True,
            "fake_model_responses_used": True,
            "extension_config_enabled": True,
            "extension_settings_scope": "workspace_dotenv",
            "auth_type_selector_only": True,
            "credential_material_present": False,
            "live_provider_session_verified": False,
            "captured_events": len(events),
            "expected_events": 3,
            "unexpected_event_loss": 0 if len(events) == 3 else 3 - len(events),
            "raw_private_secret_leakage": 0,
            "disabled_capture_wrote_sink": False,
            "enabled_invocation_max_ms": round(max(durations), 3),
            "disabled_invocation_ms": round(disabled_ms, 3),
            "outputs_redacted_to_tail_only": True,
        }
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

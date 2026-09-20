#!/usr/bin/env python3
"""Verify Gemini CLI against a real provider session without persisting credential material."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from typing import Any


def redact(text: str, secret: str) -> str:
    value = text.replace(secret, "[REDACTED]") if secret else text
    return re.sub(r"(GEMINI_API_KEY\\s*[=:]\\s*)\\S+", r"\\1[REDACTED]", value)


def run(cmd: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout)


def provider_requests(stats: dict[str, Any]) -> tuple[int, int]:
    requests = 0
    errors = 0
    for model in (stats.get("models") or {}).values():
        api = (model or {}).get("api") or {}
        requests += int(api.get("totalRequests") or 0)
        errors += int(api.get("totalErrors") or 0)
    return requests, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gemini", default="gemini")
    parser.add_argument("--extension", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        report = {
            "version": 1,
            "status": "SKIPPED_NOT_CONFIGURED",
            "credential_source": "optional_environment:GEMINI_API_KEY",
            "credential_present": False,
            "provider_verification_enabled": False,
            "required_for_release": False,
            "live_provider_session_verified": False,
            "provider_model_execution_verified": False,
        }
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, sort_keys=True))
        return 0

    expected_sha = os.environ.get("AIPS_EXPECTED_SHA", "")
    extension = args.extension.resolve()

    with tempfile.TemporaryDirectory(prefix="aips-gemini-provider-session-") as tmp:
        root = Path(tmp)
        home = root / "home"
        workspace = root / "workspace"
        sink = root / "events.jsonl"
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
        (workspace / ".env").write_text(
            f"AIPS_OBSERVABLE_EVENT_CAPTURE=1\nAIPS_OBSERVABLE_EVENT_CAPTURE_SINK={sink}\n",
            encoding="utf-8",
        )

        env = dict(os.environ)
        env.update({"HOME": str(home), "NO_COLOR": "1"})
        env.pop("GOOGLE_API_KEY", None)
        env.pop("GOOGLE_GENAI_USE_VERTEXAI", None)
        env.pop("GOOGLE_GENAI_USE_GCA", None)

        version = run([args.gemini, "--version"], cwd=workspace, env=env)
        if version.returncode != 0:
            raise RuntimeError("gemini --version failed: " + redact(version.stderr, api_key))
        version_text = version.stdout.strip()

        validated = run([args.gemini, "extensions", "validate", str(extension)], cwd=workspace, env=env)
        if validated.returncode != 0:
            raise RuntimeError("extension validation failed: " + redact(validated.stdout + validated.stderr, api_key))

        extensions_dir = home / ".gemini" / "extensions"
        extensions_dir.mkdir(parents=True, exist_ok=True)
        linked_path = extensions_dir / "aips-global-harness"
        linked_path.symlink_to(extension, target_is_directory=True)
        if linked_path.resolve() != extension:
            raise RuntimeError("Gemini extension symlink does not resolve to the trusted extension")

        target = workspace / "provider-target.txt"
        target.write_text("provider-session-marker\n", encoding="utf-8")

        prompts = [
            "Use the read_file tool to read provider-target.txt before answering. You must call read_file. After reading it, reply exactly PROVIDER_SESSION_OK.",
            "Verification protocol: your first action must be read_file with file_path provider-target.txt. Do not answer without using the tool. Then reply exactly PROVIDER_SESSION_OK.",
        ]

        attempts = 0
        last_proc: subprocess.CompletedProcess[str] | None = None
        last_doc: dict[str, Any] = {}
        started = time.perf_counter()

        for prompt in prompts:
            attempts += 1
            if sink.exists():
                sink.unlink()
            proc = run(
                [
                    args.gemini,
                    "--model",
                    "gemini-2.5-flash",
                    "--prompt",
                    prompt,
                    "--approval-mode",
                    "auto_edit",
                    "--allowed-tools",
                    "read_file",
                    "--output-format",
                    "json",
                ],
                cwd=workspace,
                env=env,
            )
            last_proc = proc
            if proc.returncode != 0:
                raise RuntimeError(
                    f"live provider invocation failed ({proc.returncode}): "
                    + redact(proc.stderr[-4000:] + proc.stdout[-4000:], api_key)
                )
            try:
                doc = json.loads(proc.stdout)
            except json.JSONDecodeError as exc:
                raise RuntimeError("Gemini provider output was not JSON") from exc
            last_doc = doc

            stats = doc.get("stats") or {}
            tools = stats.get("tools") or {}
            events = []
            if sink.exists():
                events = [json.loads(line) for line in sink.read_text(encoding="utf-8").splitlines() if line.strip()]
            if int(tools.get("totalSuccess") or 0) >= 1 and events:
                break

        elapsed_ms = (time.perf_counter() - started) * 1000
        if last_proc is None:
            raise RuntimeError("provider verification did not execute")

        stats = last_doc.get("stats") or {}
        tools = stats.get("tools") or {}
        requests, request_errors = provider_requests(stats)

        if requests < 1:
            raise RuntimeError("no real provider model request was observed")
        if request_errors >= requests:
            raise RuntimeError("all provider model requests failed")
        if int(tools.get("totalCalls") or 0) < 1 or int(tools.get("totalSuccess") or 0) < 1:
            raise RuntimeError("live provider session did not execute a successful read_file tool")
        if "PROVIDER_SESSION_OK" not in str(last_doc.get("response") or ""):
            raise RuntimeError("live provider response did not contain the verification marker")
        if not sink.exists():
            raise RuntimeError("live provider session did not produce the AfterTool capture sink")

        persisted = sink.read_text(encoding="utf-8")
        events = [json.loads(line) for line in persisted.splitlines() if line.strip()]
        if not events:
            raise RuntimeError("live provider session produced no canonical capture events")
        for event in events:
            if event.get("resource_id") != "gemini-cli-read-file" or event.get("operation") != "read":
                raise RuntimeError("live provider session captured an unexpected tool event")

        forbidden = (
            api_key,
            "provider-session-marker",
            "tool_input",
            "tool_response",
            "private_reasoning",
            "chain_of_thought",
        )
        if any(token and token in persisted for token in forbidden):
            raise RuntimeError("provider credential/raw/private payload leaked into canonical event persistence")

        combined_output = (last_proc.stdout or "") + (last_proc.stderr or "")
        if api_key in combined_output:
            raise RuntimeError("provider credential appeared in Gemini CLI process output")

        report = {
            "version": 1,
            "status": "PASS",
            "candidate_sha": expected_sha,
            "gemini_cli_version": version_text,
            "model": "gemini-2.5-flash",
            "provider_auth_method": "gemini_api_key",
            "credential_source": "optional_environment:GEMINI_API_KEY",
            "credential_present": True,
            "provider_verification_enabled": True,
            "required_for_release": False,
            "credential_value_persisted": False,
            "fake_model_responses_used": False,
            "live_provider_session_verified": True,
            "provider_model_execution_verified": True,
            "real_cli_binary_executed": True,
            "real_tool_execution_verified": True,
            "real_extension_hook_execution_verified": True,
            "live_capture_verified": True,
            "provider_requests": requests,
            "provider_request_errors": request_errors,
            "tool_calls": int(tools.get("totalCalls") or 0),
            "tool_successes": int(tools.get("totalSuccess") or 0),
            "captured_events": len(events),
            "raw_private_secret_leakage": 0,
            "attempts": attempts,
            "elapsed_ms": round(elapsed_ms, 3),
            "runtime_enforced": False,
            "automatic_remediation": False,
        }
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

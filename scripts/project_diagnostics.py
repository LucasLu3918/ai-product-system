"""Aggregate bounded, read-only AIPS project diagnostics."""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

RUNTIMES = ("codex", "opencode", "claude-code", "gemini-cli", "unknown")
MAX_CHILD_SECONDS = 8
ADAPTER_STATUSES = {"AUTOMATIC", "MANUAL", "NOT_DETECTED", "CONFIGURED", "INSTALLED", "CONFLICT", "UNVERIFIED"}
ADAPTER_CAPABILITIES = {"CONTEXT_ALWAYS", "TURN_NATIVE", "TOOL_GUARDED", "UNSUPPORTED", "ADVISORY"}


def _run_json(command: list[str], *, cwd: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=MAX_CHILD_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "diagnostic_timeout"
    except OSError:
        return None, "diagnostic_unavailable"
    if result.returncode != 0:
        return None, "diagnostic_unavailable"
    try:
        value = json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError):
        return None, "diagnostic_invalid_output"
    return (value, None) if isinstance(value, dict) else (None, "diagnostic_invalid_output")


def _command(*parts: str) -> str:
    return shlex.join(list(parts))


def _check(
    check_id: str,
    status: str,
    reason_code: str,
    message: str,
    *,
    next_action: str | None = None,
    next_actions: list[dict[str, str]] | None = None,
    verification_command: str | None = None,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "reason_code": reason_code,
        "message": message,
        "next_action": next_action,
        "next_actions": next_actions or [],
        "verification_command": verification_command,
    }


def _intelligence_check(report: dict[str, Any] | None, error: str | None, project: Path) -> dict[str, Any]:
    status_command = _command("aips", "intelligence", "status", "--project", str(project))
    if report is None:
        return _check(
            "project_intelligence", "UNKNOWN", error or "diagnostic_unavailable",
            "無法讀取 Project Intelligence 狀態；診斷沒有包含子程序錯誤輸出。",
            verification_command=status_command,
        )

    state: dict[str, Any] = {}
    freshness: dict[str, Any] = {}
    if isinstance(report.get("state"), dict):
        state = report["state"]
    if isinstance(report.get("freshness"), dict):
        freshness = report["freshness"]
    readiness = str(state.get("readiness") or "UNKNOWN").upper()
    fresh = str(freshness.get("status") or state.get("freshness") or "UNKNOWN").upper()
    exists = report.get("exists") is True
    reason = str(report.get("reason_code") or "").lower()

    if not exists or reason in {"intelligence_missing", "project_intelligence_missing"}:
        bootstrap = _command("aips", "intelligence", "bootstrap", "--project", str(project))
        finalize = _command("aips", "intelligence", "finalize", "--project", str(project))
        return _check(
            "project_intelligence", "WARN", "intelligence_missing",
            "Project Intelligence 尚未建立。診斷保持唯讀；建立後仍需補足必要語意主題並完成審查。",
            next_action=f"需要時手動執行 {bootstrap}，補足必要語意主題後再執行 {finalize}。",
            next_actions=[
                {"action": "bootstrap", "command": bootstrap, "when": "使用者決定開始使用專案 Intelligence 時"},
                {"action": "complete_required_topics", "command": "依 bootstrap/status 顯示的必要主題補充經查證內容"},
                {"action": "finalize", "command": finalize},
                {"action": "verify", "command": status_command},
            ],
            verification_command=status_command,
        )
    if readiness == "PARTIAL":
        finalize = _command("aips", "intelligence", "finalize", "--project", str(project))
        return _check(
            "project_intelligence", "WARN", "intelligence_partial",
            "Project Intelligence 尚未達到 READY；請補足缺少的必要主題與證據。",
            next_action=f"依 status 顯示補足必要語意主題，再執行 {finalize}。",
            next_actions=[
                {"action": "inspect_missing_topics", "command": status_command},
                {"action": "complete_required_topics", "command": "依 status 顯示補足缺少的必要主題與證據"},
                {"action": "finalize", "command": finalize},
                {"action": "verify", "command": status_command},
            ],
            verification_command=status_command,
        )
    if fresh == "STALE":
        plan = _command("aips", "intelligence", "refresh-plan", "--project", str(project))
        refresh = _command("aips", "intelligence", "refresh", "--project", str(project))
        return _check(
            "project_intelligence", "WARN", "intelligence_stale",
            "Project Intelligence 已過期；先檢視刷新計畫，再由使用者決定是否更新。",
            next_action=f"執行 {plan} 檢視範圍；確認後再執行 {refresh}。",
            next_actions=[
                {"action": "review_refresh_scope", "command": plan},
                {"action": "refresh_after_review", "command": refresh, "when": "使用者審閱刷新範圍並決定更新後"},
                {"action": "verify", "command": status_command},
            ],
            verification_command=status_command,
        )
    if readiness == "READY" and fresh == "CURRENT":
        return _check(
            "project_intelligence", "PASS", "intelligence_ready_current",
            "Project Intelligence 為 READY 且 CURRENT。",
            verification_command=status_command,
        )
    if fresh == "BLOCKED" or readiness == "BLOCKED":
        return _check(
            "project_intelligence", "WARN", "intelligence_blocked",
            "Project Intelligence 回報 BLOCKED；請先檢視原因，不要略過必要檢查。",
            next_action=f"執行 {status_command} 檢視可恢復原因；只依明確原因選擇 bootstrap、refresh 或修正來源路徑。",
            next_actions=[
                {"action": "inspect_block_reason", "command": status_command},
                {"action": "diagnose_recovery", "command": _command("aips", "project", "diagnose", str(project))},
                {"action": "verify", "command": status_command},
            ],
            verification_command=status_command,
        )
    return _check(
        "project_intelligence", "UNKNOWN", "intelligence_state_unrecognized",
        "Project Intelligence 回傳未辨識的狀態；請檢視 status 報告。",
        verification_command=status_command,
    )


def _harness_check(report: dict[str, Any] | None, error: str | None, project: Path, runtime: str) -> dict[str, Any]:
    verify = _command("aips", "harness", "resolve", "--runtime", runtime, "--project", str(project), "--format", "json")
    if report is None:
        return _check(
            "runtime_harness", "UNKNOWN", error or "diagnostic_unavailable",
            "無法讀取 Runtime/Harness 設定；此結果不代表原生 Hook 已執行。",
            verification_command=verify,
        )
    runtime_data: dict[str, Any] = {}
    if isinstance(report.get("runtime"), dict):
        runtime_data = report["runtime"]
    actual_runtime = str(runtime_data.get("id") or "unknown")
    if actual_runtime == "unknown" or runtime_data.get("detected") is not True:
        return _check(
            "runtime_harness", "UNKNOWN", "runtime_not_detected",
            "目前無法辨識 Agent Runtime；原生 Context 與 Hook 執行狀態維持 UNVERIFIED。",
            next_action="在支援的 Agent Runtime 內執行，或使用 --runtime 明確指定後重新診斷。",
            verification_command=verify,
        )
    adapter_status = runtime_data.get("adapter_status")
    capability = runtime_data.get("capability")
    if not isinstance(adapter_status, str):
        return _check(
            "runtime_harness", "WARN", "adapter_state_missing",
            f"已辨識 {actual_runtime}，但沒有可讀取的 Adapter 狀態；原生效果仍為 UNVERIFIED。",
            next_action="檢視 AIPS Harness 安裝狀態，再於 Agent 內驗證實際 Context 與權限行為。",
            verification_command=verify,
        )
    if adapter_status not in ADAPTER_STATUSES or (
        capability is not None
        and (not isinstance(capability, str) or capability not in ADAPTER_CAPABILITIES)
    ):
        return _check(
            "runtime_harness", "WARN", "adapter_state_unrecognized",
            f"已辨識 {actual_runtime}，但 Adapter 回傳未辨識的狀態；原生效果維持 UNVERIFIED。",
            next_action="檢查 AIPS Harness 安裝狀態，再於 Agent 內驗證實際 Context 與權限行為。",
            verification_command=verify,
        )
    return _check(
        "runtime_harness", "PASS", "runtime_configuration_read",
        f"已讀取 {actual_runtime} Adapter 設定（status={adapter_status}, capability={capability or 'UNKNOWN'}）；這不證明 Hook 或工具在 Host 中實際執行。",
        verification_command=verify,
    )


def _doctor_check(root: Path, project: Path) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [str(root / "bin" / "aips"), "doctor"],
            cwd=project,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=MAX_CHILD_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _check("aips_doctor", "UNKNOWN", "diagnostic_timeout", "AIPS doctor 超過診斷時限；子程序輸出已丟棄。", verification_command="aips doctor")
    except OSError:
        return _check("aips_doctor", "UNKNOWN", "diagnostic_unavailable", "無法執行 AIPS doctor；子程序輸出已丟棄。", verification_command="aips doctor")
    if result.returncode == 0:
        return _check("aips_doctor", "PASS", "aips_doctor_pass", "AIPS doctor 的本機檢查通過。", verification_command="aips doctor")
    return _check(
        "aips_doctor", "WARN", "aips_doctor_needs_attention",
        "AIPS doctor 回報需注意項目；詳細輸出未複製到診斷報告。",
        next_action="在本機執行 aips doctor 檢視安全的詳細修復指引。",
        verification_command="aips doctor",
    )


def recovery_plan(checks: list[dict[str, Any]]) -> dict[str, Any]:
    """Order existing next-actions without executing or inventing repair authority."""
    steps: list[dict[str, Any]] = []
    blocked_by: list[str] = []
    for check in checks:
        if check["status"] == "PASS":
            continue
        blocked_by.append(check["reason_code"])
        actions = check.get("next_actions") or []
        if not actions and check.get("verification_command"):
            actions = [{"action": "inspect", "command": check["verification_command"]}]
        previous = None
        for action in actions:
            action_id = f"{check['id']}:{len(steps) + 1}:{action['action']}"
            state_write = action["action"] in {"bootstrap", "finalize", "refresh_after_review"}
            manual = action["action"] == "complete_required_topics"
            steps.append({
                "id": action_id, "check_id": check["id"],
                "reason_code": check["reason_code"], **action,
                "depends_on": [previous] if previous else [],
                "operation": "derived_state_write" if state_write else "manual_review" if manual else "read_only",
                "authorization": "APPROVED_TASK_SCOPE_REQUIRED" if state_write else "NONE",
                "automatic": False,
            })
            previous = action_id
    return {"status": "NO_ACTIONS" if not blocked_by else "REVIEW_REQUIRED",
            "blocked_by": blocked_by, "steps": steps, "execution_authorized": False}


def diagnose(project: Path, runtime: str) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    py = sys.executable
    pi, pi_error = _run_json(
        [py, str(root / "scripts" / "project_intelligence.py"), "status", "--project", str(project), "--format", "json"],
        cwd=project,
    )
    harness, harness_error = _run_json(
        [py, str(root / "scripts" / "harness_resolve.py"), "--runtime", runtime, "--cwd", str(project), "--project", str(project), "--format", "json"],
        cwd=project,
    )
    mcp, mcp_error = _run_json(
        [py, str(root / "scripts" / "mcp_server.py"), "inspect"],
        cwd=project,
    )
    checks = [
        _doctor_check(root, project),
        _intelligence_check(pi, pi_error, project),
        _harness_check(harness, harness_error, project, runtime),
    ]
    if mcp is None:
        checks.append(_check(
            "mcp_static_capability", "UNKNOWN", mcp_error or "diagnostic_unavailable",
            "無法讀取本機 MCP 靜態能力；這項檢查不會連線或啟動 MCP Host。",
            next_action="檢查 AIPS Runtime 依賴後重新執行；此命令不會安裝依賴。",
            verification_command=_command("aips", "mcp", "inspect"),
        ))
    else:
        server: dict[str, Any] = {}
        if isinstance(mcp.get("server"), dict):
            server = mcp["server"]
        checks.append(_check(
            "mcp_static_capability", "PASS", "mcp_static_capability_available",
            f"本機 MCP 靜態能力清單可讀取（transport={server.get('transport', 'UNKNOWN')}）；未測試 Host 連線或工具執行。",
            verification_command=_command("aips", "mcp", "inspect"),
        ))

    statuses = {item["status"] for item in checks}
    overall = "NEEDS_ATTENTION" if "WARN" in statuses else ("UNKNOWN" if "UNKNOWN" in statuses else "READY")
    return {
        "schema_version": 1,
        "status": overall,
        "read_only": True,
        "project": {"mode": "ATTACHED" if (project / ".ai").is_dir() else "EPHEMERAL"},
        "runtime": runtime,
        "checks": checks,
        "recovery_plan": recovery_plan(checks),
        "limitations": [
            "診斷不會建立、刷新、索引、附加或修復 Project Intelligence。",
            "原生 Hook、工具與 MCP Host 連線狀態維持 UNVERIFIED；靜態設定不是實機執行證據。",
        ],
    }


def _text(report: dict[str, Any]) -> str:
    lines = [
        "AIPS Project Diagnostics",
        f"Status: {report['status']}",
        f"Project mode: {report['project']['mode']}",
        f"Runtime: {report['runtime']}",
    ]
    for item in report["checks"]:
        lines.append(f"\n[{item['status']}] {item['id']} — {item['message']}")
        lines.append(f"Reason: {item['reason_code']}")
        if item.get("next_action"):
            lines.append(f"Next: {item['next_action']}")
        for action in item.get("next_actions") or []:
            when = f"（{action['when']}）" if action.get("when") else ""
            lines.append(f"Action: {action.get('action', 'next')} — {action.get('command', '')}{when}")
        if item.get("verification_command"):
            lines.append(f"Verify: {item['verification_command']}")
    plan = report["recovery_plan"]
    lines.extend(["", f"Recovery plan: {plan['status']} (no actions executed)"])
    for index, step in enumerate(plan["steps"], 1):
        lines.append(f"{index}. {step['command']} [{step['operation']}; {step['authorization']}]")
    lines.extend(["", "Limitations:", *[f"- {item}" for item in report["limitations"]]])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="Existing project directory")
    parser.add_argument("--runtime", choices=RUNTIMES)
    parser.add_argument("--format", choices=("text", "yaml", "json"), default="text")
    args = parser.parse_args()
    project = Path(args.project).expanduser().resolve()
    if not project.is_dir():
        print("ERROR: project path must be an existing directory", file=sys.stderr)
        return 2

    runtime = args.runtime
    if runtime is None:
        env = os.environ
        runtime = "opencode" if env.get("OPENCODE") else (
            "gemini-cli" if env.get("GEMINI_CWD") or env.get("GEMINI_PROJECT_DIR") else (
                "claude-code" if env.get("CLAUDE_PROJECT_DIR") or env.get("CLAUDE_CODE") else (
                    "codex" if env.get("CODEX_HOME") else "unknown"
                )
            )
        )
    report = diagnose(project, runtime)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.format == "yaml":
        print(yaml.safe_dump(report, sort_keys=False, allow_unicode=True).rstrip())
    else:
        print(_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

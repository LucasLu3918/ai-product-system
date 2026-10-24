"""Shared error types for local creative execution modules."""
from __future__ import annotations

import re
import uuid
from typing import Any

RECOVERY = {
    "resource_profile_not_provided": "請在受信任 Runtime 設定中提供 Resource Authorization Profile，再重新執行。",
    "resource_profile_missing": "確認 Profile 路徑與檔案存在；不要放寬 default-deny。",
    "resource_profile_unreadable": "檢查 Profile 檔案權限，修正後重新執行。",
    "resource_profile_format_invalid": "修正 Profile 的 UTF-8 YAML 格式後重新驗證。",
    "resource_profile_schema_invalid": "依 Resource Authorization Profile Schema 修正欄位後重新驗證。",
    "resource_profile_outside_project": "將 Profile 移到專案內，並設定受信任的相對路徑。",
    "selector_mismatch": "確認 Resource ID、種類與核准 selector 完全符合。",
    "grant_kind_mismatch": "使用核准的 Resource kind，或請 Human 調整授權 Profile。",
    "operation_not_granted": "請求的操作未授權；取得核准後再重試。",
    "network_not_allowed": "此 Grant 禁止網路存取；改用已核准的本機資源。",
    "destination_constraint_mismatch": "確認目的地、Port、Method 與 Path 均在核准限制內。",
    "comfy_redirect_refused": "檢查本機 ComfyUI 位址；AIPS 不會跟隨重新導向。",
    "comfy_endpoint_invalid": "使用明確的 loopback IP 與核准的本機 Port。",
    "provider_http_error": "檢查本機 Provider 狀態；確認後再由使用者明確重試。",
    "comfy_unavailable": "啟動或修復固定 loopback 的本機 ComfyUI，再執行唯讀查詢。",
    "comfy_model_unavailable": "檢查 ComfyUI 本機模型清單與 Bundle 的模型名稱。",
    "comfy_textgenerate_schema_invalid": "檢查本機 /object_info/TextGenerate 與固定 workflow 輸入；修正 schema 相容性後重跑唯讀 preflight。",
    "comfy_final_payload_invalid": "檢查最終 ComfyUI workflow 是否仍符合 preflight 綁定的節點、欄位與連線。",
    "comfy_execution_failed": "依節點 ID 與安全摘要檢查本機 ComfyUI workflow；確認 queue/history 後再由使用者明確重試。",
    "hardware_backend_dtype_not_smoke_verified": "檢查模型精度；只有實際本機推論成功後才可標記相容。",
    "resource_profile_invalid": "檢查 Resource Authorization Profile 格式與專案路徑。",
    "runtime_capability_unknown": "確認 Host adapter 的實際 enforcement 能力後重新執行。",
    "destination_not_allowlisted": "選擇政策明列的目的地，並重新核對授權範圍。",
    "effective_sal_unknown": "先完成資料風險分類，再重新評估此動作。",
    "policy_allow": "條件符合；依原本流程繼續。",
    "policy_denied": "檢查 Runtime Policy 規則與核准範圍；取得授權前不要重試。",
    "approval_required": "取得符合此 Action、目的地、資料標籤及期限的 Human 核准。",
    "runtime_policy_blocked": "補齊 enforcement 或 sandbox 證據後重新評估。",
}

# Only status-oriented, bounded local inventory fields may cross the native
# tool boundary. In particular, provider bodies, filesystem paths, prompts,
# command arguments, and credentials are never copied into diagnostics.
_SAFE_DIAGNOSTIC_KEYS = {
    "http_status", "providers", "mflux", "mflux_health_summary", "comfyui",
    "model_status", "readiness", "generation_executed", "external_image_egress",
    "model_recommendation", "status", "reason_code", "available", "health_status",
    "capability_status", "version_status", "version", "failure_type", "exit_code",
    "command", "configured", "endpoint", "node_capabilities", "model_catalog",
    "phase", "source", "retryable", "trace_id", "recovery", "action",
    "recommended_action", "runtime", "model", "preflight", "inference",
    "healthy_commands", "total_commands", "warning", "warnings", "evidence_status",
    "backend", "accelerator_backend", "backend_capability", "mps_runtime_probe",
    "model_precision_class", "host", "architecture", "os", "weight_dtypes",
    "node_id", "node_type", "exception_type", "reason_summary", "field",
}


def _safe_diagnostic(value: Any, *, depth: int = 0) -> Any:
    if depth > 5:
        return None
    if isinstance(value, dict):
        output = {}
        for key, item in list(value.items())[:100]:
            if key == "providers" and isinstance(item, dict):
                output[key] = {
                    provider: _safe_diagnostic(details, depth=depth + 1)
                    for provider, details in list(item.items())[:2]
                    if provider in {"mflux_local", "comfyui_local"} and isinstance(details, dict)
                }
                continue
            if not isinstance(key, str) or key not in _SAFE_DIAGNOSTIC_KEYS:
                continue
            output[key] = _safe_diagnostic(item, depth=depth + 1)
        return output
    if isinstance(value, (list, tuple)):
        return [_safe_diagnostic(item, depth=depth + 1) for item in value[:100]]
    if isinstance(value, str):
        return redact(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return None


def redact(value: str) -> str:
    value = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", value)
    value = re.sub(r"(?i)(token|api[_-]?key|password|secret)=([^\s&]+)", r"\1=[REDACTED]", value)
    value = re.sub(r"(?:/Users|/home)/[^\s:]+", "[LOCAL_PATH]", value)
    return value[:500]


def error_payload(*, status: str, phase: str, reason_code: str, source: str,
                  retryable: bool = False, recovery_action: str | None = None,
                  message: str | None = None, trace_id: str | None = None,
                  diagnostics: dict[str, Any] | None = None) -> dict[str, Any]:
    safe_diagnostics = _safe_diagnostic(diagnostics or {})
    if not isinstance(safe_diagnostics, dict):
        safe_diagnostics = {}
    if "http_status" in safe_diagnostics:
        value = safe_diagnostics["http_status"]
        safe_diagnostics["http_status"] = value if isinstance(value, int) and 100 <= value <= 599 else None
    return {
        "status": status,
        "phase": phase,
        "reason_code": reason_code,
        "source": source,
        "retryable": bool(retryable),
        "trace_id": trace_id or str(uuid.uuid4()),
        "recovery": {"action": RECOVERY.get(reason_code, recovery_action or "請檢查本機設定與安全限制後再重試。"),
                     "code": recovery_action},
        "message": redact(message) if message else None,
        "diagnostics": safe_diagnostics,
    }


class Blocked(ValueError):
    def __init__(self, reason_code: str, message: str, diagnostics: dict[str, Any] | None = None,
                 *, phase: str = "creative_execution", source: str = "creative"):
        super().__init__(message)
        self.reason_code = reason_code
        self.diagnostics = diagnostics or {}
        self.phase = phase
        self.source = source

    def to_payload(self) -> dict[str, Any]:
        return error_payload(status="BLOCKED", phase=self.phase, reason_code=self.reason_code,
                             source=self.source, message=str(self), diagnostics=self.diagnostics)

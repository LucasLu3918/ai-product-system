import importlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_validation_started = time.monotonic()
_timings: list[dict[str, object]] = []


def _record_timing(name: str, started: float, status: str) -> None:
    _timings.append({
        "name": name,
        "status": status,
        "duration_ms": int((time.monotonic() - started) * 1000),
    })


def _write_timing_report(status: str) -> None:
    destination = os.environ.get("AIPS_VALIDATION_TIMING_REPORT")
    if destination:
        Path(destination).write_text(json.dumps({
            "version": 1,
            "status": status,
            "total_duration_ms": int((time.monotonic() - _validation_started) * 1000),
            "checks": _timings,
        }, indent=2) + "\n", encoding="utf-8")


def _timed_import(name: str):
    started = time.monotonic()
    try:
        module = importlib.import_module(f"validation.{name}")
    except BaseException:
        _record_timing(f"validation.{name}", started, "FAIL")
        _write_timing_report("FAIL")
        raise
    _record_timing(f"validation.{name}", started, "PASS")
    return module


def _append_validation_git_config(key: str, value: str) -> None:
    raw_count = os.environ.get("GIT_CONFIG_COUNT", "0")
    try:
        count = int(raw_count)
    except ValueError as exc:
        raise RuntimeError(f"invalid inherited GIT_CONFIG_COUNT: {raw_count!r}") from exc
    os.environ[f"GIT_CONFIG_KEY_{count}"] = key
    os.environ[f"GIT_CONFIG_VALUE_{count}"] = value
    os.environ["GIT_CONFIG_COUNT"] = str(count + 1)


def _install_validation_global_git_config() -> tempfile.TemporaryDirectory[str]:
    config_dir = tempfile.TemporaryDirectory(prefix="aips-validation-git-config-")
    config_path = Path(config_dir.name) / "gitconfig"
    config_path.write_text(
        """[gc]
    auto = 0
    autoDetach = false
[maintenance]
    auto = false
    autoDetach = false
""",
        encoding="utf-8",
    )
    os.environ["GIT_CONFIG_GLOBAL"] = str(config_path)
    os.environ["GIT_CONFIG_NOSYSTEM"] = "1"
    return config_dir


_VALIDATION_GIT_CONFIG_DIR = _install_validation_global_git_config()
_append_validation_git_config("gc.auto", "0")
_append_validation_git_config("gc.autoDetach", "false")
_append_validation_git_config("maintenance.auto", "false")
_append_validation_git_config("maintenance.autoDetach", "false")

static_contracts = _timed_import("static_contracts")
for name in (
    "runtime_contracts", "visual_render_contracts", "performance_evidence_contracts",
    "creative_evidence_contracts", "product_delivery_contracts", "evolution_radar_contracts",
    "evolution_governance_contracts", "documentation_sync_contracts",
    "documentation_audience_contracts", "documentation_placement_contracts", "governance_resume",
    "conformance_isolation", "ears_requirement_contracts", "planning_package_contracts",
):
    _timed_import(name)
implementation_profile_contracts = _timed_import("implementation_profile_contracts")
openapi_generator_adapter_contracts = _timed_import("openapi_generator_adapter_contracts")
implementation_enforcement_contracts = _timed_import("implementation_enforcement_contracts")
openapi_contracts = _timed_import("openapi_contracts")
for name in (
    "retrieval_embedding_trial_contracts", "syntax_contracts", "scheduler_gate_contracts",
    "review_isolation_contracts", "branch_hygiene_contracts", "resource_authorization_contracts",
    "runtime_policy_contracts", "agent_anomaly_evaluation_contracts",
    "agent_observable_event_trial_contracts", "gemini_observable_event_capture_contracts",
    "gemini_runtime_verification_contracts", "gemini_provider_session_verification_contracts",
    "gemini_provider_session_workflow_contracts", "external_credential_guard_contracts",
    "repository_health_contracts", "mcp_interoperability_contracts",
    "evolution_effectiveness_contracts", "publish_preflight_contracts",
):
    _timed_import(name)
eval_interop_contracts = _timed_import("eval_interop_contracts")
telemetry_export_contracts = _timed_import("telemetry_export_contracts")

for evidence in (
    Path(__file__).parent / "validation/change_impact_resolution_contracts.py",
    Path(__file__).parent / "evidence/change_impact_resolution_lifecycle.py",
    Path(__file__).parent / "test_eval_interop.py",
    Path(__file__).parent / "evidence/eval_interop_lifecycle.py",
    Path(__file__).parent / "evidence/telemetry_export_lifecycle.py",
    Path(__file__).parent / "evidence/publication_transfer_lifecycle.py",
    Path(__file__).parent / "evidence/implementation_resolution_lifecycle.py",
    Path(__file__).parent / "evidence/implementation_enforcement_lifecycle.py",
    Path(__file__).parent / "evidence/openapi_contracts_lifecycle.py",
    Path(__file__).parent / "evidence/openapi_generator_adapter_lifecycle.py",
    Path(__file__).parent / "evidence/openapi_client_pilot_lifecycle.py",
):
    started = time.monotonic()
    result = subprocess.run([sys.executable, str(evidence)], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=False)
    _record_timing(str(evidence.relative_to(Path(__file__).resolve().parents[1])), started,
                   "PASS" if result.returncode == 0 else "FAIL")
    if result.returncode:
        _write_timing_report("FAIL")
        print(f"VALIDATION FAILED: {evidence.relative_to(Path(__file__).resolve().parents[1])}")
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(result.returncode)

errors = static_contracts.errors
errors.extend(eval_interop_contracts.errors)
errors.extend(telemetry_export_contracts.errors)
errors.extend(implementation_profile_contracts.errors)
errors.extend(openapi_generator_adapter_contracts.errors)
errors.extend(implementation_enforcement_contracts.errors)
errors.extend(openapi_contracts.errors)

if errors:
    _write_timing_report("FAIL")
    print("VALIDATION FAILED")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("VALIDATION PASSED")
_write_timing_report("PASS")
print(f"version={static_contracts.version}")
print(f"roles={len(static_contracts.roles.get('roles') or {})}")
print(f"skills={len(static_contracts.skills.get('skills') or {})}")
print(f"scenarios={len(static_contracts.scenarios)}")

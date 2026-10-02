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

_import_started = time.monotonic()
from validation import static_contracts as static_contracts
_record_timing("validation.static_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import runtime_contracts as runtime_contracts  # noqa: F401
_record_timing("validation.runtime_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import visual_render_contracts as visual_render_contracts  # noqa: F401
_record_timing("validation.visual_render_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import performance_evidence_contracts as performance_evidence_contracts  # noqa: F401
_record_timing("validation.performance_evidence_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import creative_evidence_contracts as creative_evidence_contracts  # noqa: F401
_record_timing("validation.creative_evidence_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import product_delivery_contracts as product_delivery_contracts  # noqa: F401
_record_timing("validation.product_delivery_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import evolution_radar_contracts as evolution_radar_contracts  # noqa: F401
_record_timing("validation.evolution_radar_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import evolution_governance_contracts as evolution_governance_contracts  # noqa: F401
_record_timing("validation.evolution_governance_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import documentation_sync_contracts as documentation_sync_contracts  # noqa: F401
_record_timing("validation.documentation_sync_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import documentation_audience_contracts as documentation_audience_contracts  # noqa: F401
_record_timing("validation.documentation_audience_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import documentation_placement_contracts as documentation_placement_contracts  # noqa: F401
_record_timing("validation.documentation_placement_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import governance_resume as governance_resume  # noqa: F401
_record_timing("validation.governance_resume", _import_started, "PASS")
_import_started = time.monotonic()
from validation import conformance_isolation as conformance_isolation  # noqa: F401
_record_timing("validation.conformance_isolation", _import_started, "PASS")
_import_started = time.monotonic()
from validation import ears_requirement_contracts as ears_requirement_contracts  # noqa: F401
_record_timing("validation.ears_requirement_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import planning_package_contracts as planning_package_contracts  # noqa: F401
_record_timing("validation.planning_package_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import implementation_profile_contracts as implementation_profile_contracts  # noqa: F401
_record_timing("validation.implementation_profile_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import openapi_generator_adapter_contracts as openapi_generator_adapter_contracts  # noqa: F401
_record_timing("validation.openapi_generator_adapter_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import implementation_enforcement_contracts as implementation_enforcement_contracts  # noqa: F401
_record_timing("validation.implementation_enforcement_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import openapi_contracts as openapi_contracts  # noqa: F401
_record_timing("validation.openapi_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import retrieval_embedding_trial_contracts as retrieval_embedding_trial_contracts  # noqa: F401
_record_timing("validation.retrieval_embedding_trial_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import syntax_contracts as syntax_contracts  # noqa: F401
_record_timing("validation.syntax_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import scheduler_gate_contracts as scheduler_gate_contracts  # noqa: F401
_record_timing("validation.scheduler_gate_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import review_isolation_contracts as review_isolation_contracts  # noqa: F401
_record_timing("validation.review_isolation_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import branch_hygiene_contracts as branch_hygiene_contracts  # noqa: F401
_record_timing("validation.branch_hygiene_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import resource_authorization_contracts as resource_authorization_contracts  # noqa: F401
_record_timing("validation.resource_authorization_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import runtime_policy_contracts as runtime_policy_contracts  # noqa: F401
_record_timing("validation.runtime_policy_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import agent_anomaly_evaluation_contracts as agent_anomaly_evaluation_contracts  # noqa: F401
_record_timing("validation.agent_anomaly_evaluation_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import agent_observable_event_trial_contracts as agent_observable_event_trial_contracts  # noqa: F401
_record_timing("validation.agent_observable_event_trial_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import gemini_observable_event_capture_contracts as gemini_observable_event_capture_contracts  # noqa: F401
_record_timing("validation.gemini_observable_event_capture_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import gemini_runtime_verification_contracts as gemini_runtime_verification_contracts  # noqa: F401
_record_timing("validation.gemini_runtime_verification_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import gemini_provider_session_verification_contracts as gemini_provider_session_verification_contracts  # noqa: F401
_record_timing("validation.gemini_provider_session_verification_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import gemini_provider_session_workflow_contracts as gemini_provider_session_workflow_contracts  # noqa: F401
_record_timing("validation.gemini_provider_session_workflow_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import external_credential_guard_contracts as external_credential_guard_contracts  # noqa: F401
_record_timing("validation.external_credential_guard_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import repository_health_contracts as repository_health_contracts  # noqa: F401
_record_timing("validation.repository_health_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import mcp_interoperability_contracts as mcp_interoperability_contracts  # noqa: F401
_record_timing("validation.mcp_interoperability_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import evolution_effectiveness_contracts as evolution_effectiveness_contracts  # noqa: F401
_record_timing("validation.evolution_effectiveness_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import publish_preflight_contracts as publish_preflight_contracts  # noqa: F401
_record_timing("validation.publish_preflight_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import eval_interop_contracts as eval_interop_contracts  # noqa: F401
_record_timing("validation.eval_interop_contracts", _import_started, "PASS")
_import_started = time.monotonic()
from validation import telemetry_export_contracts as telemetry_export_contracts  # noqa: F401
_record_timing("validation.telemetry_export_contracts", _import_started, "PASS")

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

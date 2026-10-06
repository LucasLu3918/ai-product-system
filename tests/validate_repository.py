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

_OPENAPI_EVIDENCE = {
    "implementation_enforcement_lifecycle.py",
    "openapi_contracts_lifecycle.py",
    "openapi_generator_adapter_lifecycle.py",
    "openapi_client_pilot_lifecycle.py",
    "openapi_cli_install_lifecycle.py",
}
_ci_plan = None
if os.environ.get("AIPS_CI_VALIDATION_PLAN"):
    try:
        _ci_plan = json.loads(Path(os.environ["AIPS_CI_VALIDATION_PLAN"]).read_text(encoding="utf-8"))
        if not isinstance(_ci_plan, dict) or _ci_plan.get("version") != 1:
            _ci_plan = None
    except (OSError, ValueError, TypeError):
        _ci_plan = None
    os.environ.pop("AIPS_CI_VALIDATION_PLAN", None)

from validation.registry import ERROR_AGGREGATION_ORDER, load_validators

validation_modules = load_validators(
    lambda name, started, status: _record_timing(name, started, status),
    needs_browser=_ci_plan is None or _ci_plan.get("needs_browser") is not False,
)
static_contracts = validation_modules["validation.static_contracts"]
implementation_profile_contracts = validation_modules["validation.implementation_profile_contracts"]
openapi_generator_adapter_contracts = validation_modules["validation.openapi_generator_adapter_contracts"]
implementation_enforcement_contracts = validation_modules["validation.implementation_enforcement_contracts"]
openapi_contracts = validation_modules["validation.openapi_contracts"]
eval_interop_contracts = validation_modules["validation.eval_interop_contracts"]
telemetry_export_contracts = validation_modules["validation.telemetry_export_contracts"]

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
    Path(__file__).parent / "evidence/openapi_cli_install_lifecycle.py",
    Path(__file__).parent / "evidence/runtime_recovery_lifecycle.py",
    Path(__file__).parent / "evidence/runtime_context_lifecycle.py",
    Path(__file__).parent / "evidence/aips_cli_module_extraction_lifecycle.py",
    Path(__file__).parent / "evidence/validator_registry_lifecycle.py",
    Path(__file__).parent / "evidence/system_facts_lifecycle.py",
    Path(__file__).parent / "evidence/ci_validation_plan_lifecycle.py",
    Path(__file__).parent / "evidence/validation_shadow_plan_lifecycle.py",
    Path(__file__).parent / "evidence/conformance_summary_lifecycle.py",
    Path(__file__).parent / "evidence/python_bootstrap_action_lifecycle.py",
    Path(__file__).parent / "evidence/version_policy_lifecycle.py",
    Path(__file__).parent / "evidence/module_extraction_lifecycle.py",
    Path(__file__).parent / "evidence/retrieval_relations_extraction_lifecycle.py",
    Path(__file__).parent / "evidence/maintenance_reliability_lifecycle.py",
    Path(__file__).parent / "evidence/release_channel_lifecycle.py",
):
    if evidence.name in _OPENAPI_EVIDENCE and _ci_plan is not None and _ci_plan.get("needs_openapi") is False:
        _record_timing(str(evidence.relative_to(Path(__file__).resolve().parents[1])), time.monotonic(), "SKIPPED: exact-path plan does not require OpenAPI")
        continue
    started = time.monotonic()
    evidence_env = os.environ.copy()
    evidence_env.pop("AIPS_CI_VALIDATION_PLAN", None)
    result = subprocess.run([sys.executable, str(evidence)], cwd=Path(__file__).resolve().parents[1], env=evidence_env, capture_output=True, text=True, check=False)
    _record_timing(str(evidence.relative_to(Path(__file__).resolve().parents[1])), started,
                   "PASS" if result.returncode == 0 else "FAIL")
    if result.returncode:
        _write_timing_report("FAIL")
        print(f"VALIDATION FAILED: {evidence.relative_to(Path(__file__).resolve().parents[1])}")
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(result.returncode)

errors: list[str] = []
for module_name in ERROR_AGGREGATION_ORDER:
    errors.extend(validation_modules[module_name].errors)

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

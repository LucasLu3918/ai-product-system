import os
from pathlib import Path
import tempfile


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

from validation import static_contracts as static_contracts
from validation import runtime_contracts as runtime_contracts  # noqa: F401
from validation import visual_render_contracts as visual_render_contracts  # noqa: F401
from validation import performance_evidence_contracts as performance_evidence_contracts  # noqa: F401
from validation import creative_evidence_contracts as creative_evidence_contracts  # noqa: F401
from validation import product_delivery_contracts as product_delivery_contracts  # noqa: F401
from validation import evolution_radar_contracts as evolution_radar_contracts  # noqa: F401
from validation import evolution_governance_contracts as evolution_governance_contracts  # noqa: F401
from validation import documentation_sync_contracts as documentation_sync_contracts  # noqa: F401
from validation import documentation_audience_contracts as documentation_audience_contracts  # noqa: F401
from validation import documentation_placement_contracts as documentation_placement_contracts  # noqa: F401
from validation import governance_resume as governance_resume  # noqa: F401
from validation import conformance_isolation as conformance_isolation  # noqa: F401
from validation import ears_requirement_contracts as ears_requirement_contracts  # noqa: F401
from validation import retrieval_embedding_trial_contracts as retrieval_embedding_trial_contracts  # noqa: F401
from validation import syntax_contracts as syntax_contracts  # noqa: F401
from validation import scheduler_gate_contracts as scheduler_gate_contracts  # noqa: F401
from validation import branch_hygiene_contracts as branch_hygiene_contracts  # noqa: F401
from validation import resource_authorization_contracts as resource_authorization_contracts  # noqa: F401
from validation import agent_anomaly_evaluation_contracts as agent_anomaly_evaluation_contracts  # noqa: F401
from validation import agent_observable_event_trial_contracts as agent_observable_event_trial_contracts  # noqa: F401
from validation import gemini_observable_event_capture_contracts as gemini_observable_event_capture_contracts  # noqa: F401
from validation import gemini_runtime_verification_contracts as gemini_runtime_verification_contracts  # noqa: F401
from validation import gemini_provider_session_verification_contracts as gemini_provider_session_verification_contracts  # noqa: F401
from validation import gemini_provider_session_workflow_contracts as gemini_provider_session_workflow_contracts  # noqa: F401
from validation import external_credential_guard_contracts as external_credential_guard_contracts  # noqa: F401
from validation import repository_health_contracts as repository_health_contracts  # noqa: F401
from validation import mcp_interoperability_contracts as mcp_interoperability_contracts  # noqa: F401
from validation import evolution_effectiveness_contracts as evolution_effectiveness_contracts  # noqa: F401
from validation import publish_preflight_contracts as publish_preflight_contracts  # noqa: F401

errors = static_contracts.errors

if errors:
    print("VALIDATION FAILED")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("VALIDATION PASSED")
print(f"version={static_contracts.version}")
print(f"roles={len((static_contracts.roles.get('roles') or {}))}")
print(f"skills={len((static_contracts.skills.get('skills') or {}))}")
print(f"scenarios={len(static_contracts.scenarios)}")

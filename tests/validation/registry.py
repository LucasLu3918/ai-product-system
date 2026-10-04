"""Ordered registry of repository validation modules."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import time
from typing import Callable


@dataclass(frozen=True)
class ValidatorSpec:
    module: str
    collect_errors: bool = False


VALIDATORS = (
    ValidatorSpec("validation.static_contracts", True),
    ValidatorSpec("validation.runtime_contracts", False),
    ValidatorSpec("validation.visual_render_contracts", False),
    ValidatorSpec("validation.performance_evidence_contracts", False),
    ValidatorSpec("validation.creative_evidence_contracts", False),
    ValidatorSpec("validation.product_delivery_contracts", False),
    ValidatorSpec("validation.evolution_radar_contracts", False),
    ValidatorSpec("validation.evolution_governance_contracts", False),
    ValidatorSpec("validation.documentation_sync_contracts", False),
    ValidatorSpec("validation.documentation_audience_contracts", False),
    ValidatorSpec("validation.documentation_placement_contracts", False),
    ValidatorSpec("validation.governance_resume", False),
    ValidatorSpec("validation.conformance_isolation", False),
    ValidatorSpec("validation.ears_requirement_contracts", False),
    ValidatorSpec("validation.planning_package_contracts", False),
    ValidatorSpec("validation.implementation_profile_contracts", True),
    ValidatorSpec("validation.openapi_generator_adapter_contracts", True),
    ValidatorSpec("validation.implementation_enforcement_contracts", True),
    ValidatorSpec("validation.openapi_contracts", True),
    ValidatorSpec("validation.retrieval_embedding_trial_contracts", False),
    ValidatorSpec("validation.syntax_contracts", False),
    ValidatorSpec("validation.scheduler_gate_contracts", False),
    ValidatorSpec("validation.review_isolation_contracts", False),
    ValidatorSpec("validation.branch_hygiene_contracts", False),
    ValidatorSpec("validation.resource_authorization_contracts", False),
    ValidatorSpec("validation.runtime_policy_contracts", False),
    ValidatorSpec("validation.agent_anomaly_evaluation_contracts", False),
    ValidatorSpec("validation.agent_observable_event_trial_contracts", False),
    ValidatorSpec("validation.gemini_observable_event_capture_contracts", False),
    ValidatorSpec("validation.gemini_runtime_verification_contracts", False),
    ValidatorSpec("validation.gemini_provider_session_verification_contracts", False),
    ValidatorSpec("validation.gemini_provider_session_workflow_contracts", False),
    ValidatorSpec("validation.external_credential_guard_contracts", False),
    ValidatorSpec("validation.repository_health_contracts", False),
    ValidatorSpec("validation.mcp_interoperability_contracts", False),
    ValidatorSpec("validation.evolution_effectiveness_contracts", False),
    ValidatorSpec("validation.publish_preflight_contracts", False),
    ValidatorSpec("validation.eval_interop_contracts", True),
    ValidatorSpec("validation.telemetry_export_contracts", True),
)


ERROR_AGGREGATION_ORDER = (
    "validation.static_contracts",
    "validation.eval_interop_contracts",
    "validation.telemetry_export_contracts",
    "validation.implementation_profile_contracts",
    "validation.openapi_generator_adapter_contracts",
    "validation.implementation_enforcement_contracts",
    "validation.openapi_contracts",
)


def load_validators(record_timing: Callable[[str, float, str], None]) -> dict[str, object]:
    """Import validators in their established order and retain timing labels."""
    loaded: dict[str, object] = {}
    for spec in VALIDATORS:
        started = time.monotonic()
        try:
            loaded[spec.module] = importlib.import_module(spec.module)
        except Exception:
            record_timing(spec.module, started, "FAIL")
            raise
        record_timing(spec.module, started, "PASS")
    return loaded

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
    paths: tuple[str, ...] = ()
    always_run: bool = True
    parallel_safe: bool = False


VALIDATORS = (
    ValidatorSpec("validation.static_contracts", True),
    ValidatorSpec("validation.versioning_contracts", True),
    ValidatorSpec("validation.system_facts_contracts", True),
    ValidatorSpec("validation.runtime_contracts", False),
    ValidatorSpec("validation.visual_render_contracts", False, ("scripts/visual_*", "scripts/browser_*", "tests/evidence/visual_*", "tests/evidence/browser_*", "config/project-visual-profile.yaml"), False),
    ValidatorSpec("validation.performance_evidence_contracts", False, ("scripts/performance_*", "tests/evidence/performance_*", "config/performance-*"), False),
    ValidatorSpec("validation.creative_evidence_contracts", False, ("scripts/creative_*", "tests/evidence/creative_*", "config/creative-*"), False),
    ValidatorSpec("validation.product_delivery_contracts", False, ("scripts/product_delivery*", "tests/evidence/product_delivery*", "orchestration/PRODUCT_DELIVERY.md"), False),
    ValidatorSpec("validation.evolution_radar_contracts", False, ("scripts/evolution_*", "config/evolution-*", "tests/evidence/evolution_*", "tests/validation/evolution_*", "orchestration/EVOLUTION_RADAR.md", "docs/human/EVOLUTION_RADAR.md", ".github/workflows/evolution-*"), False),
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
    ValidatorSpec("validation.branch_hygiene_contracts", False, ("scripts/branch_hygiene.py", "config/branch-*", "tests/evidence/branch_hygiene_lifecycle.py", "tests/validation/branch_hygiene_contracts.py", ".github/workflows/branch-hygiene.yml"), False),
    ValidatorSpec("validation.ci_validation_plan_contracts", False),
    ValidatorSpec("validation.version_policy_contracts", False, ("config/version-tag-policy.yaml", "config/github-ruleset-policy.yaml", "scripts/version_tag_policy.py", "scripts/github_ruleset_policy.py", "tests/evidence/version_policy_lifecycle.py", "tests/validation/version_policy_contracts.py"), False),
    ValidatorSpec("validation.resource_authorization_contracts", False),
    ValidatorSpec("validation.runtime_policy_contracts", False),
    ValidatorSpec("validation.agent_anomaly_evaluation_contracts", False),
    ValidatorSpec("validation.agent_observable_event_trial_contracts", False),
    ValidatorSpec("validation.gemini_observable_event_capture_contracts", False),
    ValidatorSpec("validation.gemini_runtime_verification_contracts", False),
    ValidatorSpec("validation.gemini_provider_session_verification_contracts", False),
    ValidatorSpec("validation.gemini_provider_session_workflow_contracts", False),
    ValidatorSpec("validation.external_credential_guard_contracts", False),
    ValidatorSpec("validation.repository_health_contracts", False, ("scripts/repository_health.py", "config/repository-health.yaml", "tests/evidence/repository_health_lifecycle.py", "tests/validation/repository_health_contracts.py"), False),
    ValidatorSpec("validation.mcp_interoperability_contracts", False),
    ValidatorSpec("validation.evolution_effectiveness_contracts", False, ("scripts/evolution_effectiveness.py", "scripts/evolution_radar_rollup.py", "config/evolution-effectiveness.yaml", "tests/evidence/evolution_*", "tests/validation/evolution_effectiveness_contracts.py", ".github/workflows/evolution-*"), False),
    ValidatorSpec("validation.maintenance_reliability_contracts", False),
    ValidatorSpec("validation.quality_ratchet_contracts", False, ("config/quality-ratchet.yaml", "scripts/quality_ratchet.py", "requirements-validation.txt", "constraints/tested.txt", "tests/evidence/release_channel_properties.py"), False),
    ValidatorSpec("validation.publish_preflight_contracts", False),
    ValidatorSpec("validation.eval_interop_contracts", True),
    ValidatorSpec("validation.telemetry_export_contracts", True),
    ValidatorSpec("validation.security_workflow_contracts", False, (".github/workflows/dependency-review.yml", ".github/workflows/scorecard.yml", "tests/validation/security_workflow_contracts.py"), False),
    ValidatorSpec("validation.validation_graduation_contracts", False, ("config/validation-scope.yaml", "config/validation-graduation.yaml", "scripts/validation_shadow_plan.py", "scripts/validation_graduation.py", "tests/evidence/validation_graduation_lifecycle.py", "tests/validation/validation_graduation_contracts.py"), False),
)


ERROR_AGGREGATION_ORDER = (
    "validation.static_contracts",
    "validation.versioning_contracts",
    "validation.system_facts_contracts",
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

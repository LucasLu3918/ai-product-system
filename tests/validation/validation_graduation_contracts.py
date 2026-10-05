from __future__ import annotations

from .static_contracts import ROOT, errors, load_yaml

config_path = ROOT / "config/validation-graduation.yaml"
script_path = ROOT / "scripts/validation_graduation.py"
lifecycle_path = ROOT / "tests/evidence/validation_graduation_lifecycle.py"
scope_path = ROOT / "config/validation-scope.yaml"

for path in (config_path, script_path, lifecycle_path, scope_path):
    if not path.is_file():
        errors.append(f"Missing validation graduation artifact: {path.relative_to(ROOT)}")

if config_path.is_file():
    config = load_yaml(config_path)
    execution = config.get("execution") or {}
    graduation = config.get("graduation") or {}
    if config.get("version") != 1 or config.get("mode") != "full_run_shadow":
        errors.append("Validation graduation must stay version 1 full-run shadow")
    if execution.get("selective_execution_enabled") is not False or execution.get("automatic_activation_authorized") is not False:
        errors.append("Validation graduation must not enable or authorize selective execution")
    if execution.get("human_decision_required") is not True:
        errors.append("Validation graduation requires a Human decision")
    if graduation.get("minimum_observation_days", 0) < 30 or graduation.get("minimum_unique_pull_requests", 0) < 1:
        errors.append("Validation graduation must require a 30-day window and a non-empty PR cohort")
    if graduation.get("maximum_false_negatives") != 0:
        errors.append("Validation graduation must require zero false negatives")
    if graduation.get("deterministic_full_audit_modulo", 0) < 2:
        errors.append("Validation graduation requires deterministic full-run audit sampling")

if scope_path.is_file():
    scope = load_yaml(scope_path)
    prefixes = set(scope.get("full_validation_path_prefixes") or [])
    if "tests/validation/" not in prefixes or "scripts/validation_" not in prefixes:
        errors.append("Validator and governance changes must force full validation in shadow planning")

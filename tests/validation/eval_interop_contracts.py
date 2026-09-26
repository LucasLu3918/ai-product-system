from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
errors: list[str] = []


def read_yaml(relative: str) -> dict:
    try:
        value = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - report a bounded contract failure to repository validation
        errors.append(f"{relative} failed to load: {type(exc).__name__}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{relative} must be a YAML mapping")
        return {}
    return value


evidence_schema = read_yaml("orchestration/schemas/external-eval-evidence.yaml")
if evidence_schema.get("security", {}).get("external_status_grants_release_authority") is not False:
    errors.append("external Eval evidence must not grant release authority")
if evidence_schema.get("security", {}).get("reject_unknown_and_executable_fields") is not True:
    errors.append("external Eval schema must reject unknown and executable fields")

profile_config = read_yaml("config/eval-profiles.yaml")
if profile_config.get("authority", {}).get("hard_gate_eligible") != "verified_canonical_deterministic_regression_only":
    errors.append("Eval profiles must reserve hard gates for canonical deterministic regressions")
for tool in ("pyrit", "promptfoo"):
    if profile_config.get("deep_scan", {}).get(tool, {}).get("enabled_by_default") is not False:
        errors.append(f"{tool} deep scan must remain disabled by default")

cli = (ROOT / "bin/aips").read_text(encoding="utf-8")
for command in ("import-promptfoo", "export-promptfoo", "import-pyrit", "verify-evidence", "profile", "promote-finding"):
    if command not in cli:
        errors.append(f"AIPS CLI is missing Eval interoperability command {command}")

adapter = (ROOT / "scripts/eval_interop.py").read_text(encoding="utf-8")
for contract in ("UniqueSafeLoader", "PROMPTFOO_ASSERTIONS", "ADVISORY_ONLY", "fingerprint_evidence", "Human review is required"):
    if contract not in adapter:
        errors.append(f"Eval interoperability adapter is missing contract marker {contract}")

if __name__ == "__main__":
    for error in errors:
        print(error)
    raise SystemExit(bool(errors))

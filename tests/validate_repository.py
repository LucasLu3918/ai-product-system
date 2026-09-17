from validation import static_contracts as static_contracts
from validation import runtime_contracts as runtime_contracts  # noqa: F401
from validation import visual_render_contracts as visual_render_contracts  # noqa: F401
from validation import performance_evidence_contracts as performance_evidence_contracts  # noqa: F401
from validation import creative_evidence_contracts as creative_evidence_contracts  # noqa: F401
from validation import product_delivery_contracts as product_delivery_contracts  # noqa: F401
from validation import evolution_radar_contracts as evolution_radar_contracts  # noqa: F401
from validation import governance_resume as governance_resume  # noqa: F401
from validation import conformance_isolation as conformance_isolation  # noqa: F401
from validation import syntax_contracts as syntax_contracts  # noqa: F401

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

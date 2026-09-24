from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from project_intelligence import validate_traversal_evidence
from retrieval_intelligence import risk_adaptive_policy


def main() -> int:
    errors: list[str] = []
    shallow = {"docs_style_test": 0, "private_leaf": 1}
    for risk_class, expected_depth in shallow.items():
        if risk_adaptive_policy(risk_class).get("required_depth") != expected_depth:
            errors.append(f"{risk_class} must require depth {expected_depth}")

    elevated = {
        "function_signature", "return_shape", "shared_dto", "api_contract",
        "db_schema", "event_schema", "shared_library", "security_boundary", "payment",
    }
    for risk_class in elevated:
        policy = risk_adaptive_policy(risk_class)
        if policy.get("required_depth", 0) < 2 or not policy.get("history_required"):
            errors.append(f"{risk_class} must require multi-hop traversal and selective history")

    doc = {
        "change": {"risk_class": "api_contract", "target_paths": []},
        "traversal": {
            "policy_version": 1,
            "policy": "risk-adaptive-bounded",
            "status": "COMPLETE",
            "required_depth": "invalid",
            "directions": ["consumers"],
            "truncated": False,
            "unresolved": [],
            "nodes": [],
        },
    }
    try:
        validation_errors = validate_traversal_evidence(doc, [])
        if not any("required_depth" in error for error in validation_errors):
            errors.append("malformed depth evidence must fail validation explicitly")
    except Exception as exc:  # contract: malformed YAML must return errors, not crash
        errors.append(f"malformed traversal evidence raised {type(exc).__name__}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: risk-adaptive traversal contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

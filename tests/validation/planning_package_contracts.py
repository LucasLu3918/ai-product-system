from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import tempfile

import yaml

from .static_contracts import ROOT, errors

sys.path.insert(0, str(ROOT / "scripts"))
from planning_package_validate import validate_package  # noqa: E402


def fixture(root: Path) -> Path:
    package = root / "planning"
    package.mkdir(parents=True)
    files = {
        "PRODUCT_RESEARCH.md": "# Research\n",
        "PRODUCT_PLAN.md": "# Product\n",
        "EXPERIENCE_DESIGN.md": "# Experience\nSCR-001\n",
        "VISUAL_SYSTEM.md": "# Visual\nVIS-001\n",
        "DOMAIN_MODEL.md": "# Domain\nDOM-001\n",
        "API_SPEC.md": "# API\nOP-001\n",
        "TECHNICAL_ARCHITECTURE.md": "# Architecture\n",
        "IMPLEMENTATION_PLAN.md": "# Implementation\n",
        "DECISIONS_ASSUMPTIONS.md": "# Decisions\n",
    }
    for relative, body in files.items():
        (package / relative).write_text(body, encoding="utf-8")
    (package / "REQUIREMENTS.yaml").write_text(yaml.safe_dump({
        "version": 1,
        "requirements": [{
            "id": "FR-001", "kind": "functional", "ears_pattern": "event_driven",
            "statement": "When a shopper requests an item, the Store shall add the item to the cart.",
            "source": "Accepted product decision",
            "acceptance_criteria": [{
                "id": "AC-001", "observable_result": "The cart contains the requested item.",
                "verification_method": "Deterministic test", "evidence_refs": [],
            }],
        }],
    }, sort_keys=False), encoding="utf-8")
    manifest = {
        "version": 1,
        "product": {"name": "sample", "planning_status": "PLANNING"},
        "approvals": {"planning": {"status": "PENDING", "evidence": None}, "implementation": {"status": "PENDING", "evidence": None}},
        "artifacts": {
            "product_research": {"path": "PRODUCT_RESEARCH.md", "applicability": "applicable", "status": "IN_PROGRESS", "depends_on": []},
            "product_plan": {"path": "PRODUCT_PLAN.md", "applicability": "applicable", "status": "IN_PROGRESS", "depends_on": [{"artifact": "product_research", "strength": "recommended"}]},
            "requirements": {"path": "REQUIREMENTS.yaml", "applicability": "applicable", "status": "IN_PROGRESS", "depends_on": [{"artifact": "product_plan", "strength": "required"}]},
            "experience_design": {"path": "EXPERIENCE_DESIGN.md", "applicability": "applicable", "status": "IN_PROGRESS", "depends_on": [{"artifact": "requirements", "strength": "required"}]},
            "visual_system": {"path": "VISUAL_SYSTEM.md", "applicability": "applicable", "status": "IN_PROGRESS", "depends_on": [{"artifact": "experience_design", "strength": "required"}]},
            "domain_model": {"path": "DOMAIN_MODEL.md", "applicability": "applicable", "status": "IN_PROGRESS", "depends_on": [{"artifact": "requirements", "strength": "required"}]},
            "api_spec": {"path": "API_SPEC.md", "applicability": "applicable", "status": "IN_PROGRESS", "depends_on": [{"artifact": "domain_model", "strength": "recommended"}]},
            "technical_architecture": {"path": "TECHNICAL_ARCHITECTURE.md", "applicability": "applicable", "status": "IN_PROGRESS", "depends_on": [{"artifact": "requirements", "strength": "required"}]},
            "implementation_plan": {"path": "IMPLEMENTATION_PLAN.md", "applicability": "applicable", "status": "IN_PROGRESS", "depends_on": [{"artifact": "technical_architecture", "strength": "required"}]},
            "decisions_assumptions": {"path": "DECISIONS_ASSUMPTIONS.md", "applicability": "applicable", "status": "IN_PROGRESS", "depends_on": []},
            "security": {"path": "security/SECURITY_PLAN.md", "applicability": "not_applicable", "status": "N/A", "reason": "No security-specific requirements."},
        },
        "traceability": [{
            "requirement_id": "FR-001", "acceptance_ids": ["AC-001"],
            "downstream": {
                "experience_design": {"applicable": True, "refs": ["SCR-001"]},
                "visual_system": {"applicable": True, "refs": ["VIS-001"]},
                "domain_model": {"applicable": True, "refs": ["DOM-001"]},
                "api_spec": {"applicable": True, "refs": ["OP-001"]},
                "security": {"applicable": False, "reason": "No security-specific behavior."},
                "verification": {"applicable": True, "refs": ["tests/sample_test.py"]},
            },
        }],
    }
    (package / "PLANNING_MANIFEST.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return package


with tempfile.TemporaryDirectory(prefix="aips-planning-package-contract-") as temp:
    package = fixture(Path(temp))
    manifest_path = package / "PLANNING_MANIFEST.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    valid = validate_package(package)
    if valid["status"] != "PASS":
        errors.append(f"valid Planning Package v2 fixture must pass: {valid['errors']}")

    def rejects(candidate: dict, expected: str, label: str) -> None:
        manifest_path.write_text(yaml.safe_dump(candidate, sort_keys=False), encoding="utf-8")
        if not any(expected in issue for issue in validate_package(package)["errors"]):
            errors.append(label)

    bad = deepcopy(manifest)
    bad["artifacts"]["security"]["reason"] = ""
    rejects(bad, "security.reason", "N/A artifacts must require an explanatory reason")

    bad = deepcopy(manifest)
    bad["artifacts"]["product_plan"]["depends_on"] = [{"artifact": "requirements", "strength": "required"}]
    rejects(bad, "dependency cycle", "manifest must reject cyclic artifact dependencies")

    bad = deepcopy(manifest)
    bad["artifacts"]["product_plan"]["path"] = "../outside.md"
    rejects(bad, "must stay inside", "manifest must reject parent traversal in artifact paths")

    bad = deepcopy(manifest)
    bad["artifacts"]["requirements"]["depends_on"][0]["artifact"] = "missing_artifact"
    rejects(bad, "unknown artifact", "manifest must reject unknown artifact dependencies")

    bad = deepcopy(manifest)
    bad["artifacts"]["requirements"]["status"] = "READY_FOR_REVIEW"
    rejects(bad, "is not ready", "ready artifacts must have ready required dependencies")

    bad = deepcopy(manifest)
    bad["traceability"][0]["downstream"]["api_spec"]["refs"] = ["OP-404"]
    rejects(bad, "unknown OP reference", "traceability must reject unknown downstream operation IDs")

    bad = deepcopy(manifest)
    bad["traceability"] = []
    rejects(bad, "orphan requirement FR-001", "manifest must identify requirements without traceability mappings")

    bad = deepcopy(manifest)
    bad["product"]["planning_status"] = "GATE_1_APPROVED"
    rejects(bad, "human approval evidence", "Gate 1 approval status must require explicit human evidence")

    bad = deepcopy(manifest)
    bad["product"]["planning_status"] = "IMPLEMENTATION_READY"
    bad["approvals"]["planning"] = {"status": "APPROVED", "evidence": "human:gate-1"}
    rejects(bad, "separate human approval", "Gate 2 readiness must require separate human evidence")

    bad = deepcopy(manifest)
    bad["product"]["planning_status"] = "GATE_1_READY"
    rejects(bad, "GATE_1_READY requires", "Gate 1 readiness must require every applicable artifact to be ready")

    bad = deepcopy(manifest)
    bad["product"]["planning_status"] = "GATE_1_APPROVED"
    bad["approvals"]["planning"] = {"status": "APPROVED", "evidence": {"auto": True}}
    rejects(bad, "human approval evidence", "gate evidence must be an explicit human-readable reference")

    req_path = package / "REQUIREMENTS.yaml"
    req_doc = yaml.safe_load(req_path.read_text(encoding="utf-8"))
    req_doc["requirements"][0]["acceptance_criteria"] = []
    req_path.write_text(yaml.safe_dump(req_doc, sort_keys=False), encoding="utf-8")
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    if not any("acceptance_criteria" in issue for issue in validate_package(package)["errors"]):
        errors.append("validator must reuse requirement-to-acceptance contract checks")

if not (ROOT / "templates/planning-package/PLANNING_MANIFEST.yaml").is_file():
    errors.append("Missing Planning Package manifest template")

# Capability reuse and stable cross-artifact references are part of the deterministic contract.
research_skill = (ROOT / "skills/product/product-research/SKILL.md").read_text(encoding="utf-8")
discovery_skill = (ROOT / "skills/product/product-discovery/SKILL.md").read_text(encoding="utf-8")
data_model_skill = (ROOT / "skills/database/data-modeling/SKILL.md").read_text(encoding="utf-8")
if "evidence-backed product and market research" not in research_skill.lower() or "known constraints" not in research_skill.lower() or "unknowns" not in discovery_skill.lower():
    errors.append("product research must preserve evidence, constraints and unknowns across discovery")
if "domain concepts" not in data_model_skill.lower() or "DOMAIN_MODEL.md" not in data_model_skill or "database" not in (ROOT / "roles/database-engineer/ROLE.md").read_text(encoding="utf-8").lower():
    errors.append("data modeling must integrate with the existing database role")
for artifact, prefix in (("EXPERIENCE_DESIGN.md", "SCR-"), ("VISUAL_SYSTEM.md", "VIS-"), ("DOMAIN_MODEL.md", "DOM-"), ("API_SPEC.md", "OP-")):
    content = (ROOT / "templates/planning-package" / artifact).read_text(encoding="utf-8")
    if prefix not in content:
        errors.append(f"{artifact} must define stable {prefix} references")
domain_index = yaml.safe_load((ROOT / "references/domains/INDEX.yaml").read_text(encoding="utf-8"))
if domain_index.get("policy", {}).get("default_loading") != "overview_only" or domain_index.get("policy", {}).get("load_details_on_trigger") is not True:
    errors.append("domain references must remain selectively loaded by trigger")
expected_modules = {"catalog_inventory", "cart_checkout", "order_payment_refund", "operations"}
if set((domain_index.get("domains", {}).get("ecommerce", {}).get("modules") or {})) != expected_modules:
    errors.append("e-commerce pack must expose its bounded reference modules")

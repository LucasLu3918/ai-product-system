from pathlib import Path
import re
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
errors = []

def load_yaml(path: Path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"YAML parse failed: {path.relative_to(ROOT)}: {exc}")
        return None

yaml_files = [
    "roles/INDEX.yaml",
    "skills/INDEX.yaml",
    "capabilities/INDEX.yaml",
    "orchestration/schemas/context-manifest.yaml",
    "orchestration/schemas/workspace-state.yaml",
    "orchestration/schemas/execution-profile.yaml",
    "orchestration/schemas/risk-profile.yaml",
    "templates/artifact-contract.yaml",
    "templates/change-boundary.yaml",
    "templates/project/architecture-profile.yaml",
    "templates/workspace/MANIFEST.yaml",
    "templates/workspace/STATE.yaml",
    "templates/workspace/SYSTEM.yaml",
]
for rel in yaml_files:
    p = ROOT / rel
    if not p.exists():
        errors.append(f"Missing required YAML: {rel}")
    else:
        load_yaml(p)

roles = load_yaml(ROOT / "roles/INDEX.yaml") or {}
for role_id, meta in (roles.get("roles") or {}).items():
    path = ROOT / "roles" / meta["path"]
    if not path.exists():
        errors.append(f"Role path missing for {role_id}: roles/{meta['path']}")

skills = load_yaml(ROOT / "skills/INDEX.yaml") or {}
for skill_id, meta in (skills.get("skills") or {}).items():
    path = ROOT / "skills" / meta["path"]
    if not path.exists():
        errors.append(f"Skill path missing for {skill_id}: skills/{meta['path']}")
    mr = meta.get("model_requirements") or {}
    for key in ("reasoning", "coding", "reliability", "minimum_tier", "preferred_tier"):
        if key not in mr:
            errors.append(f"Skill {skill_id} missing model_requirements.{key}")
    if isinstance(mr.get("minimum_tier"), int) and isinstance(mr.get("preferred_tier"), int):
        if mr["minimum_tier"] > mr["preferred_tier"]:
            errors.append(f"Skill {skill_id}: minimum_tier exceeds preferred_tier")

required_files = [
    "AGENTS.md", "SYSTEM.md", "README.md", "USER_GUIDE.md", "CHANGELOG.md", "VERSION",
    "core/CONSTITUTION.md", "core/PRINCIPLES.md", "core/GOVERNANCE.md", "core/DECISIONS.md",
    "orchestration/ORCHESTRATOR.md", "orchestration/MODEL_ROUTING.md",
    "orchestration/INSTRUCTION_RESOLUTION.md", "orchestration/WORKSPACE_STATE.md",
    "orchestration/PLANNING_PACKAGE.md", "orchestration/SYSTEM_SELF_IMPROVEMENT.md",
    "docs/ARCHITECTURE.md", "docs/MAINTENANCE.md", "docs/INSTALLATION.md", "docs/SECURITY_ASSURANCE.md",
    "examples/EXAMPLES.md", "work-modes/README.md",
    "templates/system-improvement-review.md", "templates/constitutional-change-proposal.md",
    "templates/core-change-proposal.md", "templates/git-publish-proposal.md",
    "bin/aips", "scripts/bootstrap.sh", "requirements.txt", ".github/workflows/validate.yml",
]
security_templates = [
    "templates/security/SECURITY_PLAN.md",
    "templates/security/THREAT_MODEL.md",
    "templates/security/ABUSE_CASES.md",
    "templates/security/SECURITY_REVIEW.md",
]
planning_templates = [
    "templates/planning-package/PLANNING_INDEX.md",
    "templates/planning-package/PRODUCT_PLAN.md",
    "templates/planning-package/EXPERIENCE_DESIGN.md",
    "templates/planning-package/VISUAL_SYSTEM.md",
    "templates/planning-package/TECHNICAL_ARCHITECTURE.md",
    "templates/planning-package/API_SPEC.md",
    "templates/planning-package/IMPLEMENTATION_PLAN.md",
    "templates/planning-package/DECISIONS_ASSUMPTIONS.md",
]
for rel in required_files + planning_templates + security_templates:
    if not (ROOT / rel).exists():
        errors.append(f"Missing required file: {rel}")

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").exists() else ""
if not re.fullmatch(r"\d+\.\d+\.\d+", version):
    errors.append(f"VERSION is not SemVer x.y.z: {version!r}")

changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8") if (ROOT / "CHANGELOG.md").exists() else ""
if version and f"## {version}" not in changelog:
    errors.append(f"CHANGELOG.md has no section for VERSION {version}")

architecture = (ROOT / "docs/ARCHITECTURE.md").read_text(encoding="utf-8") if (ROOT / "docs/ARCHITECTURE.md").exists() else ""
if "mermaid" not in architecture or "flowchart" not in architecture:
    errors.append("docs/ARCHITECTURE.md must contain source-controlled Mermaid diagrams")
for phrase in ("Update preflight", "Primary planning package", "Risk-proportional security assurance"):
    if phrase not in architecture:
        errors.append(f"docs/ARCHITECTURE.md missing section: {phrase}")

system = (ROOT / "SYSTEM.md").read_text(encoding="utf-8") if (ROOT / "SYSTEM.md").exists() else ""
for phrase in ("System Update Preflight", "System Self-Improvement", "Core Change Approval Gate", "Git Publish Approval Gate", "Primary Planning Detection", "Security / Reliability Assurance", "Documentation Impact Gate"):
    if phrase not in system:
        errors.append(f"SYSTEM.md missing required behavior: {phrase}")

planning = (ROOT / "orchestration/PLANNING_PACKAGE.md").read_text(encoding="utf-8") if (ROOT / "orchestration/PLANNING_PACKAGE.md").exists() else ""
for phrase in ("Workspace first", "Gate 1", "Gate 2", "Reproducibility standard"):
    if phrase not in planning:
        errors.append(f"PLANNING_PACKAGE.md missing: {phrase}")

scenarios = sorted((ROOT / "tests/scenarios").glob("*.md"))
if len(scenarios) < 20:
    errors.append(f"Expected at least 20 acceptance scenarios, found {len(scenarios)}")

security_doc = (ROOT / "docs/SECURITY_ASSURANCE.md").read_text(encoding="utf-8") if (ROOT / "docs/SECURITY_ASSURANCE.md").exists() else ""
for phrase in ("SAL 0", "SAL 4", "Critical risk floors", "Product baseline vs change impact", "Release Security Gate"):
    if phrase not in security_doc:
        errors.append(f"SECURITY_ASSURANCE.md missing: {phrase}")

for security_skill in ("threat-modeling", "authorization-security", "business-logic-abuse", "financial-integrity", "security-testing"):
    if security_skill not in (skills.get("skills") or {}):
        errors.append(f"Missing security skill in index: {security_skill}")


constitution = (ROOT / "core/CONSTITUTION.md").read_text(encoding="utf-8") if (ROOT / "core/CONSTITUTION.md").exists() else ""
for phrase in ("Protected Human Authority", "Truth and No Silent Assumptions", "Protected Safety Boundary", "Stop-the-Line", "Scope Integrity", "Explicit Approval for High-Risk Actions", "Amendment Protocol"):
    if phrase not in constitution:
        errors.append(f"CONSTITUTION.md missing protected article: {phrase}")

self_improvement = (ROOT / "orchestration/SYSTEM_SELF_IMPROVEMENT.md").read_text(encoding="utf-8") if (ROOT / "orchestration/SYSTEM_SELF_IMPROVEMENT.md").exists() else ""
for phrase in ("Self-Improvement Review", "Constitution Impact Check", "Lower-layer preference"):
    if phrase not in self_improvement:
        errors.append(f"SYSTEM_SELF_IMPROVEMENT.md missing: {phrase}")

for shell in ("bin/aips", "scripts/bootstrap.sh"):
    p = ROOT / shell
    if p.exists():
        result = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
        if result.returncode != 0:
            errors.append(f"Shell syntax failed: {shell}: {result.stderr.strip()}")

if errors:
    print("VALIDATION FAILED")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print("VALIDATION PASSED")
print(f"version={version}")
print(f"roles={len((roles.get('roles') or {}))}")
print(f"skills={len((skills.get('skills') or {}))}")
print(f"scenarios={len(scenarios)}")

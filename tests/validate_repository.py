from pathlib import Path
import re
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
errors = []

def load_yaml(path: Path):
    try:
        class UniqueKeyLoader(yaml.SafeLoader):
            pass

        def construct_mapping(loader, node, deep=False):
            mapping = {}
            for key_node, value_node in node.value:
                key = loader.construct_object(key_node, deep=deep)
                if key in mapping:
                    raise ValueError(f"duplicate key: {key!r}")
                mapping[key] = loader.construct_object(value_node, deep=deep)
            return mapping

        UniqueKeyLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            construct_mapping,
        )
        return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
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
    "orchestration/schemas/brand-profile.yaml",
    "templates/product/PRODUCT.yaml",
    "templates/delivery/RELEASE_READINESS.yaml",
    "templates/delivery/DEPLOYMENT_UNIT.yaml",
    "templates/creative/CREATIVE_DIRECTION.yaml",
    "templates/brand/BRAND_PROFILE.yaml",
    "templates/automation/AUTOMATION_CONTRACT.yaml",
    "references/creative/styles/INDEX.yaml",
    "references/creative/styles/quiet-premium.yaml",
    "references/creative/styles/editorial-minimal.yaml",
    "references/creative/styles/modern-bento.yaml",
    "references/creative/styles/japanese-minimal.yaml",
    "references/creative/styles/cinematic-dark.yaml",
    "references/creative/styles/soft-dimensional.yaml",
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
    "orchestration/CREATIVE_DIRECTION.md", "orchestration/BRAND_SYSTEM.md",
    "orchestration/CAPABILITY_INCUBATION.md", "orchestration/DETERMINISTIC_AUTOMATION.md",
    "orchestration/PRODUCT_DELIVERY.md", "orchestration/RELEASE_READINESS.md",
    "docs/ARCHITECTURE.md", "docs/MAINTENANCE.md", "docs/INSTALLATION.md", "docs/SECURITY_ASSURANCE.md",
    "docs/GETTING_STARTED.md", "docs/USER_GUIDE.md", "docs/DOCUMENTATION_MAP.md",
    "docs/ARCHITECTURE_OVERVIEW.md", "docs/assets/system-overview.svg",
    "docs/assets/product-delivery-overview.svg",
    "examples/EXAMPLES.md", "work-modes/README.md",
    "templates/system-improvement-review.md", "templates/constitutional-change-proposal.md",
    "templates/core-change-proposal.md", "templates/git-publish-proposal.md",
    "templates/capability-reuse-review.md",
    "templates/creative/CREATIVE_BRIEF.md", "templates/creative/REFERENCE_BOARD.md",
    "templates/creative/VISUAL_REVIEW.md",
    "templates/brand/BRAND_INDEX.md", "templates/brand/BRAND_FOUNDATION.md",
    "templates/brand/BRAND_IDENTITY.md", "templates/brand/LOGO_SYSTEM.md",
    "templates/brand/VERBAL_IDENTITY.md", "templates/brand/BRAND_APPLICATION.md",
    "templates/brand/BRAND_GOVERNANCE.md",
    "templates/product/PRODUCT_WORKSPACE.md",
    "templates/delivery/LOCAL_ENVIRONMENT.md", "templates/delivery/DEPLOYMENT_PLAN.md",
    "templates/delivery/RUNBOOK.md",
    "scripts/check_release_readiness.py",
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
for phrase in ("System Update Preflight", "System Self-Improvement", "Core Change Approval Gate", "Git Publish Approval Gate", "Primary Planning Detection", "Security / Reliability Assurance", "Creative and Brand routing", "Deterministic automation", "End-to-end product delivery", "Documentation Impact Gate"):
    if phrase not in system:
        errors.append(f"SYSTEM.md missing required behavior: {phrase}")

planning = (ROOT / "orchestration/PLANNING_PACKAGE.md").read_text(encoding="utf-8") if (ROOT / "orchestration/PLANNING_PACKAGE.md").exists() else ""
for phrase in ("Workspace first", "Gate 1", "Gate 2", "Reproducibility standard"):
    if phrase not in planning:
        errors.append(f"PLANNING_PACKAGE.md missing: {phrase}")

scenarios = sorted((ROOT / "tests/scenarios").glob("*.md"))
if len(scenarios) < 34:
    errors.append(f"Expected at least 34 acceptance scenarios, found {len(scenarios)}")

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


for creative_skill in ("creative-reference-research", "creative-calibration", "brand-foundation", "visual-quality-review"):
    if creative_skill not in (skills.get("skills") or {}):
        errors.append(f"Missing creative skill in index: {creative_skill}")

for rel, phrases in {
    "orchestration/CREATIVE_DIRECTION.md": ("Input priority", "Reference research", "Calibration", "Review"),
    "orchestration/BRAND_SYSTEM.md": ("Brand creation flow", "Brand package", "Future artifact routing", "Campaign override"),
    "orchestration/CAPABILITY_INCUBATION.md": ("Reuse Check", "Creation preference", "Progressive incubation", "Role promotion test"),
    "orchestration/DETERMINISTIC_AUTOMATION.md": ("Good candidates", "Tool lifetime", "Output contract", "Shell vs Python"),
    "orchestration/PRODUCT_DELIVERY.md": ("Lifecycle", "Product Workspace", "Deployment Units, not forced repositories", "Deployment automation", "Production completion"),
    "orchestration/RELEASE_READINESS.md": ("Required evidence", "Status", "Candidate integrity", "Post-deploy"),
}.items():
    text = (ROOT / rel).read_text(encoding="utf-8") if (ROOT / rel).exists() else ""
    for phrase in phrases:
        if phrase not in text:
            errors.append(f"{rel} missing: {phrase}")

style_index = load_yaml(ROOT / "references/creative/styles/INDEX.yaml") or {}
for style_id, meta in (style_index.get("styles") or {}).items():
    path = ROOT / "references/creative/styles" / meta["path"]
    if not path.exists():
        errors.append(f"Style path missing for {style_id}: {path.relative_to(ROOT)}")

human_docs = (
    "README.md",
    "docs/GETTING_STARTED.md",
    "docs/USER_GUIDE.md",
    "docs/INSTALLATION.md",
    "docs/ARCHITECTURE_OVERVIEW.md",
    "docs/DOCUMENTATION_MAP.md",
)
for rel in human_docs:
    text = (ROOT / rel).read_text(encoding="utf-8") if (ROOT / rel).exists() else ""
    if not re.search(r"[\u4e00-\u9fff]", text):
        errors.append(f"Human doc is expected to contain Traditional Chinese content: {rel}")

root_user_guide = (ROOT / "USER_GUIDE.md").read_text(encoding="utf-8") if (ROOT / "USER_GUIDE.md").exists() else ""
if len(root_user_guide) > 1200 or "docs/USER_GUIDE.md" not in root_user_guide:
    errors.append("Root USER_GUIDE.md should remain a short redirect to docs/USER_GUIDE.md")

svg = (ROOT / "docs/assets/system-overview.svg").read_text(encoding="utf-8") if (ROOT / "docs/assets/system-overview.svg").exists() else ""
if "<svg" not in svg or "AI Product System" not in svg:
    errors.append("Human architecture SVG is missing or invalid")

for mode_file in (ROOT / "work-modes").glob("*.md"):
    text = mode_file.read_text(encoding="utf-8")
    for role_id in re.findall(r"Default role:\s*`([a-z0-9-]+)`", text):
        if role_id not in (roles.get("roles") or {}):
            errors.append(f"{mode_file.relative_to(ROOT)} references unknown default role: {role_id}")


product_manifest = load_yaml(ROOT / "templates/product/PRODUCT.yaml") or {}
for key in ("product", "workspace", "deployment_units", "environments", "commands", "delivery", "observability"):
    if key not in product_manifest:
        errors.append(f"PRODUCT.yaml missing top-level key: {key}")

release_template = load_yaml(ROOT / "templates/delivery/RELEASE_READINESS.yaml") or {}
for key in ("status", "release", "build", "tests", "security", "staging", "approval", "blockers", "evidence"):
    if key not in release_template:
        errors.append(f"RELEASE_READINESS.yaml missing top-level key: {key}")

delivery_svg = (ROOT / "docs/assets/product-delivery-overview.svg").read_text(encoding="utf-8") if (ROOT / "docs/assets/product-delivery-overview.svg").exists() else ""
if "<svg" not in delivery_svg or "End-to-End Product Delivery" not in delivery_svg:
    errors.append("Product delivery architecture SVG is missing or invalid")

release_checker = ROOT / "scripts/check_release_readiness.py"
if release_checker.exists():
    ready = subprocess.run(
        [sys.executable, str(release_checker), str(ROOT / "tests/fixtures/release-readiness-ready.yaml")],
        capture_output=True, text=True,
    )
    if ready.returncode != 0:
        errors.append(f"Release readiness checker rejected READY fixture: {ready.stdout.strip()} {ready.stderr.strip()}")

    blocked = subprocess.run(
        [sys.executable, str(release_checker), str(ROOT / "tests/fixtures/release-readiness-blocked.yaml")],
        capture_output=True, text=True,
    )
    if blocked.returncode == 0:
        errors.append("Release readiness checker accepted BLOCKED fixture")

    sal3_risk = subprocess.run(
        [sys.executable, str(release_checker), str(ROOT / "tests/fixtures/release-readiness-sal3-risk.yaml")],
        capture_output=True, text=True,
    )
    if sal3_risk.returncode != 0:
        errors.append(f"Release readiness checker over-blocked SAL 3 PASS WITH RISK fixture: {sal3_risk.stdout.strip()} {sal3_risk.stderr.strip()}")

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

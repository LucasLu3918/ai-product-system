from pathlib import Path
import json
import os
import re
import subprocess
import sys
import tempfile
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
    "harness/adapters/REGISTRY.yaml",
    "templates/harness/HARNESS_RESOLUTION.yaml",
    "templates/harness/ADAPTER_MANIFEST.yaml",
    "templates/harness/INSTALLATION_OWNERSHIP.yaml",
    "templates/quality/QUALITY_PROFILE.yaml",
    "templates/knowledge/KNOWLEDGE_INDEX.yaml",
    "templates/design/PROJECT_VISUAL_PROFILE.yaml",
    "templates/design/VISUAL_AUDIT.yaml",
    "templates/delivery/RELEASE_READINESS.yaml",
    "templates/delivery/DEPLOYMENT_UNIT.yaml",
    "templates/requirements/IMPLEMENTATION_GOAL.yaml",
    "templates/context/EXTERNAL_SOURCE.yaml",
    "templates/review/REVIEW_FINDING.yaml",
    "templates/review/LESSONS.yaml",
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
    "orchestration/REQUIREMENT_CLARIFICATION.md", "orchestration/EXTERNAL_CONTEXT_RESOLUTION.md",
    "orchestration/VISUAL_POLISH.md", "orchestration/MULTI_REVIEW.md",
    "orchestration/QUALITY_PLANNING.md", "orchestration/PROJECT_KNOWLEDGE.md",
    "orchestration/HARNESS_RESOLUTION.md",
    "harness/BOOTSTRAP.md", "harness/HARNESS_PROTOCOL.md", "harness/ADAPTER_CONTRACT.md",
    "harness/adapters/codex/AGENTS.md", "harness/adapters/claude-code/CLAUDE.md",
    "harness/adapters/gemini-cli/gemini-extension.json", "harness/adapters/gemini-cli/GEMINI.md",
    "harness/adapters/generic/BOOTSTRAP.md",
    "docs/ARCHITECTURE.md", "docs/MAINTENANCE.md", "docs/INSTALLATION.md", "docs/SECURITY_ASSURANCE.md",
    "docs/GETTING_STARTED.md", "docs/USER_GUIDE.md", "docs/DOCUMENTATION_MAP.md", "docs/HARNESS.md",
    "docs/ARCHITECTURE_OVERVIEW.md", "docs/assets/system-overview.svg",
    "docs/assets/harness-overview.svg", "docs/assets/product-delivery-overview.svg", "docs/assets/system-lifecycle.svg",
    "examples/EXAMPLES.md", "work-modes/README.md",
    "templates/system-improvement-review.md", "templates/constitutional-change-proposal.md",
    "templates/core-change-proposal.md", "templates/git-publish-proposal.md",
    "templates/capability-reuse-review.md",
    "templates/review/REVIEW_REPORT.md",
    "templates/knowledge/KNOWLEDGE_TOPIC.md",
    "templates/creative/CREATIVE_BRIEF.md", "templates/creative/REFERENCE_BOARD.md",
    "templates/creative/VISUAL_REVIEW.md",
    "templates/brand/BRAND_INDEX.md", "templates/brand/BRAND_FOUNDATION.md",
    "templates/brand/BRAND_IDENTITY.md", "templates/brand/LOGO_SYSTEM.md",
    "templates/brand/VERBAL_IDENTITY.md", "templates/brand/BRAND_APPLICATION.md",
    "templates/brand/BRAND_GOVERNANCE.md",
    "templates/product/PRODUCT_WORKSPACE.md",
    "templates/delivery/LOCAL_ENVIRONMENT.md", "templates/delivery/DEPLOYMENT_PLAN.md",
    "templates/delivery/RUNBOOK.md",
    "scripts/check_release_readiness.py", "scripts/harness_resolve.py",
    "bin/aips", "scripts/bootstrap.sh", "scripts/uninstall.sh", "requirements.txt", ".github/workflows/validate.yml",
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
for phrase in ("Runtime flow", "Update preflight", "Primary planning package", "Risk-proportional security assurance", "Installation and project lifecycle"):
    if phrase not in architecture:
        errors.append(f"docs/ARCHITECTURE.md missing section: {phrase}")

system = (ROOT / "SYSTEM.md").read_text(encoding="utf-8") if (ROOT / "SYSTEM.md").exists() else ""
for phrase in ("Global Agent Harness", "System Update Preflight", "System Self-Improvement", "Core Change Approval Gate", "Git Publish Approval Gate", "Primary Planning Detection", "Security / Reliability Assurance", "Project knowledge", "Quality planning", "Creative and Brand routing", "External context", "Visual implementation polish", "Multi-perspective review", "Deterministic automation", "End-to-end product delivery", "Documentation Impact Gate"):
    if phrase not in system:
        errors.append(f"SYSTEM.md missing required behavior: {phrase}")

planning = (ROOT / "orchestration/PLANNING_PACKAGE.md").read_text(encoding="utf-8") if (ROOT / "orchestration/PLANNING_PACKAGE.md").exists() else ""
for phrase in ("Workspace first", "Gate 1", "Gate 2", "Reproducibility standard"):
    if phrase not in planning:
        errors.append(f"PLANNING_PACKAGE.md missing: {phrase}")

scenarios = sorted((ROOT / "tests/scenarios").glob("*.md"))
if len(scenarios) < 67:
    errors.append(f"Expected at least 67 acceptance scenarios, found {len(scenarios)}")

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
    "orchestration/REQUIREMENT_CLARIFICATION.md": ("Status", "Decision rule", "Implementation-ready goal", "Guidance style"),
    "orchestration/EXTERNAL_CONTEXT_RESOLUTION.md": ("Resolution order", "Authorization", "Fallback", "Source provenance"),
    "orchestration/VISUAL_POLISH.md": ("Preserve Before Redesign", "Consistency First", "Shared root cause first", "Rendered evidence"),
    "orchestration/MULTI_REVIEW.md": ("Reviewer resolution", "Bounded parallel review", "Consolidation", "Author fix loop", "Learning extraction"),
    "orchestration/QUALITY_PLANNING.md": ("Quality classes", "Seven dimensions", "Targets and evidence", "Observability planning"),
    "orchestration/PROJECT_KNOWLEDGE.md": ("Golden rule", "Knowledge types", "Staleness / invalidation", "Targeted refresh", "Promotion"),
    "orchestration/HARNESS_RESOLUTION.md": ("Applicability", "Project modes", "Instruction composition", "Runtime coverage"),
    "harness/HARNESS_PROTOCOL.md": ("Non-invasive invariant", "Adapter preference", "Ownership", "Uninstall"),
    "harness/ADAPTER_CONTRACT.md": ("Adapter responsibilities", "Runtime-native precedence"),
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
    "docs/HARNESS.md",
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
if "EPHEMERAL" not in svg or "Global Harness" not in svg:
    errors.append("System overview SVG must reflect Global Harness and EPHEMERAL/ATTACHED architecture")

harness_svg = (ROOT / "docs/assets/harness-overview.svg").read_text(encoding="utf-8") if (ROOT / "docs/assets/harness-overview.svg").exists() else ""
if "<svg" not in harness_svg or "AIPS Global Harness" not in harness_svg:
    errors.append("Harness architecture SVG is missing or invalid")

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
if "LOCAL_COMPLETE" not in delivery_svg or "PRODUCTION_VERIFIED" not in delivery_svg:
    errors.append("Product delivery SVG must reflect LOCAL_COMPLETE and PRODUCTION_VERIFIED")

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


implementation_goal = load_yaml(ROOT / "templates/requirements/IMPLEMENTATION_GOAL.yaml") or {}
for key in ("status", "objective", "expected_output", "scope", "success_criteria", "blocking_unknowns"):
    if key not in implementation_goal:
        errors.append(f"IMPLEMENTATION_GOAL.yaml missing top-level key: {key}")

external_source = load_yaml(ROOT / "templates/context/EXTERNAL_SOURCE.yaml") or {}
for key in ("source", "resolution", "task", "provenance", "fallback"):
    if key not in external_source:
        errors.append(f"EXTERNAL_SOURCE.yaml missing top-level key: {key}")

review_finding = load_yaml(ROOT / "templates/review/REVIEW_FINDING.yaml") or {}
for key in ("id", "severity", "reviewer", "scope", "category", "finding", "impact", "evidence", "recommendation", "status"):
    if key not in review_finding:
        errors.append(f"REVIEW_FINDING.yaml missing top-level key: {key}")

lessons = load_yaml(ROOT / "templates/review/LESSONS.yaml") or {}
if "lessons" not in lessons:
    errors.append("LESSONS.yaml missing lessons list")

lifecycle_svg = (ROOT / "docs/assets/system-lifecycle.svg").read_text(encoding="utf-8") if (ROOT / "docs/assets/system-lifecycle.svg").exists() else ""
if "<svg" not in lifecycle_svg or "Installation &amp; Project Lifecycle" not in lifecycle_svg:
    errors.append("System lifecycle SVG is missing or invalid")
if "EPHEMERAL" not in lifecycle_svg or "ATTACHED" not in lifecycle_svg or "Runtime Adapters" not in lifecycle_svg:
    errors.append("System lifecycle SVG must reflect Harness adapters and EPHEMERAL/ATTACHED modes")

cli_text = (ROOT / "bin/aips").read_text(encoding="utf-8") if (ROOT / "bin/aips").exists() else ""
for phrase in ("aips attach <project-path>", "aips detach <project-path>", "aips status <project-path>", "aips harness install", "aips harness uninstall", "aips harness status", "aips harness doctor", "aips harness resolve"):
    if phrase not in cli_text:
        errors.append(f"bin/aips missing lifecycle command: {phrase}")

with tempfile.TemporaryDirectory() as tmp:
    project = Path(tmp) / "project"
    project.mkdir()
    cli = ROOT / "bin/aips"

    attach = subprocess.run(["bash", str(cli), "attach", str(project)], capture_output=True, text=True)
    if attach.returncode != 0 or not (project / ".ai").is_dir():
        errors.append(f"aips attach lifecycle test failed: {attach.stdout.strip()} {attach.stderr.strip()}")
    else:
        status = subprocess.run(["bash", str(cli), "status", str(project)], capture_output=True, text=True)
        if status.returncode != 0 or "Project attached: yes" not in status.stdout:
            errors.append(f"aips status attached test failed: {status.stdout.strip()} {status.stderr.strip()}")

        detach = subprocess.run(["bash", str(cli), "detach", str(project)], capture_output=True, text=True)
        archives = sorted(project.glob(".ai.detached-*"))
        if detach.returncode != 0 or (project / ".ai").exists() or len(archives) != 1:
            errors.append(f"aips detach lifecycle test failed: {detach.stdout.strip()} {detach.stderr.strip()}")
        else:
            blocked_attach = subprocess.run(["bash", str(cli), "attach", str(project)], capture_output=True, text=True)
            if blocked_attach.returncode == 0:
                errors.append("aips attach should stop when detached workspace exists")

            archives[0].rename(project / ".ai")
            reattach = subprocess.run(["bash", str(cli), "attach", str(project)], capture_output=True, text=True)
            if reattach.returncode != 0 or not (project / ".ai").is_dir():
                errors.append(f"aips reattach lifecycle test failed: {reattach.stdout.strip()} {reattach.stderr.strip()}")


quality_profile = load_yaml(ROOT / "templates/quality/QUALITY_PROFILE.yaml") or {}
for key in ("quality_class", "priorities", "performance", "security", "usability", "reliability", "maintainability", "resource_cost", "delivery"):
    if key not in quality_profile:
        errors.append(f"QUALITY_PROFILE.yaml missing top-level key: {key}")

knowledge_index = load_yaml(ROOT / "templates/knowledge/KNOWLEDGE_INDEX.yaml") or {}
for key in ("status", "last_project_discovery", "topics", "authoritative_pointers"):
    if key not in knowledge_index:
        errors.append(f"KNOWLEDGE_INDEX.yaml missing top-level key: {key}")

visual_profile = load_yaml(ROOT / "templates/design/PROJECT_VISUAL_PROFILE.yaml") or {}
for key in ("status", "direction", "controls", "state_rules", "representative_routes", "golden_components", "exceptions", "watch"):
    if key not in visual_profile:
        errors.append(f"PROJECT_VISUAL_PROFILE.yaml missing top-level key: {key}")

visual_audit = load_yaml(ROOT / "templates/design/VISUAL_AUDIT.yaml") or {}
for key in ("mode", "status", "component_inventory", "findings", "verification", "remaining_material_findings"):
    if key not in visual_audit:
        errors.append(f"VISUAL_AUDIT.yaml missing top-level key: {key}")

if product_manifest:
    quality = product_manifest.get("quality") or {}
    delivery = product_manifest.get("delivery") or {}
    if "profile" not in quality or "class" not in quality:
        errors.append("PRODUCT.yaml quality must reference profile and class")
    if "status" not in delivery or "production_enablement_requested" not in delivery:
        errors.append("PRODUCT.yaml delivery must track local/production milestone state")

workspace_state = load_yaml(ROOT / "templates/workspace/STATE.yaml") or {}
for key in ("quality", "knowledge", "visual", "delivery"):
    if key not in workspace_state:
        errors.append(f"STATE.yaml missing v0.7 top-level key: {key}")

workspace_manifest = load_yaml(ROOT / "templates/workspace/MANIFEST.yaml") or {}
for key in ("project_knowledge", "quality", "visual"):
    if key not in workspace_manifest:
        errors.append(f"MANIFEST.yaml missing v0.7 top-level key: {key}")


if "Project mode: EPHEMERAL (no .ai workspace created)." not in cli_text:
    errors.append("bin/aips preflight must support EPHEMERAL mode without implicit attach")
if "Project workspace is not attached; applying attach safety checks." in cli_text:
    errors.append("bin/aips still contains the old implicit preflight attach behavior")

maintenance_text = (ROOT / "docs/MAINTENANCE.md").read_text(encoding="utf-8") if (ROOT / "docs/MAINTENANCE.md").exists() else ""
if "Architecture Diagram Impact Check" not in maintenance_text:
    errors.append("docs/MAINTENANCE.md missing Architecture Diagram Impact Check")

core_change_text = (ROOT / "templates/core-change-proposal.md").read_text(encoding="utf-8") if (ROOT / "templates/core-change-proposal.md").exists() else ""
if "Architecture Diagram Impact" not in core_change_text:
    errors.append("Core Change Proposal missing Architecture Diagram Impact")

for rel, keys in {
    "templates/harness/HARNESS_RESOLUTION.yaml": ("harness", "runtime", "project", "instructions", "knowledge", "state", "system"),
    "templates/harness/ADAPTER_MANIFEST.yaml": ("id", "runtime", "detection", "integration", "ownership", "bootstrap", "verification", "uninstall"),
    "templates/harness/INSTALLATION_OWNERSHIP.yaml": ("system", "harness", "owned_resources", "adapters", "preservation_policy"),
    "harness/adapters/REGISTRY.yaml": ("adapters",),
}.items():
    doc = load_yaml(ROOT / rel) or {}
    for key in keys:
        if key not in doc:
            errors.append(f"{rel} missing top-level key: {key}")

resolver = ROOT / "scripts/harness_resolve.py"
if resolver.exists():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(resolver)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"harness_resolve.py syntax failed: {compiled.stderr.strip()}")

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    home = tmp_path / "home"
    fake_bin = tmp_path / "fake-bin"
    config = tmp_path / "config"
    bin_home = tmp_path / "bin-home"
    home.mkdir()
    fake_bin.mkdir()
    (home / ".claude").mkdir()
    custom_claude = home / ".claude" / "CLAUDE.md"
    custom_claude.write_text("# user-owned claude instructions\n", encoding="utf-8")

    for name in ("codex", "claude"):
        p = fake_bin / name
        p.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        p.chmod(0o755)

    gemini = fake_bin / "gemini"
    gemini_script = "\n".join([
        "#!/usr/bin/env bash",
        "state=\"$HOME/.fake-gemini-extension\"",
        "if [ \"${1:-}\" = extensions ]; then",
        "  case \"${2:-}\" in",
        "    list) [ -f \"$state\" ] && echo aips-global-harness; exit 0 ;;",
        "    link) touch \"$state\"; exit 0 ;;",
        "    uninstall) rm -f \"$state\"; exit 0 ;;",
        "  esac",
        "fi",
        "exit 0",
        ""
    ])
    gemini.write_text(gemini_script, encoding="utf-8")
    gemini.chmod(0o755)

    env = dict(os.environ)
    env.update({
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(config),
        "AIPS_BIN_HOME": str(bin_home),
        "PATH": f"{fake_bin}:{env.get('PATH', '')}",
    })
    cli = ROOT / "bin/aips"

    install_harness = subprocess.run(["bash", str(cli), "harness", "install"], env=env, capture_output=True, text=True)
    if install_harness.returncode != 0:
        errors.append(f"harness install test failed: {install_harness.stdout.strip()} {install_harness.stderr.strip()}")
    else:
        codex_bootstrap = home / ".codex" / "AGENTS.md"
        if not codex_bootstrap.exists():
            errors.append("Harness install did not create AIPS-owned Codex bootstrap")
        if custom_claude.read_text(encoding="utf-8") != "# user-owned claude instructions\n":
            errors.append("Harness install modified existing user-owned CLAUDE.md")
        claude_state = config / "aips" / "harness" / "adapters" / "claude-code.yaml"
        if not claude_state.exists() or 'status: "MANUAL"' not in claude_state.read_text(encoding="utf-8"):
            errors.append("Existing user CLAUDE.md should force MANUAL adapter status")
        ownership_file = config / "aips" / "harness" / "installation.yaml"
        if not ownership_file.exists():
            errors.append("Harness install did not create ownership manifest")
        else:
            ownership_text = ownership_file.read_text(encoding="utf-8")
            if "runtime_bootstrap" not in ownership_text or str(codex_bootstrap) not in ownership_text:
                errors.append("Ownership manifest does not record AIPS-owned Codex bootstrap resource")
            if "runtime_registration" not in ownership_text or "aips-global-harness" not in ownership_text:
                errors.append("Ownership manifest does not record AIPS-owned Gemini registration")
        if not (home / ".fake-gemini-extension").exists():
            errors.append("Harness install did not register fake Gemini extension")

        project = tmp_path / "project"
        project.mkdir()
        resolved = subprocess.run(
            ["bash", str(cli), "harness", "resolve", "--runtime", "codex", "--project", str(project), "--format", "json"],
            env=env, capture_output=True, text=True,
        )
        if resolved.returncode != 0:
            errors.append(f"harness resolve test failed: {resolved.stdout.strip()} {resolved.stderr.strip()}")
        else:
            try:
                data = json.loads(resolved.stdout)
                if data.get("project", {}).get("mode") != "EPHEMERAL":
                    errors.append("Harness resolver should report EPHEMERAL without .ai")
                if data.get("runtime", {}).get("id") != "codex":
                    errors.append("Harness resolver runtime mismatch")
            except Exception as exc:
                errors.append(f"Harness resolver JSON invalid: {exc}")

        uninstall_harness = subprocess.run(["bash", str(cli), "harness", "uninstall"], env=env, capture_output=True, text=True)
        if uninstall_harness.returncode != 0:
            errors.append(f"harness uninstall test failed: {uninstall_harness.stdout.strip()} {uninstall_harness.stderr.strip()}")
        if codex_bootstrap.exists():
            errors.append("Uninstall should remove unchanged AIPS-owned Codex bootstrap")
        if custom_claude.read_text(encoding="utf-8") != "# user-owned claude instructions\n":
            errors.append("Harness uninstall modified user-owned CLAUDE.md")
        if (home / ".fake-gemini-extension").exists():
            errors.append("Harness uninstall did not unregister fake Gemini extension")

        reinstall = subprocess.run(["bash", str(cli), "harness", "install"], env=env, capture_output=True, text=True)
        if reinstall.returncode == 0 and codex_bootstrap.exists():
            with codex_bootstrap.open("a", encoding="utf-8") as fh:
                fh.write("\n# user edit\n")
            preserve = subprocess.run(["bash", str(cli), "harness", "uninstall"], env=env, capture_output=True, text=True)
            if preserve.returncode != 0:
                errors.append("Second harness uninstall failed")
            if not codex_bootstrap.exists() or "# user edit" not in codex_bootstrap.read_text(encoding="utf-8"):
                errors.append("Modified AIPS-owned bootstrap should be preserved on uninstall")


with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    home = tmp_path / "home"
    fake_bin = tmp_path / "fake-bin"
    config = tmp_path / "config"
    bin_home = tmp_path / "bin-home"
    home.mkdir()
    fake_bin.mkdir()
    gemini = fake_bin / "gemini"
    gemini_script = "\n".join([
        "#!/usr/bin/env bash",
        "state=\"$HOME/.fake-gemini-extension\"",
        "fail=\"$HOME/.fake-gemini-fail-uninstall\"",
        "if [ \"${1:-}\" = extensions ]; then",
        "  case \"${2:-}\" in",
        "    list) [ -f \"$state\" ] && echo aips-global-harness; exit 0 ;;",
        "    link) touch \"$state\"; exit 0 ;;",
        "    uninstall) [ -f \"$fail\" ] && exit 9; rm -f \"$state\"; exit 0 ;;",
        "  esac",
        "fi",
        "exit 0",
        ""
    ])
    gemini.write_text(gemini_script, encoding="utf-8")
    gemini.chmod(0o755)
    env = dict(os.environ)
    env.update({
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(config),
        "AIPS_BIN_HOME": str(bin_home),
        "PATH": f"{fake_bin}:{env.get('PATH', '')}",
    })
    cli = ROOT / "bin/aips"
    first = subprocess.run(["bash", str(cli), "harness", "install"], env=env, capture_output=True, text=True)
    if first.returncode != 0:
        errors.append("Gemini recovery setup install failed")
    else:
        (home / ".fake-gemini-fail-uninstall").touch()
        failed_uninstall = subprocess.run(["bash", str(cli), "harness", "uninstall"], env=env, capture_output=True, text=True)
        harness_home = config / "aips" / "harness"
        if failed_uninstall.returncode == 0:
            errors.append("Harness uninstall should fail when an AIPS-owned Gemini registration cannot be removed")
        if not harness_home.exists():
            errors.append("Failed harness uninstall must preserve ownership state for retry")
        (home / ".fake-gemini-fail-uninstall").unlink()
        retry = subprocess.run(["bash", str(cli), "harness", "uninstall"], env=env, capture_output=True, text=True)
        if retry.returncode != 0 or harness_home.exists():
            errors.append("Harness uninstall retry should succeed after Gemini unregister recovers")

for shell in ("bin/aips", "scripts/bootstrap.sh", "scripts/uninstall.sh"):
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

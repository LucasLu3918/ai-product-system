from pathlib import Path
import json
import os
import re
import subprocess
import sys
import tempfile
import yaml

ROOT = Path(__file__).resolve().parents[2]
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
    "templates/intelligence/PROJECT_INTELLIGENCE.yaml",
    "templates/intelligence/SOURCE_REGISTRY.yaml",
    "templates/intelligence/IMPACT_GRAPH.yaml",
    "templates/intelligence/PROJECT_OVERRIDES.yaml",
    "templates/intelligence/CHANGE_IMPACT.yaml",
    "templates/intelligence/TURN_CONTEXT_MANIFEST.yaml",
    "templates/intelligence/RETRIEVAL_INDEX.yaml",
    "templates/intelligence/RETRIEVAL_EVALUATION.yaml",
    "templates/intelligence/SEMANTIC_ALIASES.yaml",
    "config/retrieval-embedding-trial.yaml",
    "tests/fixtures/retrieval_quality_corpus.yaml",
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
    "templates/conformance/AGENT_EVAL_CASE.yaml",
    "templates/conformance/AGENT_EVAL_RESULT.yaml",
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
    "orchestration/ORCHESTRATOR.md", "orchestration/MODEL_ROUTING.md", "orchestration/EXECUTION_ISOLATION.md",
    "orchestration/INSTRUCTION_RESOLUTION.md", "orchestration/WORKSPACE_STATE.md",
    "orchestration/PLANNING_PACKAGE.md", "orchestration/SYSTEM_SELF_IMPROVEMENT.md",
    "orchestration/CREATIVE_DIRECTION.md", "orchestration/BRAND_SYSTEM.md",
    "orchestration/CAPABILITY_INCUBATION.md", "orchestration/DETERMINISTIC_AUTOMATION.md",
    "orchestration/PRODUCT_DELIVERY.md", "orchestration/RELEASE_READINESS.md",
    "orchestration/REQUIREMENT_CLARIFICATION.md", "orchestration/EXTERNAL_CONTEXT_RESOLUTION.md",
    "orchestration/VISUAL_POLISH.md", "orchestration/MULTI_REVIEW.md",
    "orchestration/QUALITY_PLANNING.md", "orchestration/PROJECT_KNOWLEDGE.md",
    "orchestration/SECRET_HANDLING.md", "orchestration/CORE_CHANGE_TESTING.md",
    "orchestration/PROJECT_IDENTITY.md", "orchestration/PROJECT_INTELLIGENCE.md", "orchestration/CHANGE_IMPACT.md",
    "orchestration/TURN_HARNESS.md", "orchestration/HARNESS_RESOLUTION.md", "orchestration/CONFORMANCE.md", "orchestration/AGENT_EVAL.md",
    "harness/BOOTSTRAP.md", "harness/HARNESS_PROTOCOL.md", "harness/ADAPTER_CONTRACT.md",
    "harness/adapters/codex/AGENTS.md", "harness/adapters/claude-code/CLAUDE.md",
    "harness/adapters/gemini-cli/gemini-extension.json", "harness/adapters/gemini-cli/GEMINI.md",
    "harness/adapters/generic/BOOTSTRAP.md",
    "docs/ARCHITECTURE.md", "docs/human/MAINTENANCE.md", "docs/human/INSTALLATION.md", "docs/human/SECURITY_ASSURANCE.md",
    "docs/human/GETTING_STARTED.md", "docs/human/USER_GUIDE.md", "docs/human/DOCUMENTATION_MAP.md", "docs/human/HARNESS.md",
    "docs/human/PROJECT_INTELLIGENCE.md", "docs/human/ARCHITECTURE_OVERVIEW.md", "docs/human/assets/system-overview.svg",
    "docs/human/assets/harness-overview.svg", "docs/human/assets/project-intelligence-overview.svg", "docs/human/assets/product-delivery-overview.svg", "docs/human/assets/system-lifecycle.svg",
    "examples/EXAMPLES.md", "work-modes/README.md",
    "templates/system-improvement-review.md", "templates/constitutional-change-proposal.md",
    "templates/core-change-proposal.md", "templates/git-publish-proposal.md",
    "templates/capability-reuse-review.md",
    "templates/review/REVIEW_REPORT.md", "templates/review/CORE_CHANGE_TEST_MATRIX.yaml",
    "templates/review/TRAJECTORY_TRACE.yaml", "templates/review/TRAJECTORY_EVIDENCE.yaml",
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
    "scripts/project_intelligence.py", "scripts/retrieval_intelligence.py", "scripts/retrieval_evaluation.py", "scripts/structural_retrieval_trial.py", "scripts/retrieval_embedding_trial.py", "scripts/retrieval_embedding_trial_summary.py", "scripts/turn_context_hook.py", "scripts/manage_runtime_adapter.py",
    "scripts/aips_identity.py", "scripts/execution_isolation.py",
    "scripts/agent_eval.py", "scripts/trajectory_eval.py", "scripts/check_secret_leakage.py", "scripts/content_safety.py", "scripts/visual_profile.py",
    "scripts/requirements_traceability.py",
    "config/content-safety.yaml", "orchestration/CONTENT_SAFETY_BOUNDARY.md",
    "tests/evidence/governance_command_guard.py", "tests/evidence/trajectory_quality_gate_lifecycle.py", "tests/evidence/visual_profile_lifecycle.py",
    "bin/aips", "scripts/bootstrap.sh", "scripts/uninstall.sh", "requirements.txt", ".github/workflows/validate.yml", ".github/workflows/retrieval-semantic-trial.yml",
    ".github/dependabot.yml", "SECURITY.md",
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
    "templates/planning-package/REQUIREMENTS.yaml",
]
for rel in required_files + planning_templates + security_templates:
    if not (ROOT / rel).exists():
        errors.append(f"Missing required file: {rel}")

workflow_text = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8") if (ROOT / ".github/workflows/validate.yml").exists() else ""
if "permissions:\n  contents: read" not in workflow_text:
    errors.append("validate workflow missing explicit read-only contents permission")
for contract in (
    "push:\n    branches:\n      - main",
    "pull_request:",
    "workflow_dispatch:",
    "concurrency:",
    "group: validate-${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}",
    "cancel-in-progress: true",
    "github.event_name == 'push' && github.event.before",
):
    if contract not in workflow_text:
        errors.append(f"validate workflow missing CI-noise contract: {contract}")
for action in ("actions/checkout", "actions/setup-python"):
    match = re.search(r"uses:\s*" + re.escape(action) + r"@([0-9a-f]{40})(?:\s|$)", workflow_text)
    if not match:
        errors.append(f"validate workflow must pin {action} to an immutable full commit SHA")

dependabot_text = (ROOT / ".github/dependabot.yml").read_text(encoding="utf-8") if (ROOT / ".github/dependabot.yml").exists() else ""
for ecosystem in ('package-ecosystem: "pip"', 'package-ecosystem: "github-actions"'):
    if ecosystem not in dependabot_text:
        errors.append(f"Dependabot config missing ecosystem: {ecosystem}")

security_policy = (ROOT / "SECURITY.md").read_text(encoding="utf-8") if (ROOT / "SECURITY.md").exists() else ""
if "do not disclose credentials" not in security_policy.lower() or "Report a vulnerability" not in security_policy:
    errors.append("SECURITY.md missing private vulnerability reporting guidance")

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").exists() else ""
if not re.fullmatch(r"\d+\.\d+\.\d+", version):
    errors.append(f"VERSION is not SemVer x.y.z: {version!r}")

changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8") if (ROOT / "CHANGELOG.md").exists() else ""
if version and f"## {version}" not in changelog:
    errors.append(f"CHANGELOG.md has no section for VERSION {version}")

architecture = (ROOT / "docs/ARCHITECTURE.md").read_text(encoding="utf-8") if (ROOT / "docs/ARCHITECTURE.md").exists() else ""
if "mermaid" not in architecture or "flowchart" not in architecture:
    errors.append("docs/ARCHITECTURE.md must contain source-controlled Mermaid diagrams")
for phrase in ("Runtime flow", "Update preflight", "Primary planning package", "Risk-proportional security assurance", "Installation and project lifecycle", "Project Intelligence"):
    if phrase not in architecture:
        errors.append(f"docs/ARCHITECTURE.md missing section: {phrase}")

system = (ROOT / "SYSTEM.md").read_text(encoding="utf-8") if (ROOT / "SYSTEM.md").exists() else ""
for phrase in ("Global Agent Harness", "System Update Preflight", "System Self-Improvement", "Core Change Approval Gate", "Git Publish Approval Gate", "Primary Planning Detection", "Security / Reliability Assurance", "Project Intelligence", "Quality planning", "Creative and Brand routing", "External context", "Visual implementation polish", "Multi-perspective review", "Deterministic automation", "End-to-end product delivery", "Documentation Impact Gate"):
    if phrase not in system:
        errors.append(f"SYSTEM.md missing required behavior: {phrase}")

planning = (ROOT / "orchestration/PLANNING_PACKAGE.md").read_text(encoding="utf-8") if (ROOT / "orchestration/PLANNING_PACKAGE.md").exists() else ""
for phrase in ("Workspace first", "Gate 1", "Gate 2", "Reproducibility standard"):
    if phrase not in planning:
        errors.append(f"PLANNING_PACKAGE.md missing: {phrase}")

scenarios = sorted((ROOT / "tests/scenarios").glob("*.md"))
if len(scenarios) < 125:
    errors.append(f"Expected at least 125 acceptance scenarios, found {len(scenarios)}")

security_doc = (ROOT / "docs/human/SECURITY_ASSURANCE.md").read_text(encoding="utf-8") if (ROOT / "docs/human/SECURITY_ASSURANCE.md").exists() else ""
for phrase in ("SAL 0", "SAL 4", "Critical risk floors", "Product baseline vs change impact", "Release Security Gate"):
    if phrase not in security_doc:
        errors.append(f"SECURITY_ASSURANCE.md missing: {phrase}")

for security_skill in ("threat-modeling", "authorization-security", "business-logic-abuse", "financial-integrity", "security-testing"):
    if security_skill not in (skills.get("skills") or {}):
        errors.append(f"Missing security skill in index: {security_skill}")



secret_protocol = (ROOT / "orchestration/SECRET_HANDLING.md").read_text(encoding="utf-8") if (ROOT / "orchestration/SECRET_HANDLING.md").exists() else ""
for phrase in ("Secret values are runtime inputs", "Acquisition priority", "Secret leakage review", "Exposure response"):
    if phrase not in secret_protocol:
        errors.append(f"SECRET_HANDLING.md missing: {phrase}")

core_testing = (ROOT / "orchestration/CORE_CHANGE_TESTING.md").read_text(encoding="utf-8") if (ROOT / "orchestration/CORE_CHANGE_TESTING.md").exists() else ""
for phrase in ("Impact-derived Test Matrix", "Recompute rule", "Strict completion rule", "Actual Diff"):
    if phrase not in core_testing:
        errors.append(f"CORE_CHANGE_TESTING.md missing: {phrase}")

incubation = (ROOT / "orchestration/CAPABILITY_INCUBATION.md").read_text(encoding="utf-8") if (ROOT / "orchestration/CAPABILITY_INCUBATION.md").exists() else ""
for phrase in ("New Skill admission contract", "positive triggers", "non-triggers", "context/token cost", "unique ID/path"):
    if phrase.lower() not in incubation.lower():
        errors.append(f"CAPABILITY_INCUBATION.md missing New Skill admission requirement: {phrase}")

skill_paths = {}
for skill_id, meta in (skills.get("skills") or {}).items():
    path_value = meta.get("path")
    if path_value in skill_paths:
        errors.append(f"Duplicate Skill path registered by {skill_paths[path_value]} and {skill_id}: {path_value}")
    else:
        skill_paths[path_value] = skill_id
    body_path = ROOT / "skills" / str(path_value)
    if body_path.exists():
        body = body_path.read_text(encoding="utf-8")
        if body.startswith("---"):
            match = re.search(r"(?m)^id:\\s*([^\\s]+)\\s*$", body)
            if match and match.group(1) != skill_id:
                errors.append(f"Skill frontmatter id mismatch: index={skill_id}, body={match.group(1)}")

matrix_doc = load_yaml(ROOT / "templates/review/CORE_CHANGE_TEST_MATRIX.yaml") or {}
for key in ("change", "matrix", "scope_recomputed_after_expansion", "actual_diff_reconciled", "blockers", "status"):
    if key not in matrix_doc:
        errors.append(f"CORE_CHANGE_TEST_MATRIX.yaml missing top-level key: {key}")

constitution = (ROOT / "core/CONSTITUTION.md").read_text(encoding="utf-8") if (ROOT / "core/CONSTITUTION.md").exists() else ""
for phrase in ("Protected Human Authority", "Truth and No Silent Assumptions", "Protected Safety Boundary", "Stop-the-Line", "Scope Integrity", "Explicit Approval for High-Risk Actions", "Amendment Protocol"):
    if phrase not in constitution:
        errors.append(f"CONSTITUTION.md missing protected article: {phrase}")

self_improvement = (ROOT / "orchestration/SYSTEM_SELF_IMPROVEMENT.md").read_text(encoding="utf-8") if (ROOT / "orchestration/SYSTEM_SELF_IMPROVEMENT.md").exists() else ""
for phrase in (
    "Self-Improvement Review",
    "Problem / Solution Separation",
    "User Problem",
    "Proposed Solution",
    "Recommended AIPS Solution",
    "Additional Optimization Confirmation",
    "NOW",
    "LATER",
    "REJECT",
    "explicit Human confirmation",
    "Constitution Impact Check",
    "Lower-layer preference",
):
    if phrase not in self_improvement:
        errors.append(f"SYSTEM_SELF_IMPROVEMENT.md missing: {phrase}")

self_improvement_template = (ROOT / "templates/system-improvement-review.md").read_text(encoding="utf-8") if (ROOT / "templates/system-improvement-review.md").exists() else ""
for phrase in (
    "## User Problem",
    "## Proposed Solution",
    "## Existing Coverage",
    "## Reuse / Extension Candidates",
    "## Context / Token Cost",
    "## Security / Reliability",
    "## Architecture Diagram Impact",
    "## Recommended AIPS Solution",
    "## Additional Optimization Candidates",
    "Recommended timing: NOW / LATER / REJECT",
    "Approved additional optimizations:",
    "Deferred optimizations:",
):
    if phrase not in self_improvement_template:
        errors.append(f"system-improvement-review.md missing contract field: {phrase}")

self_improvement_scenario = ROOT / "tests/scenarios/019-system-self-improvement.md"
scenario_019 = self_improvement_scenario.read_text(encoding="utf-8") if self_improvement_scenario.exists() else ""
for phrase in (
    "User Problem, Proposed Solution and Recommended AIPS Solution",
    "existing coverage",
    "reuse/extension candidates",
    "context/token cost",
    "Human-facing docs and Agent-facing docs separately",
    "Architecture Diagram Impact",
    "NOW / LATER / REJECT",
    "explicit Human confirmation",
):
    if phrase.lower() not in scenario_019.lower():
        errors.append(f"Scenario 019 missing self-improvement acceptance contract: {phrase}")


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
    "orchestration/PROJECT_KNOWLEDGE.md": ("Compatibility rule", "No duplication", "Migration safety"),
    "orchestration/HARNESS_RESOLUTION.md": ("Two levels", "Project modes", "Runtime capability", "Instruction composition", "Failure policy"),
    "harness/HARNESS_PROTOCOL.md": ("Turn-aware flow", "Non-invasive invariant", "Capability", "Project persistence", "Uninstall"),
    "harness/ADAPTER_CONTRACT.md": ("Capability states", "Managed composition", "Runtime targets"),
    "orchestration/PROJECT_INTELLIGENCE.md": ("Initial Intelligence Bootstrap", "Source registry and deduplication", "Semantic enrichment and READY", "Sensitive data", "Human review"),
    "orchestration/CHANGE_IMPACT.md": ("Required dimensions", "Project-native style", "Diff reconciliation"),
    "orchestration/TURN_HARNESS.md": ("Turn path latency budget", "Capability states", "Failure policy"),
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
    "docs/human/GETTING_STARTED.md",
    "docs/human/USER_GUIDE.md",
    "docs/human/INSTALLATION.md",
    "docs/human/HARNESS.md",
    "docs/human/PROJECT_INTELLIGENCE.md",
    "docs/human/ARCHITECTURE_OVERVIEW.md",
    "docs/human/DOCUMENTATION_MAP.md",
)
for rel in human_docs:
    text = (ROOT / rel).read_text(encoding="utf-8") if (ROOT / rel).exists() else ""
    if not re.search(r"[\u4e00-\u9fff]", text):
        errors.append(f"Human doc is expected to contain Traditional Chinese content: {rel}")

root_user_guide = (ROOT / "USER_GUIDE.md").read_text(encoding="utf-8") if (ROOT / "USER_GUIDE.md").exists() else ""
if len(root_user_guide) > 1200 or "docs/human/USER_GUIDE.md" not in root_user_guide:
    errors.append("Root USER_GUIDE.md should remain a short redirect to docs/human/USER_GUIDE.md")

svg = (ROOT / "docs/human/assets/system-overview.svg").read_text(encoding="utf-8") if (ROOT / "docs/human/assets/system-overview.svg").exists() else ""
if "<svg" not in svg or "AI Product System" not in svg:
    errors.append("Human architecture SVG is missing or invalid")
if "EPHEMERAL" not in svg or "ATTACHED" not in svg or "Turn-Aware Harness" not in svg:
    errors.append("System overview SVG must reflect Turn-Aware Harness and EPHEMERAL/ATTACHED architecture")

harness_svg = (ROOT / "docs/human/assets/harness-overview.svg").read_text(encoding="utf-8") if (ROOT / "docs/human/assets/harness-overview.svg").exists() else ""
if "<svg" not in harness_svg or "Turn-Aware" not in harness_svg:
    errors.append("Harness architecture SVG is missing or invalid")

intelligence_svg = (ROOT / "docs/human/assets/project-intelligence-overview.svg").read_text(encoding="utf-8") if (ROOT / "docs/human/assets/project-intelligence-overview.svg").exists() else ""
if "<svg" not in intelligence_svg or "Project Intelligence" not in intelligence_svg or "Change Impact" not in intelligence_svg:
    errors.append("Project Intelligence architecture SVG is missing or invalid")

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

delivery_svg = (ROOT / "docs/human/assets/product-delivery-overview.svg").read_text(encoding="utf-8") if (ROOT / "docs/human/assets/product-delivery-overview.svg").exists() else ""
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
if not isinstance(implementation_goal.get("requirement_traceability", []), list):
    errors.append("IMPLEMENTATION_GOAL.yaml requirement_traceability must remain an optional list")

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

lifecycle_svg = (ROOT / "docs/human/assets/system-lifecycle.svg").read_text(encoding="utf-8") if (ROOT / "docs/human/assets/system-lifecycle.svg").exists() else ""
if "<svg" not in lifecycle_svg or "Installation, Harness &amp; Intelligence Lifecycle" not in lifecycle_svg:
    errors.append("System lifecycle SVG is missing or invalid")
if "EPHEMERAL" not in lifecycle_svg or "ATTACHED" not in lifecycle_svg or "managed adapters" not in lifecycle_svg:
    errors.append("System lifecycle SVG must reflect Harness adapters and EPHEMERAL/ATTACHED Intelligence modes")

cli_text = (ROOT / "bin/aips").read_text(encoding="utf-8") if (ROOT / "bin/aips").exists() else ""
for phrase in ("aips attach <project-path>", "aips detach <project-path>", "aips status <project-path>", "aips harness install", "aips harness uninstall", "aips harness status", "aips harness doctor", "aips harness resolve", "aips intelligence bootstrap", "aips intelligence status", "aips intelligence context", "aips intelligence render"):
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
for key in ("quality", "intelligence", "knowledge_compat", "visual", "delivery"):
    if key not in workspace_state:
        errors.append(f"STATE.yaml missing required top-level key: {key}")

workspace_manifest = load_yaml(ROOT / "templates/workspace/MANIFEST.yaml") or {}
for key in ("project_intelligence", "project_knowledge_compat", "quality", "visual"):
    if key not in workspace_manifest:
        errors.append(f"MANIFEST.yaml missing required top-level key: {key}")


if "Project mode: EPHEMERAL (no .ai workspace created)." not in cli_text:
    errors.append("bin/aips preflight must support EPHEMERAL mode without implicit attach")
if "refresh_harness_if_installed" not in cli_text:
    errors.append("bin/aips must refresh/migrate Harness after installed-system updates")
if 'die "CLI path already exists and is not an AIPS symlink' not in cli_text:
    errors.append("bin/aips install must reject non-AIPS CLI path collisions")
if "Project workspace is not attached; applying attach safety checks." in cli_text:
    errors.append("bin/aips still contains the old implicit preflight attach behavior")

maintenance_text = (ROOT / "docs/human/MAINTENANCE.md").read_text(encoding="utf-8") if (ROOT / "docs/human/MAINTENANCE.md").exists() else ""
if "Architecture Diagram Impact Check" not in maintenance_text:
    errors.append("docs/human/MAINTENANCE.md missing Architecture Diagram Impact Check")

core_change_text = (ROOT / "templates/core-change-proposal.md").read_text(encoding="utf-8") if (ROOT / "templates/core-change-proposal.md").exists() else ""
if "Architecture Diagram Impact" not in core_change_text:
    errors.append("Core Change Proposal missing Architecture Diagram Impact")


for rel, keys in {
    "templates/intelligence/PROJECT_INTELLIGENCE.yaml": ("schema", "generated_by", "project", "state", "topics", "canonical_artifacts"),
    "templates/intelligence/SOURCE_REGISTRY.yaml": ("sources", "runtime_visibility", "deduplication"),
    "templates/intelligence/IMPACT_GRAPH.yaml": ("nodes", "edges", "coverage", "unknowns"),
    "templates/intelligence/PROJECT_OVERRIDES.yaml": ("approved_inferences", "additional_rules", "exceptions", "excluded_inferences", "conflicts"),
    "templates/intelligence/CHANGE_IMPACT.yaml": ("change", "inputs", "outputs", "data", "events", "consumers", "compatibility", "status"),
    "templates/intelligence/TURN_CONTEXT_MANIFEST.yaml": ("runtime", "project", "task", "context", "freshness", "requirements", "fail_policy"),
}.items():
    doc = load_yaml(ROOT / rel) or {}
    for key in keys:
        if key not in doc:
            errors.append(f"{rel} missing top-level key: {key}")

for rel, keys in {
    "templates/harness/HARNESS_RESOLUTION.yaml": ("harness", "runtime", "project", "instructions", "intelligence", "state", "system"),
    "templates/harness/ADAPTER_MANIFEST.yaml": ("id", "runtime", "detection", "integration", "ownership", "bootstrap", "verification", "uninstall"),
    "templates/harness/INSTALLATION_OWNERSHIP.yaml": ("system", "harness", "owned_resources", "adapters", "preservation_policy"),
    "harness/adapters/REGISTRY.yaml": ("adapters",),
}.items():
    doc = load_yaml(ROOT / rel) or {}
    for key in keys:
        if key not in doc:
            errors.append(f"{rel} missing top-level key: {key}")

for helper in ("scripts/harness_resolve.py", "scripts/project_intelligence.py", "scripts/retrieval_intelligence.py", "scripts/retrieval_evaluation.py", "scripts/structural_retrieval_trial.py", "scripts/retrieval_embedding_trial.py", "scripts/retrieval_embedding_trial_summary.py", "scripts/turn_context_hook.py", "scripts/manage_runtime_adapter.py", "scripts/requirements_traceability.py"):
    helper_path = ROOT / helper
    if helper_path.exists():
        compiled = subprocess.run([sys.executable, "-m", "py_compile", str(helper_path)], capture_output=True, text=True)
        if compiled.returncode != 0:
            errors.append(f"{helper} syntax failed: {compiled.stderr.strip()}")

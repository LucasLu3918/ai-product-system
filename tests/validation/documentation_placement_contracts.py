from .static_contracts import ROOT, errors
import subprocess
import sys
import yaml

required = [
    ROOT / "config/documentation-placement.yaml",
    ROOT / "scripts/documentation_placement.py",
    ROOT / "docs/human/index.md",
    ROOT / "docs/human/.vitepress/config.mts",
    ROOT / "docs/human/TECHNOLOGY_GUIDE.md",
    ROOT / "docs/human/EVOLUTION_RADAR_OVERVIEW.md",
    ROOT / "scripts/install.sh",
    ROOT / "scripts/install.ps1",
    ROOT / ".github/workflows/docs-site.yml",
    ROOT / ".github/workflows/installation-entrypoints.yml",
]
for path in required:
    if not path.exists():
        errors.append(f"Missing documentation/install artifact: {path.relative_to(ROOT)}")

script = ROOT / "scripts/documentation_placement.py"
if script.exists():
    proc = subprocess.run(
        [sys.executable, "-m", "py_compile", str(script)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        errors.append(f"documentation_placement.py syntax failed: {proc.stderr.strip()}")

    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    if proc.returncode != 0:
        errors.append(
            f"documentation placement static audit failed: {proc.stdout.strip()} {proc.stderr.strip()}"
        )

config_path = ROOT / "config/documentation-placement.yaml"
if config_path.exists():
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    policy = config.get("policy") or {}
    for key in (
        "current_behavior_is_topic_oriented",
        "legacy_html_append_forbidden",
        "all_added_lines_must_match_canonical_placement",
        "new_topics_require_contract_update",
    ):
        if policy.get(key) is not True:
            errors.append(f"documentation placement policy must enable {key}")

    migration_bases = policy.get("one_time_structure_migration_bases") or []
    if migration_bases:
        errors.append("Human-doc structure migration is complete; future documentation placement must not retain bypass bases")

    strict_docs = {
        path
        for path, spec in (config.get("current_behavior_docs") or {}).items()
        if isinstance(spec, dict) and spec.get("strict_h2")
    }
    for expected in (
        "docs/human/USER_GUIDE.md",
        "docs/human/ARCHITECTURE_OVERVIEW.md",
        "docs/human/TECHNOLOGY_GUIDE.md",
        "docs/human/EVOLUTION_RADAR.md",
        "docs/human/EVOLUTION_RADAR_OVERVIEW.md",
        "docs/human/INSTALLATION.md",
    ):
        if expected not in strict_docs:
            errors.append(f"Current-behavior structure must be strict for {expected}")

package = (ROOT / "package.json").read_text(encoding="utf-8") if (ROOT / "package.json").exists() else ""
for marker in ('"vitepress": "1.6.4"', '"docs:build": "vitepress build docs/human"'):
    if marker not in package:
        errors.append(f"package.json missing docs-site contract: {marker}")

install = (ROOT / "scripts/install.sh").read_text(encoding="utf-8") if (ROOT / "scripts/install.sh").exists() else ""
for marker in ("AIPS_INSTALL_DIR", "git clone", 'exec "$INSTALL_DIR/bin/aips" install'):
    if marker not in install:
        errors.append(f"install.sh missing managed-install contract: {marker}")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
if "gh repo clone" in readme or "\ncd " in readme:
    errors.append("README public install path must not teach clone/cd preparation")

user_guide = (ROOT / "docs/human/USER_GUIDE.md").read_text(encoding="utf-8")
for topic in (
    "Creative Direction、Style 與 Brand",
    "Visual Polish 與 Product Consistency",
    "Logging、Observability 與 Operations",
    "Product Delivery lifecycle",
):
    if topic not in user_guide:
        errors.append(f"USER_GUIDE lost current AIPS capability explanation: {topic}")

placement_text = script.read_text(encoding="utf-8") if script.exists() else ""
for marker in ("git_base_resolves", "one_time_structure_migration_bases", "if base and git_base_resolves(base)"):
    if marker not in placement_text:
        errors.append(f"documentation placement helper missing migration/install-copy safety contract: {marker}")

docs_workflow = (ROOT / ".github/workflows/docs-site.yml").read_text(encoding="utf-8")
for marker in ("pages_configured", "SKIPPED_NOT_CONFIGURED", "$GITHUB_API_URL/repos/$GITHUB_REPOSITORY/pages"):
    if marker not in docs_workflow:
        errors.append(f"docs-site workflow missing truthful Pages preflight contract: {marker}")

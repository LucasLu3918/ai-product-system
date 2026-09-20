from pathlib import Path
import subprocess
import sys

from .static_contracts import ROOT, errors

required = (
    ROOT / "orchestration/EVOLUTION_RADAR.md",
    ROOT / "config/evolution-sources.yaml",
    ROOT / "templates/evolution/EVOLUTION_RADAR.yaml",
    ROOT / "scripts/evolution_radar.py",
    ROOT / "scripts/evolution_radar_rollup.py",
    ROOT / "scripts/evolution_analysis.py",
    ROOT / "config/evolution-analyzer.yaml",
    ROOT / "templates/evolution/EVOLUTION_ANALYZER_PROMPT.md",
    ROOT / "templates/evolution/EVOLUTION_ANALYZER_RESULT.schema.json",
    ROOT / ".github/workflows/evolution-radar.yml",
    ROOT / "tests/evidence/evolution_radar_lifecycle.py",
)
for path in required:
    if not path.exists():
        errors.append(f"Missing Evolution Radar artifact: {path.relative_to(ROOT)}")

for path in (
    ROOT / "scripts/evolution_radar.py",
    ROOT / "scripts/evolution_radar_rollup.py",
    ROOT / "scripts/evolution_analysis.py",
    ROOT / "tests/evidence/evolution_radar_lifecycle.py",
):
    if not path.exists():
        continue
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Evolution Radar syntax failed: {path.relative_to(ROOT)}: {compiled.stderr.strip()}")

config_check = ROOT / "scripts/evolution_radar.py"
if config_check.exists():
    result = subprocess.run(
        [sys.executable, str(config_check), "validate-config", "--config", str(ROOT / "config/evolution-sources.yaml")],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        errors.append(f"Evolution Radar source config failed: {result.stdout.strip()} {result.stderr.strip()}")

    script_text = config_check.read_text(encoding="utf-8")
    for contract in (
        "resolve_public_destination",
        "socket.getaddrinfo",
        "ipaddress.ip_address",
        "context.wrap_socket",
        "server_hostname=hostname",
        "max_response_bytes",
        "max_redirects",
        "public source redirect loop detected",
    ):
        if contract not in script_text:
            errors.append(f"Evolution Radar network safety contract missing: {contract}")

source_config = ROOT / "config/evolution-sources.yaml"
if source_config.exists():
    config_text = source_config.read_text(encoding="utf-8")
    for contract in (
        "public_only: true",
        "credentials_in_repository: false",
        "minimum_community_sources_when_available: 5",
        "target_community_sources: 6",
        "max_items_per_source: 8",
        "max_raw_signals: 50",
        "role: community",
        "role: primary",
        "max_response_bytes:",
        "max_redirects:",
    ):
        if contract not in config_text:
            errors.append(f"Evolution Radar source policy missing: {contract}")

lifecycle = ROOT / "tests/evidence/evolution_radar_lifecycle.py"
if lifecycle.exists():
    try:
        result = subprocess.run([sys.executable, str(lifecycle)], capture_output=True, text=True, timeout=45)
    except subprocess.TimeoutExpired:
        errors.append("Evolution Radar lifecycle timed out after 45 seconds")
    else:
        if result.returncode != 0:
            errors.append(f"Evolution Radar lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")

# provider-neutral semantic handoff contract
analyzer_config = ROOT / "config/evolution-analyzer.yaml"
if analyzer_config.exists():
    analyzer_text = analyzer_config.read_text(encoding="utf-8")
    for contract in (
        "fallback: handoff",
        "optional: true",
        "credential_required: false",
        "result_schema_path:",
        "binding_script: scripts/evolution_analysis.py",
        "local_preanalysis:",
        "mode: deterministic_title_metadata_only",
        "credential_required: false",
        "external_network_required: false",
        "preserve_semantic_state: ANALYSIS_PENDING",
        "selection_budget:",
        "shortlist_max: 12",
        "semantic_analysis_max: 10",
        "actionable_recommendations_max: 5",
    ):
        if contract not in analyzer_text:
            errors.append(f"Evolution Radar analyzer config missing provider-neutral contract: {contract}")

workflow_path = ROOT / ".github/workflows/evolution-radar.yml"
if workflow_path.exists():
    workflow_text = workflow_path.read_text(encoding="utf-8")
    for contract in (
        "semantic_provider:",
        "Build deterministic local pre-analysis",
        "scripts/evolution_analysis.py preanalyze",
        "preanalysis-validate",
        "--preanalysis evolution-local-preanalysis.md",
        "Build provider-neutral semantic handoff",
        "scripts/evolution_analysis.py handoff",
        "--preanalysis evolution-local-preanalysis.yaml",
        "--package evolution-analysis-package.yaml",
        "--handoff evolution-analysis-handoff.md",
        "selected=\"handoff\"",
        "quarterly",
        "0 2 1 1,4,7,10 *",
        "quarterly-rollup",
    ):
        if contract not in workflow_text:
            errors.append(f"Evolution Radar workflow missing provider-neutral contract: {contract}")

rollup_script = ROOT / "scripts/evolution_radar_rollup.py"
if rollup_script.exists():
    rollup_text = rollup_script.read_text(encoding="utf-8")
    for contract in (
        "def quarterly_rollup(",
        "def quarter_months(",
        'mode": "quarterly"',
        "monthly_evidence_count",
        "months_reviewed",
        'state": "ANALYSIS_PENDING"',
    ):
        if contract not in rollup_text:
            errors.append(f"Evolution Radar quarterly deterministic review contract missing: {contract}")

analysis_script = ROOT / "scripts/evolution_analysis.py"
if analysis_script.exists():
    analysis_text = analysis_script.read_text(encoding="utf-8")
    for contract in (
        "build_local_preanalysis",
        "validate_local_preanalysis",
        "DETERMINISTIC_PREANALYSIS",
        "semantic_suitability_inferred",
        "recommendation_state_mutated",
        "title_and_evidence_metadata_only",
        "PREANALYSIS_START",
        "_build_review_queue",
        "deterministic_preanalysis_rank",
        "max_actionable_recommendations",
        "community discovery signal requires primary-source corroboration before ADOPT",
    ):
        if contract not in analysis_text:
            errors.append(f"Evolution Radar local preanalysis contract missing: {contract}")

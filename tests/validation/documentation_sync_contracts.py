import os
import subprocess
import sys

import yaml

from .static_contracts import ROOT, errors

sys.path.insert(0, str(ROOT / 'scripts'))
try:
    from publish_preflight_policy import documentation_impact

    impact = documentation_impact(['scripts/evolution_decision.py'], ROOT)
    metrics = impact.get('amplification') or {}
    if metrics.get('direct_path_count') != 1:
        errors.append('Documentation impact amplification must count unique direct paths')
    if metrics.get('closure_path_count') != len(impact.get('closure') or []):
        errors.append('Documentation impact amplification must match the recursive closure')
    if metrics.get('required_addition_count') != len(impact.get('required_additions') or []):
        errors.append('Documentation impact amplification must match required additions')
    if metrics.get('closure_to_direct_ratio') != round(metrics.get('closure_path_count', 0), 3):
        errors.append('Documentation impact amplification ratio must be deterministic')
except (ImportError, OSError, RuntimeError, TypeError, ValueError, KeyError, yaml.YAMLError) as exc:
    errors.append(f'Documentation impact amplification contract failed: {exc}')

required = (
    ROOT / 'config/documentation-sync.yaml',
    ROOT / 'scripts/documentation_sync.py',
    ROOT / 'orchestration/DOCUMENTATION_SYNC.md',
    ROOT / 'docs/human/DOCUMENTATION_SYNC.md',
    ROOT / 'docs/human/TECHNOLOGY_GUIDE.md',
    ROOT / 'docs/human/EVOLUTION_RADAR_OVERVIEW.md',
    ROOT / 'docs/human/TECHNOLOGY_GUIDE.html',
    ROOT / 'docs/human/EVOLUTION_RADAR_OVERVIEW.html',
)
for path in required:
    if not path.exists():
        errors.append(f'Missing documentation consistency artifact: {path.relative_to(ROOT)}')

script = ROOT / 'scripts/documentation_sync.py'
if script.exists():
    compiled = subprocess.run([sys.executable, '-m', 'py_compile', str(script)], capture_output=True, text=True)
    if compiled.returncode:
        errors.append(f'Documentation sync syntax failed: {compiled.stderr.strip()}')
    sys.path.insert(0, str(ROOT / 'scripts'))
    try:
        import documentation_sync as docs_sync
        config = yaml.safe_load((ROOT / 'config/documentation-sync.yaml').read_text(encoding='utf-8')) or {}
        for error in docs_sync.validate_config(config):
            errors.append(f'Documentation sync config: {error}')
        missing = docs_sync.evaluate_changes(['scripts/evolution_decision.py'], config)
        for expected in (
            'docs/human/TECHNOLOGY_GUIDE.md',
            'docs/human/EVOLUTION_RADAR.md',
            'orchestration/EVOLUTION_RADAR.md',
        ):
            if not any(expected in item for item in missing):
                errors.append(f'Documentation sync did not require {expected}')
        complete = [
            'scripts/evolution_decision.py',
            'docs/human/EVOLUTION_RADAR.md',
            'docs/human/EVOLUTION_RADAR_OVERVIEW.md',
            'orchestration/EVOLUTION_RADAR.md',
            'orchestration/EXECUTION_ISOLATION.md',
            'docs/human/TECHNOLOGY_GUIDE.md',
        ]
        if docs_sync.evaluate_changes(complete, config):
            errors.append('Documentation sync rejected a complete Evolution documentation update')
        base = os.environ.get('AIPS_DOCS_DIFF_BASE', '').strip()
        if base and base != '0' * 40:
            for error in docs_sync.evaluate_changes(docs_sync.changed_files_from_git(base, 'HEAD'), config):
                errors.append(f'Documentation consistency: {error}')
    except (ImportError, OSError, RuntimeError, TypeError, ValueError, KeyError, yaml.YAMLError) as exc:
        errors.append(f'Documentation sync validation failed: {exc}')

workflow = ROOT / '.github/workflows/validate.yml'
if workflow.exists():
    workflow_text = workflow.read_text(encoding='utf-8')
    for contract in (
        'AIPS_DOCS_DIFF_BASE:',
        'fetch-depth: 0',
        "github.ref_name != github.event.repository.default_branch",
        "format('origin/{0}', github.event.repository.default_branch)",
    ):
        if contract not in workflow_text:
            errors.append(f'validate workflow missing documentation diff-base contract: {contract}')

for rel in ('docs/human/TECHNOLOGY_GUIDE.html', 'docs/human/EVOLUTION_RADAR_OVERVIEW.html'):
    path = ROOT / rel
    if path.exists():
        text = path.read_text(encoding='utf-8')
        for contract in (
            'name="aips-audience" content="human"',
            'name="aips-sync-policy" content="documentation-sync-v1"',
            'DOCUMENTATION_MAP.md',
        ):
            if contract not in text:
                errors.append(f'{rel} missing Human documentation contract: {contract}')

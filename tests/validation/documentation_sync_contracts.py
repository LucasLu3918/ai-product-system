import os
import subprocess
import sys
import yaml

from .static_contracts import ROOT, errors

required = (
    ROOT / 'config/documentation-sync.yaml',
    ROOT / 'scripts/documentation_sync.py',
    ROOT / 'orchestration/DOCUMENTATION_SYNC.md',
    ROOT / 'docs/human/DOCUMENTATION_SYNC.md',
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
            'docs/human/TECHNOLOGY_GUIDE.html',
            'docs/human/EVOLUTION_RADAR.md',
            'orchestration/EVOLUTION_RADAR.md',
        ):
            if not any(expected in item for item in missing):
                errors.append(f'Documentation sync did not require {expected}')
        complete = [
            'scripts/evolution_decision.py',
            'docs/human/EVOLUTION_RADAR.md',
            'docs/human/EVOLUTION_RADAR_OVERVIEW.html',
            'orchestration/EVOLUTION_RADAR.md',
            'orchestration/EXECUTION_ISOLATION.md',
            'docs/human/TECHNOLOGY_GUIDE.html',
        ]
        if docs_sync.evaluate_changes(complete, config):
            errors.append('Documentation sync rejected a complete Evolution documentation update')
        base = os.environ.get('AIPS_DOCS_DIFF_BASE', '').strip()
        if base and base != '0' * 40:
            for error in docs_sync.evaluate_changes(docs_sync.changed_files_from_git(base, 'HEAD'), config):
                errors.append(f'Documentation consistency: {error}')
    except Exception as exc:
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

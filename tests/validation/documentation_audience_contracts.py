import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from .static_contracts import ROOT, errors

required = (
    ROOT / 'config/documentation-audience.yaml',
    ROOT / 'scripts/documentation_audience.py',
    ROOT / 'docs/human/DOCUMENTATION_MAP.md',
    ROOT / 'docs/human/TECHNOLOGY_GUIDE.html',
)
for path in required:
    if not path.exists():
        errors.append(f'Missing documentation audience artifact: {path.relative_to(ROOT)}')

script = ROOT / 'scripts/documentation_audience.py'
if script.exists():
    compiled = subprocess.run([sys.executable, '-m', 'py_compile', str(script)], capture_output=True, text=True)
    if compiled.returncode:
        errors.append(f'Documentation audience syntax failed: {compiled.stderr.strip()}')
    sys.path.insert(0, str(ROOT / 'scripts'))
    try:
        import documentation_audience as audience
        config = yaml.safe_load((ROOT / 'config/documentation-audience.yaml').read_text(encoding='utf-8')) or {}
        for error in audience.validate_config(config):
            errors.append(f'Documentation audience config: {error}')
        for error in audience.validate_layout(ROOT, config):
            errors.append(f'Documentation audience layout: {error}')
        if config.get('human_root') != 'docs/human':
            errors.append('Human documentation root must remain docs/human')
        if config.get('standalone_human_prefix') != 'HUMAN_':
            errors.append('Standalone Human artifact prefix must remain HUMAN_')
        bad = dict(config)
        bad['standalone_human_documents'] = ['reports/review.md']
        if not audience.validate_config(bad):
            errors.append('Unprefixed standalone Human artifact must fail audience validation')
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp)
            (fixture / 'docs/human').mkdir(parents=True)
            (fixture / 'docs/ARCHITECTURE.md').write_text('# Architecture\n', encoding='utf-8')
            (fixture / 'docs/.DS_Store').write_bytes(b'local metadata')
            (fixture / '.gitignore').write_text('.DS_Store\n', encoding='utf-8')
            subprocess.run(['git', 'init', '-q'], cwd=fixture, check=True)
            fixture_config = {
                'version': 1,
                'human_root': 'docs/human',
                'standalone_human_prefix': 'HUMAN_',
                'shared_docs': ['docs/ARCHITECTURE.md'],
                'human_documents': [],
                'standalone_human_documents': [],
                'legacy_paths': {},
                'scan_roots': [],
            }
            ignored_errors = audience.validate_layout(fixture, fixture_config)
            if any('DS_Store' in item for item in ignored_errors):
                errors.append('Documentation audience must ignore Git-ignored local metadata')
        source = script.read_text(encoding='utf-8')
        for contract in ('aips-audience', 'standalone_human_documents', 'standalone_human_prefix'):
            if contract not in source:
                errors.append(f'Documentation audience enforcement missing: {contract}')
    except Exception as exc:
        errors.append(f'Documentation audience validation failed: {exc}')

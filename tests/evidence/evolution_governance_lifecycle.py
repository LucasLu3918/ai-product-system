#!/usr/bin/env python3
from __future__ import annotations

import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))

import evolution_analysis as analysis  # noqa: E402
import evolution_decision as decision  # noqa: E402
import evolution_trial as trial  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(root: Path, *args: str) -> str:
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def evidence(revision: str, fingerprint: str) -> dict:
    return {
        'version': 1,
        'run': {
            'mode': 'weekly',
            'generated_at': '2026-09-18T00:00:00Z',
            'repository_revision': revision,
            'analyzer': {'status': 'unavailable', 'provider': None, 'model': None},
        },
        'sources': {'configured': ['source'], 'attempted': ['source'], 'failures': []},
        'signals': [{
            'fingerprint': fingerprint,
            'title': 'Prototype signal',
            'canonical_url': 'https://example.test/prototype',
            'source_id': 'source',
            'published_at': '2026-09-17',
            'retrieved_at': '2026-09-18T00:00:00Z',
            'summary': '',
            'recurrence_count': 1,
            'duplicate_of': None,
        }],
        'recommendations': [{
            'signal_fingerprint': fingerprint,
            'state': 'ANALYSIS_PENDING',
            'aips_current_state': '',
            'benefit': '',
            'cost_complexity': '',
            'reliability_security': '',
            'confidence': None,
            'uncertainty': 'Semantic analyzer unavailable; no suitability conclusion inferred.',
            'example': '',
            'reuse_extension_path': [],
            'architecture_diagram_review_if_adopted': False,
        }],
        'summary': {
            'signal_count': 1,
            'deduplicated_count': 1,
            'recommendation_count': 1,
            'actionable_count': 0,
            'zero_recommendations_valid': True,
        },
        'authority': {
            'code_change_authorized': False,
            'branch_or_pr_authorized': False,
            'merge_authorized': False,
            'release_authorized': False,
            'human_decision_required': True,
        },
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / 'repo'
        root.mkdir()
        git(root, 'init')
        git(root, 'config', 'user.name', 'AIPS Test')
        git(root, 'config', 'user.email', 'aips@example.test')
        (root / 'README.md').write_text('baseline\n', encoding='utf-8')
        git(root, 'add', 'README.md')
        git(root, 'commit', '-m', 'baseline')
        revision = git(root, 'rev-parse', 'HEAD')

        fingerprint = 'sha256:' + '2' * 64
        raw = evidence(revision, fingerprint)
        provider = {'recommendations': [{
            'signal_fingerprint': fingerprint,
            'state': 'TRIAL',
            'aips_current_state': 'No prototype exists.',
            'gap': 'Need bounded evidence.',
            'benefit': 'Tests feasibility.',
            'cost_complexity': 'Low.',
            'reliability_security': 'No protected assets touched.',
            'maturity': 'experimental',
            'confidence': 0.7,
            'uncertainty': 'Synthetic lifecycle evidence.',
            'example': 'Create a small prototype file.',
            'reuse_extension_path': ['Execution Isolation'],
            'evidence_refs': ['https://example.test/prototype'],
            'architecture_diagram_review_if_adopted': False,
        }]}
        analyzed = analysis.finalize_provider_result(
            raw, provider, provider='test', model='test', analyzed_at='2026-09-18T01:00:00Z'
        )
        assessed = analysis.apply_analysis(raw, analyzed)
        human = decision.create_decision(
            assessed,
            signal_fingerprint=fingerprint,
            decision='TRIAL',
            approved_scope='Prototype file only',
            approved_paths=['prototype/**'],
            reason='Run bounded experiment.',
            decided_by='maintainer',
            decided_at='2026-09-18T02:00:00Z',
            current_revision=revision,
        )
        config = yaml.safe_load((ROOT / 'config/evolution-trial.yaml').read_text(encoding='utf-8')) or {}
        config = copy.deepcopy(config)
        config['validation']['command'] = "python -c 'import sys; sys.exit(0)'"
        plan = trial.build_plan(human, config, current_revision=revision)

        (root / 'prototype').mkdir()
        (root / 'prototype' / 'result.txt').write_text('trial evidence\n', encoding='utf-8')
        passed = trial.evaluate(
            plan, config, worktree=root, agent_outcome='success',
            started_at='2026-09-18T02:01:00Z', agent_summary='bounded prototype'
        )
        require(passed['result']['status'] == 'PASS', 'approved bounded change must PASS')
        require(not trial.validate_result(passed), 'PASS Trial Report must validate')

        git(root, 'reset', '--hard', revision)
        git(root, 'clean', '-fd')
        (root / '.github' / 'workflows').mkdir(parents=True)
        (root / '.github' / 'workflows' / 'bad.yml').write_text('name: bad\n', encoding='utf-8')
        broad = copy.deepcopy(plan)
        broad['trial']['approved_paths'] = ['**']
        forbidden = trial.evaluate(
            broad, config, worktree=root, agent_outcome='success',
            started_at='2026-09-18T02:02:00Z'
        )
        require(forbidden['result']['status'] == 'FAIL', 'forbidden governance path must FAIL')
        require(any('forbidden path changed' in item for item in forbidden['result']['violations']), 'forbidden path violation must be explicit')

        git(root, 'reset', '--hard', revision)
        git(root, 'clean', '-fd')
        (root / 'prototype').mkdir()
        (root / 'prototype' / 'committed.txt').write_text('bad commit\n', encoding='utf-8')
        git(root, 'add', 'prototype/committed.txt')
        git(root, 'commit', '-m', 'trial must not commit')
        committed = trial.evaluate(
            plan, config, worktree=root, agent_outcome='success',
            started_at='2026-09-18T02:03:00Z'
        )
        require(committed['result']['status'] == 'FAIL', 'Trial-created commit must FAIL')
        require(any('must not create commits' in item for item in committed['result']['violations']), 'commit violation must be explicit')

        blocked = trial.blocked_result(plan, 'provider unavailable')
        require(blocked['result']['status'] == 'BLOCKED', 'provider failure must be BLOCKED')
        require(not trial.validate_result(blocked), 'BLOCKED Trial Report must validate')

    print('EVOLUTION GOVERNANCE LIFECYCLE PASSED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

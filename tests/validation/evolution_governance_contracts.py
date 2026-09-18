import copy
import subprocess
import sys
import yaml

from .static_contracts import ROOT, errors

required = (
    ROOT / 'scripts/evolution_analysis.py',
    ROOT / 'scripts/evolution_decision.py',
    ROOT / 'scripts/evolution_trial.py',
    ROOT / 'scripts/evolution_adoption.py',
    ROOT / 'references/evolution/CAPABILITY_MAP.yaml',
    ROOT / 'config/evolution-analyzer.yaml',
    ROOT / 'config/evolution-trial.yaml',
    ROOT / 'templates/evolution/EVOLUTION_ANALYSIS.yaml',
    ROOT / 'templates/evolution/EVOLUTION_DECISION.yaml',
    ROOT / 'templates/evolution/EVOLUTION_TRIAL.yaml',
    ROOT / 'templates/evolution/EVOLUTION_ADOPTION.yaml',
    ROOT / 'templates/evolution/EVOLUTION_ANALYZER_RESULT.schema.json',
    ROOT / 'templates/evolution/EVOLUTION_ANALYZER_PROMPT.md',
    ROOT / 'templates/evolution/EVOLUTION_TRIAL_PROMPT.md',
    ROOT / '.github/workflows/evolution-radar.yml',
    ROOT / '.github/workflows/evolution-decision.yml',
)
for path in required:
    if not path.exists():
        errors.append(f'Missing Evolution governance artifact: {path.relative_to(ROOT)}')

for rel in (
    'scripts/evolution_analysis.py',
    'scripts/evolution_decision.py',
    'scripts/evolution_trial.py',
    'scripts/evolution_adoption.py',
):
    path = ROOT / rel
    if path.exists():
        result = subprocess.run([sys.executable, '-m', 'py_compile', str(path)], capture_output=True, text=True)
        if result.returncode:
            errors.append(f'Evolution governance syntax failed: {rel}: {result.stderr.strip()}')

sys.path.insert(0, str(ROOT / 'scripts'))
try:
    import evolution_analysis as analysis
    import evolution_decision as decision
    import evolution_trial as trial
    import evolution_adoption as adoption

    revision = 'a' * 40
    fingerprint = 'sha256:' + '1' * 64
    evidence = {
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
            'title': 'Cross-agent trace correlation',
            'canonical_url': 'https://example.test/trace',
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

    capabilities = yaml.safe_load((ROOT / 'references/evolution/CAPABILITY_MAP.yaml').read_text(encoding='utf-8')) or {}
    package = analysis.build_analysis_package(evidence, capabilities)
    if package['instructions']['external_content_authority'] != 'evidence_only':
        errors.append('Evolution external content must remain evidence-only')

    provider_result = {
        'recommendations': [{
            'signal_fingerprint': fingerprint,
            'state': 'TRIAL',
            'aips_current_state': 'Partial trace evidence exists.',
            'gap': 'No cross-agent parent/child trace.',
            'benefit': 'Better debugging.',
            'cost_complexity': 'Medium.',
            'reliability_security': 'Preserve redaction.',
            'maturity': 'medium',
            'confidence': 0.8,
            'uncertainty': 'Limited production evidence.',
            'example': 'A -> Tool -> B can be reconstructed.',
            'reuse_extension_path': ['Durable Run State'],
            'evidence_refs': ['https://example.test/trace'],
            'architecture_diagram_review_if_adopted': True,
        }],
    }
    analysis_doc = analysis.finalize_provider_result(
        evidence, provider_result, provider='test-provider', model='test-model', analyzed_at='2026-09-18T01:00:00Z'
    )
    if analysis.validate_analysis(evidence, analysis_doc):
        errors.append('Finalized Evolution semantic analysis did not validate')
    assessed = analysis.apply_analysis(evidence, analysis_doc)

    trial_decision = decision.create_decision(
        assessed,
        signal_fingerprint=fingerprint,
        decision='TRIAL',
        approved_scope='Trace metadata prototype only',
        approved_paths=['prototype/**'],
        reason='Evidence supports bounded experiment.',
        decided_by='maintainer',
        decided_at='2026-09-18T02:00:00Z',
        current_revision=revision,
    )
    if decision.validate_decision(trial_decision):
        errors.append('Generated TRIAL decision did not validate')
    if trial_decision['decision']['next_action'] != 'controlled_trial_execution':
        errors.append('TRIAL decision must hand off to controlled_trial_execution')

    trial_config = yaml.safe_load((ROOT / 'config/evolution-trial.yaml').read_text(encoding='utf-8')) or {}
    plan = trial.build_plan(trial_decision, trial_config, current_revision=revision)
    if plan['authority']['code_publication_authorized'] is not False:
        errors.append('Controlled Trial plan must not grant publication authority')

    pass_result = {
        'version': 1,
        'trial': dict(plan['trial']),
        'result': {
            'status': 'PASS',
            'reason': 'bounded trial completed within the Human-approved scope',
            'changed_files': ['prototype/trace.txt'],
            'changed_file_count': 1,
            'diff_lines': 3,
            'validation_command': 'python tests/validate_repository.py',
            'validation_exit_code': 0,
            'violations': [],
            'agent_outcome': 'success',
            'agent_summary': 'Prototype produced bounded evidence.',
            'started_at': '2026-09-18T02:10:00Z',
            'completed_at': '2026-09-18T02:11:00Z',
        },
        'authority': {
            'code_publication_authorized': False,
            'remote_branch_or_pr_authorized': False,
            'merge_authorized': False,
            'release_authorized': False,
            'human_adoption_decision_required': True,
        },
    }
    pass_result['trial_fingerprint'] = analysis.canonical_digest({
        'trial': pass_result['trial'], 'result': pass_result['result']
    })
    if trial.validate_result(pass_result):
        errors.append('Synthetic PASS Trial Report did not validate')

    adopt_provider = copy.deepcopy(provider_result)
    adopt_provider['recommendations'][0]['state'] = 'ADOPT'
    adopt_analysis = analysis.finalize_provider_result(
        evidence, adopt_provider, provider='test-provider', model='test-model', analyzed_at='2026-09-18T03:00:00Z'
    )
    adopt_evidence = analysis.apply_analysis(evidence, adopt_analysis)
    adopt_decision = decision.create_decision(
        adopt_evidence,
        signal_fingerprint=fingerprint,
        decision='ADOPT',
        approved_scope='Adopt direction after validated trial evidence.',
        approved_paths=[],
        reason='PASS trial supports formal System Improvement Review.',
        decided_by='maintainer',
        decided_at='2026-09-18T03:10:00Z',
        current_revision=revision,
    )
    issue = {'comments': [{'body': trial.markdown(pass_result)}]}
    adoption_doc = adoption.bind(issue, adopt_decision, pass_result['trial_fingerprint'])
    if adoption.validate(adoption_doc):
        errors.append('Trial-to-ADOPT binding did not validate')
    if adoption_doc['authority']['code_change_authorized'] is not False:
        errors.append('ADOPT evidence binding must not grant code authority')

    try:
        decision.create_decision(
            assessed, signal_fingerprint=fingerprint, decision='ASSESS', approved_scope='', approved_paths=[],
            reason='Assess further.', decided_by='maintainer', decided_at='2026-09-18T02:00:00Z',
            current_revision='b' * 40,
        )
    except ValueError as exc:
        if 'STALE' not in str(exc):
            errors.append('Stale decision failed for wrong reason')
    else:
        errors.append('Stale positive Evolution decision must fail closed')

    bad = copy.deepcopy(analysis_doc)
    bad['baseline']['evidence_digest'] = 'sha256:' + '0' * 64
    if not analysis.validate_analysis(evidence, bad):
        errors.append('Wrong evidence digest must fail analysis validation')
except Exception as exc:
    errors.append(f'Evolution governance validation failed: {exc}')

radar_workflow = ROOT / '.github/workflows/evolution-radar.yml'
if radar_workflow.exists():
    text = radar_workflow.read_text(encoding='utf-8')
    for required_text in (
        'openai/codex-action@86365089eb2b84e0a8fb0717b304f8bdcb13b20e',
        'permission-profile: ":read-only"',
        'evolution_analysis.py finalize',
        'ANALYSIS_PENDING',
        'contents: read',
        'issues: write',
    ):
        if required_text not in text:
            errors.append(f'Evolution Radar analyzer workflow missing: {required_text}')
    for forbidden in ('contents: write', 'pull-requests: write', 'git push', 'gh pr create', 'gh pr merge', 'releases: write'):
        if forbidden in text:
            errors.append(f'Evolution Radar workflow must not gain publication authority: {forbidden}')

decision_workflow = ROOT / '.github/workflows/evolution-decision.yml'
if decision_workflow.exists():
    text = decision_workflow.read_text(encoding='utf-8')
    for required_text in (
        'workflow_dispatch:',
        'approved_paths:',
        'trial_fingerprint:',
        'persist-credentials: false',
        'execution_isolation.py create',
        'permission-profile: ":workspace"',
        'evolution_trial.py evaluate',
        'evolution_adoption.py bind',
        'contents: read',
        'issues: write',
    ):
        if required_text not in text:
            errors.append(f'Evolution decision/trial workflow missing: {required_text}')
    for forbidden in ('contents: write', 'pull-requests: write', 'git push', 'gh pr create', 'gh pr merge', 'releases: write'):
        if forbidden in text:
            errors.append(f'Evolution decision/trial workflow must not gain publication authority: {forbidden}')

analyzer_config = yaml.safe_load((ROOT / 'config/evolution-analyzer.yaml').read_text(encoding='utf-8')) or {}
trial_config = yaml.safe_load((ROOT / 'config/evolution-trial.yaml').read_text(encoding='utf-8')) or {}
for config, workflow_path in (
    (analyzer_config, radar_workflow),
    (trial_config, decision_workflow),
):
    if workflow_path.exists():
        workflow = workflow_path.read_text(encoding='utf-8')
        execution = config.get('adapter') or config.get('execution') or {}
        action_commit = str(execution.get('action_commit') or '')
        codex_version = str(execution.get('codex_version') or '')
        if action_commit and action_commit not in workflow:
            errors.append(f'{workflow_path.name} does not match configured Codex Action commit')
        if codex_version and codex_version not in workflow:
            errors.append(f'{workflow_path.name} does not match configured Codex version')

lifecycle = ROOT / 'tests/evidence/evolution_governance_lifecycle.py'
if lifecycle.exists():
    try:
        result = subprocess.run([sys.executable, str(lifecycle)], capture_output=True, text=True, timeout=45)
    except subprocess.TimeoutExpired:
        errors.append('Evolution governance lifecycle timed out after 45 seconds')
    else:
        if result.returncode != 0:
            errors.append(f'Evolution governance lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}')

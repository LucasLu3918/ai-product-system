from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_secret_leakage as scanner
import governance_guard as guard
import publication_authority as auth
import publication_planning as planning
import publication_scan_evidence as evidence
import publication_ship as ship
from publication_authority import PublicationError
from publication_commands import CommandError

REAL_ACTION = auth.action


class PublicationFixture(unittest.TestCase):
    """Personal-mode fixture: local bare remote; only GitHub-URL-bound PR observations are mocked."""

    def git(self, cwd, *args):
        return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()

    def setUp(self):
        clean_environment = patch.dict(os.environ)
        clean_environment.start()
        self.addCleanup(clean_environment.stop)
        for key in list(os.environ):
            if key in {'GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_CONFIG_PARAMETERS'} or key.startswith(('GIT_CONFIG_COUNT', 'GIT_CONFIG_KEY_', 'GIT_CONFIG_VALUE_')):
                os.environ.pop(key)
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        os.environ['XDG_CACHE_HOME'] = str(self.root / 'cache')
        self.repo, self.remote = self.root / 'repo', self.root / 'remote.git'
        self.repo.mkdir()
        self.git(self.repo, 'init', '-b', 'main')
        self.git(self.repo, 'config', 'user.name', 'Fixture')
        self.git(self.repo, 'config', 'user.email', 'fixture' + '@' + 'example.test')
        (self.repo / 'file.txt').write_text('base\n')
        self.git(self.repo, 'add', '.')
        self.git(self.repo, 'commit', '-m', 'base')
        self.git(self.root, 'init', '--bare', str(self.remote))
        self.git(self.remote, 'symbolic-ref', 'HEAD', 'refs/heads/main')
        self.git(self.repo, 'remote', 'add', 'origin', str(self.remote))
        self.git(self.repo, 'push', 'origin', 'main')
        self.git(self.repo, 'switch', '-c', 'codex/ship1')
        (self.repo / 'file.txt').write_text('candidate\n')
        self.git(self.repo, 'commit', '-am', 'candidate')
        self.head = self.git(self.repo, 'rev-parse', 'HEAD')
        self.body = self.root / 'body.md'
        self.body.write_text('Candidate validation evidence.\n')
        self.rows = []
        for target, replacement in [('publication_mode', lambda: 'personal')]:
            patcher = patch.object(auth, target, replacement)
            patcher.start()
            self.addCleanup(patcher.stop)
        for target in [patch.object(planning, '_repo', return_value='fixture/repo'),
                       patch.object(planning, '_prs', side_effect=lambda *args: self.rows),
                       patch.object(auth, 'action', side_effect=self.fake_action)]:
            target.start()
            self.addCleanup(target.stop)
        self.scan = patch('check_secret_leakage.scan_candidate', side_effect=scanner.scan_candidate).start()
        self.addCleanup(patch.stopall)
        self.push = patch.object(ship, '_run_push', wraps=ship._run_push).start()
        self.pr_create = patch.object(ship, '_run_pr_create',
                                      return_value=(0, 'https://github.com/fixture/repo/pull/7\n')).start()

    def fake_action(self, root, operation, argv, base, **kwargs):
        """Only GitHub-URL-bound PR operations are mocked; the Git push scope is the real observation."""
        if operation not in {'gh_pr_create', 'gh_pr_merge'}:
            return REAL_ACTION(root, operation, argv, base, **kwargs)
        head = auth.git(root, 'rev-parse', 'HEAD^{commit}')
        branch = auth.git(root, 'branch', '--show-current')
        push = REAL_ACTION(root, 'git_push', ['git', 'push', 'origin', head + ':refs/heads/' + branch], base,
                           personal=True)
        scope = {**push, 'operations': [operation], 'target_ref': 'refs/heads/main',
                 'expected_remote_oid': auth._tip(root, 'origin', 'refs/heads/main')}
        if operation == 'gh_pr_merge':
            scope.update(github_repo='fixture/repo', merge_confirmation={
                'pr_number': 1, 'pr_url': 'https://github.com/fixture/repo/pull/1', 'head_sha': head,
                'base_branch': 'main', 'base_sha': base, 'required_checks': [],
                'required_checks_status': 'NOT_ENFORCED', 'required_checks_enforced': False, 'auto_merge': False})
        return scope

    def request(self, **overrides):
        return {'title': 'Candidate', 'body_file': str(self.body), 'base': 'main', 'head': None, **overrides}

    def row(self, state='OPEN', head=None):
        return {'number': 7, 'state': state, 'headRefOid': head or self.head, 'headRefName': 'codex/ship1',
                'baseRefName': 'main', 'isDraft': False, 'mergeCommit': None}

    def hook(self, command, runtime='claude-code'):
        output = io.StringIO()
        payload = {'cwd': str(self.repo), 'tool_input': {'command': command}}
        with patch('sys.stdin', io.StringIO(json.dumps(payload))), patch('sys.stdout', output), \
                patch('runtime_policy.action_from_hook', return_value=None), \
                patch.object(guard, 'safe_emit', return_value={'decision': 'ALLOW'}):
            guard.hook(runtime)
        return json.loads(output.getvalue())['hookSpecificOutput']

    def ship_command(self, extra=''):
        return f'aips publish ship --title Candidate --body-file {self.body} --base main{extra}'

class ShipTest(PublicationFixture):
    # --- argument grammar shared by Hook and CLI -------------------------------------------------

    def test_parser_accepts_only_the_single_literal_form(self):
        parsed = ship.parse_tokens(['--title', 'Candidate', '--body-file', 'body.md', '--base', 'main'])
        self.assertEqual(parsed, {'title': 'Candidate', 'body_file': 'body.md', 'base': 'main', 'head': None})
        forms = [
            ['--title', 'Candidate', '--body-file', 'body.md', '--base', 'main', '--admin'],
            ['--title', 'Candidate', '--body-file', 'body.md', '--base', 'main', '--delete-branch'],
            ['--title=Candidate', '--body-file', 'body.md', '--base', 'main'],
            ['--title', 'a', '--title', 'b', '--body-file', 'body.md', '--base', 'main'],
            ['--title', 'Candidate', '--body-file', 'body.md'],
            ['--title', 'Candidate', '--body-file', 'body.md', '--base', 'main', '--head', '-x'],
            ['--title', 'Candidate', '--body-file', 'body.md', '--base', 'ma in'],
        ]
        for tokens in forms:
            with self.subTest(tokens=tokens), self.assertRaises(PublicationError) as raised:
                ship.parse_tokens(tokens)
            self.assertIn(raised.exception.reason_code, {'COMMAND_FORM_UNSUPPORTED', 'PR_METADATA_INCOMPLETE',
                                                         'PR_BASE_MISMATCH', 'PR_HEAD_MISMATCH'})
        with self.assertRaises(PublicationError) as dynamic:
            ship.parse_tokens(['--title', '\0shell-expansion:$T', '--body-file', 'body.md', '--base', 'main'])
        self.assertEqual(dynamic.exception.detail_code, 'PUBLICATION_ARGUMENT_DYNAMIC')

    def test_recovery_text_names_the_single_supported_command(self):
        item = PublicationError('x', 'COMMAND_FORM_UNSUPPORTED', detail_code='SHIP_FORM_UNSUPPORTED').diagnostic()
        self.assertIn('aips publish ship --title', item['next_step'])
        self.assertIn('aips publish ship --title', item['next_step_zh'])
        evidence_item = PublicationError('x', 'PUBLICATION_SCAN_EVIDENCE_REQUIRED').diagnostic()
        self.assertIn('aips publish ship --title', evidence_item['next_step'])
        self.assertIn('aips publish ship --title', evidence_item['next_step_zh'])
        self.assertIn('aips publish prepare', evidence_item['next_step'])

    def test_argument_classifier_covers_aips_and_publish_preflight_spellings(self):
        self.assertEqual(guard.operations_for(self.ship_command()), ['publish_ship'])
        self.assertEqual(guard.operations_for(
            f'python scripts/publish_preflight.py ship --title t --body-file {self.body} --base main'), ['publish_ship'])
        self.assertEqual(guard.operations_for('aips publish prepare --worktree .'), [])
        with self.assertRaises(CommandError) as dynamic:
            guard.operations_for('aips $VERB publish ship --title t --body-file b --base main')
        self.assertEqual(dynamic.exception.reason_code, 'DYNAMIC_SUBCOMMAND')

    # --- chain: one scan, exact push, PR create ---------------------------------------------------

    def test_one_scan_then_exact_push_then_pr_create(self):
        result = ship.run(self.repo, self.request())
        self.assertEqual(result['status'], 'COMPLETE', result)
        self.assertEqual([step['step'] for step in result['steps']], ['scan', 'push', 'pr_create'])
        self.assertEqual(self.scan.call_count, 1)
        self.push.assert_called_once()
        self.assertEqual(self.push.call_args.args[1], ['git', 'push', 'origin', self.head + ':refs/heads/codex/ship1'])
        self.assertEqual(self.git(self.remote, 'rev-parse', 'refs/heads/codex/ship1'), self.head)
        argv = self.pr_create.call_args.args[1]
        for option, value in [('--repo', 'fixture/repo'), ('--head', 'codex/ship1'), ('--base', 'main'),
                              ('--title', 'Candidate')]:
            self.assertEqual(argv[argv.index(option) + 1], value)
        self.assertEqual(result['steps'][-1]['pr_url'], 'https://github.com/fixture/repo/pull/7')
        self.assertEqual(result['candidate']['candidate_sha'], self.head)
        self.assertEqual(result['candidate']['target_ref'], 'refs/heads/codex/ship1')
        self.assertFalse(result['recovery']['requires_human'])

    def test_rerun_skips_completed_push_and_existing_pr(self):
        self.assertEqual(ship.run(self.repo, self.request())['status'], 'COMPLETE')
        self.rows = [self.row()]
        result = ship.run(self.repo, self.request())
        self.assertEqual(result['status'], 'COMPLETE', result)
        self.assertEqual(result['recovery']['state'], 'EXISTING_PR')
        self.assertEqual(self.push.call_count, 1)
        self.assertEqual(self.pr_create.call_count, 1)
        self.assertIn({'step': 'pr_create', 'status': 'SKIPPED_EXISTING_PR', 'pr_number': 7}, result['steps'])

    def test_pr_create_failure_stops_and_rerun_creates_only_the_pr(self):
        self.pr_create.return_value = (1, 'raw gh output must not leak')
        result = ship.run(self.repo, self.request())
        self.assertEqual(result['status'], 'BLOCKED')
        item = result['diagnostics'][0]
        self.assertEqual(item['reason_code'], 'SHIP_PR_CREATE_FAILED')
        self.assertEqual(result['recovery']['state'], 'RERUN_SHIP')
        self.assertIn('aips publish ship', result['recovery']['next_step_zh'] or item['next_step_zh'])
        self.assertNotIn('raw gh output', json.dumps(result))
        self.pr_create.return_value = (0, 'https://github.com/fixture/repo/pull/7\n')
        retry = ship.run(self.repo, self.request())
        self.assertEqual(retry['status'], 'COMPLETE', retry)
        self.assertIn({'step': 'push', 'status': 'SKIPPED_ALREADY_AT_CANDIDATE'}, retry['steps'])
        self.assertEqual(self.push.call_count, 1)

    def test_push_failure_stops_before_pr_create(self):
        with patch.object(ship, '_run_push', return_value=1) as failing:
            result = ship.run(self.repo, self.request())
        failing.assert_called_once()
        self.assertEqual(result['diagnostics'][0]['reason_code'], 'SHIP_PUSH_FAILED')
        self.assertEqual(result['status'], 'BLOCKED')
        self.pr_create.assert_not_called()
        self.assertEqual(self.git(self.remote, 'for-each-ref', 'refs/heads/codex/ship1'), '')
        self.assertEqual(result['recovery']['state'], 'RERUN_SHIP')

    def test_scan_block_stops_the_chain_before_any_publication(self):
        with patch('check_secret_leakage.scan_candidate', return_value=([{'category': 'secret'}], [], {}, {})):
            result = ship.run(self.repo, self.request())
        self.assertEqual(result['diagnostics'][0]['reason_code'], 'CONTENT_SCAN_BLOCKED')
        self.push.assert_not_called()
        self.pr_create.assert_not_called()
        self.assertFalse(result['executed'])

    def test_forged_evidence_for_another_candidate_is_never_reused(self):
        real = REAL_ACTION(self.repo, 'git_push', ['git', 'push', 'origin', self.head + ':refs/heads/codex/ship1'],
                           self.git(self.repo, 'rev-parse', 'main'), personal=True)
        policy_hash = scanner.load_policy(scanner.DEFAULT_POLICY)[1]
        evidence.store(self.repo, {**real, 'candidate_commit': '0' * 40}, policy_digest=policy_hash)
        result = ship.run(self.repo, self.request())
        self.assertEqual(result['status'], 'COMPLETE', result)
        self.assertEqual(result['steps'][0]['evidence'], 'SCANNED')
        self.assertEqual(self.scan.call_count, 1)

    def test_candidate_change_between_scan_and_push_is_refused(self):
        original = ship._ensure_scan

        def scan_then_commit(observed, policy, policy_hash):
            status = original(observed, policy, policy_hash)
            (self.repo / 'file.txt').write_text('moved after scan\n')
            self.git(self.repo, 'commit', '-am', 'moved after scan')
            return status

        with patch.object(ship, '_ensure_scan', side_effect=scan_then_commit):
            result = ship.run(self.repo, self.request())
        self.assertEqual(result['status'], 'BLOCKED')
        self.push.assert_not_called()
        self.pr_create.assert_not_called()
        self.assertEqual(self.git(self.remote, 'for-each-ref', 'refs/heads/codex/ship1'), '')

    def test_remote_tip_change_between_scan_and_push_requires_fresh_scan(self):
        original = ship._ensure_scan

        def scan_then_remote_moves(observed, policy, policy_hash):
            status = original(observed, policy, policy_hash)
            self.git(self.repo, 'push', '--force', 'origin', 'main:refs/heads/codex/ship1')
            return status

        with patch.object(ship, '_ensure_scan', side_effect=scan_then_remote_moves):
            result = ship.run(self.repo, self.request())
        self.assertEqual(result['diagnostics'][0]['reason_code'], 'PUBLICATION_SCAN_EVIDENCE_REQUIRED')
        self.push.assert_not_called()

    def test_stale_or_unallowlisted_inputs_never_reach_a_child(self):
        self.git(self.repo, 'switch', '-c', 'main-copy')
        result = ship.run(self.repo, self.request())
        self.assertEqual(result['diagnostics'][0]['reason_code'], 'BRANCH_NOT_ALLOWLISTED')
        self.push.assert_not_called()
        self.git(self.repo, 'switch', 'codex/ship1')
        self.assertEqual(ship.run(self.repo, self.request(base='develop'))['diagnostics'][0]['reason_code'],
                         'PR_BASE_MISMATCH')
        self.assertEqual(ship.run(self.repo, self.request(head='codex/other'))['diagnostics'][0]['reason_code'],
                         'PR_HEAD_MISMATCH')
        self.push.assert_not_called()

    def test_high_assurance_never_runs_ship(self):
        with patch.object(auth, 'publication_mode', return_value='high_assurance'):
            result = ship.run(self.repo, self.request())
        self.assertEqual(result['diagnostics'][0]['reason_code'], 'ASSURANCE_MODE_BLOCKED')
        self.push.assert_not_called()

    # --- Hook validation of the one ship invocation -----------------------------------------------

    def test_hook_validates_ship_binding_and_scans_once(self):
        output = self.hook(self.ship_command())
        self.assertEqual(output['permissionDecision'], 'allow', output)
        self.assertIn(self.head, output['additionalContext'])
        self.assertIn('refs/heads/codex/ship1', output['additionalContext'])
        self.assertIn('"operation":"publish_ship"', output['additionalContext'])
        self.assertEqual(self.scan.call_count, 1)
        self.push.assert_not_called()

    def test_hook_scan_result_is_reused_by_the_cli_chain(self):
        self.assertEqual(self.hook(self.ship_command())['permissionDecision'], 'allow')
        result = ship.run(self.repo, self.request())
        self.assertEqual(result['status'], 'COMPLETE', result)
        self.assertEqual(result['steps'][0]['evidence'], 'FRESH_EVIDENCE_REUSED')
        self.assertEqual(self.scan.call_count, 1)

    def test_hook_denies_forms_outside_the_single_command(self):
        for command in [
            self.ship_command(' --admin'),
            self.ship_command(' --delete-branch'),
            self.ship_command() + ' && git push origin ' + self.head + ':refs/heads/codex/ship1',
            f'aips publish ship --title "$TITLE" --body-file {self.body} --base main',
        ]:
            with self.subTest(command=command):
                output = self.hook(command)
                self.assertEqual(output['permissionDecision'], 'deny', output)
        self.push.assert_not_called()

    def test_hook_denies_ship_when_scan_blocks_and_in_high_assurance(self):
        with patch('check_secret_leakage.scan_candidate', return_value=([{'category': 'secret'}], [], {}, {})):
            output = self.hook(self.ship_command())
        self.assertEqual(output['permissionDecision'], 'deny')
        self.assertIn('CONTENT_SCAN_BLOCKED', output['permissionDecisionReason'])
        with patch.object(auth, 'publication_mode', return_value='high_assurance'):
            output = self.hook(self.ship_command())
        self.assertEqual(output['permissionDecision'], 'deny')
        self.assertIn('ASSURANCE_MODE_BLOCKED', output['permissionDecisionReason'])

    def test_cli_ship_is_reachable_and_reports_without_network(self):
        proc = subprocess.run([str(ROOT / 'bin/aips'), 'publish', 'ship', '--title', 'Candidate', '--body-file',
                               str(self.body), '--base', 'main', '--format', 'json'],
                              cwd=self.repo, env={**os.environ, 'AIPS_VALIDATION_PYTHON': sys.executable},
                              capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload['status'], 'BLOCKED')
        self.assertEqual(payload['diagnostics'][0]['reason_code'], 'REMOTE_CONFIGURATION_INVALID')
        self.assertFalse(payload['executed'])


class MergeEvidenceTest(PublicationFixture):
    """Prepare stores merge-bound evidence; the Hook accepts only the bound merge and keeps human confirmation."""

    def merge_command(self, head=None):
        return f'gh pr merge 1 --repo fixture/repo --squash --match-head-commit {head or self.head}'

    def test_merge_without_prepare_remains_denied(self):
        output = self.hook(self.merge_command())
        self.assertEqual(output['permissionDecision'], 'deny')
        self.assertIn('PUBLICATION_SCAN_EVIDENCE_REQUIRED', output['permissionDecisionReason'])

    def test_prepare_stores_merge_evidence_and_hook_asks_for_confirmation(self):
        self.git(self.repo, 'push', 'origin', self.head + ':refs/heads/codex/ship1')
        self.rows = [self.row()]
        with patch.object(auth, 'required_checks_enforced', return_value=False), \
                patch.object(planning.authority, 'run', side_effect=self.gh_api):
            result = planning.prepare(self.repo, title='Candidate', body_file=self.body, merge_intent=True,
                                      runtime='claude-code')
        self.assertEqual(result['next_step'], 'NATIVE_MERGE_CONFIRMATION', result)
        policy_hash = scanner.load_policy(scanner.DEFAULT_POLICY)[1]
        merge_scope = self.fake_action(self.repo, 'gh_pr_merge', ['gh', 'pr', 'merge'],
                                       auth._personal_base(self.repo, 'gh_pr_merge', ['gh', 'pr', 'merge']))
        self.assertTrue(evidence.valid(self.repo, merge_scope, policy_digest=policy_hash))
        with patch.object(auth, 'required_checks_enforced', return_value=False), \
                patch.object(auth, 'run', side_effect=self.gh_api):
            output = self.hook(self.merge_command())
        self.assertEqual(output['permissionDecision'], 'ask', output)
        self.assertIn('Confirm PR merge #1', output['permissionDecisionReason'])

    def test_merge_evidence_does_not_survive_a_candidate_change(self):
        self.git(self.repo, 'push', 'origin', self.head + ':refs/heads/codex/ship1')
        self.rows = [self.row()]
        with patch.object(auth, 'required_checks_enforced', return_value=False), \
                patch.object(planning.authority, 'run', side_effect=self.gh_api):
            planning.prepare(self.repo, title='Candidate', body_file=self.body, merge_intent=True,
                             runtime='claude-code')
        (self.repo / 'file.txt').write_text('new candidate\n')
        self.git(self.repo, 'commit', '-am', 'new candidate')
        new_head = self.git(self.repo, 'rev-parse', 'HEAD')
        output = self.hook(self.merge_command(new_head))
        self.assertEqual(output['permissionDecision'], 'deny')
        self.assertIn('PUBLICATION_SCAN_EVIDENCE_REQUIRED', output['permissionDecisionReason'])

    def gh_api(self, root, *argv):
        if argv[:2] == ('gh', 'api'):
            return json.dumps({'allow_squash_merge': True})
        return REAL_RUN(root, *argv)


REAL_RUN = auth.run


if __name__ == '__main__':
    unittest.main()

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import governance_guard as guard
import publication_authority as auth
import publication_diagnostics
import publication_planning as planning
import publish_preflight as preflight


def scanner_fixture_assignment() -> str:
    """Generate per-run scanner input without storing credential-like data in source."""
    label = ''.join(map(chr, (97, 112, 105, 95, 107, 101, 121, 61)))
    return label + ''.join(uuid.uuid4().hex for _ in range(4))


class PlanningTest(unittest.TestCase):
    def git(self, cwd, *args):
        proc = subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=True)
        return proc.stdout.strip()

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
        self.git(self.repo, 'switch', '-c', 'codex/plan30')
        (self.repo / 'file.txt').write_text('candidate\n')
        self.git(self.repo, 'commit', '-am', 'candidate')
        self.head = self.git(self.repo, 'rev-parse', 'HEAD')
        self.body = self.root / 'body.md'
        self.body.write_text('Candidate validation evidence.\n')
        self.rows = []
        for target, replacement in [('publication_mode', lambda: 'personal')]:
            p = patch.object(auth, target, replacement)
            p.start()
            self.addCleanup(p.stop)
        p = patch.object(planning, '_repo', return_value='fixture/repo')
        p.start()
        self.addCleanup(p.stop)
        p = patch.object(planning, '_prs', side_effect=lambda *args: self.rows)
        p.start()
        self.addCleanup(p.stop)

    def prepare(self, **kwargs):
        return planning.prepare(self.repo, title='Candidate', body_file=self.body, **kwargs)

    def row(self, state='OPEN'):
        return {'number': 1, 'state': state, 'headRefOid': self.head, 'headRefName': 'codex/plan30',
                'baseRefName': 'main', 'isDraft': False, 'mergeCommit': None}

    def test_push_plan_is_literal_worktree_bound_and_read_only(self):
        before = self.git(self.remote, 'show-ref')
        result = self.prepare()
        self.assertEqual(result['status'], 'PLANNED', result)
        call = result['invocations'][0]
        self.assertEqual(call['cwd'], str(self.repo))
        self.assertEqual(call['argv'], ['git', 'push', 'origin', self.head + ':refs/heads/codex/plan30'])
        self.assertEqual(self.git(self.remote, 'show-ref'), before)
        self.assertFalse(result['authorized'])
        self.assertEqual(result['host_permission'], 'UNKNOWN')

    def test_dirty_and_wrong_root_have_safe_codes(self):
        (self.repo / 'private.txt').write_text('untracked')
        diagnostic = self.prepare()['diagnostics'][0]
        self.assertEqual(diagnostic['reason_code'], 'WORKTREE_DIRTY')
        self.assertEqual(diagnostic['phase'], 'candidate_validation')
        self.assertEqual(diagnostic['candidate_sha'], self.head)
        self.assertEqual(diagnostic['worktree_details']['paths']['untracked'], ['private.txt'])
        self.assertTrue(diagnostic['redacted'])
        result = planning.prepare(self.repo / '.git', title='Candidate', body_file=self.body)
        self.assertEqual(result['status'], 'BLOCKED')

    def test_changed_body_invalidates_fingerprint(self):
        first = self.prepare()
        self.body.write_text('New reviewed body\n')
        result = self.prepare(expected_fingerprint=first['fingerprint'])
        self.assertEqual(result['diagnostics'][0]['reason_code'], 'CANDIDATE_CHANGED')
        self.assertEqual(result['invocations'], [])

    def test_pushed_candidate_plans_pr_then_reuses_existing_pr(self):
        self.git(self.repo, 'push', 'origin', self.head + ':refs/heads/codex/plan30')
        # _repo is mocked for local bare-Git fixtures; action still verifies the GitHub identity.
        real_action = auth.action
        def action(root, operation, argv, base, **kwargs):
            if operation == 'gh_pr_create':
                return {}
            return real_action(root, operation, argv, base, **kwargs)
        with patch.object(auth, 'action', side_effect=action):
            result = self.prepare()
        self.assertEqual(result['next_step'], 'CREATE_PR', result)
        argv = result['invocations'][0]['argv']
        for option in ('--repo', '--head', '--base', '--title', '--body-file'):
            self.assertIn(option, argv)
        self.rows = [self.row()]
        result = self.prepare()
        self.assertEqual(result['next_step'], 'CHECKS_AND_MERGE_INTENT')
        self.assertEqual(result['invocations'], [])

    def test_duplicate_and_closed_prs_do_not_create_another(self):
        self.git(self.repo, 'push', 'origin', self.head + ':refs/heads/codex/plan30')
        self.rows = [self.row(), {**self.row(), 'number': 2}]
        self.assertEqual(self.prepare()['diagnostics'][0]['reason_code'], 'PR_STATE_AMBIGUOUS')
        self.rows = [self.row('CLOSED')]
        self.assertEqual(self.prepare()['diagnostics'][0]['reason_code'], 'PR_STATE_AMBIGUOUS')

    def test_auto_merge_plan_requires_intent_and_keeps_exact_candidate(self):
        self.git(self.repo, 'push', 'origin', self.head + ':refs/heads/codex/plan30')
        self.rows = [self.row()]
        base = self.git(self.repo, 'rev-parse', 'main')
        original_run = auth.run
        real_action = auth.action
        calls = []

        def observed_run(cwd, *argv):
            if argv[:2] == ('gh', 'api'):
                return '{"allow_squash_merge":true}'
            return original_run(cwd, *argv)

        def observed_tip(root, remote, ref):
            return self.head if ref == 'refs/heads/codex/plan30' else base

        def observe_action(root, operation, argv, base, **kwargs):
            if operation == 'gh_pr_merge':
                calls.append(argv)
                return {}
            return real_action(root, operation, argv, base, **kwargs)

        with patch('publication_planning.authority.run', side_effect=observed_run), \
                patch('publication_planning.authority.action', side_effect=observe_action), \
                patch('publication_planning.authority._tip', side_effect=observed_tip), \
                patch('publication_planning.authority._personal_base', return_value=base), \
                patch('publication_planning.authority._remote_default_branch', return_value='main'):
            result = self.prepare(merge_intent=True, auto_merge=True)
        self.assertEqual(result['next_step'], 'TASK_AUTHORIZED_MERGE', result)
        self.assertIn('--auto', calls[0])
        self.assertEqual(calls[0][calls[0].index('--match-head-commit') + 1], self.head)

    def test_auto_merge_without_explicit_intent_is_blocked(self):
        result = self.prepare(auto_merge=True)
        self.assertEqual(result['diagnostics'][0]['reason_code'], 'AUTO_MERGE_REQUIRES_INTENT')
        self.assertEqual(result['invocations'], [])

    def test_host_denial_never_retries(self):
        with patch.object(auth, 'git', side_effect=AssertionError('must not observe/retry')):
            result = self.prepare(host_denied=True)
        self.assertEqual(result['diagnostics'][0]['reason_code'], 'HOST_PERMISSION_DENIED')
        self.assertEqual(result['invocations'], [])

    def test_merge_diagnose_is_read_only_and_does_not_consume_authority(self):
        command = ('gh pr merge 17 --repo fixture/repo --squash --match-head-commit ' + self.head)
        with patch.object(auth, 'validate_personal_action', return_value={'base_commit': '0' * 40}) as validate, \
                patch.object(auth, 'action', side_effect=AssertionError('personal diagnosis must not consume a grant')):
            result = planning.diagnose(self.repo, command)
        self.assertEqual(result['status'], 'VALIDATED', result)
        self.assertFalse(result['authorized'])
        self.assertFalse(result['executed'])
        self.assertFalse(result['grant_consumed'])
        validate.assert_called_once()
        self.assertEqual(validate.call_args.args[1], 'gh_pr_merge')

    def test_required_checks_have_distinct_fail_closed_states(self):
        cases = [
            ([], 0, '', 'UNAVAILABLE', 'REQUIRED_CHECKS_POLICY_UNVERIFIED'),
            ([{'name': 'repo', 'bucket': 'fail'}], 0, '', 'FAIL', 'REQUIRED_CHECKS_FAILING'),
            ([{'name': 'repo', 'bucket': 'pending'}], 0, '', 'PENDING', 'REQUIRED_CHECKS_PENDING'),
            ([{'name': 'repo', 'bucket': 'pending'}], 8, '', 'PENDING', 'REQUIRED_CHECKS_PENDING'),
            (None, 1, "no required checks reported on the 'feature' branch", 'UNAVAILABLE', 'REQUIRED_CHECKS_POLICY_UNVERIFIED'),
            ([{'name': 'repo', 'bucket': 'cancel'}], 0, '', 'CANCELLED', 'REQUIRED_CHECKS_CANCELLED'),
            ([{'name': 'repo', 'bucket': 'skipping'}], 0, '', 'MISSING', 'REQUIRED_CHECKS_MISSING'),
            (None, 4, 'HTTP 403', 'UNAVAILABLE', 'REQUIRED_CHECKS_PERMISSION'),
            (None, 1, 'not logged into any GitHub hosts', 'UNAVAILABLE', 'REQUIRED_CHECKS_AUTHENTICATION'),
            ([{'name': 'repo', 'bucket': 'pass'}], 0, '', 'PASS', None),
        ]
        for payload, rc, stderr, status, code in cases:
            with self.subTest(status=status, code=code):
                result = publication_diagnostics.classify_required_checks(
                    payload, returncode=rc, stderr=stderr)
                self.assertEqual(result['status'], status)
                self.assertEqual(result['reason_code'], code)
        explicitly_unconfigured = publication_diagnostics.classify_required_checks(
            [], returncode=0, stderr='', required_policy=[])
        self.assertEqual(explicitly_unconfigured, {
            'status': 'UNCONFIGURED',
            'reason_code': 'REQUIRED_CHECKS_UNCONFIGURED',
            'checks': [],
        })
        no_checks_with_verified_empty_policy = publication_diagnostics.classify_required_checks(
            None, returncode=1,
            stderr="no required checks reported on the 'feature' branch",
            required_policy=[])
        self.assertEqual(no_checks_with_verified_empty_policy['status'], 'UNCONFIGURED')
        self.assertNotIn('403', str(publication_diagnostics.classify_required_checks(
            None, returncode=4, stderr='private URL HTTP 403')))

    def test_assurance_never_falls_back_or_consumes(self):
        with patch.object(auth, 'publication_mode', return_value='high_assurance'), \
                patch.object(auth, 'configured_authority', return_value=object()), \
                patch.object(auth, 'verify', side_effect=AssertionError('must not consume')):
            result = self.prepare()
        self.assertEqual(result['status'], 'AWAITING_AUTHORITY', result)
        self.assertEqual(result['diagnostics'][0]['reason_code'], 'AUTHORITY_REQUIRED')
        with patch.object(auth, 'publication_mode', side_effect=auth.PublicationError('private', 'AUTHORITY_CONFIG_INVALID')):
            result = self.prepare()
        self.assertNotIn('private', json.dumps(result))
        self.assertEqual(result['diagnostics'][0]['reason_code'], 'AUTHORITY_CONFIG_INVALID')

    def test_scan_failure_and_exception_text_are_redacted(self):
        with patch('check_secret_leakage.scan_candidate', return_value=([{'private': 'value'}], [], {}, {})):
            result = self.prepare()
        self.assertEqual(result['diagnostics'][0]['reason_code'], 'CONTENT_SCAN_BLOCKED')
        with patch.object(auth, 'git', side_effect=auth.PublicationError('https://token.invalid/private')):
            result = self.prepare()
        self.assertNotIn('token.invalid', json.dumps(result))

    def test_diagnose_source_ref_options_and_compounds(self):
        cases = [
            ('git push origin codex/plan30:refs/heads/codex/plan30', 'PUSH_SOURCE_NOT_EXACT_SHA'),
            ('git push origin ' + self.head + ':codex/plan30', 'INVALID_TARGET_REF'),
            ('git push -u origin ' + self.head + ':refs/heads/codex/plan30', 'COMMAND_FORM_UNSUPPORTED'),
            ('pwd; git push origin main', 'COMMAND_FORM_UNSUPPORTED'),
        ]
        for command, code in cases:
            with self.subTest(command=command):
                self.assertEqual(planning.diagnose(self.repo, command)['diagnostics'][0]['reason_code'], code)

    def test_high_assurance_diagnose_requires_lease_before_grant(self):
        command = 'git push origin ' + self.head + ':refs/heads/codex/plan30'
        with patch.object(auth, 'publication_mode', return_value='high_assurance'), \
                patch.object(auth, 'configured_authority', return_value=object()):
            self.assertEqual(planning.diagnose(self.repo, command)['status'], 'BLOCKED')
            leased = command.replace('git push ', 'git push --force-with-lease=refs/heads/codex/plan30: ')
            result = planning.diagnose(self.repo, leased)
        self.assertEqual(result['status'], 'AWAITING_AUTHORITY', result)
        self.assertFalse(result['authorized'])

    def test_alternate_git_environment_is_still_denied(self):
        with patch.dict(os.environ, {'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'safe.directory', 'GIT_CONFIG_VALUE_0': '*'}):
            result = self.prepare()
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(result['invocations'], [])

    def test_real_isolated_worktree_has_distinct_identity(self):
        other = self.root / 'clean'
        self.git(self.repo, 'worktree', 'add', '-b', 'codex/clean', str(other), 'HEAD')
        first = self.prepare()
        second = planning.prepare(other, title='Candidate', body_file=self.body)
        self.assertEqual(first['observation']['repository_id'], second['observation']['repository_id'])
        self.assertNotEqual(first['observation']['worktree_id'], second['observation']['worktree_id'])
        self.assertEqual(second['invocations'][0]['cwd'], str(other))

    def test_base_advance_blocks_old_candidate(self):
        self.git(self.repo, 'switch', 'main')
        (self.repo / 'base.txt').write_text('base advance\n')
        self.git(self.repo, 'add', '.')
        self.git(self.repo, 'commit', '-m', 'base advance')
        self.git(self.repo, 'push', 'origin', 'main')
        self.git(self.repo, 'switch', 'codex/plan30')
        self.assertEqual(self.prepare()['diagnostics'][0]['reason_code'], 'BASE_NOT_ANCESTOR')

    def test_squash_merge_resume_verifies_remote_integration(self):
        self.git(self.repo, 'switch', 'main')
        self.git(self.repo, 'merge', '--squash', 'codex/plan30')
        self.git(self.repo, 'commit', '-m', 'squash candidate')
        merged = self.git(self.repo, 'rev-parse', 'HEAD')
        self.git(self.repo, 'push', 'origin', 'main')
        self.git(self.repo, 'switch', 'codex/plan30')
        self.rows = [{**self.row('MERGED'), 'mergeCommit': {'oid': merged}}]
        result = self.prepare()
        self.assertEqual(result['status'], 'COMPLETE', result)
        self.assertEqual(result['recovery_state'], 'ALREADY_MERGED')
        self.assertTrue(result['idempotent'])
        self.assertEqual(result['phase'], 'post_merge_reconciliation')
        self.assertEqual(result['invocations'], [])
        self.rows[0]['mergeCommit'] = None
        self.assertEqual(self.prepare()['status'], 'BLOCKED')

    def test_doctor_is_read_only_and_separates_evidence_phases(self):
        snapshot = {
            'source_complete': True, 'source_status': 'COMPLETE', 'sources': {},
            'protection_state': 'UNPROTECTED', 'evidence_level': 'EFFECTIVE_RULES_CONFIRMED',
            'branch_exists': True, 'effective_rules': [], 'rulesets': [], 'branch_protection': {},
            'bypass_actors': [], 'activation_authorized': False, 'api_write_performed': False,
        }
        before = self.git(self.remote, 'show-ref')
        with patch('repository_governance_snapshot.build_snapshot', return_value=snapshot):
            result = planning.doctor(self.repo, branch='main', worktree_details=True)
        self.assertEqual(result['status'], 'OBSERVED', result)
        self.assertFalse(result['authorized'])
        self.assertFalse(result['api_write_performed'])
        self.assertIn({'phase': 'protection_policy_evidence', 'status': 'UNPROTECTED',
                       'evidence_level': 'EFFECTIVE_RULES_CONFIRMED', 'blocking': False}, result['phases'])
        self.assertEqual(self.git(self.remote, 'show-ref'), before)

    def test_doctor_reports_incomplete_policy_as_evidence_not_permission(self):
        snapshot = {
            'source_complete': False, 'source_status': 'UNKNOWN', 'sources': {
                'effective_rules': {'status': 'UNKNOWN', 'http_status': 403,
                    'endpoint': 'repos/fixture/repo/rules/branches/main',
                    'error_class': 'PERMISSION_OR_AUTHENTICATION',
                    'error_message': 'Resource not accessible by integration'}},
            'protection_state': 'UNKNOWN', 'evidence_level': 'INCOMPLETE', 'branch_exists': True,
            'effective_rules': [], 'rulesets': [], 'branch_protection': {}, 'bypass_actors': [],
            'activation_authorized': False, 'api_write_performed': False,
        }
        with patch('repository_governance_snapshot.build_snapshot', return_value=snapshot):
            result = planning.doctor(self.repo, branch='main')
        self.assertEqual(result['status'], 'INCOMPLETE')
        item = result['diagnostics'][0]
        self.assertEqual(item['reason_code'], 'PROTECTION_EVIDENCE_UNAVAILABLE')
        self.assertEqual(item['phase'], 'protection_policy_evidence')
        self.assertEqual(item['api_sources']['effective_rules']['http_status'], 403)
        self.assertFalse(result['authorized'])

    def test_pr_discovery_rejects_wrong_identity_and_truncation(self):
        for rows in ([{**self.row(), 'baseRefName': 'other'}], [self.row()] * 100):
            with patch.object(auth, 'run', return_value=json.dumps(rows)), self.assertRaises(auth.PublicationError):
                # Call the original function, bypassing the fixture discovery mock.
                PlanningTest.original_prs(self.repo, 'fixture/repo', 'codex/plan30', 'main')

    def test_native_runtime_diagnostics_retain_denial_and_redact_raw_error(self):
        command = 'git push origin ' + self.head + ':refs/heads/codex/plan30'
        for runtime in ('claude-code', 'gemini-cli'):
            output = io.StringIO()
            with patch('sys.stdin', io.StringIO(json.dumps({'cwd': str(self.repo), 'tool_input': {'command': command}}))), \
                    patch('sys.stdout', output), patch('runtime_policy.action_from_hook', return_value=None), \
                    patch.object(guard, 'safe_emit', return_value={'decision': 'ALLOW'}), \
                    patch.object(auth, 'validate_personal_action', side_effect=auth.PublicationError('private-token', 'WORKTREE_DIRTY')):
                guard.hook(runtime)
            response = output.getvalue()
            self.assertIn('WORKTREE_DIRTY', response)
            self.assertIn('deny', response)
            self.assertNotIn('private-token', response)

    def test_staged_content_failure_has_safe_cause_code(self):
        command = 'git commit -m candidate'
        output = io.StringIO()
        with patch('sys.stdin', io.StringIO(json.dumps({'cwd': str(self.repo), 'tool_input': {'command': command}}))), \
                patch('sys.stdout', output), patch('runtime_policy.action_from_hook', return_value=None), \
                patch.object(guard, 'commit_safety', side_effect=auth.PublicationError('private/path/value', 'STAGED_CONTENT_UNAVAILABLE')):
            guard.hook('claude-code')
        response = output.getvalue()
        self.assertIn('STAGED_CONTENT_UNAVAILABLE', response)
        self.assertIn('restage', response)
        self.assertNotIn('private/path/value', response)

    def test_preview_content_safety_handles_m4a_metadata_and_diagnostics(self):
        fixture = ROOT / 'tests/fixtures/publication/valid-audio.m4a'
        audio = fixture.read_bytes()
        candidate = self.repo / 'candidate.m4a'
        base = self.git(self.repo, 'rev-parse', 'main')
        with patch.object(preflight, 'ROOT', self.repo):
            candidate.write_bytes(audio)
            valid = preflight.preview_content_safety(base, ['candidate.m4a'])
            self.assertEqual(valid['status'], 'PASS', valid)

            fixture_assignment = scanner_fixture_assignment()
            metadata_marker = b'\n' + fixture_assignment.encode()
            moov_size = int.from_bytes(audio[28:32], 'big')
            metadata_payload = bytearray(audio[:28] + audio[28:28 + moov_size] + metadata_marker + audio[28 + moov_size:])
            metadata_payload[28:32] = (moov_size + len(metadata_marker)).to_bytes(4, 'big')
            candidate.write_bytes(metadata_payload)
            leaked = preflight.preview_content_safety(base, ['candidate.m4a'])
            self.assertEqual(leaked['status'], 'BLOCKED', leaked)

            candidate.write_text('not an M4A container')
            spoofed = preflight.preview_content_safety(base, ['candidate.m4a'])
            self.assertTrue(any('invalid or spoofed M4A' in item for item in spoofed['blockers']), spoofed)

            candidate.write_bytes(b'x' * (8 * 1024 * 1024 + 1))
            oversized = preflight.preview_content_safety(base, ['candidate.m4a'])
            self.assertTrue(any('Git LFS or external asset storage' in item for item in oversized['blockers']), oversized)

    def test_merge_plan_requires_intent_and_enabled_method(self):
        self.git(self.repo, 'push', 'origin', self.head + ':refs/heads/codex/plan30')
        self.rows = [self.row()]
        real_action = auth.action
        def action(root, operation, argv, base, **kwargs):
            return {} if operation == 'gh_pr_merge' else real_action(root, operation, argv, base, **kwargs)
        original = auth.run
        with patch.object(auth, 'run', wraps=auth.run) as run, patch.object(auth, 'action', side_effect=action):
            # Only repository-metadata REST is mocked; Git observations remain real.
            run.side_effect = lambda root, *argv: json.dumps({'allow_merge_commit': True}) if argv[:2] == ('gh', 'api') else original(root, *argv)
            result = self.prepare(merge_intent=True, runtime='claude-code')
        self.assertEqual(result['next_step'], 'NATIVE_MERGE_CONFIRMATION', result)
        self.assertIn('--merge', result['invocations'][0]['argv'])
        self.assertIn('--match-head-commit', result['invocations'][0]['argv'])

    def test_cli_prepare_and_diagnose_are_reachable(self):
        for args, code in [
            (['prepare', '--title', 'Candidate', '--body-file', str(self.body), '--host-denied'], 'HOST_PERMISSION_DENIED'),
            (['diagnose', '--command', 'pwd; git push origin main'], 'COMMAND_FORM_UNSUPPORTED'),
        ]:
            proc = subprocess.run([str(ROOT / 'bin/aips'), 'publish', *args, '--worktree', str(self.repo),
                                   '--project-root', str(ROOT), '--format', 'json'],
                                  cwd=self.root, env={**os.environ, 'AIPS_VALIDATION_PYTHON': sys.executable},
                                  capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 1, proc.stderr)
            self.assertEqual(json.loads(proc.stdout)['diagnostics'][0]['reason_code'], code)


PlanningTest.original_prs = staticmethod(planning._prs)

if __name__ == '__main__':
    unittest.main()

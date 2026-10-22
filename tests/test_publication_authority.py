from __future__ import annotations

import base64
import copy
import os
import random
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_secret_leakage as secret_scanner
import governance_guard as guard
import publication_authority as auth
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def scanner_fixture_assignment() -> str:
    """Generate per-run scanner input without storing credential-like data in source.

    Every hex digit appears exactly twice, so the value always has 4.0 bits of entropy and clears
    the generic-assignment entropy floor; a raw uuid4 hex fell below it in about 0.7% of runs.
    """
    label = ''.join(map(chr, (97, 112, 105, 95, 107, 101, 121, 61)))
    digits = list('0123456789abcdef' * 2)
    random.SystemRandom().shuffle(digits)
    return label + ''.join(digits)
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from publication_commands import CommandError, shell_commands
from publication_issuer import Issuer


class LocalAuthority(auth.Authority):
    def __init__(self, issuer):
        self.issuer = issuer
        public = issuer.key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        super().__init__({'version': 1, 'endpoint': 'https://issuer.invalid',
                          'issuers': {'fixture': base64.b64encode(public).decode()}})

    def check(self, record, consume):
        request = {'version': 1, 'nonce': 'fixture-nonce', 'record': record,
                   'record_digest': auth.digest(record), 'action_digest': auth.digest(record['scope'])}
        response = self.issuer.check(request, consume)
        self.verify_signature(response)
        if response['result'] != ('CONSUMED' if consume else 'AVAILABLE'):
            raise auth.PublicationError('denied')


class PublicationTest(unittest.TestCase):
    def setUp(self):
        clean_environment = patch.dict(os.environ)
        clean_environment.start()
        self.addCleanup(clean_environment.stop)
        for key in list(os.environ):
            if key in {'GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_CONFIG_PARAMETERS'} or key.startswith(('GIT_CONFIG_COUNT', 'GIT_CONFIG_KEY_', 'GIT_CONFIG_VALUE_')):
                os.environ.pop(key)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.repo, self.remote = self.path / 'repo', self.path / 'remote.git'
        self.repo.mkdir()
        self.run_git(self.repo, 'init', '-b', 'main')
        self.run_git(self.repo, 'config', 'user.name', 'Fixture')
        self.run_git(self.repo, 'config', 'user.email', 'fixture' + '@' + 'example.test')
        (self.repo / 'file.txt').write_text('initial\n')
        self.run_git(self.repo, 'add', 'file.txt')
        self.run_git(self.repo, 'commit', '-m', 'base')
        self.base = self.run_git(self.repo, 'rev-parse', 'HEAD')
        self.run_git(self.path, 'init', '--bare', str(self.remote))
        self.run_git(self.remote, 'symbolic-ref', 'HEAD', 'refs/heads/main')
        self.run_git(self.repo, 'remote', 'add', 'origin', str(self.remote))
        self.run_git(self.repo, 'push', 'origin', 'main')
        self.run_git(self.repo, 'switch', '-c', 'feature')
        (self.repo / 'file.txt').write_text('changed\n')
        self.run_git(self.repo, 'add', 'file.txt')
        self.run_git(self.repo, 'commit', '-m', 'candidate')
        self.head = self.run_git(self.repo, 'rev-parse', 'HEAD')
        self.argv = ['git', 'push', '--force-with-lease=refs/heads/feature:', 'origin', self.head + ':refs/heads/feature']
        self.issuer = Issuer(self.path / 'grants.sqlite', Ed25519PrivateKey.generate(), 'fixture')
        self.authority = LocalAuthority(self.issuer)
        proposal = auth.proposal(self.repo, 'git_push', self.argv, self.base)
        proposal['evidence']['validation'] = ['fixture candidate validation']
        self.record = self.issuer.issue(proposal, 'fixture-human')

    @staticmethod
    def run_git(cwd, *args):
        result = subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=False)
        if result.returncode:
            raise AssertionError(result.stderr)
        return result.stdout.strip()

    def verify(self, record=None, argv=None, consume=False, cwd=None):
        auth.verify(record or self.record, 'git_push', cwd or self.repo,
                    argv or self.argv, consume=consume, authority=self.authority)

    def test_no_upstream_full_diff_and_readonly_verification(self):
        self.assertEqual(self.record['scope']['files'], ['file.txt'])
        self.verify()
        self.verify()
        self.verify(consume=True)
        with self.assertRaises(auth.PublicationError):
            self.verify(consume=True)
        with self.assertRaises(auth.PublicationError):
            self.verify()

    def test_dirty_worktree_details_are_grouped_and_diagnostics_are_versioned(self):
        (self.repo / 'file.txt').write_text('staged content\n')
        self.run_git(self.repo, 'add', 'file.txt')
        (self.repo / 'file.txt').write_text('staged and modified\n')
        (self.repo / 'deleted.txt').write_text('remove\n')
        self.run_git(self.repo, 'add', 'deleted.txt')
        (self.repo / 'deleted.txt').unlink()
        (self.repo / 'untracked.txt').write_text('untracked\n')
        details = auth.worktree_dirty_details(self.repo)
        self.assertEqual(details['status'], 'DIRTY')
        self.assertIn('file.txt', details['paths']['staged'])
        self.assertIn('file.txt', details['paths']['modified'])
        self.assertIn('deleted.txt', details['paths']['deleted'])
        self.assertIn('untracked.txt', details['paths']['untracked'])
        diagnostic = auth.PublicationError('publication requires a clean worktree', 'WORKTREE_DIRTY',
            context={'worktree': self.repo, 'candidate_sha': self.head}).diagnostic()
        self.assertEqual(diagnostic['version'], 2)
        self.assertEqual(diagnostic['reason_code'], 'WORKTREE_DIRTY')
        self.assertEqual(diagnostic['candidate_sha'], self.head)
        self.assertTrue(diagnostic['diagnostic_id'])
        self.assertTrue(diagnostic['redacted'])
        self.assertNotIn('staged content', str(diagnostic))

    def test_default_publication_errors_map_to_specific_codes_without_raw_text(self):
        cases = {
            'personal publication requires one matching origin fetch and push URL': 'REMOTE_CONFIGURATION_INVALID',
            'required PR checks are not all complete and passing': 'REQUIRED_CHECKS_INCOMPLETE',
            'authority config/path is writable by this Agent, including ACL or privileged access': 'AUTHORITY_CONFIG_WRITABLE',
        }
        for message, expected in cases.items():
            with self.subTest(message=message):
                diagnostic = auth.PublicationError(message).diagnostic()
                self.assertEqual(diagnostic['reason_code'], expected)
                self.assertNotIn(message, str(diagnostic))
                self.assertEqual(diagnostic['blocking_rule'], 'GITHUB_OR_REMOTE_OBSERVATION' if expected.startswith(('REMOTE_', 'REQUIRED_CHECKS_')) else 'HUMAN_AUTHORITY')

    def test_unclassified_publication_error_is_an_explicit_diagnostic_gap(self):
        raw = 'private host detail: https://token.invalid/secret'
        diagnostic = auth.PublicationError(raw, phase='push_validation').diagnostic()
        self.assertEqual(diagnostic['reason_code'], 'INTERNAL_DIAGNOSTIC_GAP')
        self.assertEqual(diagnostic['phase'], 'push_validation')
        self.assertEqual(diagnostic['error_class'], 'PublicationError')
        self.assertNotIn(raw, str(diagnostic))
        self.assertNotIn('token.invalid', str(diagnostic))

    def test_unknown_explicit_reason_code_does_not_fall_back_to_generic_rejection(self):
        diagnostic = auth.PublicationError('private', 'TYPO_REASON_CODE', phase='push_validation').diagnostic()
        self.assertEqual(diagnostic['reason_code'], 'INTERNAL_DIAGNOSTIC_GAP')
        self.assertEqual(diagnostic['phase'], 'push_validation')
        self.assertEqual(diagnostic['error_class'], 'PublicationError')

    def test_known_branch_target_rejection_has_stable_specific_reason(self):
        diagnostic = auth.PublicationError(
            'personal mode permits only the current engineering branch').diagnostic()
        self.assertEqual(diagnostic['reason_code'], 'PUSH_TARGET_BRANCH_MISMATCH')
        self.assertEqual(diagnostic['phase'], 'push_validation')
        self.assertIn('detail_zh', diagnostic)
        self.assertIn('next_step_zh', diagnostic)

    def test_publication_mode_is_personal_only_when_admin_root_is_absent(self):
        config = self.path / 'authority.yaml'
        self.assertEqual(auth.publication_mode(config), 'personal')
        config.write_text('version: 1\n')
        self.assertEqual(auth.publication_mode(config), 'high_assurance')
        config.unlink()
        config.symlink_to(self.path / 'missing-target')
        with self.assertRaises(auth.PublicationError):
            auth.publication_mode(config)

    def test_personal_mode_allows_only_scoped_engineering_branch_push(self):
        self.run_git(self.repo, 'fetch', 'origin', 'main')
        self.run_git(self.repo, 'switch', '-c', 'codex/test')
        command = ['git', 'push', 'origin', self.head + ':refs/heads/codex/test']
        observed = auth.validate_personal_action(self.repo, 'git_push', command)
        self.assertEqual(observed['candidate_commit'], self.head)
        self.assertEqual(observed['target_ref'], 'refs/heads/codex/test')

        self.run_git(self.repo, 'switch', '-c', 'feat/checked-prefix')
        feat_command = ['git', 'push', 'origin', self.head + ':refs/heads/feat/checked-prefix']
        feat_observed = auth.validate_personal_action(self.repo, 'git_push', feat_command)
        self.assertEqual(feat_observed['target_ref'], 'refs/heads/feat/checked-prefix')

        self.run_git(self.repo, 'remote', 'add', 'exfil', str(self.remote))
        with self.assertRaisesRegex(auth.PublicationError, 'verified single origin'):
            auth.validate_personal_action(
                self.repo, 'git_push', ['git', 'push', 'exfil', self.head + ':refs/heads/codex/test'])

        for branch, refspec, flags in [
            ('main', 'refs/heads/main', []),
            ('codex/test', 'refs/heads/main', []),
            ('codex/test', 'refs/heads/codex/test', ['--delete']),
            ('codex/test', 'refs/heads/codex/test', ['--force']),
        ]:
            args = ['git', 'push', *flags, 'origin', self.head + ':' + refspec]
            with self.subTest(branch=branch, refspec=refspec, flags=flags), self.assertRaises(auth.PublicationError):
                auth.validate_personal_action(self.repo, 'git_push', args)

    def test_personal_mode_still_denies_tags_and_releases(self):
        with self.assertRaises(auth.PublicationError):
            auth.validate_personal_action(self.repo, 'git_tag', ['git', 'tag', 'v1'])
        with self.assertRaises(auth.PublicationError):
            auth.validate_personal_action(self.repo, 'gh_release_create', ['gh', 'release', 'create', 'v1'])

    def test_personal_merge_requires_exact_open_default_branch_pr_and_passing_checks(self):
        import json

        self.run_git(self.repo, 'switch', '-c', 'codex/test-merge')
        self.run_git(self.repo, 'remote', 'set-url', 'origin', 'https://github.com/owner/project.git')
        merge = ['gh', 'pr', 'merge', '7', '--repo', 'owner/project', '--squash',
                 '--match-head-commit', self.head]
        pr = {'url': 'https://github.com/owner/project/pull/7', 'state': 'OPEN', 'isDraft': False,
              'mergeable': 'MERGEABLE', 'headRefOid': self.head, 'headRefName': 'codex/test-merge',
              'baseRefOid': self.base,
              'baseRefName': 'main'}
        original_run = auth.run
        real_subprocess_run = subprocess.run

        def observed_run(cwd, *argv):
            if argv[:3] == ('gh', 'pr', 'view'):
                return json.dumps(pr)
            return original_run(cwd, *argv)

        def observed_subprocess_run(argv, **kwargs):
            if argv[:3] == ['gh', 'pr', 'checks']:
                return subprocess.CompletedProcess(argv, 0, '[{"bucket":"pass","name":"repository"}]', '')
            return real_subprocess_run(argv, **kwargs)

        def policy_reader(_root, endpoint):
            if endpoint.endswith('/rules/branches/main') or 'rulesets?' in endpoint:
                payload = []
            elif endpoint.endswith('/branches/main/protection'):
                payload = {'required_status_checks': {'contexts': ['repository']}}
            elif endpoint.endswith('/branches/main'):
                payload = {'name': 'main', 'protected': True}
            else:
                raise AssertionError(endpoint)
            return {'returncode': 0, 'http_status': 200, 'payload': payload,
                    'endpoint': endpoint, 'error_class': None, 'error_message': None}

        with patch.dict(os.environ, {'AIPS_ENFORCE_REQUIRED_CHECKS': ''}), \
                patch('publication_authority._personal_base', return_value=self.base), \
                patch('publication_authority._remote_default_branch', return_value='main'), \
                patch('publication_authority._tip', return_value=self.base), \
                patch('publication_authority.run', side_effect=observed_run), \
                patch('publication_authority.subprocess.run', side_effect=observed_subprocess_run), \
                patch('repository_governance_snapshot.query_github_api', side_effect=AssertionError('default mode must not require policy evidence')), \
                patch('check_secret_leakage.scan_candidate', return_value=([], [], [], {})):
            observed = auth.validate_personal_action(self.repo, 'gh_pr_merge', merge)
            binding = observed['merge_confirmation']
            self.assertFalse(binding['required_checks_enforced'])
            self.assertEqual(binding['required_checks_status'], 'NOT_ENFORCED')
            self.assertEqual(binding['required_checks'], [])
            self.assertEqual(binding['head_sha'], self.head)

        with patch.dict(os.environ, {'AIPS_ENFORCE_REQUIRED_CHECKS': '1'}), \
                patch('publication_authority._personal_base', return_value=self.base), \
                patch('publication_authority._remote_default_branch', return_value='main'), \
                patch('publication_authority._tip', return_value=self.base), \
                patch('publication_authority.run', side_effect=observed_run), \
                patch('publication_authority.subprocess.run', side_effect=observed_subprocess_run), \
                patch('repository_governance_snapshot.query_github_api', side_effect=policy_reader), \
                patch('check_secret_leakage.scan_candidate', return_value=([], [], [], {})):
            observed = auth.validate_personal_action(self.repo, 'gh_pr_merge', merge)
            binding = observed['merge_confirmation']
            self.assertEqual(binding['pr_number'], 7)
            self.assertEqual(binding['pr_url'], 'https://github.com/owner/project/pull/7')
            self.assertEqual(binding['head_sha'], self.head)
            self.assertEqual(binding['base_sha'], self.base)
            self.assertEqual(binding['required_checks'], ['repository'])
            self.assertTrue(binding['required_checks_enforced'])
            self.assertEqual(binding['required_checks_status'], 'PASS')

            pr['state'] = 'CLOSED'
            with self.assertRaisesRegex(auth.PublicationError, 'open and ready'):
                auth.validate_personal_action(self.repo, 'gh_pr_merge', merge)
            pr['state'] = 'OPEN'
            pr['isDraft'] = True
            with self.assertRaisesRegex(auth.PublicationError, 'open and ready'):
                auth.validate_personal_action(self.repo, 'gh_pr_merge', merge)
            pr['isDraft'] = False
            pr['mergeable'] = 'UNKNOWN'
            with self.assertRaisesRegex(auth.PublicationError, 'mergeability'):
                auth.validate_personal_action(self.repo, 'gh_pr_merge', merge)
            pr['mergeable'] = 'MERGEABLE'

            pr['baseRefName'] = 'release'
            with self.assertRaisesRegex(auth.PublicationError, 'default branch'):
                auth.validate_personal_action(self.repo, 'gh_pr_merge', merge)
            pr['baseRefName'] = 'main'
            pr['headRefName'] = 'other-branch'
            with self.assertRaisesRegex(auth.PublicationError, 'current allowlisted engineering branch'):
                auth.validate_personal_action(self.repo, 'gh_pr_merge', merge)
            pr['headRefName'] = 'codex/test-merge'
            pr['headRefOid'] = self.base
            with self.assertRaisesRegex(auth.PublicationError, 'head'):
                auth.validate_personal_action(self.repo, 'gh_pr_merge', merge)
            pr['headRefOid'] = self.head

            def pending_checks(argv, **kwargs):
                if argv[:3] == ['gh', 'pr', 'checks']:
                    return subprocess.CompletedProcess(argv, 8, '[{"bucket":"pending","name":"repository"}]', '')
                return real_subprocess_run(argv, **kwargs)

            with patch('publication_authority.subprocess.run', side_effect=pending_checks), \
                    self.assertRaisesRegex(auth.PublicationError, 'required PR checks'):
                auth.validate_personal_action(self.repo, 'gh_pr_merge', merge)

    def test_personal_scan_uses_live_remote_default_not_mutable_origin_head(self):
        self.run_git(self.repo, 'fetch', 'origin', 'main')
        self.run_git(self.repo, 'update-ref', 'refs/remotes/origin/agent/attacker-controlled', self.head)
        self.run_git(self.repo, 'symbolic-ref', 'refs/remotes/origin/HEAD',
                     'refs/remotes/origin/agent/attacker-controlled')
        self.assertEqual(auth._personal_base(self.repo, 'git_push', self.argv), self.base)

    def test_personal_pr_requires_allowlisted_head_and_live_default_base(self):
        self.run_git(self.repo, 'remote', 'set-url', 'origin', 'https://github.com/owner/project.git')
        command = ['gh', 'pr', 'create', '--repo', 'owner/project', '--head', 'feature', '--base', 'main',
                   '--title', 'Feature', '--body', 'body']
        with patch('publication_authority._personal_base', return_value=self.base), \
                patch('publication_authority._tip', return_value=self.head), \
                self.assertRaisesRegex(auth.PublicationError, 'PR head'):
            auth.validate_personal_action(self.repo, 'gh_pr_create', command)

        command[command.index('--base') + 1] = 'production'
        with self.assertRaisesRegex(auth.PublicationError, 'remote default branch'):
            auth._personal_base(self.repo, 'gh_pr_create', command)

    def test_personal_mode_runs_strict_candidate_and_history_secret_scan(self):
        self.run_git(self.repo, 'fetch', 'origin', 'main')
        self.run_git(self.repo, 'switch', '-c', 'codex/secret-test')
        (self.repo / 'credentials.txt').write_text('token=github_pat_' + 'a' * 36 + '\n')
        self.run_git(self.repo, 'add', 'credentials.txt')
        self.run_git(self.repo, 'commit', '-m', 'candidate with credential')
        head = self.run_git(self.repo, 'rev-parse', 'HEAD')
        command = ['git', 'push', 'origin', head + ':refs/heads/codex/secret-test']
        with self.assertRaisesRegex(auth.PublicationError, 'secret scan blocked'):
            auth.validate_personal_action(self.repo, 'git_push', command)

    def test_unsupported_command_form_is_rejected_before_candidate_or_secret_scan(self):
        command = ['git', '-C', str(self.repo), 'push', 'origin',
                   self.head + ':refs/heads/codex/test']
        with patch('publication_authority.git', side_effect=AssertionError('candidate inspected')), \
                patch('check_secret_leakage.scan_candidate', side_effect=AssertionError('scanner called')) as scan, \
                self.assertRaises(auth.PublicationError) as caught:
            auth.validate_personal_action(self.repo, 'git_push', command)
        self.assertEqual(caught.exception.reason_code, 'COMMAND_FORM_UNSUPPORTED')
        scan.assert_not_called()

    def test_secret_scanner_failure_has_stable_redacted_publication_diagnostic(self):
        raw = 'private token https://secret.invalid/value'
        command = ['git', 'push', 'origin', self.head + ':refs/heads/codex/test']
        with patch('publication_authority._personal_base', return_value=self.base), \
                patch('check_secret_leakage.load_policy', side_effect=secret_scanner.ScanError(
                    raw, reason_code='SECRET_SCAN_POLICY_INVALID', phase='content_scan.policy_validation')), \
                self.assertRaises(auth.PublicationError) as caught:
            auth.validate_personal_action(self.repo, 'git_push', command)
        diagnostic = caught.exception.diagnostic()
        self.assertEqual(diagnostic['reason_code'], 'SECRET_SCAN_POLICY_INVALID')
        self.assertEqual(diagnostic['phase'], 'content_scan.policy_validation')
        self.assertEqual(diagnostic['component'], 'check_secret_leakage')
        self.assertEqual(diagnostic['error_class'], 'ScanError')
        self.assertTrue(diagnostic['diagnostic_id'])
        self.assertFalse(diagnostic['retryable'])
        self.assertNotIn(raw, str(diagnostic))
        self.assertNotIn('secret.invalid', str(diagnostic))

    def test_secret_scanner_policy_failures_have_distinct_stable_codes(self):
        invalid = self.path / 'invalid-secret-scan.yaml'
        invalid.write_text('version: 99\n')
        with self.assertRaises(secret_scanner.ScanError) as caught:
            secret_scanner.load_policy(invalid)
        self.assertEqual(caught.exception.reason_code, 'SECRET_SCAN_POLICY_INVALID')

        policy = secret_scanner.yaml.safe_load(secret_scanner.DEFAULT_POLICY.read_text())
        policy['allowlist'] = [{'path': 'fixture.txt', 'detector': 'assignment',
            'fingerprint': 'a' * 16, 'reason': 'expired fixture',
            'expires': (datetime.now(UTC).date() - timedelta(days=1)).isoformat()}]
        expired = self.path / 'expired-secret-scan.yaml'
        expired.write_text(secret_scanner.yaml.safe_dump(policy))
        with self.assertRaises(secret_scanner.ScanError) as caught:
            secret_scanner.load_policy(expired)
        self.assertEqual(caught.exception.reason_code, 'SECRET_SCAN_ALLOWLIST_EXPIRED')

    def test_candidate_scan_classifies_invalid_base_missing_head_and_unreadable_file(self):
        policy, _ = secret_scanner.load_policy(secret_scanner.DEFAULT_POLICY)
        with self.assertRaises(secret_scanner.ScanError) as caught:
            secret_scanner.scan_candidate(self.repo, 'missing-base', 'HEAD', policy)
        self.assertEqual(caught.exception.reason_code, 'SECRET_SCAN_BASE_INVALID')
        with self.assertRaises(secret_scanner.ScanError) as caught:
            secret_scanner.scan_candidate(self.repo, self.base, 'missing-head', policy)
        self.assertEqual(caught.exception.reason_code, 'SECRET_SCAN_GIT_OBJECT_MISSING')

        self.run_git(self.repo, 'switch', '-c', 'codex/unreadable-scan-fixture')
        (self.repo / 'unreadable.txt').write_bytes(b'\xff\xfe')
        self.run_git(self.repo, 'add', 'unreadable.txt')
        self.run_git(self.repo, 'commit', '-m', 'unreadable UTF-8 fixture')
        diagnostics = []
        _findings, blockers, _base, _head = secret_scanner.scan_candidate(
            self.repo, self.base, 'HEAD', policy, diagnostics=diagnostics)
        self.assertTrue(blockers)
        self.assertEqual(diagnostics[0]['reason_code'], 'SECRET_SCAN_FILE_UNREADABLE')
        self.assertNotIn('unreadable.txt', str(diagnostics))

    def test_unexpected_secret_scanner_failure_is_redacted_as_internal_error(self):
        command = ['git', 'push', 'origin', self.head + ':refs/heads/codex/test']
        with patch('publication_authority._personal_base', return_value=self.base), \
                patch('check_secret_leakage.scan_candidate', side_effect=RuntimeError(
                    'private token https://secret.invalid/value')), \
                self.assertRaises(auth.PublicationError) as caught:
            auth.validate_personal_action(self.repo, 'git_push', command)
        diagnostic = caught.exception.diagnostic()
        self.assertEqual(diagnostic['reason_code'], 'SECRET_SCAN_INTERNAL_ERROR')
        self.assertEqual(diagnostic['error_class'], 'RuntimeError')
        self.assertNotIn('secret.invalid', str(diagnostic))

    def test_signature_tamper_unsigned_and_wrong_key(self):
        for mutate in [lambda r: r.pop('signature'), lambda r: r['approval'].update(approved_by='agent'),
                       lambda r: r['scope'].update(target_ref='refs/heads/main'), lambda r: r.update(version=1)]:
            record = copy.deepcopy(self.record)
            mutate(record)
            with self.assertRaises(auth.PublicationError):
                self.verify(record)
        wrong = LocalAuthority(Issuer(self.path / 'wrong.sqlite', Ed25519PrivateKey.generate(), 'fixture'))
        with self.assertRaises(auth.PublicationError):
            auth.verify(self.record, 'git_push', self.repo, self.argv, authority=wrong)

    def test_expiry_future_and_overlong(self):
        now = datetime.now(UTC)
        for issued, expires in [(now - timedelta(hours=1), now - timedelta(seconds=1)),
                                (now + timedelta(seconds=10), now + timedelta(seconds=60)),
                                (now, now + timedelta(hours=2))]:
            record = copy.deepcopy(self.record)
            record['approval'].update(approved_at=issued.isoformat(), expires_at=expires.isoformat())
            with self.assertRaises(auth.PublicationError):
                self.verify(self.issuer.sign(record))

    def test_wrong_remote_ref_force_delete_or_missing_actual(self):
        self.run_git(self.repo, 'remote', 'add', 'other', str(self.remote))
        candidates = [self.argv[:-2] + ['other', self.argv[-1]],
                      self.argv[:-1] + [self.head + ':refs/heads/main'],
                      ['git', 'push', '--force', 'origin', self.argv[-1]],
                      ['git', 'push', '--delete', 'origin', 'refs/heads/feature'],
                      ['git', 'push', 'origin', 'HEAD:refs/heads/feature'],
                      ['git', 'push', '--all', 'origin'], ['git', 'push', 'origin', self.argv[-1]]]
        for argv in candidates:
            with self.subTest(argv=argv), self.assertRaises(auth.PublicationError):
                self.verify(argv=argv)
        with self.assertRaises(auth.PublicationError):
            auth.verify(self.record, 'git_push', self.repo, None, authority=self.authority)

    def test_remote_state_changes_before_and_after_gate(self):
        self.verify(consume=True)
        # Server-enforced lease also rejects drift between observation and execution.
        self.run_git(self.repo, 'push', 'origin', self.base + ':refs/heads/feature')
        proc = subprocess.run(self.argv, cwd=self.repo, capture_output=True, check=False)
        self.assertNotEqual(proc.returncode, 0)
        with self.assertRaises(auth.PublicationError):
            self.verify()

    def test_cross_worktree_and_subdirectory_lookup(self):
        sub = self.repo / 'nested'
        sub.mkdir()
        self.verify(cwd=sub)
        approval = self.repo / '.ai/approvals/ACTIVE.yaml'
        approval.parent.mkdir(parents=True)
        approval.write_text('version: 2\n')
        self.assertEqual(auth.approval_location(sub), approval.resolve())
        approval.unlink()
        common = Path(self.run_git(self.repo, 'rev-parse', '--path-format=absolute', '--git-common-dir'))
        scoped = common / 'aips/approvals' / auth.identity(self.repo)['worktree_id'].split(':')[1] / 'ACTIVE.yaml'
        scoped.parent.mkdir(parents=True)
        scoped.write_text('version: 2\n')
        self.assertEqual(auth.approval_location(sub), scoped.resolve())
        self.run_git(self.repo, 'worktree', 'add', '-b', 'other', str(self.path / 'other'), self.head)
        with self.assertRaises(auth.PublicationError):
            self.verify(cwd=self.path / 'other')
        self.assertIsNone(auth.approval_location(self.path / 'other'))

    def test_candidate_dirty_and_implicit_extra_tags(self):
        (self.repo / 'file.txt').write_text('changed again')
        with self.assertRaises(auth.PublicationError):
            self.verify()

        self.run_git(self.repo, 'restore', 'file.txt')
        self.run_git(self.repo, 'config', 'push.followTags', 'true')
        with self.assertRaises(auth.PublicationError):
            self.verify()

    def test_alternate_git_configuration_is_rejected(self):
        with patch.dict(os.environ, {'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'safe.directory', 'GIT_CONFIG_VALUE_0': '*'}), self.assertRaises(auth.PublicationError):
            self.verify()

    def test_atomic_concurrent_consumption_and_tampered_store_request(self):
        request = {'version': 1, 'nonce': 'race', 'record': self.record,
                   'record_digest': auth.digest(self.record), 'action_digest': auth.digest(self.record['scope'])}
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.issuer.check(request, True)['result'], range(8)))
        self.assertEqual(results.count('CONSUMED'), 1)
        self.assertEqual(results.count('DENIED'), 7)
        changed = copy.deepcopy(request)
        changed['record']['scope']['force'] = False
        self.assertEqual(self.issuer.check(changed, False)['result'], 'DENIED')

    def test_network_outage_and_unsigned_response(self):
        real = auth.Authority(self.authority.config)
        with patch('publication_authority.build_opener', side_effect=OSError('unavailable')), self.assertRaises(OSError):
            auth.verify(self.record, 'git_push', self.repo, self.argv, authority=real)
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, size): return b'{}'
        with patch('publication_authority.build_opener') as opener:
            opener.return_value.open.return_value = Response()
            with self.assertRaises(auth.PublicationError):
                auth.verify(self.record, 'git_push', self.repo, self.argv, authority=real)

    def test_https_signed_nonce_digest_and_consume_assertions(self):
        import json
        real = auth.Authority(self.authority.config)
        issuer = self.issuer
        class Response:
            def __init__(self, data): self.data = data
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, size): return self.data
        def opened(request, timeout):
            payload = json.loads(request.data)
            response = issuer.check(payload, request.full_url.endswith('/consume'))
            return Response(auth.canonical(response))
        with patch('publication_authority.build_opener') as opener:
            opener.return_value.open.side_effect = opened
            auth.verify(self.record, 'git_push', self.repo, self.argv, authority=real)
            auth.verify(self.record, 'git_push', self.repo, self.argv, authority=real, consume=True)
            with self.assertRaises(auth.PublicationError):
                auth.verify(self.record, 'git_push', self.repo, self.argv, authority=real, consume=True)
        def wrong_nonce(request, timeout):
            response = issuer.check(json.loads(request.data), False)
            response['nonce'] = 'old-request'
            return Response(auth.canonical(issuer.sign(response)))
        with patch('publication_authority.build_opener') as opener:
            opener.return_value.open.side_effect = wrong_nonce
            with self.assertRaises(auth.PublicationError):
                auth.verify(self.record, 'git_push', self.repo, self.argv, authority=real)

    def test_legacy_verify_cannot_skip_authentication(self):
        path = self.path / 'approval.yaml'
        import yaml
        legacy = {'version': 1, 'approval': {'status': 'APPROVED'}, 'scope': {'operations': ['git_push']}}
        legacy['scope']['fingerprint'] = guard.fingerprint(legacy['scope'])
        path.write_text(yaml.safe_dump(legacy))
        self.assertFalse(guard.verify_record(path, 'git_push', self.repo, False, command=' '.join(self.argv))[0])

    def test_commit_trailer_and_real_staged_payload(self):
        email = 'author' + '@' + 'example.test'
        message = 'Feature\n\nCo-Authored-By: Fixture <' + email + '>'
        import shlex
        command = 'git commit -m ' + shlex.quote(message)
        self.assertNotEqual(guard.commit_safety(self.repo, command)['decision'], 'BLOCK')
        plain = 'git commit -m ' + shlex.quote('Contact ' + email)
        self.assertEqual(guard.commit_safety(self.repo, plain)['decision'], 'BLOCK')
        literal = 'Feature\ncat <<EOF\napi_key=' + 'A1b2C3d4E5f6G7h8I9j0K1l2' + '\nEOF\n'
        self.assertEqual(guard.commit_safety(self.repo, 'git commit -m ' + shlex.quote(literal))['decision'], 'BLOCK')
        (self.repo / 'file.txt').write_text('api_key=' + 'A1b2C3d4E5f6G7h8I9j0K1l2')
        self.run_git(self.repo, 'add', 'file.txt')
        self.assertEqual(guard.commit_safety(self.repo, command)['decision'], 'BLOCK')
        original_run = subprocess.run

        def unavailable_blob(argv, **kwargs):
            if argv[:2] == ['git', 'show']:
                return subprocess.CompletedProcess(argv, 1, b'', b'private path detail')
            return original_run(argv, **kwargs)

        with patch('governance_guard.subprocess.run', side_effect=unavailable_blob), \
                self.assertRaises(auth.PublicationError) as unavailable:
            guard.commit_safety(self.repo, command)
        self.assertEqual(unavailable.exception.reason_code, 'STAGED_BLOB_UNAVAILABLE')

        def oversized_blob(argv, **kwargs):
            if argv[:2] == ['git', 'show']:
                return subprocess.CompletedProcess(argv, 0, b'x' * (8 * 1024 * 1024 + 1), b'')
            return original_run(argv, **kwargs)

        with patch('governance_guard.subprocess.run', side_effect=oversized_blob), \
                self.assertRaises(auth.PublicationError) as oversized:
            guard.commit_safety(self.repo, command)
        self.assertEqual(oversized.exception.reason_code, 'STAGED_CONTENT_TOO_LARGE')
        # `-a` is supported; it inspects the tracked worktree content the commit would include.
        self.assertEqual(guard.commit_safety(self.repo, 'git commit -a -m candidate')['decision'], 'BLOCK')
        for unsupported in ['git commit file.txt -m candidate', 'git commit --only -m candidate',
                            'git commit -p -m candidate', 'git commit --no-edit -m candidate']:
            with self.subTest(command=unsupported), self.assertRaises(auth.PublicationError):
                guard.commit_safety(self.repo, unsupported)
        for dynamic in ['git commit -m "$MSG"', "git commit -m $'encoded\\x41message'", 'git commit -F ~/message',
                        'git commit -m author\\\n' + '@' + 'example.test', 'git commit -m {hello,world}']:
            with self.subTest(command=dynamic), self.assertRaises(auth.PublicationError):
                guard.commit_safety(self.repo, dynamic)

    def test_m4a_publication_scans_metadata_rejects_spoofs_and_enforces_size_limit(self):
        from m4a_inspection import inspect_m4a

        fixture = ROOT / 'tests/fixtures/publication/valid-audio.m4a'
        audio = fixture.read_bytes()
        self.assertEqual(inspect_m4a(audio).major_brand, b'M4A ')
        video_spoof = bytearray(audio)
        video_spoof[8:12] = b'isom'
        video_spoof[16:20] = b'mp42'
        video_spoof[20:24] = b'mp42'
        with self.assertRaises(ValueError):
            inspect_m4a(bytes(video_spoof))
        policy, _ = secret_scanner.load_policy(ROOT / 'config/secret-scan.yaml')

        # A real M4A is accepted by the staged commit guard and exact-candidate scanner.
        valid_path = self.repo / 'valid-audio.m4a'
        valid_path.write_bytes(audio)
        # Minimal valid ID3v2.4 tag, followed by opaque audio bytes.
        (self.repo / 'legacy-audio.mp3').write_bytes(b'ID3\x04\x00\x00\x00\x00\x00\x00' + b'\xff\xfb\x90\x64' + b'legacy audio bytes')
        self.run_git(self.repo, 'add', 'valid-audio.m4a', 'legacy-audio.mp3')
        command = 'git commit -m ' + __import__('shlex').quote('add audio fixture')
        self.assertNotEqual(guard.commit_safety(self.repo, command)['decision'], 'BLOCK')
        self.run_git(self.repo, 'commit', '-m', 'add audio fixture')
        valid_head = self.run_git(self.repo, 'rev-parse', 'HEAD')
        findings, blockers, _, _ = secret_scanner.scan_candidate(self.repo, self.base, valid_head, policy)
        self.assertEqual(findings, [])
        self.assertEqual(blockers, [])

        # Metadata remains text-scanned while the mdat audio bytes are never decoded.
        fixture_assignment = scanner_fixture_assignment()
        metadata_marker = b'\n' + fixture_assignment.encode()
        moov_size = int.from_bytes(audio[28:32], 'big')
        metadata_payload = bytearray(audio[:28] + audio[28:28 + moov_size] + metadata_marker + audio[28 + moov_size:])
        metadata_payload[28:32] = (moov_size + len(metadata_marker)).to_bytes(4, 'big')
        fixture_path = self.repo / 'metadata-marker.m4a'
        fixture_path.write_bytes(metadata_payload)
        self.run_git(self.repo, 'add', 'metadata-marker.m4a')
        self.assertEqual(guard.commit_safety(self.repo, command)['decision'], 'BLOCK')
        self.run_git(self.repo, 'commit', '-m', 'metadata security fixture')
        metadata_head = self.run_git(self.repo, 'rev-parse', 'HEAD')
        findings, _, _, _ = secret_scanner.scan_candidate(self.repo, valid_head, metadata_head, policy)
        self.assertTrue(any(item['path'] == 'metadata-marker.m4a' for item in findings), findings)

        # Text disguised as M4A is scanned and fails structural validation.
        spoof_path = self.repo / 'spoofed.m4a'
        spoof_path.write_text(fixture_assignment + '\n')
        self.run_git(self.repo, 'add', 'spoofed.m4a')
        with self.assertRaises(auth.PublicationError) as spoofed:
            guard.commit_safety(self.repo, command)
        self.assertEqual(spoofed.exception.reason_code, 'M4A_INVALID')
        self.run_git(self.repo, 'commit', '-m', 'spoofed audio fixture')
        spoof_head = self.run_git(self.repo, 'rev-parse', 'HEAD')
        findings, blockers, _, _ = secret_scanner.scan_candidate(self.repo, metadata_head, spoof_head, policy)
        self.assertTrue(any(item['path'] == 'spoofed.m4a' for item in findings), findings)
        self.assertTrue(any('invalid or spoofed M4A' in item for item in blockers), blockers)

        # Oversized M4A gets a fixed, actionable reason in both checks.
        oversized_path = self.repo / 'oversized.m4a'
        oversized_path.write_bytes(b'x' * (8 * 1024 * 1024 + 1))
        self.run_git(self.repo, 'add', 'oversized.m4a')
        with self.assertRaises(auth.PublicationError) as oversized:
            guard.commit_safety(self.repo, command)
        self.assertEqual(oversized.exception.reason_code, 'M4A_TOO_LARGE')
        output = __import__('io').StringIO()
        with patch('sys.stdout', output):
            guard.deny_hook_input('claude-code', 'M4A_TOO_LARGE')
        self.assertIn('Git LFS or external asset storage', output.getvalue())
        self.run_git(self.repo, 'commit', '-m', 'oversized audio fixture')
        oversized_head = self.run_git(self.repo, 'rev-parse', 'HEAD')
        _, blockers, _, _ = secret_scanner.scan_candidate(self.repo, spoof_head, oversized_head, policy)
        self.assertTrue(any('exceeds 8 MiB' in item and 'Git LFS' in item for item in blockers), blockers)

    def test_authority_configuration_is_not_agent_supplied(self):
        path = self.path / 'trust.yaml'
        path.write_text('version: 1\n')
        with self.assertRaises(auth.PublicationError):
            auth.protected_file(path)
        with patch.dict(os.environ, {'AIPS_PUBLICATION_AUTHORITY': str(path)}):
            self.assertEqual(auth.CONFIG, Path('/etc/aips/publication-authority.yaml'))
        with patch('publication_authority.protected_file', return_value=path), patch('publication_authority.os.access', return_value=True), self.assertRaises(auth.PublicationError):
            auth.configured_authority()

    def test_github_option_aliases_and_body_file_actual_cwd(self):
        self.run_git(self.repo, 'remote', 'set-url', 'origin', 'https://github.com/owner/project.git')
        sub = self.repo / 'sub'
        sub.mkdir()
        # Keep message files outside the tracked tree to preserve a clean candidate.
        first, second = self.path / 'first.md', self.path / 'second.md'
        first.write_text('first body')
        second.write_text('second body')
        argv = ['gh', 'pr', 'create', '--repo', 'owner/project', '--head', 'feature', '--base', 'main',
                '--title', 'Feature', '--body-file', '../first.md']
        with patch('publication_authority._tip', side_effect=lambda cwd, remote, ref: self.head if ref.endswith('/feature') else self.base):
            observed = auth.action(self.repo, 'gh_pr_create', argv, self.base)
            self.assertEqual(observed['file_inputs']['--body-file']['path'], str(first.resolve()))
            with self.assertRaises(FileNotFoundError):
                auth.action(sub, 'gh_pr_create', argv, self.base)
            for extra in [['-R', 'other/repo'], ['--repo=other/repo'], ['-B', 'other']]:
                with self.assertRaises(auth.PublicationError):
                    auth.action(self.repo, 'gh_pr_create', argv + extra, self.base)

    def test_merge_and_release_exact_targets(self):
        self.run_git(self.repo, 'remote', 'set-url', 'origin', 'https://github.com/owner/project.git')
        merge = ['gh', 'pr', 'merge', '7', '--repo', 'owner/project', '--squash', '--match-head-commit', self.head]
        original = auth.run
        real_subprocess_run = subprocess.run
        def observe(cwd, *argv):
            if argv[0] == 'gh':
                import json
                return json.dumps({'url': 'https://github.com/owner/project/pull/7', 'state': 'OPEN',
                                   'isDraft': False, 'mergeable': 'MERGEABLE', 'headRefOid': self.head,
                                   'headRefName': 'codex/test-merge',
                                   'baseRefOid': self.base, 'baseRefName': 'main'})
            return original(cwd, *argv)
        def observe_checks(argv, **kwargs):
            if argv[:3] == ['gh', 'pr', 'checks']:
                return subprocess.CompletedProcess(argv, 0, '[{"bucket":"pass","name":"repository"}]', '')
            return real_subprocess_run(argv, **kwargs)
        def policy_reader(_root, endpoint):
            if endpoint.endswith('/rules/branches/main') or 'rulesets?' in endpoint:
                payload = []
            elif endpoint.endswith('/branches/main/protection'):
                payload = {'required_status_checks': {'contexts': ['repository']}}
            elif endpoint.endswith('/branches/main'):
                payload = {'name': 'main', 'protected': True}
            else:
                raise AssertionError(endpoint)
            return {'returncode': 0, 'http_status': 200, 'payload': payload,
                    'endpoint': endpoint, 'error_class': None, 'error_message': None}
        with patch('publication_authority._tip', return_value=self.base), \
                patch('publication_authority._remote_default_branch', return_value='main'), \
                patch('publication_authority.run', side_effect=observe), \
                patch('publication_authority.subprocess.run', side_effect=observe_checks), \
                patch('repository_governance_snapshot.query_github_api', side_effect=policy_reader):
            self.assertEqual(auth.action(self.repo, 'gh_pr_merge', merge, self.base)['target_ref'], 'refs/heads/main')
            self.assertTrue(auth.action(self.repo, 'gh_pr_merge', merge + ['--auto'], self.base)['merge_confirmation']['auto_merge'])
            for flag in ['-d', '--auto=true', '--admin=true', '--delete-branch=true']:
                with self.assertRaises(auth.PublicationError):
                    auth.action(self.repo, 'gh_pr_merge', merge + [flag], self.base)

            with patch.dict(os.environ, {'AIPS_ENFORCE_REQUIRED_CHECKS': '1'}), \
                    patch('publication_authority.subprocess.run', side_effect=lambda argv, **kwargs:
                          subprocess.CompletedProcess(argv, 0, '[]', '') if argv[:3] == ['gh', 'pr', 'checks']
                          else observe_checks(argv, **kwargs)), \
                    self.assertRaisesRegex(auth.PublicationError, 'missing or not all passing'):
                auth.action(self.repo, 'gh_pr_merge', merge + ['--auto'], self.base)
        self.run_git(self.repo, 'tag', 'v1')
        release = ['gh', 'release', 'create', 'v1', '--repo', 'owner/project', '--verify-tag']
        with patch('publication_authority._tip', return_value=self.head):
            self.assertEqual(auth.action(self.repo, 'gh_release_create', release, self.base)['tag_oid'], self.head)
            with self.assertRaises(auth.PublicationError):
                auth.action(self.repo, 'gh_release_create', release + ['--target', self.base], self.base)
        with patch('publication_authority._tip', return_value=self.base), self.assertRaises(auth.PublicationError):
            auth.action(self.repo, 'gh_release_create', release, self.base)

    def test_hook_denies_unsupported_shell(self):
        import json
        commands = ["sh <<'EOF'\ngit push origin main\nEOF\n", 'G=git; $G push origin main',
                    "env -S 'git push origin main'", 'git -c alias.publish=push publish origin main']
        for command in commands:
            payload = {'cwd': str(self.repo), 'tool_input': {'command': command}}
            proc = subprocess.run([sys.executable, str(ROOT / 'scripts/governance_guard.py'), 'hook', '--runtime', 'claude-code'],
                                  input=json.dumps(payload), text=True, capture_output=True, check=False)
            self.assertEqual(proc.returncode, 0)
            response = json.loads(proc.stdout)['hookSpecificOutput']
            self.assertEqual(response['permissionDecision'], 'deny')
        dynamic = {'cwd': str(self.repo), 'tool_input': {'command': 'git "$(printf push)" origin main'}}
        proc = subprocess.run([sys.executable, str(ROOT / 'scripts/governance_guard.py'), 'hook', '--runtime', 'claude-code'],
                              input=json.dumps(dynamic), text=True, capture_output=True, check=False)
        response = json.loads(proc.stdout)['hookSpecificOutput']
        self.assertEqual(response['permissionDecision'], 'deny')
        self.assertIn('[DYNAMIC_SUBCOMMAND]', response['permissionDecisionReason'])

    def test_claude_hook_accepts_safe_argument_substitutions(self):
        import json
        for command in ['git show "$(git rev-parse HEAD)"',
                        'git diff "$(git merge-base HEAD origin/main)" HEAD',
                        'cat <<EOF\nrevision=$(git rev-parse HEAD)\nEOF\n']:
            payload = {'cwd': str(self.repo), 'tool_input': {'command': command}}
            proc = subprocess.run([sys.executable, str(ROOT / 'scripts/governance_guard.py'), 'hook', '--runtime', 'claude-code'],
                                  input=json.dumps(payload), text=True, capture_output=True, check=False)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(json.loads(proc.stdout), {})

    def test_personal_merge_hook_respects_confirmed_merge_and_task_authorized_auto_merge(self):
        import io
        import json
        import tomllib

        command = 'gh pr merge 7 --repo owner/project --squash --match-head-commit ' + self.head
        publication = {
            'github_repo': 'owner/project',
            'merge_confirmation': {'pr_number': 7, 'required_checks': ['repository'],
                                   'base_branch': 'main', 'base_sha': self.base, 'head_sha': self.head},
        }
        payload = {'cwd': str(self.repo), 'tool_input': {'command': command}}
        for runtime in ['claude-code', 'gemini-cli']:
            output = io.StringIO()
            with patch('sys.stdin', io.StringIO(json.dumps(payload))), patch('sys.stdout', output), \
                    patch('runtime_policy.action_from_hook', return_value=None), \
                    patch.object(guard, 'safe_emit', return_value={'decision': 'ALLOW'}), \
                    patch('publication_authority.publication_mode', return_value='personal'), \
                    patch('publication_authority.validate_personal_action', return_value=publication):
                guard.hook(runtime)
            response = json.loads(output.getvalue())
            if runtime == 'claude-code':
                hook_output = response['hookSpecificOutput']
                self.assertEqual(hook_output['permissionDecision'], 'ask')
                self.assertIn(self.head, hook_output['permissionDecisionReason'])
                self.assertIn(self.base, hook_output['permissionDecisionReason'])
            else:
                self.assertEqual(response['decision'], 'allow')
                self.assertIn(self.head, response['systemMessage'])

        # Explicit task intent plus the fully validated --auto path lets GitHub
        # finish after checks pass without a second Claude per-call prompt.
        auto_command = command + ' --auto'
        auto_payload = {'cwd': str(self.repo), 'tool_input': {'command': auto_command}}
        auto_publication = {**publication, 'merge_confirmation': {**publication['merge_confirmation'], 'auto_merge': True}}
        with patch('sys.stdin', io.StringIO(json.dumps(auto_payload))), patch('sys.stdout', io.StringIO()) as output, \
                patch('runtime_policy.action_from_hook', return_value=None), \
                patch.object(guard, 'safe_emit', return_value={'decision': 'ALLOW'}), \
                patch('publication_authority.publication_mode', return_value='personal'), \
                patch('publication_authority.validate_personal_action', return_value=auto_publication):
            guard.hook('claude-code')
        auto_response = json.loads(output.getvalue())['hookSpecificOutput']
        self.assertEqual(auto_response['permissionDecision'], 'allow')
        self.assertIn('enable auto-merge', auto_response['permissionDecisionReason'])
        self.assertIn(self.head, auto_response['permissionDecisionReason'])

        # Gemini retains its native ask_user extension rule, including for --auto.
        with patch('sys.stdin', io.StringIO(json.dumps(auto_payload))), patch('sys.stdout', io.StringIO()) as output, \
                patch('runtime_policy.action_from_hook', return_value=None), \
                patch.object(guard, 'safe_emit', return_value={'decision': 'ALLOW'}), \
                patch('publication_authority.publication_mode', return_value='personal'), \
                patch('publication_authority.validate_personal_action', return_value=auto_publication):
            guard.hook('gemini-cli')
        gemini_auto = json.loads(output.getvalue())
        self.assertEqual(gemini_auto['decision'], 'allow')
        self.assertIn(self.head, gemini_auto['systemMessage'])

        policy_path = ROOT / 'harness/adapters/gemini-cli/policies/personal-pr-merge.toml'
        rule = tomllib.loads(policy_path.read_text())['rule'][0]
        self.assertEqual(rule['decision'], 'ask_user')
        self.assertTrue(rule['interactive'])
        self.assertEqual(set(rule['modes']), {'default', 'autoEdit', 'yolo'})

    def test_claude_hook_allows_a_valid_personal_branch_push_without_grant(self):
        import json
        self.run_git(self.repo, 'fetch', 'origin', 'main')
        self.run_git(self.repo, 'switch', '-c', 'codex/hook-test')
        command = f'git push origin {self.head}:refs/heads/codex/hook-test'
        payload = {'cwd': str(self.repo), 'tool_input': {'command': command}}
        proc = subprocess.run([sys.executable, str(ROOT / 'scripts/governance_guard.py'), 'hook', '--runtime', 'claude-code'],
                              input=json.dumps(payload), text=True, capture_output=True, check=False)
        self.assertEqual(proc.returncode, 0)
        response = json.loads(proc.stdout)['hookSpecificOutput']
        self.assertEqual(response['permissionDecision'], 'allow')
        self.assertIn('personal publication checks passed', response['permissionDecisionReason'])


class ShellTest(unittest.TestCase):
    def test_strings_heredocs_and_executable_substitutions(self):
        literal = 'text\ncat <<EOF\nliteral payload\nEOF\n'
        import shlex
        self.assertEqual(shell_commands('printf ' + shlex.quote(literal))[0][1], literal)
        harmless = ["printf 'git push'", "cat <<'EOF'\ngit push origin main\nEOF\n",
                    'cat <<EOF\ngit push origin main\nEOF\n', "echo '$(git push)'", '# git push\ngit status']
        for command in harmless:
            self.assertEqual(guard.operations_for(command), [])
        for command in ['echo $(git push origin main)', 'echo `git push origin main`',
                        'cat <(git push origin main)', 'git status\ngit push origin main',
                        'cat <<EOF\n$(git push origin main)\nEOF\n',
                        'cat <<EOF\n`git push origin main`\nEOF\n',
                        'echo "${VALUE:-$(git push origin main)}"',
                        'cat <<EOF\n${VALUE:-$(git push origin main)}\nEOF\n',
                        'cat <<-EOF\n\t$(git push origin main)\n\tEOF\n']:
            self.assertIn('git_push', guard.operations_for(command))
        for command in ["cat <<'EOF'\n$(git push origin main)\nEOF\n",
                        'cat <<EOF\n\\$(git push origin main)\nEOF\n',
                        'cat <<EOF\njust $HOME\nEOF\n',
                        'git show "$(git rev-parse HEAD)"',
                        'git diff "$(git merge-base HEAD origin/main)" HEAD',
                        'echo "${VALUE:-$(git rev-parse HEAD)}"',
                        'cat <<EOF\n${VALUE:-$(git rev-parse HEAD)}\nEOF\n',
                        'git show -- "$(git rev-parse HEAD)"',
                        'gh --repo owner/project pr view "$(printf 7)"',
                        'cat <<EOF\n\\`git push origin main\\`\nEOF\n']:
            with self.subTest(command=command):
                self.assertEqual(guard.operations_for(command), [])
        # A dynamic directory/repository is allowed for read-only commands only.
        for command in ['git -C "$(pwd)" status', 'gh --repo "$(printf owner/project)" pr view']:
            with self.subTest(command=command):
                self.assertEqual(guard.operations_for(command), [])
        for command, code in [('git "$(printf status)"', 'DYNAMIC_SUBCOMMAND'),
                              ('gh pr "$(printf view)"', 'DYNAMIC_SUBCOMMAND'),
                              ('git -C "$(pwd)" push origin main', 'DYNAMIC_CLI_OPTION'),
                              ('gh --repo "$(printf owner/project)" pr create --title x', 'DYNAMIC_CLI_OPTION'),
                              ('git -c "$KEY" status', 'DYNAMIC_CLI_OPTION'),
                              ('git --exec-path="$DIR" status', 'DYNAMIC_CLI_OPTION')]:
            with self.subTest(command=command), self.assertRaises(CommandError) as raised:
                guard.operations_for(command)
            self.assertEqual(raised.exception.reason_code, code)
        with self.assertRaises(CommandError) as raised:
            shell_commands('cat <<EOF\n$(git push origin main\nEOF\n')
        self.assertEqual(raised.exception.reason_code, 'UNSUPPORTED_HEREDOC')

    def test_tag_reads_and_merge_mutation(self):
        for command in ['git tag', 'git tag --list', 'git tag -l "v*"', 'git tag --verify v1', 'git tag -n9']:
            self.assertEqual(guard.operations_for(command), [])
        for command in ['git tag v1', 'git tag -d v1', 'git tag --list -f v1']:
            self.assertEqual(guard.operations_for(command), ['git_tag'])
        self.assertEqual(guard.operations_for('gh pr merge 1'), ['gh_pr_merge'])

    def test_malformed_shell_fails_closed(self):
        with self.assertRaises(CommandError):
            shell_commands('git push "')
        for command in ["sh <<'EOF'\ngit push origin main\nEOF\n", 'x=git; "$x" push', 'git "$operation" origin main',
                        'git${EMPTY} push origin main', 'git -c alias.publish=push publish origin main',
                        "env -S 'git push origin main'", 'g[i]t push origin main', 'sh < commands.sh',
                        "printf 'git push origin main' | sh"]:
            with self.subTest(command=command), self.assertRaises(CommandError):
                guard.operations_for(command)
        self.assertIn('git_push', guard.operations_for("bash --rcfile /tmp/rc -c 'git push origin main'"))
        for command in ['git send-pack origin main', 'git http-push origin main', 'gh api repos/owner/repo/git/refs -X POST',
                        'gh pr close 1 --delete-branch', 'gh release edit v1 --target other']:
            with self.subTest(command=command), self.assertRaises(CommandError):
                guard.operations_for(command)
        self.assertEqual(guard.operations_for('gh api --method GET repos/owner/repo'), [])

    def test_unquoted_glob_cannot_reuse_a_literal_grant(self):
        literal = shell_commands("gh pr create --body '*'")
        expanded = shell_commands('gh pr create --body *')
        self.assertNotEqual(literal, expanded)
        self.assertIn('\0', expanded[0][-1])
        self.assertIn('\0', shell_commands('gh pr create --body ~/body')[0][-1])


class GuardFalseDenialTest(unittest.TestCase):
    """Read-only and standard commit forms are allowed; publication-capable forms stay denied."""

    HEREDOC = "git commit -m \"$(cat <<'EOF'\n{body}\nEOF\n)\""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        for args in (['init', '-q', '-b', 'main'], ['config', 'user.name', 'Fixture'],
                     ['config', 'user.email', 'fixture' + '@' + 'users.noreply.github.com']):
            self.git(*args)
        (self.repo / 'file.txt').write_text('initial\n')
        self.git('add', 'file.txt')
        self.git('commit', '-qm', 'base')
        corpus = (ROOT / 'tests/fixtures/content-safety/corpus.json').read_text(encoding='utf-8')
        import json
        self.ambiguous = bytes.fromhex(json.loads(corpus)['ambiguous_hex']).decode('utf-8')

    def git(self, *args, cwd=None):
        return subprocess.run(['git', *args], cwd=cwd or self.repo, capture_output=True, text=True, check=True).stdout

    def hook(self, command, cwd=None):
        import json
        payload = {'hook_event_name': 'PreToolUse', 'tool_name': 'Bash', 'cwd': str(cwd or self.repo),
                   'tool_input': {'command': command}}
        proc = subprocess.run([sys.executable, str(ROOT / 'scripts/governance_guard.py'), 'hook', '--runtime', 'claude-code'],
                              input=json.dumps(payload), text=True, capture_output=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout).get('hookSpecificOutput', {})

    def test_read_only_classification_table(self):
        allowed = ['git -C $PWD status', 'gh --repo "$(printf a/b)" pr view', '$TOOLS/.venv/bin/python x.py',
                   'gh api repos/a/b', 'gh api -X GET repos/a/b', 'gh api --method=GET repos/a/b --paginate',
                   'git lfs pull', 'git lfs ls-files', 'git lfs track "*.psd"']
        for command in allowed:
            with self.subTest(command=command):
                self.assertEqual(guard.operations_for(command, self.repo), [])
        denied = {'$X push': 'DYNAMIC_EXECUTABLE', '"$x" push': 'DYNAMIC_EXECUTABLE', '$D/git push': 'DYNAMIC_EXECUTABLE',
                  '$D/gh pr create': 'DYNAMIC_EXECUTABLE', '$D/bash -c x': 'DYNAMIC_EXECUTABLE',
                  'git -C $X push origin main': 'DYNAMIC_CLI_OPTION', 'git --config-env=$X status': 'DYNAMIC_CLI_OPTION',
                  'gh api repos/a/b -X POST': 'UNBOUND_GITHUB_API_MUTATION', 'gh api -XPATCH repos/a': 'UNBOUND_GITHUB_API_MUTATION',
                  'gh api graphql -f query=x': 'UNBOUND_GITHUB_API_MUTATION', 'gh api --input body.json repos/a': 'UNBOUND_GITHUB_API_MUTATION',
                  'gh api -X "$M" repos/a': 'AMBIGUOUS_GITHUB_API_REQUEST',
                  'git lfs push origin main': 'UNSUPPORTED_GIT_LFS_COMMAND', 'git lfs lock x': 'UNSUPPORTED_GIT_LFS_COMMAND'}
        for command, code in denied.items():
            with self.subTest(command=command), self.assertRaises(CommandError) as raised:
                guard.operations_for(command, self.repo)
            self.assertEqual(raised.exception.reason_code, code)

    def test_git_aliases_expand_only_to_read_only_commands(self):
        for name, value in {'st': 'status -sb', 'lg': '!git log --oneline', 'pub': 'push origin main',
                            'ci': 'commit -m x', 'shpub': '!git push origin main', 'nest': 'pub', 'loop': '!git loop'}.items():
            self.git('config', 'alias.' + name, value)
        self.assertEqual(guard.operations_for('git st', self.repo), [])
        self.assertEqual(guard.operations_for('git lg', self.repo), [])
        for command, code in {'git pub': 'GIT_ALIAS_PUBLICATION_UNSUPPORTED', 'git ci': 'GIT_ALIAS_PUBLICATION_UNSUPPORTED',
                              'git shpub': 'GIT_ALIAS_PUBLICATION_UNSUPPORTED', 'git nest': 'GIT_ALIAS_PUBLICATION_UNSUPPORTED',
                              'git loop': 'UNKNOWN_GIT_COMMAND', 'git nosuch': 'UNKNOWN_GIT_COMMAND',
                              # Global options can change which configuration defines the alias.
                              'git -C . st': 'UNKNOWN_GIT_COMMAND',
                              'git -c alias.publish=push publish origin main': 'UNKNOWN_GIT_COMMAND'}.items():
            with self.subTest(command=command), self.assertRaises(CommandError) as raised:
                guard.operations_for(command, self.repo)
            self.assertEqual(raised.exception.reason_code, code)

    def test_literal_heredoc_message_is_inlined_only_when_bash_would_keep_it_literal(self):
        message = 'fix: `quoted` costs $5\n\nCo-Authored-By: Claude <noreply' + '@' + 'anthropic.com>'
        command = self.HEREDOC.format(body=message)
        self.assertEqual(shell_commands(command, mark_dynamic=True), [['git', 'commit', '-m', message]])
        self.assertEqual(guard.operations_for(command), ['git_commit'])
        tabbed = "git commit -m \"$(cat <<-'EOF'\n\tline\n\tEOF\n)\""
        self.assertEqual(shell_commands(tabbed), [['git', 'commit', '-m', 'line']])
        # The heredoc would end early, after a comment or with an unquoted delimiter: never treat as literal.
        unsafe = ["git commit -m \"$(cat <<'EOF'\nmsg\nEOF\ngit push origin main\nEOF\n)\"",
                  "git commit -m x # \"$(cat <<'EOF'\ngit push origin main\nEOF\n)\"",
                  "git commit -m \"$(cat <<'EOF'\nmsg\n\tEOF\n)\""]
        for item in unsafe:
            with self.subTest(command=item), self.assertRaises(CommandError):
                guard.operations_for(item)
        self.assertIn('git_push', guard.operations_for("git commit -m \"$(cat <<EOF\n$(git push origin main)\nEOF\n)\""))

    def test_standard_commit_forms_are_scanned_not_denied(self):
        self.git('config', 'user.email', 'fixture' + '@' + 'users.noreply.github.com')
        (self.repo / 'file.txt').write_text('clean change\n')
        self.git('add', 'file.txt')
        self.assertEqual(self.hook(self.HEREDOC.format(body='fix: clean `change`'))['permissionDecision'], 'allow')
        self.assertEqual(self.hook("git commit -m 'literal `ticks` and $HOME'")['permissionDecision'], 'allow')
        self.assertEqual(self.hook('git commit -m "$MSG"')['permissionDecision'], 'deny')
        self.assertEqual(guard.commit_safety(self.repo, 'git commit --amend -m amended')['decision'], 'ALLOW')
        self.assertEqual(guard.commit_safety(self.repo, 'git commit --amend --no-edit')['decision'], 'ALLOW')
        self.git('reset', '-q')
        (self.repo / 'sub').mkdir()
        (self.repo / 'sub/new.txt').write_text('new\n')
        self.assertEqual(self.hook('git add new.txt && git commit -m add', cwd=self.repo / 'sub')['permissionDecision'], 'allow')
        self.assertEqual(self.hook('git add -A && ' + self.HEREDOC.format(body='add all'))['permissionDecision'], 'allow')
        for unsupported in ['git add -p && git commit -m x', 'git add x; git commit -m x', 'git status && git commit -m x',
                            'git add x && git commit -m x && git push origin main']:
            with self.subTest(command=unsupported):
                self.assertEqual(self.hook(unsupported)['permissionDecision'], 'deny')

    def test_unstaged_content_that_the_commit_includes_is_scanned(self):
        fixture_assignment = scanner_fixture_assignment() + '\n'
        (self.repo / 'sub').mkdir()
        (self.repo / 'sub/leak.txt').write_text(fixture_assignment)
        for command, cwd in [('git add leak.txt && git commit -m add', self.repo / 'sub'),
                             ('git add -A && git commit -m add', self.repo),
                             ('git add . && ' + self.HEREDOC.format(body='add'), self.repo)]:
            with self.subTest(command=command):
                response = self.hook(command, cwd=cwd)
                self.assertEqual(response['permissionDecision'], 'deny')
                self.assertIn('CONTENT_SECRET_BLOCKED', response['permissionDecisionReason'])
        (self.repo / 'sub/leak.txt').unlink()
        (self.repo / 'file.txt').write_text(fixture_assignment)
        for command in ['git commit -a -m change', 'git commit -am change']:
            with self.subTest(command=command):
                self.assertIn('CONTENT_SECRET_BLOCKED', self.hook(command)['permissionDecisionReason'])
        self.assertEqual(self.hook(self.HEREDOC.format(body=fixture_assignment.strip()))['permissionDecision'], 'deny')

    def test_ambiguous_injection_review_still_blocks_commit(self):
        # Push-time candidate scanning covers secrets only, so commit is the local injection gate.
        (self.repo / 'notes.md').write_text(self.ambiguous)
        self.git('add', 'notes.md')
        staged = guard.commit_safety(self.repo, 'git commit -m notes')
        self.assertEqual(staged['decision'], 'BLOCK')
        self.assertEqual(staged['reason_code'], 'CONTENT_REVIEW_REQUIRED')
        response = self.hook('git commit -m notes')
        self.assertEqual(response['permissionDecision'], 'deny')
        self.assertIn('CONTENT_REVIEW_REQUIRED', response['permissionDecisionReason'])
        self.git('reset', '-q')
        import shlex
        message = guard.commit_safety(self.repo, 'git commit --allow-empty -m ' + shlex.quote(self.ambiguous))
        self.assertEqual(message['decision'], 'BLOCK')
        self.assertEqual(message['reason_code'], 'CONTENT_REVIEW_REQUIRED')

    def test_command_classification_denials_have_stable_diagnostics(self):
        import re
        source = (ROOT / 'scripts/governance_guard.py').read_text() + (ROOT / 'scripts/publication_commands.py').read_text()
        codes = set(re.findall(r"""CommandError\([^)]*?['"]([A-Z][A-Z_]{5,})['"]\)""", source))
        self.assertTrue({'DYNAMIC_EXECUTABLE', 'UNKNOWN_GIT_COMMAND', 'GIT_ALIAS_PUBLICATION_UNSUPPORTED'} <= codes, codes)
        for code in sorted(codes):
            with self.subTest(code=code):
                self.assertIn(code, auth.PUBLICATION_DIAGNOSTICS)
                self.assertEqual(auth.PublicationError('', code).diagnostic()['reason_code'], code)
        for command, code in {'$X push': 'DYNAMIC_EXECUTABLE', 'git nosuch': 'UNKNOWN_GIT_COMMAND',
                              'gh api repos/a -X POST': 'UNBOUND_GITHUB_API_MUTATION'}.items():
            with self.subTest(command=command):
                import json
                response = self.hook(command)
                self.assertIn('[' + code + ']', response['permissionDecisionReason'])
                context = json.loads(response['additionalContext'].split('AIPS diagnostic: ', 1)[1])
                self.assertEqual(context['reason_code'], code)
                self.assertTrue(context['detail_zh'])

    def test_untracked_files_are_reported_but_do_not_block_publication(self):
        (self.repo / 'draft.md').write_text('local notes\n')
        details = auth.worktree_dirty_details(self.repo)
        self.assertEqual(details['status'], 'CLEAN')
        self.assertEqual(details['untracked_count'], 1)
        self.assertEqual(details['paths']['untracked'], ['draft.md'])
        (self.repo / 'file.txt').write_text('tracked edit\n')
        self.assertEqual(auth.worktree_dirty_details(self.repo)['status'], 'DIRTY')


if __name__ == '__main__':
    unittest.main()

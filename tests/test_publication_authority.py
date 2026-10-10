from __future__ import annotations

import base64
import copy
import os
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
import governance_guard as guard
import publication_authority as auth
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
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
        with self.assertRaises(auth.PublicationError):
            guard.commit_safety(self.repo, 'git commit -a -m candidate')
        for dynamic in ['git commit -m "$MSG"', "git commit -m $'encoded\\x41message'", 'git commit -F ~/message',
                        'git commit -m author\\\n' + '@' + 'example.test', 'git commit -m {hello,world}']:
            with self.subTest(command=dynamic), self.assertRaises(auth.PublicationError):
                guard.commit_safety(self.repo, dynamic)

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
        def observe(cwd, *argv):
            if argv[0] == 'gh':
                import json
                return json.dumps({'headRefOid': self.head, 'baseRefOid': self.base, 'baseRefName': 'main'})
            return original(cwd, *argv)
        with patch('publication_authority._tip', return_value=self.base), patch('publication_authority.run', side_effect=observe):
            self.assertEqual(auth.action(self.repo, 'gh_pr_merge', merge, self.base)['target_ref'], 'refs/heads/main')
            for flag in ['-d', '--auto=true', '--admin=true', '--delete-branch=true']:
                with self.assertRaises(auth.PublicationError):
                    auth.action(self.repo, 'gh_pr_merge', merge + [flag], self.base)
        self.run_git(self.repo, 'tag', 'v1')
        release = ['gh', 'release', 'create', 'v1', '--repo', 'owner/project', '--verify-tag']
        with patch('publication_authority._tip', return_value=self.head):
            self.assertEqual(auth.action(self.repo, 'gh_release_create', release, self.base)['tag_oid'], self.head)
            with self.assertRaises(auth.PublicationError):
                auth.action(self.repo, 'gh_release_create', release + ['--target', self.base], self.base)
        with patch('publication_authority._tip', return_value=self.base), self.assertRaises(auth.PublicationError):
            auth.action(self.repo, 'gh_release_create', release, self.base)

    def test_hook_returns_normal_deny_for_merge_and_unsupported_shell(self):
        import json
        commands = ['gh pr merge 7', "sh <<'EOF'\ngit push origin main\nEOF\n", 'G=git; $G push origin main',
                    "env -S 'git push origin main'", 'git -c alias.publish=push publish origin main']
        for command in commands:
            payload = {'cwd': str(self.repo), 'tool_input': {'command': command}}
            proc = subprocess.run([sys.executable, str(ROOT / 'scripts/governance_guard.py'), 'hook', '--runtime', 'claude-code'],
                                  input=json.dumps(payload), text=True, capture_output=True, check=False)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(json.loads(proc.stdout)['hookSpecificOutput']['permissionDecision'], 'deny')


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
                        'cat <(git push origin main)', 'git status\ngit push origin main']:
            self.assertIn('git_push', guard.operations_for(command))
        with self.assertRaises(CommandError):
            shell_commands('cat <<EOF\n$(git push origin main)\nEOF\n')

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


if __name__ == '__main__':
    unittest.main()

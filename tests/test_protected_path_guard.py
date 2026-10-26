from __future__ import annotations

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
import manage_runtime_adapter as adapter
import protected_paths as pp

GUARD = ROOT / 'scripts' / 'governance_guard.py'
PYTHON = sys.executable


class ProtectedPathResolutionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(os.path.realpath(self._tmp.name)) / 'home'
        self.project = Path(os.path.realpath(self._tmp.name)) / 'project'
        self.project.mkdir(parents=True)
        self.env = {'HOME': str(self.home)}
        self.env_patch = patch.dict(os.environ, self.env, clear=False)
        self.env_patch.start()
        for key in ('XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'AIPS_INSTALL_DIR'):
            os.environ.pop(key, None)
        self.addCleanup(self.env_patch.stop)
        self.system = self.home / '.local' / 'share' / 'aips' / 'system'
        self.config = self.home / '.config' / 'aips'

    def test_default_install_and_config_roots_follow_home(self):
        self.assertIn(self.system.resolve(), pp.installed_system_roots())
        self.assertEqual(pp.config_home(), self.config)

    def test_env_overrides_are_honored(self):
        override = Path(self._tmp.name) / 'custom-install'
        xdg = Path(self._tmp.name) / 'xdg-config'
        with patch.dict(os.environ, {'AIPS_INSTALL_DIR': str(override), 'XDG_CONFIG_HOME': str(xdg)}):
            self.assertIn(override.resolve(), pp.installed_system_roots())
            self.assertEqual(pp.config_home(), xdg / 'aips')
            self.assertEqual(pp.protected_category((xdg / 'aips' / 'profile.yaml').resolve()), 'profile_settings')

    def test_categories_cover_system_tree_and_profile_settings_only(self):
        self.assertEqual(pp.protected_category((self.system / 'scripts' / 'x.py').resolve()), 'installed_system')
        self.assertEqual(pp.protected_category(self.system.resolve()), 'installed_system')
        self.assertEqual(pp.protected_category((self.config / 'profile.yaml').resolve()), 'profile_settings')
        self.assertEqual(pp.protected_category((self.config / 'profiles' / 'x.yaml').resolve()), 'profile_settings')
        self.assertIsNone(pp.protected_category((self.config / 'harness' / 'x.yaml').resolve()))
        self.assertIsNone(pp.protected_category((self.home / '.local' / 'share' / 'aips' / 'other').resolve()))
        self.assertIsNone(pp.protected_category((self.project / 'x').resolve()))

    def test_edit_tools_resolve_dotdot_and_symlinks(self):
        link = self.project / 'link'
        link.symlink_to(self.system)
        traversal = str(self.project / '..' / 'home' / '.local' / 'share' / 'aips' / 'system' / 'x.py')
        self.assertTrue(pp.file_tool_write_is_protected('Edit', {'file_path': traversal}, self.project))
        self.assertTrue(pp.file_tool_write_is_protected('Write', {'file_path': str(link / 'x.py')}, self.project))
        self.assertTrue(pp.file_tool_write_is_protected('NotebookEdit', {'notebook_path': str(self.system / 'n.ipynb')}, self.project))
        self.assertTrue(pp.file_tool_write_is_protected('MultiEdit', {'file_path': str(self.system / 'm.py')}, self.project))
        self.assertTrue(pp.file_tool_write_is_protected('Edit', {'file_path': str(self.config / 'profile.yaml')}, self.project))

    def test_edit_tools_allow_project_and_unrelated_paths(self):
        self.assertFalse(pp.file_tool_write_is_protected('Edit', {'file_path': str(self.project / 'a.py')}, self.project))
        self.assertFalse(pp.file_tool_write_is_protected('Write', {'file_path': 'relative.txt'}, self.project))
        self.assertFalse(pp.file_tool_write_is_protected('Read', {'file_path': str(self.system / 'x')}, self.project))
        self.assertFalse(pp.file_tool_write_is_protected('Edit', {'file_path': ''}, self.project))

    def test_unresolvable_edit_path_denies_only_plausible_aips_paths(self):
        self.assertTrue(pp.file_tool_write_is_protected('Edit', {'file_path': 'aips\x00bad'}, self.project))
        self.assertFalse(pp.file_tool_write_is_protected('Edit', {'file_path': 'other\x00bad'}, self.project))

    def test_bash_write_forms_are_detected(self):
        target = str(self.system / 'VERSION')
        denied = [
            f'echo 1.0 > {target}',
            f'echo 1.0 >> {target}',
            f'echo 1.0 2>/dev/null > {target}',
            f'cp /tmp/a {target}',
            f'mv {target} {target}.bak',
            f'rm -f {target}',
            f'tee {target}',
            f"sed -i 's/a/b/' {target}",
            f'ln -sf /tmp/x {target}',
            f'install -m 644 a {target}',
            f'dd if=/dev/zero of={target}',
            f'truncate -s 0 {target}',
            f'bash -c "echo x > {target}"',
            'echo x > "$HOME/.local/share/aips/system/VERSION"',
            f'echo x > {self.config}/profile.yaml',
            f'tee {self.config}/profile.yaml',
            f'echo ok && rm {self.config}/profile.yaml',
            f'git -C {self.system} commit -m fix',
            f'git -C {self.system} checkout -- .',
            f'git -C {self.system} reset --hard',
            f'git -C {self.system} stash',
            f'git -C {self.system} apply patch.diff',
            f'git --git-dir={self.system}/.git add x',
            f'cd {self.system} && rm -f VERSION',
            f'cd {self.system} && git commit -m fix',
            f'cd {self.system}; echo x > VERSION',
        ]
        for command in denied:
            with self.subTest(command=command):
                self.assertTrue(pp.bash_command_writes_protected(command, self.project))

    def test_bash_reads_and_unrelated_writes_are_allowed(self):
        allowed = [
            f'cat {self.system}/VERSION',
            f'ls {self.system}',
            f'grep -n guard {self.system}/scripts/governance_guard.py',
            f'git -C {self.system} status --short',
            f'git -C {self.system} log --oneline -1',
            f'git -C {self.system} diff --stat',
            f'git -C {self.system} rev-parse HEAD',
            f'cd {self.system} && cat VERSION',
            'echo x > out.txt',
            f'echo x > {self.project}/out.txt',
            f'cp {self.system}/VERSION {self.project}/VERSION.copy',
            f'echo x > {self.home}/.local/share/aips/harness/state.yaml',
            f'echo x > {self.config}/harness/state.yaml',
            'git status',
            'python -m pytest -q tests',
        ]
        for command in allowed:
            with self.subTest(command=command):
                self.assertFalse(pp.bash_command_writes_protected(command, self.project))

    def test_human_cli_maintenance_commands_are_not_path_writes(self):
        # aips update/install/preflight name no protected path, so the hook does not classify them.
        # The CLI keeps its own clean-tree checks: update refuses and preflight skips on local changes.
        for command in ('aips update', 'aips install', 'aips system preflight /p', 'aips preflight /p --allow-major',
                        f'{self.home}/.local/bin/aips update', 'aips update > ' + str(self.project / 'log.txt')):
            with self.subTest(command=command):
                self.assertFalse(pp.bash_command_writes_protected(command, self.project))

    def test_unparseable_command_mentioning_aips_fails_closed(self):
        self.assertTrue(pp.bash_command_writes_protected('echo "aips > x', self.project))
        self.assertFalse(pp.bash_command_writes_protected('echo "unfinished', self.project))

    def test_wrapper_nesting_beyond_limit_fails_closed(self):
        state = {'cwd': self.project}
        self.assertTrue(pp._command_writes_protected('echo x', state, pp.MAX_WRAPPER_DEPTH + 1))
        self.assertFalse(pp._command_writes_protected('echo x', state, 0))


class ClaudeGuardInstallerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.settings = Path(self._tmp.name) / 'settings.json'

    def test_guard_matcher_covers_file_edit_tools_and_keeps_failure_policy(self):
        status, _ = adapter.install_claude_hook(self.settings, 'AIPS_MANAGED_HOOK=1 hook', 'AIPS_MANAGED_HOOK=1 guard hook --runtime claude-code',
                                                'AIPS_MANAGED_HOOK=1 guard hook --runtime claude-code', fail_closed=True)
        self.assertEqual(status, 'OK')
        data = json.loads(self.settings.read_text(encoding='utf-8'))
        guard_group = next(g for g in data['hooks']['PreToolUse'] if adapter.is_aips_hook(g))
        self.assertEqual(guard_group['matcher'], 'Bash|Edit|Write|NotebookEdit|MultiEdit')
        self.assertEqual(guard_group['hooks'][0]['onFailure'], 'block')
        failure_group = next(g for g in data['hooks']['PostToolUseFailure'] if adapter.is_aips_hook(g))
        self.assertEqual(failure_group['matcher'], 'Bash')
        self.assertNotIn('onFailure', failure_group['hooks'][0])

    def test_refresh_without_failure_blocking_keeps_matcher_and_omits_onfailure(self):
        adapter.install_claude_hook(self.settings, 'AIPS_MANAGED_HOOK=1 hook', 'AIPS_MANAGED_HOOK=1 guard hook --runtime claude-code',
                                    'AIPS_MANAGED_HOOK=1 guard hook --runtime claude-code', fail_closed=True)
        adapter.install_claude_hook(self.settings, 'AIPS_MANAGED_HOOK=1 hook', 'AIPS_MANAGED_HOOK=1 guard hook --runtime claude-code',
                                    'AIPS_MANAGED_HOOK=1 guard hook --runtime claude-code', fail_closed=False)
        data = json.loads(self.settings.read_text(encoding='utf-8'))
        guard_groups = [g for g in data['hooks']['PreToolUse'] if adapter.is_aips_hook(g)]
        self.assertEqual(len(guard_groups), 1)
        self.assertEqual(guard_groups[0]['matcher'], 'Bash|Edit|Write|NotebookEdit|MultiEdit')
        self.assertNotIn('onFailure', guard_groups[0]['hooks'][0])


class GuardHookSubprocessTests(unittest.TestCase):
    """Run the real Claude Code PreToolUse hook entry point in a subprocess with a temporary HOME."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(os.path.realpath(self._tmp.name))
        self.home = self.base / 'home'
        self.project = self.base / 'project'
        self.project.mkdir(parents=True)
        self.system = self.home / '.local' / 'share' / 'aips' / 'system'
        self.system.mkdir(parents=True)
        (self.system / 'VERSION').write_text('0.1.0\n', encoding='utf-8')
        self.config = self.home / '.config' / 'aips'
        self.config.mkdir(parents=True)

    def _env(self):
        env = {key: value for key, value in os.environ.items()
               if key not in {'XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'AIPS_INSTALL_DIR',
                              'AIPS_GOVERNANCE_AUDIT_LEDGER', 'AIPS_RUNTIME_POLICY_PATH'}}
        env['HOME'] = str(self.home)
        return env

    def _run_hook(self, tool_name, tool_input):
        payload = {'hook_event_name': 'PreToolUse', 'tool_name': tool_name, 'tool_input': tool_input,
                   'cwd': str(self.project)}
        proc = subprocess.run([PYTHON, str(GUARD), 'hook', '--runtime', 'claude-code'], input=json.dumps(payload),
                              text=True, capture_output=True, env=self._env(), cwd=str(ROOT), check=False, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout, json.loads(proc.stdout or '{}')

    def _assert_denied(self, tool_name, tool_input):
        stdout, response = self._run_hook(tool_name, tool_input)
        hook_output = response.get('hookSpecificOutput', {})
        self.assertEqual(hook_output.get('permissionDecision'), 'deny', stdout)
        reason = hook_output.get('permissionDecisionReason', '')
        self.assertIn('PROTECTED_PATH_WRITE', reason)
        self.assertIn('development repository', hook_output.get('additionalContext', '') + reason)
        # The denial must never echo the protected path or the command text.
        self.assertNotIn(str(self.home), stdout)
        self.assertNotIn(str(self.system), stdout)
        self.assertNotIn(str(self.config), stdout)

    def _assert_allowed(self, tool_name, tool_input):
        stdout, response = self._run_hook(tool_name, tool_input)
        self.assertNotIn('hookSpecificOutput', response, stdout)
        self.assertNotIn('PROTECTED_PATH_WRITE', stdout)

    def test_edit_family_writes_to_installed_system_are_denied(self):
        target = str(self.system / 'scripts' / 'x.py')
        self._assert_denied('Edit', {'file_path': target, 'old_string': 'a', 'new_string': 'b'})
        self._assert_denied('Write', {'file_path': target, 'content': 'x'})
        self._assert_denied('MultiEdit', {'file_path': target, 'edits': []})
        self._assert_denied('NotebookEdit', {'notebook_path': str(self.system / 'n.ipynb')})
        self._assert_denied('Edit', {'file_path': str(self.project / '..' / 'home' / '.local' / 'share' / 'aips' / 'system' / 'x')})

    def test_edit_family_writes_to_profile_settings_are_denied(self):
        self._assert_denied('Write', {'file_path': str(self.config / 'profile.yaml'), 'content': 'x'})
        self._assert_denied('Edit', {'file_path': str(self.config / 'profiles' / 'p.yaml')})

    def test_edit_family_writes_outside_protected_paths_are_allowed(self):
        self._assert_allowed('Edit', {'file_path': str(self.project / 'a.py'), 'old_string': 'a', 'new_string': 'b'})
        self._assert_allowed('Write', {'file_path': str(self.config / 'harness' / 'state.yaml'), 'content': 'x'})
        self._assert_allowed('Write', {'file_path': str(self.home / '.local' / 'share' / 'aips' / 'harness' / 'x'), 'content': 'x'})

    def test_bash_writes_to_protected_paths_are_denied(self):
        target = str(self.system / 'VERSION')
        self._assert_denied('Bash', {'command': f'echo 9 > {target}'})
        self._assert_denied('Bash', {'command': f'sed -i "s/0/1/" {target}'})
        self._assert_denied('Bash', {'command': f'rm -f {target}'})
        self._assert_denied('Bash', {'command': f'git -C {self.system} commit -m "fix"'})
        self._assert_denied('Bash', {'command': f'git -C {self.system} reset --hard'})
        self._assert_denied('Bash', {'command': f'cd {self.system} && git stash'})
        self._assert_denied('Bash', {'command': f'echo x | tee {self.config}/profile.yaml'})

    def test_bash_reads_and_cli_maintenance_are_allowed(self):
        self._assert_allowed('Bash', {'command': f'cat {self.system}/VERSION'})
        self._assert_allowed('Bash', {'command': f'git -C {self.system} status --short'})
        self._assert_allowed('Bash', {'command': 'aips update'})
        self._assert_allowed('Bash', {'command': 'aips install --no-configure-shell'})
        self._assert_allowed('Bash', {'command': 'aips system preflight ' + str(self.project)})
        self._assert_allowed('Bash', {'command': f'echo ok > {self.project}/out.txt'})

    def test_publication_hook_still_handles_non_protected_commands(self):
        _stdout, response = self._run_hook('Bash', {'command': 'git status'})
        self.assertEqual(response, {})


if __name__ == '__main__':
    unittest.main()

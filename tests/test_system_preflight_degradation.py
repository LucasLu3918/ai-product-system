from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIT_IDENTITY = {'GIT_AUTHOR_NAME': 'AIPS Test', 'GIT_AUTHOR_EMAIL': 'aips-fixture',
                'GIT_COMMITTER_NAME': 'AIPS Test', 'GIT_COMMITTER_EMAIL': 'aips-fixture'}


class SystemPreflightDegradationTests(unittest.TestCase):
    """Run the real CLI from a temporary installed-system copy; the bin/aips stub replaces the post-update step."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(os.path.realpath(self._tmp.name))
        self.system = base / 'system'
        self.project = base / 'project'
        self.project.mkdir()
        self.home = base / 'home'
        self.home.mkdir()
        self.config = base / 'config'
        self.bin_home = base / 'bin'
        self._copy_cli()
        self._init_git_repo()

    def _copy_cli(self):
        (self.system / 'scripts' / 'aips_cli').mkdir(parents=True)
        (self.system / 'bin').mkdir()
        shutil.copy(ROOT / 'VERSION', self.system / 'VERSION')
        shutil.copy(ROOT / 'scripts' / 'aips_cli.sh', self.system / 'scripts' / 'aips_cli.sh')
        for script in (ROOT / 'scripts' / 'aips_cli').glob('*.sh'):
            shutil.copy(script, self.system / 'scripts' / 'aips_cli' / script.name)
        stub = self.system / 'bin' / 'aips'
        stub.write_text('#!/usr/bin/env bash\necho "STUB $*"\n', encoding='utf-8')
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR)

    def _git(self, *args):
        env = {**os.environ, **GIT_IDENTITY}
        return subprocess.run(['git', '-C', str(self.system), *args], capture_output=True, text=True,
                              check=True, env=env)

    def _init_git_repo(self):
        self._git('init', '-q', '-b', 'main')
        self._git('add', '-A')
        self._git('commit', '-q', '-m', 'test: installed system snapshot')

    def _dirty(self):
        target = self.system / 'scripts' / 'aips_cli' / 'help.sh'
        target.write_text(target.read_text(encoding='utf-8') + '\n# local agent edit\n', encoding='utf-8')
        return target

    def _cli(self, *args):
        env = {**os.environ, 'HOME': str(self.home), 'XDG_CONFIG_HOME': str(self.config),
               'AIPS_BIN_HOME': str(self.bin_home)}
        return subprocess.run(['bash', str(self.system / 'scripts' / 'aips_cli.sh'), *args], capture_output=True,
                              text=True, env=env, check=False, timeout=60)

    def test_preflight_skips_update_on_local_changes_and_keeps_changes(self):
        target = self._dirty()
        head_before = self._git('rev-parse', 'HEAD').stdout.strip()
        result = self._cli('system', 'preflight', str(self.project))
        self.assertIn('skipping the automatic update', result.stderr)
        self.assertIn('continuing with', result.stderr)
        version = (self.system / 'VERSION').read_text(encoding='utf-8').strip()
        self.assertIn(version, result.stderr)
        self.assertIn(head_before, result.stderr)
        self.assertIn('git -C', result.stdout)
        self.assertIn('aips update', result.stdout)
        self.assertIn('STUB _preflight-after-update', result.stdout)
        self.assertEqual(result.returncode, 0, result.stderr)
        # Degradation never discards or commits the local change.
        self.assertIn('# local agent edit', target.read_text(encoding='utf-8'))
        self.assertTrue(self._git('status', '--porcelain').stdout.strip())
        self.assertEqual(self._git('rev-parse', 'HEAD').stdout.strip(), head_before)

    def test_top_level_preflight_command_also_degrades(self):
        self._dirty()
        result = self._cli('preflight', str(self.project))
        self.assertIn('skipping the automatic update', result.stderr)
        self.assertIn('STUB _preflight-after-update', result.stdout)

    def test_explicit_update_still_refuses_on_local_changes_without_discarding(self):
        target = self._dirty()
        result = self._cli('update')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('System repo has local changes', result.stderr)
        self.assertNotIn('STUB', result.stdout)
        self.assertIn('# local agent edit', target.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()

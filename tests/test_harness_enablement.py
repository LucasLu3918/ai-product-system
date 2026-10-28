from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import harness_enablement


class HarnessEnablementTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.config = self.root / 'config'
        self.config.mkdir(mode=0o700)
        self.system = self.root / 'system'
        self.system.mkdir()
        self.harness = self.config / 'harness'
        self.marker = self.config / 'system-dir'

    def tearDown(self):
        self.temp.cleanup()

    def valid_state(self):
        self.marker.write_text(str(self.system) + '\n')
        self.marker.chmod(0o600)
        self.harness.mkdir(mode=0o700)
        manifest = self.harness / 'installation.yaml'
        manifest.write_text(yaml.safe_dump({'version': 1, 'system': {'root': str(self.system)}, 'harness': {'enabled': True}}))
        manifest.chmod(0o600)
        return manifest

    def test_missing_state_is_off_but_partial_state_unknown(self):
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'OFF')
        self.marker.write_text(str(self.system) + '\n')
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'OFF')
        self.harness.mkdir()
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'UNKNOWN')

    def test_valid_owned_state_and_wrong_system(self):
        manifest = self.valid_state()
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'ACTIVE')
        manifest.write_text(yaml.safe_dump({'version': 1, 'system': {'root': str(self.root)}, 'harness': {'enabled': True}}))
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'UNKNOWN')

    def test_explicit_source_checkout_install_reports_active_without_auto_refresh(self):
        home = self.root / 'home'
        home.mkdir()
        env = dict(os.environ)
        env.update({
            'HOME': str(home), 'XDG_CONFIG_HOME': str(self.root / 'xdg'),
            'CODEX_HOME': str(home / '.codex'), 'AIPS_BIN_HOME': str(self.root / 'bin'),
            'OPENCODE_CONFIG_DIR': str(self.root / 'xdg' / 'opencode'),
            'AIPS_VALIDATION_PYTHON': sys.executable, 'PATH': '/usr/bin:/bin:/usr/sbin:/sbin',
        })
        command = ['bash', str(ROOT / 'bin/aips')]
        installed = subprocess.run(command + ['harness', 'install'], env=env, capture_output=True, text=True, check=False)
        self.assertEqual(installed.returncode, 0, installed.stderr)
        manifest = self.root / 'xdg' / 'aips' / 'harness' / 'installation.yaml'
        before = manifest.read_bytes()
        status = subprocess.run(command + ['harness', 'status'], env=env, capture_output=True, text=True, check=False)
        self.assertIn('Harness: ACTIVE', status.stdout)
        refresh = subprocess.run(command + ['_refresh-harness-after-update'], env=env, capture_output=True, text=True, check=False)
        self.assertEqual(refresh.returncode, 0, refresh.stderr)
        self.assertEqual(manifest.read_bytes(), before)
        self.assertIn('unknown', refresh.stderr.lower())

    def test_system_paths_preserve_spaces_and_require_absolute_records(self):
        spaced = self.root / 'system '
        spaced.mkdir()
        self.marker.write_text(str(spaced) + '\n')
        self.marker.chmod(0o600)
        self.harness.mkdir(mode=0o700)
        manifest = self.harness / 'installation.yaml'
        manifest.write_text(yaml.safe_dump({'version': 1, 'system': {'root': str(spaced)}, 'harness': {'enabled': True}}))
        manifest.chmod(0o600)
        self.assertEqual(harness_enablement.classify(self.config, spaced), 'ACTIVE')
        self.marker.write_text('.\n')
        self.assertEqual(harness_enablement.classify(self.config, spaced), 'UNKNOWN')

    def test_bad_records_are_unknown_and_unchanged(self):
        manifest = self.valid_state()
        manifest.write_text('bad: [')
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'UNKNOWN')
        self.assertEqual(manifest.read_text(), 'bad: [')
        manifest.unlink()
        manifest.symlink_to(self.marker)
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'UNKNOWN')

    def test_untrusted_or_incomplete_records_stay_unknown(self):
        manifest = self.valid_state()
        self.marker.write_text(str(self.root) + '\n')
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'UNKNOWN')
        self.marker.write_text(str(self.system) + '\n')
        self.marker.chmod(0o666)
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'UNKNOWN')
        self.marker.chmod(0o600)
        self.harness.chmod(0o777)
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'UNKNOWN')
        self.harness.chmod(0o700)
        manifest.write_bytes(b'x' * (harness_enablement.MAX_RECORD_BYTES + 1))
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'UNKNOWN')
        manifest.write_text(yaml.safe_dump({'version': 1, 'system': {'root': str(self.system)}, 'harness': {'enabled': False}}))
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'UNKNOWN')
        manifest.write_text(yaml.safe_dump({'version': 1, 'system': {'root': str(self.system)}, 'harness': {'enabled': True}}))
        self.marker.unlink()
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'ACTIVE')
        self.assertEqual(harness_enablement.classify(self.config, self.system, require_install_marker=True), 'UNKNOWN')

    def test_insecure_and_symlinked_state_is_unknown(self):
        manifest = self.valid_state()
        manifest.chmod(0o666)
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'UNKNOWN')
        manifest.chmod(0o600)
        self.marker.unlink()
        self.marker.symlink_to(manifest)
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'UNKNOWN')
        self.marker.unlink()
        self.marker.write_text(str(self.system) + '\n')
        manifest.unlink()
        self.harness.rmdir()
        self.harness.symlink_to(self.system, target_is_directory=True)
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'UNKNOWN')

    def test_disabled_state_is_off_and_is_bound_to_system(self):
        self.valid_state()
        harness_enablement.set_disabled(self.config, self.system, disabled=True)
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'OFF')
        self.assertEqual(harness_enablement.classify(self.config, self.system, require_install_marker=True), 'OFF')
        self.assertEqual(harness_enablement.classify(self.config, self.root / 'other-system'), 'UNKNOWN')
        harness_enablement.set_disabled(self.config, self.system, disabled=False)
        self.assertEqual(harness_enablement.classify(self.config, self.system), 'ACTIVE')

    def test_disabled_record_refuses_symlink_and_foreign_content(self):
        self.valid_state()
        disabled = self.harness / 'disabled'
        disabled.write_text(str(self.root / 'another-system') + '\n')
        disabled.chmod(0o600)
        with self.assertRaisesRegex(ValueError, 'another system'):
            harness_enablement.set_disabled(self.config, self.system, disabled=False)
        disabled.unlink()
        external = self.root / 'external-disable-record'
        external.write_text(str(self.system) + '\n')
        external.chmod(0o600)
        disabled.symlink_to(external)
        with self.assertRaises(OSError):
            harness_enablement.set_disabled(self.config, self.system, disabled=True)

    def test_locked_command_inherits_exclusive_lifecycle_lock(self):
        probe = (
            'import fcntl, os, sys; fd=os.open(sys.argv[1], os.O_RDWR); '
            'fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)'
        )
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/harness_enablement.py'), '--config', str(self.config),
             '--system', str(self.system), '--lock-exec', sys.executable, '-c', probe,
             str(self.config / 'harness-lifecycle.lock')],
            capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('BlockingIOError', result.stderr)


if __name__ == '__main__':
    unittest.main()

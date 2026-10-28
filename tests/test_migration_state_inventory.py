from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/migration_state_inventory.py'
CLI = ROOT / 'bin/aips'
sys.path.insert(0, str(ROOT / 'scripts'))
import migration_state_inventory


class InventoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / '.aips').mkdir()
        (self.root / '.aips' / 'human decision\nname.md').write_bytes(b'Keep this decision\n')
        (self.root / '.aips' / 'outside').symlink_to('/etc/passwd')
        subprocess.run(['git', '-C', str(self.root), 'add', '--', '.aips'], check=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_inventory_is_read_only_and_conservative(self):
        before = subprocess.check_output(['git', '-C', str(self.root), 'status', '--porcelain=v1', '-z'])
        result = subprocess.run([sys.executable, str(SCRIPT), '--project', str(self.root), '--dry-run'], capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        rows = {row['path']: row for row in data['files']}
        normal = rows['.aips/human decision\nname.md']
        self.assertEqual(normal['sha256'], hashlib.sha256(b'Keep this decision\n').hexdigest())
        self.assertEqual(normal['classification'], 'review_required')
        self.assertEqual(rows['.aips/outside']['kind'], 'symlink')
        self.assertIsNone(rows['.aips/outside']['sha256'])
        self.assertEqual(before, subprocess.check_output(['git', '-C', str(self.root), 'status', '--porcelain=v1', '-z']))

    def test_untracked_and_ignored_are_reported_without_mutation(self):
        (self.root / '.gitignore').write_text('/.aips/ignored.txt\n')
        (self.root / '.aips' / 'ignored.txt').write_text('private note')
        (self.root / '.aips' / 'untracked.txt').write_text('new note')
        before = subprocess.check_output(['git', '-C', str(self.root), 'status', '--porcelain=v1', '-z'])
        result = subprocess.run([sys.executable, str(SCRIPT), '--project', str(self.root), '--dry-run'], capture_output=True, text=True, check=True)
        rows = {row['path']: row for row in json.loads(result.stdout)['files']}
        self.assertEqual(rows['.aips/ignored.txt']['tracking'], 'ignored')
        self.assertEqual(rows['.aips/untracked.txt']['tracking'], 'untracked')
        self.assertEqual(rows['.aips/ignored.txt']['classification'], 'review_required')
        self.assertIs(rows['.aips/ignored.txt']['tracked_and_ignored'], False)
        self.assertEqual(before, subprocess.check_output(['git', '-C', str(self.root), 'status', '--porcelain=v1', '-z']))

    def test_tracked_ignored_file_is_not_treated_as_untracked(self):
        tracked = self.root / '.aips' / 'decision.md'
        tracked.write_text('durable decision')
        subprocess.run(['git', '-C', str(self.root), 'add', '--', '.aips/decision.md'], check=True)
        (self.root / '.gitignore').write_text('/.aips/decision.md\n')
        result = subprocess.run([sys.executable, str(SCRIPT), '--project', str(self.root), '--dry-run'], capture_output=True, text=True, check=True)
        rows = {row['path']: row for row in json.loads(result.stdout)['files']}
        self.assertEqual(rows['.aips/decision.md']['tracking'], 'tracked')
        self.assertIs(rows['.aips/decision.md']['tracked_and_ignored'], True)
        self.assertIs(rows['.aips/human decision\nname.md']['tracked_and_ignored'], False)

    def test_ignore_negation_and_observation_failure(self):
        tracked = self.root / '.aips' / 'decision.md'
        tracked.write_text('keep')
        subprocess.run(['git', '-C', str(self.root), 'add', '--', '.aips/decision.md'], check=True)
        (self.root / '.gitignore').write_text('/.aips/*\n!/.aips/decision.md\n')
        result = subprocess.run([sys.executable, str(SCRIPT), '--project', str(self.root), '--dry-run'], capture_output=True, text=True, check=True)
        rows = {row['path']: row for row in json.loads(result.stdout)['files']}
        self.assertIs(rows['.aips/decision.md']['tracked_and_ignored'], False)
        failed = subprocess.CompletedProcess([], 2, stdout=b'', stderr=b'failure')
        with patch.object(migration_state_inventory.subprocess, 'run', return_value=failed):
            self.assertEqual(migration_state_inventory.tracked_ignore_status(self.root, ['.aips/decision.md']), {'.aips/decision.md': None})
        with patch.object(migration_state_inventory.subprocess, 'run', side_effect=OSError('unavailable')):
            self.assertEqual(migration_state_inventory.tracked_ignore_status(self.root, ['.aips/decision.md']), {'.aips/decision.md': None})

    def test_entire_ignored_directory_is_enumerated(self):
        (self.root / '.gitignore').write_text('/.ai/\n')
        (self.root / '.ai' / 'runs').mkdir(parents=True)
        (self.root / '.ai' / 'runs' / 'record.txt').write_text('human context')
        result = subprocess.run([sys.executable, str(SCRIPT), '--project', str(self.root), '--dry-run'], capture_output=True, text=True, check=True)
        rows = {row['path']: row for row in json.loads(result.stdout)['files']}
        self.assertEqual(rows['.ai/runs/record.txt']['tracking'], 'ignored')
        self.assertEqual(rows['.ai/runs/record.txt']['classification'], 'review_required')

    def test_missing_and_replaced_parent_stay_unavailable(self):
        nested = self.root / '.aips' / 'nested'
        nested.mkdir()
        (nested / 'item').write_text('content')
        subprocess.run(['git', '-C', str(self.root), 'add', '--', '.aips/nested/item'], check=True)
        (nested / 'item').unlink()
        nested.rmdir()
        nested.symlink_to('/tmp', target_is_directory=True)
        result = subprocess.run([sys.executable, str(SCRIPT), '--project', str(self.root), '--dry-run'], capture_output=True, text=True, check=True)
        rows = {row['path']: row for row in json.loads(result.stdout)['files']}
        self.assertEqual(rows['.aips/nested/item']['kind'], 'symlink')
        self.assertIsNone(rows['.aips/nested/item']['sha256'])

    def test_deleted_tracked_file_is_reported_unknown(self):
        (self.root / '.aips' / 'human decision\nname.md').unlink()
        result = subprocess.run([sys.executable, str(SCRIPT), '--project', str(self.root), '--dry-run'], capture_output=True, text=True, check=True)
        rows = {row['path']: row for row in json.loads(result.stdout)['files']}
        self.assertEqual(rows['.aips/human decision\nname.md']['kind'], 'unavailable')
        self.assertIsNone(rows['.aips/human decision\nname.md']['sha256'])

    def test_cli_requires_explicit_dry_run(self):
        command = [str(CLI), 'migrate-state', '--project', str(self.root)]
        refused = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertNotEqual(refused.returncode, 0)
        accepted = subprocess.run(command + ['--dry-run'], capture_output=True, text=True, check=True)
        self.assertEqual(len(json.loads(accepted.stdout)['files']), 2)

    def test_non_repository_fails_without_creating_files(self):
        with tempfile.TemporaryDirectory() as directory:
            other = Path(directory)
            result = subprocess.run([sys.executable, str(SCRIPT), '--project', str(other), '--dry-run'], capture_output=True, text=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(other.iterdir()), [])


if __name__ == '__main__':
    unittest.main()

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/migration_state_inventory.py'


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
        result = subprocess.run([sys.executable, str(SCRIPT), '--project', str(self.root)], capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        rows = {row['path']: row for row in data['files']}
        normal = rows['.aips/human decision\nname.md']
        self.assertEqual(normal['sha256'], hashlib.sha256(b'Keep this decision\n').hexdigest())
        self.assertEqual(normal['classification'], 'review_required')
        self.assertEqual(rows['.aips/outside']['kind'], 'symlink')
        self.assertIsNone(rows['.aips/outside']['sha256'])
        self.assertEqual(before, subprocess.check_output(['git', '-C', str(self.root), 'status', '--porcelain=v1', '-z']))

    def test_missing_and_replaced_parent_stay_unavailable(self):
        nested = self.root / '.aips' / 'nested'
        nested.mkdir()
        (nested / 'item').write_text('content')
        subprocess.run(['git', '-C', str(self.root), 'add', '--', '.aips/nested/item'], check=True)
        (nested / 'item').unlink()
        nested.rmdir()
        nested.symlink_to('/tmp', target_is_directory=True)
        result = subprocess.run([sys.executable, str(SCRIPT), '--project', str(self.root)], capture_output=True, text=True, check=True)
        rows = {row['path']: row for row in json.loads(result.stdout)['files']}
        self.assertEqual(rows['.aips/nested/item']['kind'], 'symlink')
        self.assertIsNone(rows['.aips/nested/item']['sha256'])

    def test_deleted_tracked_file_is_reported_unknown(self):
        (self.root / '.aips' / 'human decision\nname.md').unlink()
        result = subprocess.run([sys.executable, str(SCRIPT), '--project', str(self.root)], capture_output=True, text=True, check=True)
        rows = {row['path']: row for row in json.loads(result.stdout)['files']}
        self.assertEqual(rows['.aips/human decision\nname.md']['kind'], 'unavailable')
        self.assertIsNone(rows['.aips/human decision\nname.md']['sha256'])

    def test_non_repository_fails_without_creating_files(self):
        with tempfile.TemporaryDirectory() as directory:
            other = Path(directory)
            result = subprocess.run([sys.executable, str(SCRIPT), '--project', str(other)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(other.iterdir()), [])


if __name__ == '__main__':
    unittest.main()

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import claude_permission_denied as observer


class PermissionDeniedObserverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / "diagnostics"
        self.log = self.directory / "claude-permission-denied.jsonl"
        self.now = datetime(2026, 11, 1, 12, tzinfo=UTC)
        self.payload = {
            "hook_event_name": "PermissionDenied",
            "tool_name": "Bash",
            "tool_input": {"command": "private command text"},
            "reason": "Claude Auto Mode: Self-Modification",
            "tool_use_id": "tool-use-secret-id",
            "session_id": "session-secret-id",
        }

    def test_records_only_fixed_fields_and_hashes_with_private_permissions(self) -> None:
        self.assertTrue(observer.record(self.payload, path=self.log, now=self.now))
        record = json.loads(self.log.read_text(encoding="utf-8"))

        self.assertEqual(record["source"], "claude_auto_mode")
        self.assertEqual(record["reason_class"], "self_modification")
        self.assertEqual(record["tool_name"], "Bash")
        self.assertRegex(record["tool_input_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(set(record), {
            "version", "timestamp", "event", "source", "reason_class", "tool_name",
            "reason_sha256", "tool_input_sha256", "tool_use_id_sha256", "session_id_sha256",
        })
        raw = self.log.read_text(encoding="utf-8")
        for secret in ("private command text", "Self-Modification", "tool-use-secret-id", "session-secret-id"):
            self.assertNotIn(secret, raw)
        self.assertEqual(self.directory.stat().st_mode & 0o777, 0o700)
        self.assertEqual(self.log.stat().st_mode & 0o777, 0o600)

    def test_wrong_event_is_ignored_and_uninstall_can_leave_user_events_untouched(self) -> None:
        payload = {**self.payload, "hook_event_name": "PreToolUse"}
        self.assertFalse(observer.record(payload, path=self.log, now=self.now))
        self.assertFalse(self.log.exists())

    def test_retention_enforces_thirty_days_and_one_thousand_records(self) -> None:
        self.directory.mkdir(mode=0o700)
        old = {
            "version": 1, "timestamp": (self.now - timedelta(days=31)).isoformat(),
            "event": "PermissionDenied", "source": "claude_auto_mode", "reason_class": "other",
            "tool_name": "Bash", "reason_sha256": "a" * 64, "tool_input_sha256": "b" * 64,
            "tool_use_id_sha256": "c" * 64, "session_id_sha256": "d" * 64,
        }
        recent = {**old, "timestamp": (self.now - timedelta(days=1)).isoformat()}
        self.log.write_text("\n".join(json.dumps(recent) for _ in range(1000)) + "\n", encoding="utf-8")
        os.chmod(self.log, 0o600)
        with self.log.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(old) + "\n")

        self.assertTrue(observer.record(self.payload, path=self.log, now=self.now))
        records = [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(records), 1000)
        self.assertTrue(all((self.now - datetime.fromisoformat(row["timestamp"])).days <= 30 for row in records))

    def test_symlink_log_is_not_followed_and_observer_emits_no_decision(self) -> None:
        target = Path(self.temp.name) / "outside.jsonl"
        target.write_text("user data\n", encoding="utf-8")
        self.directory.mkdir(mode=0o700)
        self.log.symlink_to(target)
        self.assertFalse(observer.record(self.payload, path=self.log, now=self.now))
        self.assertEqual(target.read_text(encoding="utf-8"), "user data\n")


if __name__ == "__main__":
    unittest.main()

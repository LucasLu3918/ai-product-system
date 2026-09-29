#!/usr/bin/env python3
"""Deterministic lifecycle evidence for the read-only Run Projection contract."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.run_projection import _load_events, _project_run


class DashboardLifecycle(unittest.TestCase):
    def test_parallel_projection_cases(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            checkpoint = root / "CHECKPOINT.yaml"
            checkpoint.write_text(
                yaml.safe_dump(
                    {
                        "version": 3,
                        "run_id": "run-waiting",
                        "protocol": "product-delivery",
                        "status": "WAITING",
                        "current_step": "core-change-approval",
                        "execution": {"task_id": "backend-api", "role": "backend", "runtime": "codex", "isolation_id": "api-1"},
                        "gate": {"id": "core-change-approval", "status": "WAITING"},
                        "workspace": {"repository_id": "repo", "workspace_id": "ws", "revision": "abc"},
                        "updated_at": "2026-09-23T00:00:00Z",
                    }
                ),
                encoding="utf-8",
            )
            (root / "EVENTS.jsonl").write_text(
                json.dumps({"sequence": 1, "timestamp": "2026-09-23T00:00:00Z", "event": "waiting", "status": "INFO"})
                + "\n"
                + '{"sequence": 2, "event": "partial"',
                encoding="utf-8",
            )
            ownership = root / "TASK_OWNERSHIP.yaml"
            ownership.write_text(
                yaml.safe_dump(
                    {
                        "version": 1,
                        "task_id": "backend-api",
                        "execution_id": "exec-1",
                        "status": "ACTIVE",
                        "change_boundary": ["apps/backend"],
                        "write_set": ["apps/backend/**"],
                        "dependencies": ["prepare"],
                        "workspace_id": "ws",
                        "branch": "feature/backend",
                        "heartbeat_at": "2026-09-23T00:00:00Z",
                        "expires_at": "2026-09-23T00:05:00Z",
                        "observed_dirty_files": ["apps/backend/api.py"],
                        "resource_authorization": {"enforcement_capability": "ADVISORY"},
                    }
                ),
                encoding="utf-8",
            )
            original_ownership = ownership.read_bytes()
            projected = _project_run(checkpoint, "EPHEMERAL", None)
            self.assertEqual(projected["display_column"], "WAITING: core-change-approval")
            self.assertEqual(projected["ownership"]["owner_execution_id"], "exec-1")
            self.assertEqual(projected["ownership"]["change_boundary"], ["apps/backend"])
            self.assertEqual(projected["ownership"]["dirty_files"], ["apps/backend/api.py"])
            self.assertEqual(projected["ownership"]["enforcement_capability"], "ADVISORY")
            self.assertEqual(ownership.read_bytes(), original_ownership)
            self.assertEqual(projected["event_count"], 1)
            self.assertNotIn("prompt", projected)
            self.assertNotIn("reasoning", projected)
            self.assertEqual(_load_events(root / "EVENTS.jsonl")[0]["event"], "waiting")


if __name__ == "__main__":
    unittest.main()

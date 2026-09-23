#!/usr/bin/env python3
"""Deterministic lifecycle evidence for the read-only Run Projection contract."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import yaml

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
            projected = _project_run(checkpoint, "EPHEMERAL", None)
            self.assertEqual(projected["display_column"], "WAITING: core-change-approval")
            self.assertEqual(projected["event_count"], 1)
            self.assertNotIn("prompt", projected)
            self.assertNotIn("reasoning", projected)
            self.assertEqual(_load_events(root / "EVENTS.jsonl")[0]["event"], "waiting")


if __name__ == "__main__":
    unittest.main()

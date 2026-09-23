from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

from scripts.run_projection import _display_column, _load_events, _project_run, build_projection


class RunProjectionTests(unittest.TestCase):
    def test_display_columns_are_projection_values(self) -> None:
        self.assertEqual(_display_column("WAITING", {"id": "core", "status": "WAITING"}, "step"), "WAITING: core")
        self.assertEqual(_display_column("ACTIVE", {}, "janitor-validation"), "VALIDATION")
        self.assertEqual(_display_column("COMPLETE", {}, "done"), "COMPLETE")

    def test_truncated_jsonl_keeps_valid_events_and_omits_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            events = Path(td) / "EVENTS.jsonl"
            events.write_text(
                json.dumps({"sequence": 1, "timestamp": "t1", "event": "safe", "status": "INFO", "artifact": "/secret/path"})
                + "\n"
                + '{"sequence": 2, "event": "unfinished"',
                encoding="utf-8",
            )
            result = _load_events(events)
            self.assertEqual(len(result), 1)
            self.assertTrue(result[0]["has_evidence"])
            self.assertNotIn("artifact", result[0])

    def test_legacy_checkpoint_projects_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            checkpoint = Path(td) / "CHECKPOINT.yaml"
            checkpoint.write_text(
                yaml.safe_dump(
                    {
                        "version": 2,
                        "run_id": "run-1",
                        "protocol": "test",
                        "status": "ACTIVE",
                        "current_step": "implementation",
                        "workspace": {"repository_id": "repo", "workspace_id": "ws", "revision": "abc"},
                    }
                ),
                encoding="utf-8",
            )
            result = _project_run(checkpoint, "EPHEMERAL", None)
            assert result is not None
            self.assertEqual(result["run_id"], "run-1")
            self.assertEqual(result["checkpoint_version"], 2)
            self.assertEqual(result["workspace"]["health"], "UNKNOWN")
            self.assertEqual(result["execution"]["task_id"], "UNKNOWN")

    def test_same_projection_has_same_fingerprint(self) -> None:
        with patch("scripts.run_projection._workspace_catalog", return_value={}), patch(
            "scripts.run_projection._run_candidates", return_value=[]
        ):
            first = build_projection(".")
            second = build_projection(".")
        self.assertEqual(first["snapshot_fingerprint"], second["snapshot_fingerprint"])
        self.assertEqual(first["runs"], second["runs"])


if __name__ == "__main__":
    unittest.main()

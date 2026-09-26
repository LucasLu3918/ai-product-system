from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "eval_interop.py"
FIXTURES = ROOT / "tests" / "fixtures" / "eval_interop"
sys.path.insert(0, str(ROOT / "scripts"))
from agent_eval import fingerprint


class EvalInteropLifecycleTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=ROOT, capture_output=True, text=True, check=False)

    def test_import_verify_and_stale_provenance_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "external.yaml"
            imported = self.run_cli("import-promptfoo", "--config", str(FIXTURES / "promptfoo.config.yaml"), "--results", str(FIXTURES / "promptfoo.results.jsonl"), "--output", str(out))
            self.assertEqual(imported.returncode, 0, imported.stderr)
            verified = self.run_cli("verify-evidence", "--evidence", str(out), "--config", str(FIXTURES / "promptfoo.config.yaml"), "--results", str(FIXTURES / "promptfoo.results.jsonl"))
            self.assertEqual(verified.returncode, 0, verified.stderr)
            stale = Path(temp) / "changed.jsonl"
            stale.write_text((FIXTURES / "promptfoo.results.jsonl").read_text() + "\n", encoding="utf-8")
            rejected = self.run_cli("verify-evidence", "--evidence", str(out), "--config", str(FIXTURES / "promptfoo.config.yaml"), "--results", str(stale))
            self.assertEqual(rejected.returncode, 2)
            self.assertNotIn("blue", rejected.stderr)

    def test_confirmed_finding_promotes_to_canonical_case_and_scores(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "regression.yaml"
            promoted = self.run_cli("promote-finding", "--finding", str(FIXTURES / "finding-confirmed.yaml"), "--output", str(out))
            self.assertEqual(promoted.returncode, 0, promoted.stderr)
            result = Path(temp) / "result.yaml"
            case_doc = out.read_text(encoding="utf-8")
            import yaml
            case = yaml.safe_load(case_doc)
            result.write_text(yaml.safe_dump({
                "version": 1,
                "case_id": case["id"],
                "scenario_id": case["scenario_id"],
                "case_fingerprint": fingerprint(case),
                "execution": {"provider": "offline", "model": "fixture", "runtime": "local", "executed_at": "2026-09-26T14:00:00+08:00"},
                "response": {"disclosure_detected": False},
            }, sort_keys=False), encoding="utf-8")
            scored = subprocess.run([sys.executable, str(ROOT / "scripts/agent_eval.py"), "score", "--case", str(out), "--result", str(result), "--format", "json"], cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(scored.returncode, 0, scored.stdout + scored.stderr)


if __name__ == "__main__":
    unittest.main()

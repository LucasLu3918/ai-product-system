from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import eval_interop as interop

FIXTURES = ROOT / "tests" / "fixtures" / "eval_interop"


class SafeInputTests(unittest.TestCase):
    def test_rejects_duplicate_keys_aliases_tags_and_limits(self) -> None:
        for source in (
            "a: 1\na: 2\n",
            "a: &shared [1]\nb: *shared\n",
            "a: !!python/object/apply:os.system ['echo unsafe']\n",
            "a: " + "x" * (interop.MAX_BYTES + 1),
        ):
            with self.subTest(source=source[:20]), self.assertRaises(interop.InputError):
                interop.parse_yaml_bytes(source.encode())

    def test_rejects_secret_and_private_reasoning_without_echoing_content(self) -> None:
        for doc in ({"response": {"analysis": "private"}}, {"vars": {"api_key": "not-a-real-key"}}, {"response": "token=abcdefghijk"}):
            with self.subTest(doc=doc), self.assertRaises(interop.InputError) as caught:
                interop._validate_sensitive(doc)
            self.assertNotIn("private", str(caught.exception).replace("private reasoning", ""))

    def test_rejects_unknown_and_executable_promptfoo_assertions(self) -> None:
        base = {
            "prompts": ["hello"],
            "providers": ["openai:chat:gpt-4o-mini"],
            "tests": [{"vars": {}, "assert": [{"type": "javascript", "value": "return true"}]}],
        }
        with self.assertRaises(interop.InputError):
            interop._parse_promptfoo_config(base)
        base["unknown"] = "file://provider.js"
        with self.assertRaises(interop.InputError):
            interop._parse_promptfoo_config(base)


class InteropContractTests(unittest.TestCase):
    def test_promptfoo_import_is_fingerprinted_and_advisory(self) -> None:
        evidence = interop.import_promptfoo(FIXTURES / "promptfoo.config.yaml", FIXTURES / "promptfoo.results.jsonl")
        self.assertEqual(evidence["status"], "SIGNAL")
        self.assertEqual(evidence["gate_eligibility"], "CANONICAL_REGRESSION_REQUIRED")
        self.assertTrue(evidence["fingerprint"].startswith("sha256:"))
        self.assertEqual(interop.verify_evidence.__name__, "verify_evidence")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "evidence.yaml"
            interop.write_yaml(path, evidence)
            verified = interop.verify_evidence(path, FIXTURES / "promptfoo.config.yaml", FIXTURES / "promptfoo.results.jsonl")
            self.assertEqual(verified["status"], "VERIFIED")
            data = yaml.safe_load(path.read_text())
            data["status"] = "PASS"
            path.write_text(yaml.safe_dump(data))
            with self.assertRaises(interop.InputError):
                interop.verify_evidence(path)

    def test_promptfoo_export_requires_explicit_builtin_provider(self) -> None:
        case = yaml.safe_load((ROOT / "tests/agent_eval/cases/001-product-creation.yaml").read_text())
        with self.assertRaises(interop.InputError):
            interop.export_promptfoo(case, "file://untrusted/provider.py")
        config = interop.export_promptfoo(case, "openai:chat:gpt-4o-mini")
        self.assertEqual(config["providers"], ["openai:chat:gpt-4o-mini"])
        self.assertEqual(config["tests"][0]["vars"], case["input"]["context"])

    def test_pyrit_is_review_only_and_finding_requires_human_confirmation(self) -> None:
        evidence = interop.import_pyrit_bridge(FIXTURES / "pyrit.bridge.yaml")
        self.assertEqual(evidence["status"], "REVIEW")
        self.assertEqual(evidence["gate_eligibility"], "ADVISORY_ONLY")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "pyrit-evidence.yaml"
            interop.write_yaml(path, evidence)
            self.assertEqual(interop.verify_evidence(path, bridge_path=FIXTURES / "pyrit.bridge.yaml")["status"], "VERIFIED")
        finding = yaml.safe_load((FIXTURES / "finding-confirmed.yaml").read_text())
        case = interop.promote_finding(finding)
        self.assertEqual(case["scenario_id"], "180")
        finding["review"]["status"] = "PENDING"
        with self.assertRaises(interop.InputError):
            interop.promote_finding(finding)
        finding["review"]["status"] = "APPROVED"
        finding["state"] = "DISCOVERED"
        with self.assertRaises(interop.InputError):
            interop.promote_finding(finding)

    def test_risk_profile_escalates_to_strongest_selected_area(self) -> None:
        selected = interop.choose_profile("ordinary", ["prompt_system", "mcp_tool_permissions"], True)
        self.assertEqual(selected["profile"], "mcp_tool_permissions")
        self.assertEqual(selected["optional_deep_scan"]["authority"], "ADVISORY_ONLY")
        self.assertTrue(selected["human_authority_preserved"])


if __name__ == "__main__":
    unittest.main()

"""Regression evidence for plan17 publication and validation failures."""

from __future__ import annotations

import itertools
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import documentation_placement
from ci_validation_plan import validation_capabilities
from content_safety import _luhn, git_diff_payload, safe_emit
from dependency_review_evidence import capture, compare
from github_workflow_validation import validate_workflows
from publish_preflight import summarize_checks
from publish_preflight_policy import documentation_impact
from runtime_context import resolve_python, validation_environment
from validation.registry import ERROR_AGGREGATION_ORDER, VALIDATORS, load_validators


def main() -> int:
    numeric_blob = next(str(value) for value in range(1000000, 1000100) if _luhn(str(value) + "100644"))
    metadata = f"index abcdef0..{numeric_blob} 100644"
    assert safe_emit(sink="source_artifact", payload=metadata)["decision"] == "BLOCK"
    assert safe_emit(sink="source_artifact", payload=git_diff_payload(metadata + "\n+ordinary content"))["decision"] == "ALLOW"
    card = "4" + "1" * 15
    for prefix in ("+", "-", " ", "+index ", "unexpected-header "):
        result = safe_emit(sink="source_artifact", payload=git_diff_payload(metadata + "\n" + prefix + card))
        assert result["decision"] == "BLOCK", prefix
    assert safe_emit(sink="source_artifact", payload=git_diff_payload("+++ b/" + card))["decision"] == "BLOCK"

    for invalid in (None, {}, {"version": 1}, {"version": 1, "needs_browser": "false"}):
        assert all(validation_capabilities(invalid).values())
    for browser, openapi in itertools.product((False, True), repeat=2):
        caps = validation_capabilities({"version": 1, "needs_node": False, "needs_browser": browser, "needs_openapi": openapi})
        imported = []
        with patch("validation.registry.importlib.import_module", side_effect=lambda name, target=imported: target.append(name)):
            selected = load_validators(lambda *_: None, needs_browser=caps["browser"])
        assert set(ERROR_AGGREGATION_ORDER) <= set(selected), "capabilities must not skip mandatory error aggregators"
        assert all((spec.module in selected) == (not spec.requires_browser or browser) for spec in VALIDATORS)
        assert caps["openapi"] == openapi

    env = validation_environment(sys.executable, {"PATH": "/usr/bin:/bin", "HOME": "/identity",
        "GH_CONFIG_DIR": "/auth", "AIPS_CI_VALIDATION_PLAN": "/injected", "PYTHONPATH": "/shim",
        "AIPS_VALIDATION_VENV": "/foreign", "PYTHONHOME": "/foreign"})
    assert env["HOME"] == "/identity" and env["GH_CONFIG_DIR"] == "/auth"
    assert "PYTHONPATH" not in env and "AIPS_CI_VALIDATION_PLAN" not in env and "AIPS_VALIDATION_VENV" not in env
    selected, _ = resolve_python(ROOT, ROOT, require_full=True, env={"AIPS_VALIDATION_PYTHON": "/missing-explicit-python"})
    assert selected is None, "explicit invalid executor must never fall back to an installed venv"
    child = subprocess.run(["python3", "-c", "import sys; print(sys.prefix)"], env=validation_environment(sys.executable), capture_output=True, text=True, check=True)
    assert child.stdout.strip() == sys.prefix

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".github/workflows").mkdir(parents=True)
        callee = {"on": {"workflow_call": {}}, "permissions": {"contents": "read", "pull-requests": "read"}, "jobs": {"verify": {"runs-on": "ubuntu-24.04", "steps": []}}}
        caller = {"on": {"pull_request": {}}, "permissions": {"contents": "read"}, "jobs": {"call": {"uses": "./.github/workflows/callee.yml"}}}
        (root / ".github/workflows/callee.yml").write_text(yaml.safe_dump(callee))
        caller_path = root / ".github/workflows/caller.yml"
        caller_path.write_text(yaml.safe_dump(caller))
        assert any("cannot elevate" in error for error in validate_workflows(root))
        caller["jobs"]["call"]["permissions"] = callee["permissions"]
        caller_path.write_text(yaml.safe_dump(caller))
        assert not validate_workflows(root)
        caller["jobs"]["call"]["continue-on-error"] = True
        caller_path.write_text(yaml.safe_dump(caller))
        assert any("unsupported reusable caller" in error for error in validate_workflows(root))
        del caller["jobs"]["call"]["continue-on-error"]
        caller["jobs"]["other"] = {"runs-on": "ubuntu-24.04", "steps": [], "needs": "call"}
        caller_path.write_text(yaml.safe_dump(caller))
        assert not validate_workflows(root)
        caller["jobs"]["other"]["needs"] = ["call"]
        caller_path.write_text(yaml.safe_dump(caller))
        assert not validate_workflows(root)

        (root / "config").mkdir()
        (root / "config/documentation-sync.yaml").write_text(yaml.safe_dump({"rules": [{"id": "chain", "triggers": ["a.py"], "human_docs": ["a.md"], "agent_docs": []}]}))
        (root / "config/documentation-placement.yaml").write_text(yaml.safe_dump({"placement_rules": [{"id": "recursive", "triggers": ["a.md"], "placements": {"b.md": {}}}, {"id": "cycle", "triggers": ["b.md"], "placements": {"a.md": {}}}]}))
        impact = documentation_impact(["a.py"], root)
        assert impact["required_additions"] == ["a.md", "b.md"]
        assert "placement:recursive" in impact["required_by"]["b.md"]
        assert documentation_impact(impact["closure"], root)["complete"]
        (root / "guide.md").write_text("# Guide\n## First\nfirst change\n## Second\nsecond change\n## Unrelated\nwrong place\n")
        rules = {"placement_rules": [{"id": "first", "triggers": ["a.py"], "placements": {"guide.md": ["First"]}},
                                     {"id": "second", "triggers": ["b.py"], "placements": {"guide.md": ["Second"]}}]}
        with patch.object(documentation_placement, "ROOT", root), patch.object(documentation_placement, "changed_files", return_value=["a.py", "b.py", "guide.md"]), patch.object(documentation_placement, "behavior_trigger_patterns", return_value=[]):
            with patch.object(documentation_placement, "added_line_numbers", return_value=[3, 5]):
                assert not documentation_placement.placement_errors(rules, "base")
            with patch.object(documentation_placement, "added_line_numbers", return_value=[3]):
                assert any("no added content" in error for error in documentation_placement.placement_errors(rules, "base"))
            with patch.object(documentation_placement, "added_line_numbers", return_value=[3, 5, 7]):
                assert any("outside allowed" in error for error in documentation_placement.placement_errors(rules, "base"))

    checks = summarize_checks({"statusCheckRollup": [{"name": "repository", "workflowName": "validate", "startedAt": "1", "conclusion": "CANCELLED"}, {"name": "repository", "workflowName": "validate", "startedAt": "2", "conclusion": "SUCCESS"}]}, ["repository"])
    assert checks["status"] == "PASS" and checks["superseded_checks"][0]["status"] == "SUPERSEDED"
    assert summarize_checks({"statusCheckRollup": [{"name": "repository", "conclusion": "CANCELLED"}]}, ["repository"])["status"] == "INCOMPLETE"
    inputs = {"CANDIDATE_HEAD": "a" * 40, "CANDIDATE_BASE": "b" * 40, "REVIEW_OUTCOME": "success",
              **{key: "[]" for key in ("DEPENDENCY_CHANGES", "VULNERABLE_CHANGES", "INVALID_LICENSE_CHANGES", "DENIED_CHANGES")}}
    first, second = capture(inputs), capture({**inputs, "IS_SHADOW": "true"})
    assert compare(first, second) == "PARITY"
    assert compare(first, {**second, "findings_sha256": "tampered"}) == "UNKNOWN"
    assert compare(first, {**second, "variant": []}) == "UNKNOWN"
    ordered = capture({**inputs, "DEPENDENCY_CHANGES": '[{"name":"a"},{"name":"b"}]'})
    reversed_order = capture({**inputs, "IS_SHADOW": "true", "DEPENDENCY_CHANGES": '[{"name":"b"},{"name":"a"}]'})
    assert compare(ordered, reversed_order) == "PARITY"
    assert compare(first, capture({**inputs, "IS_SHADOW": "true", "DEPENDENCY_CHANGES": ""})) == "UNKNOWN"
    assert compare(first, capture({**inputs, "IS_SHADOW": "true", "VULNERABLE_CHANGES": json.dumps([{"severity": "high"}])})) == "MISMATCH"
    assert compare(first, capture({**inputs, "IS_SHADOW": "true", "CANDIDATE_HEAD": "c" * 40})) == "UNKNOWN"
    assert not first["promotion_authorized"]
    assert not validate_workflows(ROOT), validate_workflows(ROOT)
    print("RELIABILITY HARDENING LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
from argparse import Namespace
from unittest.mock import Mock
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_module():
    spec = importlib.util.spec_from_file_location("publish_preflight", ROOT / "scripts/publish_preflight.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    publish = load_module()

    change_class, warning = publish.resolve_change_class("auto", "bug,aips:core-change")
    assert change_class == "core" and warning is None
    explicit, warning = publish.resolve_change_class("large", "aips:core-change")
    assert explicit == "large" and warning

    impact = publish.documentation_impact(["bin/aips"])
    for required in (
        "docs/human/USER_GUIDE.md",
        "docs/human/TECHNOLOGY_GUIDE.md",
    ):
        assert required in impact["required_additions"]
    assert "docs/human/INSTALLATION.md" not in impact["required_additions"]
    assert "docs/human/GETTING_STARTED.md" not in impact["required_additions"]
    assert not impact["complete"]

    complete_files = ["bin/aips", *impact["required_additions"]]
    assert publish.documentation_impact(complete_files)["complete"]

    test_impact = publish.documentation_impact(["tests/validation/ears_requirement_contracts.py"])
    assert set(test_impact["required_additions"]) == {
        "docs/human/CONFORMANCE.md",
        "docs/human/TECHNOLOGY_GUIDE.md",
        "orchestration/CONFORMANCE.md",
    }
    source_impact = publish.documentation_impact(["scripts/requirements_traceability.py"])
    assert "orchestration/REQUIREMENT_CLARIFICATION.md" in source_impact["required_additions"]
    assert "orchestration/PLANNING_PACKAGE.md" in source_impact["required_additions"]
    assert not source_impact["complete"]

    commits = "a" * 40 + "\n" + "b" * 40
    rejected_email = "private.address" + chr(64) + "example.com"
    def fake_git(*args: str) -> str:
        if args[:2] == ("rev-list", "--reverse"):
            return commits
        if args[:2] == ("show", "-s"):
            if args[-1].startswith("a"):
                return "123+codex" + chr(64) + "users.noreply.github.com\x00noreply" + chr(64) + "github.com"
            return rejected_email + "\x00noreply" + chr(64) + "github.com"
        raise AssertionError(args)

    with patch.object(publish, "git", side_effect=fake_git):
        identity = publish.commit_identity_plan("base", "head")
    assert identity["status"] == "BLOCKED"
    assert identity["findings"] == [{"commit": "b" * 12, "field": "author", "reason": "email_not_approved"}]
    assert rejected_email not in repr(identity)

    profile = {"matrix_required_change_classes": ["large", "core"], "matrix_required_paths": []}
    assert publish.matrix_required(profile, ["docs/README.md"], "core")
    assert not publish.matrix_required(profile, ["docs/README.md"], "standard")

    with patch.object(publish, "resolve_commit", side_effect=["base-sha", "head-sha"]), patch.object(
        publish, "worktree_changed_files", return_value=["bin/aips", "untracked-note.md"]
    ):
        preview = publish.preview_candidate(Namespace(
            base="main", head="HEAD", change_class="core", labels="aips:core-change",
            profile=ROOT / "config/integration-gate.yaml", matrix=None,
        ))
    assert preview["preview"] is True
    assert preview["candidate"]["changed_files"] == [
        ".aips/review/CORE_CHANGE_TEST_MATRIX.yaml", "bin/aips", "untracked-note.md"
    ]
    assert preview["matrix"]["required"] is True
    assert "placement:publication-cli" in preview["documentation"]["required_by"]["docs/human/USER_GUIDE.md"]

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        matrix_path = root / ".aips" / "review" / "CORE_CHANGE_TEST_MATRIX.yaml"
        matrix_path.parent.mkdir(parents=True)
        matrix_path.write_text(
            "version: 1\ncandidate:\n  base_sha: old\n  changed_files_hash: old\nactual_diff_reconciled: true\nblockers: []\nstatus: READY\n",
            encoding="utf-8",
        )
        with patch.object(publish, "ROOT", root), patch.object(publish, "CANONICAL_MATRIX", matrix_path), patch.object(
            publish, "resolve_commit", side_effect=["base-sha", "head-sha"]
        ), patch.object(publish, "worktree_changed_files", return_value=["src/feature.py"]):
            synced = publish.sync_matrix_binding("main", "HEAD", matrix_path)
        bound = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
        assert synced["changed_files"] == [".aips/review/CORE_CHANGE_TEST_MATRIX.yaml", "src/feature.py"]
        assert bound["candidate"]["base_sha"] == "base-sha"
        assert bound["candidate"]["changed_files_hash"] == publish.canonical_hash(synced["changed_files"])
        assert bound["status"] == "DRAFT"
        assert bound["actual_diff_reconciled"] is False
        assert bound["blockers"]

    environment = publish.environment_status()
    assert environment["status"] in {"READY", "ENVIRONMENT_BLOCKED"}
    assert isinstance(environment["blockers"], list)
    assert isinstance(environment["diagnostics"], list)
    denied_socket = Mock()
    denied_socket.bind.side_effect = PermissionError("sandbox denied bind")
    denied_browser = {"status": "BROWSER_LAUNCH_FAILED", "provider": "system", "path": "/browser", "stderr": "launch denied"}
    with patch.object(publish.socket, "socket", return_value=denied_socket), patch.object(
        publish, "discover_browser", return_value={"provider": "system", "path": "/browser"}
    ), patch.object(publish, "probe_browser", return_value=denied_browser):
        blocked_environment = publish.environment_status()
    assert blocked_environment["status"] == "ENVIRONMENT_BLOCKED"
    assert {item["check"] for item in blocked_environment["diagnostics"]} == {"localhost_bind", "browser_probe"}
    assert all(item["next_step"] for item in blocked_environment["diagnostics"])
    missing_browser = publish.probe_browser(None, provider="managed")
    assert missing_browser["status"] == "BROWSER_NOT_FOUND"
    assert missing_browser["provider"] == "managed"

    source = (ROOT / "scripts/publish_preflight.py").read_text(encoding="utf-8")
    for contract in (
        "AIPS_DOCS_DIFF_BASE",
        "CORE_CHANGE_TEST_MATRIX.yaml",
        "ENVIRONMENT_BLOCKED",
        "probe_browser",
        "changed_files_hash",
        "RESET_EQUIVALENT_TREE",
        "refresh-intelligence",
    ):
        assert contract in source
    browser_source = (ROOT / "scripts/browser_runtime.py").read_text(encoding="utf-8")
    for contract in ("BROWSER_LAUNCH_FAILED", "sync_playwright", "AIPS_BROWSER_PROVIDER"):
        assert contract in browser_source

    print("PUBLISH PREFLIGHT LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

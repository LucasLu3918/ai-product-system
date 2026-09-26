from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
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
    from integration_gate import GateError, matrix_fingerprint

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
    assert publish.pr_creation_plan("core")["gh_create_args"] == ["gh", "pr", "create", "--label", "aips:core-change"]
    assert publish.pr_creation_plan("core")["label_timing"] == "initial_create_request"
    assert publish.pr_creation_plan("large")["required_label"] == "aips:large-change"
    assert publish.pr_creation_plan("standard")["required_label"] is None

    with patch.object(publish, "resolve_commit", side_effect=["base-sha", "head-sha"]), patch.object(
        publish, "worktree_changed_files", return_value=["bin/aips", "untracked-note.md"]
    ), patch.object(publish, "preview_content_safety", return_value={"status": "PASS", "findings": [], "unscannable_count": 0, "blockers": []}), patch.object(
        publish, "configured_identity_plan", return_value={"status": "PASS", "configured": True, "findings": [], "blockers": []}
    ), patch.object(
        publish.documentation_placement, "audit_worktree", return_value=["guide.md: outside allowed H2"]
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
    assert preview["content_safety"]["status"] == "PASS" and preview["git_identity"]["status"] == "PASS"
    assert "placement:publication-cli" in preview["documentation"]["required_by"]["docs/human/USER_GUIDE.md"]
    assert preview["documentation_placement"]["status"] == "BLOCKED"
    assert "Documentation placement: guide.md: outside allowed H2" in preview["pending"]
    assert preview["matrix"]["next_step"].startswith("Run `aips publish matrix-sync")
    assert preview["pr_creation"]["required_label"] == "aips:core-change"

    with tempfile.TemporaryDirectory() as td:
        matrix_path = Path(td) / "matrix.yaml"
        files = ["scripts/feature.py"]
        matrix_hash = publish.canonical_hash(files)
        matrix = {
            "candidate": {"base_sha": "base-sha", "changed_files_hash": matrix_hash},
            "status": "READY", "blockers": [], "actual_diff_reconciled": True,
        }
        cases = [
            ({"status": "DRAFT"}, ["status"]),
            ({"blockers": ["pending review"]}, ["blockers"]),
            ({"actual_diff_reconciled": False}, ["actual_diff_reconciled"]),
            ({"candidate": {"base_sha": "old", "changed_files_hash": matrix_hash}}, ["base_sha"]),
            ({}, []),
        ]
        for changes, expected_issues in cases:
            candidate = {**matrix, **changes}
            matrix_path.write_text(yaml.safe_dump(candidate), encoding="utf-8")
            with patch.object(publish, "resolve_commit", side_effect=["base-sha", "head-sha"]), patch.object(
                publish, "worktree_changed_files", return_value=files
            ), patch.object(
                publish, "documentation_impact", return_value={"required_additions": [], "complete": True}
            ), patch.object(
                publish.documentation_placement, "audit_worktree", return_value=[]
            ), patch.object(
                publish, "preview_content_safety", return_value={"status": "PASS", "blockers": []}
            ), patch.object(
                publish, "configured_identity_plan", return_value={"status": "PASS", "blockers": []}
            ):
                candidate_preview = publish.preview_candidate(Namespace(
                    base="main", head="HEAD", change_class="core", labels="aips:core-change",
                    profile=ROOT / "config/integration-gate.yaml", matrix=matrix_path,
                ))
            assert candidate_preview["matrix"]["issues"] == expected_issues
            assert candidate_preview["status"] == ("NEEDS_WORK" if expected_issues else "READY_FOR_GATE")
            if expected_issues:
                try:
                    matrix_fingerprint(matrix_path, True, base_sha="base-sha", changed_files_hash=matrix_hash)
                except GateError:
                    pass
                else:
                    raise AssertionError(f"Gate accepted matrix issues: {expected_issues}")
            else:
                assert matrix_fingerprint(matrix_path, True, base_sha="base-sha", changed_files_hash=matrix_hash)[0]

    with patch.object(publish.shutil, "which", return_value="/usr/bin/gh"), patch.object(
        publish, "git", return_value="https://github.com/owner/repo.git"
    ), patch.object(publish.subprocess, "run", return_value=Mock(returncode=1, stderr="private error")):
        auth = publish.remote_policy("main", False)
    assert auth["status"] == "AUTH_REQUIRED"
    assert "gh auth login" in auth["next_step"]
    assert "private error" not in repr(auth)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "config").mkdir()
        (root / "docs").mkdir()
        (root / "src.txt").write_text("before\n", encoding="utf-8")
        (root / "docs/guide.md").write_text("# Guide\n## Allowed\nExisting\n## Other\nExisting\n", encoding="utf-8")
        (root / "config/documentation-placement.yaml").write_text(yaml.safe_dump({
            "current_behavior_docs": {"docs/guide.md": {"required_h2": ["Allowed", "Other"], "strict_h2": True}},
            "placement_rules": [{"id": "sample", "triggers": ["src.txt"], "placements": {"docs/guide.md": ["Allowed"]}}],
        }), encoding="utf-8")
        (root / "config/documentation-sync.yaml").write_text(yaml.safe_dump({
            "technology_guide": {"triggers": ["src.txt"]},
        }), encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=noreply" + chr(64) + "github.com", "commit", "-qm", "base"], cwd=root, check=True)
        (root / "src.txt").write_text("after\n", encoding="utf-8")
        (root / "docs/guide.md").write_text("# Guide\n## Allowed\nExisting\n## Other\nExisting\nNew text\n", encoding="utf-8")
        place = publish.documentation_placement
        with patch.object(place, "ROOT", root), patch.object(place, "CONFIG", root / "config/documentation-placement.yaml"), patch.object(
            place, "SYNC_CONFIG", root / "config/documentation-sync.yaml"
        ):
            failures = place.audit_worktree("HEAD")
            assert any("allowed H2: ['Allowed']" in item for item in failures)
            (root / "docs/guide.md").write_text("# Guide\n## Allowed\nExisting\nNew text\n## Other\nExisting\n", encoding="utf-8")
            assert place.audit_worktree("HEAD") == []
            (root / "new.txt").write_text("untracked\n", encoding="utf-8")
            assert "new.txt" in place.working_tree_changed_files("HEAD")
            invalid = place.load_config()
            invalid["placement_rules"][0]["placements"]["docs/guide.md"] = ["Missing"]
            assert any("missing H2" in item for item in place.static_errors(invalid))
            (root / "docs/guide.md").unlink()
            assert any("required canonical Human doc is missing" in item for item in place.placement_errors(place.load_config(), "HEAD", working_tree=True))

    with tempfile.TemporaryDirectory() as td:
        check = subprocess.run(
            [sys.executable, str(ROOT / "bin/prepare-local-validation"), "--check-only", "--venv", str(Path(td) / "missing")],
            cwd=ROOT, capture_output=True, text=True,
        )
        assert check.returncode == 2
        assert "python3.12 bin/prepare-local-validation" in check.stderr

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        candidate = root / "untracked.txt"
        private_email = "private.address" + "@" + "example.com"
        candidate.write_text("contact " + private_email, encoding="utf-8")
        with patch.object(publish, "ROOT", root), patch.object(publish, "git", return_value=""):
            early_safety = publish.preview_content_safety("base-sha", ["untracked.txt"])
        assert early_safety["status"] == "BLOCKED"
        assert private_email not in repr(early_safety)
    private_email = "private.address" + "@" + "example.com"
    with patch.object(publish, "git", return_value=private_email):
        early_identity = publish.configured_identity_plan()
    assert early_identity["status"] == "BLOCKED" and private_email not in repr(early_identity)
    with patch.object(publish, "git", return_value=""):
        missing_identity = publish.configured_identity_plan()
    assert missing_identity["findings"] == [{"reason": "git_email_not_configured"}]

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

        matrix_path.write_text(
            "version: 1\ncandidate:\n  base_sha: old\n  changed_files_hash: old\nactual_diff_reconciled: true\nblockers:\n- pending review\nstatus: READY\n",
            encoding="utf-8",
        )
        with patch.object(publish, "ROOT", root), patch.object(publish, "CANONICAL_MATRIX", matrix_path), patch.object(
            publish, "resolve_commit", side_effect=["base-sha", "head-sha"]
        ), patch.object(publish, "worktree_changed_files", return_value=["src/feature.py"]):
            publish.sync_matrix_binding("main", "HEAD", matrix_path)
        populated = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
        assert len(populated["blockers"]) == 2
        assert populated["blockers"][0] == "pending review"

    environment = publish.environment_status()
    assert environment["status"] in {"READY", "ENVIRONMENT_BLOCKED"}
    assert "python" in environment and "python_modules" in environment

    repo_spec = importlib.util.spec_from_file_location("repository_preflight", ROOT / "scripts/repository_preflight.py")
    assert repo_spec and repo_spec.loader
    repository_preflight = importlib.util.module_from_spec(repo_spec)
    repo_spec.loader.exec_module(repository_preflight)
    with tempfile.TemporaryDirectory() as td:
        docs_root = Path(td)
        (docs_root / "docs").mkdir()
        (docs_root / "docs/guide.md").write_text(
            "[valid](./target.md) [missing](./missing.md) [outside](../../outside.md)\n"
            "```md\n[ignored](./not-a-real-link.md)\n```\n"
            "[external](https://example.com/docs)\n",
            encoding="utf-8",
        )
        (docs_root / "docs/target.md").write_text("# Target\n", encoding="utf-8")
        link_errors = repository_preflight.check_markdown_links(docs_root, ["docs/guide.md"])
        assert "docs/guide.md: local Markdown link target does not exist: ./missing.md" in link_errors
        assert any("escapes the repository" in error for error in link_errors)
        assert not any("not-a-real-link" in error for error in link_errors)
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
    assert "launch denied" not in repr(blocked_environment)
    assert "/browser" not in repr(blocked_environment)
    with patch.object(publish, "environment_status", return_value=blocked_environment), patch.object(
        publish, "build_plan", side_effect=AssertionError("full plan must not run after an environment blocker")
    ), patch.object(publish, "emit") as emitted:
        assert publish.run_candidate(Namespace(format="json")) == 2
        assert emitted.call_args.args[0]["status"] == "ENVIRONMENT_BLOCKED"
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
        "preview_content_safety",
        "configured_identity_plan",
    ):
        assert contract in source
    browser_source = (ROOT / "scripts/browser_runtime.py").read_text(encoding="utf-8")
    for contract in ("BROWSER_LAUNCH_FAILED", "sync_playwright", "AIPS_BROWSER_PROVIDER"):
        assert contract in browser_source
    workflow = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    ordered_steps = (
        "Mandatory candidate secret scan (fail fast)",
        "Repository preflight (fail fast)",
        "python -m pip install -r requirements.txt",
        "Install deterministic Playwright Chromium",
        "deterministic integration gate",
    )
    positions = [workflow.index(step) for step in ordered_steps]
    assert positions == sorted(positions), "CI must reject repository drift before expensive validation"
    assert 'python scripts/repository_preflight.py' in workflow
    assert '--base "$AIPS_GATE_BASE" --head "$AIPS_GATE_HEAD"' in workflow

    print("PUBLISH PREFLIGHT LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

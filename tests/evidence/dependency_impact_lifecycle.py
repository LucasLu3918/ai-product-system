"""Exercise dependency update classification and validation planning."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/dependency_impact.py"
POLICY = ROOT / "config/dependency-policy.yaml"


def run(*args: str) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return result, json.loads(result.stdout)


policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
ruff, ruff_report = run("plan", "--ecosystem", "pip", "--name", "ruff")
assert ruff.returncode == 0 and ruff_report["classification"] == "DEV_TOOL"
assert ruff_report["risk"] == "LOW" and "targeted_tool_validation" in ruff_report["recommended_validation_plan"]
assert ruff_report["automatic_merge_authorized"] is False and ruff_report["human_decision_required"] is True

semantic, semantic_report = run("plan", "--ecosystem", "pip", "--name", "sentence-transformers")
assert semantic.returncode == 0 and semantic_report["classification"] == "SEMANTIC_RUNTIME"
assert semantic_report["risk"] == "HIGH"
assert {"retrieval_regression", "semantic_trial"}.issubset(semantic_report["recommended_validation_plan"])

unclassified, unknown = run("plan", "--ecosystem", "pip", "--name", "new-package")
assert unclassified.returncode == 0 and unknown["classification"] == "UNCLASSIFIED"
assert unknown["risk"] == "HIGH" and unknown["human_decision_required"] is True

inventory = ROOT / "tests/fixtures/dependency-impact/inventory.yaml"
report, report_data = run("report", "--input", str(inventory))
assert report.returncode == 0 and report_data["status"] == "READY_FOR_HUMAN_REVIEW"
assert report_data["dependency_count"] == 3
assert len({item["dependency"]["normalized_name"] for item in report_data["items"]}) == 3

invalid_policy = dict(policy)
invalid_policy["automatic_merge_authorized"] = True
with tempfile.TemporaryDirectory() as temporary:
    invalid_path = Path(temporary) / "policy.yaml"
    invalid_path.write_text(yaml.safe_dump(invalid_policy), encoding="utf-8")
    invalid, invalid_report = run("classify", "--ecosystem", "pip", "--name", "ruff", "--policy", str(invalid_path))
assert invalid.returncode != 0 and invalid_report["status"] == "BLOCKED"

# Pure dependency update documentation exemption (deterministic diff shape).
sys.path.insert(0, str(ROOT / "scripts"))
from dependency_impact import pure_dependency_update, validate_policy
from publish_preflight_policy import documentation_impact

OLD_SHA, NEW_SHA = "a" * 40, "b" * 40
WORKFLOW = (
    "name: scorecard\njobs:\n  analysis:\n    steps:\n"
    f"      - uses: actions/checkout@{OLD_SHA} # v4.1.0\n"
    "        with:\n          persist-credentials: false\n"
    "      - name: Upload\n"
    f"        uses: github/codeql-action/upload-sarif@{OLD_SHA} # v4.37.4\n"
    "        run: echo done\n"
)
FILES = {
    ".github/workflows/scorecard.yml": WORKFLOW,
    "constraints/tested.txt": "attrs==26.1.0\ncoverage==7.16.1\ncryptography==50.0.1\n",
    "requirements-validation.txt": "ruff==0.16.8\ncoverage==7.16.1\n",
    "requirements.txt": "PyYAML>=6.0.3,<7\ncryptography==50.0.1\n",
    "docs/notes.md": "notes\n",
    ".github/actions/setup/action.yml": "runs:\n  using: composite\n",
}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True,
        env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@localhost", "GIT_COMMITTER_NAME": "t",
             "GIT_COMMITTER_EMAIL": "t@localhost", "HOME": str(repo), "PATH": "/usr/bin:/bin:/opt/homebrew/bin"},
    ).stdout


def scope_for(edit, *, commit: bool = True, exemption: dict[str, object] | None = None, **kwargs: object) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="aips-dep-scope-") as temporary:
        repo = Path(temporary)
        git(repo, "init", "-q", "-b", "main")
        for rel, text in FILES.items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_bytes(text.encode("utf-8"))
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "base")
        edit(repo)
        if commit:
            git(repo, "add", "-A")
            git(repo, "commit", "-qm", "head", "--allow-empty")
        candidate = json.loads(json.dumps(policy))
        if exemption:
            candidate["documentation_exemption"].update(exemption)
        return pure_dependency_update("HEAD~1" if commit else "HEAD", "HEAD" if commit else None, repo,
                                      policy=candidate, **kwargs)


def replace(rel: str, old: str, new: str):
    def edit(repo: Path) -> None:
        path = repo / rel
        text = path.read_text(encoding="utf-8")
        assert old in text, (rel, old)
        path.write_bytes(text.replace(old, new).encode("utf-8"))
    return edit


def combine(*edits):
    def edit(repo: Path) -> None:
        for item in edits:
            item(repo)
    return edit


WF = ".github/workflows/scorecard.yml"
sarif_bump = replace(WF, f"upload-sarif@{OLD_SHA} # v4.37.4", f"upload-sarif@{NEW_SHA} # v4.38.3")
coverage_bump = combine(
    replace("constraints/tested.txt", "coverage==7.16.1", "coverage==7.16.2"),
    replace("requirements-validation.txt", "coverage==7.16.1", "coverage==7.16.2"),
)

# Positive cases.
single = scope_for(sarif_bump)
assert single["status"] == "PURE_DEPENDENCY_UPDATE", single
assert single["files"] == [WF] and single["items"][0]["name"] == "github/codeql-action"
assert single["items"][0]["classification"] == "CI_ACTION" and single["automatic_merge_authorized"] is False
repin = scope_for(replace(WF, f"checkout@{OLD_SHA} # v4.1.0", f"checkout@{NEW_SHA} # v4.1.0"))
assert repin["status"] == "PURE_DEPENDENCY_UPDATE" and repin["items"][0]["repinned_same_version"] is True
major_group = scope_for(combine(sarif_bump, replace(WF, f"checkout@{OLD_SHA} # v4.1.0", f"checkout@{NEW_SHA} # v5.0.0")))
assert major_group["status"] == "PURE_DEPENDENCY_UPDATE" and len(major_group["items"]) == 2
pip = scope_for(coverage_bump)
assert pip["status"] == "PURE_DEPENDENCY_UPDATE", pip
assert pip["files"] == ["constraints/tested.txt", "requirements-validation.txt"]
security = scope_for(combine(
    replace("constraints/tested.txt", "cryptography==50.0.1", "cryptography==50.0.2"),
    replace("requirements.txt", "cryptography==50.0.1", "cryptography==50.0.2"),
))
assert security["status"] == "PURE_DEPENDENCY_UPDATE" and security["human_review_required"] is True
assert {item["risk"] for item in security["items"]} == {"HIGH"}

impact = documentation_impact([WF], ROOT, single)
assert impact["complete"] and not impact["required_additions"], impact["required_additions"]
assert impact["dependency_update_exemption"]["applied"] is True
assert impact["dependency_update_exemption"]["suppressed_required_additions"]
assert documentation_impact([WF], ROOT)["required_additions"] == impact["dependency_update_exemption"]["suppressed_required_additions"]
mismatch = documentation_impact([WF, "docs/notes.md"], ROOT, single)
assert not mismatch["complete"] and mismatch["dependency_update_exemption"]["applied"] is False

# Negative cases: every one keeps the full documentation rules.
negatives = {
    "UNPAIRED_LINE": [
        combine(sarif_bump, replace(WF, "        run: echo done\n", "        run: echo done\n        env: {X: 1}\n")),
        replace(WF, "      - name: Upload\n", f"      - uses: evil/action@{NEW_SHA} # v1\n      - name: Upload\n"),
    ],
    "OUT_OF_SHAPE": [
        combine(sarif_bump, replace(WF, "persist-credentials: false", "persist-credentials: true")),
        replace(WF, "run: echo done", "run: make build"),
        replace(WF, f"checkout@{OLD_SHA} # v4.1.0", "./.github/actions/setup"),
        replace("requirements.txt", "PyYAML>=6.0.3,<7", "PyYAML>=6.0.4,<7"),
        replace("constraints/tested.txt", "coverage==7.16.1", "coverage[toml]==7.16.2"),
        replace("constraints/tested.txt", "coverage==7.16.1", "coverage==7.16.2rc1"),
        replace("constraints/tested.txt", "coverage==7.16.1", "coverage==7.16.2 ; python_version>'3'"),
        replace("constraints/tested.txt", "coverage==7.16.1\n", "coverage==7.16.2\r\n"),
        replace("constraints/tested.txt", "coverage==7.16.1", "c\u043everage==7.16.2"),
        replace(WF, f"upload-sarif@{OLD_SHA} # v4.37.4", f"upload-sarif@{NEW_SHA}"),
    ],
    "ACTION_DOWNGRADE": [replace(WF, f"upload-sarif@{OLD_SHA} # v4.37.4", f"upload-sarif@{NEW_SHA} # v4.36.0")],
    "PIP_DOWNGRADE": [replace("constraints/tested.txt", "coverage==7.16.1", "coverage==7.15.9")],
    "PIP_NO_CHANGE": [replace("constraints/tested.txt", "coverage==7.16.1", "coverage==7.16.1.0")],
    "UNPINNED_REFERENCE": [replace(WF, f"upload-sarif@{OLD_SHA} # v4.37.4", "upload-sarif@v4")],
    "ACTION_IDENTITY_CHANGED": [replace(WF, f"github/codeql-action/upload-sarif@{OLD_SHA}", f"evil/codeql-action/upload-sarif@{NEW_SHA}")],
    "PACKAGE_IDENTITY_CHANGED": [replace("constraints/tested.txt", "coverage==7.16.1", "coverag3==7.16.2")],
    "PATH_NOT_ALLOWED": [
        combine(sarif_bump, replace("docs/notes.md", "notes", "more notes")),
        replace(".github/actions/setup/action.yml", "composite", "node20"),
    ],
}
for reason, edits in negatives.items():
    for index, edit in enumerate(edits):
        observed = scope_for(edit)
        assert observed["status"] == "NOT_PURE" and observed["reason"] == reason, (reason, index, observed)


def add_file(rel: str, text: str = "x==1.0\n"):
    def edit(repo: Path) -> None:
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(text, encoding="utf-8")
    return edit


def chmod_requirements(repo: Path) -> None:
    (repo / "requirements-validation.txt").chmod(0o755)


def delete_constraints(repo: Path) -> None:
    (repo / "constraints/tested.txt").unlink()


for edit in (add_file("requirements-new.txt"), chmod_requirements, delete_constraints,
             add_file("constraints/sub/nested.txt"), add_file("requirements/extra.txt")):
    observed = scope_for(edit)
    assert observed["status"] == "NOT_PURE" and observed["reason"] in {"FILE_ENTRY_NOT_ALLOWED", "PATH_NOT_ALLOWED"}, observed
assert scope_for(lambda repo: None)["reason"] == "NO_CHANGES"
assert scope_for(sarif_bump, planned_paths=["docs/human/MAINTENANCE.md"])["reason"] == "PLANNED_PATHS_PRESENT"
assert scope_for(coverage_bump, exemption={"max_line_pairs": 1})["reason"] == "SIZE_LIMIT"
assert scope_for(coverage_bump, exemption={"max_files": 1})["reason"] == "SIZE_LIMIT"
assert scope_for(sarif_bump, exemption={"enabled": False})["reason"] == "DISABLED"
assert scope_for(coverage_bump, exemption={"paths": ["**"]})["reason"] == "CLASSIFIER_BLOCKED"
assert scope_for(combine(
    replace("constraints/tested.txt", "cryptography==50.0.1", "cryptography==50.0.2"),
), exemption={"high_risk_classes_exempt": False})["reason"] == "HIGH_RISK_NOT_EXEMPT"
worktree_pure = scope_for(coverage_bump, commit=False)
assert worktree_pure["status"] == "PURE_DEPENDENCY_UPDATE", worktree_pure
assert scope_for(combine(coverage_bump, add_file("scratch.txt")), commit=False)["reason"] == "UNTRACKED_PRESENT"
assert pure_dependency_update("does-not-exist", "HEAD", ROOT, policy=policy)["reason"] == "GIT_ERROR"
broad = json.loads(json.dumps(policy))
broad["documentation_exemption"]["paths"] = ["scripts/*.py"]
assert validate_policy(broad), "broad exemption paths must be rejected"
print("dependency impact lifecycle: PASS")

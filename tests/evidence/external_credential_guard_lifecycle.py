#!/usr/bin/env python3
from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import external_credential_guard as guard  # noqa: E402

CONFIG = ROOT / "config/external-credentials.yaml"

config = guard.load_yaml(CONFIG)
guard.validate_config(config)
current = guard.audit(ROOT, config)
assert current["status"] == "PASS", current
assert current["policy"]["external_credentials_required_for_baseline"] is False
assert current["policy"]["external_credentials_required_for_release"] is False
assert set(current["discovered_credentials"]) == {"E2B_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY"}
assert current["authority"] == {
    "human_approval_granted": False,
    "merge_authorized": False,
    "release_authorized": False,
    "publication_authorized": False,
    "credential_creation_authorized": False,
}

with tempfile.TemporaryDirectory(prefix="aips-credential-guard-") as tmp:
    root = Path(tmp)
    (root / ".github/workflows").mkdir(parents=True)
    (root / "config").mkdir()
    (root / "scripts").mkdir()

    minimal = {
        "version": 1,
        "scope": {
            "scan_roots": [".github/workflows", "config", "scripts"],
            "file_suffixes": [".yml", ".yaml", ".py"],
        },
        "policy": {
            "external_credentials_required_for_baseline": False,
            "external_credentials_required_for_release": False,
            "undeclared_external_credential": "BLOCK",
            "pull_request_secret_exposure": "BLOCK",
            "credential_values_in_repository": False,
        },
        "credentials": {
            "OPENAI_API_KEY": {
                "class": "external_agent_provider",
                "optional": True,
                "activation": "explicit_secret_configuration",
                "missing_behaviors": ["ANALYSIS_PENDING"],
                "required_for_baseline": False,
                "required_for_release": False,
                "allowed_consumers": [".github/workflows/test.yml"],
            }
        },
        "conditional_workflow_exposure": [],
        "authority": {
            "human_approval_granted": False,
            "merge_authorized": False,
            "release_authorized": False,
            "publication_authorized": False,
            "credential_creation_authorized": False,
        },
    }

    secret_expr = "$" + "{{ secrets.OPENAI_API_KEY }}"
    (root / ".github/workflows/test.yml").write_text(
        "name: test\non:\n  workflow_dispatch:\njobs:\n  x:\n    env:\n      OPENAI_API_KEY: " + secret_expr + "\n",
        encoding="utf-8",
    )
    passed = guard.audit(root, minimal)
    assert passed["status"] == "PASS", passed

    anthropic_expr = "$" + "{{ secrets.ANTHROPIC_API_KEY }}"
    (root / ".github/workflows/undeclared.yml").write_text(
        "name: undeclared\non:\n  workflow_dispatch:\njobs:\n  x:\n    env:\n      ANTHROPIC_API_KEY: " + anthropic_expr + "\n",
        encoding="utf-8",
    )
    undeclared = guard.audit(root, minimal)
    assert undeclared["status"] == "BLOCKED"
    assert any("ANTHROPIC_API_KEY" in item for item in undeclared["findings"])
    (root / ".github/workflows/undeclared.yml").unlink()

    (root / ".github/workflows/test.yml").write_text(
        "name: test\non:\n  pull_request:\njobs:\n  x:\n    env:\n      OPENAI_API_KEY: " + secret_expr + "\n",
        encoding="utf-8",
    )
    pr_exposure = guard.audit(root, minimal)
    assert pr_exposure["status"] == "BLOCKED"
    assert any("pull_request" in item for item in pr_exposure["findings"])

    invalid = copy.deepcopy(minimal)
    invalid["credentials"]["OPENAI_API_KEY"]["required_for_baseline"] = True
    try:
        guard.validate_config(invalid)
    except guard.GuardError:
        pass
    else:
        raise AssertionError("required external credential must be rejected")

print("external credential dependency guard lifecycle: PASS")

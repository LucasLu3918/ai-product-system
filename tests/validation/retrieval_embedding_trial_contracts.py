from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import yaml

from .static_contracts import ROOT, errors

CONFIG = ROOT / "config" / "retrieval-embedding-trial.yaml"
SCRIPT = ROOT / "scripts" / "retrieval_embedding_trial.py"
SUMMARY_SCRIPT = ROOT / "scripts" / "retrieval_embedding_trial_summary.py"
WORKFLOW = ROOT / ".github" / "workflows" / "retrieval-semantic-trial.yml"

for path in (CONFIG, SCRIPT, SUMMARY_SCRIPT, WORKFLOW):
    if not path.is_file():
        errors.append(f"Missing embedding Trial artifact: {path.relative_to(ROOT)}")

if CONFIG.is_file():
    try:
        config = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        errors.append(f"Embedding Trial config YAML invalid: {exc}")
        config = {}
    provider = config.get("provider") or {}
    privacy = config.get("privacy") or {}
    fallback = config.get("fallback") or {}
    authority = config.get("authority") or {}
    if provider.get("endpoint") != "https://api.openai.com/v1/embeddings":
        errors.append("Embedding Trial endpoint must be the approved OpenAI embeddings endpoint")
    if provider.get("default_model") != "text-embedding-3-small":
        errors.append("Embedding Trial default model must be text-embedding-3-small")
    if provider.get("required_secret") != "OPENAI_API_KEY":
        errors.append("Embedding Trial must reuse OPENAI_API_KEY secret reference")
    if privacy.get("source_scope") != "synthetic_fixture_only":
        errors.append("Embedding Trial must be synthetic_fixture_only")
    if privacy.get("repository_source_transfer") is not False:
        errors.append("Embedding Trial must forbid repository source transfer")
    if fallback.get("missing_credentials") != "TRIAL_PENDING":
        errors.append("Missing embedding credentials must produce TRIAL_PENDING")
    if fallback.get("provider_failure") != "TRIAL_BLOCKED":
        errors.append("Embedding provider failure must produce TRIAL_BLOCKED")
    for key in ("default_enablement", "provider_auto_enablement", "production_source_transfer", "adoption_without_human_decision"):
        if authority.get(key) is not False:
            errors.append(f"Embedding Trial authority.{key} must be false")

if SCRIPT.is_file() and CONFIG.is_file():
    env = dict(os.environ)
    env.pop("OPENAI_API_KEY", None)
    readiness = subprocess.run([
        sys.executable, str(SCRIPT),
        "--config", str(CONFIG),
        "--check-readiness",
    ], cwd=ROOT, env=env, capture_output=True, text=True)
    if readiness.returncode != 0:
        errors.append(f"Embedding Trial readiness check failed: {readiness.stdout} {readiness.stderr}")
    else:
        try:
            doc = json.loads(readiness.stdout)
        except json.JSONDecodeError as exc:
            errors.append(f"Embedding Trial readiness output invalid JSON: {exc}")
        else:
            if doc.get("status") != "TRIAL_PENDING":
                errors.append("Missing credential readiness must report TRIAL_PENDING")
            provider = doc.get("provider") or {}
            if provider.get("credential_available") is not False:
                errors.append("Missing credential readiness must report credential_available=false")

if WORKFLOW.is_file():
    workflow_text = WORKFLOW.read_text(encoding="utf-8")
    required = [
        "workflow_dispatch:",
        "feature/retrieval-embedding-trial",
        "OPENAI_API_KEY: " + "$" + "{{ secrets.OPENAI_API_KEY }}",
        'AIPS_RUN_REMOTE_EMBEDDING_TRIAL: "1"',
        "AIPS_EMBEDDING_TRIAL_OUTPUT:",
        "python tests/evidence/retrieval_quality_evaluation_lifecycle.py",
        "Publish Trial operator summary",
        "scripts/retrieval_embedding_trial_summary.py",
        "GITHUB_STEP_SUMMARY",
    ]
    for needle in required:
        if needle not in workflow_text:
            errors.append(f"Embedding Trial workflow missing contract text: {needle}")
    if "pull_request:" in workflow_text:
        errors.append("Embedding Trial workflow must not run on every pull request")
    if "branches:\n      - main" in workflow_text:
        errors.append("Embedding Trial workflow must not run on every main push")


if SUMMARY_SCRIPT.is_file():
    compiled = subprocess.run(
        [sys.executable, "-m", "py_compile", str(SUMMARY_SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if compiled.returncode != 0:
        errors.append(f"Embedding Trial summary syntax failed: {compiled.stderr.strip()}")
    with tempfile.TemporaryDirectory(prefix="aips-embedding-summary-") as tmp:
        temp = Path(tmp)
        report = temp / "report.json"
        output = temp / "summary.md"
        report.write_text(json.dumps({
            "trial": {"status": "TRIAL_PENDING", "recommendation": "PENDING_CREDENTIAL"},
            "provider": {
                "id": "openai-embeddings",
                "model": "text-embedding-3-small",
                "credential_available": False,
            },
            "privacy": {
                "source_scope": "synthetic_fixture_only",
                "repository_source_transfer": False,
            },
            "summary": {"reason": "required credential is unavailable; provider was not called"},
            "authority": {
                "default_enablement": False,
                "provider_auto_enablement": False,
                "production_source_transfer": False,
                "adoption_without_human_decision": False,
            },
        }), encoding="utf-8")
        rendered = subprocess.run([
            sys.executable, str(SUMMARY_SCRIPT),
            "--report", str(report),
            "--output", str(output),
        ], cwd=ROOT, capture_output=True, text=True)
        if rendered.returncode != 0:
            errors.append(f"Embedding Trial summary render failed: {rendered.stdout} {rendered.stderr}")
        elif not output.is_file():
            errors.append("Embedding Trial summary renderer must create the requested output")
        else:
            summary_text = output.read_text(encoding="utf-8")
            for needle in (
                "TRIAL_PENDING",
                "PENDING_CREDENTIAL",
                "OPENAI_API_KEY",
                "retrieval-semantic-trial",
                "Credential available",
                "Repository source transfer",
                "Human Adoption Decision",
            ):
                if needle not in summary_text:
                    errors.append(f"Embedding Trial summary missing operator guidance: {needle}")

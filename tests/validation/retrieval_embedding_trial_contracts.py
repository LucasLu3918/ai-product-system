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
SEMANTIC_REQUIREMENTS = ROOT / "requirements-semantic-trial.txt"

for path in (CONFIG, SCRIPT, SUMMARY_SCRIPT, WORKFLOW, SEMANTIC_REQUIREMENTS):
    if not path.is_file():
        errors.append(f"Missing embedding Trial artifact: {path.relative_to(ROOT)}")

if CONFIG.is_file():
    try:
        config = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        errors.append(f"Embedding Trial config YAML invalid: {exc}")
        config = {}
    selector = config.get("provider") or {}
    providers = config.get("providers") or {}
    local = providers.get("local") or {}
    remote = providers.get("remote") or {}
    privacy = config.get("privacy") or {}
    fallback = config.get("fallback") or {}
    authority = config.get("authority") or {}

    if config.get("version") != 2:
        errors.append("Embedding Trial config version must be 2")
    if selector.get("default") != "local":
        errors.append("Embedding Trial must default to local provider")
    if selector.get("selection_env") != "AIPS_RETRIEVAL_EMBEDDING_PROVIDER":
        errors.append("Embedding Trial provider selector env mismatch")
    if local.get("kind") != "sentence-transformers":
        errors.append("Local embedding provider must use sentence-transformers")
    if local.get("default_model") != "BAAI/bge-small-en-v1.5":
        errors.append("Local embedding Trial default model must be BAAI/bge-small-en-v1.5")
    revision = str(local.get("model_revision") or "")
    if len(revision) != 40 or any(ch not in "0123456789abcdef" for ch in revision):
        errors.append("Local embedding model revision must be a pinned 40-character commit")
    if local.get("dimensions") != 384:
        errors.append("Local embedding Trial dimensions must be 384")
    if local.get("execution_location") != "runner-local":
        errors.append("Local embedding inference must execute runner-local")
    if local.get("model_download_network") is not True:
        errors.append("Local embedding model download network declaration missing")

    if remote.get("endpoint") != "https://api.openai.com/v1/embeddings":
        errors.append("Optional remote endpoint must remain the approved OpenAI embeddings endpoint")
    if remote.get("default_model") != "text-embedding-3-small":
        errors.append("Optional remote default model must remain text-embedding-3-small")
    if remote.get("required_secret") != "OPENAI_API_KEY":
        errors.append("Optional remote provider must reuse OPENAI_API_KEY secret reference")
    if privacy.get("source_scope") != "synthetic_fixture_only":
        errors.append("Embedding Trial must be synthetic_fixture_only")
    if privacy.get("repository_source_transfer") is not False:
        errors.append("Embedding Trial must forbid repository source transfer")
    if fallback.get("missing_remote_credentials") != "TRIAL_PENDING":
        errors.append("Missing remote embedding credentials must produce TRIAL_PENDING")
    if fallback.get("provider_failure") != "TRIAL_BLOCKED":
        errors.append("Embedding provider failure must produce TRIAL_BLOCKED")
    for key in ("default_enablement", "provider_auto_enablement", "production_source_transfer", "adoption_without_human_decision"):
        if authority.get(key) is not False:
            errors.append(f"Embedding Trial authority.{key} must be false")

if SEMANTIC_REQUIREMENTS.is_file() and "sentence-transformers==" not in SEMANTIC_REQUIREMENTS.read_text(encoding="utf-8"):
    errors.append("Semantic Trial dependency must pin sentence-transformers")

for script in (SCRIPT, SUMMARY_SCRIPT):
    if script.is_file():
        compiled = subprocess.run([sys.executable, "-m", "py_compile", str(script)], cwd=ROOT, capture_output=True, text=True)
        if compiled.returncode != 0:
            errors.append(f"Embedding Trial script syntax failed: {script.name}: {compiled.stderr.strip()}")

if SCRIPT.is_file() and CONFIG.is_file():
    local_env = dict(os.environ)
    local_env.pop("OPENAI_API_KEY", None)
    local_env.pop("AIPS_RETRIEVAL_EMBEDDING_PROVIDER", None)
    readiness = subprocess.run([sys.executable, str(SCRIPT), "--config", str(CONFIG), "--check-readiness"], cwd=ROOT, env=local_env, capture_output=True, text=True)
    if readiness.returncode != 0:
        errors.append(f"Local embedding Trial readiness check failed: {readiness.stdout} {readiness.stderr}")
    else:
        try:
            doc = json.loads(readiness.stdout)
        except json.JSONDecodeError as exc:
            errors.append(f"Local embedding Trial readiness output invalid JSON: {exc}")
        else:
            provider = doc.get("provider") or {}
            if doc.get("status") != "READY":
                errors.append("Default local embedding readiness must report READY")
            if provider.get("mode") != "local" or provider.get("credential_required") is not False:
                errors.append("Default local embedding provider must be credential-free")
            if provider.get("execution_location") != "runner-local" or provider.get("inference_source_transfer") is not False:
                errors.append("Local embedding readiness must prove runner-local inference without source transfer")

    remote_env = dict(local_env)
    remote_env["AIPS_RETRIEVAL_EMBEDDING_PROVIDER"] = "remote"
    remote_readiness = subprocess.run([sys.executable, str(SCRIPT), "--config", str(CONFIG), "--check-readiness"], cwd=ROOT, env=remote_env, capture_output=True, text=True)
    if remote_readiness.returncode != 0:
        errors.append(f"Remote embedding Trial readiness check failed: {remote_readiness.stdout} {remote_readiness.stderr}")
    else:
        try:
            doc = json.loads(remote_readiness.stdout)
        except json.JSONDecodeError as exc:
            errors.append(f"Remote embedding Trial readiness output invalid JSON: {exc}")
        else:
            provider = doc.get("provider") or {}
            if doc.get("status") != "TRIAL_PENDING":
                errors.append("Missing remote credential readiness must report TRIAL_PENDING")
            if provider.get("mode") != "remote" or provider.get("credential_available") is not False:
                errors.append("Explicit remote provider must report missing credential truthfully")

if WORKFLOW.is_file():
    workflow_text = WORKFLOW.read_text(encoding="utf-8")
    required = [
        "workflow_dispatch:",
        "feature/retrieval-embedding-trial",
        "AIPS_RETRIEVAL_EMBEDDING_PROVIDER:",
        "OPENAI_API_KEY: " + "$" + "{{ secrets.OPENAI_API_KEY }}",
        'AIPS_RUN_EMBEDDING_TRIAL: "1"',
        "requirements-semantic-trial.txt",
        "SENTENCE_TRANSFORMERS_HOME:",
        'HF_HUB_DISABLE_TELEMETRY: "1"',
        "python tests/evidence/retrieval_quality_evaluation_lifecycle.py",
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
    with tempfile.TemporaryDirectory(prefix="aips-embedding-summary-") as tmp:
        temp = Path(tmp)
        samples = [
            (
                "local",
                {
                    "trial": {"status": "TRIAL_BLOCKED", "recommendation": "HOLD"},
                    "provider": {
                        "mode": "local",
                        "id": "local-bge-small",
                        "model": "BAAI/bge-small-en-v1.5",
                        "model_revision": "0b329b72cad8d6ff9a504a30a6c239b87802dc84",
                        "execution_location": "runner-local",
                        "credential_required": False,
                        "credential_available": None,
                        "inference_source_transfer": False,
                        "model_download_network": True,
                    },
                    "privacy": {"source_scope": "synthetic_fixture_only", "repository_source_transfer": False},
                    "summary": {"reason": "local embedding model download/load/inference failed"},
                    "authority": {"default_enablement": False, "provider_auto_enablement": False, "production_source_transfer": False, "adoption_without_human_decision": False},
                },
                ("TRIAL_BLOCKED", "runner-local", "not-required", "No OpenAI API key is required", "Human Adoption Decision"),
            ),
            (
                "remote",
                {
                    "trial": {"status": "TRIAL_PENDING", "recommendation": "PENDING_CREDENTIAL"},
                    "provider": {
                        "mode": "remote",
                        "id": "openai-embeddings",
                        "model": "text-embedding-3-small",
                        "execution_location": "remote",
                        "credential_required": True,
                        "credential_available": False,
                        "inference_source_transfer": True,
                    },
                    "privacy": {"source_scope": "synthetic_fixture_only", "repository_source_transfer": False},
                    "summary": {"reason": "required remote credential is unavailable; provider was not called"},
                    "authority": {"default_enablement": False, "provider_auto_enablement": False, "production_source_transfer": False, "adoption_without_human_decision": False},
                },
                ("TRIAL_PENDING", "PENDING_CREDENTIAL", "OPENAI_API_KEY", "retrieval-semantic-trial", "Credential available"),
            ),
        ]
        for name, payload, needles in samples:
            report = temp / f"{name}.json"
            output = temp / f"{name}.md"
            report.write_text(json.dumps(payload), encoding="utf-8")
            rendered = subprocess.run([sys.executable, str(SUMMARY_SCRIPT), "--report", str(report), "--output", str(output)], cwd=ROOT, capture_output=True, text=True)
            if rendered.returncode != 0 or not output.is_file():
                errors.append(f"{name} embedding Trial summary render failed: {rendered.stdout} {rendered.stderr}")
                continue
            summary_text = output.read_text(encoding="utf-8")
            for needle in needles:
                if needle not in summary_text:
                    errors.append(f"{name} embedding Trial summary missing guidance: {needle}")

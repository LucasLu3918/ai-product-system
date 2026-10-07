"""Bounded semantic checks for repository-local GitHub Actions workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CALLER_KEYS = {"name", "uses", "with", "secrets", "strategy", "needs", "if", "concurrency", "permissions", "cache-mode"}
LEVELS = {"none": 0, "read": 1, "write": 2}


def triggers(workflow: dict[str, Any]) -> dict[str, Any]:
    value = workflow.get("on", workflow.get(True, {}))
    return value if isinstance(value, dict) else {}


def permissions(value: Any) -> dict[str, int] | None:
    if value in ("read-all", "write-all"):
        return {"*": 1 if value == "read-all" else 2}
    if not isinstance(value, dict):
        return None
    return {str(key): LEVELS.get(str(level), -1) for key, level in value.items()}


def validate_workflows(root: Path) -> list[str]:
    errors: list[str] = []
    documents: dict[str, dict[str, Any]] = {}
    for path in sorted((root / ".github/workflows").glob("*.y*ml")):
        name = str(path.relative_to(root))
        try:
            doc = yaml.safe_load(path.read_text())
            if not isinstance(doc, dict) or not isinstance(doc.get("jobs"), dict):
                raise TypeError("workflow must declare jobs")
            documents[name] = doc
        except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
            errors.append(f"{name}: invalid workflow ({type(exc).__name__})")
    for name, doc in documents.items():
        jobs = doc["jobs"]
        for job_id, job in jobs.items():
            if not isinstance(job, dict):
                errors.append(f"{name}:{job_id}: job must be a mapping")
                continue
            needs = job.get("needs", [])
            needs = [needs] if isinstance(needs, str) else needs
            if not isinstance(needs, list) or any(not isinstance(item, str) or item not in jobs for item in needs):
                errors.append(f"{name}:{job_id}: invalid needs")
            for step in job.get("steps", []):
                if not isinstance(step, dict) or not str(step.get("uses", "")).startswith("./.github/actions/"):
                    continue
                action_path = root / str(step["uses"])[2:] / "action.yml"
                if not action_path.resolve().is_relative_to(root.resolve()):
                    errors.append(f"{name}:{job_id}: local action path escapes repository")
                    continue
                try:
                    action = yaml.safe_load(action_path.read_text())
                    declared = action.get("inputs", {})
                    supplied_inputs = step.get("with", {})
                    for key, settings in declared.items():
                        if settings.get("required") is True and key not in supplied_inputs and not settings.get("default"):
                            errors.append(f"{name}:{job_id}: local action is missing required input {key}")
                except (OSError, ValueError, TypeError, AttributeError, yaml.YAMLError):
                    errors.append(f"{name}:{job_id}: local action is missing or invalid")
            if "uses" not in job:
                continue
            unknown = set(job) - CALLER_KEYS
            if unknown:
                errors.append(f"{name}:{job_id}: unsupported reusable caller keys {sorted(unknown)}")
            reference = str(job["uses"])
            if not reference.startswith(("./", "$/")):
                continue  # External workflow contents are outside this local semantic check.
            target = reference[2:]
            if not target.startswith(".github/workflows/") or ".." in Path(target).parts:
                errors.append(f"{name}:{job_id}: reusable workflow path escapes workflow directory")
                continue
            callee = documents.get(target)
            if not callee or "workflow_call" not in triggers(callee):
                errors.append(f"{name}:{job_id}: local callee is missing workflow_call")
                continue
            supplied = permissions(job.get("permissions", doc.get("permissions")))
            for callee_job in callee["jobs"].values():
                if not isinstance(callee_job, dict):
                    continue
                requested = permissions(callee_job.get("permissions", callee.get("permissions")))
                if requested is None:
                    continue
                for permission, level in requested.items():
                    available = supplied.get(permission, supplied.get("*", 0)) if supplied is not None else 0
                    if level < 0 or available < level:
                        errors.append(f"{name}:{job_id}: callee cannot elevate {permission} permission")
    return sorted(set(errors))

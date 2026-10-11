"""Bounded, versioned creative feedback and repair; machine evidence has no authority."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from contextvars import ContextVar
from pathlib import Path
from typing import Any

import yaml
from creative_errors import Blocked

execution_deadline: ContextVar[float | None] = ContextVar("creative_execution_deadline", default=None)


def remaining_timeout(requested: float) -> float:
    deadline = execution_deadline.get()
    if deadline is None:
        return requested
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise Blocked("time_budget_exhausted", "The shared execution deadline expired.")
    return min(requested, remaining)


def executor():
    # Lazy import preserves the established executor facade and its test injection points.
    import creative_execution
    return creative_execution


def timed_lock(fd: int, deadline: float) -> None:
    c = executor()
    while True:
        if time.monotonic() >= deadline:
            raise Blocked("time_budget_exhausted", "Time budget expired while waiting for the source lock.")
        try:
            if os.name == "nt":
                os.lseek(fd, 0, os.SEEK_SET)
                c.msvcrt.locking(fd, c.msvcrt.LK_NBLCK, 1)
            else:
                c.fcntl.flock(fd, c.fcntl.LOCK_EX | c.fcntl.LOCK_NB)
            return
        except (BlockingIOError, PermissionError):
            time.sleep(min(0.05, max(0, deadline - time.monotonic())))


def checklist(profiles: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    character = profiles.get("character", {})
    acceptance = character.get("acceptance_criteria") or {}
    rows: list[dict[str, Any]] = []
    groups = [("required", acceptance.get("critical_features") or character.get("identity_features") or [], True),
              ("forbidden", acceptance.get("forbidden_misplacements") or [], True),
              ("style", [profiles.get("style", {}).get("intent", "")], False)]
    for kind, rules, critical in groups:
        if not isinstance(rules, list) or len(rules) > 12:
            raise Blocked("quality_criteria_invalid", "Criteria must be bounded string lists.")
        for rule in rules:
            if not isinstance(rule, str) or len(rule) > 600:
                raise Blocked("quality_criteria_invalid", "Each criterion must be a bounded string.")
            if rule.strip():
                rows.append({"id": f"{kind}-{len(rows) + 1}", "rule": rule.strip(), "critical": critical, "kind": kind})
    if not any(row["critical"] for row in rows):
        raise Blocked("quality_criteria_missing", "Declare visible identity criteria before machine checking.")
    return rows


def validate_checks(value: Any, criteria: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != len(criteria):
        raise Blocked("visual_review_response_invalid", "Every criterion requires exactly one observation.")
    expected = {item["id"] for item in criteria}
    found: dict[str, dict[str, Any]] = {}
    for item in value:
        if (not isinstance(item, dict) or set(item) != {"id", "assessment", "evidence", "suggestion"}
                or item.get("id") not in expected or item["id"] in found
                or item.get("assessment") not in {"MATCH", "DEFECT", "UNCERTAIN"}
                or any(not isinstance(item.get(key), str) or not item[key].strip() or len(item[key]) > 500
                       for key in ("evidence", "suggestion"))):
            raise Blocked("visual_review_response_invalid", "Criterion evidence is missing, duplicated or invalid.")
        found[item["id"]] = item
    return [{**criterion, **found[criterion["id"]]} for criterion in criteria]


def machine_decision(checks: list[dict[str, Any]]) -> str:
    if any(item["assessment"] == "DEFECT" for item in checks):
        return "DEFECTS_FOUND"
    if any(item["assessment"] == "UNCERTAIN" for item in checks):
        return "UNVERIFIED"
    return "MATCHES_CRITERIA"


def bound_manifest(project: Path, name: str) -> tuple[Path, Path, dict[str, Any]]:
    c = executor()
    root = project.expanduser().resolve(strict=True)
    path = c.confined(root, name, exists=True)
    if c.is_git_workspace(root) or path.name != "creative-execution-manifest.json" or path.stat().st_size > 256 * 1024:
        raise Blocked("manifest_invalid", "Use a bounded non-Git creative execution manifest.")
    for raw in (name,):
        if Path(raw).is_absolute() or ".." in Path(raw).parts or "\\" in raw or any((root / Path(*Path(raw).parts[:i])).is_symlink() for i in range(1, len(Path(raw).parts) + 1)):
            raise Blocked("manifest_invalid", "Manifest paths cannot traverse symlinks.")
    data = json.loads(path.read_text(encoding="utf-8"))
    output = data.get("output", {})
    raw_image = output.get("path", "")
    if not isinstance(raw_image, str) or ".." in Path(raw_image).parts or "\\" in raw_image or any((root / Path(*Path(raw_image).parts[:i])).is_symlink() for i in range(1, len(Path(raw_image).parts) + 1)):
        raise Blocked("manifest_invalid", "Image paths cannot traverse symlinks.")
    image = c.confined(root, raw_image, exists=True)
    if image.is_symlink() or not image.is_file() or image.stat().st_size > c.MAX_IMAGE_BYTES or c.digest(image) != output.get("sha256"):
        raise Blocked("manifest_hash_mismatch", "Output differs from the bound image.")
    scope = c.confined(root, data.get("output_scope", ""))
    if scope == root or scope not in image.parents or path.parent != scope or not c.output_magic(image):
        raise Blocked("manifest_scope_invalid", "Image and manifest must share the declared output scope.")
    profiles = data.get("profiles", [])
    if not isinstance(profiles, list) or not 1 <= len(profiles) <= 8:
        raise Blocked("manifest_invalid", "Repair requires profile provenance.")
    for row in profiles:
        source = c._profile_reference(root, row["path"], "profile")
        if c.digest(source) != row["sha256"]:
            raise Blocked("profile_hash_mismatch", "A source profile changed after generation.")
    return root, path, data


def write_versioned(parent: Path, stem: str, data: dict[str, Any]) -> Path:
    c = executor()
    for version in range(1, 10000):
        target = parent / f"{stem}-v{version}.json"
        try:
            c.atomic_manifest(target, data)
            return target
        except FileExistsError:
            continue
    raise Blocked("creative_version_exhausted", "No report version remains.")


def feedback(project: Path, manifest: str, defects: list[str]) -> dict[str, Any]:
    c = executor()
    root, source, data = bound_manifest(project, manifest)
    if (not isinstance(defects, list) or not 1 <= len(defects) <= 12
            or any(not isinstance(item, str) or not item.strip() or len(item) > 500 for item in defects)):
        raise Blocked("creative_feedback_invalid", "Feedback requires bounded concrete defects.")
    report = {"version": 1, "status": "NEEDS_REVISION", "authority": "NONE", "source": "user_feedback",
              "manifest": manifest, "manifest_sha256": c.digest(source), "image_sha256": data["output"]["sha256"],
              "defects": defects, "user_acceptance": "NOT_RECORDED", "generation_executed": False}
    path = write_versioned(source.parent, "creative-feedback", report)
    return {**report, "report": path.relative_to(root).as_posix()}


def revision(project: Path, manifest: str, settings: dict[str, Any]) -> dict[str, Any]:
    """Copy bound profiles and build a new Bundle; never execute or modify historical inputs."""
    c = executor()
    root, source, data = bound_manifest(project, manifest)
    allowed = {"prompt", "critical_features", "forbidden_misplacements", "defects", "prefer_edit"}
    if not isinstance(settings, dict) or set(settings) - allowed or not settings.get("defects"):
        raise Blocked("creative_repair_invalid", "A repair requires defects and allowlisted settings.")
    for field in ("critical_features", "forbidden_misplacements", "defects"):
        items = settings.get(field, [])
        if not isinstance(items, list) or len(items) > 12 or any(not isinstance(x, str) or not x.strip() or len(x) > 500 for x in items):
            raise Blocked("creative_repair_invalid", "Repair criteria must be bounded string lists.")
    if "prefer_edit" in settings and not isinstance(settings["prefer_edit"], bool):
        raise Blocked("creative_repair_invalid", "prefer_edit must be boolean.")
    prompt = settings.get("prompt")
    if prompt is not None and (not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 4000):
        raise Blocked("creative_repair_invalid", "Repair prompt exceeds its bound.")
    # Resolve only a manifest-bound Bundle: arbitrary caller Bundles cannot change the subject/provider.
    candidates = []
    for profile in data["profiles"]:
        if Path(profile["path"]).name == "CHARACTER_PROFILE.yaml":
            candidates = sorted((root / profile["path"]).parent.joinpath("bundles").glob("*.yaml"))
            break
    bundle_path = next((path for path in candidates if not path.is_symlink() and c.digest(path) == data.get("bundle_sha256")), None)
    if bundle_path is None:
        raise Blocked("creative_repair_source_missing", "The exact generated Bundle is unavailable.")
    _, old = c.read_bundle(root, bundle_path.relative_to(root).as_posix(), allow_existing_output=True)
    bundle = copy.deepcopy(old)
    bundle["provider"] = data.get("provider", old["provider"])
    chosen = "generate"
    reason = "selected_engine_has_no_edit_capability"
    capability = c.MFLUX_CAPABILITIES.get(bundle["model"]["id"], {}).get("edit")
    if settings.get("prefer_edit", True) and bundle["provider"] == "mflux_local" and capability:
        configured_command = bundle.get("mflux_executable")
        command = configured_command if isinstance(configured_command, str) and Path(configured_command).name == capability["command"] and Path(configured_command).is_file() and os.access(configured_command, os.X_OK) else shutil.which(str(capability["command"]))
        if command:
            chosen, reason = "edit", "installed_selected_model_edit_command"
            bundle["mflux_executable"] = command
    # ComfyUI edit needs a staged hash-verified input; do not stage or switch providers implicitly.
    bundle["operation"] = chosen
    bundle.pop("input_images", None)
    bundle["input_image"] = data["output"]["path"] if chosen == "edit" else None
    bundle["prompt"] = prompt or (old["prompt"] + "\nCorrect these defects while preserving all other identity/style details: " + "; ".join(settings["defects"]))
    if len(bundle["prompt"]) > 4000:
        raise Blocked("creative_repair_invalid", "Supply a shorter repair prompt.")
    parent = bundle_path.parent.parent
    lock_fd = os.open(parent / ".aips-creative-repair.lock", os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    locked = False
    try:
        deadline = execution_deadline.get()
        if deadline is None:
            c.lock_prepare_scope(lock_fd)
        else:
            timed_lock(lock_fd, deadline)
        locked = True
        for version in range(1, 10000):
            target = parent / f"repair-v{version}"
            if target.exists() or target.is_symlink():
                continue
            stage = Path(tempfile.mkdtemp(prefix=".repair-", dir=parent))
            try:
                (stage / "bundles").mkdir()
                for row in data["profiles"]:
                    original = c._profile_reference(root, row["path"], "profile")
                    if original.name not in {"CHARACTER_PROFILE.yaml", "STYLE_PROFILE.yaml"}:
                        continue
                    profile_bytes = original.read_bytes()
                    if "sha256:" + hashlib.sha256(profile_bytes).hexdigest() != row["sha256"]:
                        raise Blocked("creative_repair_source_changed", "A copied profile differs from its source hash.")
                    profile = yaml.safe_load(profile_bytes)
                    if original.name == "CHARACTER_PROFILE.yaml":
                        acceptance = profile.setdefault("acceptance_criteria", {})
                        for key in ("critical_features", "forbidden_misplacements"):
                            acceptance[key] = list(dict.fromkeys((acceptance.get(key) or []) + settings.get(key, [])))
                        if not acceptance.get("critical_features"):
                            acceptance["critical_features"] = profile.get("identity_features", [])
                    (stage / original.name).write_text(yaml.safe_dump(profile, sort_keys=False, allow_unicode=True), encoding="utf-8")
                relative = target.relative_to(root).as_posix()
                bundle["output_scope"] = relative + "/output"
                bundle["output_path"] = relative + "/output/image.png"
                # Validate the same fixed provider contract before publishing the revision.
                (stage / "bundles/CREATIVE_BUNDLE.yaml").write_text(yaml.safe_dump(bundle, sort_keys=False, allow_unicode=True), encoding="utf-8")
                lineage = {"version": 1, "parent_manifest": manifest, "parent_manifest_sha256": c.digest(source),
                           "parent_image_sha256": data["output"]["sha256"], "defects": settings["defects"],
                           "operation": chosen, "selection_reason": reason, "generation_executed": False}
                (stage / "REPAIR_LINEAGE.json").write_text(json.dumps(lineage, ensure_ascii=False, indent=2), encoding="utf-8")
                c.read_bundle(root, (stage / "bundles/CREATIVE_BUNDLE.yaml").relative_to(root).as_posix())
                _, fresh_source, fresh_data = bound_manifest(root, manifest)
                if c.digest(fresh_source) != lineage["parent_manifest_sha256"] or fresh_data != data:
                    raise Blocked("creative_repair_source_changed", "Repair source changed during preparation.")
                os.rename(stage, target)
                return {"status": "REPAIR_PREPARED", "bundle": relative + "/bundles/CREATIVE_BUNDLE.yaml",
                        "lineage": relative + "/REPAIR_LINEAGE.json", "operation": chosen,
                        "selection_reason": reason, "generation_executed": False, "overwrite": False}
            except BaseException:
                shutil.rmtree(stage, ignore_errors=True)
                raise
        raise Blocked("creative_version_exhausted", "No repair version remains.")
    finally:
        if locked:
            c.unlock_prepare_scope(lock_fd)
        os.close(lock_fd)


def compare(project: Path, before: str, after: str) -> dict[str, Any]:
    c = executor()
    root, source, a = bound_manifest(project, before)
    _, target, b = bound_manifest(project, after)
    character_path = next((row["path"] for row in b["profiles"] if Path(row["path"]).name == "CHARACTER_PROFILE.yaml"), None)
    lineage_path = c._profile_reference(root, character_path, "character profile").parent / "REPAIR_LINEAGE.json" if character_path else target.parent / "REPAIR_LINEAGE.json"
    if not lineage_path.is_file() or lineage_path.is_symlink():
        raise Blocked("creative_comparison_lineage_missing", "Comparison requires a repair lineage.")
    lineage = json.loads(lineage_path.read_text())
    if lineage.get("parent_manifest") != before or lineage.get("parent_manifest_sha256") != c.digest(source):
        raise Blocked("creative_comparison_lineage_mismatch", "The compared revision belongs to a different parent.")
    report = {"version": 1, "status": "READY_FOR_HUMAN_COMPARISON", "authority": "NONE",
              "before": {"manifest": before, "manifest_sha256": c.digest(source), "image": a["output"]},
              "after": {"manifest": after, "manifest_sha256": c.digest(target), "image": b["output"]},
              "defects": lineage["defects"], "human_review_required": True, "user_acceptance": "NOT_RECORDED"}
    path = write_versioned(target.parent, "creative-comparison", report)
    return {**report, "report": path.relative_to(root).as_posix()}


def quality_loop(project: Path, bundle_name: str, model: str, max_repairs: int, time_budget: int) -> dict[str, Any]:
    """Explicit opt-in orchestration. Each inference is counted, checked and bounded."""
    c = executor()
    if type(max_repairs) is not int or not 0 <= max_repairs <= 2 or type(time_budget) is not int or not 1 <= time_budget <= 3600:
        raise Blocked("creative_repair_budget_invalid", "Use 0-2 repairs and a 1-3600 second time budget.")
    if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", model):
        raise Blocked("visual_review_model_invalid", "Specify an installed local reviewer id before generation.")
    started = time.monotonic()
    deadline = started + time_budget
    root, initial = c.read_bundle(project, bundle_name)
    reservation = c.confined(root, bundle_name, exists=True).parent / (".quality-loop-" + c.digest(c.confined(root, bundle_name, exists=True)).removeprefix("sha256:") + ".json")
    if reservation.exists() or reservation.is_symlink():
        raise Blocked("creative_request_already_used", "This exact Bundle already reserved a quality loop; explicitly configure a new request.")
    profiles, _ = c.load_profile_documents(root, initial, c.confined(root, bundle_name, exists=True))
    checklist(profiles)
    # Check installed review capability BEFORE spending any generation attempt.
    inventory = json.loads(c.local_request(c.DEFAULT_OLLAMA_BASE_URL + "/api/tags", timeout=min(3, max(0.1, deadline - time.monotonic())), max_bytes=512 * 1024))
    if model not in {row.get("name") for row in inventory.get("models", []) if isinstance(row, dict)}:
        raise Blocked("visual_review_model_not_installed", "No image is generated without the requested installed reviewer.")
    attempts: list[dict[str, Any]] = []
    current = bundle_name
    previous: str | None = None
    decision = "UNVERIFIED"
    previous_defects: set[str] = set()
    stop = "repair_budget_exhausted"
    # Parent lock serializes all loop invocations for this source, including separate processes.
    lock_path = c.confined(root, bundle_name, exists=True).parent / ".quality-loop.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    locked = False
    deadline_token = execution_deadline.set(deadline)
    try:
        timed_lock(fd, deadline)
        locked = True
        try:
            c.atomic_manifest(reservation, {"version": 1, "status": "RESERVED", "bundle_sha256": c.digest(c.confined(root, bundle_name, exists=True)), "max_repairs": max_repairs, "time_budget_seconds": time_budget})
        except FileExistsError as exc:
            raise Blocked("creative_request_already_used", "A concurrent request already reserved this Bundle.") from exc
        for attempt in range(max_repairs + 1):
            remaining = time_budget - (time.monotonic() - started)
            if remaining < 4:
                stop = "time_budget_exhausted"
                break
            # No internal timeout retry may exceed the explicitly reserved inference count.
            c.read_bundle(root, current)
            configured = c.configure(root, current, {"timeout_seconds": max(1, math.floor(remaining - 3)), "max_retries": 0})
            current = configured["bundle"]
            try:
                preflight_result = subprocess.run([sys.executable, str(Path(c.__file__)), "preflight", "--project", str(root), "--bundle", current], capture_output=True, text=True, timeout=max(0.1, deadline - time.monotonic() - 2), check=False)
                ready = json.loads(preflight_result.stdout)
            except subprocess.TimeoutExpired:
                stop = "time_budget_exhausted"
                break
            if ready.get("status") != "READY":
                stop = ready.get("reason_code", "creative_preflight_failed")
                break
            remaining = deadline - time.monotonic()
            if remaining < 4:
                stop = "time_budget_exhausted"
                break
            configured = c.configure(root, current, {"timeout_seconds": max(1, math.floor(remaining - 3)), "max_retries": 0})
            current = configured["bundle"]
            row: dict[str, Any] = {"attempt": attempt + 1, "kind": "initial" if attempt == 0 else "repair", "status": "RESERVED"}
            attempts.append(row)
            try:
                generated = c.execute(root, current)
                row.update(status="GENERATED", manifest=generated["manifest"])
                remaining = time_budget - (time.monotonic() - started)
                if remaining < 4:
                    stop = "time_budget_exhausted"
                    break
                checked = c.review_assist(root, generated["manifest"], model, detailed=True, timeout=min(120, remaining - 3))
                report = json.loads(c.confined(root, checked["report"], exists=True).read_text())
                decision = report["machine_decision"]
                row.update(machine_decision=decision, report=checked["report"])
                if previous:
                    row["comparison"] = compare(root, previous, generated["manifest"])["report"]
                if decision != "DEFECTS_FOUND":
                    stop = "awaiting_human_review" if decision == "MATCHES_CRITERIA" else "uncertain_machine_review"
                    break
                if attempt == max_repairs:
                    break
                defect_ids = {item["id"] for item in report["checks"] if item["assessment"] == "DEFECT"}
                if previous_defects and defect_ids == previous_defects:
                    stop = "repeated_defect_requires_strategy"
                    break
                previous_defects = defect_ids
                defects = [item["evidence"][:240] + " Correction: " + item["suggestion"][:240] for item in report["checks"] if item["assessment"] == "DEFECT"]
                previous = generated["manifest"]
                prepared = revision(root, previous, {"defects": defects})
                current = prepared["bundle"]
            except Blocked as exc:
                row.update(status="BLOCKED", reason_code=exc.reason_code)
                stop = exc.reason_code
                break
        result = {"version": 1, "status": "READY_FOR_HUMAN_REVIEW" if decision == "MATCHES_CRITERIA" and stop == "awaiting_human_review" else "NEEDS_ATTENTION",
                  "reason_code": stop, "deliverable_count": 1, "generation_attempts": len(attempts),
                  "repair_attempts": max(0, len(attempts) - 1), "accepted_count": 0, "attempts": attempts,
                  "max_repairs": max_repairs, "time_budget_seconds": time_budget,
                  "elapsed_ms": round((time.monotonic() - started) * 1000), "user_acceptance": "NOT_RECORDED",
                  "human_review_required": True, "external_image_egress": False,
                  "next_action": "Inspect the latest image and comparison. If defects persist, use a supported local edit or explicitly authorize a different model; no automatic scope expansion."}
        path = write_versioned(lock_path.parent, "creative-quality-loop", result)
        return {**result, "report": path.relative_to(root).as_posix()}
    finally:
        execution_deadline.reset(deadline_token)
        if locked:
            c.unlock_prepare_scope(fd)
        os.close(fd)

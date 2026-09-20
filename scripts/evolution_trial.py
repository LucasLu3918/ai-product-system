#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fnmatch
import json
from pathlib import Path
import shlex
import subprocess
from typing import Any

import yaml

from evolution_analysis import canonical_digest
from evolution_decision import validate_decision


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_yaml(path: str | Path) -> dict[str, Any]:
    value = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a mapping")
    return value


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if config.get("version") != 1:
        errors.append("trial config version must be 1")
    selection = config.get("selection") or {}
    if selection.get("default") != "auto":
        errors.append("trial selection.default must be auto")
    if selection.get("fallback") != "handoff":
        errors.append("trial selection.fallback must be handoff")
    if selection.get("allowed") != ["auto", "openai-codex-action", "handoff"]:
        errors.append("trial selection.allowed must contain auto/openai-codex-action/handoff")
    execution = config.get("execution") or {}
    if execution.get("isolation_mode") != "worktree":
        errors.append("trial isolation_mode must be worktree")
    if execution.get("permission_profile") != ":workspace":
        errors.append("trial permission_profile must be :workspace")
    handoff = config.get("handoff") or {}
    if handoff.get("enabled") is not True:
        errors.append("trial handoff must be enabled")
    if handoff.get("state") != "TRIAL_HANDOFF_READY":
        errors.append("trial handoff state must be TRIAL_HANDOFF_READY")
    if handoff.get("credential_required") is not False:
        errors.append("trial handoff must not require a provider credential")
    if handoff.get("deterministic_validation_required") is not True:
        errors.append("trial handoff must require deterministic validation")
    limits = config.get("limits") or {}
    for key in ("max_changed_files", "max_diff_lines"):
        value = limits.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            errors.append(f"limits.{key} must be a positive integer")
    forbidden = config.get("forbidden_paths")
    if not isinstance(forbidden, list) or not forbidden:
        errors.append("forbidden_paths must be a non-empty list")
    authority = config.get("authority") or {}
    for key in ("publish_code", "create_remote_branch_or_pr", "merge", "release"):
        if authority.get(key) is not False:
            errors.append(f"authority.{key} must be false")
    return errors


def validate_trial_decision(decision_doc: dict[str, Any], current_revision: str) -> dict[str, Any]:
    errors = validate_decision(decision_doc)
    if errors:
        raise ValueError("invalid Human Decision: " + "; ".join(errors))
    decision = decision_doc["decision"]
    if decision.get("decision") != "TRIAL":
        raise ValueError("controlled trial requires a TRIAL Human Decision")
    if decision.get("baseline_status") != "CURRENT":
        raise ValueError("controlled trial requires CURRENT decision baseline")
    if decision.get("baseline_repository_revision") != current_revision:
        raise ValueError("controlled trial baseline revision is stale")
    if not decision.get("approved_paths"):
        raise ValueError("controlled trial requires approved_paths")
    return decision


def build_plan(
    decision_doc: dict[str, Any],
    config: dict[str, Any],
    *,
    current_revision: str,
) -> dict[str, Any]:
    config_errors = validate_config(config)
    if config_errors:
        raise ValueError("invalid trial config: " + "; ".join(config_errors))
    decision = validate_trial_decision(decision_doc, current_revision)
    candidate = str(decision["candidate_id"])
    suffix = candidate.removeprefix("EVO-").lower()
    trial = {
        "trial_id": f"TRIAL-{candidate}",
        "candidate_id": candidate,
        "signal_fingerprint": decision["signal_fingerprint"],
        "decision_fingerprint": decision_doc["decision_fingerprint"],
        "baseline_repository_revision": current_revision,
        "approved_scope": decision["approved_scope"],
        "approved_paths": list(decision["approved_paths"]),
        "isolation_mode": "worktree",
        "boundary_id": f"evo-{suffix}",
        "status": "PLANNED",
        "max_changed_files": int(config["limits"]["max_changed_files"]),
        "max_diff_lines": int(config["limits"]["max_diff_lines"]),
        "forbidden_paths": list(config["forbidden_paths"]),
    }
    core = {"version": 1, "trial": trial}
    core["trial_fingerprint"] = canonical_digest(core)
    core["authority"] = {
        "code_publication_authorized": False,
        "remote_branch_or_pr_authorized": False,
        "merge_authorized": False,
        "release_authorized": False,
        "human_adoption_decision_required": True,
    }
    return core


def build_handoff(plan: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    config_errors = validate_config(config)
    if config_errors:
        raise ValueError("invalid trial config: " + "; ".join(config_errors))
    trial = dict(plan.get("trial") or {})
    if not trial or plan.get("trial_fingerprint") is None:
        raise ValueError("trial handoff requires a valid trial plan")
    handoff_cfg = config["handoff"]
    payload = {
        "version": 1,
        "state": "TRIAL_HANDOFF_READY",
        "binding": {
            "trial_fingerprint": plan["trial_fingerprint"],
            "baseline_repository_revision": trial.get("baseline_repository_revision"),
            "decision_fingerprint": trial.get("decision_fingerprint"),
        },
        "trial": trial,
        "execution_contract": {
            "provider_neutral": True,
            "credential_required": False,
            "prompt_path": handoff_cfg["prompt_path"],
            "isolation_required": True,
            "required_isolation_mode": trial.get("isolation_mode"),
            "validation_command": str((config.get("validation") or {}).get("command") or ""),
            "deterministic_validation_required": True,
            "external_executor_may_claim_pass": False,
        },
        "authority": {
            "trial_execution_authorized": True,
            "code_publication_authorized": False,
            "remote_branch_or_pr_authorized": False,
            "merge_authorized": False,
            "release_authorized": False,
            "human_adoption_decision_required": True,
        },
    }
    payload["handoff_fingerprint"] = canonical_digest({
        "state": payload["state"],
        "binding": payload["binding"],
        "trial": payload["trial"],
        "execution_contract": payload["execution_contract"],
    })
    return payload


def validate_handoff(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("version") != 1 or doc.get("state") != "TRIAL_HANDOFF_READY":
        errors.append("trial handoff must be version 1 TRIAL_HANDOFF_READY")
    binding = doc.get("binding") or {}
    trial = doc.get("trial") or {}
    execution = doc.get("execution_contract") or {}
    if binding.get("trial_fingerprint") is None or binding.get("decision_fingerprint") != trial.get("decision_fingerprint"):
        errors.append("trial handoff binding mismatch")
    if binding.get("baseline_repository_revision") != trial.get("baseline_repository_revision"):
        errors.append("trial handoff baseline mismatch")
    if execution.get("provider_neutral") is not True or execution.get("credential_required") is not False:
        errors.append("trial handoff must remain provider-neutral and credential-free")
    if execution.get("isolation_required") is not True or execution.get("required_isolation_mode") != "worktree":
        errors.append("trial handoff must preserve worktree isolation requirement")
    if execution.get("deterministic_validation_required") is not True:
        errors.append("trial handoff must require deterministic validation")
    if execution.get("external_executor_may_claim_pass") is not False:
        errors.append("external executor must not be allowed to self-assert PASS")
    authority = doc.get("authority") or {}
    for key in ("code_publication_authorized", "remote_branch_or_pr_authorized", "merge_authorized", "release_authorized"):
        if authority.get(key) is not False:
            errors.append(f"handoff authority.{key} must be false")
    if authority.get("human_adoption_decision_required") is not True:
        errors.append("trial handoff must preserve Human adoption decision")
    expected = canonical_digest({
        "state": doc.get("state"),
        "binding": binding,
        "trial": trial,
        "execution_contract": execution,
    })
    if doc.get("handoff_fingerprint") != expected:
        errors.append("handoff_fingerprint mismatch")
    return errors


def handoff_markdown(doc: dict[str, Any]) -> str:
    errors = validate_handoff(doc)
    if errors:
        raise ValueError("invalid trial handoff: " + "; ".join(errors))
    trial = doc["trial"]
    execution = doc["execution_contract"]
    return "\n".join([
        f"## Controlled Trial Handoff — {trial.get('candidate_id')}",
        "",
        "- State: **TRIAL_HANDOFF_READY**",
        f"- Baseline: `{trial.get('baseline_repository_revision')}`",
        f"- Trial fingerprint: `{doc['binding'].get('trial_fingerprint')}`",
        f"- Handoff fingerprint: `{doc.get('handoff_fingerprint')}`",
        f"- Approved scope: {trial.get('approved_scope')}",
        f"- Required isolation: `{execution.get('required_isolation_mode')}`",
        f"- Deterministic validation: `{execution.get('validation_command')}`",
        "",
        "A Human-selected compatible Agent may execute this exact bounded Trial contract. "
        "The external executor cannot self-assert PASS. PASS/FAIL remains valid only after "
        "AIPS deterministic scope/diff/validation evidence is produced.",
        "",
        "**Approved paths**",
        "",
        *[f"- `{path}`" for path in trial.get("approved_paths") or []],
        "",
        "<!-- AIPS_EVOLUTION_TRIAL_HANDOFF_START -->",
        "```yaml",
        yaml.safe_dump(doc, sort_keys=False, allow_unicode=True).rstrip(),
        "```",
        "<!-- AIPS_EVOLUTION_TRIAL_HANDOFF_END -->",
        "",
    ])


def _status_paths(worktree: Path) -> list[str]:
    result = git(worktree, "status", "--porcelain=v1", "--untracked-files=all")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git status failed")
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        raw = line[3:].strip()
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1].strip()
        if raw.startswith('"') and raw.endswith('"'):
            raw = raw[1:-1]
        raw = raw.replace("\\", "/")
        if raw not in paths:
            paths.append(raw)
    return paths


def _matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _diff_lines(worktree: Path) -> int:
    result = git(worktree, "diff", "HEAD", "--numstat")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git diff --numstat failed")
    total = 0
    tracked: set[str] = set()
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        add, delete, path = parts[0], parts[1], parts[-1]
        tracked.add(path)
        if add.isdigit():
            total += int(add)
        if delete.isdigit():
            total += int(delete)
    for path in _status_paths(worktree):
        if path in tracked:
            continue
        target = worktree / path
        if target.is_file():
            try:
                total += min(len(target.read_text(encoding="utf-8").splitlines()), 2000)
            except (UnicodeDecodeError, OSError):
                total += 1
    return total


def _head_revision(worktree: Path) -> str:
    result = git(worktree, "rev-parse", "HEAD")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git rev-parse failed")
    return result.stdout.strip()


def evaluate(
    plan: dict[str, Any],
    config: dict[str, Any],
    *,
    worktree: Path,
    agent_outcome: str,
    started_at: str,
    agent_summary: str = "",
) -> dict[str, Any]:
    config_errors = validate_config(config)
    if config_errors:
        raise ValueError("invalid trial config: " + "; ".join(config_errors))
    trial = plan.get("trial") or {}
    violations: list[str] = []
    changed_files = _status_paths(worktree)
    diff_lines = _diff_lines(worktree)

    if _head_revision(worktree) != trial.get("baseline_repository_revision"):
        violations.append("trial agent must not create commits")

    approved = list(trial.get("approved_paths") or [])
    forbidden = list(trial.get("forbidden_paths") or [])
    for path in changed_files:
        if _matches(path, forbidden):
            violations.append(f"forbidden path changed: {path}")
        if not _matches(path, approved):
            violations.append(f"path outside approved trial scope: {path}")

    if len(changed_files) > int(trial.get("max_changed_files") or 0):
        violations.append("changed-file limit exceeded")
    if diff_lines > int(trial.get("max_diff_lines") or 0):
        violations.append("diff-line limit exceeded")

    validation_command = str((config.get("validation") or {}).get("command") or "").strip()
    validation_exit_code: int | None = None
    if validation_command and not violations:
        command = shlex.split(validation_command)
        try:
            proc = subprocess.run(
                command,
                cwd=worktree,
                capture_output=True,
                text=True,
                timeout=180,
            )
            validation_exit_code = proc.returncode
            if proc.returncode != 0:
                violations.append("repository validation failed")
        except subprocess.TimeoutExpired:
            validation_exit_code = 124
            violations.append("repository validation timed out")

    status = "PASS"
    reason = "bounded trial completed within the Human-approved scope"
    if violations:
        status = "FAIL"
        reason = "trial violated scope, limits, commit boundary, or validation requirements"
    if agent_outcome != "success":
        status = "BLOCKED"
        reason = f"trial agent outcome: {agent_outcome}"

    result = {
        "version": 1,
        "trial": dict(trial),
        "result": {
            "status": status,
            "reason": reason,
            "changed_files": changed_files,
            "changed_file_count": len(changed_files),
            "diff_lines": diff_lines,
            "validation_command": validation_command,
            "validation_exit_code": validation_exit_code,
            "violations": violations,
            "agent_outcome": agent_outcome,
            "agent_summary": agent_summary.strip()[:6000],
            "started_at": started_at,
            "completed_at": utc_now(),
        },
    }
    result["trial_fingerprint"] = canonical_digest(
        {"trial": result["trial"], "result": result["result"]}
    )
    result["authority"] = {
        "code_publication_authorized": False,
        "remote_branch_or_pr_authorized": False,
        "merge_authorized": False,
        "release_authorized": False,
        "human_adoption_decision_required": True,
    }
    return result


def blocked_result(plan: dict[str, Any], reason: str) -> dict[str, Any]:
    now = utc_now()
    result = {
        "version": 1,
        "trial": dict(plan.get("trial") or {}),
        "result": {
            "status": "BLOCKED",
            "reason": reason.strip(),
            "changed_files": [],
            "changed_file_count": 0,
            "diff_lines": 0,
            "validation_command": "",
            "validation_exit_code": None,
            "violations": [],
            "agent_outcome": "not_started",
            "agent_summary": "",
            "started_at": now,
            "completed_at": now,
        },
    }
    result["trial_fingerprint"] = canonical_digest(
        {"trial": result["trial"], "result": result["result"]}
    )
    result["authority"] = {
        "code_publication_authorized": False,
        "remote_branch_or_pr_authorized": False,
        "merge_authorized": False,
        "release_authorized": False,
        "human_adoption_decision_required": True,
    }
    return result


def validate_result(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("version") != 1:
        errors.append("trial result version must be 1")
    trial = doc.get("trial") or {}
    result = doc.get("result") or {}
    if result.get("status") not in {"PASS", "FAIL", "BLOCKED"}:
        errors.append("result.status must be PASS, FAIL or BLOCKED")
    if result.get("status") == "PASS" and result.get("violations"):
        errors.append("PASS trial must have no violations")
    authority = doc.get("authority") or {}
    for key in (
        "code_publication_authorized",
        "remote_branch_or_pr_authorized",
        "merge_authorized",
        "release_authorized",
    ):
        if authority.get(key) is not False:
            errors.append(f"authority.{key} must be false")
    if authority.get("human_adoption_decision_required") is not True:
        errors.append("Human adoption decision must remain required")
    expected = canonical_digest({"trial": trial, "result": result})
    if doc.get("trial_fingerprint") != expected:
        errors.append("trial_fingerprint mismatch")
    return errors


def markdown(doc: dict[str, Any]) -> str:
    trial = doc["trial"]
    result = doc["result"]
    lines = [
        f"## Controlled Trial — {trial.get('candidate_id')}",
        "",
        f"- Status: **{result.get('status')}**",
        f"- Baseline: `{trial.get('baseline_repository_revision')}`",
        f"- Approved scope: {trial.get('approved_scope')}",
        f"- Changed files: {result.get('changed_file_count')}",
        f"- Diff lines: {result.get('diff_lines')}",
        f"- Validation exit: `{result.get('validation_exit_code')}`",
        f"- Agent outcome: `{result.get('agent_outcome')}`",
        "",
        f"**Reason:** {result.get('reason')}",
        "",
    ]
    if trial.get("approved_paths"):
        lines += ["**Approved paths**", ""]
        lines += [f"- `{path}`" for path in trial["approved_paths"]]
        lines.append("")
    if result.get("changed_files"):
        lines += ["**Observed trial changes**", ""]
        lines += [f"- `{path}`" for path in result["changed_files"]]
        lines.append("")
    if result.get("agent_summary"):
        lines += ["**Trial agent summary**", "", result["agent_summary"], ""]
    if result.get("violations"):
        lines += ["**Violations / blockers**", ""]
        lines += [f"- {item}" for item in result["violations"]]
        lines.append("")
    lines += [
        "Trial changes existed only in the isolated ephemeral workspace. "
        "This report does not authorize adoption, remote publication, merge or release.",
        "",
        "<!-- AIPS_EVOLUTION_TRIAL_START -->",
        "```yaml",
        yaml.safe_dump(doc, sort_keys=False, allow_unicode=True).rstrip(),
        "```",
        "<!-- AIPS_EVOLUTION_TRIAL_END -->",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan")
    plan.add_argument("--decision", required=True)
    plan.add_argument("--config", required=True)
    plan.add_argument("--current-revision", required=True)
    plan.add_argument("--output", required=True)

    handoff = sub.add_parser("handoff")
    handoff.add_argument("--plan", required=True)
    handoff.add_argument("--config", required=True)
    handoff.add_argument("--output", required=True)

    handoff_validate = sub.add_parser("handoff-validate")
    handoff_validate.add_argument("handoff_file")

    handoff_render = sub.add_parser("handoff-markdown")
    handoff_render.add_argument("handoff_file")
    handoff_render.add_argument("--output", required=True)

    evaluate_cmd = sub.add_parser("evaluate")
    evaluate_cmd.add_argument("--plan", required=True)
    evaluate_cmd.add_argument("--config", required=True)
    evaluate_cmd.add_argument("--worktree", required=True)
    evaluate_cmd.add_argument("--agent-outcome", required=True)
    evaluate_cmd.add_argument("--started-at", required=True)
    evaluate_cmd.add_argument("--agent-summary-file")
    evaluate_cmd.add_argument("--output", required=True)

    blocked = sub.add_parser("blocked")
    blocked.add_argument("--plan", required=True)
    blocked.add_argument("--reason", required=True)
    blocked.add_argument("--output", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("trial_file")

    render = sub.add_parser("markdown")
    render.add_argument("trial_file")
    render.add_argument("--output", required=True)

    args = parser.parse_args()
    if args.command == "plan":
        doc = build_plan(
            load_yaml(args.decision),
            load_yaml(args.config),
            current_revision=args.current_revision,
        )
        Path(args.output).write_text(
            yaml.safe_dump(doc, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        return 0
    if args.command == "handoff":
        doc = build_handoff(load_yaml(args.plan), load_yaml(args.config))
        errors = validate_handoff(doc)
        if errors:
            raise ValueError("generated invalid trial handoff: " + "; ".join(errors))
        Path(args.output).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return 0
    if args.command == "handoff-validate":
        errors = validate_handoff(load_yaml(args.handoff_file))
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        return 0 if not errors else 1
    if args.command == "handoff-markdown":
        Path(args.output).write_text(handoff_markdown(load_yaml(args.handoff_file)), encoding="utf-8")
        return 0
    if args.command == "evaluate":
        doc = evaluate(
            load_yaml(args.plan),
            load_yaml(args.config),
            worktree=Path(args.worktree),
            agent_outcome=args.agent_outcome,
            started_at=args.started_at,
            agent_summary=(
                Path(args.agent_summary_file).read_text(encoding="utf-8")
                if args.agent_summary_file and Path(args.agent_summary_file).exists()
                else ""
            ),
        )
        Path(args.output).write_text(
            yaml.safe_dump(doc, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        return 0
    if args.command == "blocked":
        doc = blocked_result(load_yaml(args.plan), args.reason)
        Path(args.output).write_text(
            yaml.safe_dump(doc, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        return 0

    doc = load_yaml(args.trial_file)
    errors = validate_result(doc)
    if args.command == "validate":
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        return 0 if not errors else 1
    if errors:
        raise ValueError("invalid trial result: " + "; ".join(errors))
    Path(args.output).write_text(markdown(doc), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "project_diagnostics.py"
sys.path.insert(0, str(ROOT / "scripts"))
import project_diagnostics
from project_diagnostics import _harness_check, _intelligence_check, _run_json


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(project: Path, fmt: str = "json", *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(project), "--runtime", "unknown", "--format", fmt],
        cwd=project if project.is_dir() else ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="aips-project-diagnostics-") as temp:
        base = Path(temp)
        project = base / "project"
        project.mkdir()
        (project / "README.md").write_text("fixture\n", encoding="utf-8")
        env = dict(os.environ)
        env.update({"XDG_CONFIG_HOME": str(base / "config"), "XDG_CACHE_HOME": str(base / "cache")})
        sentinel = "DIAGNOSTICS_SECRET_SENTINEL"
        env["AIPS_DIAGNOSTICS_TEST_SENTINEL"] = sentinel
        before = sorted(str(path.relative_to(project)) for path in project.rglob("*"))

        result = run(project, env=env)
        require(result.returncode == 0, "valid project diagnostics should return a report")
        data = json.loads(result.stdout)
        require(data["schema_version"] == 1 and data["read_only"] is True, "report contract/read-only marker missing")
        require(data["status"] == "NEEDS_ATTENTION", "missing Project Intelligence should need attention")
        pi = next(item for item in data["checks"] if item["id"] == "project_intelligence")
        require(pi["reason_code"] == "intelligence_missing", "missing PI reason code is unstable")
        require("bootstrap" in (pi["next_action"] or ""), "missing PI recovery action must be actionable")
        require([item["action"] for item in pi["next_actions"]] == ["bootstrap", "complete_required_topics", "finalize", "verify"], "missing PI next-action sequence is incomplete")
        require("UNVERIFIED" in " ".join(data["limitations"]), "native runtime limits must remain explicit")
        require(sentinel not in result.stdout, "environment content leaked into report")
        after = sorted(str(path.relative_to(project)) for path in project.rglob("*"))
        require(before == after and not (project / ".ai").exists(), "diagnostics must not write or attach the project")

        yaml_result = run(project, "yaml", env=env)
        require(yaml_result.returncode == 0, "YAML format should succeed")
        import yaml
        yaml_data = yaml.safe_load(yaml_result.stdout)
        require(yaml_data["schema_version"] == 1, "YAML report contract is invalid")

        partial = _intelligence_check({"exists": True, "state": {"readiness": "PARTIAL"}, "freshness": {"status": "CURRENT"}}, None, project)
        require(partial["reason_code"] == "intelligence_partial" and "finalize" in (partial["next_action"] or ""), "partial PI recovery guidance missing")
        require(partial["next_actions"][0]["action"] == "inspect_missing_topics", "partial recovery must begin with read-only inspection")
        stale = _intelligence_check({"exists": True, "state": {"readiness": "READY"}, "freshness": {"status": "STALE"}}, None, project)
        require(stale["reason_code"] == "intelligence_stale" and "refresh-plan" in (stale["next_action"] or ""), "stale PI recovery guidance missing")
        require(stale["next_actions"][1]["when"] == "使用者審閱刷新範圍並決定更新後", "stale recovery must retain user decision boundary")
        blocked = _intelligence_check({"exists": True, "state": {"readiness": "BLOCKED"}, "freshness": {"status": "BLOCKED"}}, None, project)
        require(blocked["reason_code"] == "intelligence_blocked" and blocked["next_actions"][0]["action"] == "inspect_block_reason", "blocked PI must guide inspection without bypassing its gate")
        require(all("bootstrap" not in item.get("command", "") and "refresh" not in item.get("command", "") for item in blocked["next_actions"]), "blocked PI must not recommend speculative repair")
        hostile = _harness_check({"runtime": {"id": "codex", "detected": True, "adapter_status": sentinel, "capability": sentinel}}, None, project, "codex")
        require(hostile["reason_code"] == "adapter_state_unrecognized" and sentinel not in json.dumps(hostile), "unrecognized adapter values must be allowlisted")
        malformed = _harness_check({"runtime": {"id": "codex", "detected": True, "adapter_status": "AUTOMATIC", "capability": []}}, None, project, "codex")
        require(malformed["reason_code"] == "adapter_state_unrecognized", "malformed adapter capability must not crash diagnostics")
        _failed_report, failure_code = _run_json([sys.executable, "-c", "import sys; print('LEAK'); sys.exit(1)"], cwd=project)
        require(failure_code == "diagnostic_unavailable", "failed child command should map to a stable reason code")
        original_timeout = project_diagnostics.MAX_CHILD_SECONDS
        project_diagnostics.MAX_CHILD_SECONDS = 0.1
        try:
            _timed_report, timeout_code = _run_json([sys.executable, "-c", "import time; time.sleep(1)"], cwd=project)
        finally:
            project_diagnostics.MAX_CHILD_SECONDS = original_timeout
        require(timeout_code == "diagnostic_timeout", "slow child command should be bounded by timeout")

        text_result = run(project, "text", env=env)
        require(text_result.returncode == 0 and "AIPS Project Diagnostics" in text_result.stdout, "text format missing")

        invalid = run(base / "missing", env=env)
        require(invalid.returncode == 2, "missing project path should be rejected")
        require(sentinel not in invalid.stdout + invalid.stderr, "invalid-path error leaked environment data")
    print("Project diagnostics lifecycle passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

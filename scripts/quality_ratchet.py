"""Enforce the existing Ruff debt ceiling without imposing a new target."""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def finding_key(item: dict, root: Path = ROOT) -> tuple[str, str, str, str, str]:
    raw_path = str(item.get("filename") or "")
    try:
        path = Path(raw_path).resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        path = Path(raw_path).as_posix()
    return (path, str(item.get("code") or ""), str(item.get("name") or ""), str(item.get("message") or ""), str(item.get("cell") or ""))


def added_touched_findings(current: list[dict], previous: list[dict], touched: set[str]) -> list[dict]:
    old = Counter(finding_key(item) for item in previous)
    additions: list[dict] = []
    for item in current:
        key = finding_key(item)
        if key[0] not in touched:
            continue
        if old[key]:
            old[key] -= 1
        else:
            additions.append(item)
    return additions


def summarize(findings: list[dict]) -> dict:
    rules: dict[str, Counter] = defaultdict(Counter)
    modules: dict[str, Counter] = defaultdict(Counter)
    for item in findings:
        fixable = bool(item.get("fix"))
        code = str(item.get("code") or "UNKNOWN")
        path = finding_key(item)[0]
        rules[code]["findings"] += 1
        rules[code]["fixable" if fixable else "manual"] += 1
        modules[path]["findings"] += 1
        modules[path]["fixable" if fixable else "manual"] += 1
    return {
        "total": len(findings),
        "fixable": sum(1 for item in findings if item.get("fix")),
        "manual": sum(1 for item in findings if not item.get("fix")),
        "by_rule": {key: dict(value) for key, value in sorted(rules.items())},
        "by_module": {key: dict(value) for key, value in sorted(modules.items())},
    }


def module_debt_violations(
    report: dict,
    budgets: dict[str, dict],
    *,
    touched: set[str] | None = None,
    previous_counts: dict[str, int] | None = None,
) -> list[str]:
    modules = report.get("by_module") or {}
    violations: list[str] = []
    for path, budget in sorted(budgets.items()):
        current = int((modules.get(path) or {}).get("findings", 0))
        allowed = int(budget.get("current_findings", -1))
        next_target = int(budget.get("next_target", -1))
        if allowed < 0 or next_target < 0 or next_target >= allowed:
            violations.append(f"{path}: module ledger must define a lower non-negative next_target")
        if current > allowed:
            violations.append(f"{path}: {current} findings exceed recorded current_findings {allowed}")
        if touched and path in touched and previous_counts and path in previous_counts:
            previous = previous_counts[path]
            if previous > 0:
                required = max(1, math.floor(previous * 0.9))
                if current > required:
                    violations.append(f"{path}: {current} findings exceed 10% burn-down target {required} from base {previous}")
    return violations


def run_ruff(files: list[str] | None = None, *, stdin_text: str | None = None, stdin_filename: str | None = None) -> tuple[list[dict] | None, str]:
    command = [sys.executable, "-m", "ruff", "check", "--no-cache", "--output-format=json"]
    if stdin_text is not None and stdin_filename:
        command.extend(("--stdin-filename", stdin_filename, "-"))
    else:
        command.extend(files or ["scripts", "tests"])
    result = subprocess.run(command, cwd=ROOT, input=stdin_text, capture_output=True, text=True, check=False)
    if result.returncode not in (0, 1):
        return None, result.stderr.strip() or "Ruff could not produce a debt report"
    try:
        return json.loads(result.stdout), ""
    except json.JSONDecodeError:
        return None, "Ruff returned invalid JSON"


def changed_python_paths(base: str) -> set[str] | None:
    exists = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", base + "^{commit}"], capture_output=True, text=True, check=False)
    if exists.returncode:
        return None
    paths: set[str] = set()
    for command in (
        ["git", "-C", str(ROOT), "diff", "--name-only", base + "...HEAD"],
        ["git", "-C", str(ROOT), "diff", "--name-only", "HEAD"],
        ["git", "-C", str(ROOT), "ls-files", "--others", "--exclude-standard"],
    ):
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode:
            return None
        paths.update(line.strip() for line in result.stdout.splitlines() if line.strip())
    return {path for path in paths if path.endswith(".py") and path.startswith(("scripts/", "tests/"))}


def previous_file_findings(base: str, path: str) -> list[dict] | None:
    result = subprocess.run(["git", "-C", str(ROOT), "show", f"{base}:{path}"], capture_output=True, text=True, check=False)
    if result.returncode:
        return []
    findings, _ = run_ruff(stdin_text=result.stdout, stdin_filename=path)
    return None if findings is None else findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "report"))
    parser.add_argument("--config", type=Path, default=ROOT / "config/quality-ratchet.yaml")
    parser.add_argument("--base", default=os.environ.get("AIPS_QUALITY_BASE", "origin/main"))
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
    baseline = int((config.get("ruff") or {}).get("baseline_findings", -1))
    findings, error = run_ruff()
    if findings is None:
        print(error, file=sys.stderr)
        return 2
    count = len(findings)
    report = summarize(findings)
    if args.command == "report":
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    print(f"Ruff findings: {count}; allowed baseline: {baseline}; auto-fixable: {report['fixable']}; manual: {report['manual']}")
    if count > baseline:
        print("QUALITY_RATCHET_BLOCKED: Ruff findings increased beyond the established baseline", file=sys.stderr)
        return 1
    if (config.get("touched_code") or {}).get("policy") == "no_new_findings":
        touched = changed_python_paths(args.base)
        if touched is None:
            print(f"QUALITY_RATCHET_BLOCKED: cannot resolve touched-code baseline from {args.base}", file=sys.stderr)
            return 2
        additions: list[dict] = []
        for path in sorted(touched):
            previous = previous_file_findings(args.base, path)
            if previous is None:
                print(f"QUALITY_RATCHET_BLOCKED: cannot produce base Ruff evidence for {path}", file=sys.stderr)
                return 2
            additions.extend(added_touched_findings(findings, previous, {path}))
        if additions:
            details = ", ".join(f"{finding_key(item)[0]}:{item.get('code')}" for item in additions)
            print(f"QUALITY_RATCHET_BLOCKED: new Ruff findings in touched code: {details}", file=sys.stderr)
            return 1
        print(f"Touched-code Ruff findings: no growth across {len(touched)} Python files (base {args.base})")
        budgets = (config.get("ruff") or {}).get("module_budgets") or {}
        previous_counts: dict[str, int] = {}
        for path in budgets:
            if path not in touched:
                continue
            previous = previous_file_findings(args.base, path)
            if previous is None:
                print(f"QUALITY_RATCHET_BLOCKED: cannot produce module debt baseline for {path}", file=sys.stderr)
                return 2
            previous_counts[path] = len(previous)
        violations = module_debt_violations(report, budgets, touched=touched, previous_counts=previous_counts)
        if violations:
            print("QUALITY_RATCHET_BLOCKED: " + "; ".join(violations), file=sys.stderr)
            return 1
        if budgets:
            print(f"Module Ruff debt: {len(budgets)} tracked budgets; changed facades must reduce findings by at least 10%")
    mypy = config.get("mypy") or {}
    modules = [str(path) for path in mypy.get("modules") or []]
    with tempfile.TemporaryDirectory(prefix="aips-quality-mypy-") as cache_dir:
        type_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                "--cache-dir",
                cache_dir,
                "--follow-imports",
                str(mypy.get("follow_imports", "skip")),
                "--ignore-missing-imports",
                *modules,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    type_errors = sum(": error:" in line for line in type_result.stdout.splitlines())
    print(f"Mypy findings: {type_errors}; allowed baseline: {mypy.get('maximum_findings')}")
    if type_result.returncode not in (0, 1) or type_errors > int(mypy.get("maximum_findings", -1)):
        print(type_result.stdout.strip() or type_result.stderr.strip(), file=sys.stderr)
        print("QUALITY_RATCHET_BLOCKED: selected-module mypy debt increased", file=sys.stderr)
        return 1
    print("QUALITY_RATCHET_PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

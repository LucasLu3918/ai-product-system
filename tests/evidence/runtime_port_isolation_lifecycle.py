#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
ISOLATION = ROOT / "scripts" / "execution_isolation.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, env=env, capture_output=True, text=True)


def json_run(args: list[str], env: dict[str, str]) -> dict:
    result = run(args, env)
    require(result.returncode == 0, f"command failed: {args}: {result.stdout} {result.stderr}")
    return json.loads(result.stdout)


def git(project: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=project, check=True, capture_output=True, text=True)


def create(project: Path, env: dict[str, str], isolation_id: str, boundary: str) -> dict:
    return json_run(
        [
            sys.executable,
            str(ISOLATION),
            "create",
            "--project",
            str(project),
            "--id",
            isolation_id,
            "--boundary",
            boundary,
            "--format",
            "json",
        ],
        env,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        project = base / "project"
        config = base / "config"
        project.mkdir()
        (project / "README.md").write_text("base\n", encoding="utf-8")
        git(project, "init", "-q")
        git(project, "config", "user.email", "aips@example.invalid")
        git(project, "config", "user.name", "AIPS Test")
        git(project, "add", "README.md")
        git(project, "commit", "-qm", "initial")

        env = dict(os.environ)
        env["XDG_CONFIG_HOME"] = str(config)

        iso_a = create(project, env, "agent-a", "frontend-a")
        iso_b = create(project, env, "agent-b", "frontend-b")
        require(Path(iso_a["path"]).is_dir() and Path(iso_b["path"]).is_dir(), "parallel worktrees missing")

        occupied = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        occupied.bind(("127.0.0.1", 0))
        occupied.listen(1)
        occupied_port = occupied.getsockname()[1]
        try:
            dev = json_run(
                [
                    sys.executable,
                    str(ISOLATION),
                    "runtime-lease",
                    "--project",
                    str(project),
                    "--id",
                    "agent-a",
                    "--port",
                    "dev",
                    "--preferred",
                    str(occupied_port),
                    "--expose",
                    "PORT",
                    "--port-start",
                    "42000",
                    "--port-end",
                    "42100",
                    "--format",
                    "json",
                ],
                env,
            )
        finally:
            occupied.close()
        require(dev["port"] != occupied_port, "occupied preferred port must fall back")
        require(dev["runtime"]["environment"]["PORT"] == str(dev["port"]), "PORT exposure missing")
        require(dev["runtime"]["environment"]["AIPS_PORT"] == str(dev["port"]), "canonical AIPS_PORT missing")
        require(dev["runtime"]["environment"]["AIPS_PORT_DEV"] == str(dev["port"]), "named canonical port missing")

        stable = json_run(
            [
                sys.executable,
                str(ISOLATION),
                "runtime-lease",
                "--project",
                str(project),
                "--id",
                "agent-a",
                "--port",
                "dev",
                "--port-start",
                "42000",
                "--port-end",
                "42100",
                "--format",
                "json",
            ],
            env,
        )
        require(stable["port"] == dev["port"] and stable["reused"] is True, "existing lease must be stable")

        cmd_a = [
            sys.executable,
            str(ISOLATION),
            "runtime-lease",
            "--project",
            str(project),
            "--id",
            "agent-a",
            "--port",
            "test",
            "--port-start",
            "43000",
            "--port-end",
            "43010",
            "--format",
            "json",
        ]
        cmd_b = [
            sys.executable,
            str(ISOLATION),
            "runtime-lease",
            "--project",
            str(project),
            "--id",
            "agent-b",
            "--port",
            "test",
            "--port-start",
            "43000",
            "--port-end",
            "43010",
            "--format",
            "json",
        ]
        proc_a = subprocess.Popen(cmd_a, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        proc_b = subprocess.Popen(cmd_b, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out_a, err_a = proc_a.communicate(timeout=20)
        out_b, err_b = proc_b.communicate(timeout=20)
        require(proc_a.returncode == 0, f"concurrent A lease failed: {out_a} {err_a}")
        require(proc_b.returncode == 0, f"concurrent B lease failed: {out_b} {err_b}")
        lease_a = json.loads(out_a)
        lease_b = json.loads(out_b)
        require(lease_a["port"] != lease_b["port"], "atomic registry must prevent duplicate concurrent leases")

        moved = json_run(
            [
                sys.executable,
                str(ISOLATION),
                "runtime-reallocate",
                "--project",
                str(project),
                "--id",
                "agent-a",
                "--port",
                "test",
                "--port-start",
                "43000",
                "--port-end",
                "43010",
                "--max-attempts",
                "10",
                "--format",
                "json",
            ],
            env,
        )
        require(moved["port"] != lease_a["port"], "bounded reallocation must not return the failed port")
        require(moved["reallocated_from"] == lease_a["port"], "reallocation evidence missing old port")

        dirty = Path(iso_a["path"]) / "dirty.txt"
        dirty.write_text("keep\n", encoding="utf-8")
        released = json_run(
            [
                sys.executable,
                str(ISOLATION),
                "runtime-release",
                "--project",
                str(project),
                "--id",
                "agent-a",
                "--port",
                "dev",
                "--format",
                "json",
            ],
            env,
        )
        require(released["released"], "runtime release must work independently of worktree cleanliness")
        require(dirty.exists(), "runtime release must not modify dirty worktree content")
        blocked = run(
            [
                sys.executable,
                str(ISOLATION),
                "remove",
                "--project",
                str(project),
                "--id",
                "agent-a",
                "--format",
                "json",
            ],
            env,
        )
        require(blocked.returncode == 2 and dirty.exists(), "dirty worktree must still block workspace cleanup")
        dirty.unlink()

        removed_a = json_run(
            [sys.executable, str(ISOLATION), "remove", "--project", str(project), "--id", "agent-a", "--format", "json"],
            env,
        )
        require(removed_a["status"] == "REMOVED", "clean worktree A removal failed")
        status_b = json_run(
            [sys.executable, str(ISOLATION), "status", "--project", str(project), "--id", "agent-b", "--format", "json"],
            env,
        )
        require("test" in status_b["runtime"]["ports"], "agent B lease must survive agent A cleanup")

        iso_c = create(project, env, "agent-c", "frontend-c")
        json_run(
            [
                sys.executable,
                str(ISOLATION),
                "runtime-lease",
                "--project",
                str(project),
                "--id",
                "agent-c",
                "--port",
                "dev",
                "--port-start",
                "44000",
                "--port-end",
                "44020",
                "--format",
                "json",
            ],
            env,
        )
        record_path = Path(iso_c["record"])
        record = yaml.safe_load(record_path.read_text(encoding="utf-8"))
        record["status"] = "REMOVED"
        record_path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        reconciled = json_run(
            [sys.executable, str(ISOLATION), "runtime-reconcile", "--project", str(project), "--format", "json"],
            env,
        )
        require(
            any(item["isolation_id"] == "agent-c" for item in reconciled["released"]),
            "orphaned lease must be detectable and recoverable",
        )

        json_run(
            [sys.executable, str(ISOLATION), "remove", "--project", str(project), "--id", "agent-b", "--format", "json"],
            env,
        )
        json_run(
            [sys.executable, str(ISOLATION), "remove", "--project", str(project), "--id", "agent-c", "--format", "json"],
            env,
        )

        registry = config / "aips" / "runtime"
        if registry.exists():
            for path in registry.glob("*/ports.yaml"):
                doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                require(not (doc.get("leases") or []), "all test leases must be released")

    print("runtime port isolation lifecycle: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

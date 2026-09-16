#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
PI = ROOT / "scripts" / "project_intelligence.py"
CLI = ROOT / "bin" / "aips"


def run(args: list[str], *, env: dict[str, str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, env=env, cwd=cwd, capture_output=True, text=True)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def git(project: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=project, check=True, capture_output=True, text=True)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        project = base / "project"
        config = base / "config"
        home = base / "home"
        bin_home = base / "bin"
        project.mkdir()
        home.mkdir()
        (project / "internal" / "domain").mkdir(parents=True)
        (project / "AGENTS.md").write_text("# Project Rules\nUse existing architecture.\n", encoding="utf-8")
        (project / "main.go").write_text("package main\nfunc main() {}\n", encoding="utf-8")
        (project / "internal" / "domain" / "order.go").write_text(
            "package domain\ntype Order struct{}\n", encoding="utf-8"
        )
        (project / ".env").write_text("PASSWORD=fixture-placeholder\n", encoding="utf-8")

        git(project, "init", "-q")
        git(project, "config", "user.email", "aips@example.invalid")
        git(project, "config", "user.name", "AIPS Test")
        git(project, "add", "AGENTS.md", "main.go", "internal/domain/order.go")
        git(project, "commit", "-qm", "initial")

        env = dict(os.environ)
        env["XDG_CONFIG_HOME"] = str(config)
        env["HOME"] = str(home)
        env["AIPS_BIN_HOME"] = str(bin_home)

        boot = run(
            [sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json"],
            env=env,
        )
        require(boot.returncode == 0, f"bootstrap failed: {boot.stdout} {boot.stderr}")
        boot_doc = json.loads(boot.stdout)
        require(boot_doc.get("mode") == "EPHEMERAL", "bootstrap must use EPHEMERAL mode")
        require(boot_doc.get("readiness") == "PARTIAL", "deterministic inventory must remain PARTIAL")
        require(not (project / ".ai").exists(), "EPHEMERAL bootstrap must not create project .ai")

        store = Path(boot_doc["store"])
        require((store / "PROJECT_INTELLIGENCE.yaml").is_file(), "external Project Intelligence missing")
        registry = load_yaml(store / "SOURCE_REGISTRY.yaml")
        agents = [s for s in registry.get("sources", []) if s.get("path") == "AGENTS.md"]
        require(bool(agents), "AGENTS.md pointer missing from SOURCE_REGISTRY")
        require(agents[0].get("content_duplicated") is False, "authoritative source content must not be duplicated")
        require("codex" in (agents[0].get("auto_loaded_by") or []), "runtime visibility missing for AGENTS.md")

        intel_path = store / "PROJECT_INTELLIGENCE.yaml"
        intel = load_yaml(intel_path)
        require((intel.get("state") or {}).get("readiness") == "PARTIAL", "bootstrap state must be PARTIAL")
        intel.setdefault("architecture", {}).update(
            {"summary": "Layered test architecture", "confidence": "high", "source": "topics/architecture.md"}
        )
        intel["unknowns"] = []
        topics = intel.setdefault("topics", {})
        for name in ("architecture", "data-flow", "modules", "conventions", "testing", "security"):
            topic_file = store / "topics" / f"{name}.md"
            topic_file.parent.mkdir(parents=True, exist_ok=True)
            topic_file.write_text(
                f"# {name}\n\nEvidence-grounded test topic for deterministic readiness validation.\n",
                encoding="utf-8",
            )
            topics[name] = {
                "path": f"topics/{name}.md",
                "type": "INTERPRETATION",
                "confidence": "high",
                "evidence": ["AGENTS.md", "main.go"],
                "watch": ["internal/domain/**"] if name == "architecture" else [],
            }
        intel_path.write_text(yaml.safe_dump(intel, sort_keys=False), encoding="utf-8")

        final = run(
            [sys.executable, str(PI), "finalize", "--project", str(project), "--format", "json"],
            env=env,
        )
        require(final.returncode == 0, f"finalize failed: {final.stdout} {final.stderr}")
        require(json.loads(final.stdout).get("readiness") == "READY", "semantic finalize must reach READY")

        review = store / "reviews" / "PROJECT_INTELLIGENCE_REVIEW.html"
        review_text = review.read_text(encoding="utf-8")
        require("Project Intelligence Review" in review_text, "review HTML missing")
        require("fixture-placeholder" not in review_text, "review HTML exposed secret-like value")
        require("cdn." not in review_text.lower(), "review HTML must be self-contained")
        require("<script src=" not in review_text.lower(), "review HTML must not load remote scripts")

        (project / "NOTES.txt").write_text("unrelated\n", encoding="utf-8")
        git(project, "add", "NOTES.txt")
        git(project, "commit", "-qm", "unrelated")
        current = run(
            [sys.executable, str(PI), "status", "--project", str(project), "--format", "json"],
            env=env,
        )
        require(current.returncode == 0, "status after unrelated commit failed")
        require(
            (json.loads(current.stdout).get("freshness") or {}).get("status") == "CURRENT",
            "unrelated commit must not stale Project Intelligence",
        )

        (project / "internal" / "domain" / "order.go").write_text(
            "package domain\ntype Order struct{ ID string }\n", encoding="utf-8"
        )
        git(project, "add", "internal/domain/order.go")
        git(project, "commit", "-qm", "domain change")
        stale = run(
            [sys.executable, str(PI), "status", "--project", str(project), "--format", "json"],
            env=env,
        )
        stale_doc = json.loads(stale.stdout)
        require((stale_doc.get("freshness") or {}).get("status") == "STALE", "watched change must stale Intelligence")
        require(
            "architecture" in ((stale_doc.get("freshness") or {}).get("affected_topics") or []),
            "watched architecture change must target architecture topic",
        )

        with (project / "internal" / "domain" / "order.go").open("a", encoding="utf-8") as fh:
            fh.write("// dirty\n")
        dirty = run(
            [sys.executable, str(PI), "status", "--project", str(project), "--format", "json"],
            env=env,
        )
        dirty_reasons = (json.loads(dirty.stdout).get("freshness") or {}).get("reasons") or []
        require(
            any(str(reason).startswith("dirty_watched_path:") for reason in dirty_reasons),
            "dirty watched path must be represented in freshness",
        )
        git(project, "checkout", "--", "internal/domain/order.go")

        lock = store / ".writer.lock"
        lock.write_text("test", encoding="utf-8")
        locked = run(
            [sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json"],
            env=env,
        )
        require(locked.returncode != 0, "second Project Intelligence writer must be blocked")
        lock.unlink()

        uninstall = run(["bash", str(CLI), "uninstall"], env=env)
        require(uninstall.returncode == 0, f"isolated uninstall failed: {uninstall.stdout} {uninstall.stderr}")
        require(store.exists(), "normal uninstall must preserve External Project Intelligence cache")

        attach = run(["bash", str(CLI), "attach", str(project)], env=env)
        require(attach.returncode == 0, f"attach failed: {attach.stdout} {attach.stderr}")
        require((project / ".ai" / "STATE.yaml").is_file(), "ATTACHED workspace state missing")
        require((project / ".ai" / "MANIFEST.yaml").is_file(), "ATTACHED workspace manifest missing")
        require((project / ".ai" / "SYSTEM.yaml").is_file(), "ATTACHED system provenance missing")
        require(
            (project / ".ai" / "intelligence" / "PROJECT_INTELLIGENCE.yaml").is_file(),
            "attach must migrate External Intelligence to project-local Intelligence",
        )

        uninstall_attached = run(["bash", str(CLI), "uninstall"], env=env)
        require(uninstall_attached.returncode == 0, "uninstall after attach failed")
        require((project / ".ai").is_dir(), "uninstall must preserve ATTACHED project workspace")

        detach = run(["bash", str(CLI), "detach", str(project)], env=env)
        require(detach.returncode == 0, f"detach failed: {detach.stdout} {detach.stderr}")
        require(not (project / ".ai").exists(), "detach must archive .ai workspace")
        require(any(project.glob(".ai.detached-*")), "detach archive missing")
        status = run(
            [sys.executable, str(PI), "status", "--project", str(project), "--format", "json"],
            env=env,
        )
        status_doc = json.loads(status.stdout)
        require(status_doc.get("mode") == "EPHEMERAL", "detached project must return to EPHEMERAL mode")
        require(status_doc.get("exists") is True, "detach must sync local Intelligence back to external cache")

    print("project_intelligence_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

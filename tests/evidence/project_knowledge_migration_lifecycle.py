#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
PI = ROOT / "scripts" / "project_intelligence.py"


def run(args: list[str], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, env=env, capture_output=True, text=True)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def git(project: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=project, check=True, capture_output=True, text=True)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        project = base / "project"
        config = base / "config"
        home = base / "home"
        project.mkdir()
        home.mkdir()
        legacy_dir = project / ".ai" / "knowledge"
        legacy_dir.mkdir(parents=True)
        legacy_index = legacy_dir / "KNOWLEDGE_INDEX.yaml"
        legacy_index.write_text(
            "version: 1\nitems:\n  - id: legacy-architecture\n    summary: Preserve as migration evidence only.\n",
            encoding="utf-8",
        )
        (project / "AGENTS.md").write_text(
            "# Project Rules\nCanonical project rules remain authoritative here.\n",
            encoding="utf-8",
        )
        (project / "main.py").write_text("print('fixture')\n", encoding="utf-8")

        git(project, "init", "-q")
        git(project, "config", "user.email", "aips@example.invalid")
        git(project, "config", "user.name", "AIPS Test")
        git(project, "add", "AGENTS.md", "main.py", ".ai/knowledge/KNOWLEDGE_INDEX.yaml")
        git(project, "commit", "-qm", "legacy knowledge fixture")

        env = dict(os.environ)
        env["XDG_CONFIG_HOME"] = str(config)
        env["HOME"] = str(home)
        legacy_before = digest(legacy_index)

        boot = run(
            [sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json"],
            env=env,
        )
        require(boot.returncode == 0, f"bootstrap failed: {boot.stdout} {boot.stderr}")
        boot_doc = json.loads(boot.stdout)
        require(boot_doc.get("mode") == "ATTACHED", "legacy .ai project must remain ATTACHED")

        store = project / ".ai" / "intelligence"
        intel_path = store / "PROJECT_INTELLIGENCE.yaml"
        registry_path = store / "SOURCE_REGISTRY.yaml"
        require(intel_path.is_file(), "canonical Project Intelligence was not created")
        require(registry_path.is_file(), "SOURCE_REGISTRY was not created")
        require(legacy_index.is_file(), "legacy Project Knowledge must be preserved")
        require(digest(legacy_index) == legacy_before, "bootstrap must not rewrite legacy Project Knowledge")

        intel = load_yaml(intel_path)
        migration = intel.get("migration") or {}
        require(migration.get("from_project_knowledge") is True, "migration provenance must detect legacy Project Knowledge")
        require(
            ".ai/knowledge/KNOWLEDGE_INDEX.yaml" in (migration.get("sources") or []),
            "legacy Project Knowledge path must be retained as migration evidence",
        )

        registry = load_yaml(registry_path)
        agents = [s for s in registry.get("sources", []) if s.get("path") == "AGENTS.md"]
        require(bool(agents), "authoritative AGENTS.md pointer missing")
        require(agents[0].get("content_duplicated") is False, "authoritative content must stay pointer-over-copy")

        topic_path = store / "topics" / "architecture.md"
        topic_path.parent.mkdir(parents=True, exist_ok=True)
        topic_path.write_text(
            "# Architecture\n\nNew reusable conclusion persisted in Project Intelligence, not legacy knowledge.\n",
            encoding="utf-8",
        )
        intel.setdefault("architecture", {}).update(
            {"summary": "Migrated reusable architecture understanding", "confidence": "high", "source": "topics/architecture.md"}
        )
        intel["unknowns"] = []
        topics = intel.setdefault("topics", {})
        for name in ("architecture", "data-flow", "modules", "conventions", "testing", "security"):
            p = store / "topics" / f"{name}.md"
            if not p.exists():
                p.write_text(f"# {name}\n\nCanonical Project Intelligence topic.\n", encoding="utf-8")
            topics[name] = {
                "path": f"topics/{name}.md",
                "type": "INTERPRETATION",
                "confidence": "high",
                "evidence": ["AGENTS.md", "main.py"],
                "watch": ["main.py"] if name == "architecture" else [],
            }
        intel_path.write_text(yaml.safe_dump(intel, sort_keys=False), encoding="utf-8")

        final = run(
            [sys.executable, str(PI), "finalize", "--project", str(project), "--format", "json"],
            env=env,
        )
        require(final.returncode == 0, f"finalize failed: {final.stdout} {final.stderr}")
        require(json.loads(final.stdout).get("readiness") == "READY", "migrated Intelligence must finalize READY")
        require(topic_path.is_file(), "new reusable conclusion must live in Project Intelligence")
        require(digest(legacy_index) == legacy_before, "finalize must preserve legacy Project Knowledge evidence unchanged")
        require(
            "New reusable conclusion" not in legacy_index.read_text(encoding="utf-8"),
            "new conclusions must not be written back to legacy Project Knowledge",
        )

    print("project_knowledge_migration_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

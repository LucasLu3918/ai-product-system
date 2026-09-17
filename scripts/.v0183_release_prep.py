#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"marker not found in {path}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def update_project_intelligence() -> None:
    path = ROOT / "scripts/project_intelligence.py"
    text = path.read_text(encoding="utf-8")

    old = '''                "excluded_inferences": [],\n                "conflicts": [],\n            })\n'''
    new = '''                "excluded_inferences": [],\n                "promotion_approvals": [],\n                "conflicts": [],\n            })\n'''
    if old not in text:
        raise RuntimeError("bootstrap overrides marker not found")
    text = text.replace(old, new, 1)

    marker = '''\ndef resolve_component_context(store: Path, intel: dict[str, Any], component: str | None) -> tuple[dict[str, Any], list[str]]:\n'''
    block = r'''
def _promotion_candidate(store: Path, intel: dict[str, Any], topic_name: str) -> tuple[dict[str, Any], Path]:
    topic = (intel.get("topics") or {}).get(topic_name)
    if not isinstance(topic, dict):
        raise RuntimeError(f"Unknown Project Intelligence topic: {topic_name}")
    path_value = topic.get("path")
    if not path_value:
        raise RuntimeError(f"Project Intelligence topic has no derived content path: {topic_name}")
    derived_path = store / str(path_value)
    if not derived_path.is_file():
        raise RuntimeError(f"Project Intelligence topic content is missing: {path_value}")
    promotion = topic.get("promotion") or {}
    confirmations = [str(value) for value in (promotion.get("confirmations") or []) if str(value).strip()]
    confirmations = list(dict.fromkeys(confirmations))
    eligible = (
        len(confirmations) >= 2
        and topic.get("type") in {"FACT", "INTERPRETATION", "OBSERVED_CONVENTION"}
        and bool(topic.get("evidence"))
    )
    return {
        "topic": topic_name,
        "status": "RECOMMENDED" if eligible else "NOT_READY",
        "approval_required": True,
        "mutation_performed": False,
        "confirmations": confirmations,
        "confirmation_count": len(confirmations),
        "reason": "repeated_confirmed_derived_invariant" if eligible else "insufficient_confirmation_or_evidence",
        "allowed_targets": ["AGENTS.md", "AGENTS.override.md", "docs/<official-project-rule>.md"],
    }, derived_path


def promotion_plan(root: Path, topic_name: str) -> dict[str, Any]:
    store, mode, pid = intelligence_store(root)
    intel_path = store / "PROJECT_INTELLIGENCE.yaml"
    if not intel_path.exists():
        raise RuntimeError("Project Intelligence is not initialized")
    intel = load_yaml(intel_path, {})
    candidate, _ = _promotion_candidate(store, intel, topic_name)
    return {"project_id": pid, "mode": mode, **candidate}


def _promotion_target(root: Path, target: str) -> Path:
    raw = Path(target)
    if raw.is_absolute():
        raise RuntimeError("Promotion target must be project-relative")
    resolved = (root / raw).resolve()
    try:
        relative = resolved.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise RuntimeError("Promotion target escapes project root") from exc
    allowed = raw.name in SOURCE_NAMES or (relative.startswith("docs/") and raw.suffix.lower() in DOC_EXT)
    if not allowed:
        raise RuntimeError("Promotion target must be AGENTS*/runtime instruction source or an official docs/* document")
    return resolved


def promotion_apply(root: Path, topic_name: str, target: str, approval_id: str) -> dict[str, Any]:
    store, mode, pid = intelligence_store(root)
    intel_path = store / "PROJECT_INTELLIGENCE.yaml"
    registry_path = store / "SOURCE_REGISTRY.yaml"
    overrides_path = store / "PROJECT_OVERRIDES.yaml"
    for required in (intel_path, registry_path, overrides_path):
        if not required.exists():
            raise RuntimeError(f"Required Project Intelligence artifact missing: {required.name}")

    target_path = _promotion_target(root, target)
    target_rel = target_path.relative_to(root.resolve()).as_posix()
    if target_path.exists():
        raise RuntimeError(f"Promotion target already exists; automatic overwrite is not allowed: {target_rel}")

    with writer_lock(store):
        intel = load_yaml(intel_path, {})
        registry = load_yaml(registry_path, {"version": 1, "sources": []})
        overrides = load_yaml(overrides_path, {})
        candidate, derived_path = _promotion_candidate(store, intel, topic_name)
        if candidate["status"] != "RECOMMENDED":
            raise RuntimeError(f"Project Intelligence topic is not ready for promotion: {topic_name}")

        approval = None
        for item in overrides.get("promotion_approvals") or []:
            if not isinstance(item, dict) or str(item.get("id")) != approval_id:
                continue
            if (
                str(item.get("status", "")).upper() == "APPROVED"
                and str(item.get("topic")) == topic_name
                and str(item.get("target")) == target_rel
                and str(item.get("approved_by", "")).strip()
                and str(item.get("approved_at", "")).strip()
            ):
                approval = item
                break
        if approval is None:
            raise RuntimeError("Matching APPROVED promotion approval is required before authoritative mutation")

        content = derived_path.read_text(encoding="utf-8")
        source_id = f"src-{sha(target_rel)[:10]}"
        authority = "project_instruction" if target_path.name in SOURCE_NAMES else "official_document"
        auto: list[str] = []
        if target_path.name.startswith("AGENTS"):
            auto.append("codex")
        if target_path.name == "CLAUDE.md":
            auto.append("claude-code")
        if target_path.name == "GEMINI.md":
            auto.append("gemini-cli")

        existing_sources = [item for item in (registry.get("sources") or []) if isinstance(item, dict)]
        if any(str(item.get("path")) == target_rel for item in existing_sources):
            raise RuntimeError(f"SOURCE_REGISTRY already contains promotion target: {target_rel}")
        new_source = {
            "id": source_id,
            "path": target_rel,
            "authority": authority,
            "scope": str(Path(target_rel).parent.as_posix()),
            "hash": sha(content),
            "auto_loaded_by": auto,
            "content_duplicated": False,
            "promoted_from": topic_name,
            "approval_id": approval_id,
        }

        topic = (intel.get("topics") or {}).get(topic_name)
        original_topic = dict(topic)
        original_registry = list(existing_sources)
        original_approval = dict(approval)
        derived_content = content
        target_created = False
        derived_removed = False
        try:
            atomic_text(target_path, content)
            target_created = True
            # Verify bytes before registering authoritative source.
            new_source["hash"] = file_hash(target_path)
            registry["sources"] = sorted([*existing_sources, new_source], key=lambda item: str(item.get("path", "")))

            topic.pop("path", None)
            topic["authoritative_pointer"] = {"source_id": source_id, "path": target_rel}
            topic["content_duplicated"] = False
            topic["promotion"] = {
                "status": "PROMOTED",
                "approval_id": approval_id,
                "approved_by": approval.get("approved_by"),
                "approved_at": approval.get("approved_at"),
                "promoted_at": utc_now(),
            }
            approval["status"] = "APPLIED"
            approval["applied_at"] = utc_now()
            approval["source_id"] = source_id

            atomic_yaml(registry_path, registry)
            atomic_yaml(intel_path, intel)
            atomic_yaml(overrides_path, overrides)
            derived_path.unlink()
            derived_removed = True
        except Exception:
            if target_created:
                with contextlib.suppress(FileNotFoundError):
                    target_path.unlink()
            if derived_removed and not derived_path.exists():
                atomic_text(derived_path, derived_content)
            (intel.get("topics") or {})[topic_name] = original_topic
            registry["sources"] = original_registry
            approval.clear()
            approval.update(original_approval)
            atomic_yaml(registry_path, registry)
            atomic_yaml(intel_path, intel)
            atomic_yaml(overrides_path, overrides)
            raise

    return {
        "project_id": pid,
        "mode": mode,
        "topic": topic_name,
        "status": "PROMOTED",
        "approval_id": approval_id,
        "authoritative_source": target_rel,
        "source_id": source_id,
        "derived_content_removed": True,
        "content_duplicated": False,
    }

'''
    if marker not in text:
        raise RuntimeError("component context insertion marker not found")
    text = text.replace(marker, "\n" + block + marker.lstrip("\n"), 1)

    old = '''    p = sub.add_parser("impact-init")\n'''
    new = '''    p = sub.add_parser("promotion-plan")\n    p.add_argument("--project", default=os.getcwd())\n    p.add_argument("--topic", required=True)\n    p.add_argument("--format", choices=["yaml", "json"], default="yaml")\n\n    p = sub.add_parser("promotion-apply")\n    p.add_argument("--project", default=os.getcwd())\n    p.add_argument("--topic", required=True)\n    p.add_argument("--target", required=True)\n    p.add_argument("--approval-id", required=True)\n    p.add_argument("--format", choices=["yaml", "json"], default="yaml")\n\n    p = sub.add_parser("impact-init")\n'''
    if old not in text:
        raise RuntimeError("promotion parser marker not found")
    text = text.replace(old, new, 1)

    old = '''        elif args.command == "impact-init":\n            result = impact_init(root, args.prompt, args.change_id)\n'''
    new = '''        elif args.command == "promotion-plan":\n            result = promotion_plan(root, args.topic)\n        elif args.command == "promotion-apply":\n            result = promotion_apply(root, args.topic, args.target, args.approval_id)\n        elif args.command == "impact-init":\n            result = impact_init(root, args.prompt, args.change_id)\n'''
    if old not in text:
        raise RuntimeError("promotion dispatch marker not found")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def update_templates_and_cli() -> None:
    path = ROOT / "templates/intelligence/PROJECT_OVERRIDES.yaml"
    text = path.read_text(encoding="utf-8")
    marker = '''excluded_inferences: []\n\nconflicts: []\n'''
    addition = '''excluded_inferences: []\n\npromotion_approvals: []\n# - id: PROMOTE-001\n#   topic: api-error-contract\n#   target: docs/API_ERROR_RULE.md\n#   status: APPROVED\n#   approved_by: human\n#   approved_at: 2026-01-01T00:00:00Z\n\nconflicts: []\n'''
    if marker not in text:
        raise RuntimeError("PROJECT_OVERRIDES template marker not found")
    path.write_text(text.replace(marker, addition, 1), encoding="utf-8")

    cli = ROOT / "bin/aips"
    text = cli.read_text(encoding="utf-8")
    old = '''  aips intelligence reconcile-overrides [--project <path>]\n  aips intelligence render [--project <path>]\n'''
    new = '''  aips intelligence reconcile-overrides [--project <path>]\n  aips intelligence promotion-plan --topic <name> [--project <path>]\n  aips intelligence promotion-apply --topic <name> --target <path> --approval-id <id> [--project <path>]\n  aips intelligence render [--project <path>]\n'''
    if old not in text:
        raise RuntimeError("CLI usage marker not found")
    cli.write_text(text.replace(old, new, 1), encoding="utf-8")


def create_lifecycle() -> None:
    path = ROOT / "tests/evidence/project_intelligence_promotion_lifecycle.py"
    path.write_text(r'''#!/usr/bin/env python3
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


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        home = base / "home"
        config = base / "config"
        project = base / "project"
        home.mkdir()
        project.mkdir()
        (project / ".ai").mkdir()
        (project / "src").mkdir()
        (project / "src" / "api.py").write_text("def error_response():\n    return {'error': 'stable'}\n", encoding="utf-8")
        (project / "README.md").write_text("# Promotion fixture\n", encoding="utf-8")
        git(project, "init", "-q")
        git(project, "branch", "-m", "main")
        git(project, "config", "user.email", "aips@example.invalid")
        git(project, "config", "user.name", "AIPS Evidence")
        git(project, "add", "-A")
        git(project, "commit", "-qm", "baseline")

        env = dict(os.environ)
        env["HOME"] = str(home)
        env["XDG_CONFIG_HOME"] = str(config)
        boot = json_run([sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json"], env)
        store = Path(boot["store"])
        intel_path = store / "PROJECT_INTELLIGENCE.yaml"
        overrides_path = store / "PROJECT_OVERRIDES.yaml"
        registry_path = store / "SOURCE_REGISTRY.yaml"

        topic_rel = "topics/api-error-contract.md"
        topic_path = store / topic_rel
        topic_path.parent.mkdir(parents=True, exist_ok=True)
        derived_content = "# API Error Contract\n\nAll public API errors use the stable envelope `{error: string}`.\n"
        topic_path.write_text(derived_content, encoding="utf-8")
        intel = load_yaml(intel_path)
        intel.setdefault("topics", {})["api-error-contract"] = {
            "path": topic_rel,
            "type": "OBSERVED_CONVENTION",
            "confidence": "high",
            "evidence": ["src/api.py", "review:api-contract-1", "review:api-contract-2"],
            "watch": ["src/api.py"],
            "promotion": {"confirmations": ["review:api-contract-1", "review:api-contract-2"]},
        }
        intel_path.write_text(yaml.safe_dump(intel, sort_keys=False), encoding="utf-8")

        target = "docs/API_ERROR_RULE.md"
        plan = json_run([
            sys.executable, str(PI), "promotion-plan", "--project", str(project),
            "--topic", "api-error-contract", "--format", "json",
        ], env)
        require(plan.get("status") == "RECOMMENDED", "repeated confirmed invariant must be recommended for promotion")
        require(plan.get("approval_required") is True, "promotion recommendation must require approval")
        require(plan.get("mutation_performed") is False, "promotion plan must remain non-mutating")
        require(not (project / target).exists(), "promotion plan must not create authoritative source")
        require(topic_path.exists(), "promotion plan must preserve derived content")

        denied = run([
            sys.executable, str(PI), "promotion-apply", "--project", str(project),
            "--topic", "api-error-contract", "--target", target,
            "--approval-id", "PROMOTE-API-001", "--format", "json",
        ], env)
        require(denied.returncode != 0, "promotion without approval must fail")
        require("Matching APPROVED promotion approval" in denied.stderr, "missing approval failure must be explicit")
        require(not (project / target).exists(), "failed promotion must not mutate authoritative project files")
        require(topic_path.exists(), "failed promotion must preserve derived content")

        overrides = load_yaml(overrides_path)
        overrides["promotion_approvals"] = [{
            "id": "PROMOTE-API-001",
            "topic": "api-error-contract",
            "target": target,
            "status": "APPROVED",
            "approved_by": "fixture-human",
            "approved_at": "2026-09-17T00:00:00Z",
        }]
        overrides_path.write_text(yaml.safe_dump(overrides, sort_keys=False), encoding="utf-8")

        applied = json_run([
            sys.executable, str(PI), "promotion-apply", "--project", str(project),
            "--topic", "api-error-contract", "--target", target,
            "--approval-id", "PROMOTE-API-001", "--format", "json",
        ], env)
        require(applied.get("status") == "PROMOTED", "approved promotion must succeed")
        require(applied.get("content_duplicated") is False, "promotion must report pointer-over-copy deduplication")
        authoritative = project / target
        require(authoritative.read_text(encoding="utf-8") == derived_content, "authoritative source must receive approved derived rule content")
        require(not topic_path.exists(), "duplicate derived content must be removed after promotion")

        registry = load_yaml(registry_path)
        promoted_sources = [item for item in registry.get("sources") or [] if item.get("path") == target]
        require(len(promoted_sources) == 1, "promoted authoritative source must be registered exactly once")
        source = promoted_sources[0]
        require(source.get("authority") == "official_document", "docs promotion must register official_document authority")
        require(source.get("content_duplicated") is False, "SOURCE_REGISTRY must retain pointer-over-copy deduplication")
        require(source.get("promoted_from") == "api-error-contract", "promotion provenance must be registered")

        intel = load_yaml(intel_path)
        topic = (intel.get("topics") or {}).get("api-error-contract") or {}
        require("path" not in topic, "promoted topic must not keep a duplicate derived content path")
        pointer = topic.get("authoritative_pointer") or {}
        require(pointer.get("path") == target, "promoted topic must become authoritative pointer")
        require(topic.get("content_duplicated") is False, "promoted PI topic must explicitly remain non-duplicated")
        require((topic.get("promotion") or {}).get("status") == "PROMOTED", "promotion status must be durable")

        overrides = load_yaml(overrides_path)
        approval = (overrides.get("promotion_approvals") or [])[0]
        require(approval.get("status") == "APPLIED", "approval record must transition to APPLIED")
        require(approval.get("source_id") == source.get("id"), "approval record must link authoritative source")

        ctx = json_run([
            sys.executable, str(PI), "context", "--project", str(project),
            "--runtime", "claude-code", "--prompt", "Explain the API error contract.", "--format", "json",
        ], env)
        require(str(authoritative) in ((ctx.get("context") or {}).get("project_native") or []), "promoted source must enter authoritative project context")

    print("project_intelligence_promotion_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''', encoding="utf-8")


def promote_scenario_and_validator() -> None:
    coverage = ROOT / "tests/scenario_coverage.yaml"
    text = coverage.read_text(encoding="utf-8")
    pattern = re.compile(
        r'(?ms)(  - id: "054"\n    path: tests/scenarios/054-project-knowledge-promotion\.md\n)'
        r'    coverage: manual\n'
        r'    evidence:\n      - tests/scenarios/054-project-knowledge-promotion\.md\n'
        r'    note: "Requires executable approval-to-authoritative-source promotion plus SOURCE_REGISTRY deduplication; current evidence does not exercise the complete mutation lifecycle\."\n'
    )
    replacement = (
        r'\1'
        '    coverage: lifecycle\n'
        '    evidence:\n'
        '      - tests/evidence/project_intelligence_promotion_lifecycle.py\n'
        '      - scripts/project_intelligence.py\n'
        '      - tests/validate_repository.py\n'
    )
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError("Scenario 054 manual block not found exactly once")
    coverage.write_text(updated, encoding="utf-8")

    validator = ROOT / "tests/validation/conformance_isolation.py"
    text = validator.read_text(encoding="utf-8")
    old = '''        if cov.get("manual") != 7 or cov.get("agent_eval") != 52 or cov.get("lifecycle") != 47 or cov.get("automated") != 118:\n            errors.append("v0.18.2 baseline must report manual=7, lifecycle=47, agent_eval=52 and automated=118")'''
    new = '''        if cov.get("manual") != 6 or cov.get("agent_eval") != 52 or cov.get("lifecycle") != 48 or cov.get("automated") != 119:\n            errors.append("v0.18.3 baseline must report manual=6, lifecycle=48, agent_eval=52 and automated=119")'''
    if old not in text:
        raise RuntimeError("v0.18.2 baseline marker not found")
    text = text.replace(old, new, 1)
    text = text.replace(
        'errors.append("v0.18.2 committed Agent Eval baseline must contain 52 passing case/result pairs")',
        'errors.append("v0.18.3 committed Agent Eval baseline must contain 52 passing case/result pairs")',
        1,
    )
    marker = "# v0.18.2 monorepo lazy component Intelligence lifecycle\n"
    block = '''# v0.18.3 Project Intelligence promotion lifecycle\nproject_intelligence_promotion_evidence = ROOT / "tests/evidence/project_intelligence_promotion_lifecycle.py"\nif not project_intelligence_promotion_evidence.exists():\n    errors.append("Missing v0.18.3 Project Intelligence promotion lifecycle evidence")\nelse:\n    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(project_intelligence_promotion_evidence)], capture_output=True, text=True)\n    if compiled.returncode != 0:\n        errors.append(f"Project Intelligence promotion evidence syntax failed: {compiled.stderr.strip()}")\n    else:\n        result = subprocess.run([sys.executable, str(project_intelligence_promotion_evidence)], capture_output=True, text=True)\n        if result.returncode != 0:\n            errors.append(f"Project Intelligence promotion lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")\n\n'''
    if marker not in text:
        raise RuntimeError("validator insertion marker not found")
    validator.write_text(text.replace(marker, block + marker, 1), encoding="utf-8")


def update_release_docs() -> None:
    version = ROOT / "VERSION"
    if version.read_text(encoding="utf-8").strip() != "0.18.2":
        raise RuntimeError("v0.18.3 prep requires VERSION 0.18.2")
    version.write_text("0.18.3\n", encoding="utf-8")

    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    section = '''## 0.18.3\n\n### Project Intelligence Promotion\n\n- Add a non-mutating `promotion-plan` stage for repeatedly confirmed derived project invariants; recommendation never implies authority and always reports approval required.\n- Add approval-backed `promotion-apply` using the existing `PROJECT_OVERRIDES.yaml` authority container rather than introducing a new Approval Agent or gate.\n- Restrict automatic authoritative mutation to new project instruction sources or `docs/` official documents; existing targets are never overwritten automatically.\n- After an approved promotion, register the authoritative source in `SOURCE_REGISTRY.yaml`, transition the approval to `APPLIED`, remove duplicate derived topic content, and retain only an authoritative pointer in Project Intelligence.\n- Add executable temporary-project lifecycle evidence and promote Scenario 054 from manual to lifecycle.\n- Raise conformance baseline to 125 total / 6 manual / 19 deterministic / 48 lifecycle / 52 agent_eval / 119 automated / 0 uncovered (95.2% automated).\n- Architecture Diagram Impact: N/A — this extends existing Project Intelligence / Project Authority mutation semantics; no runtime topology, Role, Skill, Capability category, Approval Gate, or Constitution change.\n\n'''
    marker = "# Changelog\n\n"
    if not text.startswith(marker):
        raise RuntimeError("CHANGELOG marker not found")
    changelog.write_text(text.replace(marker, marker + section, 1), encoding="utf-8")

    conformance = ROOT / "docs/CONFORMANCE.md"
    text = conformance.read_text(encoding="utf-8")
    section = '''\n\n## v0.18.3 Project Intelligence Promotion\n\nPromoted evidence:\n\n~~~text\n054 Project Intelligence Promotion to Authoritative Source -> Lifecycle\n~~~\n\nScenario 054 now executes a temporary Git project with a repeatedly confirmed derived invariant. The lifecycle proves recommendation is non-mutating, missing approval fails closed, a matching human/project approval in `PROJECT_OVERRIDES.yaml` permits creation of a new authoritative project document, `SOURCE_REGISTRY.yaml` records that source with promotion provenance and pointer-over-copy semantics, the duplicate derived topic file is removed, and Project Intelligence retains only an authoritative pointer. Existing authoritative targets are never overwritten automatically.\n\nv0.18.3 baseline:\n\n~~~text\nTotal         125\nManual          6\nDeterministic  19\nLifecycle      48\nAgent Eval     52\nAutomated     119\nUncovered       0\nAutomated     95.2%\n~~~\n\nResidual manual gaps remain 004, 021, 022, 028, 039 and 055.\n\nArchitecture Diagram Impact: N/A. This is an additive Project Intelligence / Project Authority lifecycle contract; runtime topology and governance layers are unchanged.\n'''
    conformance.write_text(text.rstrip() + section + "\n", encoding="utf-8")


def main() -> int:
    update_project_intelligence()
    update_templates_and_cli()
    create_lifecycle()
    promote_scenario_and_validator()
    update_release_docs()
    result = subprocess.run([sys.executable, str(ROOT / "tests/validate_repository.py")], cwd=ROOT, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        return result.returncode
    print("v0.18.3 release preparation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

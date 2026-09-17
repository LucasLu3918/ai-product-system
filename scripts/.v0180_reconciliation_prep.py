#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSERT_BLOCK = '\n\nRECONCILE_MANAGED_BY = "aips_project_intelligence_reconcile"\nRECONCILE_OVERRIDE_TYPES = (\n    "approved_inferences",\n    "additional_rules",\n    "exceptions",\n    "excluded_inferences",\n)\n\n\ndef canonical_json(value: Any) -> str:\n    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)\n\n\ndef reconciliation_subject(entry: dict[str, Any]) -> str:\n    return str(entry.get("subject") or "").strip()\n\n\ndef reconciliation_scope(entry: dict[str, Any]) -> str:\n    value = str(entry.get("scope") or "project").strip().strip("/")\n    return value or "project"\n\n\ndef reconciliation_value_hash(entry: dict[str, Any]) -> str | None:\n    if "value" not in entry:\n        return None\n    return sha(canonical_json(entry.get("value")))\n\n\ndef scope_applies(override_scope: str, discovery_scope: str) -> bool:\n    if override_scope == "project":\n        return True\n    if discovery_scope == override_scope:\n        return True\n    return discovery_scope.startswith(override_scope.rstrip("/") + "/")\n\n\ndef load_reconciliation_discoveries(path: Path) -> tuple[list[dict[str, Any]], str]:\n    candidate = path.expanduser().resolve()\n    if not candidate.is_file():\n        raise RuntimeError(f"Discovery candidate file does not exist: {candidate}")\n    doc = load_yaml(candidate, {})\n    if not isinstance(doc, dict) or doc.get("version") != 1:\n        raise RuntimeError("Discovery candidate file must be a mapping with version: 1")\n    raw = doc.get("discoveries")\n    if not isinstance(raw, list):\n        raise RuntimeError("Discovery candidate file must contain a discoveries list")\n\n    normalized: list[dict[str, Any]] = []\n    for index, item in enumerate(raw):\n        if not isinstance(item, dict):\n            raise RuntimeError(f"Discovery candidate #{index + 1} must be a mapping")\n        subject = reconciliation_subject(item)\n        if not subject:\n            raise RuntimeError(f"Discovery candidate #{index + 1} requires subject")\n        if "value" not in item:\n            raise RuntimeError(f"Discovery candidate {subject!r} requires value")\n        scope = reconciliation_scope(item)\n        identity_payload = {"subject": subject, "scope": scope, "value": item.get("value")}\n        normalized.append({\n            "id": str(item.get("id") or f"discovery-{sha(canonical_json(identity_payload))[:12]}"),\n            "subject": subject,\n            "scope": scope,\n            "value": item.get("value"),\n            "type": str(item.get("type") or "INTERPRETATION"),\n            "confidence": item.get("confidence"),\n            "evidence": [str(x) for x in (item.get("evidence") or [])][:50],\n            "material": bool(item.get("material", True)),\n        })\n    return normalized, file_hash(candidate)\n\n\ndef managed_conflicts(conflicts: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:\n    preserved: list[dict[str, Any]] = []\n    managed: list[dict[str, Any]] = []\n    for item in conflicts or []:\n        if not isinstance(item, dict):\n            continue\n        if item.get("managed_by") == RECONCILE_MANAGED_BY:\n            managed.append(item)\n        else:\n            preserved.append(item)\n    return preserved, managed\n\n\ndef reconcile(root: Path, discoveries_path: Path) -> dict[str, Any]:\n    store, mode, pid = intelligence_store(root)\n    intelligence_path = store / "PROJECT_INTELLIGENCE.yaml"\n    overrides_path = store / "PROJECT_OVERRIDES.yaml"\n    discovery_path = store / "DISCOVERY.yaml"\n    if not intelligence_path.is_file() or not overrides_path.is_file():\n        raise RuntimeError("Project Intelligence must be initialized before reconciliation")\n\n    discoveries, source_hash = load_reconciliation_discoveries(discoveries_path)\n    with writer_lock(store):\n        intel = load_yaml(intelligence_path, {})\n        overrides = load_yaml(overrides_path, {})\n        if not isinstance(overrides, dict):\n            raise RuntimeError("PROJECT_OVERRIDES.yaml must be a mapping")\n        version = overrides.get("version")\n        if version not in {1, 2}:\n            raise RuntimeError(f"Unsupported PROJECT_OVERRIDES version: {version}")\n\n        comparable: list[tuple[str, dict[str, Any], str, str, str]] = []\n        for override_type in RECONCILE_OVERRIDE_TYPES:\n            entries = overrides.get(override_type) or []\n            if not isinstance(entries, list):\n                raise RuntimeError(f"PROJECT_OVERRIDES {override_type} must be a list")\n            for entry in entries:\n                if not isinstance(entry, dict):\n                    continue\n                subject = reconciliation_subject(entry)\n                value_hash = reconciliation_value_hash(entry)\n                if not subject or value_hash is None:\n                    continue\n                comparable.append((\n                    override_type,\n                    entry,\n                    subject,\n                    reconciliation_scope(entry),\n                    value_hash,\n                ))\n\n        conflicts: list[dict[str, Any]] = []\n        aligned_ids: list[str] = []\n        accepted_ids: list[str] = []\n        for discovery in discoveries:\n            subject = discovery["subject"]\n            scope = discovery["scope"]\n            discovery_hash = sha(canonical_json(discovery["value"]))\n            applicable = [\n                item for item in comparable\n                if item[2] == subject and scope_applies(item[3], scope)\n            ]\n            if not applicable:\n                accepted_ids.append(discovery["id"])\n                continue\n\n            conflict_count = 0\n            for override_type, override, _, override_scope, override_hash in applicable:\n                is_conflict = override_type == "excluded_inferences" or override_hash != discovery_hash\n                if not is_conflict:\n                    continue\n                conflict_count += 1\n                conflict_payload = {\n                    "subject": subject,\n                    "scope": scope,\n                    "override_type": override_type,\n                    "override_id": str(override.get("id") or ""),\n                    "override_scope": override_scope,\n                    "override_value_hash": override_hash,\n                    "discovery_id": discovery["id"],\n                    "discovery_value_hash": discovery_hash,\n                }\n                conflicts.append({\n                    "id": f"reconcile-{sha(canonical_json(conflict_payload))[:16]}",\n                    "status": "OPEN",\n                    "kind": "DISCOVERY_OVERRIDE_CONFLICT",\n                    "material": discovery["material"],\n                    "subject": subject,\n                    "scope": scope,\n                    "managed_by": RECONCILE_MANAGED_BY,\n                    "override": {\n                        "type": override_type,\n                        "id": override.get("id"),\n                        "scope": override_scope,\n                        "value_hash": override_hash,\n                    },\n                    "discovery": {\n                        "id": discovery["id"],\n                        "type": discovery["type"],\n                        "confidence": discovery["confidence"],\n                        "evidence": discovery["evidence"],\n                        "value_hash": discovery_hash,\n                    },\n                })\n            if conflict_count:\n                continue\n            aligned_ids.append(discovery["id"])\n\n        conflicts = sorted(conflicts, key=lambda x: x["id"])\n        preserved_override_conflicts, _ = managed_conflicts(overrides.get("conflicts"))\n        overrides["conflicts"] = preserved_override_conflicts + conflicts\n        if version == 1 and comparable:\n            overrides["version"] = 2\n\n        preserved_intel_conflicts, _ = managed_conflicts(intel.get("conflicts"))\n        intel["conflicts"] = preserved_intel_conflicts + conflicts\n\n        discovery_doc = load_yaml(discovery_path, {}) if discovery_path.exists() else {}\n        if not isinstance(discovery_doc, dict):\n            discovery_doc = {}\n        discovery_doc["reconciliation"] = {\n            "version": 1,\n            "source_hash": source_hash,\n            "status": "CONFLICT" if conflicts else "ALIGNED",\n            "evaluated": len(discoveries),\n            "accepted_ids": sorted(accepted_ids),\n            "aligned_ids": sorted(aligned_ids),\n            "conflict_ids": [c["id"] for c in conflicts],\n        }\n\n        atomic_yaml(overrides_path, overrides)\n        atomic_yaml(intelligence_path, intel)\n        atomic_yaml(discovery_path, discovery_doc)\n\n    review = render_review(root)\n    return {\n        "project_id": pid,\n        "mode": mode,\n        "status": "CONFLICT" if conflicts else "ALIGNED",\n        "evaluated": len(discoveries),\n        "accepted": len(accepted_ids),\n        "aligned": len(aligned_ids),\n        "conflicts": len(conflicts),\n        "conflict_ids": [c["id"] for c in conflicts],\n        "review_html": str(review),\n    }\n'
TEMPLATE_CONTENT = 'version: 2\n\napproved_inferences: []\n# - id: INF-001\n#   subject: architecture.orders.persistence\n#   scope: project\n#   value: repository\n#   reason: confirmed by project owner\n\nadditional_rules: []\n# - id: RULE-001\n#   subject: architecture.payments.layering\n#   scope: project\n#   value: application-before-infrastructure\n#   reason: project policy\n\nexceptions: []\n# - id: EX-001\n#   subject: architecture.legacy-payment.layering\n#   scope: legacy/payment\n#   value: direct-access-allowed\n#   reason: legacy migration\n\nexcluded_inferences: []\n# - id: EXCLUDE-001\n#   subject: architecture.framework\n#   scope: project\n#   value: active-record\n#   reason: explicitly rejected inference\n\nconflicts: []\n# Managed reconciliation conflicts are added here without changing approved lists.\n'
DOC_BLOCK = '## Override reconciliation\n\n`PROJECT_OVERRIDES.yaml` version 2 gives approved decisions a stable `subject`, `scope` and `value`.\nLater discovery is reconciled through a separate candidate file rather than writing directly over approved state:\n\n~~~yaml\nversion: 1\ndiscoveries:\n  - id: discovery-orders-persistence\n    subject: architecture.orders.persistence\n    scope: project\n    value: repository\n    type: OBSERVED_CONVENTION\n    confidence: high\n    evidence:\n      - internal/orders/repository.py\n~~~\n\nRun:\n\n~~~bash\naips intelligence reconcile --project /path/to/project --discoveries /path/to/discoveries.yaml\n~~~\n\nReconciliation is deterministic and non-destructive:\n\n- approved inferences, additional rules, exceptions and exclusions are preserved;\n- matching values are reported as aligned;\n- discoveries without an applicable override remain derived candidates;\n- contradictory discoveries create stable `DISCOVERY_OVERRIDE_CONFLICT` records in both Project Intelligence and `PROJECT_OVERRIDES.yaml`;\n- exclusion matches are conflicts rather than silently reintroduced inferences;\n- conflict records persist hashes/pointers/evidence metadata, not duplicate raw discovered values;\n- generated Human Review HTML surfaces the conflict;\n- legacy unkeyed override entries are preserved but are not guessed into reconciliation semantics.\n\nA later reconciliation can clear AIPS-managed conflicts when the candidate evidence no longer contradicts approved state. Manually maintained conflicts are preserved.\n\n'
FIXTURE_CONTENT = '#!/usr/bin/env python3\nfrom __future__ import annotations\n\nimport json\nimport os\nfrom pathlib import Path\nimport subprocess\nimport sys\nimport tempfile\n\nimport yaml\n\nROOT = Path(__file__).resolve().parents[2]\nSCRIPT = ROOT / "scripts/project_intelligence.py"\nCLI = ROOT / "bin/aips"\n\n\ndef run(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:\n    return subprocess.run(args, capture_output=True, text=True, env=env)\n\n\ndef check(condition: bool, message: str) -> None:\n    if not condition:\n        raise AssertionError(message)\n\n\ndef load_yaml(path: Path) -> dict:\n    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}\n\n\ndef main() -> int:\n    with tempfile.TemporaryDirectory() as tmp:\n        base = Path(tmp)\n        project = base / "project"\n        project.mkdir()\n        (project / ".ai").mkdir()\n        (project / "AGENTS.md").write_text("# Project instructions\\nPreserve approved architecture decisions.\\n", encoding="utf-8")\n        (project / "main.py").write_text("print(\'ok\')\\n", encoding="utf-8")\n        subprocess.run(["git", "init", "-q"], cwd=project, check=True)\n        subprocess.run(["git", "config", "user.email", "aips@example.invalid"], cwd=project, check=True)\n        subprocess.run(["git", "config", "user.name", "AIPS Test"], cwd=project, check=True)\n        subprocess.run(["git", "add", "AGENTS.md", "main.py"], cwd=project, check=True)\n        subprocess.run(["git", "commit", "-qm", "initial"], cwd=project, check=True)\n\n        env = dict(os.environ)\n        env["HOME"] = str(base / "home")\n        env["XDG_CONFIG_HOME"] = str(base / "config")\n        (base / "home").mkdir()\n\n        boot = run([sys.executable, str(SCRIPT), "bootstrap", "--project", str(project), "--format", "json"], env)\n        check(boot.returncode == 0, f"bootstrap failed: {boot.stdout} {boot.stderr}")\n\n        store = project / ".ai" / "intelligence"\n        overrides_path = store / "PROJECT_OVERRIDES.yaml"\n        intel_path = store / "PROJECT_INTELLIGENCE.yaml"\n        overrides = {\n            "version": 2,\n            "approved_inferences": [{\n                "id": "INF-ORDERS",\n                "subject": "architecture.orders.persistence",\n                "scope": "project",\n                "value": "repository",\n                "reason": "confirmed",\n            }],\n            "additional_rules": [{\n                "id": "RULE-PAYMENTS",\n                "subject": "architecture.payments.layering",\n                "scope": "project",\n                "value": "application-before-infrastructure",\n                "reason": "project policy",\n            }],\n            "exceptions": [{\n                "id": "EX-LEGACY",\n                "subject": "architecture.legacy-payment.layering",\n                "scope": "legacy/payment",\n                "value": "direct-access-allowed",\n                "reason": "migration exception",\n            }],\n            "excluded_inferences": [{\n                "id": "EXCLUDE-FRAMEWORK",\n                "subject": "architecture.framework",\n                "scope": "project",\n                "value": "active-record",\n                "reason": "explicitly rejected",\n            }],\n            "conflicts": [{\n                "id": "manual-existing",\n                "status": "OPEN",\n                "kind": "MANUAL_REVIEW",\n                "subject": "manual.subject",\n            }],\n        }\n        overrides_path.write_text(yaml.safe_dump(overrides, sort_keys=False), encoding="utf-8")\n        protected_keys = ("approved_inferences", "additional_rules", "exceptions", "excluded_inferences")\n        protected_before = {key: overrides[key] for key in protected_keys}\n\n        candidates = base / "discoveries.yaml"\n        candidates.write_text(yaml.safe_dump({\n            "version": 1,\n            "discoveries": [\n                {"id": "D-ORDERS", "subject": "architecture.orders.persistence", "scope": "project", "value": "repository", "type": "FACT", "evidence": ["main.py"]},\n                {"id": "D-PAYMENTS", "subject": "architecture.payments.layering", "scope": "project", "value": "handler-direct-db", "type": "OBSERVED_CONVENTION", "confidence": "high", "evidence": ["main.py"]},\n                {"id": "D-LEGACY", "subject": "architecture.legacy-payment.layering", "scope": "legacy/payment/handler", "value": "strict-clean-architecture", "type": "INTERPRETATION", "confidence": "medium", "evidence": ["main.py"]},\n                {"id": "D-FRAMEWORK", "subject": "architecture.framework", "scope": "project", "value": "active-record", "type": "OBSERVED_CONVENTION", "confidence": "medium", "evidence": ["main.py"]},\n                {"id": "D-NEW", "subject": "architecture.new-derived-fact", "scope": "project", "value": {"enabled": True}, "type": "FACT", "evidence": ["main.py"]},\n            ],\n        }, sort_keys=False), encoding="utf-8")\n\n        first = run(["bash", str(CLI), "intelligence", "reconcile", "--project", str(project), "--discoveries", str(candidates), "--format", "json"], env)\n        check(first.returncode == 0, f"reconcile failed: {first.stdout} {first.stderr}")\n        first_doc = json.loads(first.stdout)\n        check(first_doc["status"] == "CONFLICT", "contradictory discovery must report CONFLICT")\n        check(first_doc["conflicts"] == 3, "expected three override conflicts")\n        check(first_doc["aligned"] == 1, "expected one aligned approved inference")\n        check(first_doc["accepted"] == 1, "expected one unmatched derived candidate")\n\n        after = load_yaml(overrides_path)\n        for key in protected_keys:\n            check(after[key] == protected_before[key], f"{key} was overwritten during reconciliation")\n        managed = [c for c in after["conflicts"] if c.get("managed_by") == "aips_project_intelligence_reconcile"]\n        check(len(managed) == 3, "managed conflicts were not persisted")\n        check(any(c.get("id") == "manual-existing" for c in after["conflicts"]), "manual conflict must be preserved")\n        serialized_managed = yaml.safe_dump(managed, sort_keys=False)\n        check("handler-direct-db" not in serialized_managed, "raw discovered values must not be duplicated into conflict records")\n        check("strict-clean-architecture" not in serialized_managed, "raw discovered values must not be duplicated into conflict records")\n\n        intel = load_yaml(intel_path)\n        intel_managed = [c for c in intel.get("conflicts", []) if c.get("managed_by") == "aips_project_intelligence_reconcile"]\n        check([c["id"] for c in intel_managed] == [c["id"] for c in managed], "Project Intelligence conflict view must match overrides")\n\n        review = store / "reviews" / "PROJECT_INTELLIGENCE_REVIEW.html"\n        check("architecture.payments.layering" in review.read_text(encoding="utf-8"), "review must surface reconciliation conflict subjects")\n\n        second = run([sys.executable, str(SCRIPT), "reconcile", "--project", str(project), "--discoveries", str(candidates), "--format", "json"], env)\n        check(second.returncode == 0, f"idempotent reconcile failed: {second.stdout} {second.stderr}")\n        second_doc = json.loads(second.stdout)\n        check(second_doc["conflict_ids"] == first_doc["conflict_ids"], "conflict IDs must be deterministic")\n        second_overrides = load_yaml(overrides_path)\n        check(len([c for c in second_overrides["conflicts"] if c.get("managed_by") == "aips_project_intelligence_reconcile"]) == 3, "reconciliation must not duplicate managed conflicts")\n\n        candidates.write_text(yaml.safe_dump({\n            "version": 1,\n            "discoveries": [\n                {"id": "D-ORDERS", "subject": "architecture.orders.persistence", "scope": "project", "value": "repository", "type": "FACT", "evidence": ["main.py"]},\n                {"id": "D-PAYMENTS", "subject": "architecture.payments.layering", "scope": "project", "value": "application-before-infrastructure", "type": "OBSERVED_CONVENTION", "confidence": "high", "evidence": ["main.py"]},\n                {"id": "D-LEGACY", "subject": "architecture.legacy-payment.layering", "scope": "legacy/payment/handler", "value": "direct-access-allowed", "type": "INTERPRETATION", "confidence": "medium", "evidence": ["main.py"]},\n                {"id": "D-NEW", "subject": "architecture.new-derived-fact", "scope": "project", "value": {"enabled": True}, "type": "FACT", "evidence": ["main.py"]},\n            ],\n        }, sort_keys=False), encoding="utf-8")\n        resolved = run([sys.executable, str(SCRIPT), "reconcile", "--project", str(project), "--discoveries", str(candidates), "--format", "json"], env)\n        check(resolved.returncode == 0, f"resolved reconcile failed: {resolved.stdout} {resolved.stderr}")\n        resolved_doc = json.loads(resolved.stdout)\n        check(resolved_doc["status"] == "ALIGNED", "resolved candidate set must clear managed conflicts")\n        final_overrides = load_yaml(overrides_path)\n        for key in protected_keys:\n            check(final_overrides[key] == protected_before[key], f"{key} changed after conflict resolution")\n        check([c for c in final_overrides["conflicts"] if c.get("managed_by") == "aips_project_intelligence_reconcile"] == [], "stale managed conflicts should clear when evidence aligns")\n        check(any(c.get("id") == "manual-existing" for c in final_overrides["conflicts"]), "manual conflict must survive managed conflict cleanup")\n\n    print("project override reconciliation lifecycle: PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"marker not found in {path}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_project_intelligence() -> None:
    path = ROOT / "scripts/project_intelligence.py"
    text = path.read_text(encoding="utf-8")
    old = """                "version": 1,
                "approved_inferences": [],
                "additional_rules": [],
                "exceptions": [],
                "excluded_inferences": [],
                "conflicts": [],
"""
    new = """                "version": 2,
                "approved_inferences": [],
                "additional_rules": [],
                "exceptions": [],
                "excluded_inferences": [],
                "conflicts": [],
"""
    if old not in text:
        raise RuntimeError("bootstrap PROJECT_OVERRIDES marker not found")
    text = text.replace(old, new, 1)

    marker = "\ndef adapter_capability(runtime: str) -> str:\n"
    if marker not in text:
        raise RuntimeError("adapter_capability insertion marker not found")
    text = text.replace(marker, INSERT_BLOCK + marker, 1)

    old_intel = """        "intelligence": {
            "readiness": readiness,
            "review": state.get("review", "UNREVIEWED"),
            "freshness": fr["status"],
        },
"""
    new_intel = """        "intelligence": {
            "readiness": readiness,
            "review": state.get("review", "UNREVIEWED"),
            "freshness": fr["status"],
            "conflicts": [
                c for c in (intel.get("conflicts") or [])
                if isinstance(c, dict) and c.get("status", "OPEN") == "OPEN"
            ],
        },
"""
    if old_intel not in text:
        raise RuntimeError("context intelligence block marker not found")
    text = text.replace(old_intel, new_intel, 1)

    old_status = """        "state": intel.get("state") if intel else None,
        "freshness": freshness(root),
        "review_html": str(store / "reviews" / "PROJECT_INTELLIGENCE_REVIEW.html"),
"""
    new_status = """        "state": intel.get("state") if intel else None,
        "conflicts": (intel.get("conflicts") or []) if intel else [],
        "freshness": freshness(root),
        "review_html": str(store / "reviews" / "PROJECT_INTELLIGENCE_REVIEW.html"),
"""
    if old_status not in text:
        raise RuntimeError("status block marker not found")
    text = text.replace(old_status, new_status, 1)

    old_parser = """    p = sub.add_parser("impact-init")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--prompt", default="")
    p.add_argument("--change-id")
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")
"""
    new_parser = """    p = sub.add_parser("impact-init")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--prompt", default="")
    p.add_argument("--change-id")
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")

    p = sub.add_parser("reconcile")
    p.add_argument("--project", default=os.getcwd())
    p.add_argument("--discoveries", required=True)
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")
"""
    if old_parser not in text:
        raise RuntimeError("impact-init parser marker not found")
    text = text.replace(old_parser, new_parser, 1)

    old_dispatch = """        elif args.command == "impact-init":
            result = impact_init(root, args.prompt, args.change_id)
        elif args.command == "migrate-attached":
"""
    new_dispatch = """        elif args.command == "impact-init":
            result = impact_init(root, args.prompt, args.change_id)
        elif args.command == "reconcile":
            result = reconcile(root, Path(args.discoveries))
        elif args.command == "migrate-attached":
"""
    if old_dispatch not in text:
        raise RuntimeError("command dispatch marker not found")
    text = text.replace(old_dispatch, new_dispatch, 1)

    path.write_text(text, encoding="utf-8")


def patch_cli_help() -> None:
    replace_once(
        ROOT / "bin/aips",
        "  aips intelligence render [--project <path>]\n",
        "  aips intelligence render [--project <path>]\n"
        "  aips intelligence reconcile --discoveries <yaml> [--project <path>]\n",
    )


def write_template() -> None:
    (ROOT / "templates/intelligence/PROJECT_OVERRIDES.yaml").write_text(TEMPLATE_CONTENT, encoding="utf-8")


def patch_doc() -> None:
    path = ROOT / "orchestration/PROJECT_INTELLIGENCE.md"
    text = path.read_text(encoding="utf-8")
    marker = "## Intelligence types\n"
    if DOC_BLOCK not in text:
        if marker not in text:
            raise RuntimeError("Project Intelligence doc marker not found")
        text = text.replace(marker, DOC_BLOCK + marker, 1)
    path.write_text(text, encoding="utf-8")


def write_fixture() -> None:
    (ROOT / "tests/evidence/project_override_reconciliation_lifecycle.py").write_text(FIXTURE_CONTENT, encoding="utf-8")


def main() -> int:
    patch_project_intelligence()
    patch_cli_help()
    write_template()
    patch_doc()
    write_fixture()
    print("v0.18.0 capability preparation: APPLIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

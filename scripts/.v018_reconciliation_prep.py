#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"marker not found in {path}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_project_intelligence() -> None:
    path = ROOT / "scripts/project_intelligence.py"
    text = path.read_text(encoding="utf-8")

    old_registry = '''            "deduplication": {"storage": "pointer_over_copy", "runtime_context": "runtime_aware"},\n        }'''
    new_registry = '''            "deduplication": {"storage": "pointer_over_copy", "runtime_context": "runtime_aware"},\n            "assertions": [],\n        }'''
    if old_registry not in text:
        raise RuntimeError("SOURCE_REGISTRY bootstrap marker missing")
    text = text.replace(old_registry, new_registry, 1)

    old_discovery = '''            "repository_identity_source_hash": ident["repository_source_hash"],\n            "inventory": inv,\n        })'''
    new_discovery = '''            "repository_identity_source_hash": ident["repository_source_hash"],\n            "inventory": inv,\n            "assertions": [],\n        })'''
    if old_discovery not in text:
        raise RuntimeError("DISCOVERY bootstrap marker missing")
    text = text.replace(old_discovery, new_discovery, 1)

    insert_marker = '''def impact_path(root: Path, change_id: str) -> Path:\n'''
    if insert_marker not in text:
        raise RuntimeError("impact_path insertion marker missing")

    block = r'''AUTHORITY_RANK = {
    "approved_override": 0,
    "runtime_instruction": 1,
    "project_instruction": 1,
    "official_document": 2,
    "accepted_contract": 2,
    "canonical_artifact": 3,
    "derived_intelligence": 9,
}

OVERRIDE_BUCKETS = (
    "approved_inferences",
    "additional_rules",
    "exceptions",
    "excluded_inferences",
)


def _assertion_fingerprint(value: Any) -> str:
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str))


def _safe_assertion_value(key: str, value: Any) -> Any:
    low = key.lower()
    if any(word in low for word in ("password", "secret", "token", "credential", "api_key", "apikey", "private_key")):
        return "[REDACTED]"
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [_safe_assertion_value(key, item) for item in value]
    if isinstance(value, dict):
        return {str(k): _safe_assertion_value(f"{key}.{k}", v) for k, v in value.items()}
    return value


def _scope_depth(scope: str) -> int:
    cleaned = str(scope or ".").strip().strip("/")
    if cleaned in {"", "."}:
        return 0
    return len([part for part in cleaned.split("/") if part and part != "."])


def _claim_priority(claim: dict[str, Any]) -> tuple[int, int, int]:
    return (
        AUTHORITY_RANK.get(str(claim.get("authority") or "derived_intelligence"), 8),
        -_scope_depth(str(claim.get("scope") or ".")),
        -int(bool(claim.get("runtime_native"))),
    )


def _normalized_claim(
    raw: dict[str, Any],
    *,
    default_authority: str,
    default_source: str,
    runtime: str,
) -> dict[str, Any] | None:
    key = str(raw.get("key") or "").strip()
    if not key or "value" not in raw:
        return None
    value = raw.get("value")
    authority = str(raw.get("authority") or default_authority)
    native_for = [str(x) for x in (raw.get("native_for") or [])]
    runtime_native = bool(raw.get("runtime_native")) or (bool(runtime) and runtime in native_for)
    return {
        "id": str(raw.get("id") or f"assert-{sha(default_source + ':' + key)[:12]}"),
        "key": key,
        "value": value,
        "value_fingerprint": _assertion_fingerprint(value),
        "persisted_value": _safe_assertion_value(key, value),
        "source": str(raw.get("source") or default_source),
        "authority": authority,
        "scope": str(raw.get("scope") or "."),
        "runtime_native": runtime_native,
        "material": bool(raw.get("material", True)),
        "origin": str(raw.get("origin") or "structured_assertion"),
    }


def _collect_reconciliation_claims(
    registry: dict[str, Any],
    discovery: dict[str, Any],
    overrides: dict[str, Any],
    runtime: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    source_authority = {
        str(item.get("path")): str(item.get("authority") or "official_document")
        for item in (registry.get("sources") or [])
        if isinstance(item, dict) and item.get("path")
    }
    source_runtime = {
        str(item.get("path")): [str(x) for x in (item.get("auto_loaded_by") or [])]
        for item in (registry.get("sources") or [])
        if isinstance(item, dict) and item.get("path")
    }

    for raw in registry.get("assertions") or []:
        if not isinstance(raw, dict):
            continue
        source = str(raw.get("source") or "SOURCE_REGISTRY.yaml")
        enriched = dict(raw)
        enriched.setdefault("authority", source_authority.get(source, "project_instruction"))
        if runtime and runtime in source_runtime.get(source, []):
            enriched.setdefault("runtime_native", True)
        claim = _normalized_claim(
            enriched,
            default_authority=str(enriched.get("authority") or "project_instruction"),
            default_source=source,
            runtime=runtime,
        )
        if claim:
            result.append(claim)

    for raw in discovery.get("assertions") or []:
        if not isinstance(raw, dict):
            continue
        claim = _normalized_claim(
            raw,
            default_authority="derived_intelligence",
            default_source="DISCOVERY.yaml",
            runtime=runtime,
        )
        if claim:
            result.append(claim)

    for bucket in OVERRIDE_BUCKETS:
        for raw in overrides.get(bucket) or []:
            if not isinstance(raw, dict):
                continue
            claim = _normalized_claim(
                raw,
                default_authority="approved_override",
                default_source=f"PROJECT_OVERRIDES.yaml#{bucket}",
                runtime=runtime,
            )
            if claim:
                claim["override_bucket"] = bucket
                result.append(claim)
    return result


def _public_claim(claim: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": claim["id"],
        "source": claim["source"],
        "authority": claim["authority"],
        "scope": claim["scope"],
        "runtime_native": claim["runtime_native"],
        "material": claim["material"],
        "value": claim["persisted_value"],
        "value_fingerprint": claim["value_fingerprint"],
    }


def reconcile(root: Path, runtime: str = "") -> dict[str, Any]:
    store, mode, pid = intelligence_store(root)
    ip = store / "PROJECT_INTELLIGENCE.yaml"
    if not ip.exists():
        raise RuntimeError("Project Intelligence is not initialized")

    with writer_lock(store):
        intel = load_yaml(ip, {})
        registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": [], "assertions": []})
        discovery = load_yaml(store / "DISCOVERY.yaml", {"assertions": []})
        overrides_path = store / "PROJECT_OVERRIDES.yaml"
        overrides = load_yaml(overrides_path, {})
        claims = _collect_reconciliation_claims(registry, discovery, overrides, runtime)

        grouped: dict[str, list[dict[str, Any]]] = {}
        for claim in claims:
            grouped.setdefault(claim["key"], []).append(claim)

        resolutions: list[dict[str, Any]] = []
        conflicts: list[dict[str, Any]] = []
        unresolved_material = 0

        for key in sorted(grouped):
            key_claims = grouped[key]
            fingerprints = {claim["value_fingerprint"] for claim in key_claims}
            ordered = sorted(key_claims, key=_claim_priority)
            selected = ordered[0]
            status = "CONSISTENT"
            reason = "single_effective_value"

            if len(fingerprints) > 1:
                override_claims = [c for c in key_claims if c["authority"] == "approved_override"]
                if override_claims:
                    selected = sorted(override_claims, key=_claim_priority)[0]
                    status = "HUMAN_REVIEW"
                    reason = "approved_override_contradicted"
                else:
                    top_priority = _claim_priority(ordered[0])
                    top = [c for c in ordered if _claim_priority(c) == top_priority]
                    top_values = {c["value_fingerprint"] for c in top}
                    if len(top_values) == 1:
                        selected = top[0]
                        status = "RESOLVED_BY_PRECEDENCE"
                        reason = "authority_scope_native_precedence"
                    else:
                        selected = top[0]
                        status = "HUMAN_REVIEW"
                        reason = "equal_precedence_conflict"

                material = any(bool(c.get("material")) for c in key_claims)
                conflict = {
                    "id": f"conflict-{sha(key + ':' + ':'.join(sorted(fingerprints)))[:12]}",
                    "key": key,
                    "status": status,
                    "reason": reason,
                    "material": material,
                    "selected_claim_id": selected["id"],
                    "claims": [_public_claim(c) for c in ordered],
                }
                conflicts.append(conflict)
                if status == "HUMAN_REVIEW" and material:
                    unresolved_material += 1

            resolutions.append({
                "key": key,
                "status": status,
                "reason": reason,
                "selected": _public_claim(selected),
                "claim_count": len(key_claims),
            })

        state = "REVIEW_REQUIRED" if unresolved_material else "RESOLVED"
        reconciliation = {
            "version": 1,
            "generated_at": utc_now(),
            "runtime": runtime or None,
            "project_id": pid,
            "mode": mode,
            "status": state,
            "blocked": unresolved_material > 0,
            "unresolved_material_conflicts": unresolved_material,
            "source_preservation": {
                "source_registry_mutated": False,
                "discovery_mutated": False,
                "project_overrides_mutated": False,
            },
            "resolutions": resolutions,
            "conflicts": conflicts,
        }
        atomic_yaml(store / "RECONCILIATION.yaml", reconciliation)
        intel["conflicts"] = conflicts
        intel["reconciliation"] = {
            "path": "RECONCILIATION.yaml",
            "status": state,
            "unresolved_material_conflicts": unresolved_material,
            "reconciled_at": reconciliation["generated_at"],
        }
        atomic_yaml(ip, intel)

    review = render_review(root)
    return {
        "project_id": pid,
        "mode": mode,
        "status": state,
        "blocked": unresolved_material > 0,
        "unresolved_material_conflicts": unresolved_material,
        "conflict_count": len(conflicts),
        "resolution_count": len(resolutions),
        "reconciliation": str(store / "RECONCILIATION.yaml"),
        "review_html": str(review),
    }


'''
    text = text.replace(insert_marker, block + insert_marker, 1)

    parser_marker = '''    p = sub.add_parser("context")\n    p.add_argument("--project", default=os.getcwd())'''
    parser_replacement = '''    p = sub.add_parser("reconcile")\n    p.add_argument("--project", default=os.getcwd())\n    p.add_argument("--runtime", default="")\n    p.add_argument("--format", choices=["yaml", "json"], default="yaml")\n\n    p = sub.add_parser("context")\n    p.add_argument("--project", default=os.getcwd())'''
    if parser_marker not in text:
        raise RuntimeError("context parser marker missing")
    text = text.replace(parser_marker, parser_replacement, 1)

    dispatch_marker = '''        elif args.command == "context":\n            result = context_manifest(root, args.runtime, args.prompt, args.explain)'''
    dispatch_replacement = '''        elif args.command == "reconcile":\n            result = reconcile(root, args.runtime)\n        elif args.command == "context":\n            result = context_manifest(root, args.runtime, args.prompt, args.explain)'''
    if dispatch_marker not in text:
        raise RuntimeError("context dispatch marker missing")
    text = text.replace(dispatch_marker, dispatch_replacement, 1)

    context_marker = '''    registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []}) if store.exists() else {"sources": []}\n    state = intel.get("state") or {}'''
    context_replacement = '''    registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": [], "assertions": []}) if store.exists() else {"sources": [], "assertions": []}\n    discovery = load_yaml(store / "DISCOVERY.yaml", {"assertions": []}) if store.exists() else {"assertions": []}\n    overrides = load_yaml(store / "PROJECT_OVERRIDES.yaml", {}) if store.exists() else {}\n    reconciliation = load_yaml(store / "RECONCILIATION.yaml", {}) if (store / "RECONCILIATION.yaml").exists() else {}\n    state = intel.get("state") or {}\n    structured_assertions = bool(registry.get("assertions") or discovery.get("assertions") or any(overrides.get(k) for k in OVERRIDE_BUCKETS))'''
    if context_marker not in text:
        raise RuntimeError("context registry marker missing")
    text = text.replace(context_marker, context_replacement, 1)

    fail_marker = '''        if readiness != "READY":\n            fail_closed_reasons.append(f"intelligence_readiness_{readiness.lower()}")'''
    fail_replacement = '''        if readiness != "READY":\n            fail_closed_reasons.append(f"intelligence_readiness_{readiness.lower()}")\n        if structured_assertions and not reconciliation:\n            fail_closed_reasons.append("context_reconciliation_required")\n        if (reconciliation.get("unresolved_material_conflicts") or 0) > 0:\n            fail_closed_reasons.append("material_context_conflict")'''
    if fail_marker not in text:
        raise RuntimeError("fail-closed marker missing")
    text = text.replace(fail_marker, fail_replacement, 1)

    requirements_marker = '''            "change_impact_required": mutation,\n        },'''
    requirements_replacement = '''            "change_impact_required": mutation,\n            "context_reconciliation_required": structured_assertions and not bool(reconciliation),\n            "material_context_conflicts": int(reconciliation.get("unresolved_material_conflicts") or 0),\n        },\n        "reconciliation": {\n            "status": reconciliation.get("status", "MISSING" if structured_assertions else "NOT_REQUIRED"),\n            "path": str(store / "RECONCILIATION.yaml") if structured_assertions else None,\n            "blocked": bool(reconciliation.get("blocked", False)),\n        },'''
    if requirements_marker not in text:
        raise RuntimeError("requirements marker missing")
    text = text.replace(requirements_marker, requirements_replacement, 1)

    path.write_text(text, encoding="utf-8")


def patch_cli() -> None:
    path = ROOT / "bin/aips"
    text = path.read_text(encoding="utf-8")
    old = '''  aips intelligence context --runtime <id> [--project <path>] [--prompt <text>]\n  aips intelligence render [--project <path>]'''
    new = '''  aips intelligence context --runtime <id> [--project <path>] [--prompt <text>]\n  aips intelligence reconcile [--runtime <id>] [--project <path>]\n  aips intelligence render [--project <path>]'''
    if old not in text:
        raise RuntimeError("CLI intelligence usage marker missing")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_contract() -> None:
    path = ROOT / "orchestration/PROJECT_INTELLIGENCE.md"
    text = path.read_text(encoding="utf-8")
    marker = '''If new evidence conflicts with an override, mark a conflict for human review.\n\n## Intelligence types'''
    section = '''If new evidence conflicts with an override, mark a conflict for human review.\n\n### Structured reconciliation\n\nMaterial instruction/discovery reconciliation uses structured assertions rather than pretending deterministic string matching understands natural-language semantics. The Agent or targeted discovery may normalize relevant claims into `key` / `value` / `source` / `scope` / `authority` assertions in `SOURCE_REGISTRY.yaml`, `DISCOVERY.yaml`, or the existing override buckets.\n\n`aips intelligence reconcile` applies deterministic precedence without deleting any source:\n\n~~~text\nexplicit approved override\n→ applicable runtime/project instruction\n→ accepted ADR / contract / official document\n→ approved canonical artifact\n→ derived Intelligence\n~~~\n\nWithin the same authority tier, narrower scope wins before runtime-native visibility. Equal-precedence contradictory material claims remain `HUMAN_REVIEW`. Contradictory discovery never overwrites an approved override: the override remains selected, the conflict is surfaced, and material mutation fails closed until review.\n\nReconciliation writes `RECONCILIATION.yaml` and mirrors conflict summaries into `PROJECT_INTELLIGENCE.yaml`; it does not mutate `SOURCE_REGISTRY.yaml`, `DISCOVERY.yaml`, or `PROJECT_OVERRIDES.yaml`. Natural-language sources remain authoritative pointers and are never copied merely to normalize them.\n\n## Intelligence types'''
    if marker not in text:
        raise RuntimeError("Project Intelligence authority marker missing")
    path.write_text(text.replace(marker, section, 1), encoding="utf-8")


def write_evidence() -> None:
    path = ROOT / "tests/evidence/project_intelligence_reconciliation_lifecycle.py"
    path.write_text(r'''#!/usr/bin/env python3
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
CLI = ROOT / "bin" / "aips"


def run(args: list[str], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, env=env, capture_output=True, text=True)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_yaml(path: Path, doc: dict) -> None:
    path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(project: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=project, check=True, capture_output=True, text=True)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        project = base / "project"
        config = base / "config"
        home = base / "home"
        project.mkdir()
        home.mkdir()
        (project / ".ai").mkdir()
        (project / "services" / "payments").mkdir(parents=True)
        (project / "AGENTS.md").write_text("# Project rules\nPayment service uses project-scoped instructions.\n", encoding="utf-8")
        (project / "ADR.md").write_text("# ADR\nDeployment requires an explicit decision.\n", encoding="utf-8")
        (project / "services" / "payments" / "main.py").write_text("print('payments')\n", encoding="utf-8")
        git(project, "init", "-q")
        git(project, "config", "user.email", "aips@example.invalid")
        git(project, "config", "user.name", "AIPS Test")
        git(project, "add", ".")
        git(project, "commit", "-qm", "initial")

        env = dict(os.environ)
        env["XDG_CONFIG_HOME"] = str(config)
        env["HOME"] = str(home)

        boot = run([sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json"], env=env)
        require(boot.returncode == 0, f"bootstrap failed: {boot.stdout} {boot.stderr}")
        store = Path(json.loads(boot.stdout)["store"])
        registry_path = store / "SOURCE_REGISTRY.yaml"
        discovery_path = store / "DISCOVERY.yaml"
        overrides_path = store / "PROJECT_OVERRIDES.yaml"

        registry = load_yaml(registry_path)
        source_paths = {s.get("path") for s in registry.get("sources") or []}
        require("AGENTS.md" in source_paths, "AGENTS.md must remain a SOURCE_REGISTRY pointer")
        require(all((s.get("content_duplicated") is False) for s in registry.get("sources") or []), "authoritative sources must remain pointer-over-copy")
        registry["assertions"] = [
            {
                "id": "runtime-format",
                "key": "format.line_width",
                "value": 100,
                "source": "runtime-native",
                "authority": "runtime_instruction",
                "scope": ".",
                "runtime_native": True,
            },
            {
                "id": "project-format",
                "key": "format.line_width",
                "value": 120,
                "source": "AGENTS.md",
                "authority": "project_instruction",
                "scope": "services/payments",
            },
            {
                "id": "runtime-test",
                "key": "testing.runner",
                "value": "pytest",
                "source": "runtime-native",
                "authority": "runtime_instruction",
                "scope": ".",
                "runtime_native": True,
            },
            {
                "id": "project-test",
                "key": "testing.runner",
                "value": "unittest",
                "source": "AGENTS.md",
                "authority": "project_instruction",
                "scope": ".",
            },
            {
                "id": "deploy-a",
                "key": "deployment.mode",
                "value": "manual",
                "source": "AGENTS.md",
                "authority": "project_instruction",
                "scope": "services/payments",
                "material": True,
            },
            {
                "id": "deploy-b",
                "key": "deployment.mode",
                "value": "automatic",
                "source": "runtime-native",
                "authority": "runtime_instruction",
                "scope": "services/payments",
                "material": True,
            },
            {
                "id": "authoritative-architecture",
                "key": "architecture.pattern",
                "value": "hexagonal",
                "source": "AGENTS.md",
                "authority": "project_instruction",
                "scope": ".",
            },
        ]
        write_yaml(registry_path, registry)

        discovery = load_yaml(discovery_path)
        discovery["assertions"] = [
            {
                "id": "derived-architecture",
                "key": "architecture.pattern",
                "value": "layered",
                "source": "repository-discovery",
                "scope": ".",
            },
            {
                "id": "derived-migration",
                "key": "database.migrations",
                "value": "automatic_on_boot",
                "source": "repository-discovery",
                "scope": ".",
                "material": True,
            },
        ]
        write_yaml(discovery_path, discovery)

        overrides = load_yaml(overrides_path)
        overrides["approved_inferences"] = [
            {
                "id": "approved-migration-policy",
                "key": "database.migrations",
                "value": "manual_approval",
                "scope": ".",
                "material": True,
            }
        ]
        write_yaml(overrides_path, overrides)
        override_hash_before = digest(overrides_path)
        registry_hash_before = digest(registry_path)
        discovery_hash_before = digest(discovery_path)

        reconcile = run(
            ["bash", str(CLI), "intelligence", "reconcile", "--project", str(project), "--runtime", "codex", "--format", "json"],
            env=env,
        )
        require(reconcile.returncode == 0, f"reconcile failed: {reconcile.stdout} {reconcile.stderr}")
        reconcile_doc = json.loads(reconcile.stdout)
        require(reconcile_doc.get("status") == "REVIEW_REQUIRED", "material equal-precedence/override conflicts must require review")
        require(reconcile_doc.get("blocked") is True, "material unresolved conflicts must block mutation")
        require(reconcile_doc.get("unresolved_material_conflicts") == 2, "expected exactly two unresolved material conflicts")

        require(digest(overrides_path) == override_hash_before, "approved overrides must survive reconciliation byte-for-byte")
        require(digest(registry_path) == registry_hash_before, "SOURCE_REGISTRY must not be mutated by reconciliation")
        require(digest(discovery_path) == discovery_hash_before, "DISCOVERY must not be mutated by reconciliation")

        rec = load_yaml(store / "RECONCILIATION.yaml")
        resolutions = {r.get("key"): r for r in rec.get("resolutions") or []}
        conflicts = {c.get("key"): c for c in rec.get("conflicts") or []}

        require(resolutions["format.line_width"]["selected"]["id"] == "project-format", "narrower project scope must win within equal authority tier")
        require(resolutions["testing.runner"]["selected"]["id"] == "runtime-test", "runtime-native visibility must win when authority and scope are equal")
        require(resolutions["architecture.pattern"]["selected"]["id"] == "authoritative-architecture", "authoritative instruction must stay above derived Intelligence")
        require(conflicts["deployment.mode"]["status"] == "HUMAN_REVIEW", "equal-precedence material conflict must be surfaced")
        require(conflicts["database.migrations"]["status"] == "HUMAN_REVIEW", "contradictory discovery against approved override must be surfaced")
        require(resolutions["database.migrations"]["selected"]["id"] == "approved-migration-policy", "approved override must remain selected when contradicted")
        require(any(c.get("status") == "RESOLVED_BY_PRECEDENCE" for c in rec.get("conflicts") or []), "precedence-resolved conflicts must remain visible rather than silently discarded")

        context = run(
            [sys.executable, str(PI), "context", "--project", str(project), "--runtime", "codex", "--prompt", "modify payment API", "--format", "json"],
            env=env,
        )
        require(context.returncode == 0, f"context failed: {context.stdout} {context.stderr}")
        ctx = json.loads(context.stdout)
        reasons = (ctx.get("fail_policy") or {}).get("reasons") or []
        require("material_context_conflict" in reasons, "material unresolved reconciliation conflict must fail closed for mutation")
        require((ctx.get("reconciliation") or {}).get("status") == "REVIEW_REQUIRED", "Turn Context must expose reconciliation state")

        review = (store / "reviews" / "PROJECT_INTELLIGENCE_REVIEW.html").read_text(encoding="utf-8")
        require("approved_override_contradicted" in review, "review must surface override conflict")
        require("equal_precedence_conflict" in review, "review must surface equal-precedence conflict")

    print("project_intelligence_reconciliation_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''', encoding="utf-8")


def main() -> int:
    patch_project_intelligence()
    patch_cli()
    patch_contract()
    write_evidence()
    print("v0.18.0 reconciliation capability preparation: APPLIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

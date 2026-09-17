#!/usr/bin/env python3
from pathlib import Path

p = Path('scripts/project_intelligence.py')
s = p.read_text(encoding='utf-8')

old = '''def context_manifest(root: Path, runtime: str, prompt: str, explain: bool = False) -> dict[str, Any]:\n'''
new = '''def selected_topics_for_task(available: dict[str, Any], desired_topics: list[str], component: str | None) -> list[tuple[str, dict[str, Any]]]:\n    selected: list[tuple[str, dict[str, Any]]] = []\n    for name, raw in available.items():\n        if not isinstance(raw, dict) or not raw.get("path"):\n            continue\n        semantic = str(raw.get("topic", name))\n        if semantic not in desired_topics:\n            continue\n        owner = raw.get("component")\n        if component and owner not in (None, "", "system", "shared", component):\n            continue\n        selected.append((name, raw))\n    return selected\n\n\ndef scoped_graph_context(graph: dict[str, Any], component: str | None) -> dict[str, Any]:\n    if not component:\n        return {"target_component": None, "nodes": [], "edges": [], "excluded_components": []}\n    nodes = graph.get("nodes") or {}\n    if not isinstance(nodes, dict):\n        nodes = {}\n    selected_ids: set[str] = set()\n    excluded: set[str] = set()\n    for node_id, raw in nodes.items():\n        if not isinstance(raw, dict):\n            continue\n        owner = raw.get("component")\n        if owner in (None, "", "system", "shared", component):\n            selected_ids.add(str(node_id))\n        else:\n            excluded.add(str(owner))\n    selected_nodes = [dict({"id": node_id}, **nodes[node_id]) for node_id in sorted(selected_ids)]\n    selected_edges: list[dict[str, Any]] = []\n    for raw in graph.get("edges") or []:\n        if not isinstance(raw, dict):\n            continue\n        source = str(raw.get("source", ""))\n        target = str(raw.get("target", ""))\n        if source in selected_ids and target in selected_ids:\n            selected_edges.append(dict(raw))\n    return {\n        "target_component": component,\n        "nodes": selected_nodes,\n        "edges": selected_edges,\n        "excluded_components": sorted(excluded),\n    }\n\n\ndef context_manifest(root: Path, runtime: str, prompt: str, explain: bool = False, component: str | None = None) -> dict[str, Any]:\n'''
if old not in s:
    raise SystemExit('context marker missing')
s = s.replace(old, new, 1)

old = '''    available = intel.get("topics") or {}\n    selected: list[str] = []\n    for name in desired_topics:\n        topic = available.get(name)\n        if isinstance(topic, dict) and topic.get("path"):\n            selected.append(str(store / topic["path"]))\n'''
new = '''    available = intel.get("topics") or {}\n    selected_records = selected_topics_for_task(available, desired_topics, component)\n    selected = [str(store / topic["path"]) for _, topic in selected_records]\n    graph = load_yaml(store / "IMPACT_GRAPH.yaml", {"nodes": {}, "edges": []}) if store.exists() else {"nodes": {}, "edges": []}\n    scoped_graph = scoped_graph_context(graph, component)\n'''
if old not in s:
    raise SystemExit('topic selection marker missing')
s = s.replace(old, new, 1)

old = '''            "optional_evidence": [str(store / "DISCOVERY.yaml")] if (store / "DISCOVERY.yaml").exists() else [],\n        },\n'''
new = '''            "optional_evidence": [str(store / "DISCOVERY.yaml")] if (store / "DISCOVERY.yaml").exists() else [],\n            "monorepo": {\n                "target_component": component,\n                "system_summary": (intel.get("architecture") or {}).get("summary"),\n                "selected_topic_keys": [name for name, _ in selected_records],\n                "shared_relationships": scoped_graph,\n            },\n        },\n'''
if old not in s:
    raise SystemExit('context output marker missing')
s = s.replace(old, new, 1)

marker = '''def topic_is_complete(store: Path, name: str, topic: Any) -> bool:\n'''
block = '''def promotion_target_allowed(root: Path, target: Path) -> bool:\n    try:\n        relative = target.resolve().relative_to(root.resolve()).as_posix()\n    except ValueError:\n        return False\n    if target.name in SOURCE_NAMES and target.parent.resolve() == root.resolve():\n        return True\n    return relative.startswith("docs/") and target.suffix.lower() == ".md"\n\n\ndef promote_invariant(root: Path, invariant_id: str, target_path: str, approved: bool) -> dict[str, Any]:\n    if not approved:\n        raise RuntimeError("Promotion requires explicit project/user approval (--approved)")\n    store, mode, pid = intelligence_store(root)\n    intel_path = store / "PROJECT_INTELLIGENCE.yaml"\n    registry_path = store / "SOURCE_REGISTRY.yaml"\n    if not intel_path.exists() or not registry_path.exists():\n        raise RuntimeError("Project Intelligence is not initialized")\n    target = root / target_path\n    if not target.is_file():\n        raise RuntimeError("Promotion target must already exist")\n    if not promotion_target_allowed(root, target):\n        raise RuntimeError("Promotion target must be a root project instruction or docs/*.md")\n\n    with writer_lock(store):\n        intel = load_yaml(intel_path, {})\n        candidates = intel.get("derived_invariants") or []\n        if not isinstance(candidates, list):\n            raise RuntimeError("derived_invariants must be a list")\n        candidate = next((item for item in candidates if isinstance(item, dict) and str(item.get("id")) == invariant_id), None)\n        if candidate is None:\n            raise RuntimeError(f"Derived invariant not found: {invariant_id}")\n        statement = candidate.get("statement") or candidate.get("text") or candidate.get("value")\n        if not isinstance(statement, str) or not statement.strip():\n            if candidate.get("status") == "PROMOTED" and candidate.get("authoritative_source") == target_path:\n                return {"project_id": pid, "mode": mode, "status": "ALREADY_PROMOTED", "target": target_path, "invariant_id": invariant_id}\n            raise RuntimeError("Derived invariant has no promotable statement")\n\n        begin = f"<!-- AIPS:promoted:{invariant_id} -->"\n        end = f"<!-- /AIPS:promoted:{invariant_id} -->"\n        body = target.read_text(encoding="utf-8")\n        managed = f"{begin}\\n- {statement.strip()}\\n{end}"\n        if begin not in body:\n            atomic_text(target, body.rstrip() + "\\n\\n" + managed + "\\n")\n\n        registry = load_yaml(registry_path, {"version": 1, "sources": []})\n        sources = registry.setdefault("sources", [])\n        rel_target = rel(root, target)\n        source = next((item for item in sources if isinstance(item, dict) and item.get("path") == rel_target), None)\n        if source is None:\n            authority = "project_instruction" if target.name in SOURCE_NAMES else "official_document"\n            auto = ["codex"] if target.name.startswith("AGENTS") else ["claude-code"] if target.name == "CLAUDE.md" else ["gemini-cli"] if target.name == "GEMINI.md" else []\n            source = {\n                "id": f"src-{sha(rel_target)[:10]}", "path": rel_target, "authority": authority,\n                "scope": str(Path(rel_target).parent.as_posix()), "hash": file_hash(target),\n                "auto_loaded_by": auto, "content_duplicated": False,\n            }\n            sources.append(source)\n        else:\n            source["hash"] = file_hash(target)\n            source["content_duplicated"] = False\n        registry["sources"] = sorted(sources, key=lambda item: str(item.get("path", "")))\n        visibility = registry.setdefault("runtime_visibility", {})\n        for runtime in ("codex", "claude-code", "gemini-cli"):\n            visibility[runtime] = sorted({str(item.get("path")) for item in sources if runtime in (item.get("auto_loaded_by") or []) and item.get("path")})\n        atomic_yaml(registry_path, registry)\n\n        for key in ("statement", "text", "value"):\n            candidate.pop(key, None)\n        candidate["status"] = "PROMOTED"\n        candidate["authoritative_source"] = rel_target\n        candidate["authoritative_pointer"] = {"path": rel_target, "marker": begin}\n        candidate["promoted_at"] = utc_now()\n        atomic_yaml(intel_path, intel)\n\n    review = render_review(root)\n    return {\n        "project_id": pid, "mode": mode, "status": "PROMOTED", "target": rel(root, target),\n        "invariant_id": invariant_id, "content_duplicated": False, "review_html": str(review),\n    }\n\n\n'''
if marker not in s:
    raise SystemExit('promotion insertion marker missing')
s = s.replace(marker, block + marker, 1)

old = '''    p.add_argument("--explain", action="store_true")\n\n    p = sub.add_parser("reconcile-overrides")\n'''
new = '''    p.add_argument("--explain", action="store_true")\n    p.add_argument("--component")\n\n    p = sub.add_parser("reconcile-overrides")\n'''
if old not in s:
    raise SystemExit('context cli marker missing')
s = s.replace(old, new, 1)

old = '''    p = sub.add_parser("impact-init")\n'''
new = '''    p = sub.add_parser("promote-invariant")\n    p.add_argument("--project", default=os.getcwd())\n    p.add_argument("--invariant-id", required=True)\n    p.add_argument("--target", required=True)\n    p.add_argument("--approved", action="store_true")\n    p.add_argument("--format", choices=["yaml", "json"], default="yaml")\n\n    p = sub.add_parser("impact-init")\n'''
if old not in s:
    raise SystemExit('impact cli marker missing')
s = s.replace(old, new, 1)

old = '''        elif args.command == "context":\n            result = context_manifest(root, args.runtime, args.prompt, args.explain)\n        elif args.command == "reconcile-overrides":\n'''
new = '''        elif args.command == "context":\n            result = context_manifest(root, args.runtime, args.prompt, args.explain, args.component)\n        elif args.command == "reconcile-overrides":\n'''
if old not in s:
    raise SystemExit('dispatch context marker missing')
s = s.replace(old, new, 1)

old = '''        elif args.command == "impact-init":\n            result = impact_init(root, args.prompt, args.change_id)\n'''
new = '''        elif args.command == "promote-invariant":\n            result = promote_invariant(root, args.invariant_id, args.target, args.approved)\n        elif args.command == "impact-init":\n            result = impact_init(root, args.prompt, args.change_id)\n'''
if old not in s:
    raise SystemExit('dispatch impact marker missing')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('patched project_intelligence.py')

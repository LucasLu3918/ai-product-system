"""Generic validator for audited ComfyUI topology templates.

Templates are data (templates/creative/COMFYUI_TOPOLOGY_TEMPLATES.yaml). This
module only checks a workflow against a template: node classes and counts,
exact input keys, fixed links, fixed values and profile/component bindings.
It never decides trust; node-class trust stays in comfyui_workflow_policy.py
and the executor's core allowlist.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any

from creative_errors import Blocked

TOPOLOGY_REASON = "comfy_workflow_topology_invalid"
BINDING_REASON = "comfy_model_profile_invalid"
TEMPLATE_REASON = "comfy_topology_template_invalid"
IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
CLASS_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,63}$")
TEMPLATE_KEYS = {"clip_type", "components", "upsampler", "runtime_schema_class", "roles", "nodes", "links", "bindings", "inventory"}
ROLE_KEYS = {"prompt", "latent", "sampler", "save"}
# Input-image classes never appear in a registered model topology (no file-reading inputs).
TEMPLATE_DENIED_CLASSES = {"LoadImage", "LoadImageMask", "VAEEncode", "VAEEncodeForInpaint", "SetLatentNoiseMask"}
PROFILE_PATHS = {"clip_type", "upsampler.max_length"}
PROFILE_GROUPS = {"sampler"}
BINDING_SOURCES = ("component", "profile", "profile_group", "value", "constraint")
SCALAR_TYPES = (str, int, float, bool)


def _invalid(message: str = "Topology template data is invalid.") -> Blocked:
    return Blocked(TEMPLATE_REASON, message)


def _identifier(value: Any) -> bool:
    return isinstance(value, str) and bool(IDENTIFIER.fullmatch(value))


def _normalize_template(raw: Any, core_classes: set[str]) -> dict[str, Any]:
    if not isinstance(raw, dict) or not set(raw) <= TEMPLATE_KEYS:
        raise _invalid()
    clip_type = raw.get("clip_type")
    components = raw.get("components")
    upsampler = raw.get("upsampler", False)
    if (not isinstance(clip_type, str) or not clip_type.strip() or len(clip_type) > 32
            or not isinstance(components, list) or not components or len(set(components)) != len(components)
            or any(not _identifier(name) for name in components) or not isinstance(upsampler, bool)):
        raise _invalid()
    raw_nodes = raw.get("nodes")
    if not isinstance(raw_nodes, dict) or not raw_nodes:
        raise _invalid()
    nodes: dict[str, dict[str, Any]] = {}
    for name, spec in raw_nodes.items():
        if not _identifier(name) or not isinstance(spec, dict) or not set(spec) <= {"class_type", "inputs", "select"}:
            raise _invalid()
        class_type, inputs, select = spec.get("class_type"), spec.get("inputs"), spec.get("select")
        if (not isinstance(class_type, str) or not CLASS_NAME.fullmatch(class_type) or class_type not in core_classes
                or not isinstance(inputs, list) or not inputs or len(set(inputs)) != len(inputs)
                or any(not _identifier(field) for field in inputs)):
            raise _invalid()
        if select is not None:
            if (not isinstance(select, dict) or set(select) != {"field", "component"}
                    or select["field"] not in inputs or select["component"] not in components):
                raise _invalid()
            select = {"field": select["field"], "component": select["component"]}
        nodes[name] = {"class_type": class_type, "inputs": tuple(inputs), "select": select}
    class_counts = Counter(spec["class_type"] for spec in nodes.values())
    for spec in nodes.values():
        if class_counts[spec["class_type"]] > 1 and spec["select"] is None:
            raise _invalid()
    # Input-image and single-save constraints are part of every audited template, not just profile checks.
    if class_counts["SaveImage"] != 1 or set(class_counts) & TEMPLATE_DENIED_CLASSES:
        raise _invalid()

    roles = raw.get("roles")
    if not isinstance(roles, dict) or set(roles) != ROLE_KEYS:
        raise _invalid()
    prompt = roles["prompt"]
    if not isinstance(prompt, dict) or set(prompt) != {"node", "field"} or prompt["node"] not in nodes or prompt["field"] not in nodes[prompt["node"]]["inputs"]:
        raise _invalid()
    for role in ("latent", "sampler", "save"):
        if roles[role] not in nodes:
            raise _invalid()
    if nodes[roles["sampler"]]["class_type"] != "KSampler" or nodes[roles["save"]]["class_type"] != "SaveImage":
        raise _invalid()
    normalized_roles = {"prompt": {"node": prompt["node"], "field": prompt["field"]},
                        "latent": roles["latent"], "sampler": roles["sampler"], "save": roles["save"]}

    raw_links = raw.get("links", {})
    if not isinstance(raw_links, dict):
        raise _invalid()
    links: list[tuple[str, str, str, int]] = []
    for target, source in raw_links.items():
        dst, _, field = str(target).partition(".")
        src, _, index = str(source).rpartition(".")
        if (dst not in nodes or field not in nodes[dst]["inputs"] or src not in nodes or not index.isdigit()):
            raise _invalid()
        links.append((dst, field, src, int(index)))

    used_components = {spec["select"]["component"] for spec in nodes.values() if spec["select"]}
    bindings: list[dict[str, Any]] = []
    for entry in raw.get("bindings", []):
        normalized = _normalize_binding(entry, nodes, components, upsampler)
        used_components.add(normalized.get("component", ""))
        bindings.append(normalized)
    inventory: list[dict[str, Any]] = []
    for entry in raw.get("inventory", []):
        if not isinstance(entry, dict) or set(entry) - {"class_type", "field", "component", "profile"} or "class_type" not in entry:
            raise _invalid()
        if entry["class_type"] not in class_counts or "field" not in entry or not isinstance(entry.get("field"), str):
            raise _invalid()
        if not any(entry["field"] in spec["inputs"] for spec in nodes.values() if spec["class_type"] == entry["class_type"]):
            raise _invalid()
        source = _source_of(entry, components, upsampler)
        used_components.add(source.get("component", ""))
        inventory.append({"class_type": entry["class_type"], "field": entry["field"], **source})
    if set(components) - used_components:
        raise _invalid()
    runtime_schema_class = raw.get("runtime_schema_class")
    if runtime_schema_class is not None and runtime_schema_class not in class_counts:
        raise _invalid()
    return {"clip_type": clip_type, "components": tuple(components), "upsampler": upsampler,
            "roles": normalized_roles, "nodes": nodes, "links": tuple(links), "bindings": tuple(bindings),
            "inventory": tuple(inventory), "runtime_schema_class": runtime_schema_class}


def _source_of(entry: dict[str, Any], components: list[str], upsampler: bool) -> dict[str, Any]:
    keys = [key for key in ("component", "profile") if key in entry]
    if len(keys) != 1:
        raise _invalid()
    if "component" in keys:
        if entry["component"] not in components:
            raise _invalid()
        return {"component": entry["component"]}
    path = entry["profile"]
    if path not in PROFILE_PATHS or (path.startswith("upsampler.") and not upsampler):
        raise _invalid()
    return {"profile": path}


def _normalize_binding(entry: Any, nodes: dict[str, dict[str, Any]], components: list[str], upsampler: bool) -> dict[str, Any]:
    if not isinstance(entry, dict) or ("node" in entry) == ("class_type" in entry):
        raise _invalid()
    if "node" in entry:
        if entry["node"] not in nodes:
            raise _invalid()
        targets = [entry["node"]]
        scope = {"node": entry["node"]}
    else:
        if not any(spec["class_type"] == entry["class_type"] for spec in nodes.values()):
            raise _invalid()
        targets = [name for name, spec in nodes.items() if spec["class_type"] == entry["class_type"]]
        scope = {"class_type": entry["class_type"]}
    sources = [key for key in BINDING_SOURCES if key in entry]
    if len(sources) != 1:
        raise _invalid()
    source = sources[0]
    if source == "profile_group":
        if "class_type" in scope or entry["profile_group"] not in PROFILE_GROUPS or "field" in entry:
            raise _invalid()
        return {**scope, "kind": source, "group": entry["profile_group"]}
    if not isinstance(entry.get("field"), str) or any(entry["field"] not in nodes[name]["inputs"] for name in targets):
        raise _invalid()
    field = entry["field"]
    if source == "value":
        if not isinstance(entry["value"], SCALAR_TYPES):
            raise _invalid()
        return {**scope, "field": field, "kind": "value", "value": entry["value"]}
    if source == "constraint":
        if entry["constraint"] != "nonempty_string":
            raise _invalid()
        return {**scope, "field": field, "kind": "constraint"}
    if source == "component":
        if entry["component"] not in components:
            raise _invalid()
        return {**scope, "field": field, "kind": "component", "component": entry["component"]}
    path = entry["profile"]
    if path not in PROFILE_PATHS or (path.startswith("upsampler.") and not upsampler):
        raise _invalid()
    return {**scope, "field": field, "kind": "profile", "profile": path}


def normalize_templates(document: Any, *, reviewed_ids: set[str], core_classes: set[str]) -> dict[str, dict[str, Any]]:
    """Validate the template document; every reviewed template id must be defined exactly once."""
    if not isinstance(document, dict) or document.get("version") != 1 or not isinstance(document.get("templates"), dict):
        raise _invalid()
    raw = document["templates"]
    if set(raw) != set(reviewed_ids):
        raise _invalid()
    return {template_id: _normalize_template(raw[template_id], core_classes) for template_id in sorted(reviewed_ids)}


def _same(actual: Any, expected: Any) -> bool:
    """Compare JSON values without treating booleans as integers."""
    if isinstance(actual, bool) or isinstance(expected, bool):
        return isinstance(actual, bool) and isinstance(expected, bool) and actual == expected
    return actual == expected


def _topology_error() -> Blocked:
    return Blocked(TOPOLOGY_REASON, "Workflow does not match its audited topology template.")


def _binding_error() -> Blocked:
    return Blocked(BINDING_REASON, "Workflow model files or fixed profile values do not match the audited topology template.")


def resolve_topology(workflow: dict[str, Any], template: dict[str, Any], config: dict[str, Any], profile: dict[str, Any]) -> dict[str, str]:
    """Return logical node name -> workflow node id after every structural and binding check passes."""
    nodes = template["nodes"]
    expected_classes = Counter(spec["class_type"] for spec in nodes.values())
    actual_classes = Counter(node.get("class_type") for node in workflow.values() if isinstance(node, dict))
    if actual_classes != expected_classes or len(workflow) != sum(expected_classes.values()):
        raise _topology_error()
    ids: dict[str, str] = {}
    for name, spec in nodes.items():
        candidates = [node_id for node_id, node in workflow.items() if node.get("class_type") == spec["class_type"]]
        if spec["select"] is not None:
            field, selected = spec["select"]["field"], config.get(spec["select"]["component"])
            candidates = [node_id for node_id in candidates if _same(workflow[node_id]["inputs"].get(field), selected)]
        if len(candidates) != 1:
            raise _topology_error()
        ids[name] = candidates[0]
    if len(set(ids.values())) != len(ids):
        raise _topology_error()
    for name, spec in nodes.items():
        if set(workflow[ids[name]]["inputs"]) != set(spec["inputs"]):
            raise _topology_error()
    for dst, field, src, index in template["links"]:
        if workflow[ids[dst]]["inputs"].get(field) != [ids[src], index]:
            raise _topology_error()
    for binding in template["bindings"]:
        targets = [ids[binding["node"]]] if "node" in binding else [
            ids[name] for name, spec in nodes.items() if spec["class_type"] == binding["class_type"]]
        for node_id in targets:
            if not _binding_matches(binding, workflow[node_id]["inputs"], config, profile):
                raise _binding_error()
    return ids


def _binding_matches(binding: dict[str, Any], inputs: dict[str, Any], config: dict[str, Any], profile: dict[str, Any]) -> bool:
    kind = binding["kind"]
    if kind == "profile_group":
        group = profile.get(binding["group"])
        if not isinstance(group, dict):
            return False
        return all(value is None or _same(inputs.get(key), value) for key, value in group.items())
    actual = inputs.get(binding["field"])
    if kind == "value":
        return _same(actual, binding["value"])
    if kind == "constraint":
        return isinstance(actual, str) and bool(actual.strip())
    if kind == "component":
        return _same(actual, config.get(binding["component"]))
    return _same(actual, _profile_value(profile, binding["profile"]))


def _profile_value(profile: dict[str, Any], path: str) -> Any:
    """Resolve an allowed profile path: clip_type or upsampler.max_length."""
    if path == "clip_type":
        return profile.get("clip_type")
    return (profile.get("upsampler") or {}).get("max_length")


def inventory_checks(template: dict[str, Any], config: dict[str, Any], profile: dict[str, Any]) -> list[tuple[str, str, Any]]:
    """Return (class_type, field, selected value) tuples that must appear in the local model inventory."""
    checks = []
    for entry in template["inventory"]:
        selected = config.get(entry["component"]) if "component" in entry else _profile_value(profile, entry["profile"])
        checks.append((entry["class_type"], entry["field"], selected))
    return checks

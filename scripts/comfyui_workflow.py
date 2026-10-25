"""API-format workflow parsing, schema checks, binding validation and injection."""
from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any

from comfyui_capabilities import input_choices
from comfyui_workflow_policy import require_safe_node, validate_node_id
from creative_errors import Blocked

MAX_WORKFLOW_BYTES = 4 * 1024 * 1024
MAX_REFERENCE_BINDINGS = 8
MAX_WORKFLOW_NODES = 256
MAX_INPUTS_PER_NODE = 128
MAX_WORKFLOW_NODE_BYTES = 256 * 1024
SAFE_OUTPUT_CLASS = "SaveImage"
FIELD_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")


def parse_workflow(raw: bytes) -> dict[str, Any]:
    if not isinstance(raw, bytes) or len(raw) > MAX_WORKFLOW_BYTES:
        raise Blocked("WORKFLOW_TOO_LARGE", "Workflow exceeds the configured byte limit.", phase="creative.workflow", source="comfyui")
    try:
        workflow = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise Blocked("WORKFLOW_INVALID", "Workflow is not valid API-format JSON.", phase="creative.workflow", source="comfyui") from exc
    if not isinstance(workflow, dict) or not workflow or len(workflow) > MAX_WORKFLOW_NODES:
        raise Blocked("WORKFLOW_INVALID", "Workflow must be a non-empty API graph within the node-count limit.", phase="creative.workflow", source="comfyui")
    for node_id, node in workflow.items():
        if not validate_node_id(node_id) or not isinstance(node, dict) or not isinstance(node.get("class_type"), str):
            raise Blocked("WORKFLOW_INVALID", "Workflow node IDs or entries are invalid.", phase="creative.workflow", source="comfyui")
        if len(json.dumps(node, separators=(",", ":")).encode("utf-8")) > MAX_WORKFLOW_NODE_BYTES:
            raise Blocked("WORKFLOW_INVALID", "A workflow node exceeds the configured size limit.", phase="creative.workflow", source="comfyui")
        inputs = node.get("inputs")
        if not isinstance(inputs, dict) or len(inputs) > MAX_INPUTS_PER_NODE:
            raise Blocked("WORKFLOW_INVALID", "Workflow node inputs are invalid or exceed the field limit.", phase="creative.workflow", source="comfyui")
        if any(not isinstance(name, str) or not FIELD_NAME.fullmatch(name) for name in inputs):
            raise Blocked("WORKFLOW_INPUT_INVALID", "Workflow contains an invalid input field name.", phase="creative.workflow", source="comfyui")
    return workflow


def validate_schema(workflow: dict[str, Any], object_info: dict[str, Any]) -> dict[str, Any]:
    missing_nodes: list[str] = []
    missing_models: list[dict[str, str]] = []
    outputs: list[str] = []
    model_candidates: list[dict[str, Any]] = []
    prompt_candidates: list[dict[str, str]] = []
    seed_candidates: list[dict[str, str]] = []
    width_candidates: list[dict[str, str]] = []
    height_candidates: list[dict[str, str]] = []
    for node_id, node in workflow.items():
        node_class = node["class_type"]
        metadata = object_info.get(node_class)
        if not isinstance(metadata, dict):
            missing_nodes.append(node_class)
            continue
        require_safe_node(node_class, metadata)
        input_schema = metadata.get("input") or {}
        required_fields = input_schema.get("required") or {}
        if not isinstance(required_fields, dict):
            raise Blocked("COMFY_SCHEMA_INVALID", "ComfyUI required-input schema is invalid.", {"node_id": node_id}, phase="creative.workflow_schema", source="comfyui")
        absent = sorted(set(required_fields) - set(node["inputs"]))
        if absent:
            raise Blocked("WORKFLOW_INPUT_INVALID", "Workflow omits required ComfyUI inputs.", {"node_id": node_id, "input_names": absent[:64]}, phase="creative.workflow_schema", source="comfyui")
        allowed_fields: set[str] = set()
        for group in ("required", "optional"):
            fields = input_schema.get(group) or {}
            if isinstance(fields, dict):
                allowed_fields.update(fields)
        for field_name, value in node["inputs"].items():
            if field_name not in allowed_fields:
                raise Blocked("WORKFLOW_INPUT_INVALID", "Workflow field does not exist in the current ComfyUI schema.", {"node_id": node_id, "input_name": field_name}, phase="creative.workflow_schema", source="comfyui")
            spec = (input_schema.get("required") or {}).get(field_name) or (input_schema.get("optional") or {}).get(field_name)
            choices = input_choices(spec)
            if choices is not None and isinstance(value, str) and value not in choices and any(token in field_name.casefold() for token in ("model", "ckpt", "unet", "clip", "vae", "lora", "upscale")):
                missing_models.append({"node_id": node_id, "input_name": field_name, "filename": value})
            if field_name == "filename_prefix" and (
                not isinstance(value, str) or not value or len(value) > 120
                or "/" in value or "\\" in value or ".." in value
            ):
                raise Blocked("WORKFLOW_OUTPUT_PATH_DENIED", "SaveImage output prefix must be a local filename without path components.", {"node_id": node_id, "input_name": field_name}, phase="creative.workflow_schema", source="comfyui")
            if choices is not None and any(token in field_name.casefold() for token in ("model", "ckpt", "unet", "clip", "vae", "lora", "upscale")):
                model_candidates.append({"node_id": node_id, "input_name": field_name, "candidates": [item for item in choices[:200] if isinstance(item, str)]})
            if field_name in {"text", "prompt"} and isinstance(value, str):
                prompt_candidates.append({"node_id": node_id, "input": field_name})
            if field_name in {"seed", "noise_seed"}:
                seed_candidates.append({"node_id": node_id, "input": field_name})
            if field_name in {"width", "image_width"}:
                width_candidates.append({"node_id": node_id, "input": field_name})
            if field_name in {"height", "image_height"}:
                height_candidates.append({"node_id": node_id, "input": field_name})
        if node_class == SAFE_OUTPUT_CLASS:
            outputs.append(node_id)
        for field_name, value in node["inputs"].items():
            if isinstance(value, list):
                if len(value) != 2 or not isinstance(value[0], str) or not isinstance(value[1], int) or isinstance(value[1], bool):
                    raise Blocked("WORKFLOW_LINK_INVALID", "Workflow contains an invalid node connection.", {"node_id": node_id}, phase="creative.workflow_graph", source="comfyui")
                source = workflow.get(value[0])
                if not isinstance(source, dict):
                    raise Blocked("WORKFLOW_LINK_INVALID", "Workflow connection references a missing node.", {"node_id": node_id}, phase="creative.workflow_graph", source="comfyui")
                source_schema = object_info.get(source["class_type"], {})
                source_outputs = source_schema.get("output") or []
                if not isinstance(source_outputs, list) or not 0 <= value[1] < len(source_outputs):
                    raise Blocked("WORKFLOW_LINK_INVALID", "Workflow connection references a missing output slot.", {"node_id": node_id}, phase="creative.workflow_graph", source="comfyui")
                input_spec = (input_schema.get("required") or {}).get(field_name) or (input_schema.get("optional") or {}).get(field_name)
                expected_type = input_spec[0] if isinstance(input_spec, list) and input_spec else None
                actual_type = source_outputs[value[1]]
                if isinstance(expected_type, str) and isinstance(actual_type, str) and expected_type != "*" and actual_type != "*" and expected_type != actual_type:
                    raise Blocked("WORKFLOW_LINK_INVALID", "Workflow connection types do not match the current ComfyUI schema.", {"node_id": node_id, "input_name": field_name}, phase="creative.workflow_graph", source="comfyui")
    if missing_nodes:
        raise Blocked("WORKFLOW_NODE_MISSING", "Workflow requires nodes not present in the current local ComfyUI schema.", {"node_classes": sorted(set(missing_nodes))[:64]}, phase="creative.workflow_schema", source="comfyui")
    if missing_models:
        raise Blocked("MODEL_COMPONENT_MISSING", "Workflow selects model components absent from the current loader schema.", {"missing_components": missing_models[:64]}, phase="creative.workflow_schema", source="comfyui")
    if len(outputs) != 1:
        raise Blocked("WORKFLOW_OUTPUT_INVALID", "Workflow must contain exactly one supported local SaveImage output.", {"output_count": len(outputs)}, phase="creative.workflow_policy", source="comfyui")
    return {"output_node_id": outputs[0], "model_candidates": model_candidates,
            "binding_candidates": {"prompt": prompt_candidates, "seed": seed_candidates,
                                   "width": width_candidates, "height": height_candidates}}


def validate_bindings(bindings: Any, workflow: dict[str, Any], analysis: dict[str, Any], object_info: dict[str, Any] | None = None, values: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(bindings, dict) or set(bindings) - {"prompt", "seed", "width", "height", "steps", "cfg", "output", "reference", "references", "reference_encoder"}:
        raise Blocked("WORKFLOW_BINDING_INVALID", "Dynamic workflow bindings contain unsupported names.", phase="creative.workflow_bindings", source="comfyui")
    validated: dict[str, Any] = {}
    for name in ("prompt", "seed", "width", "height", "steps", "cfg"):
        value = bindings.get(name)
        if value is None:
            continue
        if not isinstance(value, dict) or set(value) != {"node_id", "input"}:
            raise Blocked("WORKFLOW_BINDING_INVALID", "Each scalar binding must name exactly one node_id and input.", {"binding": name}, phase="creative.workflow_bindings", source="comfyui")
        node_id, input_name = str(value["node_id"]), value["input"]
        node = workflow.get(node_id)
        if not isinstance(input_name, str) or not isinstance(node, dict) or input_name not in node["inputs"]:
            raise Blocked("WORKFLOW_BINDING_INVALID", "Binding references a missing node or input.", {"binding": name, "node_id": node_id, "input_name": str(input_name)[:128]}, phase="creative.workflow_bindings", source="comfyui")
        current = node["inputs"][input_name]
        if isinstance(current, (list, dict)):
            raise Blocked("WORKFLOW_BINDING_INVALID", "Bindings may only replace scalar workflow values.", {"binding": name, "node_id": node_id, "input_name": input_name}, phase="creative.workflow_bindings", source="comfyui")
        if name == "prompt" and (not isinstance(current, str) or input_name not in {"text", "prompt"}):
            raise Blocked("WORKFLOW_BINDING_INVALID", "Prompt binding must target a text input.", {"node_id": node_id, "input_name": input_name}, phase="creative.workflow_bindings", source="comfyui")
        if name in {"seed", "width", "height", "steps", "cfg"} and (not isinstance(current, (int, float)) or isinstance(current, bool)):
            raise Blocked("WORKFLOW_BINDING_INVALID", "Numeric binding must target a numeric workflow input.", {"binding": name, "node_id": node_id, "input_name": input_name}, phase="creative.workflow_bindings", source="comfyui")
        if name in {"seed", "width", "height", "steps", "cfg"} and object_info is not None:
            metadata = object_info.get(node["class_type"], {})
            input_schema = metadata.get("input") or {}
            spec = (input_schema.get("required") or {}).get(input_name) or (input_schema.get("optional") or {}).get(input_name)
            kind = spec[0] if isinstance(spec, list) and spec else None
            if name == "cfg" and kind not in {"FLOAT", "INT", "NUMBER"} or name != "cfg" and kind not in {"INT", "NUMBER"}:
                raise Blocked("WORKFLOW_BINDING_INVALID", "Numeric binding does not match the ComfyUI input type.", {"binding": name, "node_id": node_id, "input_name": input_name}, phase="creative.workflow_bindings", source="comfyui")
            options = spec[1] if isinstance(spec, list) and len(spec) > 1 and isinstance(spec[1], dict) else {}
            lower, upper = options.get("min"), options.get("max")
            if lower is not None and not isinstance(lower, (int, float)) or upper is not None and not isinstance(upper, (int, float)) or isinstance(lower, (int, float)) and isinstance(upper, (int, float)) and lower > upper:
                raise Blocked("COMFY_SCHEMA_INVALID", "ComfyUI input range metadata is invalid.", {"node_id": node_id, "input_name": input_name}, phase="creative.workflow_schema", source="comfyui")
            value = (values or {}).get(name)
            if value is not None and (isinstance(lower, (int, float)) and value < lower or isinstance(upper, (int, float)) and value > upper):
                raise Blocked("WORKFLOW_INPUT_INVALID", "Bound value is outside the current ComfyUI input range.", {"binding": name, "node_id": node_id, "input_name": input_name}, phase="creative.workflow_bindings", source="comfyui")
        validated[name] = {"node_id": node_id, "input": input_name}
    output = bindings.get("output")
    if output is not None:
        if not isinstance(output, dict) or set(output) != {"node_id", "kind"} or str(output["node_id"]) != analysis["output_node_id"] or output["kind"] != "local_image":
            raise Blocked("WORKFLOW_BINDING_INVALID", "Output binding must identify the single local image output.", phase="creative.workflow_bindings", source="comfyui")
        validated["output"] = {"node_id": analysis["output_node_id"], "kind": "local_image"}
    reference = bindings.get("reference")
    if reference is not None:
        if not isinstance(reference, dict) or set(reference) != {"node_id", "input"}:
            raise Blocked("WORKFLOW_BINDING_INVALID", "Reference binding must name exactly one node_id and input.", phase="creative.workflow_bindings", source="comfyui")
        node_id, input_name = str(reference["node_id"]), reference["input"]
        node = workflow.get(node_id)
        if not isinstance(node, dict) or node["class_type"] != "LoadImage" or input_name != "image" or input_name not in node["inputs"]:
            raise Blocked("WORKFLOW_BINDING_INVALID", "Reference binding must identify a core LoadImage image input.", phase="creative.workflow_bindings", source="comfyui")
        validated["reference"] = {"node_id": node_id, "input": input_name}
    references = bindings.get("references")
    if references is not None:
        if not isinstance(references, list) or not 1 <= len(references) <= MAX_REFERENCE_BINDINGS:
            raise Blocked("WORKFLOW_BINDING_INVALID", "Reference binding count exceeds the bounded local image limit.", phase="creative.workflow_bindings", source="comfyui")
        validated_references = []
        slots = set()
        nodes = set()
        for item in references:
            if not isinstance(item, dict) or set(item) != {"node_id", "input", "slot"}:
                raise Blocked("WORKFLOW_BINDING_INVALID", "Each reference binding must name node_id, input, and slot.", phase="creative.workflow_bindings", source="comfyui")
            node_id, input_name, slot = str(item["node_id"]), item["input"], item["slot"]
            node = workflow.get(node_id)
            if (not isinstance(node, dict) or node["class_type"] != "LoadImage" or input_name != "image"
                    or input_name not in node["inputs"] or slot != f"image_{len(validated_references) + 1}"
                    or slot in slots or node_id in nodes):
                raise Blocked("WORKFLOW_BINDING_INVALID", "Reference slots must map uniquely to core LoadImage image inputs.", phase="creative.workflow_bindings", source="comfyui")
            slots.add(slot)
            nodes.add(node_id)
            validated_references.append({"node_id": node_id, "input": input_name, "slot": slot})
        encoder = bindings.get("reference_encoder")
        if not isinstance(encoder, dict) or set(encoder) != {"node_id", "input"}:
            raise Blocked("WORKFLOW_BINDING_INVALID", "Multi-reference binding requires a Qwen image encoder binding.", phase="creative.workflow_bindings", source="comfyui")
        encoder_node_id, encoder_input = str(encoder["node_id"]), encoder["input"]
        encoder_node = workflow.get(encoder_node_id)
        if (not isinstance(encoder_node, dict) or encoder_node["class_type"] != "TextEncodeQwenImage21"
                or encoder_input != "images" or encoder_input not in encoder_node["inputs"]):
            raise Blocked("WORKFLOW_BINDING_INVALID", "Reference encoder must target the Qwen Image 2.1 images input.", phase="creative.workflow_bindings", source="comfyui")
        if slots != {f"image_{index}" for index in range(1, len(references) + 1)}:
            raise Blocked("WORKFLOW_BINDING_INVALID", "Reference slots must be contiguous and ordered from image_1.", phase="creative.workflow_bindings", source="comfyui")
        validated["references"] = validated_references
        validated["reference_encoder"] = {"node_id": encoder_node_id, "input": encoder_input}
    return validated


def inject_bindings(workflow: dict[str, Any], bindings: dict[str, Any], values: dict[str, Any], output_prefix: str) -> dict[str, Any]:
    result = deepcopy(workflow)
    for name in ("prompt", "seed", "width", "height", "steps", "cfg"):
        binding = bindings.get(name)
        if binding is not None and name in values:
            result[binding["node_id"]]["inputs"][binding["input"]] = values[name]
    output = bindings.get("output")
    output_id = output["node_id"] if output else next(node_id for node_id, node in result.items() if node["class_type"] == SAFE_OUTPUT_CLASS)
    result[output_id]["inputs"]["filename_prefix"] = output_prefix
    reference = bindings.get("reference")
    if reference is not None and values.get("reference") is not None:
        result[reference["node_id"]]["inputs"][reference["input"]] = values["reference"]
    references = bindings.get("references")
    reference_names = values.get("references")
    if references is not None and reference_names is not None:
        if len(references) != len(reference_names):
            raise Blocked("WORKFLOW_BINDING_INVALID", "The number of staged references does not match the workflow bindings.", phase="creative.workflow_bindings", source="comfyui")
        encoder = bindings["reference_encoder"]
        image_map = {}
        for binding, image_name in zip(references, reference_names, strict=True):
            result[binding["node_id"]]["inputs"][binding["input"]] = image_name
            image_map[binding["slot"]] = [binding["node_id"], 0]
        result[encoder["node_id"]]["inputs"][encoder["input"]] = image_map
    return result

"""Equivalence cases for audited ComfyUI topology templates.

The baseline in golden_before_refactor.json was captured from the hard-coded
executor before topology templates existed. run_cases() must keep reproducing
its provider summaries and final API prompts for every registered system
profile, and its accept/reject outcomes for the single-field mutations below.
"""
from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).resolve().parent
TEMPLATES = FIXTURES.parents[2] / "templates" / "creative"
ZIMAGE_SOURCE = "COMFYUI_Z_IMAGE_TURBO_API.json"
FLUX_SOURCE = "COMFYUI_FLUX3_IMAGE_KLEIN_API.json"
ZIMAGE_CONFIG = {
    "base_url": "http://127.0.0.1:8188", "model_profile": "z-image-turbo", "model_id": "z-image-turbo",
    "unet_name": "z_image_turbo_bf16.safetensors", "clip_name": "qwen_3_4b.safetensors", "vae_name": "ae.safetensors",
    "prompt_node_id": "27", "latent_node_id": "13", "sampler_node_id": "3", "save_node_id": "9",
}
FLUX_CONFIG = {
    "base_url": "http://127.0.0.1:8188", "model_profile": "flux3-image-klein-base-int8", "model_id": "flux3-image-klein-base",
    "unet_name": "flux3-image-klein-base-int8-convrot.safetensors", "clip_name": "qwen3vl_4b_int8_convrot.safetensors",
    "prompt_upsampler_name": "qwen3.5_9b_flux3_prompt_upsampler_w4a8.safetensors", "vae_name": "flux2-vae.safetensors",
    "prompt_node_id": "5", "latent_node_id": "8", "sampler_node_id": "9", "save_node_id": "11",
}
DISTILLED_CONFIG = {**FLUX_CONFIG, "model_profile": "flux3-image-klein-distilled-int8", "model_id": "flux3-image-klein-distilled",
                    "unet_name": "flux3-image-klein-int8-convrot.safetensors"}
BUNDLE = {"operation": "generate", "prompt": "fixture caption", "seed": 7, "width": 64, "height": 64, "steps": 8}
VARIANT_BUNDLE = {**BUNDLE, "prompt": "another fixture caption", "seed": 123, "width": 512, "height": 256, "steps": 12}
# The FLUX 3 executor validates a live TextGenerate schema; this mirrors the installed node's shape.
TEXTGEN_SCHEMA = {"input": {
    "required": {"clip": ["CLIP", {}], "prompt": ["STRING", {"default": ""}], "max_length": ["INT", {"default": 512, "min": 1, "max": 32768}], "sampling_mode": ["COMFY_DYNAMICCOMBO_V3", {"options": [{"key": "on", "inputs": {"required": {"temperature": ["FLOAT", {"default": 0.7, "min": 0.01, "max": 2.0}]}}}, {"key": "off", "inputs": {"required": {}}}]}]},
    "optional": {"thinking": ["BOOLEAN", {"default": False}], "use_default_template": ["BOOLEAN", {"default": True}], "mtp": ["COMBO", {"options": ["auto", "off", "2", "3", "4", "5"]}], "system_prompt": ["STRING", {"forceInput": True}]},
}}

# Single-field mutations of the reference workflows: each maps to a list of (path, value) edits.
# A value of "__DELETE__" removes the key.
ZIMAGE_MUTATIONS: dict[str, list[tuple[list[Any], Any]]] = {
    "z_negative_conditioning": [(["3", "inputs", "negative"], ["27", 0])],
    "z_extra_node": [(["99"], {"class_type": "CustomNode", "inputs": {}})],
    "z_missing_node": [(["33"], "__DELETE__")],
    "z_unet_name_mismatch": [(["28", "inputs", "unet_name"], "z_image_turbo_fp8.safetensors")],
    "z_clip_device": [(["30", "inputs", "device"], "cpu")],
    "z_clip_type": [(["30", "inputs", "type"], "flux3")],
    "z_shift": [(["11", "inputs", "shift"], 4)],
    "z_batch_size": [(["13", "inputs", "batch_size"], 2)],
    "z_cfg_profile": [(["3", "inputs", "cfg"], 5)],
    "z_sampler_name": [(["3", "inputs", "sampler_name"], "euler")],
    "z_denoise": [(["3", "inputs", "denoise"], 0.5)],
    "z_weight_dtype": [(["28", "inputs", "weight_dtype"], "fp8_e4m3fn")],
    "z_vae_link": [(["8", "inputs", "vae"], ["29", 1])],
    "z_extra_input": [(["3", "inputs", "extra"], 1)],
    "z_bool_batch": [(["13", "inputs", "batch_size"], True)],
    "z_save_prefix_untouched_schema": [(["9", "inputs", "filename_prefix"], "x")],
    "z_latent_size_free": [(["13", "inputs", "width"], 512)],
    "z_prompt_link_clip": [(["27", "inputs", "clip"], ["28", 0])],
}
FLUX_MUTATIONS: dict[str, list[tuple[list[Any], Any]]] = {
    "f_encoder_upsampler_swapped": [(["5", "inputs", "clip"], ["2", 0])],
    "f_cfg_profile": [(["9", "inputs", "cfg"], 1)],
    "f_max_length": [(["5", "inputs", "max_length"], 48)],
    "f_system_prompt_empty": [(["5", "inputs", "system_prompt"], "   ")],
    "f_thinking_true": [(["5", "inputs", "thinking"], True)],
    "f_latent_width": [(["8", "inputs", "width"], 512)],
    "f_clip_device": [(["2", "inputs", "device"], "cpu")],
    "f_clip_type": [(["3", "inputs", "type"], "lumina2")],
    "f_extra_node": [(["12"], {"class_type": "CustomNode", "inputs": {}})],
    "f_sampling_mode": [(["5", "inputs", "sampling_mode"], "auto")],
    "f_vae_link": [(["10", "inputs", "vae"], ["2", 0])],
    "f_steps_profile": [(["9", "inputs", "steps"], 30)],
    "f_textgen_missing_key": [(["5", "inputs", "mtp"], "__DELETE__")],
    "f_clip_names_duplicate": [(["3", "inputs", "clip_name"], "qwen3vl_4b_int8_convrot.safetensors")],
    "f_unet_name_mismatch": [(["1", "inputs", "unet_name"], "flux3-image-klein-int8-convrot.safetensors")],
    "f_save_link": [(["11", "inputs", "images"], ["9", 0])],
}


def load_source(name: str) -> dict[str, Any]:
    return json.loads((TEMPLATES / name).read_text(encoding="utf-8"))


def mutate(source: dict[str, Any], edits: list[tuple[list[Any], Any]]) -> dict[str, Any]:
    flow = copy.deepcopy(source)
    for path, value in edits:
        node: Any = flow
        for key in path[:-1]:
            node = node[key]
        if value == "__DELETE__":
            node.pop(path[-1])
        else:
            node[path[-1]] = value
    return flow


def distilled_flux() -> dict[str, Any]:
    return mutate(load_source(FLUX_SOURCE), [(["1", "inputs", "unet_name"], "flux3-image-klein-int8-convrot.safetensors"),
                                             (["9", "inputs", "steps"], 16), (["9", "inputs", "cfg"], 1.0)])


def _attempt(creative: Any, root: Path, config: dict[str, Any], workflow: dict[str, Any], bundle: dict[str, Any]) -> dict[str, Any]:
    name = f"case-{abs(hash(json.dumps(workflow, sort_keys=True)))}.json"
    (root / name).write_text(json.dumps(workflow), encoding="utf-8")
    try:
        _, info = creative.load_comfy_workflow(root, {**config, "workflow_path": name})
    except creative.Blocked as exc:
        return {"accepted": False, "reason_code": exc.reason_code}
    if info["profile"] is not None and info["profile"]["topology"] == "flux3_klein_t2i":
        info["textgen_schema"] = TEXTGEN_SCHEMA
    final = creative.build_comfy_workflow(bundle, info)
    provider = {"prompt_id": info["prompt_id"], "prompt_field": info["prompt_field"], "save_nodes": info["save_nodes"],
                "latent_node_id": info["latent_node_id"], "sampler_node_id": info["sampler_node_id"], "profile": info["profile"]}
    return {"accepted": True, "provider": provider, "final_prompt": final}


def run_cases(creative: Any, root: Path) -> dict[str, Any]:
    """Return the same structure as golden_before_refactor.json for the given creative_execution module."""
    zimage = load_source(ZIMAGE_SOURCE)
    flux = load_source(FLUX_SOURCE)
    result: dict[str, Any] = {"system_profiles": {}, "mutations": {}}
    result["system_profiles"]["z-image-turbo"] = {"config": ZIMAGE_CONFIG, "bundle": BUNDLE,
                                                 "outcome": _attempt(creative, root, ZIMAGE_CONFIG, zimage, BUNDLE)}
    result["system_profiles"]["flux3-image-klein-base-int8"] = {"config": FLUX_CONFIG, "bundle": BUNDLE,
                                                               "outcome": _attempt(creative, root, FLUX_CONFIG, flux, BUNDLE)}
    result["system_profiles"]["flux3-image-klein-distilled-int8"] = {"config": DISTILLED_CONFIG, "bundle": BUNDLE,
                                                                    "outcome": _attempt(creative, root, DISTILLED_CONFIG, distilled_flux(), BUNDLE)}
    result["system_profiles"]["z-image-turbo:variant-bundle"] = {"config": ZIMAGE_CONFIG, "bundle": VARIANT_BUNDLE,
                                                                "outcome": _attempt(creative, root, ZIMAGE_CONFIG, zimage, VARIANT_BUNDLE)}
    result["system_profiles"]["flux3-image-klein-base-int8:variant-bundle"] = {"config": FLUX_CONFIG, "bundle": VARIANT_BUNDLE,
                                                                              "outcome": _attempt(creative, root, FLUX_CONFIG, flux, VARIANT_BUNDLE)}
    for name, edits in ZIMAGE_MUTATIONS.items():
        result["mutations"][name] = {"config": ZIMAGE_CONFIG, "outcome": _attempt(creative, root, ZIMAGE_CONFIG, mutate(zimage, edits), BUNDLE)}
    for name, edits in FLUX_MUTATIONS.items():
        result["mutations"][name] = {"config": FLUX_CONFIG, "outcome": _attempt(creative, root, FLUX_CONFIG, mutate(flux, edits), BUNDLE)}
    return result


def run_in_temp(creative: Any) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="aips-topology-golden-") as temp:
        return run_cases(creative, Path(temp).resolve())

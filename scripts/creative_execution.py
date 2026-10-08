"""Preflight and execute a scoped, local-only creative bundle."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from creative_image_validation import valid_raster

if os.name == "nt":
    msvcrt: Any = importlib.import_module("msvcrt")
else:
    import fcntl

ROOT = Path(__file__).resolve().parents[1]
RASTER_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMAGE_BYTES = 25 * 1024 * 1024
MAX_REFERENCE_BYTES = 12 * 1024 * 1024
MAX_REFERENCE_BATCH_BYTES = 25 * 1024 * 1024
MAX_REFERENCE_IMAGES = 8
MAX_PROMPT_CHARS = 4000
MAX_RETRIES = 2
MAX_TIMEOUT_SECONDS = 3600
TRACE_LIMIT_BYTES = 512 * 1024
COMFY_CHECKPOINT_NODES = {
    "CheckpointLoaderSimple", "CLIPTextEncode", "EmptyLatentImage", "KSampler",
    "VAEDecode", "SaveImage", "LoadImage", "VAEEncode", "VAEEncodeForInpaint",
    "SetLatentNoiseMask", "ImageScale", "ImageCrop",
}
COMFY_ZIMAGE_NODES = {"UNETLoader", "CLIPLoader", "VAELoader", "CLIPTextEncode", "ConditioningZeroOut", "EmptySD3LatentImage", "ModelSamplingAuraFlow", "KSampler", "VAEDecode", "SaveImage"}
COMFY_CORE_NODES = COMFY_CHECKPOINT_NODES | COMFY_ZIMAGE_NODES
MFLUX_CAPABILITIES: dict[str, dict[str, dict[str, str | None]]] = {
    # Keep executable names and argument shapes fixed. Model IDs never become
    # command fragments, and unsupported model/operation pairs fail closed.
    "dev": {
        "generate": {"command": "mflux-generate", "cli_model": "dev", "image_option": None},
        "edit": {"command": "mflux-generate", "cli_model": "dev", "image_option": "--image-path"},
    },
    "schnell": {
        "generate": {"command": "mflux-generate", "cli_model": "schnell", "image_option": None},
        "edit": {"command": "mflux-generate", "cli_model": "schnell", "image_option": "--image-path"},
    },
    "z-image-turbo": {
        "generate": {"command": "mflux-generate-z-image-turbo", "cli_model": "z-image-turbo", "image_option": None},
    },
    "flux2-klein-4b": {
        "generate": {"command": "mflux-generate-flux2", "cli_model": "flux2-klein-4b", "image_option": None},
        "edit": {"command": "mflux-generate-flux2-edit", "cli_model": "flux2-klein-4b", "image_option": "--image-paths"},
    },
    "flux2-klein-9b": {
        "generate": {"command": "mflux-generate-flux2", "cli_model": "flux2-klein-9b", "image_option": None},
        "edit": {"command": "mflux-generate-flux2-edit", "cli_model": "flux2-klein-9b", "image_option": "--image-paths"},
    },
    "flux2-klein-9b-kv": {
        "generate": {"command": "mflux-generate-flux2", "cli_model": "flux2-klein-9b-kv", "image_option": None},
        "edit": {"command": "mflux-generate-flux2-edit", "cli_model": "flux2-klein-9b-kv", "image_option": "--image-paths"},
    },
    "qwen-image-edit-2511": {
        "edit": {"command": "mflux-generate-qwen-edit", "cli_model": "qwen-image-edit", "image_option": "--image-paths"},
    },
}
CHARACTER_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
OFFLINE_ENV = {
    "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "HF_DATASETS_OFFLINE": "1",
    "DIFFUSERS_OFFLINE": "1", "NO_PROXY": "127.0.0.1,localhost,::1",
    "no_proxy": "127.0.0.1,localhost,::1",
}


class Blocked(ValueError):
    def __init__(self, reason_code: str, message: str):
        super().__init__(message)
        self.reason_code = reason_code


class TransientProviderError(RuntimeError):
    pass


def lock_prepare_scope(fd: int) -> None:
    if os.name == "nt":
        os.lseek(fd, 0, os.SEEK_END)
        if os.lseek(fd, 0, os.SEEK_CUR) == 0:
            os.write(fd, b"\0")
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_EX)


def unlock_prepare_scope(fd: int) -> None:
    if os.name == "nt":
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return "sha256:" + value.hexdigest()


def confined(root: Path, raw: str, *, exists: bool = False) -> Path:
    candidate = Path(raw).expanduser()
    if candidate.is_absolute():
        raise Blocked("path_not_relative", "Bundle paths must be relative to the project.")
    try:
        resolved = (root / candidate).resolve(strict=exists)
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise Blocked("path_outside_project", "A bundle path is missing or escapes the project root.") from exc
    return resolved


def is_git_workspace(root: Path) -> bool:
    if any((parent / ".git").exists() for parent in (root, *root.parents)):
        return True
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=3, check=False, shell=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def bundle_input_images(root: Path, value: dict[str, Any]) -> list[Path]:
    multiple = value.get("input_images")
    single = value.get("input_image")
    if multiple not in (None, []) and single not in (None, ""):
        raise Blocked("input_image_ambiguous", "Use either input_image or input_images, not both.")
    if multiple is None or multiple == []:
        raw_paths = [single] if isinstance(single, str) and single else []
    elif isinstance(multiple, list) and 1 <= len(multiple) <= MAX_REFERENCE_IMAGES:
        raw_paths = multiple
    else:
        raise Blocked("input_image_invalid", f"input_images must contain between 1 and {MAX_REFERENCE_IMAGES} project-relative paths.")
    if any(not isinstance(raw, str) or not raw for raw in raw_paths):
        raise Blocked("input_image_invalid", "Every reference image path must be a non-empty string.")
    paths: list[Path] = []
    total_size = 0
    for raw in raw_paths:
        path = confined(root, raw, exists=True)
        if not path.is_file() or path.is_symlink() or path.suffix.lower() not in RASTER_SUFFIXES:
            raise Blocked("input_image_invalid", "Reference images must be regular in-project PNG, JPEG, or WEBP files.")
        size = path.stat().st_size
        if size > MAX_REFERENCE_BYTES:
            raise Blocked("input_image_too_large", "A reference image exceeds the 12 MiB limit.")
        total_size += size
        if total_size > MAX_REFERENCE_BATCH_BYTES:
            raise Blocked("input_images_too_large", "Combined reference images exceed the 25 MiB limit.")
        paths.append(path)
    return paths


def read_bundle(project: Path, bundle_path: str) -> tuple[Path, dict[str, Any]]:
    root = project.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise Blocked("project_not_directory", "Project must be a directory.")
    if is_git_workspace(root):
        raise Blocked("creative_git_workspace", "Creative Bundle execution is restricted to non-Git EPHEMERAL workspaces.")
    bundle = confined(root, bundle_path, exists=True)
    if bundle.suffix.lower() not in {".yaml", ".yml"} or not bundle.is_file():
        raise Blocked("bundle_invalid", "Bundle must be an in-project YAML file.")
    try:
        value = yaml.safe_load(bundle.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise Blocked("bundle_invalid", "Bundle YAML could not be read.") from exc
    if not isinstance(value, dict) or value.get("version") != 1 or value.get("mode") != "EPHEMERAL":
        raise Blocked("bundle_invalid", "Bundle must use version 1 and mode EPHEMERAL.")
    operation = value.get("operation")
    if operation not in {"generate", "edit"}:
        raise Blocked("operation_unsupported", "Operation must be generate or edit.")
    prompt = value.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > MAX_PROMPT_CHARS:
        raise Blocked("prompt_invalid", "Bundle prompt is empty or exceeds the 4000 character limit.")
    output_scope = value.get("output_scope")
    output_path = value.get("output_path")
    if not isinstance(output_scope, str) or not output_scope.strip() or not isinstance(output_path, str):
        raise Blocked("output_scope_invalid", "Bundle must declare an output_scope and output_path.")
    scope = confined(root, output_scope)
    output = confined(root, output_path)
    if scope == root or output == scope or scope not in output.parents:
        raise Blocked("output_scope_invalid", "Output path must be a child of the declared output scope.")
    if output.suffix.lower() not in RASTER_SUFFIXES:
        raise Blocked("output_format_unsupported", "Generated output must use PNG, JPEG, or WEBP.")
    if output.exists() or output.is_symlink():
        raise Blocked("creative_target_exists", "Creative output already exists; choose a new versioned path.")
    manifest = output.parent / "creative-execution-manifest.json"
    if manifest.exists() or manifest.is_symlink():
        raise Blocked("manifest_target_exists", "Execution manifest already exists; choose a new versioned output folder.")
    retries = value.get("max_retries", 0)
    timeout = value.get("timeout_seconds", 900)
    if not isinstance(retries, int) or isinstance(retries, bool) or not 0 <= retries <= MAX_RETRIES:
        raise Blocked("retry_limit_invalid", "max_retries must be between 0 and 2.")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= MAX_TIMEOUT_SECONDS:
        raise Blocked("timeout_invalid", "timeout_seconds must be between 1 and 3600.")
    for key, low, high in (("width", 64, 2048), ("height", 64, 2048), ("steps", 1, 100)):
        number = value.get(key, {"width": 1024, "height": 1024, "steps": 20}[key])
        if not isinstance(number, int) or isinstance(number, bool) or not low <= number <= high:
            raise Blocked("generation_setting_invalid", f"{key} must be an integer between {low} and {high}.")
    if value.get("seed", 0) is not None and (not isinstance(value.get("seed", 0), int) or isinstance(value.get("seed", 0), bool)):
        raise Blocked("generation_setting_invalid", "seed must be an integer.")
    input_images = bundle_input_images(root, value)
    if operation == "edit" and not input_images:
        raise Blocked("input_image_missing", "Edit bundles require an in-project input_image or input_images list.")
    if operation == "generate" and input_images:
        raise Blocked("input_image_unsupported", "Reference images are only supported for edit operations.")
    model = value.get("model")
    if not isinstance(model, dict) or not all(isinstance(model.get(key), str) and model[key].strip() for key in ("id", "license")):
        raise Blocked("model_provenance_missing", "Bundle must declare a model id and license.")
    if model.get("local_path") is not None and (not isinstance(model["local_path"], str) or not Path(model["local_path"]).expanduser().is_absolute()):
        raise Blocked("model_not_local", "MFLUX model_path must be an absolute local path; model downloads are disabled.")
    if not all(isinstance(value.get(key), str) and value[key].strip() for key in ("runtime", "runtime_version")):
        raise Blocked("runtime_provenance_missing", "Bundle must identify the local runtime and its observed version.")
    if not all(isinstance(model.get(key), str) and model[key].strip() for key in ("revision", "license_source")):
        raise Blocked("model_provenance_missing", "Bundle must identify model revision and license source.")
    return root, value


def loopback_base(raw: Any) -> str:
    if not isinstance(raw, str):
        raise Blocked("comfy_endpoint_invalid", "ComfyUI endpoint must be an explicit loopback URL.")
    parsed = urllib.parse.urlsplit(raw)
    host = (parsed.hostname or "").lower()
    allowed = host in {"localhost", "127.0.0.1", "::1"}
    try:
        allowed = allowed or ipaddress.ip_address(host).is_loopback
    except ValueError:
        pass
    if parsed.scheme != "http" or not allowed or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
        raise Blocked("comfy_endpoint_invalid", "ComfyUI must use plain HTTP on a loopback address with no credentials or custom path.")
    return raw.rstrip("/")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "redirect refused", headers, fp)


def local_request(url: str, *, data: bytes | None = None, headers: dict[str, str] | None = None, timeout: float = 2.0, max_bytes: int = MAX_IMAGE_BYTES) -> bytes:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect)
    request = urllib.request.Request(url, data=data, headers=headers or {}, method="POST" if data is not None else "GET")
    try:
        with opener.open(request, timeout=timeout) as response:
            if response.geturl().split("/", 3)[:3] != urllib.parse.urlsplit(url).geturl().split("/", 3)[:3]:
                raise Blocked("comfy_redirect_refused", "ComfyUI redirected outside the requested local endpoint.")
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise Blocked("provider_output_too_large", "Local provider response exceeds the configured byte limit.")
            return body
    except urllib.error.HTTPError as exc:
        if exc.code >= 500:
            raise TransientProviderError("local ComfyUI returned a server error") from exc
        raise Blocked("comfy_request_failed", f"Local ComfyUI request failed with HTTP {exc.code}.") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise TransientProviderError("local ComfyUI could not be reached") from exc


def load_comfy_workflow(root: Path, config: Any) -> tuple[str, dict[str, Any]]:
    if not isinstance(config, dict):
        raise Blocked("comfy_config_invalid", "ComfyUI configuration is required for this provider.")
    base = loopback_base(config.get("base_url"))
    workflow_name = config.get("workflow_path")
    if not isinstance(workflow_name, str):
        raise Blocked("comfy_workflow_invalid", "ComfyUI workflow_path is required.")
    path = confined(root, workflow_name, exists=True)
    if path.suffix.lower() != ".json" or not path.is_file():
        raise Blocked("comfy_workflow_invalid", "ComfyUI workflow must be an in-project API-format JSON file.")
    try:
        workflow = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Blocked("comfy_workflow_invalid", "ComfyUI workflow JSON could not be read.") from exc
    if not isinstance(workflow, dict) or not workflow:
        raise Blocked("comfy_workflow_invalid", "ComfyUI workflow must be a non-empty API-format object.")
    for node in workflow.values():
        if not isinstance(node, dict) or node.get("class_type") not in COMFY_CORE_NODES or not isinstance(node.get("inputs"), dict):
            raise Blocked("comfy_custom_node_blocked", "Only the allowlisted built-in ComfyUI nodes are supported; custom nodes are blocked.")
    prompt_id = str(config.get("prompt_node_id", ""))
    prompt_node = workflow.get(prompt_id)
    if not isinstance(prompt_node, dict) or prompt_node.get("class_type") != "CLIPTextEncode":
        raise Blocked("comfy_prompt_node_invalid", "prompt_node_id must identify a built-in CLIPTextEncode node.")
    save_nodes = [key for key, node in workflow.items() if node.get("class_type") == "SaveImage"]
    if not save_nodes:
        raise Blocked("comfy_save_node_missing", "Workflow must end in a built-in SaveImage node.")
    if config.get("save_node_id") and str(config["save_node_id"]) not in save_nodes:
        raise Blocked("comfy_save_node_invalid", "save_node_id must identify a built-in SaveImage node.")
    if len(save_nodes) != 1:
        raise Blocked("comfy_save_node_invalid", "Workflow must contain exactly one built-in SaveImage node.")
    if config.get("save_node_id"):
        save_nodes = [str(config["save_node_id"])]
    model_profile = config.get("model_profile")
    bundle_model_id = config.get("model_id")
    checkpoint_name = config.get("checkpoint_name")
    if model_profile == "z-image-turbo":
        if bundle_model_id != "z-image-turbo":
            raise Blocked("comfy_model_profile_invalid", "The Z-Image Turbo profile requires model_id z-image-turbo.")
        model_fields = {"unet_name", "clip_name", "vae_name"}
        if any(not isinstance(config.get(key), str) or not config[key].strip() or Path(config[key]).name != config[key] for key in model_fields):
            raise Blocked("comfy_model_profile_invalid", "Z-Image Turbo requires explicit local UNET, CLIP and VAE filenames.")
        expected_types = {"UNETLoader", "CLIPLoader", "VAELoader", "CLIPTextEncode", "ConditioningZeroOut", "EmptySD3LatentImage", "ModelSamplingAuraFlow", "KSampler", "VAEDecode", "SaveImage"}
        if len(workflow) != len(expected_types) or {node["class_type"] for node in workflow.values()} != expected_types:
            raise Blocked("comfy_workflow_topology_invalid", "Z-Image Turbo accepts only its exact built-in split-loader workflow topology.")
        by_type = {node["class_type"]: (key, node["inputs"]) for key, node in workflow.items()}
        expected_inputs = {
            "UNETLoader": {"unet_name", "weight_dtype"}, "CLIPLoader": {"clip_name", "type", "device"},
            "VAELoader": {"vae_name"}, "CLIPTextEncode": {"text", "clip"}, "ConditioningZeroOut": {"conditioning"},
            "EmptySD3LatentImage": {"width", "height", "batch_size"}, "ModelSamplingAuraFlow": {"model", "shift"},
            "KSampler": {"model", "positive", "negative", "latent_image", "seed", "steps", "cfg", "sampler_name", "scheduler", "denoise"},
            "VAEDecode": {"samples", "vae"}, "SaveImage": {"images", "filename_prefix"},
        }
        if any(set(by_type[node_type][1]) != keys for node_type, keys in expected_inputs.items()):
            raise Blocked("comfy_workflow_topology_invalid", "Z-Image Turbo workflow inputs do not match the registered built-in topology.")
        unet_id, unet = by_type["UNETLoader"]
        clip_id, clip = by_type["CLIPLoader"]
        vae_id, vae = by_type["VAELoader"]
        text_id, text = by_type["CLIPTextEncode"]
        zero_id, zero = by_type["ConditioningZeroOut"]
        latent_node_id, latent = by_type["EmptySD3LatentImage"]
        sampling_id, sampling = by_type["ModelSamplingAuraFlow"]
        sampler_node_id, sampler = by_type["KSampler"]
        decode_id, decode = by_type["VAEDecode"]
        save_id, save = by_type["SaveImage"]
        if (unet["unet_name"] != config["unet_name"] or unet["weight_dtype"] != "default"
                or clip["clip_name"] != config["clip_name"] or clip["type"] != "lumina2" or clip["device"] != "default"
                or vae["vae_name"] != config["vae_name"] or sampling["shift"] != 3 or latent.get("batch_size") != 1
                or sampler.get("cfg") != 1 or sampler.get("sampler_name") != "res_multistep"
                or sampler.get("scheduler") != "simple" or sampler.get("denoise") != 1):
            raise Blocked("comfy_model_profile_invalid", "Z-Image Turbo workflow model files or fixed sampler profile do not match configuration.")
        link = lambda node_id: [node_id, 0]
        links = ((sampling, "model", link(unet_id)), (sampler, "model", link(sampling_id)), (text, "clip", link(clip_id)),
                 (zero, "conditioning", link(text_id)), (sampler, "positive", link(text_id)), (sampler, "negative", link(zero_id)),
                 (sampler, "latent_image", link(latent_node_id)), (decode, "samples", link(sampler_node_id)),
                 (decode, "vae", link(vae_id)), (save, "images", link(decode_id)))
        if any(inputs.get(name) != value for inputs, name, value in links):
            raise Blocked("comfy_workflow_topology_invalid", "Z-Image Turbo workflow connections do not match the registered built-in topology.")
        if prompt_id != text_id or (config.get("save_node_id") and str(config["save_node_id"]) != save_id):
            raise Blocked("comfy_workflow_topology_invalid", "Configured prompt or save node does not match the Z-Image Turbo topology.")
        checkpoint_node_id = None
        save_nodes = [save_id]
    elif model_profile is None:
        if any(node["class_type"] not in COMFY_CHECKPOINT_NODES for node in workflow.values()):
            raise Blocked("comfy_custom_node_blocked", "Split-loader nodes are accepted only in the registered Z-Image Turbo profile.")
        checkpoint_node_id = str(config.get("checkpoint_node_id", ""))
        checkpoint_node = workflow.get(checkpoint_node_id)
        if not isinstance(checkpoint_node, dict) or checkpoint_node.get("class_type") != "CheckpointLoaderSimple" or not isinstance(checkpoint_name, str) or not checkpoint_name.strip():
            raise Blocked("comfy_checkpoint_invalid", "checkpoint_node_id and checkpoint_name must identify a built-in local checkpoint node.")
        if checkpoint_node["inputs"].get("ckpt_name") != checkpoint_name:
            raise Blocked("comfy_checkpoint_invalid", "Workflow checkpoint must match the explicitly declared local model.")
        if bundle_model_id and checkpoint_name != bundle_model_id:
            raise Blocked("comfy_checkpoint_invalid", "ComfyUI model id must match the selected workflow checkpoint.")
        checkpoint_nodes = [key for key, node in workflow.items() if node.get("class_type") == "CheckpointLoaderSimple"]
        if checkpoint_nodes != [checkpoint_node_id] or Path(checkpoint_name).name != checkpoint_name:
            raise Blocked("comfy_checkpoint_invalid", "Workflow may use only the explicitly declared local checkpoint node and filename.")
        latent_node_id = str(config.get("latent_node_id", ""))
        sampler_node_id = str(config.get("sampler_node_id", ""))
        if not isinstance(workflow.get(latent_node_id), dict) or workflow[latent_node_id].get("class_type") != "EmptyLatentImage":
            raise Blocked("comfy_generation_node_invalid", "latent_node_id must identify a built-in EmptyLatentImage node.")
    else:
        raise Blocked("comfy_model_profile_invalid", "Unsupported ComfyUI model profile.")
    if not isinstance(workflow.get(sampler_node_id), dict) or workflow[sampler_node_id].get("class_type") != "KSampler":
        raise Blocked("comfy_generation_node_invalid", "sampler_node_id must identify a built-in KSampler node.")
    image_nodes = [key for key, node in workflow.items() if node.get("class_type") == "LoadImage"]
    input_node_id = config.get("input_image_node_id")
    if image_nodes and (len(image_nodes) != 1 or str(input_node_id) != image_nodes[0]):
        raise Blocked("comfy_input_node_invalid", "Workflow may read only the explicitly declared local edit input.")
    if not image_nodes and input_node_id is not None:
        raise Blocked("comfy_input_node_invalid", "input_image_node_id must match one built-in LoadImage node.")
    if model_profile == "z-image-turbo" and (image_nodes or input_node_id is not None):
        raise Blocked("comfy_workflow_topology_invalid", "Z-Image Turbo generate workflows do not accept input-image nodes.")
    return base, {"path": path, "workflow": workflow, "prompt_id": prompt_id, "save_nodes": save_nodes, "checkpoint_node_id": checkpoint_node_id, "latent_node_id": latent_node_id, "sampler_node_id": sampler_node_id, "config": config}


def verify_comfy(root: Path, bundle: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    base, info = load_comfy_workflow(root, bundle.get("comfyui"))
    config = info["config"]
    profile = config.get("model_profile")
    if profile == "z-image-turbo":
        if bundle["operation"] != "generate" or bundle["model"]["id"] != "z-image-turbo":
            raise Blocked("comfy_model_profile_invalid", "The Z-Image Turbo ComfyUI profile supports generate only.")
    elif bundle["model"]["id"] != config["checkpoint_name"]:
        raise Blocked("comfy_checkpoint_invalid", "Bundle model id must match the selected ComfyUI checkpoint.")
    try:
        local_request(base + "/system_stats", timeout=2, max_bytes=256 * 1024)
        if profile == "z-image-turbo":
            inventories = {}
            for node_type in ("UNETLoader", "CLIPLoader", "VAELoader"):
                inventories[node_type] = json.loads(local_request(base + "/object_info/" + node_type, timeout=3, max_bytes=1024 * 1024)).get(node_type, {})
        else:
            object_info = json.loads(local_request(base + "/object_info/CheckpointLoaderSimple", timeout=3, max_bytes=1024 * 1024))
    except TransientProviderError as exc:
        raise Blocked("comfy_unavailable", "Configured local ComfyUI is unavailable.") from exc
    if profile == "z-image-turbo":
        fields = (("UNETLoader", "unet_name", config["unet_name"]), ("CLIPLoader", "clip_name", config["clip_name"]), ("CLIPLoader", "type", "lumina2"), ("VAELoader", "vae_name", config["vae_name"]))
        for node_type, field, selected in fields:
            required = ((inventories[node_type].get("input") or {}).get("required") or {})
            choices = required.get(field, [[]])[0]
            if not isinstance(choices, list) or selected not in choices:
                raise Blocked("comfy_model_unavailable", "A configured Z-Image Turbo model component is not present in the local ComfyUI model list.")
    else:
        node_info = object_info.get("CheckpointLoaderSimple", {})
        required = ((node_info.get("input") or {}).get("required") or {})
        choices = required.get("ckpt_name", [[]])[0]
        if not isinstance(choices, list) or config["checkpoint_name"] not in choices:
            raise Blocked("comfy_model_unavailable", "Selected ComfyUI checkpoint is not present in the local server model list.")
    if bundle["operation"] == "edit":
        input_images = bundle_input_images(root, bundle)
        if len(input_images) != 1:
            raise Blocked("comfy_input_count_unsupported", "The bounded ComfyUI workflow accepts exactly one staged edit reference.")
        cfg = info["config"]
        node_id = str(cfg.get("input_image_node_id", ""))
        node = info["workflow"].get(node_id)
        image_name = cfg.get("input_image_name")
        if not isinstance(node, dict) or node.get("class_type") != "LoadImage" or not isinstance(image_name, str) or Path(image_name).name != image_name:
            raise Blocked("comfy_input_node_invalid", "Edit requires a LoadImage node and a filename already staged in ComfyUI input.")
        source = input_images[0]
        if source.stat().st_size > MAX_REFERENCE_BYTES:
            raise Blocked("input_image_too_large", "Input image exceeds the 12 MiB limit.")
        query = urllib.parse.urlencode({"filename": image_name, "type": "input"})
        staged = local_request(base + "/view?" + query, timeout=5, max_bytes=MAX_REFERENCE_BYTES)
        if hashlib.sha256(staged).digest() != hashlib.sha256(source.read_bytes()).digest():
            raise Blocked("comfy_input_hash_mismatch", "Staged ComfyUI input does not match the selected project reference image.")
    return base, info


def resolve_provider(root: Path, bundle: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    requested = bundle.get("provider", "auto")
    if requested not in {"auto", "mflux_local", "comfyui_local"}:
        raise Blocked("provider_unsupported", "Provider must be auto, mflux_local, or comfyui_local.")
    checks: list[tuple[str, str]] = []
    choices = [requested] if requested != "auto" else ["mflux_local", "comfyui_local"]
    for provider in choices:
        if provider == "mflux_local":
            model_id = bundle["model"].get("id")
            model_capabilities = MFLUX_CAPABILITIES.get(model_id, {}) if isinstance(model_id, str) else {}
            capability = model_capabilities.get(bundle["operation"])
            if capability is None:
                checks.append((provider, "mflux_model_operation_unsupported"))
                continue
            command_name = capability.get("command")
            if not isinstance(command_name, str):
                checks.append((provider, "mflux_model_operation_unsupported"))
                continue
            if capability.get("image_option") == "--image-path" and len(bundle_input_images(root, bundle)) != 1:
                checks.append((provider, "mflux_reference_count_unsupported"))
                if requested != "auto":
                    raise Blocked("mflux_reference_count_unsupported", "This MFLUX command accepts exactly one edit reference.")
                continue
            executable = bundle.get("mflux_executable")
            if not isinstance(executable, str) or not executable:
                executable = shutil.which(command_name)
            if not isinstance(executable, str) or not Path(executable).expanduser().is_absolute():
                checks.append((provider, "executable_not_configured"))
                continue
            if Path(executable).name != command_name:
                checks.append((provider, "mflux_command_mismatch"))
                if requested != "auto":
                    raise Blocked("mflux_command_mismatch", "Configured MFLUX executable does not match the registered model/operation command.")
                continue
            model_path_raw = bundle["model"].get("local_path")
            if not isinstance(model_path_raw, str) or not Path(model_path_raw).expanduser().is_dir():
                checks.append((provider, "model_not_local"))
                if requested != "auto":
                    raise Blocked("BLOCKED_NO_ENGINE", "MFLUX requires an existing local model directory; downloads are disabled.")
                continue
            binary = Path(executable).expanduser().resolve(strict=False)
            if not binary.is_file() or not os.access(binary, os.X_OK):
                checks.append((provider, "executable_unavailable"))
                continue
            return provider, {"executable": binary, "capability": capability}
        if provider == "comfyui_local":
            try:
                base, info = verify_comfy(root, bundle)
                return provider, {"base_url": base, **info}
            except Blocked as exc:
                checks.append((provider, exc.reason_code))
                if requested != "auto":
                    raise
    if requested == "auto" or not choices:
        raise Blocked("BLOCKED_NO_ENGINE", "No configured local image engine passed Creative Preflight. Install no model; configure a local engine and rerun preflight.")
    raise Blocked("BLOCKED_NO_ENGINE", "The selected local image engine is unavailable.")


def preflight(project: Path, bundle_path: str) -> dict[str, Any]:
    root, bundle = read_bundle(project, bundle_path)
    provider, _resolved = resolve_provider(root, bundle)
    return {
        "status": "READY", "reason_code": "local_engine_ready", "provider": provider,
        "operation": bundle["operation"], "output_path": bundle["output_path"],
        "output_scope": bundle["output_scope"], "overwrite": False,
        "max_attempts": bundle.get("max_retries", 0) + 1,
        "timeout_seconds": bundle.get("timeout_seconds", 900),
        "model_id": bundle["model"]["id"], "local_only": True,
    }


def discover(project: Path) -> dict[str, Any]:
    """Inventory fixed local commands without launching engines or downloads."""
    root = project.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise Blocked("project_not_directory", "Project must be a directory.")
    commands = sorted({str(c["command"]) for operations in MFLUX_CAPABILITIES.values() for c in operations.values()})
    runtimes = [{"command": command, "available": bool(shutil.which(command))} for command in commands]
    return {"status": "DISCOVERED", "runtimes": runtimes, "supported_models": sorted(MFLUX_CAPABILITIES),
            "model_status": "NOT_VERIFIED", "generation_executed": False,
            "external_image_egress": False, "next_action": "configure_then_preflight",
            "comfyui_status": "NOT_PROBED_REQUIRES_EXPLICIT_BUNDLE"}


def configure(project: Path, bundle_path: str, settings: dict[str, Any]) -> dict[str, Any]:
    """Create a validated configured Bundle version; never edit the source."""
    allowed = {"provider", "model", "runtime", "runtime_version", "mflux_executable", "comfyui",
               "width", "height", "steps", "seed", "max_retries", "timeout_seconds", "prompt",
               "operation", "input_image", "input_images"}
    if not isinstance(settings, dict) or not settings or set(settings) - allowed:
        raise Blocked("creative_configuration_invalid", "Configuration contains unsupported fields.")
    root, bundle = read_bundle(project, bundle_path)
    source = confined(root, bundle_path, exists=True)
    # Reject symlink components even when they resolve within the project.
    relative = Path(bundle_path)
    if ".." in relative.parts or "\\" in bundle_path or any((root / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
        raise Blocked("creative_configuration_invalid", "Configuration source may not use traversal or symlinks.")
    mapping_fields = {
        "model": {"id", "revision", "local_path", "license", "license_source"},
        "comfyui": {"base_url", "workflow_path", "checkpoint_node_id", "checkpoint_name", "model_id",
                    "prompt_node_id", "latent_node_id", "sampler_node_id", "save_node_id", "input_image_node_id", "input_image_name",
                    "model_profile", "unet_name", "clip_name", "vae_name"},
    }
    for key, keys in mapping_fields.items():
        value = settings.get(key)
        if key in settings and (not isinstance(value, dict) or set(value) - keys):
            raise Blocked("creative_configuration_invalid", f"Unsupported {key} configuration.")
    configured = {**bundle, **settings}
    if not isinstance(configured.get("provider"), str) or configured["provider"] not in {"mflux_local", "comfyui_local"}:
        raise Blocked("provider_unsupported", "Configuration must explicitly select a local provider.")
    if configured["provider"] == "mflux_local":
        model_id = (configured.get("model") or {}).get("id")
        if not isinstance(model_id, str) or configured.get("operation") not in MFLUX_CAPABILITIES.get(model_id, {}):
            raise Blocked("mflux_operation_unsupported", "Unsupported local model/operation pair.")
        configured["comfyui"] = None
    elif not isinstance(configured.get("comfyui"), dict):
        raise Blocked("creative_configuration_invalid", "ComfyUI requires an explicit workflow configuration.")
    else:
        loopback_base(configured["comfyui"].get("base_url"))
        configured["mflux_executable"] = None
    # Bound input before serializing it, including model/runtime strings.
    if len(json.dumps(configured, ensure_ascii=False)) > 32 * 1024:
        raise Blocked("creative_configuration_invalid", "Configuration exceeds its size limit.")
    for number in range(1, 10000):
        target = source.with_name(f"{source.stem}-configured-v{number}.yaml")
        if target.exists() or target.is_symlink():
            continue
        output_scope = f"{bundle['output_scope']}/{source.stem}-configured-v{number}"
        configured.update(output_scope=output_scope, output_path=f"{output_scope}/image{Path(bundle['output_path']).suffix}")
        fd, temp_name = tempfile.mkstemp(prefix=".aips-configure-", suffix=".yaml", dir=source.parent)
        temporary = Path(temp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                yaml.safe_dump(configured, stream, sort_keys=False, allow_unicode=True)
                stream.flush()
                os.fsync(stream.fileno())
            read_bundle(root, temporary.relative_to(root).as_posix())
            provenance = [configured["runtime"], configured["runtime_version"], *(configured["model"][key] for key in ("id", "revision", "license", "license_source"))]
            if any(value.strip().upper() in {"UNCONFIGURED", "UNVERIFIED"} for value in provenance):
                raise Blocked("model_provenance_missing", "Configure observed local model/runtime provenance before preflight.")
            # Local contract checks only; no version command, HTTP, or generation.
            if configured["provider"] == "mflux_local":
                capability = MFLUX_CAPABILITIES[configured["model"]["id"]][configured["operation"]]
                executable = configured.get("mflux_executable")
                if not isinstance(executable, str) or not Path(executable).is_absolute() or Path(executable).name != capability["command"]:
                    raise Blocked("mflux_command_mismatch", "Executable must match the fixed local model registry.")
            else:
                workflow = confined(root, str(configured["comfyui"].get("workflow_path", "")), exists=True)
                if not workflow.is_file():
                    raise Blocked("comfy_workflow_invalid", "A local workflow file is required.")
            try:
                os.link(temporary, target)
            except FileExistsError:
                continue
            return {"status": "CONFIGURED", "bundle": target.relative_to(root).as_posix(), "source_sha256": digest(source),
                    "bundle_sha256": digest(target), "output_scope": output_scope, "overwrite": False,
                    "preflight_status": "NOT_RUN", "generation_executed": False}
        finally:
            temporary.unlink(missing_ok=True)
    raise Blocked("creative_version_exhausted", "No available configuration version remains.")


def prepare(
    project: Path,
    scope: str,
    character_id: str,
    character_name: str,
    summary: str,
    style_intent: str,
    prompt: str,
    identity_features: list[str],
) -> dict[str, Any]:
    """Create a versioned, template-bound creative workspace without overwrites."""
    root = project.expanduser().resolve(strict=True)
    if not root.is_dir() or is_git_workspace(root):
        raise Blocked("creative_ephemeral_required", "Creative preparation is restricted to a non-Git EPHEMERAL workspace.")
    if not isinstance(scope, str) or not scope.strip() or Path(scope).is_absolute() or "\\" in scope or ".." in Path(scope).parts:
        raise Blocked("output_scope_invalid", "Preparation scope must be a project-relative path without parent traversal.")
    scope_path = confined(root, scope)
    if scope_path == root:
        raise Blocked("output_scope_invalid", "Preparation requires an explicit child directory as its output scope.")
    current = root
    for part in Path(scope).parts:
        if part in {"", ".", ".."}:
            raise Blocked("output_scope_invalid", "Preparation scope contains an invalid path component.")
        current = current / part
        if current.is_symlink():
            raise Blocked("output_scope_symlink", "Preparation scope may not contain symlinks.")
    if scope_path.exists() and not scope_path.is_dir():
        raise Blocked("output_scope_invalid", "Preparation scope must be a directory.")
    if not isinstance(character_id, str) or not CHARACTER_ID_PATTERN.fullmatch(character_id):
        raise Blocked("character_id_invalid", "character_id must use 1-64 lowercase letters, numbers, hyphens, or underscores.")
    for name, value, maximum in (
        ("character_name", character_name, 120), ("summary", summary, 600),
        ("style_intent", style_intent, 600), ("prompt", prompt, MAX_PROMPT_CHARS),
    ):
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            raise Blocked("creative_profile_invalid", f"{name} must be non-empty and at most {maximum} characters.")
    if not isinstance(identity_features, list) or not 1 <= len(identity_features) <= 12 or any(
        not isinstance(item, str) or not item.strip() or len(item) > 160 for item in identity_features
    ):
        raise Blocked("creative_profile_invalid", "identity_features must contain 1-12 non-empty entries of at most 160 characters.")
    try:
        character = yaml.safe_load((ROOT / "templates/creative/CHARACTER_PROFILE.yaml").read_text(encoding="utf-8"))
        style = yaml.safe_load((ROOT / "templates/creative/STYLE_PROFILE.yaml").read_text(encoding="utf-8"))
        bundle = yaml.safe_load((ROOT / "templates/creative/CREATIVE_BUNDLE.yaml").read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise Blocked("creative_template_invalid", "AIPS creative templates could not be loaded safely.") from exc
    if not all(isinstance(item, dict) for item in (character, style, bundle)):
        raise Blocked("creative_template_invalid", "AIPS creative templates must be YAML mappings.")
    character.update({"id": character_id, "name": character_name.strip(), "summary": summary.strip(), "identity_features": [item.strip() for item in identity_features], "references": []})
    style.update({"id": f"{character_id}-style", "name": f"{character_name.strip()} style", "intent": style_intent.strip()})
    bundle.update({
        "operation": "generate", "provider": "auto", "prompt": prompt.strip(),
        "model": {"id": "UNCONFIGURED", "revision": "UNVERIFIED", "local_path": None, "license": "UNVERIFIED", "license_source": "UNVERIFIED"},
        "runtime": "UNCONFIGURED", "runtime_version": "UNVERIFIED", "mflux_executable": None,
    })
    scope_path.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(scope_path, 0o700)
    lock_path = scope_path / ".aips-creative-prepare.lock"
    try:
        if lock_path.is_symlink():
            raise OSError("scope lock may not be a symlink")
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
        if hasattr(os, "fchmod"):
            os.fchmod(lock_fd, 0o600)
    except OSError as exc:
        raise Blocked("creative_prepare_failed", "Could not safely lock the selected creative scope.") from exc
    locked = False
    try:
        lock_prepare_scope(lock_fd)
        locked = True
        for version in range(1, 10000):
            final = scope_path / f"{character_id}-v{version}"
            if final.exists() or final.is_symlink():
                continue
            stage = Path(tempfile.mkdtemp(prefix=".aips-creative-prepare-", dir=scope_path))
            try:
                (stage / "bundles").mkdir(mode=0o700)
                (stage / "output/character-v1").mkdir(parents=True, mode=0o700)
                version_root = final.relative_to(root).as_posix()
                bundle["output_scope"] = f"{version_root}/output/character-v1"
                bundle["output_path"] = f"{version_root}/output/character-v1/full-body.png"
                generated = {
                    "README.md": (
                        f"# {character_name.strip()}\n\n"
                        "This local creative workspace was prepared by AIPS.\n\n"
                        "## Next steps\n\n"
                        "1. Review `CHARACTER_PROFILE.yaml` and `STYLE_PROFILE.yaml`.\n"
                        "2. Use `aips creative discover`, then `aips creative configure` to create a configured Bundle version.\n"
                        "3. Run `aips creative preflight` before explicitly executing a generation.\n"
                        "4. Review generated images visually; file validity is not a quality PASS.\n"
                    ),
                    "CHARACTER_PROFILE.yaml": yaml.safe_dump(character, sort_keys=False, allow_unicode=True),
                    "STYLE_PROFILE.yaml": yaml.safe_dump(style, sort_keys=False, allow_unicode=True),
                    "bundles/CREATIVE_BUNDLE.yaml": yaml.safe_dump(bundle, sort_keys=False, allow_unicode=True),
                }
                for relative, content in generated.items():
                    target = stage / relative
                    fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                    with os.fdopen(fd, "w", encoding="utf-8") as stream:
                        stream.write(content)
                        stream.flush()
                        os.fsync(stream.fileno())
                os.rename(stage, final)
                files = [f"{version_root}/{relative}" for relative in generated]
                return {
                    "status": "PREPARED", "reason_code": "creative_workspace_prepared",
                    "version": final.name, "scope": version_root,
                    "bundle": f"{version_root}/bundles/CREATIVE_BUNDLE.yaml",
                    "files": files, "output_scope": f"{version_root}/output/character-v1",
                    "engine_status": "UNCONFIGURED", "overwrite": False,
                }
            except FileExistsError:
                shutil.rmtree(stage, ignore_errors=True)
                continue
            except OSError as exc:
                shutil.rmtree(stage, ignore_errors=True)
                raise Blocked("creative_prepare_failed", "Could not atomically create the versioned creative workspace.") from exc
        raise Blocked("creative_version_exhausted", "No available version number remains in the selected scope.")
    finally:
        if locked:
            unlock_prepare_scope(lock_fd)
        os.close(lock_fd)


def output_magic(path: Path) -> bool:
    return valid_raster(path)


def strip_png_text_metadata(data: bytes) -> bytes:
    """Remove ComfyUI's prompt-bearing PNG text chunks while preserving image chunks."""
    signature = b"\x89PNG\r\n\x1a\n"
    if not data.startswith(signature):
        return data
    output = bytearray(signature)
    offset = len(signature)
    found_iend = False
    while offset + 12 <= len(data):
        size = int.from_bytes(data[offset:offset + 4], "big")
        end = offset + size + 12
        if end > len(data):
            raise Blocked("comfy_output_invalid", "ComfyUI returned a malformed PNG chunk stream.")
        kind = data[offset + 4:offset + 8]
        if kind not in {b"tEXt", b"zTXt", b"iTXt"}:
            output.extend(data[offset:end])
        offset = end
        if kind == b"IEND":
            found_iend = True
            break
    if not found_iend:
        raise Blocked("comfy_output_invalid", "ComfyUI returned a PNG without a complete IEND chunk.")
    return bytes(output)


def mflux_command(root: Path, bundle: dict[str, Any], executable: Path, temp_output: Path) -> list[str]:
    model = bundle["model"]
    model_id = model.get("id")
    capability = MFLUX_CAPABILITIES.get(model_id, {}).get(bundle["operation"]) if isinstance(model_id, str) else None
    if not capability:
        raise Blocked("mflux_model_operation_unsupported", "No registered MFLUX command supports this model and operation.")
    command_name = capability.get("command")
    cli_model = capability.get("cli_model")
    if not isinstance(command_name, str) or not isinstance(cli_model, str):
        raise Blocked("mflux_model_operation_unsupported", "Registered MFLUX command metadata is invalid.")
    if executable.name != command_name:
        raise Blocked("mflux_command_mismatch", "Configured MFLUX executable does not match the registered model/operation command.")
    local_model = str(Path(model["local_path"]).expanduser())
    # MFLUX 0.22's Turbo parser accepts a local --model plus its fixed base;
    # it no longer exposes the legacy --model-path argument.
    model_arguments = (["--model", local_model, "--base-model", cli_model, "--no-exif"]
                       if model_id == "z-image-turbo" else ["--model", cli_model, "--model-path", local_model])
    command: list[str] = [
        str(executable), *model_arguments,
        "--prompt", str(bundle["prompt"]), "--output", str(temp_output), "--steps", str(bundle.get("steps", 20)),
        "--seed", str(bundle.get("seed", 0)), "--width", str(bundle.get("width", 1024)), "--height", str(bundle.get("height", 1024)),
    ]
    image_option = capability["image_option"]
    if image_option:
        images = bundle_input_images(root, bundle)
        if image_option == "--image-path" and len(images) != 1:
            raise Blocked("mflux_reference_count_unsupported", "This MFLUX command accepts exactly one edit reference.")
        command.append(image_option)
        command.extend(str(path) for path in images)
    return command


def mflux_execute(root: Path, bundle: dict[str, Any], provider: dict[str, Any], temp_output: Path, timeout: int) -> None:
    command = mflux_command(root, bundle, provider["executable"], temp_output)
    env = {**os.environ, **OFFLINE_ENV}
    env.pop("HF_TOKEN", None)
    env.pop("HUGGING_FACE_HUB_TOKEN", None)
    try:
        result = subprocess.run(
            command, cwd=Path(bundle["model"]["local_path"]).expanduser(), stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout, check=False,
            shell=False, env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise TransientProviderError("local MFLUX execution timed out") from exc
    except OSError as exc:
        raise Blocked("mflux_execution_failed", "Configured local MFLUX executable could not be started.") from exc
    if result.returncode != 0:
        raise Blocked("mflux_execution_failed", f"Local MFLUX exited with status {result.returncode}; provider output was suppressed.")


def comfy_execute(bundle: dict[str, Any], provider: dict[str, Any], temp_output: Path, timeout: int) -> None:
    workflow = json.loads(json.dumps(provider["workflow"]))
    workflow[provider["prompt_id"]]["inputs"]["text"] = bundle["prompt"]
    workflow[provider["latent_node_id"]]["inputs"].update({"width": bundle.get("width", 1024), "height": bundle.get("height", 1024)})
    workflow[provider["sampler_node_id"]]["inputs"].update({"seed": bundle.get("seed", 0), "steps": bundle.get("steps", 20)})
    if bundle["operation"] == "edit":
        cfg = provider["config"]
        workflow[str(cfg["input_image_node_id"])]["inputs"]["image"] = cfg["input_image_name"]
    for node_id in provider["save_nodes"]:
        workflow[node_id]["inputs"]["filename_prefix"] = "aips_local"
    payload = json.dumps({"prompt": workflow, "client_id": str(uuid.uuid4())}, separators=(",", ":")).encode()
    started = time.monotonic()
    try:
        response = local_request(provider["base_url"] + "/prompt", data=payload, headers={"Content-Type": "application/json"}, timeout=min(timeout, 30), max_bytes=256 * 1024)
        prompt_id = json.loads(response).get("prompt_id")
        if not isinstance(prompt_id, str) or not prompt_id:
            raise Blocked("comfy_job_invalid", "Local ComfyUI did not return an execution id.")
        while time.monotonic() - started < timeout:
            history_body = local_request(provider["base_url"] + "/history/" + urllib.parse.quote(prompt_id, safe=""), timeout=5, max_bytes=1024 * 1024)
            history = json.loads(history_body).get(prompt_id)
            if history:
                status = history.get("status") or {}
                if status.get("status_str") == "error" or status.get("completed") is False and status.get("messages"):
                    raise Blocked("comfy_execution_failed", "Local ComfyUI workflow failed; provider details were suppressed.")
                outputs = history.get("outputs") or {}
                for node_id in provider["save_nodes"]:
                    images = (outputs.get(node_id) or {}).get("images") or []
                    if not images:
                        continue
                    image = images[0]
                    if not isinstance(image, dict) or image.get("type") != "output":
                        raise Blocked("comfy_output_invalid", "ComfyUI returned an unsupported output reference.")
                    query = urllib.parse.urlencode({"filename": str(image.get("filename", "")), "subfolder": str(image.get("subfolder", "")), "type": "output"})
                    image_bytes = local_request(provider["base_url"] + "/view?" + query, timeout=30, max_bytes=MAX_IMAGE_BYTES)
                    temp_output.write_bytes(strip_png_text_metadata(image_bytes))
                    return
            time.sleep(0.25)
    except TransientProviderError:
        raise
    except (json.JSONDecodeError, KeyError, TypeError, OSError) as exc:
        raise Blocked("comfy_response_invalid", "Local ComfyUI returned an invalid response.") from exc
    raise TransientProviderError("local ComfyUI execution timed out")


def trace_path() -> Path:
    state = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")).expanduser()
    return state / "aips/creative-execution/events.jsonl"


def read_trace(limit: int = 20) -> dict[str, Any]:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    path = trace_path()
    if not path.exists():
        return {"status": "NO_EVENTS", "events": [], "invalid_records": 0}
    allowed = {"at", "provider", "operation", "status", "reason_code", "attempts", "elapsed_ms", "input_sha256", "output_sha256"}
    events: list[dict[str, Any]] = []
    invalid = 0
    for line in path.read_bytes()[-TRACE_LIMIT_BYTES:].splitlines()[-500:]:
        try:
            item = json.loads(line)
            if not isinstance(item, dict) or set(item) - allowed:
                invalid += 1
                continue
            if item.get("provider") not in {"mflux_local", "comfyui_local"} or item.get("operation") not in {"generate", "edit"} or item.get("status") not in {"COMPLETE", "BLOCKED"}:
                invalid += 1
                continue
            if not isinstance(item.get("reason_code"), str) or len(item["reason_code"]) > 80 or not isinstance(item.get("at"), str) or len(item["at"]) > 40:
                invalid += 1
                continue
            if not isinstance(item.get("attempts"), int) or isinstance(item["attempts"], bool) or not 0 <= item["attempts"] <= MAX_RETRIES + 1:
                invalid += 1
                continue
            if not isinstance(item.get("elapsed_ms"), int) or isinstance(item["elapsed_ms"], bool) or not 0 <= item["elapsed_ms"] <= MAX_TIMEOUT_SECONDS * 1000:
                invalid += 1
                continue
            for key in ("input_sha256", "output_sha256"):
                value = item.get(key)
                if value is not None and (not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:") or any(char not in "0123456789abcdef" for char in value[7:])):
                    raise ValueError("invalid digest")
            events.append(item)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            invalid += 1
    return {"status": "READY" if events else "NO_EVENTS", "invalid_records": invalid, "events": events[-limit:]}


def record_trace(event: dict[str, Any]) -> None:
    allowed = {"at", "provider", "operation", "status", "reason_code", "attempts", "elapsed_ms", "input_sha256", "output_sha256"}
    if set(event) - allowed:
        return
    try:
        path = trace_path()
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(path.parent, 0o700)
        if path.exists() and path.stat().st_size > TRACE_LIMIT_BYTES:
            path.write_text("", encoding="utf-8")
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        os.chmod(path, 0o600)
    except OSError:
        pass


def atomic_manifest(path: Path, value: dict[str, Any]) -> None:
    fd, temporary = tempfile.mkstemp(prefix=".aips-creative-manifest-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.link(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def execute(project: Path, bundle_path: str) -> dict[str, Any]:
    root, bundle = read_bundle(project, bundle_path)
    bundle_file = confined(root, bundle_path, exists=True)
    bundle_hash = digest(bundle_file)
    profile_dir = bundle_file.parent.parent
    profiles = [{"path": path.relative_to(root).as_posix(), "sha256": digest(path)}
                for name in ("CHARACTER_PROFILE.yaml", "STYLE_PROFILE.yaml")
                if bundle_file.parent.name == "bundles" and profile_dir.is_relative_to(root)
                and (path := profile_dir / name).is_file() and not path.is_symlink()]
    provider_name, provider = resolve_provider(root, bundle)
    output = confined(root, bundle["output_path"])
    sources = bundle_input_images(root, bundle)
    source = sources[0] if sources else None
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.parent.is_symlink() or not output.parent.resolve().is_relative_to(confined(root, bundle["output_scope"])):
        raise Blocked("output_scope_escape", "Output directory escaped the declared bundle scope.")
    if output.exists() or output.is_symlink():
        raise Blocked("creative_target_exists", "Creative output already exists; choose a new versioned path.")
    manifest_path = output.parent / "creative-execution-manifest.json"
    if manifest_path.exists() or manifest_path.is_symlink():
        raise Blocked("manifest_target_exists", "Execution manifest already exists; choose a new versioned output folder.")
    fd, temp_name = tempfile.mkstemp(prefix=".aips-creative-output-", suffix=output.suffix.lower(), dir=output.parent)
    os.close(fd)
    temp_output = Path(temp_name)
    temp_output.unlink()
    started = time.monotonic()
    attempts = 0
    try:
        for attempt in range(bundle.get("max_retries", 0) + 1):
            attempts = attempt + 1
            temp_output.unlink(missing_ok=True)
            try:
                if provider_name == "mflux_local":
                    mflux_execute(root, bundle, provider, temp_output, bundle.get("timeout_seconds", 900))
                else:
                    comfy_execute(bundle, provider, temp_output, bundle.get("timeout_seconds", 900))
                if not output_magic(temp_output):
                    raise Blocked("provider_output_invalid", "Local engine did not produce a supported image within the byte limit.")
                break
            except TransientProviderError:
                if attempts > bundle.get("max_retries", 0):
                    raise Blocked("provider_timeout", "Local image engine timed out after the configured finite retry limit.")
        if digest(bundle_file) != bundle_hash or any(digest(confined(root, profile["path"], exists=True)) != profile["sha256"] for profile in profiles):
            raise Blocked("creative_inputs_changed", "Bundle or identity/style profiles changed during generation; output was not published.")
        output_hash = digest(temp_output)
        os.link(temp_output, output)
        elapsed = round((time.monotonic() - started) * 1000)
        input_records = [{"sha256": digest(path), "path": path.relative_to(root).as_posix()} for path in sources]
        manifest = {
            "version": 1, "status": "COMPLETE", "operation": bundle["operation"], "provider": provider_name,
            "model": {"id": bundle["model"]["id"], "revision": bundle["model"]["revision"], "runtime": bundle["runtime"], "runtime_version": bundle["runtime_version"], "license": bundle["model"]["license"], "license_source": bundle["model"]["license_source"], "location": "local"},
            "bundle_sha256": bundle_hash,
            "profiles": profiles,
            "workflow_sha256": digest(provider["path"]) if provider_name == "comfyui_local" else None,
            "input": input_records[0] if len(input_records) == 1 else None,
            "inputs": input_records if len(input_records) > 1 else [],
            "output": {"path": bundle["output_path"], "sha256": output_hash, "format": output.suffix.lower().lstrip("."), "bytes": output.stat().st_size},
            "output_scope": bundle["output_scope"],
            "prompt_sha256": "sha256:" + hashlib.sha256(bundle["prompt"].encode()).hexdigest(),
            "execution": {"attempts": attempts, "retry_count": attempts - 1, "elapsed_ms": elapsed, "completed_at": datetime.now(UTC).isoformat()},
            "review": {"status": "PENDING", "reviewer": None, "decision": None, "reviewed_at": None},
            "acceptance": {"file_validity": "PASS", "visual_quality": "PENDING", "user_acceptance": "NOT_RECORDED"},
            "validation_scope": "bounded_container_checks_not_visual_quality",
            "privacy": {"raw_prompt_stored": False, "image_bytes_stored_in_manifest": False, "external_image_egress": False},
        }
        try:
            atomic_manifest(manifest_path, manifest)
        except OSError:
            output.unlink(missing_ok=True)
            raise Blocked("manifest_write_failed", "Could not safely create the provenance manifest; generated output was rolled back.")
        input_hash = digest(source) if source else None
        record_trace({"at": datetime.now(UTC).isoformat(), "provider": provider_name, "operation": bundle["operation"], "status": "COMPLETE", "reason_code": "execution_complete", "attempts": attempts, "elapsed_ms": elapsed, "input_sha256": input_hash, "output_sha256": output_hash})
        return {"status": "COMPLETE", "reason_code": "execution_complete", "provider": provider_name, "output": bundle["output_path"], "manifest": str(manifest_path.relative_to(root)), "review_status": "PENDING", "attempts": attempts, "elapsed_ms": elapsed, "overwrite": False}
    except Blocked as exc:
        record_trace({"at": datetime.now(UTC).isoformat(), "provider": provider_name, "operation": bundle["operation"], "status": "BLOCKED", "reason_code": exc.reason_code, "attempts": attempts, "elapsed_ms": round((time.monotonic() - started) * 1000), "input_sha256": digest(source) if source else None, "output_sha256": None})
        raise
    finally:
        temp_output.unlink(missing_ok=True)


def review(project: Path, manifest_name: str, reviewer: str, decision: str, note: str) -> dict[str, Any]:
    root = project.expanduser().resolve(strict=True)
    manifest = confined(root, manifest_name, exists=True)
    if manifest.name != "creative-execution-manifest.json" or not manifest.is_file():
        raise Blocked("manifest_invalid", "Review target must be a generated creative execution manifest.")
    if is_git_workspace(root):
        raise Blocked("creative_git_workspace", "Creative review records are restricted to the non-Git EPHEMERAL project.")
    if not reviewer.strip() or len(reviewer) > 120 or decision not in {"PASS", "REVISE"} or len(note) > 1000:
        raise Blocked("review_invalid", "Review requires a reviewer, PASS/REVISE decision, and a note of at most 1000 characters.")
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Blocked("manifest_invalid", "Execution manifest is invalid.") from exc
    output_path = confined(root, str((data.get("output") or {}).get("path", "")), exists=True)
    output_scope = confined(root, str(data.get("output_scope", "")))
    if output_scope == root or output_scope not in output_path.parents:
        raise Blocked("manifest_scope_invalid", "Generated output no longer matches its declared bundle scope.")
    if digest(output_path) != (data.get("output") or {}).get("sha256"):
        raise Blocked("manifest_hash_mismatch", "Generated output no longer matches its provenance hash.")
    for profile in data.get("profiles", []):
        if digest(confined(root, profile["path"], exists=True)) != profile["sha256"]:
            raise Blocked("profile_hash_mismatch", "Reviewed identity/style profile changed after generation.")
    data["review"] = {"status": decision, "reviewer": reviewer.strip(), "decision": decision, "note": note.strip(), "reviewed_at": datetime.now(UTC).isoformat()}
    if isinstance(data.get("acceptance"), dict):
        data["acceptance"]["visual_quality"] = decision
    replacement = manifest.with_name(".creative-execution-manifest.review.tmp")
    replacement.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.chmod(replacement, 0o600)
    os.replace(replacement, manifest)
    return {"status": "REVIEWED", "decision": decision, "manifest": str(manifest.relative_to(root))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--project", type=Path, required=True)
    prepare_parser.add_argument("--scope", required=True)
    prepare_parser.add_argument("--character-id", required=True)
    prepare_parser.add_argument("--character-name", required=True)
    prepare_parser.add_argument("--summary", required=True)
    prepare_parser.add_argument("--style-intent", required=True)
    prepare_parser.add_argument("--prompt", required=True)
    prepare_parser.add_argument("--identity-feature", action="append", default=[])
    discover_parser = sub.add_parser("discover")
    discover_parser.add_argument("--project", type=Path, required=True)
    configure_parser = sub.add_parser("configure")
    configure_parser.add_argument("--project", type=Path, required=True)
    configure_parser.add_argument("--bundle", required=True)
    configure_parser.add_argument("--settings-json", help="Bounded JSON settings; omitted means stdin (no prompt in argv).")
    for action in ("preflight", "execute"):
        command = sub.add_parser(action)
        command.add_argument("--project", type=Path, required=True)
        command.add_argument("--bundle", required=True)
    review_parser = sub.add_parser("review")
    review_parser.add_argument("--project", type=Path, required=True)
    review_parser.add_argument("--manifest", required=True)
    review_parser.add_argument("--reviewer", required=True)
    review_parser.add_argument("--decision", choices=("PASS", "REVISE"), required=True)
    review_parser.add_argument("--note", default="")
    trace_parser = sub.add_parser("trace")
    trace_parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            result = prepare(args.project, args.scope, args.character_id, args.character_name, args.summary, args.style_intent, args.prompt, args.identity_feature)
        elif args.action == "discover":
            result = discover(args.project)
        elif args.action == "configure":
            raw = args.settings_json if args.settings_json is not None else sys.stdin.read(32 * 1024 + 1)
            if len(raw) > 32 * 1024:
                raise Blocked("creative_configuration_invalid", "Configuration exceeds its size limit.")
            result = configure(args.project, args.bundle, json.loads(raw))
        elif args.action == "preflight":
            result = preflight(args.project, args.bundle)
        elif args.action == "execute":
            result = execute(args.project, args.bundle)
        elif args.action == "review":
            result = review(args.project, args.manifest, args.reviewer, args.decision, args.note)
        else:
            result = read_trace(args.limit)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Blocked as exc:
        print(json.dumps({"status": "BLOCKED", "reason_code": exc.reason_code, "message": str(exc)}, ensure_ascii=False))
        return 2
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason_code": "creative_execution_error", "message": type(exc).__name__}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

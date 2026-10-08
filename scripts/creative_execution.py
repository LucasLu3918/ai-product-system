"""Preflight and execute a scoped, local-only creative bundle."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import subprocess
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

ROOT = Path(__file__).resolve().parents[1]
RASTER_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMAGE_BYTES = 25 * 1024 * 1024
MAX_REFERENCE_BYTES = 12 * 1024 * 1024
MAX_PROMPT_CHARS = 4000
MAX_RETRIES = 2
MAX_TIMEOUT_SECONDS = 3600
TRACE_LIMIT_BYTES = 512 * 1024
COMFY_CORE_NODES = {
    "CheckpointLoaderSimple", "CLIPTextEncode", "EmptyLatentImage", "KSampler",
    "VAEDecode", "SaveImage", "LoadImage", "VAEEncode", "VAEEncodeForInpaint",
    "SetLatentNoiseMask", "ImageScale", "ImageCrop",
}
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
    if operation == "edit":
        source = value.get("input_image")
        if not isinstance(source, str) or not source:
            raise Blocked("input_image_missing", "Edit bundles require an in-project input_image.")
        source_path = confined(root, source, exists=True)
        if not source_path.is_file() or source_path.is_symlink() or source_path.suffix.lower() not in RASTER_SUFFIXES:
            raise Blocked("input_image_invalid", "Input image must be a regular in-project PNG, JPEG, or WEBP file.")
        if source_path.stat().st_size > MAX_REFERENCE_BYTES:
            raise Blocked("input_image_too_large", "Input image exceeds the 12 MiB limit.")
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
    checkpoint_node_id = str(config.get("checkpoint_node_id", ""))
    checkpoint_node = workflow.get(checkpoint_node_id)
    checkpoint_name = config.get("checkpoint_name")
    if not isinstance(checkpoint_node, dict) or checkpoint_node.get("class_type") != "CheckpointLoaderSimple" or not isinstance(checkpoint_name, str) or not checkpoint_name.strip():
        raise Blocked("comfy_checkpoint_invalid", "checkpoint_node_id and checkpoint_name must identify a built-in local checkpoint node.")
    bundle_model_id = config.get("model_id")
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
    if not isinstance(workflow.get(sampler_node_id), dict) or workflow[sampler_node_id].get("class_type") != "KSampler":
        raise Blocked("comfy_generation_node_invalid", "sampler_node_id must identify a built-in KSampler node.")
    image_nodes = [key for key, node in workflow.items() if node.get("class_type") == "LoadImage"]
    input_node_id = config.get("input_image_node_id")
    if image_nodes and (len(image_nodes) != 1 or str(input_node_id) != image_nodes[0]):
        raise Blocked("comfy_input_node_invalid", "Workflow may read only the explicitly declared local edit input.")
    if not image_nodes and input_node_id is not None:
        raise Blocked("comfy_input_node_invalid", "input_image_node_id must match one built-in LoadImage node.")
    return base, {"path": path, "workflow": workflow, "prompt_id": prompt_id, "save_nodes": save_nodes, "checkpoint_node_id": checkpoint_node_id, "latent_node_id": latent_node_id, "sampler_node_id": sampler_node_id, "config": config}


def verify_comfy(root: Path, bundle: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    base, info = load_comfy_workflow(root, bundle.get("comfyui"))
    if bundle["model"]["id"] != info["config"]["checkpoint_name"]:
        raise Blocked("comfy_checkpoint_invalid", "Bundle model id must match the selected ComfyUI checkpoint.")
    try:
        local_request(base + "/system_stats", timeout=2, max_bytes=256 * 1024)
        object_info = json.loads(local_request(base + "/object_info/CheckpointLoaderSimple", timeout=3, max_bytes=1024 * 1024))
    except TransientProviderError as exc:
        raise Blocked("comfy_unavailable", "Configured local ComfyUI is unavailable.") from exc
    node_info = object_info.get("CheckpointLoaderSimple", {})
    required = ((node_info.get("input") or {}).get("required") or {})
    choices = required.get("ckpt_name", [[]])[0]
    if not isinstance(choices, list) or info["config"]["checkpoint_name"] not in choices:
        raise Blocked("comfy_model_unavailable", "Selected ComfyUI checkpoint is not present in the local server model list.")
    if bundle["operation"] == "edit":
        cfg = info["config"]
        node_id = str(cfg.get("input_image_node_id", ""))
        node = info["workflow"].get(node_id)
        image_name = cfg.get("input_image_name")
        if not isinstance(node, dict) or node.get("class_type") != "LoadImage" or not isinstance(image_name, str) or Path(image_name).name != image_name:
            raise Blocked("comfy_input_node_invalid", "Edit requires a LoadImage node and a filename already staged in ComfyUI input.")
        source = confined(root, bundle["input_image"], exists=True)
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
            executable = bundle.get("mflux_executable")
            model_path_raw = bundle["model"].get("local_path")
            if not isinstance(executable, str) or not Path(executable).expanduser().is_absolute():
                checks.append((provider, "executable_not_configured"))
                continue
            if not isinstance(model_path_raw, str) or not Path(model_path_raw).expanduser().is_dir():
                checks.append((provider, "model_not_local"))
                if requested != "auto":
                    raise Blocked("BLOCKED_NO_ENGINE", "MFLUX requires an existing local model directory; downloads are disabled.")
                continue
            binary = Path(executable).expanduser().resolve(strict=False)
            if not binary.is_file() or not os.access(binary, os.X_OK):
                checks.append((provider, "executable_unavailable"))
                continue
            return provider, {"executable": binary}
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


def output_magic(path: Path) -> bool:
    try:
        size = path.stat().st_size
        if size <= 0 or size > MAX_IMAGE_BYTES:
            return False
        with path.open("rb") as stream:
            head = stream.read(16)
        suffix = path.suffix.lower()
        if suffix == ".png":
            return head.startswith(b"\x89PNG\r\n\x1a\n")
        if suffix in {".jpg", ".jpeg"}:
            return head.startswith(b"\xff\xd8\xff")
        if suffix == ".webp":
            return head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    except OSError:
        return False
    return False


def mflux_command(root: Path, bundle: dict[str, Any], executable: Path, temp_output: Path) -> list[str]:
    model = bundle["model"]
    command = [
        str(executable), "--model", str(model["id"]), "--model-path", str(Path(model["local_path"]).expanduser()),
        "--prompt", str(bundle["prompt"]), "--output", str(temp_output), "--steps", str(bundle.get("steps", 20)),
        "--seed", str(bundle.get("seed", 0)), "--width", str(bundle.get("width", 1024)), "--height", str(bundle.get("height", 1024)),
    ]
    if bundle["operation"] == "edit":
        command.extend(["--image-path", str(confined(root, bundle["input_image"], exists=True))])
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
                    temp_output.write_bytes(local_request(provider["base_url"] + "/view?" + query, timeout=30, max_bytes=MAX_IMAGE_BYTES))
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
    provider_name, provider = resolve_provider(root, bundle)
    output = confined(root, bundle["output_path"])
    source = confined(root, bundle["input_image"], exists=True) if bundle.get("input_image") else None
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
        output_hash = digest(temp_output)
        os.link(temp_output, output)
        elapsed = round((time.monotonic() - started) * 1000)
        manifest = {
            "version": 1, "status": "COMPLETE", "operation": bundle["operation"], "provider": provider_name,
            "model": {"id": bundle["model"]["id"], "revision": bundle["model"]["revision"], "runtime": bundle["runtime"], "runtime_version": bundle["runtime_version"], "license": bundle["model"]["license"], "license_source": bundle["model"]["license_source"], "location": "local"},
            "bundle_sha256": digest(confined(root, bundle_path, exists=True)),
            "workflow_sha256": digest(provider["path"]) if provider_name == "comfyui_local" else None,
            "input": {"sha256": digest(source), "path": bundle["input_image"]} if source else None,
            "output": {"path": bundle["output_path"], "sha256": output_hash, "format": output.suffix.lower().lstrip("."), "bytes": output.stat().st_size},
            "output_scope": bundle["output_scope"],
            "prompt_sha256": "sha256:" + hashlib.sha256(bundle["prompt"].encode()).hexdigest(),
            "execution": {"attempts": attempts, "retry_count": attempts - 1, "elapsed_ms": elapsed, "completed_at": datetime.now(UTC).isoformat()},
            "review": {"status": "PENDING", "reviewer": None, "decision": None, "reviewed_at": None},
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
    data["review"] = {"status": decision, "reviewer": reviewer.strip(), "decision": decision, "note": note.strip(), "reviewed_at": datetime.now(UTC).isoformat()}
    replacement = manifest.with_name(".creative-execution-manifest.review.tmp")
    replacement.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.chmod(replacement, 0o600)
    os.replace(replacement, manifest)
    return {"status": "REVIEWED", "decision": decision, "manifest": str(manifest.relative_to(root))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
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
        if args.action == "preflight":
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
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason_code": "creative_execution_error", "message": type(exc).__name__}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Synthetic local-only lifecycle for Creative Bundle execution."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zlib
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import creative_execution as creative
import opencode_native_guard as guard
from creative_request_policy_lifecycle import main as request_policy_cases

PNG = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c6360000200000500017a5eab3f0000000049454e44ae426082")
_prompt_text = b"prompt\x00private creative prompt"
_text_chunk = len(_prompt_text).to_bytes(4, "big") + b"tEXt" + _prompt_text + zlib.crc32(b"tEXt" + _prompt_text).to_bytes(4, "big")
PNG_WITH_PROMPT = PNG[:-12] + _text_chunk + PNG[-12:]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def multi_reference_binding_cases() -> None:
    require(creative.safe_comfy_input_name("reference 1.png"), "safe ComfyUI input filename was rejected")
    require(not any(creative.safe_comfy_input_name(name) for name in ("../secret.png", "..\\secret.png", "..", "")),
            "unsafe ComfyUI staged filename was accepted")
    workflow = {
        str(index): {"class_type": "LoadImage", "inputs": {"image": "placeholder.png"}}
        for index in range(1, 4)
    }
    workflow["encoder"] = {"class_type": "TextEncodeQwenImage21", "inputs": {"images": {}}}
    workflow["save"] = {"class_type": "SaveImage", "inputs": {"images": ["encoder", 0], "filename_prefix": "fixture"}}
    analysis = {"nodes": []}
    bindings = {
        "references": [
            {"node_id": node_id, "input": "image", "slot": f"image_{index}"}
            for index, node_id in enumerate(("3", "1", "2"), start=1)
        ],
        "reference_encoder": {"node_id": "encoder", "input": "images"},
    }
    validated = creative.comfyui_workflow.validate_bindings(bindings, workflow, analysis)
    injected = creative.comfyui_workflow.inject_bindings(
        workflow, validated, {"references": ["a.png", "b.png", "c.png"]}, "fixture"
    )
    require(injected["encoder"]["inputs"]["images"] == {
        "image_1": ["3", 0], "image_2": ["1", 0], "image_3": ["2", 0]
    }, "three ordered local references were not injected")
    edit_plus_workflow = {
        "1": {"class_type": "LoadImage", "inputs": {"image": "placeholder-a.png"}},
        "2": {"class_type": "LoadImage", "inputs": {"image": "placeholder-b.png"}},
        "encoder": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {"image1": None, "image2": None, "image3": None}},
        "save": {"class_type": "SaveImage", "inputs": {"images": ["encoder", 0], "filename_prefix": "fixture"}},
    }
    edit_plus_bindings = {
        "references": [
            {"node_id": "1", "input": "image", "slot": "image_1"},
            {"node_id": "2", "input": "image", "slot": "image_2"},
        ],
        "reference_encoder": {"node_id": "encoder", "input": "image1"},
    }
    edit_plus_validated = creative.comfyui_workflow.validate_bindings(edit_plus_bindings, edit_plus_workflow, analysis)
    edit_plus_injected = creative.comfyui_workflow.inject_bindings(
        edit_plus_workflow, edit_plus_validated, {"references": ["identity.png", "product.png"]}, "edit-plus"
    )
    require(edit_plus_injected["encoder"]["inputs"]["image1"] == ["1", 0]
            and edit_plus_injected["encoder"]["inputs"]["image2"] == ["2", 0]
            and edit_plus_injected["encoder"]["inputs"]["image3"] is None,
            "Qwen Edit Plus did not preserve the two ordered identity/product reference slots")
    require(edit_plus_injected["1"]["inputs"]["image"] == "identity.png"
            and edit_plus_injected["2"]["inputs"]["image"] == "product.png",
            "Qwen Edit Plus references were not staged into their distinct LoadImage nodes")
    expect_blocked(lambda: creative.comfyui_workflow.validate_bindings(
        {**edit_plus_bindings, "reference_encoder": {"node_id": "encoder", "input": "images"}}, edit_plus_workflow, analysis
    ), "Qwen Edit Plus accepted the Qwen 2.1 object-map input")
    expect_blocked(lambda: creative.comfyui_workflow.validate_bindings(
        {**edit_plus_bindings, "references": edit_plus_bindings["references"] + [
            {"node_id": "3", "input": "image", "slot": "image_3"},
            {"node_id": "4", "input": "image", "slot": "image_4"},
        ]},
        {**edit_plus_workflow,
         "3": {"class_type": "LoadImage", "inputs": {"image": "placeholder-c.png"}},
         "4": {"class_type": "LoadImage", "inputs": {"image": "placeholder-d.png"}}}, analysis
    ), "Qwen Edit Plus exceeded its three-image encoder limit")
    expect_blocked(lambda: creative.comfyui_workflow.validate_bindings(
        {**edit_plus_bindings, "references": [
            edit_plus_bindings["references"][0], {"node_id": "2", "input": "image", "slot": "image_3"}
        ]}, edit_plus_workflow, analysis
    ), "Qwen Edit Plus accepted a non-contiguous reference slot")
    too_many = {**bindings, "references": [
        {"node_id": str(index), "input": "image", "slot": f"image_{index}"}
        for index in range(1, creative.MAX_REFERENCE_IMAGES + 2)
    ]}
    expanded = {**workflow, **{
        str(index): {"class_type": "LoadImage", "inputs": {"image": "placeholder.png"}}
        for index in range(4, creative.MAX_REFERENCE_IMAGES + 2)
    }}
    expect_blocked(lambda: creative.comfyui_workflow.validate_bindings(too_many, expanded, analysis),
                   "reference binding exceeded the shared resource bound")


def write_bundle(project: Path, **overrides):
    output = {
        "version": 1, "mode": "EPHEMERAL", "operation": "generate", "provider": "mflux_local",
        "prompt": "private creative prompt", "output_scope": "creative-output",
        "output_path": "creative-output/run-v1/image-v1.png", "input_image": None,
        "width": 64, "height": 64, "steps": 2, "seed": 7, "max_retries": 1, "timeout_seconds": 10,
        "runtime": "mflux-generate", "runtime_version": "fixture-1",
        "model": {"id": "dev", "revision": "fixture-sha", "local_path": str(project / "model"), "license": "fixture license", "license_source": "https://example.test/license"},
        "mflux_executable": str(project / "bin/mflux-generate"),
    }
    output.update(overrides)
    path = project / "creative-bundle.yaml"
    path.write_text(yaml.safe_dump(output, sort_keys=False), encoding="utf-8")
    return path, output


def fixture_project(base: Path) -> Path:
    project = base / "creative-project"
    (project / "creative-output/run-v1").mkdir(parents=True)
    (project / "model").mkdir()
    (project / "bin").mkdir()
    return project


def mflux_fixture(project: Path, *, sleep_seconds: float = 0, command_name: str = "mflux-generate") -> Path:
    executable = project / "bin" / command_name
    executable.write_text(
        "#!/usr/bin/env python3\n"
        "import os, pathlib, sys, time\n"
        "pathlib.Path(os.environ['FAKE_MFLUX_ARGS']).write_text('\\n'.join(sys.argv[1:]))\n"
        f"time.sleep({sleep_seconds!r})\n"
        "out = pathlib.Path(sys.argv[sys.argv.index('--output') + 1])\n"
        f"out.write_bytes(bytes.fromhex('{PNG.hex()}'))\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable


class FakeComfyHandler(BaseHTTPRequestHandler):
    prompts = 0
    workflow = None
    staged_reference = PNG
    prompt_id = "fixture-job"
    missing_vae = False
    fp8_unet = False
    unet_filename = None
    system_status = None
    flux3 = False
    invalid_sampling_mode = False
    execution_error = None
    extra_unets: ClassVar[list[str]] = []
    extra_clips: ClassVar[list[str]] = []

    def log_message(self, *_args):
        return

    def send_bytes(self, data: bytes, content_type: str = "application/json"):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/system_stats":
            if type(self).system_status is not None:
                status = type(self).system_status
                self.send_response(status)
                if status == 302:
                    self.send_header("Location", "http://example.invalid/redirected")
                self.send_header("Content-Length", "20")
                self.end_headers()
                self.wfile.write(b"synthetic-token-body")
                return
            return self.send_bytes(b"{}")
        if self.path == "/object_info/CheckpointLoaderSimple":
            return self.send_bytes(json.dumps({"CheckpointLoaderSimple": {"input": {"required": {"ckpt_name": [["model.safetensors"]]}}}}).encode())
        if self.path == "/object_info/UNETLoader":
            if type(self).flux3:
                choices = ["flux3-image-klein-base-int8-convrot.safetensors", "flux3-image-klein-int8-convrot.safetensors", *type(self).extra_unets]
                return self.send_bytes(json.dumps({"UNETLoader": {"input": {"required": {"unet_name": [choices]}}}}).encode())
            unet = type(self).unet_filename or ("z_image_turbo_fp8.safetensors" if type(self).fp8_unet else "z_image_turbo_bf16.safetensors")
            return self.send_bytes(json.dumps({"UNETLoader": {"input": {"required": {"unet_name": [[unet]]}}}}).encode())
        if self.path == "/object_info/CLIPLoader":
            if type(self).flux3:
                clips = ["qwen3vl_4b_int8_convrot.safetensors", "qwen3.5_9b_flux3_prompt_upsampler_w4a8.safetensors", *type(self).extra_clips]
                return self.send_bytes(json.dumps({"CLIPLoader": {"input": {"required": {"clip_name": [clips], "type": [["flux3"]]}}}}).encode())
            return self.send_bytes(json.dumps({"CLIPLoader": {"input": {"required": {"clip_name": [["qwen_3_4b.safetensors"]], "type": [["lumina2"]]}}}}).encode())
        if self.path == "/object_info/VAELoader":
            choices = [] if type(self).missing_vae else (["flux2-vae.safetensors"] if type(self).flux3 else ["ae.safetensors"])
            return self.send_bytes(json.dumps({"VAELoader": {"input": {"required": {"vae_name": [choices]}}}}).encode())
        if self.path == "/object_info/TextGenerate":
            options = [
                {"key": "on", "inputs": {"required": {"temperature": ["FLOAT", {"default": 0.7, "min": 0.01, "max": 2.0}], "top_k": ["INT", {"default": 64, "min": 0, "max": 1000}], "top_p": ["FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0}], "min_p": ["FLOAT", {"default": 0.05, "min": 0.0, "max": 1.0}], "repetition_penalty": ["FLOAT", {"default": 1.05, "min": 0.0, "max": 5.0}], "seed": ["INT", {"default": 0, "min": 0, "max": 18446744073709551615}]}, "optional": {"presence_penalty": ["FLOAT", {"default": 0.0, "min": 0.0, "max": 5.0}]}}},
                {"key": "off", "inputs": {"required": {}}},
            ]
            if type(self).invalid_sampling_mode:
                options = options[:1]
            schema = {"TextGenerate": {"input": {
                "required": {"clip": ["CLIP", {}], "prompt": ["STRING", {"default": ""}], "max_length": ["INT", {"default": 512, "min": 1, "max": 32768}], "sampling_mode": ["COMFY_DYNAMICCOMBO_V3", {"options": options}]},
                "optional": {"thinking": ["BOOLEAN", {"default": False}], "use_default_template": ["BOOLEAN", {"default": True}], "mtp": ["COMBO", {"options": ["auto", "off", "2", "3", "4", "5"]}], "system_prompt": ["STRING", {"forceInput": True}]},
            }}}
            return self.send_bytes(json.dumps(schema).encode())
        if self.path == "/object_info":
            vae_choices = [] if type(self).missing_vae else ["ae.safetensors"]
            schema = {
                "CheckpointLoaderSimple": {"python_module": "nodes", "input": {"required": {"ckpt_name": [["model.safetensors"]]}}, "output": ["MODEL", "CLIP", "VAE"]},
                "UNETLoader": {"python_module": "nodes", "input": {"required": {"unet_name": [["z_image_turbo_bf16.safetensors"]]}}, "output": ["MODEL"]},
                "CLIPLoader": {"python_module": "nodes", "input": {"required": {"clip_name": [["qwen_3_4b.safetensors"]]}}, "output": ["CLIP"]},
                "VAELoader": {"python_module": "nodes", "input": {"required": {"vae_name": [vae_choices]}}, "output": ["VAE"]},
            }
            return self.send_bytes(json.dumps(schema).encode())
        if self.path.startswith("/view?"):
            from urllib.parse import parse_qs, urlsplit
            query = parse_qs(urlsplit(self.path).query)
            body = self.staged_reference if query.get("type") == ["input"] else PNG_WITH_PROMPT
            return self.send_bytes(body, "image/png")
        if self.path == "/history/fixture-job":
            image_ref = {"images": [{"filename": "generated.png", "subfolder": "", "type": "output"}]}
            status = {"status_str": "success", "completed": True}
            if type(self).execution_error:
                status = {"status_str": "error", "completed": True, "messages": [["execution_error", type(self).execution_error]]}
            item = {self.prompt_id: {"status": status, "outputs": {"9": image_ref, "11": image_ref}}}
            return self.send_bytes(json.dumps(item).encode())
        self.send_error(404)

    def do_POST(self):
        if self.path != "/prompt":
            return self.send_error(404)
        size = int(self.headers.get("Content-Length", "0"))
        item = json.loads(self.rfile.read(size))
        type(self).workflow = item["prompt"]
        type(self).prompts += 1
        self.send_bytes(json.dumps({"prompt_id": self.prompt_id}).encode())


def comfy_server():
    FakeComfyHandler.prompts = 0
    server = HTTPServer(("127.0.0.1", 0), FakeComfyHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def comfy_workflow(project: Path, *, edit: bool = False, custom: bool = False) -> Path:
    workflow = {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "model.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "placeholder"}},
        "1": {"class_type": "EmptyLatentImage", "inputs": {"width": 64, "height": 64}},
        "3": {"class_type": "KSampler", "inputs": {"seed": 1}},
        "7": {"class_type": "VAEDecode", "inputs": {}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "old"}},
    }
    if edit:
        workflow["12"] = {"class_type": "LoadImage", "inputs": {"image": "placeholder.png"}}
    if custom:
        workflow["99"] = {"class_type": "CustomNode", "inputs": {}}
    path = project / "workflow.json"
    path.write_text(json.dumps(workflow), encoding="utf-8")
    return path


def zimage_workflow(project: Path) -> Path:
    workflow = {
        "28": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
        "30": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2", "device": "default"}},
        "29": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "27": {"class_type": "CLIPTextEncode", "inputs": {"text": "placeholder", "clip": ["30", 0]}},
        "33": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["27", 0]}},
        "13": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "11": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["28", 0], "shift": 3}},
        "3": {"class_type": "KSampler", "inputs": {"model": ["11", 0], "positive": ["27", 0], "negative": ["33", 0], "latent_image": ["13", 0], "seed": 0, "steps": 8, "cfg": 1, "sampler_name": "res_multistep", "scheduler": "simple", "denoise": 1}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["29", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "old"}},
    }
    path = project / "zimage-workflow.json"
    path.write_text(json.dumps(workflow), encoding="utf-8")
    return path


def flux3_workflow(project: Path, filename: str = "flux3-workflow.json") -> Path:
    source = ROOT / "templates/creative/COMFYUI_FLUX3_IMAGE_KLEIN_API.json"
    path = project / filename
    path.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def guard_cases(project: Path):
    inside = str(project)
    allowed = guard.evaluate_shell(command="aips creative preflight --project . --bundle creative-bundle.yaml", cwd=inside, root=inside)
    require(allowed["decision"] == "ALLOW" and allowed["reason_code"] == "shell_aips_readonly", "bounded Creative Preflight was not allowed")
    denied = guard.evaluate_shell(command="aips creative execute --project . --bundle creative-bundle.yaml", cwd=inside, root=inside)
    require(denied["decision"] == "DENY" and denied["reason_code"] == "shell_aips_command_unsupported", "Creative execution leaked into the Shell allowlist")
    for command in ("aips creative prepare --project . --scope assets", "python3 -c print(1)", "aips publish push", "aips creative preflight --project /tmp --bundle x.yaml", "aips creative trace --limit 1000", "aips creative preflight --project . --bundle x.yaml && pwd"):
        result = guard.evaluate_shell(command=command, cwd=inside, root=inside)
        require(result["decision"] != "ALLOW", f"unsafe diagnostic command was allowed: {command}")


def mflux_cases(base: Path):
    project = fixture_project(base)
    mflux_fixture(project)
    args_path = base / "mflux-args.txt"
    os.environ["FAKE_MFLUX_ARGS"] = str(args_path)
    bundle_path, bundle = write_bundle(project, asset_preset="texture")
    before = creative.preflight(project, bundle_path.name)
    require(before["status"] == "READY" and not args_path.exists(), "preflight started the configured generator")
    compatibility = before["backend_compatibility"]
    require(compatibility["status"] == "UNVERIFIED" and compatibility["backend"] == "mflux_local", "static readiness must not imply real hardware/backend compatibility")
    require(compatibility["evidence_status"] == "STATIC_METADATA_ONLY"
            and compatibility["mps_runtime_probe"] == "NOT_PERFORMED"
            and compatibility["accelerator_backend"] in {"mps", "NOT_APPLICABLE"},
            "static MPS diagnostics claimed an inference or runtime probe")
    require(compatibility["host"]["os"] and compatibility["host"]["architecture"] and compatibility["weight_dtypes"] == ["NOT_EXPOSED_BY_CONFIGURED_WORKFLOW"], "preflight did not disclose available host/model compatibility inputs")
    require(not args_path.exists() and compatibility["evidence"].startswith("Static local preflight only"), "compatibility inspection executed inference")
    result = creative.execute(project, bundle_path.name)
    output = project / bundle["output_path"]
    manifest_path = project / result["manifest"]
    manifest = json.loads(manifest_path.read_text())
    args = args_path.read_text()
    require(result["status"] == "COMPLETE" and result["review_status"] == "PENDING", "MFLUX execution did not retain pending human review")
    require(manifest["model"]["revision"] == "fixture-sha" and manifest["bundle_sha256"].startswith("sha256:"), "model/bundle provenance was not recorded")
    require(manifest["output"]["sha256"] == creative.digest(output) and manifest["privacy"]["external_image_egress"] is False, "output provenance or privacy boundary missing")
    require(manifest["verification"] == {"workflow_execution": "PASS", "raster_container": "PASS", "model_inference": "UNVERIFIED", "human_visual_review": "PENDING", "user_acceptance": "NOT_RECORDED"}, "workflow, inference, visual review and user acceptance evidence must remain distinct")
    require("private creative prompt" not in manifest_path.read_text() and "private creative prompt" not in creative.read_trace(20).__repr__(), "raw prompt reached a manifest or trace")
    require("--output\n" in args and "--model-path\n" in args and "--prompt\nRequested image brief: private creative prompt" in args, "fixed MFLUX argv or compiled prompt was not formed")
    require("Creative asset preset: Texture asset" in args
            and manifest["creative_asset_preset"]["id"] == "texture"
            and manifest["creative_asset_preset"]["registry_sha256"].startswith("sha256:"),
            "shared creative preset guidance or provenance was not recorded")
    require("HF_HUB_OFFLINE" not in args and output_magic(output), "MFLUX output fixture was not written")
    expect_blocked(lambda: creative.execute(project, bundle_path.name), "existing output was overwritten")
    reviewed = creative.review(project, result["manifest"], "Independent Human", "PASS", "Identity and style match the approved profiles.")
    require(reviewed["status"] == "REVIEWED" and json.loads(manifest_path.read_text())["review"]["decision"] == "PASS", "human review was not recorded")
    reviewed_manifest = json.loads(manifest_path.read_text())
    require(reviewed_manifest["verification"]["human_visual_review"] == "PASS" and reviewed_manifest["acceptance"]["visual_quality"] == "PASS" and reviewed_manifest["verification"]["user_acceptance"] == "NOT_RECORDED", "human review and user acceptance must remain distinct")
    guard_cases(project)

    bundle["output_path"] = "outside-v1.png"
    write_bundle(project, **bundle)
    expect_blocked(lambda: creative.preflight(project, bundle_path.name), "output outside declared scope was accepted")

    rollback = fixture_project(base / "rollback")
    mflux_fixture(rollback)
    rollback_bundle, _ = write_bundle(rollback)
    with patch.object(creative, "atomic_manifest", side_effect=OSError("fixture")):
        expect_blocked(lambda: creative.execute(rollback, rollback_bundle.name), "manifest failure did not block execution")
    require(not (rollback / "creative-output/run-v1/image-v1.png").exists(), "manifest failure did not roll back the image")

    timeout = fixture_project(base / "timeout")
    mflux_fixture(timeout, sleep_seconds=2)
    timeout_bundle, _ = write_bundle(timeout, timeout_seconds=1, max_retries=1)
    try:
        creative.execute(timeout, timeout_bundle.name)
    except creative.Blocked as exc:
        require(exc.reason_code == "provider_timeout", "timeout had the wrong reason code")
    else:
        raise AssertionError("finite MFLUX timeout unexpectedly completed")
    require(not (timeout / "creative-output/run-v1/image-v1.png").exists(), "timeout left an output behind")


def mflux_capability_cases(base: Path):
    project = fixture_project(base)
    first = project / "reference-one.png"
    second = project / "reference-two.webp"
    first.write_bytes(PNG)
    second.write_bytes(PNG)
    bundle = {
        "operation": "edit", "model": {"id": "flux2-klein-4b", "local_path": str(project / "model")},
        "prompt": "edit", "input_images": [first.name, second.name], "steps": 2,
    }
    executable = project / "bin/mflux-generate-flux2-edit"
    command = creative.mflux_command(project.resolve(), bundle, executable, project / "out.png")
    require(command[0] == str(executable) and command[command.index("--model") + 1] == "flux2-klein-4b", "FLUX.2 edit capability used the wrong CLI mapping")
    require(command[command.index("--image-paths") + 1:command.index("--image-paths") + 3] == [str(first.resolve()), str(second.resolve())], "multiple edit references were not mapped to --image-paths")
    cases = [
        ("z-image-turbo", "generate", "mflux-generate-z-image-turbo", None),
        ("flux2-klein-4b", "generate", "mflux-generate-flux2", None),
        ("flux2-klein-9b", "generate", "mflux-generate-flux2", None),
        ("flux2-klein-9b-kv", "edit", "mflux-generate-flux2-edit", "--image-paths"),
        ("qwen-image-edit-2511", "edit", "mflux-generate-qwen-edit", "--image-paths"),
        ("schnell", "edit", "mflux-generate", "--image-path"),
    ]
    for model_id, operation, command_name, image_option in cases:
        capability = creative.MFLUX_CAPABILITIES[model_id][operation]
        require(capability["command"] == command_name and capability["image_option"] == image_option, f"incorrect registered MFLUX capability for {model_id}/{operation}")
    turbo_executable = project / "bin/mflux-generate-z-image-turbo"
    turbo = {**bundle, "operation": "generate", "model": {"id": "z-image-turbo", "local_path": str(project / "model")}, "input_images": [], "steps": 8}
    turbo_command = creative.mflux_command(project.resolve(), turbo, turbo_executable, project / "turbo.png")
    require(turbo_command[0] == str(turbo_executable) and turbo_command[turbo_command.index("--base-model") + 1] == "z-image-turbo", "Turbo used the wrong fixed command or base model")
    require(turbo_command[turbo_command.index("--model") + 1] == str(project / "model") and "--model-path" not in turbo_command and "--no-exif" in turbo_command, "Turbo local weights or metadata policy did not match the installed CLI")
    require(turbo_command[turbo_command.index("--steps") + 1] == "8" and not any(arg.startswith("--image-path") for arg in turbo_command), "Turbo generation changed explicit steps or accepted edit inputs")
    expect_blocked(lambda: creative.mflux_command(project.resolve(), {**turbo, "operation": "edit"}, turbo_executable, project / "bad.png"), "Turbo edit was silently routed to generation")
    expect_blocked(lambda: creative.mflux_command(project.resolve(), {**turbo, "model": {"id": "z-image"}}, turbo_executable, project / "bad.png"), "non-Turbo Z-Image was accepted")
    expect_blocked(lambda: creative.mflux_command(project.resolve(), turbo, project / "bin/mflux-generate", project / "bad.png"), "Turbo accepted the generic FLUX command")
    mflux_fixture(project, command_name=turbo_executable.name)
    turbo_args = base / "turbo-args.txt"
    os.environ["FAKE_MFLUX_ARGS"] = str(turbo_args)
    turbo_path, _ = write_bundle(
        project, runtime=turbo_executable.name, mflux_executable=str(turbo_executable), steps=8,
        model={"id": "z-image-turbo", "revision": "fixture-sha", "local_path": str(project / "model"), "license": "fixture", "license_source": "https://example.test/license"},
        output_scope="creative-output/turbo-v1", output_path="creative-output/turbo-v1/image.png",
    )
    turbo_result = creative.execute(project, turbo_path.name)
    turbo_manifest = json.loads((project / turbo_result["manifest"]).read_text())
    require(turbo_result["status"] == "COMPLETE" and turbo_manifest["model"]["id"] == "z-image-turbo" and turbo_result["review_status"] == "PENDING", "Turbo execution lost model provenance or pending review")
    require("--base-model\nz-image-turbo" in turbo_args.read_text() and "--no-exif" in turbo_args.read_text(), "Turbo execute did not use the registered local command shape")
    expect_blocked(lambda: creative.mflux_command(project.resolve(), {**bundle, "model": {"id": []}}, executable, project / "bad.png"), "non-string MFLUX model id was accepted")
    expect_blocked(lambda: creative.mflux_command(project.resolve(), bundle, project / "bin/mflux-generate", project / "bad.png"), "mismatched fixed MFLUX executable was accepted")
    expect_blocked(lambda: creative.bundle_input_images(project.resolve(), {"input_images": [first.name] * 9}), "reference batch count limit was not enforced")
    single_reference_capability = creative.MFLUX_CAPABILITIES["dev"]["edit"]
    require(single_reference_capability["image_option"] == "--image-path", "legacy MFLUX edit did not retain its single-reference CLI option")
    expect_blocked(lambda: creative.mflux_command(project.resolve(), {**bundle, "model": {"id": "dev", "local_path": str(project / "model")}}, project / "bin/mflux-generate", project / "bad.png"), "single-reference MFLUX CLI accepted multiple input images")

    mflux_fixture(project, command_name="mflux-generate-flux2-edit")
    args_path = base / "mflux-multi-args.txt"
    os.environ["FAKE_MFLUX_ARGS"] = str(args_path)
    bundle_path, _ = write_bundle(
        project, operation="edit", input_images=[first.name, second.name], provider="mflux_local",
        runtime="mflux-generate-flux2-edit", model={"id": "flux2-klein-4b", "revision": "fixture-sha", "local_path": str(project / "model"), "license": "fixture", "license_source": "https://example.test/license"},
        mflux_executable=str(project / "bin/mflux-generate-flux2-edit"),
    )
    result = creative.execute(project, bundle_path.name)
    manifest = json.loads((project / result["manifest"]).read_text())
    require(result["status"] == "COMPLETE" and len(manifest["inputs"]) == 2, "multi-reference MFLUX execution did not record both local inputs")
    require(args_path.read_text().count("reference-") == 2, "multi-reference fake MFLUX did not receive both staged paths")


def prepare_cases(base: Path):
    project = base / "ephemeral-project"
    project.mkdir(parents=True)
    kwargs = {
        "project": project, "scope": "art", "character_id": "mira-7", "character_name": "Mira",
        "summary": "A traveling botanist", "style_intent": "Soft ink and watercolor", "prompt": "A full-body character sheet",
        "identity_features": ["copper bob", "round glasses"],
    }
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: creative.prepare(**kwargs), range(2)))
    require({item["version"] for item in results} == {"mira-7-v1", "mira-7-v2"}, "concurrent preparation overwrote a versioned workspace")
    prepared = project / results[0]["scope"]
    for relative in results[0]["files"]:
        require((project / relative).is_file(), f"prepared file missing: {relative}")
    require((prepared / "README.md").stat().st_mode & 0o777 == 0o600, "prepared README permissions were not private")
    require((prepared / "bundles/CREATIVE_BUNDLE.yaml").is_file(), "prepared Bundle was missing")
    require((prepared / "output/character-v1").stat().st_mode & 0o777 == 0o700, "prepared output scope permissions were not private")
    try:
        creative.preflight(prepared, "bundles/CREATIVE_BUNDLE.yaml")
    except creative.Blocked as exc:
        require(exc.reason_code == "BLOCKED_NO_ENGINE", "unconfigured prepared workspace had the wrong preflight result")
    else:
        raise AssertionError("prepared workspace without an installed engine was presented as READY")
    expect_blocked(lambda: creative.prepare(**{**kwargs, "scope": "../outside"}), "preparation path traversal was accepted")
    expect_blocked(lambda: creative.prepare(**{**kwargs, "prompt": "x" * (creative.MAX_PROMPT_CHARS + 1)}), "oversized preparation prompt was accepted")
    expect_blocked(lambda: creative.prepare(**{**kwargs, "identity_features": []}), "empty identity features were accepted")
    linked = project / "linked"
    linked.symlink_to(project / "art", target_is_directory=True)
    expect_blocked(lambda: creative.prepare(**{**kwargs, "scope": "linked"}), "symlinked preparation scope was accepted")
    git_project = base / "git-project"
    git_project.mkdir()
    (git_project / ".git").mkdir()
    expect_blocked(lambda: creative.prepare(**{**kwargs, "project": git_project}), "Git workspace preparation was accepted")


def cli_prepare_case(base: Path):
    project = base / "cli-ephemeral"
    project.mkdir(parents=True)
    command = [
        str(ROOT / "bin/aips"), "creative", "prepare", "--project", str(project), "--scope", "characters",
        "--character-id", "cli-mira", "--character-name", "Mira", "--summary", "A test character",
        "--style-intent", "Watercolor", "--prompt", "Full-body reference", "--identity-feature", "copper hair",
    ]
    env = {**os.environ, "AIPS_VALIDATION_PYTHON": sys.executable}
    result = __import__("subprocess").run(command, capture_output=True, text=True, env=env, check=False, timeout=20)
    require(result.returncode == 0, "aips creative prepare dispatcher failed: " + result.stderr)
    payload = json.loads(result.stdout)
    require(payload["status"] == "PREPARED" and (project / payload["bundle"]).is_file(), "CLI prepare did not return its created Bundle")


def comfy_cases(base: Path):
    project = fixture_project(base)
    workflow_path = comfy_workflow(project)
    server, thread = comfy_server()
    try:
        url = f"http://127.0.0.1:{server.server_port}"
        comfy = {"base_url": url, "workflow_path": workflow_path.name, "checkpoint_node_id": "4", "checkpoint_name": "model.safetensors", "model_id": "model.safetensors", "prompt_node_id": "6", "latent_node_id": "1", "sampler_node_id": "3", "save_node_id": "9"}
        bundle_path, _ = write_bundle(project, provider="comfyui_local", model={"id": "model.safetensors", "revision": "local-checkpoint", "license": "fixture", "license_source": "local model card"}, runtime="ComfyUI", runtime_version="fixture-1", comfyui=comfy)
        result = creative.preflight(project, bundle_path.name)
        require(result["status"] == "READY" and FakeComfyHandler.prompts == 0, "ComfyUI preflight submitted a workflow")
        require(result["backend_compatibility"]["status"] == "UNVERIFIED"
                and result["backend_compatibility"]["warnings"] == []
                and "Inspect model precision metadata" in result["backend_compatibility"]["recommended_action"],
                "unknown model precision was promoted to compatible or produced an FP8 warning")
        require(result["readiness"] == {"command": "LOCAL_SERVICE_REACHABLE", "runtime": "RUNTIME_VERIFIED",
                                        "model": "MODEL_CONFIGURED_PRESENT", "preflight": "PREFLIGHT_READY",
                                        "inference": "INFERENCE_UNVERIFIED"},
                "ComfyUI staged readiness implied inference or hid model preflight")
        executed = creative.execute(project, bundle_path.name)
        require(executed["status"] == "COMPLETE" and FakeComfyHandler.workflow["6"]["inputs"]["text"] == "Requested image brief: private creative prompt", "ComfyUI workflow did not receive the profile-compiled prompt")
        saved_png = (project / executed["output"]).read_bytes()
        require(b"private creative prompt" not in saved_png and saved_png == PNG, "ComfyUI prompt metadata was retained in the AIPS output")
        require(FakeComfyHandler.workflow["1"]["inputs"]["width"] == 64 and FakeComfyHandler.workflow["3"]["inputs"]["steps"] == 2, "ComfyUI generation settings escaped Bundle limits")
        require(json.loads((project / executed["manifest"]).read_text())["workflow_sha256"].startswith("sha256:"), "ComfyUI workflow hash missing")

        edit_project = fixture_project(base / "edit")
        ref = edit_project / "reference.png"
        ref.write_bytes(PNG)
        edit_workflow = comfy_workflow(edit_project, edit=True)
        FakeComfyHandler.staged_reference = PNG
        edit_comfy = {**comfy, "workflow_path": edit_workflow.name, "input_image_node_id": "12", "input_image_name": "reference.png"}
        edit_bundle, _ = write_bundle(edit_project, operation="edit", input_image="reference.png", provider="comfyui_local", model={"id": "model.safetensors", "revision": "local-checkpoint", "license": "fixture", "license_source": "local model card"}, runtime="ComfyUI", runtime_version="fixture-1", comfyui=edit_comfy)
        creative.preflight(edit_project, edit_bundle.name)
        creative.execute(edit_project, edit_bundle.name)
        require(FakeComfyHandler.workflow["12"]["inputs"]["image"] == "reference.png", "ComfyUI edit did not use the hash-checked staged input")

        FakeComfyHandler.staged_reference = b"different reference"
        expect_blocked(lambda: creative.preflight(edit_project, edit_bundle.name), "ComfyUI accepted a mismatched staged input")
        expect_blocked(lambda: creative.loopback_base("http://example.com:8188"), "external ComfyUI host was accepted")
        custom_path = comfy_workflow(project, custom=True)
        custom_config = {**comfy, "workflow_path": custom_path.name}
        try:
            creative.load_comfy_workflow(project.resolve(strict=True), custom_config)
        except creative.Blocked as exc:
            require(exc.reason_code == "comfy_custom_node_blocked", "custom node had the wrong reason code")
        else:
            raise AssertionError("custom ComfyUI node was accepted")
        require(FakeComfyHandler.prompts >= 2, "expected only the explicit execution calls to submit jobs")

        zimage_project = fixture_project(base / "zimage")
        zimage_path = zimage_workflow(zimage_project)
        zimage_config = {"base_url": url, "workflow_path": zimage_path.name, "model_profile": "z-image-turbo", "model_id": "z-image-turbo", "unet_name": "z_image_turbo_bf16.safetensors", "clip_name": "qwen_3_4b.safetensors", "vae_name": "ae.safetensors", "prompt_node_id": "27", "latent_node_id": "13", "sampler_node_id": "3", "save_node_id": "9"}
        zimage_bundle, _ = write_bundle(zimage_project, provider="comfyui_local", model={"id": "z-image-turbo", "revision": "local-model-files", "license": "Apache-2.0", "license_source": "https://huggingface.co/Tongyi-MAI/Z-Image-Turbo"}, runtime="ComfyUI", runtime_version="fixture-1", comfyui=zimage_config, steps=8)
        ready = creative.preflight(zimage_project, zimage_bundle.name)
        require(ready["status"] == "READY" and FakeComfyHandler.prompts == 2, "Z-Image Turbo preflight submitted a workflow or did not become ready")
        require(ready["backend_compatibility"]["status"] == "UNVERIFIED" and "default" in ready["backend_compatibility"]["weight_dtypes"], "ComfyUI dtype/backend evidence was not surfaced conservatively")
        require(ready["readiness"]["model"] == "MODEL_CONFIGURED_PRESENT"
                and ready["readiness"]["inference"] == "INFERENCE_UNVERIFIED",
                "Z-Image preflight implied verified inference")
        with patch.object(creative.platform, "system", return_value="Darwin"), patch.object(creative.platform, "machine", return_value="arm64"):
            bf16_ready = creative.preflight(zimage_project, zimage_bundle.name)
        require(bf16_ready["backend_compatibility"]["status"] == "UNVERIFIED"
                and bf16_ready["backend_compatibility"]["warnings"] == []
                and "FP16/BF16 metadata was observed" in bf16_ready["backend_compatibility"]["recommended_action"]
                and bf16_ready["readiness"]["inference"] == "INFERENCE_UNVERIFIED",
                "BF16 metadata implied runtime compatibility on Apple Silicon")
        fp16_project = fixture_project(base / "zimage-fp16")
        fp16_path = fp16_project / "fp16-workflow.json"
        fp16_workflow = json.loads(zimage_path.read_text())
        fp16_workflow["28"]["inputs"]["unet_name"] = "z_image_turbo_fp16.safetensors"
        fp16_path.write_text(json.dumps(fp16_workflow), encoding="utf-8")
        FakeComfyHandler.unet_filename = "z_image_turbo_fp16.safetensors"
        try:
            fp16_bundle, _ = write_bundle(fp16_project, provider="comfyui_local", model={"id": "z-image-turbo", "revision": "local-model-files", "license": "Apache-2.0", "license_source": "local model card"}, runtime="ComfyUI", runtime_version="fixture-1", comfyui={**zimage_config, "base_url": url, "workflow_path": fp16_path.name, "unet_name": "z_image_turbo_fp16.safetensors"}, steps=8)
            with patch.object(creative.platform, "system", return_value="Darwin"), patch.object(creative.platform, "machine", return_value="arm64"):
                fp16_ready = creative.preflight(fp16_project, fp16_bundle.name)
            require(fp16_ready["backend_compatibility"]["status"] == "UNVERIFIED"
                    and fp16_ready["backend_compatibility"]["warnings"] == []
                    and "FP16/BF16 metadata was observed" in fp16_ready["backend_compatibility"]["recommended_action"]
                    and fp16_ready["readiness"]["inference"] == "INFERENCE_UNVERIFIED"
                    and FakeComfyHandler.prompts == 2,
                    "FP16 metadata implied runtime compatibility or preflight launched inference")
        finally:
            FakeComfyHandler.unet_filename = None
        fp8_project = fixture_project(base / "zimage-fp8")
        fp8_path = fp8_project / "fp8-workflow.json"
        fp8_workflow = json.loads(zimage_path.read_text())
        fp8_workflow["28"]["inputs"]["unet_name"] = "z_image_turbo_fp8.safetensors"
        fp8_path.write_text(json.dumps(fp8_workflow), encoding="utf-8")
        FakeComfyHandler.fp8_unet = True
        try:
            fp8_bundle, _ = write_bundle(fp8_project, provider="comfyui_local", model={"id": "z-image-turbo", "revision": "local-model-files", "license": "Apache-2.0", "license_source": "local model card"}, runtime="ComfyUI", runtime_version="fixture-1", comfyui={**zimage_config, "base_url": url, "workflow_path": fp8_path.name, "unet_name": "z_image_turbo_fp8.safetensors"}, steps=8)
            with patch.object(creative.platform, "system", return_value="Darwin"), patch.object(creative.platform, "machine", return_value="arm64"):
                fp8_ready = creative.preflight(fp8_project, fp8_bundle.name)
            require(fp8_ready["backend_compatibility"]["status"] == "WARNING"
                    and fp8_ready["backend_compatibility"]["warnings"] == ["apple_mps_fp8_static_warning"]
                    and "Prefer a locally installed FP16/BF16" in fp8_ready["backend_compatibility"]["recommended_action"]
                    and fp8_ready["readiness"]["inference"] == "INFERENCE_UNVERIFIED"
                    and FakeComfyHandler.prompts == 2,
                    "Apple Silicon FP8 warning was not advisory or preflight launched inference")
        finally:
            FakeComfyHandler.fp8_unet = False
        zimage_result = creative.execute(zimage_project, zimage_bundle.name)
        require(zimage_result["status"] == "COMPLETE" and FakeComfyHandler.workflow["13"]["inputs"]["width"] == 64 and FakeComfyHandler.workflow["3"]["inputs"]["steps"] == 8, "Z-Image Turbo settings were not applied to the registered workflow")
        FakeComfyHandler.missing_vae = True
        try:
            expect_blocked(lambda: creative.preflight(zimage_project, zimage_bundle.name), "Z-Image Turbo accepted a VAE absent from the local inventory")
        finally:
            FakeComfyHandler.missing_vae = False
        zimage_edit_project = fixture_project(base / "zimage-edit")
        zimage_edit_path = zimage_workflow(zimage_edit_project)
        (zimage_edit_project / "reference.png").write_bytes(PNG)
        edit_config = {**zimage_config, "workflow_path": zimage_edit_path.name}
        edit_bundle, _ = write_bundle(zimage_edit_project, operation="edit", input_image="reference.png", provider="comfyui_local", model={"id": "z-image-turbo", "revision": "local-model-files", "license": "Apache-2.0", "license_source": "local model card"}, runtime="ComfyUI", runtime_version="fixture-1", comfyui=edit_config, steps=8)
        expect_blocked(lambda: creative.preflight(zimage_edit_project, edit_bundle.name), "Z-Image Turbo ComfyUI profile accepted image editing")
        bad_topology = json.loads(zimage_path.read_text())
        bad_topology["3"]["inputs"]["negative"] = ["27", 0]
        zimage_path.write_text(json.dumps(bad_topology))
        expect_blocked(lambda: creative.preflight(zimage_project, zimage_bundle.name), "Z-Image Turbo accepted a malformed conditioning topology")
        zimage_path.write_text(json.dumps(json.loads(zimage_path.read_text()) | {"99": {"class_type": "CustomNode", "inputs": {}}}))
        expect_blocked(lambda: creative.preflight(zimage_project, zimage_bundle.name), "Z-Image Turbo accepted a custom node")

        FakeComfyHandler.flux3 = True
        flux3_project = fixture_project(base / "flux3-klein")
        flux3_path = flux3_workflow(flux3_project)
        flux3_config = {
            "base_url": url, "workflow_path": flux3_path.name,
            "model_profile": "flux3-image-klein-base-int8", "model_id": "flux3-image-klein-base",
            "unet_name": "flux3-image-klein-base-int8-convrot.safetensors",
            "clip_name": "qwen3vl_4b_int8_convrot.safetensors",
            "prompt_upsampler_name": "qwen3.5_9b_flux3_prompt_upsampler_w4a8.safetensors",
            "vae_name": "flux2-vae.safetensors", "prompt_node_id": "5", "latent_node_id": "8",
            "sampler_node_id": "9", "save_node_id": "11",
        }
        flux3_bundle, flux3_bundle_data = write_bundle(
            flux3_project, provider="comfyui_local", model={"id": "flux3-image-klein-base", "revision": "local-model-files", "license": "FLUX Kommunity License", "license_source": "https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy"},
            runtime="ComfyUI", runtime_version="fixture-1", comfyui=flux3_config,
        )
        flux3_prompt_count = FakeComfyHandler.prompts
        flux3_ready = creative.preflight(flux3_project, flux3_bundle.name)
        require(flux3_ready["status"] == "READY" and FakeComfyHandler.prompts == flux3_prompt_count, f"FLUX 3 Klein preflight was not ready or submitted a workflow: status={flux3_ready.get('status')} reason={flux3_ready.get('reason_code')} phase={flux3_ready.get('phase')}")

        FakeComfyHandler.invalid_sampling_mode = True
        try:
            try:
                creative.preflight(flux3_project, flux3_bundle.name)
            except creative.Blocked as exc:
                require(exc.reason_code == "comfy_textgenerate_schema_invalid", "unsupported TextGenerate Dynamic Combo did not return a stable preflight reason")
            else:
                raise AssertionError("FLUX 3 preflight accepted a server schema without the configured sampling_mode option")
            require(FakeComfyHandler.prompts == flux3_prompt_count, "invalid TextGenerate schema submitted a ComfyUI workflow")
        finally:
            FakeComfyHandler.invalid_sampling_mode = False

        flux3_result = creative.execute(flux3_project, flux3_bundle.name)
        require(flux3_result["status"] == "COMPLETE" and FakeComfyHandler.workflow["5"]["inputs"]["prompt"] == "Requested image brief: private creative prompt", "compiled FLUX 3 prompt was not routed through the prompt upsampler")
        require(FakeComfyHandler.workflow["9"]["inputs"]["steps"] == 50 and FakeComfyHandler.workflow["9"]["inputs"]["cfg"] == 3.5 and FakeComfyHandler.workflow["8"]["inputs"]["width"] == 64, "FLUX 3 execution did not preserve fixed Base sampler settings or apply Bundle dimensions")
        require(FakeComfyHandler.workflow["5"]["inputs"]["sampling_mode"] == "off", "final FLUX 3 payload did not serialize the Dynamic Combo option key expected by ComfyUI's API parser")
        require(FakeComfyHandler.prompts == flux3_prompt_count + 1, "FLUX 3 execution did not submit exactly one explicit workflow")

        distilled_project = fixture_project(base / "flux3-klein-distilled")
        distilled_path = flux3_workflow(distilled_project)
        distilled_flow = json.loads(distilled_path.read_text())
        distilled_flow["1"]["inputs"]["unet_name"] = "flux3-image-klein-int8-convrot.safetensors"
        distilled_flow["9"]["inputs"].update({"steps": 16, "cfg": 1.0})
        distilled_path.write_text(json.dumps(distilled_flow), encoding="utf-8")
        distilled_config = {
            **flux3_config, "workflow_path": distilled_path.name,
            "model_profile": "flux3-image-klein-distilled-int8", "model_id": "flux3-image-klein-distilled",
            "unet_name": "flux3-image-klein-int8-convrot.safetensors",
        }
        distilled_bundle, _ = write_bundle(
            distilled_project, provider="comfyui_local",
            model={"id": "flux3-image-klein-distilled", "revision": "local-model-files", "license": "FLUX Kommunity License", "license_source": "local model card"},
            runtime="ComfyUI", runtime_version="fixture-1", comfyui=distilled_config,
        )
        distilled_ready = creative.preflight(distilled_project, distilled_bundle.name)
        require(distilled_ready["status"] == "READY", "Distilled profile did not pass local schema and inventory validation")
        distilled_result = creative.execute(distilled_project, distilled_bundle.name)
        require(distilled_result["status"] == "COMPLETE" and FakeComfyHandler.workflow["9"]["inputs"]["steps"] == 16
                and FakeComfyHandler.workflow["9"]["inputs"]["cfg"] == 1.0,
                "Distilled execution did not use its registered sampler settings")

        _, flux3_provider = creative.resolve_provider(flux3_project.resolve(strict=True), flux3_bundle_data)
        FakeComfyHandler.execution_error = {
            "node_id": "5", "node_type": "TextGenerate", "exception_type": "TypeError",
            "exception_message": "TextGenerate.execute() missing 1 required positional argument: 'sampling_mode' for private creative prompt at /Users/lucas/private/profile.yaml token=synthetic-token",
            "traceback": ["/Users/lucas/private/comfy/node.py"],
        }
        try:
            try:
                creative.comfy_execute(flux3_bundle_data, flux3_provider, base / "comfy-error.png", 3)
            except creative.Blocked as exc:
                payload = exc.to_payload()
                diagnostic_text = repr(payload)
                require(exc.reason_code == "comfy_execution_failed" and payload["diagnostics"].get("node_id") == "5"
                        and payload["diagnostics"].get("node_type") == "TextGenerate"
                        and payload["diagnostics"].get("exception_type") == "TypeError"
                        and payload["diagnostics"].get("reason_summary") == "missing required argument 'sampling_mode'",
                        "ComfyUI failure omitted its bounded node and exception identity")
                require("private creative prompt" not in diagnostic_text and "/Users/lucas/private" not in diagnostic_text
                        and "synthetic-token" not in diagnostic_text and "traceback" not in diagnostic_text,
                        "ComfyUI failure diagnostics leaked prompt, path, credential-like content or traceback")
            else:
                raise AssertionError("synthetic TextGenerate execution error was not surfaced")
        finally:
            FakeComfyHandler.execution_error = None

        bad_flux3 = json.loads(flux3_path.read_text())
        bad_flux3["5"]["inputs"]["clip"] = ["2", 0]
        flux3_path.write_text(json.dumps(bad_flux3), encoding="utf-8")
        expect_blocked(lambda: creative.load_comfy_workflow(flux3_project.resolve(strict=True), flux3_config), "FLUX 3 accepted the image encoder in place of its prompt upsampler")
        bad_flux3["5"]["inputs"]["clip"] = ["3", 0]
        bad_flux3["9"]["inputs"]["cfg"] = 1
        flux3_path.write_text(json.dumps(bad_flux3), encoding="utf-8")
        expect_blocked(lambda: creative.load_comfy_workflow(flux3_project.resolve(strict=True), flux3_config), "FLUX 3 accepted distilled sampler settings for its Base model")

        distilled_profile = creative.load_comfy_profile("flux3-image-klein-distilled-int8")
        require(distilled_profile["sampler"]["steps"] == 16 and distilled_profile["sampler"]["cfg"] == 1,
                "Distilled profile did not retain its profile-specific sampler settings")
        invalid_distilled = {**distilled_profile, "sampler": {**distilled_profile["sampler"], "steps": 0}}
        fractional_steps = {**distilled_profile, "sampler": {**distilled_profile["sampler"], "steps": 16.5}}
        invalid_registry = yaml.safe_load(creative.COMFY_PROFILE_REGISTRY_PATH.read_text(encoding="utf-8"))
        invalid_registry["profiles"]["invalid-distilled"] = invalid_distilled
        invalid_registry["profiles"]["fractional-steps"] = fractional_steps
        invalid_registry_path = base / "invalid-distilled-profiles.yaml"
        invalid_registry_path.write_text(yaml.safe_dump(invalid_registry, sort_keys=False), encoding="utf-8")
        with patch.object(creative, "COMFY_PROFILE_REGISTRY_PATH", invalid_registry_path):
            expect_blocked(lambda: creative.load_comfy_profile("invalid-distilled"),
                           "invalid data-only profile sampler settings passed validation")
            expect_blocked(lambda: creative.load_comfy_profile("fractional-steps"),
                           "fractional sampler steps passed integer-field validation")

        # A new model can reuse an audited topology family by adding data to the registry only.
        future_profile = {
            "model_id": "future-klein-base", "topology": "flux3_klein_t2i", "operation": "generate",
            "components": {"unet_name": ["future-klein-base-int8.safetensors", "future-klein-base-fp8.safetensors"], "clip_name": ["future-qwenvl4b.safetensors", "future-qwenvl4b-fp8.safetensors"], "prompt_upsampler_name": ["future-qwen35-upsampler.safetensors"], "vae_name": ["flux2-vae.safetensors"]},
            "clip_type": "flux3", "sampler": {"steps": 50, "cfg": 3.5, "sampler_name": "euler", "scheduler": "simple", "denoise": 1},
        }
        future_registry = yaml.safe_load(creative.COMFY_PROFILE_REGISTRY_PATH.read_text(encoding="utf-8"))
        future_registry["profiles"]["future-klein-profile"] = future_profile
        future_registry_path = base / "future-model-profiles.yaml"
        future_registry_path.write_text(yaml.safe_dump(future_registry, sort_keys=False), encoding="utf-8")
        FakeComfyHandler.extra_unets = ["future-klein-base-int8.safetensors"]
        FakeComfyHandler.extra_clips = ["future-qwenvl4b.safetensors", "future-qwen35-upsampler.safetensors"]
        future_project = fixture_project(base / "future-klein")
        future_path = flux3_workflow(future_project, "future-workflow.json")
        future_selection = {"unet_name": "future-klein-base-int8.safetensors", "clip_name": "future-qwenvl4b.safetensors", "prompt_upsampler_name": "future-qwen35-upsampler.safetensors", "vae_name": "flux2-vae.safetensors"}
        future_workflow = json.loads(future_path.read_text())
        future_workflow["1"]["inputs"]["unet_name"] = future_selection["unet_name"]
        future_workflow["2"]["inputs"]["clip_name"] = future_selection["clip_name"]
        future_workflow["3"]["inputs"]["clip_name"] = future_selection["prompt_upsampler_name"]
        future_path.write_text(json.dumps(future_workflow), encoding="utf-8")
        future_config = {**flux3_config, "workflow_path": future_path.name, "model_profile": "future-klein-profile", "model_id": "future-klein-base", **future_selection}
        future_bundle, _ = write_bundle(future_project, provider="comfyui_local", model={"id": "future-klein-base", "revision": "local-model-files", "license": "fixture", "license_source": "local model card"}, runtime="ComfyUI", runtime_version="fixture-1", comfyui=future_config)
        with patch.object(creative, "COMFY_PROFILE_REGISTRY_PATH", future_registry_path):
            future_ready = creative.preflight(future_project, future_bundle.name)
        require(future_ready["status"] == "READY" and future_ready["model_id"] == "future-klein-base", "data-only model profile could not reuse the audited FLUX 3 topology family")
        profile_parameter_cases(base / "profile-parameters", flux3_config, flux3_bundle_data)
        FakeComfyHandler.flux3 = False
        FakeComfyHandler.extra_unets = []
        FakeComfyHandler.extra_clips = []
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _patched_registry(base: Path, name: str, mutate) -> Path:
    registry = yaml.safe_load(creative.COMFY_PROFILE_REGISTRY_PATH.read_text(encoding="utf-8"))
    mutate(registry)
    path = base / f"{name}.yaml"
    path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
    return path


def profile_parameter_cases(base: Path, flux3_config: dict, flux3_bundle: dict) -> None:
    """Sampler/upsampler values come from profile data bounded by family data; budgets gate submission."""
    base.mkdir(parents=True)
    flux3_project = fixture_project(base / "flux3")
    flux3_workflow(flux3_project, flux3_config["workflow_path"])
    write_bundle(flux3_project, **{key: value for key, value in flux3_bundle.items() if key != "model"}, model=flux3_bundle["model"])
    # Equivalence: the registered profiles resolve to the exact values the executor hard-coded before.
    legacy = {
        "z-image-turbo": ({"steps": None, "cfg": 1, "sampler_name": "res_multistep", "scheduler": "simple", "denoise": 1}, {}),
        "flux3-image-klein-base-int8": ({"steps": 50, "cfg": 3.5, "sampler_name": "euler", "scheduler": "simple", "denoise": 1}, {"max_length": 1024}),
        "flux3-image-klein-distilled-int8": ({"steps": 16, "cfg": 1, "sampler_name": "euler", "scheduler": "simple", "denoise": 1}, {"max_length": 1024}),
    }
    for profile_id, (sampler, upsampler) in legacy.items():
        profile = creative.load_comfy_profile(profile_id)
        require(profile["sampler"] == sampler and profile["upsampler"] == upsampler and "runtime_budget" not in profile,
                f"{profile_id} no longer resolves to its pre-parameterization sampler/upsampler values")
        estimate = creative.comfy_runtime_estimate({"steps": 8}, profile)
        require(estimate["status"] == "UNESTIMATED" and estimate["timeout_seconds"] == 900 and estimate["timeout_source"] == "default",
                f"{profile_id} without a runtime budget must keep the 900 second default and stay unestimated")
        require(creative.effective_timeout_seconds({"timeout_seconds": 10}, profile) == 10, "explicit Bundle timeout must keep precedence")
    base_ready = creative.preflight(flux3_project, "creative-bundle.yaml")
    require(base_ready["status"] == "READY" and base_ready["timeout_seconds"] == flux3_bundle["timeout_seconds"]
            and base_ready["runtime_budget"]["status"] == "UNESTIMATED", "Base preflight changed its timeout or budget status")
    flux_root = flux3_project.resolve(strict=True)
    flux_path = flux3_project / flux3_config["workflow_path"]
    original_flux = flux_path.read_text(encoding="utf-8")
    short_flux = json.loads(original_flux)
    short_flux["5"]["inputs"]["max_length"] = 48
    flux_path.write_text(json.dumps(short_flux), encoding="utf-8")
    expect_blocked(lambda: creative.load_comfy_workflow(flux_root, flux3_config), "Base profile accepted a workflow upsampler token length other than its registered 1024")

    # A same-family variant needs only profile data: fewer steps and a 48-token upsampler.
    def add_variant(registry):
        variant = {**registry["profiles"]["flux3-image-klein-base-int8"]}
        variant["sampler"] = {**variant["sampler"], "steps": 30}
        variant["upsampler"] = {"max_length": 48}
        variant["runtime_budget"] = {"upsampler_token_cap": 64, "timeout_seconds": 1200}
        registry["profiles"]["flux3-klein-base-fast"] = variant
    variant_registry = _patched_registry(base, "variant", add_variant)
    short_flux["9"]["inputs"]["steps"] = 30
    flux_path.write_text(json.dumps(short_flux), encoding="utf-8")
    variant_config = {**flux3_config, "model_profile": "flux3-klein-base-fast"}
    with patch.object(creative, "COMFY_PROFILE_REGISTRY_PATH", variant_registry):
        _, info = creative.load_comfy_workflow(flux_root, variant_config)
        require(info["profile"]["upsampler"]["max_length"] == 48 and info["profile"]["sampler"]["steps"] == 30,
                "data-only FLUX variant did not supply its own sampler steps and upsampler tokens")
        require(creative.effective_timeout_seconds({}, info["profile"]) == 1200, "profile timeout was not used when the Bundle omits timeout_seconds")
        short_flux["5"]["inputs"]["max_length"] = 1024
        flux_path.write_text(json.dumps(short_flux), encoding="utf-8")
        expect_blocked(lambda: creative.load_comfy_workflow(flux_root, variant_config), "variant accepted a workflow token length that differs from its profile")
    flux_path.write_text(original_flux, encoding="utf-8")

    # Z-Image family: the validator reads sampler values from the profile instead of fixed literals.
    zimage_project = fixture_project(base / "zimage")
    zimage_path = zimage_workflow(zimage_project)
    zimage_root = zimage_project.resolve(strict=True)
    zimage_config = {"base_url": "http://127.0.0.1:8188", "workflow_path": zimage_path.name, "model_profile": "z-image-turbo", "model_id": "z-image-turbo",
                     "unet_name": "z_image_turbo_bf16.safetensors", "clip_name": "qwen_3_4b.safetensors", "vae_name": "ae.safetensors",
                     "prompt_node_id": "27", "latent_node_id": "13", "sampler_node_id": "3", "save_node_id": "9"}
    creative.load_comfy_workflow(zimage_root, zimage_config)
    zimage_variant_flow = json.loads(zimage_path.read_text(encoding="utf-8"))
    zimage_variant_flow["3"]["inputs"].update({"cfg": 4, "sampler_name": "euler", "steps": 30})
    zimage_path.write_text(json.dumps(zimage_variant_flow), encoding="utf-8")
    expect_blocked(lambda: creative.load_comfy_workflow(zimage_root, zimage_config), "Z-Image Turbo accepted sampler values outside its registered profile")

    def add_zimage_variant(registry):
        variant = {**registry["profiles"]["z-image-turbo"], "model_id": "z-image-variant"}
        variant["sampler"] = {**variant["sampler"], "steps": 30, "cfg": 4, "sampler_name": "euler"}
        registry["profiles"]["z-image-variant"] = variant
    zimage_registry = _patched_registry(base, "zimage-variant", add_zimage_variant)
    with patch.object(creative, "COMFY_PROFILE_REGISTRY_PATH", zimage_registry):
        _, zinfo = creative.load_comfy_workflow(zimage_root, {**zimage_config, "model_profile": "z-image-variant", "model_id": "z-image-variant"})
        require(zinfo["profile"]["sampler"]["cfg"] == 4, "Z-Image family variant was not accepted as profile data")
        zimage_variant_flow["3"]["inputs"]["steps"] = 12
        zimage_path.write_text(json.dumps(zimage_variant_flow), encoding="utf-8")
        expect_blocked(lambda: creative.load_comfy_workflow(zimage_root, {**zimage_config, "model_profile": "z-image-variant", "model_id": "z-image-variant"}),
                       "Z-Image variant with fixed profile steps accepted different workflow steps")

    # Family and profile values stay inside declared and executor-owned bounds.
    def profile_edit(profile_id: str, **changes):
        def mutate(registry):
            profile = {**registry["profiles"][profile_id]}
            for key, value in changes.items():
                profile[key] = {**profile.get(key, {}), **value} if isinstance(value, dict) else value
            registry["profiles"]["candidate"] = profile
        return mutate

    invalid_profiles = {
        "cfg above family range": profile_edit("flux3-image-klein-base-int8", sampler={"cfg": 31}),
        "sampler outside family enum": profile_edit("flux3-image-klein-base-int8", sampler={"sampler_name": "dpmpp_2m"}),
        "boolean denoise": profile_edit("flux3-image-klein-base-int8", sampler={"denoise": True}),
        "null steps on FLUX": profile_edit("flux3-image-klein-base-int8", sampler={"steps": None}),
        "upsampler tokens above family range": profile_edit("flux3-image-klein-base-int8", upsampler={"max_length": 8192}),
        "upsampler on Z-Image": profile_edit("z-image-turbo", upsampler={"max_length": 48}),
        "upsampler token cap below max_length": profile_edit("flux3-image-klein-base-int8", runtime_budget={"upsampler_token_cap": 512}),
        "upsampler budget on Z-Image": profile_edit("z-image-turbo", runtime_budget={"estimated_upsampler_seconds_per_token": 0.1}),
        "timeout above ceiling": profile_edit("flux3-image-klein-base-int8", runtime_budget={"timeout_seconds": 3601}),
        "unknown budget field": profile_edit("flux3-image-klein-base-int8", runtime_budget={"interrupt": True}),
        "unknown profile field": profile_edit("flux3-image-klein-base-int8", nodes={"99": "CustomNode"}),
        "input image operation": profile_edit("flux3-image-klein-base-int8", operation="edit"),
    }
    invalid_families = {
        "family widened past executor ceiling": lambda registry: registry["topology_families"]["flux3_klein_t2i"]["sampler"]["steps"].update({"max": 1000}),
        "family enum with unsafe value": lambda registry: registry["topology_families"]["flux3_klein_t2i"]["sampler"]["sampler_name"].update({"enum": ["euler; rm"]}),
        "family missing upsampler default": lambda registry: registry["topology_families"]["flux3_klein_t2i"]["upsampler"]["max_length"].pop("default"),
        "family missing sampler field": lambda registry: registry["topology_families"]["flux3_klein_t2i"]["sampler"].pop("denoise"),
        "family declared upsampler on Z-Image": lambda registry: registry["topology_families"]["z_image_split_loader"].update({"upsampler": {"max_length": {"type": "integer", "min": 1, "max": 64, "default": 8}}}),
    }
    for profile_id in ("flux3-image-klein-base-int8", "z-image-turbo"):
        with patch.object(creative, "COMFY_PROFILE_REGISTRY_PATH", _patched_registry(base, "control-" + profile_id, profile_edit(profile_id))):
            require(creative.load_comfy_profile("candidate")["topology"], "unmodified candidate control profile was rejected")
    for name, mutate in invalid_profiles.items():
        with patch.object(creative, "COMFY_PROFILE_REGISTRY_PATH", _patched_registry(base, "invalid-" + str(abs(hash(name))), mutate)):
            expect_blocked(lambda: creative.load_comfy_profile("candidate"), f"invalid profile passed validation: {name}")
    for name, mutate in invalid_families.items():
        with patch.object(creative, "COMFY_PROFILE_REGISTRY_PATH", _patched_registry(base, "family-" + str(abs(hash(name))), mutate)):
            profile_id = "z-image-turbo" if "Z-Image" in name else "flux3-image-klein-base-int8"
            expect_blocked(lambda profile_id=profile_id: creative.load_comfy_profile(profile_id), f"invalid family passed validation: {name}")
    unknown = _patched_registry(base, "unknown-family", lambda registry: registry["topology_families"].update({"custom_topology": registry["topology_families"]["flux3_klein_t2i"]})
                                or registry["profiles"].update({"candidate": {**registry["profiles"]["flux3-image-klein-base-int8"], "topology": "custom_topology"}}))
    with patch.object(creative, "COMFY_PROFILE_REGISTRY_PATH", unknown):
        expect_blocked(lambda: creative.load_comfy_profile("candidate"), "registry data registered a topology family the executor has not reviewed")

    # Runtime budget: a profile estimate over the effective timeout blocks before any submission.
    prompts_before = FakeComfyHandler.prompts
    budgets = {
        # 8.5 + 0.1 s/step * 50 steps * (64x64 px / 0.01 MP reference) = 10.548 s > 10 s Bundle timeout.
        "over": ({"estimated_overhead_seconds": 8.5, "estimated_seconds_per_step": 0.1, "reference_megapixels": 0.01}, "BLOCKED"),
        "near": ({"estimated_overhead_seconds": 9}, "WARNING"),
        "within": ({"estimated_overhead_seconds": 1, "estimated_upsampler_seconds_per_token": 0.001}, "WITHIN_BUDGET"),
    }
    for name, (budget, expected) in budgets.items():
        registry_path = _patched_registry(base, "budget-" + name, lambda registry, budget=budget:
                                          registry["profiles"]["flux3-image-klein-base-int8"].update({"runtime_budget": budget}))
        with patch.object(creative, "COMFY_PROFILE_REGISTRY_PATH", registry_path):
            if expected == "BLOCKED":
                for action in (lambda: creative.preflight(flux3_project, "creative-bundle.yaml"), lambda: creative.execute(flux3_project, "creative-bundle.yaml")):
                    try:
                        action()
                    except creative.Blocked as exc:
                        payload = exc.to_payload()
                        require(exc.reason_code == "comfy_runtime_budget_exceeded" and exc.phase == "creative.runtime_budget",
                                f"over-budget profile did not return a stable pre-submission reason: {exc.reason_code}")
                        details = payload["diagnostics"]["runtime_budget"]
                        require(details["estimated_seconds"] == 10.5 and details["timeout_seconds"] == 10
                                and details["recommended_timeout_seconds"] == 14 and details["steps"] == 50
                                and "private creative prompt" not in repr(payload), "budget diagnostics were incomplete or leaked the prompt")
                    else:
                        raise AssertionError("over-budget profile was accepted")
            else:
                ready = creative.preflight(flux3_project, "creative-bundle.yaml")
                require(ready["status"] == "READY" and ready["runtime_budget"]["status"] == expected, f"runtime budget {name} did not report {expected}")
    require(FakeComfyHandler.prompts == prompts_before, "runtime budget checks submitted a ComfyUI workflow")


class OwnedJobComfyHandler(BaseHTTPRequestHandler):
    """Stateful synthetic ComfyUI queue mirroring the 0.42.x /queue and targeted /interrupt contract."""
    running: ClassVar[list[str]] = []
    pending: ClassVar[list[str]] = []
    requests: ClassVar[list[tuple[str, str, object]]] = []
    honor_interrupt = True
    accept_as = "pending"
    queue_status: int | None = None
    accepted = 0

    def log_message(self, *_args):
        return

    def _json(self, value, status: int = 200):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        cls = type(self)
        cls.requests.append(("GET", self.path, None))
        if self.path == "/queue":
            if cls.queue_status is not None:
                return self._json({"error": "fixture"}, cls.queue_status)
            # Items carry a private workflow and extra data that the executor must never copy.
            item = lambda number, prompt_id: [number, prompt_id, {"1": {"inputs": {"text": "private queued prompt"}}}, {"client_id": "x"}, []]
            return self._json({"queue_running": [item(0, prompt_id) for prompt_id in cls.running],
                               "queue_pending": [item(index + 1, prompt_id) for index, prompt_id in enumerate(cls.pending)]})
        if self.path.startswith("/history/"):
            return self._json({})
        self.send_error(404)

    def do_POST(self):
        cls = type(self)
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")
        cls.requests.append(("POST", self.path, body))
        if self.path == "/prompt":
            cls.accepted += 1
            prompt_id = f"00000000-0000-4000-8000-{cls.accepted:012d}"
            (cls.running if cls.accept_as == "running" else cls.pending).append(prompt_id)
            return self._json({"prompt_id": prompt_id, "number": cls.accepted})
        if self.path == "/queue":
            cls.pending[:] = [item for item in cls.pending if item not in body.get("delete", [])]
            return self._json({})
        if self.path == "/interrupt":
            # Targeted interrupt: only the named running prompt is stopped (server-side re-check).
            if cls.honor_interrupt and body.get("prompt_id") in cls.running:
                cls.running.remove(body["prompt_id"])
            return self._json({})
        self.send_error(404)


def owned_job_recovery_cases(base: Path) -> None:
    base.mkdir(parents=True, exist_ok=True)
    handler = OwnedJobComfyHandler
    server = HTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    provider = {"base_url": url, "workflow": {"1": {"inputs": {}}, "2": {"inputs": {}}, "3": {"inputs": {}}, "4": {"inputs": {}}},
                "prompt_id": "1", "latent_node_id": "2", "sampler_node_id": "3", "save_nodes": ["4"],
                "config": {"model_profile": "flux3-image-klein-base-int8"}}
    bundle = {"prompt": "private owned-job prompt", "operation": "generate"}
    foreign = "ffffffff-0000-4000-8000-000000000001"

    def reset(*, running=(), pending=(), honor=True, accept_as="pending", queue_status=None):
        handler.running[:] = list(running)
        handler.pending[:] = list(pending)
        handler.requests.clear()
        handler.honor_interrupt, handler.accept_as, handler.queue_status = honor, accept_as, queue_status

    def timed_out(timeout: float = 0.3) -> creative.Blocked:
        try:
            creative.comfy_execute(bundle, provider, base / "never.png", timeout)
        except creative.Blocked as exc:
            require(exc.reason_code == "comfy_job_recovery_required", "owned-job timeout used the wrong reason code")
            require(not (base / "never.png").exists(), "owned-job timeout left an output")
            require(sum(path == "/prompt" for method, path, _ in handler.requests if method == "POST") == 1, "timeout resubmitted the job")
            return exc
        raise AssertionError("owned-job timeout unexpectedly completed")

    def posts(path: str) -> list[object]:
        return [body for method, request_path, body in handler.requests if method == "POST" and request_path == path]

    try:
        # Loopback allowlist: GET /queue and POST /interrupt only, with no query; nothing else is opened.
        creative.validate_local_request(url + "/interrupt", "POST", "comfyui")
        creative.validate_local_request(url + "/queue", "GET", "comfyui")
        for method, path in (("GET", "/interrupt"), ("POST", "/interrupt?all=1"), ("GET", "/queue?x=1"), ("POST", "/free"), ("POST", "/history")):
            expect_blocked(lambda method=method, path=path: creative.validate_local_request(url + path, method, "comfyui"),
                           f"allowlist accepted {method} {path}")
        expect_blocked(lambda: creative.validate_local_request("http://192.0.2.1:8188/interrupt", "POST", "comfyui"),
                       "non-loopback interrupt was accepted")

        # 1. Owned job running at timeout while a foreign job waits: targeted interrupt of only the owned id.
        reset(pending=[foreign], accept_as="running")
        exc = timed_out()
        details = exc.diagnostics
        owned_id = posts("/interrupt")[0]["prompt_id"] if posts("/interrupt") else None
        require(posts("/interrupt") == [{"prompt_id": owned_id}] and owned_id != foreign, "interrupt was not targeted at the owned prompt_id")
        require(handler.pending == [foreign] and posts("/queue") == [], "foreign queued job was touched")
        require(details["job_state"] == "CLEARED" and details["interrupt_requested"] is True and details["ownership"] == "AIPS_OWNED"
                and details["recovery"]["automatic_resubmission"] is False, "owned interrupt did not report a re-checked final state")
        require(creative.owned_comfy_jobs(url) == [], "cleared owned job was kept in the ledger")
        payload = json.dumps(exc.to_payload(), ensure_ascii=False)
        require("private" not in payload and str(base) not in payload and "aips creative recover" in payload,
                "recovery payload leaked prompt text/paths or lacked Traditional Chinese recovery")

        # 2. Foreign job running, owned job still queued: exact-id delete, never interrupt.
        reset(running=[foreign])
        exc = timed_out()
        require(posts("/interrupt") == [] and handler.running == [foreign], "a foreign running job was interrupted")
        require(len(posts("/queue")) == 1 and foreign not in posts("/queue")[0]["delete"], "queued owned job was not deleted by exact id")
        require(exc.diagnostics["job_state"] == "CLEARED" and exc.diagnostics["other_jobs_running"] == 1, "foreign job count missing")

        # 3. Queue unreadable: no interrupt without ownership evidence; ledger keeps the job for explicit recovery.
        reset(queue_status=500)
        exc = timed_out()
        require(posts("/interrupt") == [] and exc.diagnostics["job_state"] == "UNKNOWN"
                and exc.diagnostics["recovery"]["action"] == "RUN_AIPS_CREATIVE_RECOVER", "unknown queue state permitted interrupt")
        unknown = [item["prompt_id"] for item in creative.owned_comfy_jobs(url)]
        require(len(unknown) == 1, "unknown-state job was not retained in the owned-job ledger")

        # 4. Interrupt not honored (e.g. older ComfyUI or a busy node): STILL_RUNNING is reported, never resubmitted.
        time.sleep(1.1)  # The ledger rounds the job timeout up to whole seconds; let it elapse.
        handler.queue_status = None
        handler.running[:] = unknown
        handler.pending.clear()
        handler.requests.clear()
        handler.honor_interrupt = False
        with patch.object(creative, "COMFY_RECHECK_INTERVAL_SECONDS", 0.01):
            stuck = creative.recover_comfy_jobs(url)
        require(stuck["status"] == "RECOVERY_INCOMPLETE" and stuck["jobs"] == [{"prompt_id": unknown[0], "profile_id": "flux3-image-klein-base-int8", "state": "STILL_RUNNING"}]
                and posts("/prompt") == [], "unhonored interrupt was not reported as STILL_RUNNING")
        require(len(creative.owned_comfy_jobs(url)) == 1, "still-running job was released from the ledger")

        # 5. Restart: a new process recognizes ownership from the ledger alone and interrupts only that id.
        handler.requests.clear()
        handler.honor_interrupt = True
        handler.running[:] = unknown
        cli = subprocess.run([sys.executable, str(ROOT / "scripts/creative_execution.py"), "recover", "--base-url", url],
                             capture_output=True, text=True, timeout=30, check=False, env=os.environ.copy())
        recovered = json.loads(cli.stdout)
        require(cli.returncode == 0 and recovered["status"] == "RECOVERED" and recovered["job_state"] == "CLEARED"
                and posts("/interrupt") == [{"prompt_id": unknown[0]}] and recovered["automatic_resubmission"] is False,
                "restart recovery did not interrupt the ledger-owned job: " + cli.stdout + cli.stderr)
        require(creative.owned_comfy_jobs(url) == [] and "private" not in cli.stdout and str(base) not in cli.stdout,
                "recovery did not release the ledger or leaked private data")

        # 6. Ownership is bound to the endpoint and the job's own deadline.
        reset(running=["00000000-0000-4000-8000-0000000000aa"])
        require(creative.record_owned_comfy_job("http://127.0.0.1:1", "00000000-0000-4000-8000-0000000000aa", None, 0), "fixture record failed")
        require(creative.record_owned_comfy_job(url, "00000000-0000-4000-8000-0000000000bb", None, 3600), "fixture record failed")
        handler.running.append("00000000-0000-4000-8000-0000000000bb")
        idle = creative.recover_comfy_jobs(url)
        require(idle["status"] == "NOTHING_TO_RECOVER" and idle["active_within_timeout"] == 1 and posts("/interrupt") == [],
                "recovery interrupted a job owned by another endpoint or still inside its own timeout")
        ledger = creative.comfy_job_ledger_path()
        require(ledger.stat().st_mode & 0o777 == 0o600 and ledger.parent.stat().st_mode & 0o777 == 0o700, "ledger permissions are not private")
        document = json.loads(ledger.read_text(encoding="utf-8"))
        require(all(set(item) == {"prompt_id", "submitted_at", "profile_id", "timeout_seconds", "binding_sha256"} for item in document["jobs"])
                and "127.0.0.1" not in ledger.read_text(encoding="utf-8") and "private" not in ledger.read_text(encoding="utf-8"),
                "ledger stored fields beyond the privacy-bounded schema")
        document["jobs"][-1]["timeout_seconds"] = 0
        ledger.write_text(json.dumps(document), encoding="utf-8")
        require(all(item["prompt_id"] != "00000000-0000-4000-8000-0000000000bb" for item in creative.owned_comfy_jobs(url)),
                "a tampered ledger entry still proved ownership")
        require(creative.recover_comfy_jobs(url)["status"] == "NOTHING_TO_RECOVER" and posts("/interrupt") == [],
                "a tampered ledger entry caused an interrupt")
        creative.release_owned_comfy_jobs({"00000000-0000-4000-8000-0000000000aa", "00000000-0000-4000-8000-0000000000bb"})
    finally:
        server.shutdown()
        thread.join(timeout=2)


def output_magic(path: Path) -> bool:
    return creative.output_magic(path)


def expect_blocked(action, message: str):
    try:
        action()
    except (creative.Blocked, OSError, ValueError):
        return
    raise AssertionError(message)


def no_engine_case(base: Path):
    project = fixture_project(base)
    bundle, _ = write_bundle(project, provider="auto", mflux_executable="/missing/mflux", model={"id": "local-model", "revision": "r1", "license": "local", "license_source": "fixture"}, comfyui=None)
    try:
        creative.preflight(project, bundle.name)
    except creative.Blocked as exc:
        require(exc.reason_code == "BLOCKED_NO_ENGINE", "missing engine did not return BLOCKED_NO_ENGINE")
        require(exc.diagnostics.get("generation_executed") is False and exc.diagnostics.get("external_image_egress") is False,
                "missing-engine diagnostics implied inference or external image egress")
        require(exc.diagnostics.get("comfyui", {}).get("configured") is False
                and exc.diagnostics.get("comfyui", {}).get("status") in {"UNAVAILABLE", "UNVERIFIED", "REACHABLE"},
                "unconfigured ComfyUI discovery status was not explained")
        require(exc.diagnostics.get("readiness", {}).get("inference") == "INFERENCE_UNVERIFIED",
                "missing engine diagnostics implied inference readiness")
        require(isinstance(exc.diagnostics.get("mflux"), list), "missing-engine diagnostics omitted MFLUX probes")
    else:
        raise AssertionError("missing local engine was presented as READY")


def diagnostic_cases(base: Path):
    normalized = creative.error_payload(status="UNAVAILABLE", phase="creative.discovery",
                                        reason_code="provider_http_error", source="comfyui", retryable=True,
                                        message="Bearer synthetic-secret /Users/lucas/private/profile.yaml token=abc",
                                        diagnostics={"http_status": 503, "body": "synthetic-token-body", "authorization": "secret"})
    require({"status", "phase", "reason_code", "source", "retryable", "trace_id", "recovery", "diagnostics"} <= normalized.keys()
            and normalized["diagnostics"] == {"http_status": 503}
            and "synthetic-secret" not in repr(normalized) and "/Users/lucas/" not in repr(normalized)
            and "[REDACTED]" in normalized["message"],
            "structured provider diagnostics exposed unbounded data or omitted stable fields")
    project = fixture_project(base)
    executable = project / "mflux-generate"
    executable.write_text("fixture", encoding="utf-8")
    executable.chmod(0o755)
    which = lambda command: str(executable) if command == "mflux-generate" else None
    with patch.object(creative.shutil, "which", side_effect=which), \
         patch.object(creative.subprocess, "run", side_effect=subprocess.TimeoutExpired("mflux-generate", 3)):
        timed_out = creative.discover(project)
    timeout = next(item for item in timed_out["runtimes"] if item["command"] == "mflux-generate")
    require(timeout["health_status"] == "UNVERIFIED" and timeout["available"] is True
            and timeout["capability_status"] == "COMMAND_PRESENT"
            and timeout["readiness"]["runtime"] == "RUNTIME_UNVERIFIED" and timeout["version_status"] == "TIMEOUT"
            and timeout["reason_code"] == "version_probe_timeout", "version timeout was not classified precisely")
    require(timed_out["generation_executed"] is False and timed_out["external_image_egress"] is False,
            "health discovery performed inference or external egress")
    server, thread = comfy_server()
    try:
        invalid_requests = (
            ("http://example.invalid:8188/system_stats", "GET", "comfyui"),
            ("http://127.0.0.1:8188/prompt", "GET", "comfyui"),
            ("http://127.0.0.1:8188/system_stats", "POST", "comfyui"),
            ("http://127.0.0.1:8188/arbitrary", "GET", "comfyui"),
            ("http://127.0.0.1:11435/api/chat", "POST", "ollama"),
        )
        for request in invalid_requests:
            expect_blocked(lambda item=request: creative.validate_local_request(*item),
                           f"unapproved local provider request was accepted: {request}")
        loopback = f"http://127.0.0.1:{server.server_port}"
        with patch.object(creative, "DEFAULT_COMFYUI_BASE_URL", loopback), \
             patch.object(creative.shutil, "which", return_value=None):
            discovered = creative.discover(project)
        require(discovered["comfyui"]["status"] == "REACHABLE"
                and discovered["comfyui"]["readiness"]["runtime"] == "RUNTIME_VERIFIED"
                and discovered["comfyui"]["readiness"]["inference"] == "INFERENCE_UNVERIFIED"
                and all(value == "MODEL_CATALOG_AVAILABLE" for value in discovered["comfyui"]["node_capabilities"].values())
                and discovered["comfyui"]["model_catalog"]["CheckpointLoaderSimple"] == ["model.safetensors"]
                and FakeComfyHandler.prompts == 0,
                "read-only loopback discovery did not report staged service/model readiness")
        require(creative.discover_comfyui("http://127.0.0.1:8189")["reason_code"] == "default_loopback_only",
                "ComfyUI discovery accepted a non-default service endpoint")
        FakeComfyHandler.missing_vae = True
        try:
            with patch.object(creative, "DEFAULT_COMFYUI_BASE_URL", loopback):
                empty_catalog = creative.discover_comfyui()
            require(empty_catalog["readiness"]["model"] == "MODEL_CATALOG_INCOMPLETE"
                    and empty_catalog["node_capabilities"]["VAELoader"] == "MODEL_CATALOG_EMPTY",
                    "empty ComfyUI inventory was reported as an available model")
        finally:
            FakeComfyHandler.missing_vae = False
        for status, expected_status, expected_reason, retryable in (
            (404, "UNVERIFIED", "provider_http_error", False),
            (500, "UNAVAILABLE", "provider_http_error", True),
            (302, "UNVERIFIED", "comfy_redirect_refused", False),
        ):
            FakeComfyHandler.system_status = status
            try:
                with patch.object(creative, "DEFAULT_COMFYUI_BASE_URL", loopback):
                    failed_probe = creative.discover_comfyui()
                require(failed_probe["status"] == expected_status and failed_probe["reason_code"] == expected_reason
                        and failed_probe["retryable"] is retryable
                        and failed_probe.get("diagnostics", {}).get("http_status") == status
                        and "synthetic-token-body" not in repr(failed_probe),
                        f"HTTP {status} ComfyUI diagnostics were not classified/redacted: {failed_probe}")
            finally:
                FakeComfyHandler.system_status = None
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    with patch.object(creative.shutil, "which", side_effect=which), \
         patch.object(creative.subprocess, "run", return_value=SimpleNamespace(returncode=7, stdout="", stderr="failed")):
        failed = creative.discover(project)
    nonzero = next(item for item in failed["runtimes"] if item["command"] == "mflux-generate")
    require(nonzero["available"] is True and nonzero["capability_status"] == "COMMAND_PRESENT"
            and nonzero["health_status"] == "UNVERIFIED" and nonzero["reason_code"] == "version_probe_nonzero_exit" and nonzero["exit_code"] == 7,
            "nonzero version probe did not retain its safe failure category")
    with patch.object(creative.shutil, "which", side_effect=which), \
         patch.object(creative.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="runtime ready", stderr="")):
        unparsed = creative.discover(project)
    responsive = next(item for item in unparsed["runtimes"] if item["command"] == "mflux-generate")
    require(responsive["health_status"] == "HEALTHY" and responsive["readiness"]["runtime"] == "RUNTIME_VERIFIED"
            and responsive["version_status"] == "UNRECOGNIZED",
            "responsive command with an unknown version was conflated with a failed health probe")


def configure_cases(base: Path):
    project = fixture_project(base)
    executable = mflux_fixture(project)
    bundle_path, bundle = write_bundle(project)
    before = bundle_path.read_bytes()
    settings = {key: bundle[key] for key in ("provider", "model", "runtime", "runtime_version", "mflux_executable", "width", "height", "steps")}
    args_path = base / "configure-args.txt"
    os.environ["FAKE_MFLUX_ARGS"] = str(args_path)
    configured = creative.configure(project, bundle_path.name, settings)
    require(bundle_path.read_bytes() == before and not args_path.exists(), "configure changed source or launched engine")
    require(configured["status"] == "CONFIGURED" and configured["generation_executed"] is False, "configure claimed generation")
    require(creative.preflight(project, configured["bundle"])["status"] == "READY" and not args_path.exists(), "configured preflight launched engine")
    output = creative.execute(project, configured["bundle"])
    manifest = json.loads((project / output["manifest"]).read_text())
    require(manifest["acceptance"] == {"file_validity": "PASS", "visual_quality": "PENDING", "user_acceptance": "NOT_RECORDED"}, "execution conflated acceptance states")
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(lambda _: creative.configure(project, bundle_path.name, settings), range(3)))
    require(len({result["bundle"] for result in results}) == 3, "configuration collision overwrote another version")
    for malicious in ({"output_path": "outside.png"}, {"provider": "cloud"}, {"model": {"id": []}}, {"comfyui": {"shell": "touch bad"}}, {"prompt": "x" * 4001}, {"width": True}):
        expect_blocked(lambda malicious=malicious: creative.configure(project, bundle_path.name, malicious), "unsafe configuration accepted")
    link = project / "linked.yaml"
    link.symlink_to(bundle_path)
    expect_blocked(lambda: creative.configure(project, link.name, settings), "symlink configuration source accepted")
    require(not list(project.glob(".aips-configure-*")), "configuration left staging files")
    inventory = creative.discover(project)
    require(inventory["generation_executed"] is False and inventory["model_status"] == "NOT_VERIFIED", "inventory claimed model inference")
    require(executable.is_file(), "discovery changed runtime")
    prepared = creative.prepare(project, "art", "wizard", "Wizard", "A wizard", "Detailed anime", "Generate a wizard image", ["round glasses"])
    profile_bundle = creative.configure(project, prepared["bundle"], settings)
    style = project / prepared["scope"] / "STYLE_PROFILE.yaml"
    style_before = style.read_bytes()
    def mutate_profile(_root, _bundle, _provider, temporary, _timeout):
        temporary.write_bytes(PNG)
        style.write_text("changed during generation")
    with patch.object(creative, "mflux_execute", side_effect=mutate_profile):
        expect_blocked(lambda: creative.execute(project, profile_bundle["bundle"]), "profile changed during generation was accepted")
    scoped = yaml.safe_load((project / profile_bundle["bundle"]).read_text())
    require(not (project / scoped["output_path"]).exists(), "changed-profile output was published")
    style.write_bytes(style_before)
    generated = creative.execute(project, profile_bundle["bundle"])
    provenance = json.loads((project / generated["manifest"]).read_text())
    require(len(provenance["profiles"]) == 2, "prepared profiles were not bound to output")
    require(provenance["prompt_compiler"] == "profile-driven-v1" and len(provenance["compiled_prompt_sha256"]) == 71, "compiled prompt fingerprint was not recorded")
    require("round glasses" not in json.dumps(provenance) and "private creative prompt" not in json.dumps(provenance), "profile text or raw prompt was persisted in the manifest")
    style.write_text("changed after generation")
    expect_blocked(lambda: creative.review(project, generated["manifest"], "Human", "PASS", "fixture"), "stale profile review was accepted")
    corrupt = project / "corrupt.png"
    for content in (PNG[:16], PNG[:-4], PNG[:48] + b"bad!" + PNG[52:], b"\x89PNG\r\n\x1a\n"):
        corrupt.write_bytes(content)
        require(not creative.output_magic(corrupt), "invalid raster container was accepted")
    manifest_context = {"task": {"classification": {"domain": "creative", "intent": "create", "creative_medium": "raster"}}}
    denied = guard.evaluate_write(tool="write", resources=["fallback.svg"], root=str(project), manifest=manifest_context)
    require(denied["reason_code"] == "creative_medium_mismatch", "raster silently fell back to SVG")
    manifest_context["task"]["classification"]["creative_medium"] = "vector"
    require(guard.evaluate_write(tool="write", resources=["vector.svg"], root=str(project), manifest=manifest_context)["decision"] == "ALLOW", "explicit vector output blocked")


def main() -> int:
    multi_reference_binding_cases()
    with tempfile.TemporaryDirectory(prefix="aips-creative-execution-") as tmp:
        base = Path(tmp)
        state = base / "state"
        state.mkdir()
        os.environ["XDG_STATE_HOME"] = str(state)
        no_engine_case(base / "no-engine")
        diagnostic_cases(base / "diagnostics")
        configure_cases(base / "configure")
        request_policy_cases()
        node = os.environ.get("AIPS_NODE_BINARY") or shutil.which("node")
        if node:
            tool_project = base / "native-tool"
            tool_project.mkdir()
            environment = {**os.environ, "AIPS_CLI": str(ROOT / "bin/aips"), "AIPS_GUARD_PYTHON": sys.executable,
                           "AIPS_VALIDATION_PYTHON": sys.executable, "XDG_CONFIG_HOME": str(base / "native-config")}
            native = subprocess.run([node, str(ROOT / "tests/evidence/creative_tool_harness.mjs"), str(ROOT), str(tool_project)],
                                    env=environment, capture_output=True, text=True, timeout=120, check=False)
            require(native.returncode == 0, "native creative tool fixture failed: " + native.stdout + native.stderr)
            print(native.stdout.strip())
        mflux_cases(base / "mflux")
        mflux_capability_cases(base / "mflux-capabilities")
        prepare_cases(base / "prepare")
        cli_prepare_case(base / "cli")
        comfy_cases(base / "comfy")
        owned_job_recovery_cases(base / "owned-jobs")
        trace = creative.read_trace(100)
        require(trace["status"] == "READY", "privacy-limited creative trace was not readable")
        trace_file = creative.trace_path()
        with trace_file.open("a") as stream:
            stream.write(json.dumps({"provider": "mflux_local", "operation": "generate", "status": "COMPLETE", "prompt": "private"}) + "\n")
        filtered = creative.read_trace(100)
        require(filtered["invalid_records"] >= 1 and "prompt" not in json.dumps(filtered), "trace reader accepted a sensitive field")
    print("Creative execution lifecycle PASS: EPHEMERAL preparation/versioning, preflight, fixed MFLUX CLI mapping and multi-reference edit, ComfyUI loopback/single-reference edit hash, create-only output, finite retry, provenance, human review and trace privacy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

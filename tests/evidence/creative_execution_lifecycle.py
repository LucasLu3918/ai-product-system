"""Synthetic local-only lifecycle for Creative Bundle execution."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import zlib
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from types import SimpleNamespace
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
            return self.send_bytes(b"{}")
        if self.path == "/object_info/CheckpointLoaderSimple":
            return self.send_bytes(json.dumps({"CheckpointLoaderSimple": {"input": {"required": {"ckpt_name": [["model.safetensors"]]}}}}).encode())
        if self.path == "/object_info/UNETLoader":
            unet = type(self).unet_filename or ("z_image_turbo_fp8.safetensors" if type(self).fp8_unet else "z_image_turbo_bf16.safetensors")
            return self.send_bytes(json.dumps({"UNETLoader": {"input": {"required": {"unet_name": [[unet]]}}}}).encode())
        if self.path == "/object_info/CLIPLoader":
            return self.send_bytes(json.dumps({"CLIPLoader": {"input": {"required": {"clip_name": [["qwen_3_4b.safetensors"]], "type": [["lumina2"]]}}}}).encode())
        if self.path == "/object_info/VAELoader":
            choices = [] if type(self).missing_vae else ["ae.safetensors"]
            return self.send_bytes(json.dumps({"VAELoader": {"input": {"required": {"vae_name": [choices]}}}}).encode())
        if self.path.startswith("/view?"):
            from urllib.parse import parse_qs, urlsplit
            query = parse_qs(urlsplit(self.path).query)
            body = self.staged_reference if query.get("type") == ["input"] else PNG_WITH_PROMPT
            return self.send_bytes(body, "image/png")
        if self.path == "/history/fixture-job":
            item = {self.prompt_id: {"status": {"status_str": "success", "completed": True}, "outputs": {"9": {"images": [{"filename": "generated.png", "subfolder": "", "type": "output"}]}}}}
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
    bundle_path, bundle = write_bundle(project)
    before = creative.preflight(project, bundle_path.name)
    require(before["status"] == "READY" and not args_path.exists(), "preflight started the configured generator")
    compatibility = before["backend_compatibility"]
    require(compatibility["status"] == "UNVERIFIED" and compatibility["backend"] == "mflux_local", "static readiness must not imply real hardware/backend compatibility")
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
    require("--output\n" in args and "--model-path\n" in args and "--prompt\nprivate creative prompt" in args, "fixed MFLUX argv was not formed")
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
        require(executed["status"] == "COMPLETE" and FakeComfyHandler.workflow["6"]["inputs"]["text"] == "private creative prompt", "ComfyUI workflow did not receive the explicit prompt")
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
    finally:
        server.shutdown()
        server.server_close()
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
        loopback = f"http://127.0.0.1:{server.server_port}"
        with patch.object(creative, "DEFAULT_COMFYUI_BASE_URL", loopback), \
             patch.object(creative.shutil, "which", return_value=None):
            discovered = creative.discover(project)
        require(discovered["comfyui"]["status"] == "REACHABLE"
                and discovered["comfyui"]["readiness"]["runtime"] == "RUNTIME_VERIFIED"
                and discovered["comfyui"]["readiness"]["inference"] == "INFERENCE_UNVERIFIED"
                and all(value == "MODEL_CATALOG_AVAILABLE" for value in discovered["comfyui"]["node_capabilities"].values())
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
                                    env=environment, capture_output=True, text=True, timeout=60, check=False)
            require(native.returncode == 0, "native creative tool fixture failed: " + native.stdout + native.stderr)
            print(native.stdout.strip())
        mflux_cases(base / "mflux")
        mflux_capability_cases(base / "mflux-capabilities")
        prepare_cases(base / "prepare")
        cli_prepare_case(base / "cli")
        comfy_cases(base / "comfy")
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

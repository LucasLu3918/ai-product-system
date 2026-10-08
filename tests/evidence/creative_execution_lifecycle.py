"""Synthetic local-only lifecycle for Creative Bundle execution."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import creative_execution as creative
import opencode_native_guard as guard

PNG = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c636000020000050001a5f645400000000049454e44ae426082")


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


def mflux_fixture(project: Path, *, sleep_seconds: float = 0) -> Path:
    executable = project / "bin/mflux-generate"
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
        if self.path.startswith("/view?"):
            from urllib.parse import parse_qs, urlsplit
            query = parse_qs(urlsplit(self.path).query)
            body = self.staged_reference if query.get("type") == ["input"] else PNG
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


def guard_cases(project: Path):
    inside = str(project)
    allowed = guard.evaluate_shell(command="aips creative preflight --project . --bundle creative-bundle.yaml", cwd=inside, root=inside)
    require(allowed["decision"] == "ALLOW" and allowed["reason_code"] == "shell_aips_readonly", "bounded Creative Preflight was not allowed")
    denied = guard.evaluate_shell(command="aips creative execute --project . --bundle creative-bundle.yaml", cwd=inside, root=inside)
    require(denied["decision"] == "DENY" and denied["reason_code"] == "shell_aips_command_unsupported", "Creative execution leaked into the Shell allowlist")
    for command in ("python3 -c print(1)", "aips publish push", "aips creative preflight --project /tmp --bundle x.yaml", "aips creative trace --limit 1000", "aips creative preflight --project . --bundle x.yaml && pwd"):
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
    result = creative.execute(project, bundle_path.name)
    output = project / bundle["output_path"]
    manifest_path = project / result["manifest"]
    manifest = json.loads(manifest_path.read_text())
    args = args_path.read_text()
    require(result["status"] == "COMPLETE" and result["review_status"] == "PENDING", "MFLUX execution did not retain pending human review")
    require(manifest["model"]["revision"] == "fixture-sha" and manifest["bundle_sha256"].startswith("sha256:"), "model/bundle provenance was not recorded")
    require(manifest["output"]["sha256"] == creative.digest(output) and manifest["privacy"]["external_image_egress"] is False, "output provenance or privacy boundary missing")
    require("private creative prompt" not in manifest_path.read_text() and "private creative prompt" not in creative.read_trace(20).__repr__(), "raw prompt reached a manifest or trace")
    require("--output\n" in args and "--model-path\n" in args and "--prompt\nprivate creative prompt" in args, "fixed MFLUX argv was not formed")
    require("HF_HUB_OFFLINE" not in args and output_magic(output), "MFLUX output fixture was not written")
    expect_blocked(lambda: creative.execute(project, bundle_path.name), "existing output was overwritten")
    reviewed = creative.review(project, result["manifest"], "Independent Human", "PASS", "Identity and style match the approved profiles.")
    require(reviewed["status"] == "REVIEWED" and json.loads(manifest_path.read_text())["review"]["decision"] == "PASS", "human review was not recorded")
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
        executed = creative.execute(project, bundle_path.name)
        require(executed["status"] == "COMPLETE" and FakeComfyHandler.workflow["6"]["inputs"]["text"] == "private creative prompt", "ComfyUI workflow did not receive the explicit prompt")
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
    else:
        raise AssertionError("missing local engine was presented as READY")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="aips-creative-execution-") as tmp:
        base = Path(tmp)
        state = base / "state"
        state.mkdir()
        os.environ["XDG_STATE_HOME"] = str(state)
        no_engine_case(base / "no-engine")
        mflux_cases(base / "mflux")
        comfy_cases(base / "comfy")
        trace = creative.read_trace(100)
        require(trace["status"] == "READY", "privacy-limited creative trace was not readable")
        trace_file = creative.trace_path()
        with trace_file.open("a") as stream:
            stream.write(json.dumps({"provider": "mflux_local", "operation": "generate", "status": "COMPLETE", "prompt": "private"}) + "\n")
        filtered = creative.read_trace(100)
        require(filtered["invalid_records"] >= 1 and "prompt" not in json.dumps(filtered), "trace reader accepted a sensitive field")
    print("Creative execution lifecycle PASS: EPHEMERAL scope, preflight, MFLUX argv/offline, ComfyUI loopback/edit hash, create-only output, finite retry, provenance, human review and trace privacy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

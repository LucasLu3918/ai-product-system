"""Synthetic, loopback-only acceptance lifecycle for dynamic ComfyUI workflows.

This proves request, schema, policy, binding, recovery and output contracts. It
does not execute model weights or claim hardware inference compatibility.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import comfyui_workflow
import creative_execution as creative

PNG = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c6360000200000500017a5eab3f0000000049454e44ae426082")
MODEL = "a-model-never-registered-in-aips.safetensors"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def field(kind: str, **options):
    return [kind, options] if options else [kind]


def schema() -> dict:
    return {
        "CheckpointLoaderSimple": {"python_module": "nodes", "input": {"required": {"ckpt_name": [[MODEL]]}}, "output": ["MODEL", "CLIP", "VAE"]},
        "CLIPTextEncode": {"python_module": "nodes", "input": {"required": {"text": field("STRING", multiline=True), "clip": ["CLIP"]}}, "output": ["CONDITIONING"]},
        "EmptyLatentImage": {"python_module": "nodes", "input": {"required": {"width": field("INT", min=64, max=2048), "height": field("INT", min=64, max=2048), "batch_size": field("INT", min=1, max=8)}}, "output": ["LATENT"]},
        "KSampler": {"python_module": "nodes", "input": {"required": {"model": ["MODEL"], "positive": ["CONDITIONING"], "negative": ["CONDITIONING"], "latent_image": ["LATENT"], "seed": field("INT", min=0), "steps": field("INT", min=1), "cfg": field("FLOAT", min=0), "sampler_name": [["euler"]], "scheduler": [["normal"]], "denoise": field("FLOAT", min=0, max=1)}}, "output": ["LATENT"]},
        "VAEDecode": {"python_module": "nodes", "input": {"required": {"samples": ["LATENT"], "vae": ["VAE"]}}, "output": ["IMAGE"]},
        "SaveImage": {"python_module": "nodes", "input": {"required": {"images": ["IMAGE"], "filename_prefix": field("STRING")}}, "output": []},
        "ComfyCoreNovel": {"python_module": "comfy_extras.nodes_novel", "input": {"required": {"enabled": field("BOOLEAN")}}, "output": ["MODEL"]},
        "RemoteImageAPI": {"python_module": "comfy_api_nodes.nodes_remote", "input": {"required": {"url": field("STRING")}}, "output": ["IMAGE"]},
        "UnreviewedCustom": {"python_module": "custom_nodes.unreviewed", "input": {"required": {"enabled": field("BOOLEAN")}}, "output": ["IMAGE"]},
    }


def valid_graph():
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": MODEL}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "workflow default prompt", "clip": ["1", 1]}},
        "3": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "4": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["2", 0], "negative": ["2", 0], "latent_image": ["3", 0], "seed": 77, "steps": 50, "cfg": 3.5, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0}},
        "5": {"class_type": "VAEDecode", "inputs": {"samples": ["4", 0], "vae": ["1", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["5", 0], "filename_prefix": "workflow-default"}},
    }


class Handler(BaseHTTPRequestHandler):
    prompts = 0
    prompt_graph = None
    drop_response = False

    def log_message(self, *_args):
        pass

    def send_json(self, value):
        body = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/system_stats":
            return self.send_json({"system": {"comfyui_version": "fixture-1"}})
        if self.path == "/object_info":
            return self.send_json(schema())
        if self.path == "/history/dynamic-job":
            return self.send_json({"dynamic-job": {"status": {"status_str": "success", "completed": True}, "outputs": {"9": {"images": [{"filename": "fixture.png", "subfolder": "", "type": "output"}]}}}})
        if urlsplit(self.path).path == "/view":
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(PNG)))
            self.end_headers()
            self.wfile.write(PNG)
            return
        self.send_error(404)

    def do_POST(self):
        if self.path != "/prompt":
            return self.send_error(404)
        size = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(size))
        type(self).prompt_graph = body["prompt"]
        type(self).prompts += 1
        if type(self).drop_response:
            self.close_connection = True
            return
        self.send_json({"prompt_id": "dynamic-job"})


def server():
    Handler.prompts = 0
    Handler.prompt_graph = None
    Handler.drop_response = False
    instance = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    return instance, thread


def write_bundle(root: Path, base: str, workflow_path: str, bindings: dict | None = None):
    bundle = {
        "version": 1, "mode": "EPHEMERAL", "operation": "generate", "provider": "comfyui_local",
        "prompt": "A synthetic acceptance prompt", "output_scope": "out", "output_path": "out/asset.png",
        "width": 512, "height": 640, "steps": 20, "seed": 123, "max_retries": 2,
        "timeout_seconds": 10, "runtime": "ComfyUI", "runtime_version": "fixture-1",
        "model": {"id": "brand-new-model-label", "revision": "local-file-sha", "license": "fixture", "license_source": "local fixture"},
        "comfyui": {"mode": "dynamic_local", "base_url": base, "workflow_path": workflow_path,
                    "settings_policy": "preserve_workflow_defaults", "bindings": bindings if bindings is not None else {
                        "prompt": {"node_id": "2", "input": "text"}, "seed": {"node_id": "4", "input": "seed"},
                        "width": {"node_id": "3", "input": "width"}, "height": {"node_id": "3", "input": "height"},
                        "output": {"node_id": "9", "kind": "local_image"}}},
    }
    (root / "workflow.json").write_text(json.dumps(valid_graph()), encoding="utf-8")
    (root / "bundle.yaml").write_text(yaml.safe_dump(bundle, sort_keys=False), encoding="utf-8")
    return bundle


def expect_blocked(callback, reason: str):
    try:
        callback()
    except creative.Blocked as exc:
        require(exc.reason_code == reason, f"expected {reason}, got {exc.reason_code}")
        return exc
    raise AssertionError(f"expected {reason}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="aips-comfy-dynamic-") as temporary:
        root = Path(temporary).resolve()
        # Keep the owned-job ledger and trace out of the real user state directory.
        os.environ["XDG_STATE_HOME"] = str(root / "state")
        instance, thread = server()
        base = f"http://127.0.0.1:{instance.server_port}"
        try:
            write_bundle(root, base, "workflow.json")
            loaded = creative.preflight(root, "bundle.yaml")
            require(loaded["status"] == "READY" and Handler.prompts == 0, "A01/A02/A03/A08: dynamic valid workflow was blocked or preflight queued work")
            require(loaded["model_id"] == "brand-new-model-label", "A01/A09: model label was forced through an AIPS allowlist or fallback")
            result = creative.execute(root, "bundle.yaml")
            require(result["status"] == "COMPLETE" and Handler.prompts == 1, "A10: execute did not submit exactly once")
            graph = Handler.prompt_graph
            require(graph["2"]["inputs"]["text"] == "Requested image brief: A synthetic acceptance prompt", "A10: explicit prompt binding was not injected")
            require(graph["4"]["inputs"]["seed"] == 123 and graph["3"]["inputs"]["width"] == 512 and graph["3"]["inputs"]["height"] == 640, "A10: explicit numeric bindings were not injected")
            require(graph["4"]["inputs"]["steps"] == 50 and graph["4"]["inputs"]["cfg"] == 3.5, "A13: unbound workflow settings were overwritten")
            require(graph["9"]["inputs"]["filename_prefix"].startswith("aips_") and "/" not in graph["9"]["inputs"]["filename_prefix"], "A20: output prefix escaped create-only local output policy")
            manifest = json.loads((root / "out/creative-execution-manifest.json").read_text())
            require(manifest["comfyui_workflow_mode"] == "dynamic_local" and manifest["comfyui_schema_sha256"].startswith("sha256:"), "runtime schema/workflow provenance missing")
            require((root / "out/asset.png").read_bytes() == PNG and manifest["verification"]["model_inference"] == "UNVERIFIED", "synthetic lifecycle implied actual inference")
            require(Handler.prompts == 1, "A10: execute submitted more than one POST")

            metadata = schema()
            novel = valid_graph()
            novel["10"] = {"class_type": "ComfyCoreNovel", "inputs": {"enabled": False}}
            analysis = comfyui_workflow.validate_schema(novel, metadata)
            require("output_node_id" in analysis, "A03: new reviewed core node was rejected by a model/topology registry")
            missing = valid_graph()
            missing["1"]["inputs"]["ckpt_name"] = "missing-component.safetensors"
            expect_blocked(lambda: comfyui_workflow.validate_schema(missing, metadata), "MODEL_COMPONENT_MISSING")
            missing_node = valid_graph()
            missing_node["7"] = {"class_type": "NotInstalledNode", "inputs": {}}
            expect_blocked(lambda: comfyui_workflow.validate_schema(missing_node, metadata), "WORKFLOW_NODE_MISSING")
            for class_type, module, expected in (("RemoteImageAPI", "comfy_api_nodes.nodes_remote", "EXTERNAL_EGRESS_DENIED"),
                                                  ("UnreviewedCustom", "custom_nodes.unreviewed", "CUSTOM_NODE_TRUST_REQUIRED")):
                unsafe = valid_graph()
                unsafe["10"] = {"class_type": class_type, "inputs": {"url": "https://example.invalid"} if class_type == "RemoteImageAPI" else {"enabled": True}}
                unsafe_info = {**metadata, class_type: {**metadata[class_type], "python_module": module}}
                expect_blocked(lambda g=unsafe, i=unsafe_info: comfyui_workflow.validate_schema(g, i), expected)
            ambiguous = valid_graph()
            ambiguous["10"] = {"class_type": "CLIPTextEncode", "inputs": {"text": "second", "clip": ["1", 1]}}
            ambiguity_root = root / "ambiguity"
            ambiguity_root.mkdir()
            ambiguity_bundle = write_bundle(ambiguity_root, base, "workflow.json", bindings={})
            (ambiguity_root / "workflow.json").write_text(json.dumps(ambiguous), encoding="utf-8")
            (ambiguity_root / "bundle.yaml").write_text(yaml.safe_dump(ambiguity_bundle, sort_keys=False), encoding="utf-8")
            expect_blocked(lambda: creative.preflight(ambiguity_root, "bundle.yaml"), "WORKFLOW_BINDING_AMBIGUOUS")
            require(Handler.prompts == 1, "preflight denial caused network submission")

            # A broken connection after the server accepts the one POST must never retry blindly.
            recovery_root = root / "recovery"
            recovery_root.mkdir()
            write_bundle(recovery_root, base, "workflow.json")
            Handler.drop_response = True
            exc = expect_blocked(lambda: creative.execute(recovery_root, "bundle.yaml"), "comfy_job_recovery_required")
            require(exc.diagnostics.get("retryable") is False and Handler.prompts == 2, "A11: uncertain acceptance retried or omitted recovery guidance")
            Handler.drop_response = False

            workflow_source = root / "source.json"
            workflow_source.write_text(json.dumps(valid_graph()), encoding="utf-8")
            imported = creative.workflows_import(root, workflow_source, "workflows/imported.json")
            require(imported["status"] == "IMPORTED" and imported["overwrite"] is False, "A17: local create-only workflow import failed")
            expect_blocked(lambda: creative.workflows_import(root, workflow_source, "workflows/imported.json"), "workflow_import_target_invalid")
            inspect = creative.workflows_inspect(root, "workflow.json", base)
            require(inspect["status"] == "READY" and inspect["generation_executed"] is False, "P2 inspect performed work or failed to report candidates")
            inspect_text = json.dumps(inspect)
            require(MODEL not in inspect_text and "fixture-1" not in inspect_text
                    and "model_candidates" not in inspect,
                    "P2 inspect exposed model filenames, runtime version, or raw candidate lists")
            scan = creative.workflows_scan(root, base)
            require(scan["status"] == "READY" and scan["readiness"]["inference"] == "INFERENCE_UNVERIFIED", "A16 scan did not refresh live capabilities conservatively")
            scan_text = json.dumps(scan)
            require(MODEL not in scan_text and "fixture-1" not in scan_text,
                    "A16 scan exposed model filenames or runtime version")
            cli_response = creative.workflow_cli_response("inspect")
            require(cli_response == {"status": "READY", "generation_executed": False,
                                     "external_image_egress": False,
                                     "readiness": {"inference": "INFERENCE_UNVERIFIED"}},
                    "P2 CLI response exposed runtime/workflow inspection details")
            require(creative.workflow_cli_response("import") == {"status": "IMPORTED", "overwrite": False},
                    "A17 CLI response exposed imported workflow details")
            require(Handler.prompts == 2, "scan/import/inspect caused generation")
        finally:
            instance.shutdown()
            instance.server_close()
            thread.join(timeout=3)
    print("comfyui_dynamic_workflow_lifecycle PASS (synthetic; model inference UNVERIFIED)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

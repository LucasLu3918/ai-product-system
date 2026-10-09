"""Contract and single-owner synthetic lifecycle for local creative execution."""
import subprocess
import sys

import yaml

from .static_contracts import ROOT, errors

required = (
    ROOT / "scripts/creative_execution.py",
    ROOT / "templates/creative/CREATIVE_BUNDLE.yaml",
    ROOT / "templates/creative/COMFYUI_Z_IMAGE_TURBO_API.json",
    ROOT / "tests/evidence/creative_execution_lifecycle.py",
    ROOT / "tests/evidence/creative_generate_set_lifecycle.py",
    ROOT / "templates/creative/CREATIVE_COLLECTION_PROFILE.yaml",
    ROOT / "templates/creative/CREATIVE_JOB_MANIFEST.yaml",
    ROOT / "tests/scenarios/236-local-creative-execution.md",
    ROOT / "tests/scenarios/238-creative-task-authorization-and-multi-item-execution.md",
    ROOT / "orchestration/CREATIVE_DIRECTION.md",
    ROOT / "docs/human/USER_GUIDE.md",
    ROOT / "docs/human/TECHNOLOGY_GUIDE.md",
)
for path in required:
    if not path.is_file():
        errors.append(f"Missing local creative execution artifact: {path.relative_to(ROOT)}")

if all(path.is_file() for path in required):
    bundle = yaml.safe_load(required[1].read_text(encoding="utf-8")) or {}
    executor = required[0].read_text(encoding="utf-8")
    docs = required[9].read_text(encoding="utf-8")
    plugin = (ROOT / "harness/adapters/opencode/plugin.ts").read_text(encoding="utf-8")
    compatibility = (ROOT / "harness/adapters/opencode/COMPATIBILITY.md").read_text(encoding="utf-8")
    contracts = (
        (bundle.get("mode") == "EPHEMERAL", "Bundle template must default to EPHEMERAL"),
        ("BLOCKED_NO_ENGINE" in executor, "missing engines must fail closed"),
        ("shell=False" in executor and "subprocess.run" in executor, "MFLUX must use argv-only process execution"),
        ("ProxyHandler({})" in executor and "class NoRedirect" in executor, "ComfyUI requests must block proxies and redirects"),
        ("COMFY_CORE_NODES" in executor and "comfy_custom_node_blocked" in executor, "ComfyUI workflow must reject non-core nodes"),
        ('model_profile == "z-image-turbo"' in executor and '"lumina2"' in executor and "comfy_model_unavailable" in executor, "Z-Image Turbo ComfyUI must remain a fixed, local-inventory-verified profile"),
        ("strip_png_text_metadata" in executor and "prompt-bearing PNG text chunks" in executor, "ComfyUI outputs must not persist prompt-bearing PNG metadata"),
        ("UNETLoader" in required[2].read_text(encoding="utf-8") and "ConditioningZeroOut" in required[2].read_text(encoding="utf-8"), "Z-Image Turbo API template must retain its fixed split-loader topology"),
        ("creative-execution-manifest.json" in executor and "PENDING" in executor, "execution must retain provenance and pending human review"),
        ("aips creative preflight" in docs and "BLOCKED_NO_ENGINE" in docs, "Creative Direction must document preflight and missing-engine state"),
        ("MFLUX_CAPABILITIES" in executor and "mflux-generate-flux2-edit" in executor and "mflux-generate-qwen-edit" in executor, "MFLUX commands must use the closed capability registry"),
        ("MAX_REFERENCE_IMAGES = 8" in executor and "--image-paths" in executor, "MFLUX edit reference batches must be bounded and explicit"),
        ("def prepare(" in executor and "os.O_EXCL" in executor and "creative_ephemeral_required" in executor, "preparation must be confined, create-only and EPHEMERAL"),
        ("exactly one hash-checked reference" in compatibility, "ComfyUI compatibility docs must state the single-reference boundary"),
        ('enum: ["prepare", "configure", "discover", "preflight", "execute", "generate-set"]' in plugin and 'classification.intent !== "create"' in plugin, "OpenCode preparation and generation sets must remain explicit and intent-gated"),
        ('ctx.session.hook("prompt"' in plugin and 'creativeAdmissions' in plugin and 'creative_admission_grant_missing' in plugin and 'slice(-64)' not in plugin, "OpenCode mutation authority must use current prompt admission, independent of transcript truncation"),
        ('def generate_set(' in executor and 'verified_prior_success' in executor and 'batch must continue after an item fails' in (ROOT / "tests/evidence/creative_generate_set_lifecycle.py").read_text(encoding="utf-8"), "multi-item execution must continue failures and verify resume evidence"),
        ('bounded_version_only' in executor and 'timeout=3' in executor, "engine discovery must use bounded version-only health probes"),
        ('creative_request_policy.py' in plugin and 'contextMessages' in plugin, "OpenCode must normalize native context for advisory routing"),
    )
    for condition, message in contracts:
        if not condition:
            errors.append(message)

    lifecycle = subprocess.run(
        [sys.executable, str(ROOT / "tests/evidence/creative_execution_lifecycle.py")],
        cwd=ROOT, capture_output=True, text=True, timeout=90, check=False,
    )
    if lifecycle.returncode:
        errors.append("Creative execution lifecycle failed: " + lifecycle.stdout + lifecycle.stderr)
    else:
        print(lifecycle.stdout.strip())
    batch = subprocess.run(
        [sys.executable, str(ROOT / "tests/evidence/creative_generate_set_lifecycle.py")],
        cwd=ROOT, capture_output=True, text=True, timeout=90, check=False,
    )
    if batch.returncode:
        errors.append("Creative generate-set lifecycle failed: " + batch.stdout + batch.stderr)
    else:
        print(batch.stdout.strip())

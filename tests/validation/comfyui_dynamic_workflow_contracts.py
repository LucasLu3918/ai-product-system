"""Contracts for model-agnostic, fail-closed ComfyUI workflow support."""
import subprocess
import sys

from .static_contracts import ROOT, errors

required = (
    ROOT / "scripts/comfyui_capabilities.py",
    ROOT / "scripts/comfyui_workflow.py",
    ROOT / "scripts/comfyui_workflow_policy.py",
    ROOT / "scripts/creative_execution.py",
    ROOT / "scripts/aips_cli/dispatch.sh",
    ROOT / "scripts/aips_cli/help.sh",
    ROOT / "templates/creative/CREATIVE_BUNDLE.yaml",
    ROOT / "tests/evidence/comfyui_dynamic_workflow_lifecycle.py",
    ROOT / "tests/scenarios/268-comfyui-model-agnostic-workflows.md",
)
for path in required:
    if not path.is_file():
        errors.append(f"Missing dynamic ComfyUI artifact: {path.relative_to(ROOT)}")

if all(path.is_file() for path in required):
    capabilities = required[0].read_text(encoding="utf-8")
    workflow = required[1].read_text(encoding="utf-8")
    policy = required[2].read_text(encoding="utf-8")
    executor = required[3].read_text(encoding="utf-8")
    discovery = executor.split("def discover_comfyui(", 1)[1].split("\ndef discover(", 1)[0]
    dispatch = required[4].read_text(encoding="utf-8")
    help_text = required[5].read_text(encoding="utf-8")
    bundle = required[6].read_text(encoding="utf-8")
    contracts = (
        ("MAX_OBJECT_INFO_BYTES" in capabilities and "MAX_OBJECT_INFO_NODES" in capabilities, "object_info must be byte- and node-bounded"),
        ("record_private_snapshot" in capabilities and "private_fingerprints_only" in capabilities, "cache must be private and contain fingerprints only"),
        ("MAX_WORKFLOW_BYTES" in workflow and "MAX_WORKFLOW_NODES" in workflow and "WORKFLOW_LINK_INVALID" in workflow, "workflow parsing must be bounded and validate graph links"),
        ("WORKFLOW_BINDING_AMBIGUOUS" in executor and "preserve_workflow_defaults" in executor, "bindings must be explicit and preserve unbound defaults"),
        ("comfy_api_nodes" in policy and "CUSTOM_NODE_TRUST_REQUIRED" in policy and "TRUSTED_CORE" in policy, "API/custom node trust must stay separate from model IDs"),
        ('"/object_info"' in executor and '"/prompt"' in executor, "capability discovery and execution must use separate local routes"),
        ("INSPECT_COMFYUI_QUEUE_AND_HISTORY" in executor and "automatic_resubmission" in executor, "unknown single-POST acceptance must require manual recovery"),
        ("mps_dtype_unsupported" in executor and "gpu_out_of_memory" in executor, "hardware failures must retain their actual safe category"),
        ("workflows_import" in executor and "os.O_EXCL" in executor and "creative_ephemeral_required" in executor, "workflow import must be local, EPHEMERAL and create-only"),
        ("def workflow_cli_response" in executor and 'response = workflow_cli_response(args.workflow_action) if args.action == "workflows" else result' in executor, "workflow CLI stdout must use fixed acknowledgements while preserving other Creative CLI response contracts"),
        ('"trusted_core_nodes"' not in discovery and '"denied_nodes"' not in discovery, "ComfyUI discovery must not expose a local node inventory"),
        ("workflows)" in dispatch and "creative workflows scan" in help_text and "creative workflows inspect" in help_text, "workflow subcommands must be publicly routed and documented"),
        ("mode: fixed" in bundle and "dynamic_local" in bundle, "dynamic mode must be opt-in with the fixed default preserved"),
        ("model inference UNVERIFIED" in required[7].read_text(encoding="utf-8"), "synthetic lifecycle must not claim real inference"),
    )
    for condition, message in contracts:
        if not condition:
            errors.append(message)
    if not errors:
        result = subprocess.run(
            [sys.executable, str(required[7])], cwd=ROOT, capture_output=True,
            text=True, timeout=90, check=False,
        )
        if result.returncode:
            errors.append("Dynamic ComfyUI lifecycle failed: " + result.stdout + result.stderr)
        else:
            print(result.stdout.strip())

if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print("comfyui_dynamic_workflow_contracts PASS")

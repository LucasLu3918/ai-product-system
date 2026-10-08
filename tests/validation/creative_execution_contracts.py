"""Contract and single-owner synthetic lifecycle for local creative execution."""
import subprocess
import sys

import yaml

from .static_contracts import ROOT, errors

required = (
    ROOT / "scripts/creative_execution.py",
    ROOT / "templates/creative/CREATIVE_BUNDLE.yaml",
    ROOT / "tests/evidence/creative_execution_lifecycle.py",
    ROOT / "tests/scenarios/236-local-creative-execution.md",
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
    docs = required[4].read_text(encoding="utf-8")
    contracts = (
        (bundle.get("mode") == "EPHEMERAL", "Bundle template must default to EPHEMERAL"),
        ("BLOCKED_NO_ENGINE" in executor, "missing engines must fail closed"),
        ("shell=False" in executor and "subprocess.run" in executor, "MFLUX must use argv-only process execution"),
        ("ProxyHandler({})" in executor and "class NoRedirect" in executor, "ComfyUI requests must block proxies and redirects"),
        ("COMFY_CORE_NODES" in executor and "comfy_custom_node_blocked" in executor, "ComfyUI workflow must reject non-core nodes"),
        ("creative-execution-manifest.json" in executor and "PENDING" in executor, "execution must retain provenance and pending human review"),
        ("aips creative preflight" in docs and "BLOCKED_NO_ENGINE" in docs, "Creative Direction must document preflight and missing-engine state"),
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

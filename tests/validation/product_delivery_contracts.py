import json
from pathlib import Path
import subprocess
import sys

from .static_contracts import ROOT, errors

LIFECYCLE = ROOT / "tests/evidence/product_delivery_lifecycle.py"
VALIDATOR = ROOT / "scripts/product_delivery_evidence.py"
READINESS = ROOT / "scripts/check_release_readiness.py"
PRODUCT_DELIVERY = ROOT / "orchestration/PRODUCT_DELIVERY.md"
RELEASE_READINESS = ROOT / "orchestration/RELEASE_READINESS.md"
PRODUCT_TEMPLATE = ROOT / "templates/product/PRODUCT.yaml"
READINESS_TEMPLATE = ROOT / "templates/delivery/RELEASE_READINESS.yaml"

for required in (
    LIFECYCLE,
    VALIDATOR,
    READINESS,
    PRODUCT_DELIVERY,
    RELEASE_READINESS,
    PRODUCT_TEMPLATE,
    READINESS_TEMPLATE,
):
    if not required.exists():
        errors.append(f"Missing product delivery evidence artifact: {required.relative_to(ROOT)}")

for script in (LIFECYCLE, VALIDATOR, READINESS):
    if not script.exists():
        continue
    compiled = subprocess.run(
        [sys.executable, "-m", "py_compile", str(script)], capture_output=True, text=True
    )
    if compiled.returncode != 0:
        errors.append(f"Product delivery artifact syntax failed: {script.relative_to(ROOT)}: {compiled.stderr.strip()}")

if LIFECYCLE.exists():
    try:
        result = subprocess.run(
            [sys.executable, str(LIFECYCLE)],
            capture_output=True,
            text=True,
            timeout=45,
        )
        if result.returncode != 0:
            errors.append(
                "Product delivery lifecycle evidence failed: "
                + result.stdout.strip()
                + " "
                + result.stderr.strip()
            )
        elif "PRODUCT DELIVERY LIFECYCLE PASSED" not in result.stdout:
            errors.append("Product delivery lifecycle did not emit its PASS sentinel")
    except subprocess.TimeoutExpired:
        errors.append("Product delivery lifecycle evidence timed out after 45 seconds")

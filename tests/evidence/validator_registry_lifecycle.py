from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))

from validation.registry import ERROR_AGGREGATION_ORDER, VALIDATORS  # noqa: E402


modules = [entry.module for entry in VALIDATORS]
assert modules and len(modules) == len(set(modules)), "validator registry must be ordered and unique"
assert modules[0] == "validation.static_contracts", "static validation remains first"
assert ERROR_AGGREGATION_ORDER == (
    "validation.static_contracts",
    "validation.eval_interop_contracts",
    "validation.telemetry_export_contracts",
    "validation.implementation_profile_contracts",
    "validation.openapi_generator_adapter_contracts",
    "validation.implementation_enforcement_contracts",
    "validation.openapi_contracts",
), "validation error aggregation order is a compatibility contract"
aggregators = {entry.module for entry in VALIDATORS if entry.collect_errors}
assert aggregators == set(ERROR_AGGREGATION_ORDER), "error-collecting validators must match the declared aggregation set"
for module in modules:
    assert importlib.util.find_spec(module) is not None, f"registered validator is unavailable: {module}"
print(f"VALIDATOR REGISTRY LIFECYCLE PASSED modules={len(modules)} error_aggregators={len(aggregators)}")

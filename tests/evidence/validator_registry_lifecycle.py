from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))

from validation.registry import (
    ERROR_AGGREGATION_ORDER,
    VALIDATORS,
    load_validators,
)

modules = [entry.module for entry in VALIDATORS]
assert modules and len(modules) == len(set(modules)), "validator registry must be ordered and unique"
assert modules[0] == "validation.static_contracts", "static validation remains first"
assert ERROR_AGGREGATION_ORDER == (
    "validation.static_contracts",
    "validation.versioning_contracts",
    "validation.system_facts_contracts",
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

browser_modules = {entry.module for entry in VALIDATORS if entry.requires_browser}
assert browser_modules == {
    "validation.visual_render_contracts",
    "validation.creative_evidence_contracts",
}, "only the visual and creative render validators require the browser toolchain"

default_imported: list[str] = []
with patch("validation.registry.importlib.import_module", side_effect=default_imported.append):
    default_selected = load_validators(lambda _name, _started, _status: None)
assert set(default_selected) == set(modules), "missing plan must keep the full validator profile"
assert set(default_imported) == set(modules), "missing plan must import every validator"

for needs_browser, expected in (
    (False, set(modules) - browser_modules),
    (True, set(modules)),
):
    imported: list[str] = []
    timings: list[tuple[str, str]] = []

    def fake_import(module: str, target: list[str] = imported) -> object:
        target.append(module)
        return object()

    with patch("validation.registry.importlib.import_module", side_effect=fake_import):
        selected = load_validators(
            lambda name, _started, status, target=timings: target.append((name, status)),
            needs_browser=needs_browser,
        )
    assert set(selected) == expected, f"wrong validators selected when needs_browser={needs_browser}"
    assert set(imported) == expected, f"unexpected imports when needs_browser={needs_browser}"
    if not needs_browser:
        skipped = {name for name, status in timings if status.startswith("SKIPPED:")}
        assert skipped == browser_modules, "browser skips must be explicit in timing evidence"
print(f"VALIDATOR REGISTRY LIFECYCLE PASSED modules={len(modules)} error_aggregators={len(aggregators)}")

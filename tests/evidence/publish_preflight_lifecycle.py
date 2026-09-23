from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module():
    spec = importlib.util.spec_from_file_location("publish_preflight", ROOT / "scripts/publish_preflight.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    publish = load_module()

    change_class, warning = publish.resolve_change_class("auto", "bug,aips:core-change")
    assert change_class == "core" and warning is None
    explicit, warning = publish.resolve_change_class("large", "aips:core-change")
    assert explicit == "large" and warning

    impact = publish.documentation_impact(["bin/aips"])
    for required in (
        "docs/human/INSTALLATION.md",
        "docs/human/GETTING_STARTED.md",
        "docs/human/TECHNOLOGY_GUIDE.md",
    ):
        assert required in impact["required_additions"]
    assert not impact["complete"]

    complete_files = ["bin/aips", *impact["required_additions"]]
    assert publish.documentation_impact(complete_files)["complete"]

    profile = {"matrix_required_change_classes": ["large", "core"], "matrix_required_paths": []}
    assert publish.matrix_required(profile, ["docs/README.md"], "core")
    assert not publish.matrix_required(profile, ["docs/README.md"], "standard")

    environment = publish.environment_status()
    assert environment["status"] in {"READY", "ENVIRONMENT_BLOCKED"}
    assert isinstance(environment["blockers"], list)

    source = (ROOT / "scripts/publish_preflight.py").read_text(encoding="utf-8")
    for contract in (
        "AIPS_DOCS_DIFF_BASE",
        "CORE_CHANGE_TEST_MATRIX.yaml",
        "ENVIRONMENT_BLOCKED",
        "RESET_EQUIVALENT_TREE",
        "refresh-intelligence",
    ):
        assert contract in source

    print("PUBLISH PREFLIGHT LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

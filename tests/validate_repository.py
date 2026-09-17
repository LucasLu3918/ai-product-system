import os


def _append_validation_git_config(key: str, value: str) -> None:
    """Apply test-only Git config to this validation process and its children."""
    raw_count = os.environ.get("GIT_CONFIG_COUNT", "0")
    try:
        count = int(raw_count)
    except ValueError as exc:
        raise RuntimeError(f"invalid inherited GIT_CONFIG_COUNT: {raw_count!r}") from exc
    os.environ[f"GIT_CONFIG_KEY_{count}"] = key
    os.environ[f"GIT_CONFIG_VALUE_{count}"] = value
    os.environ["GIT_CONFIG_COUNT"] = str(count + 1)


# Lifecycle evidence rapidly creates, updates and deletes temporary Git repositories.
# Disable automatic detached gc only for repository validation so a background Git
# maintenance process cannot race TemporaryDirectory cleanup after the Git command
# under test has already returned. Product/runtime Git behavior is intentionally unchanged.
_append_validation_git_config("gc.auto", "0")
_append_validation_git_config("gc.autoDetach", "false")

from validation import static_contracts as static_contracts
from validation import runtime_contracts as runtime_contracts  # noqa: F401
from validation import visual_render_contracts as visual_render_contracts  # noqa: F401
from validation import performance_evidence_contracts as performance_evidence_contracts  # noqa: F401
from validation import creative_evidence_contracts as creative_evidence_contracts  # noqa: F401
from validation import product_delivery_contracts as product_delivery_contracts  # noqa: F401
from validation import evolution_radar_contracts as evolution_radar_contracts  # noqa: F401
from validation import governance_resume as governance_resume  # noqa: F401
from validation import conformance_isolation as conformance_isolation  # noqa: F401
from validation import syntax_contracts as syntax_contracts  # noqa: F401

errors = static_contracts.errors

if errors:
    print("VALIDATION FAILED")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("VALIDATION PASSED")
print(f"version={static_contracts.version}")
print(f"roles={len((static_contracts.roles.get('roles') or {}))}")
print(f"skills={len((static_contracts.skills.get('skills') or {}))}")
print(f"scenarios={len(static_contracts.scenarios)}")

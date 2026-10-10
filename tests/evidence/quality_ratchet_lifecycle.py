from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import quality_ratchet


def main() -> int:
    old = [{"filename": str(ROOT / "scripts/example.py"), "code": "F401", "name": "unused-import", "message": "unused import", "location": {"row": 2}, "cell": None}]
    same = [{"filename": str(ROOT / "scripts/example.py"), "code": "F401", "name": "unused-import", "message": "unused import", "location": {"row": 9}, "cell": None}]
    added = [{"filename": str(ROOT / "scripts/example.py"), "code": "F821", "name": "undefined-name", "message": "undefined name", "location": {"row": 10}, "cell": None}]
    assert quality_ratchet.added_touched_findings(same, old, {"scripts/example.py"}) == []
    assert quality_ratchet.added_touched_findings(same + added, old, {"scripts/example.py"}) == added
    assert quality_ratchet.added_touched_findings(added, old, {"tests/other.py"}) == []
    summary = quality_ratchet.summarize(old + added)
    assert summary["total"] == 2 and summary["fixable"] == 0 and summary["manual"] == 2
    assert summary["by_rule"]["F401"]["findings"] == 1
    violations = quality_ratchet.module_debt_violations(
        {"by_module": {"scripts/project_intelligence.py": {"findings": 13}}},
        {"scripts/project_intelligence.py": {"current_findings": 13, "next_target": 11}},
        touched={"scripts/project_intelligence.py"},
        previous_counts={"scripts/project_intelligence.py": 20},
    )
    assert violations == []
    terminal_zero = quality_ratchet.module_debt_violations(
        {"by_module": {"scripts/project_intelligence.py": {"findings": 0}}},
        {"scripts/project_intelligence.py": {"current_findings": 0, "next_target": 0}},
    )
    assert terminal_zero == []
    terminal_zero_violation = quality_ratchet.module_debt_violations(
        {"by_module": {"scripts/project_intelligence.py": {"findings": 1}}},
        {"scripts/project_intelligence.py": {"current_findings": 0, "next_target": 0}},
    )
    assert terminal_zero_violation and "1 findings exceed recorded current_findings 0" in terminal_zero_violation[0]
    violations = quality_ratchet.module_debt_violations(
        {"by_module": {"scripts/project_intelligence.py": {"findings": 19}}},
        {"scripts/project_intelligence.py": {"current_findings": 19, "next_target": 17}},
        touched={"scripts/project_intelligence.py"},
        previous_counts={"scripts/project_intelligence.py": 20},
    )
    assert violations and "10% burn-down target 18" in violations[0]
    print("QUALITY RATCHET LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

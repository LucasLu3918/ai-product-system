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
    print("QUALITY RATCHET LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

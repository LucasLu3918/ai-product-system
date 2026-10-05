#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

def main() -> int:
    import retrieval_intelligence as facade
    import retrieval_relations as implementation

    source = (
        "def apply_change(value):\n"
        "    # ignored_comment()\n"
        "    text = 'ignored_string()'\n"
        "    return normalize(value)\n"
    )
    masked = facade.code_without_comments_or_strings(source)
    assert masked == implementation.code_without_comments_or_strings(source)
    expected = implementation.relation_rows(
        masked,
        facade.extract_symbols("sample.py", source),
        max_rows=facade.IMPACT_MAX_RELATIONS_PER_FILE,
    )
    assert facade.extract_code_relations("sample.py", source) == expected
    assert expected == [
        {
            "source_name": "apply_change",
            "source_definition_line": 1,
            "target_name": "text",
            "source_line": 3,
            "relation": "references",
        },
        {
            "source_name": "apply_change",
            "source_definition_line": 1,
            "target_name": "normalize",
            "source_line": 4,
            "relation": "calls",
        },
        {
            "source_name": "apply_change",
            "source_definition_line": 1,
            "target_name": "value",
            "source_line": 4,
            "relation": "references",
        },
    ]
    assert any(
        row["target_name"] == "normalize" and row["relation"] == "calls"
        for row in expected
    )
    assert all(
        row["target_name"] not in {"ignored_comment", "ignored_string"}
        for row in expected
    )
    assert facade.extract_code_relations("sample.txt", source) == []
    assert facade.extract_code_relations("config/credentials.json", source) == []
    print("RETRIEVAL RELATIONS EXTRACTION FACADE LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
